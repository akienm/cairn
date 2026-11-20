"""Proof for ticket e44cf1f23c84 — a scratch bus's socket path does not ride the length of TMPDIR.

MEASURED 2026-11-19 on akiendelllinux: with TMPDIR=/var/tmp a scratch bus home's
``<home>/bus.sock`` came to 110 bytes against Linux's 107, and every proof that binds one
red 'OSError: AF_UNIX path too long'. /tmp fit the socket but not the tester's instance
snapshots that the same TMPDIR places. So a scratch bus's socket now lives at
``$XDG_RUNTIME_DIR/cairn-bus-<hash>.sock`` (``remote.socket_path``), with ``<home>/bus.sock``
a link to it; the live home's address is unchanged.

Every bus here is a child ``serve --scratch --lan 0`` at a scratch home made deliberately deep
(``<home>/bus.sock`` over 150 bytes), with TMPDIR pointed at that depth too. No tooth dials the
live bus; every child is reaped and every unit stopped by name in a finally.

  1. test_a_deep_scratch_home_serves: the bus serves and a client at that home is answered;
  2. test_the_socket_is_short_and_under_the_runtime_dir: the bound socket is
     $XDG_RUNTIME_DIR/<unit>.sock — under 108 bytes, not under TMPDIR, mode 0600 — and
     <home>/bus.sock links to it; the live home's address is <live home>/bus.sock;
  3. test_nothing_stale_and_nothing_shared: two homes get two sockets, and after each exits
     neither its runtime socket nor its link remains;
  4. test_no_runtime_dir_refuses_loudly: with XDG_RUNTIME_DIR unset and a deep home, serve
     exits non-zero naming AF_UNIX, the path and its byte count, and binds nothing;
  5. test_a_fixture_bus_is_dialled_where_it_binds_and_leaves_nothing: bus_client's draining
     proof, whose fake bus stands in for the server, run as a child with XDG_RUNTIME_DIR a fresh
     0700 directory, CAIRN_BUS_UNIT unset and TMPDIR deep (so the old <home>/bus.sock cannot
     bind), passes its three teeth, and leaves that directory empty.

    python3 cairn/devices/cairn/machines/bus/proofs/test_a_scratch_bus_socket_does_not_ride_tmpdir.py
"""
from __future__ import annotations

import hashlib
import os
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"e44cf1f23c84": {
    "1": "test_a_deep_scratch_home_serves",
    "2": "test_the_socket_is_short_and_under_the_runtime_dir",
    "3": "test_nothing_stale_and_nothing_shared",
    "4": "test_no_runtime_dir_refuses_loudly",
    "5": "test_a_fixture_bus_is_dialled_where_it_binds_and_leaves_nothing",
}}

_MODULE = "cairn.devices.cairn.machines.bus"
_START_S = 30.0
_EXIT_S = 30.0
_DEEP = 150   # <home>/bus.sock is made longer than this: far past the 107-byte limit
_DRAINING = _REPO / "cairn" / "tools" / "bus_client" / "proofs" / "test_a_draining_bus_is_used_not_raced.py"


def _deep_home(tag: str) -> tuple[Path, Path]:
    """(home, tmpdir): a scratch home nested until its bus.sock is over _DEEP bytes, and the
    directory above it, which the child takes as its TMPDIR."""
    from cairn.tools.scratch.scratch import scratch_dir
    top = scratch_dir(f"testing-e44cf1f23c84-{tag}-")
    tmp = top
    while len(os.fsencode(str(tmp / "h" / "bus.sock"))) <= _DEEP:
        tmp = tmp / ("deep-" + "d" * 20)
    home = tmp / "h"
    home.mkdir(parents=True)
    return home, tmp


def _hashed(home: Path) -> str:
    return "cairn-bus-" + hashlib.sha1(str(home).encode()).hexdigest()[:10]


def _runtime() -> Path:
    run = os.environ.get("XDG_RUNTIME_DIR")
    assert run and Path(run).is_dir(), f"XDG_RUNTIME_DIR is {run!r}: the box this proof runs on has no runtime dir"
    return Path(run)


def _env(home: Path, tmp: Path, *, runtime: bool = True) -> dict:
    env = dict(os.environ)
    env["CAIRN_BUS_HOME"] = str(home)
    env["TMPDIR"] = str(tmp)
    env["PYTHONPATH"] = str(_REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("CAIRN_BUS_UNIT", None)   # the unit, and so the socket, is named by the home's hash
    if not runtime:
        env.pop("XDG_RUNTIME_DIR", None)
    return env


def _serve(home: Path, tmp: Path, *, runtime: bool = True) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", _MODULE, "serve", "--home", str(home), "--scratch", "--lan", "0"],
        cwd=str(_REPO), env=_env(home, tmp, runtime=runtime), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


class _NoUnitName:
    """CAIRN_BUS_UNIT out of this process's env while a tooth computes addresses in-process."""

    def __enter__(self):
        self.saved = os.environ.pop("CAIRN_BUS_UNIT", None)

    def __exit__(self, *exc):
        if self.saved is not None:
            os.environ["CAIRN_BUS_UNIT"] = self.saved


def _ask(home: Path, op: str, timeout: float = 30) -> dict:
    from cairn.tools.bus_client.remote import exchange
    with _NoUnitName():
        return exchange({"op": op}, home, timeout=timeout)


def _answered(proc: subprocess.Popen, home: Path) -> dict:
    """Wait until the bus at ``home`` answers stats; the reply."""
    deadline = time.monotonic() + _START_S
    last = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise AssertionError(f"the bus exited {proc.returncode} before it answered: "
                                 f"{proc.stdout.read()[-800:]}")
        try:
            return _ask(home, "stats", timeout=5)
        except OSError as exc:   # not bound yet: no file, refused, or (unfixed) too long
            last = exc
        time.sleep(0.1)
    raise AssertionError(f"no answer from the bus at {home} within {_START_S:.0f}s: last {last!r}")


def _shutdown(proc: subprocess.Popen, home: Path) -> str:
    """End the bus by its verb and wait; its output."""
    try:
        _ask(home, "shutdown", timeout=10)
    except OSError:
        pass
    try:
        out, _ = proc.communicate(timeout=_EXIT_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
        raise AssertionError(f"the bus did not exit within {_EXIT_S:.0f}s of shutdown: {out[-800:]}")
    return out


def _reap(proc: subprocess.Popen, home: Path) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=_EXIT_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    try:
        subprocess.run(["systemctl", "--user", "stop", f"{_hashed(home)}.service"],
                       capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        pass


def test_a_deep_scratch_home_serves():
    home, tmp = _deep_home("serves")
    assert len(os.fsencode(str(home / "bus.sock"))) > _DEEP
    proc = _serve(home, tmp)
    try:
        reply = _answered(proc, home)
        assert reply.get("ok"), f"stats did not answer ok: {reply!r}"
        _shutdown(proc, home)
    finally:
        _reap(proc, home)


def test_the_socket_is_short_and_under_the_runtime_dir():
    from cairn.tools.bus_client.remote import _live_home, socket_path
    run = _runtime()
    home, tmp = _deep_home("short")
    proc = _serve(home, tmp)
    try:
        _answered(proc, home)
        want = run / f"{_hashed(home)}.sock"
        with _NoUnitName():
            got = socket_path(home)
        assert got == want, f"socket_path({home}) is {got}, want {want}"
        n = len(os.fsencode(str(got)))
        assert n < 108, f"the socket path is {n} bytes: {got}"
        assert not str(got).startswith(str(tmp)), f"the socket {got} sits under TMPDIR {tmp}"
        st = os.stat(got)
        assert stat.S_ISSOCK(st.st_mode), f"{got} is not a socket: {oct(st.st_mode)}"
        assert stat.S_IMODE(st.st_mode) == 0o600, f"{got} has mode {oct(stat.S_IMODE(st.st_mode))}"
        link = home / "bus.sock"
        assert link.is_symlink(), f"{link} is not a link"
        assert Path(os.readlink(link)) == want, f"{link} points at {os.readlink(link)}, want {want}"
        live = _live_home()
        assert socket_path(live) == live / "bus.sock", f"the live home's address moved: {socket_path(live)}"
        _shutdown(proc, home)
    finally:
        _reap(proc, home)


def test_nothing_stale_and_nothing_shared():
    run = _runtime()
    (a, ta), (b, tb) = _deep_home("one"), _deep_home("two")
    pa, pb = _serve(a, ta), _serve(b, tb)
    try:
        _answered(pa, a)
        _answered(pb, b)
        sa, sb = run / f"{_hashed(a)}.sock", run / f"{_hashed(b)}.sock"
        assert sa != sb, f"two homes share one socket: {sa}"
        assert sa.is_socket() and sb.is_socket(), f"not both bound: {sa} {sa.exists()}, {sb} {sb.exists()}"
        for proc, home, sock in ((pa, a, sa), (pb, b, sb)):
            out = _shutdown(proc, home)
            assert not os.path.lexists(sock), f"the runtime socket {sock} outlived its bus: {out[-400:]}"
            assert not os.path.lexists(home / "bus.sock"), f"the link {home / 'bus.sock'} outlived its bus"
    finally:
        _reap(pa, a)
        _reap(pb, b)


def test_no_runtime_dir_refuses_loudly():
    home, tmp = _deep_home("refuses")
    own = home / "bus.sock"
    n = len(os.fsencode(str(own)))
    proc = _serve(home, tmp, runtime=False)
    try:
        try:
            out, _ = proc.communicate(timeout=_START_S)
        except subprocess.TimeoutExpired:
            raise AssertionError("with no runtime dir and a deep home the bus served on")
        assert proc.returncode != 0, f"serve exited 0: {out[-600:]}"
        for want in ("AF_UNIX", str(own), f"{n} bytes"):
            assert want in out, f"the refusal does not name {want!r}: {out[-800:]}"
        assert not os.path.lexists(own), f"something was bound at {own}"
        run = os.environ.get("XDG_RUNTIME_DIR")
        if run:
            ghost = Path(run) / f"{_hashed(home)}.sock"
            assert not os.path.lexists(ghost), f"a socket was bound at {ghost}"
    finally:
        _reap(proc, home)


def test_a_fixture_bus_is_dialled_where_it_binds_and_leaves_nothing():
    from cairn.tools.scratch.scratch import scratch_dir
    run = scratch_dir("testing-e44cf1f23c84-rt-")
    os.chmod(run, 0o700)
    _, tmp = _deep_home("fixture")
    env = _env(tmp / "unused", tmp)
    env.pop("CAIRN_BUS_HOME", None)
    env["XDG_RUNTIME_DIR"] = str(run)
    r = subprocess.run([sys.executable, str(_DRAINING)], cwd=str(_REPO), env=env,
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    out = r.stdout + r.stderr
    assert r.returncode == 0, f"the draining proof exited {r.returncode} over a private runtime dir: {out[-1200:]}"
    # print_teeth_main marks a passing tooth "ok  <name>" (proof_coverage.py)
    passed = {x.split()[1] for x in out.splitlines() if x.strip().startswith("ok ")}
    want = {"test_a_draining_bus_is_used", "test_an_idle_replace_still_spawns", "test_a_drained_use_is_noted"}
    assert passed == want, f"want the draining proof's three teeth ok, got {sorted(passed)}: {out[-800:]}"
    left = sorted(p.name for p in Path(run).iterdir())
    assert left == [], f"the fixture left {left} in its runtime dir {run}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

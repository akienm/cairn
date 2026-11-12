"""Proof for ticket d832a24e5144 — a bare `cairn librarian` opens the librarian's chat, no URL.

Q#30, Akien 2026-11-06: "a bare call to librarian should 1) launch that device's shim, which
2) parses the request (nothing) and so 3) launches the librarian and 4) launches a browser".
One tooth per numbered falsifier clause:

  1. A bare call, with the opener stubbed, prints no line containing 'http'.
  2. The stub is called once, with path /device/librarian.
  3. The device is started by its shim on the bare call: afterwards the shim's `start`
     answers that the librarian is already running.
  4. The launcher contains no systemd-run, setsid or listener.py.
  5. The librarian's standing proofs that touch the shim stay green.

The world: a scratch bus under a scratch CAIRN_BUS_HOME with its own unit name, a scratch
CAIRN_INSTANCE_ROOT, and a BROWSER stub that records the URL it is handed — no real browser,
no port 80. The launcher runs under a pty so its stdout is a terminal, the one place it opens
a browser. Every import of what the build added happens inside a tooth.

    python3 cairn/devices/librarian/proofs/test_a_bare_librarian_opens_its_chat.py
"""
from __future__ import annotations

import os
import pty
import select
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"d832a24e5144": {
    "1": "clause_1",
    "2": "clause_2",
    "3": "clause_3",
    "4": "clause_4",
    "5": "clause_5",
}}

LAUNCHER = REPO / "cairn" / "devices" / "librarian" / "0" / "bin" / "librarian"
PROOFS = REPO / "cairn" / "devices" / "librarian" / "proofs"
STANDING = ("test_librarian_ask.py", "test_librarian_chat.py",
            "test_the_probe_reads_the_tree_the_face_writes.py")
UNIT = f"cairn-bus-librarian-chat-proof-{os.getpid()}"
FAILURES: list[str] = []
_W: dict = {}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail[:1200]}"), flush=True)
    if not ok:
        FAILURES.append(name)


def _env() -> dict:
    env = dict(os.environ)
    env.update(CAIRN_BUS_HOME=str(_W["bus"]), CAIRN_BUS_UNIT=UNIT,
               CAIRN_INSTANCE_ROOT=str(_W["inst"]), PYTHONDONTWRITEBYTECODE="1",
               BROWSER=f"{_W['stub']} %s", CAIRN_WEB_SERVER_PORT="8799",
               PYTHONPATH=str(REPO) + os.pathsep + env.get("PYTHONPATH", ""))
    env.pop("CAIRN_LIBRARIAN_NO_BROWSER", None)
    env.pop("CAIRN_HOME_HOST", None)
    return env


def _world() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    base = scratch_dir("d832-librarian-chat-")
    _W.update(base=base, bus=base / "bus", inst=base / "devices", calls=base / "opened.txt",
              stub=base / "browser-stub")
    _W["bus"].mkdir()
    _W["inst"].mkdir()
    _W["stub"].write_text(f"#!/bin/sh\nprintf '%s\\n' \"$1\" >> '{_W['calls']}'\n")
    _W["stub"].chmod(0o755)
    r = subprocess.run([sys.executable, "-c",
                        "from cairn.tools.bus_client.remote import ensure_bus\n"
                        "ensure_bus(scratch=True)\nprint('up')\n"],
                       env=_env(), cwd=str(REPO), capture_output=True, text=True, timeout=180)
    if r.stdout.strip() != "up":
        print(f"  (scratch bus did not start: {(r.stdout + r.stderr)[-600:]})", flush=True)


def _teardown() -> None:
    if not _W:
        return
    subprocess.run([sys.executable, "-c",
                    "from cairn.tools.bus_client.remote import RemoteBus\n"
                    "try:\n    RemoteBus().shutdown()\nexcept Exception:\n    pass\n"],
                   env=_env(), cwd=str(REPO), capture_output=True, timeout=60)
    subprocess.run(["systemctl", "--user", "stop", f"{UNIT}.service"], capture_output=True)
    subprocess.run(["systemctl", "--user", "reset-failed", f"{UNIT}.service"], capture_output=True)
    shutil.rmtree(_W["base"], ignore_errors=True)


def _bare_under_a_pty(timeout: float = 240) -> tuple[int, str]:
    """Run the bare launcher with its stdout (and stderr) on a pty; return (rc, all it said)."""
    if "bare" in _W:
        return _W["bare"]
    master, slave = pty.openpty()
    p = subprocess.Popen([str(LAUNCHER)], env=_env(), cwd="/", stdin=subprocess.DEVNULL,
                         stdout=slave, stderr=slave, close_fds=True)
    os.close(slave)
    out = b""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r, _, _ = select.select([master], [], [], 0.5)
        if r:
            try:
                chunk = os.read(master, 4096)
            except OSError:
                chunk = b""
            if not chunk and p.poll() is not None:
                break
            out += chunk
        elif p.poll() is not None:
            break
    if p.poll() is None:
        p.kill()
    os.close(master)
    _W["bare"] = (p.wait(), out.decode("utf-8", "replace"))
    return _W["bare"]


def clause_1() -> None:
    rc, said = _bare_under_a_pty()
    http = [ln for ln in said.splitlines() if "http" in ln]
    check("clause_1", rc == 0 and not http and "librarian" in said,
          f"rc={rc} http-lines={http!r} said={said[-800:]!r}")


def clause_2() -> None:
    _bare_under_a_pty()
    calls = _W["calls"].read_text().splitlines() if _W["calls"].exists() else []
    from urllib.parse import urlparse
    ok = len(calls) == 1 and urlparse(calls[0]).path == "/device/librarian"
    check("clause_2", ok, f"opener calls={calls!r}")


def clause_3() -> None:
    _bare_under_a_pty()
    r = subprocess.run([sys.executable, "-c",
                        "import sys\nfrom cairn.tools.base.shim import cli_main\n"
                        "from cairn.devices.librarian.shim import LibrarianShim\n"
                        "sys.exit(cli_main(LibrarianShim, ['start']))\n"],
                       env=_env(), cwd=str(REPO), capture_output=True, text=True, timeout=180)
    said = r.stdout + r.stderr
    check("clause_3", r.returncode == 0 and "already running" in said,
          f"rc={r.returncode} said={said[-600:]!r}")


def clause_4() -> None:
    text = LAUNCHER.read_text()
    found = [w for w in ("systemd-run", "setsid", "listener.py") if w in text]
    check("clause_4", not found, f"launcher still names {found}")


def clause_5() -> None:
    bad = []
    for name in STANDING:
        r = subprocess.run([sys.executable, str(PROOFS / name)], cwd=str(REPO),
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            bad.append(f"{name}: rc={r.returncode} {(r.stdout + r.stderr)[-400:]!r}")
    check("clause_5", not bad, "; ".join(bad))


def main() -> int:
    print("d832a24e5144 — a bare cairn librarian opens its chat and prints no URL")
    try:
        _world()
        for tooth in (clause_1, clause_2, clause_3, clause_4, clause_5):
            try:
                tooth()
            except Exception as exc:  # noqa: BLE001 — every tooth reports even when one raises
                check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    finally:
        _teardown()
    print(f"{'GREEN' if not FAILURES else 'RED'}: {len(FAILURES)} failing: {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

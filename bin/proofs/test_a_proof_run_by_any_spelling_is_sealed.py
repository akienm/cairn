"""PROOF for ticket dda0e72b9c67: a proof's isolation holds however it is invoked.

Measured 2026-11-18 on akiendelllinux: the live ~/.cairn/devices fixture folders of 11-13 and
11-16 were written by BARE proof runs (`timeout 300 python3 $p`, `env PYTHONPATH=. python3
<bus proof>`) that no text gate saw. Inside the tester's seal ~/.cairn is a swap (its own
st_dev); a `systemd-run --user` unit runs in the user manager's mount namespace and sees the
LIVE tree (dev 66306 against the swap's 50), while a setsid child stays in the seal.

This proof runs under the tester's seal (`bin/cairn test --seal <this file>`). It reads the
live tree from inside the seal through exactly the escape D6 closes for the loop: a
`systemd-run --user --wait --pipe` unit, which is read-only here (ls / stat).

  4. NO PROOF RUN WRITES LIVE ~/.cairn: a sealed run of a bus proof that makes fixture devices
     (test_mail_in_delivery_is_never_bounced) leaves the live ~/.cairn/devices listing (names
     + mtimes) identical before and after.
  5. A PROOF REFUSES TO RUN OUTSIDE THE SEAL (D5): a proof file (proofs/test_*.py) run bare
     OUTSIDE the seal (a user unit, the account's HOME, no CAIRN_TESTER_TEST_ID, no seal marker)
     that enters the scratch door exits nonzero naming the seal, and writes nothing: the marked
     folder it would make next under live ~/.cairn/devices does not appear.
  6. A LOOP A SEALED RUN SPAWNS STAYS IN THE SEAL (D6, cairn/tools/base/shim.py): inside the
     seal, with the account's HOME, ensure_ground_loop's loop is a process of this run's mount
     namespace whose ~/.cairn has the swap's st_dev, not the live one.

    bin/cairn test --seal bin/proofs/test_a_proof_run_by_any_spelling_is_sealed.py
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PROVES = {"dda0e72b9c67": {
    "1": "test_a_sealed_fixture_proof_leaves_live_cairn_as_it_was",
    "2": "test_a_run_outside_the_seal_refuses_and_writes_nothing",
    "3": "test_a_loop_a_sealed_run_spawns_sees_the_swap",
}, "973ead3631e1": {
    "1": "test_the_proof_reads_the_seal_without_reaching_into_the_tester",
}}

_TAG = f"{os.getpid()}"
_CAIRN = Path(os.path.expanduser("~/.cairn"))
_FIXTURE = ROOT / "cairn/devices/cairn/machines/bus/proofs/test_mail_in_delivery_is_never_bounced.py"
_LOOP_MODULE = "cairn.devices.cairn.machines.ground_loop"
_UNITS: list[str] = []
_PIDS: list[int] = []
_LIVE_LEFTOVERS: list[str] = []


def _outside(argv: list[str], env: dict[str, str] | None = None, timeout: int = 120):
    """Run argv in the user manager's namespace (outside bwrap), waiting for it, output piped."""
    unit = f"cairn-proof-dda0-{_TAG}-{len(_UNITS)}"
    _UNITS.append(unit)
    flags = [f"--setenv={k}={v}" for k, v in (env or {}).items()]
    return subprocess.run(["systemd-run", "--user", "--wait", "--pipe", "--quiet",
                           "--unit", unit, "-p", "CollectMode=inactive-or-failed", *flags, "--", *argv],
                          capture_output=True, text=True, timeout=timeout)


def _live_listing() -> list[str]:
    """The LIVE ~/.cairn/devices names + mtimes, read from outside the seal."""
    r = _outside(["python3", "-c",
                  "import os,json; d=os.path.expanduser('~/.cairn/devices'); "
                  "print(json.dumps(sorted([n, int(os.stat(os.path.join(d, n)).st_mtime)] "
                  "for n in os.listdir(d))))"])
    assert r.returncode == 0, f"could not read the live tree from outside the seal: {r.stderr[-300:]}"
    return [f"{n} {m}" for n, m in json.loads(r.stdout)]


def _live_dev() -> int:
    r = _outside(["python3", "-c", "import os; print(os.stat(os.path.expanduser('~/.cairn')).st_dev)"])
    assert r.returncode == 0, r.stderr[-300:]
    return int(r.stdout.strip())


def _require_the_seal() -> None:
    from cairn.devices.tester.isolation import inside_an_instance_seal
    assert inside_an_instance_seal() and os.environ.get("CAIRN_TESTER_TEST_ID"), \
        "this proof measures from inside the tester's seal: run it with bin/cairn test --seal"
    assert _live_dev() != os.stat(_CAIRN).st_dev, \
        "~/.cairn here has the live tree's st_dev: no swap is bound, so nothing below means anything"


def test_a_sealed_fixture_proof_leaves_live_cairn_as_it_was():
    _require_the_seal()
    before = _live_listing()
    r = subprocess.run([sys.executable, str(_FIXTURE)], cwd=str(ROOT), capture_output=True, text=True,
                       timeout=600, env={**os.environ, "PYTHONPATH": str(ROOT)})
    after = _live_listing()
    added = sorted(set(after) - set(before))
    gone = sorted(set(before) - set(after))
    assert not added and not gone, (f"the sealed run of {_FIXTURE.name} (rc {r.returncode}) changed live "
                                    f"~/.cairn/devices: added/touched {added[:6]}, removed {gone[:6]}")


_BARE = ("import os, sys; sys.path.insert(0, %r)\n"
         "from cairn.tools.scratch.scratch import scratch_dir\n"
         "scratch_dir('cairn-proof-dda0-bare-')\n"
         "d = os.path.join(os.path.expanduser('~/.cairn/devices'), %r)\n"
         "os.makedirs(d, exist_ok=True)\n"
         "print('WROTE', d)\n")


def test_a_run_outside_the_seal_refuses_and_writes_nothing():
    _require_the_seal()
    marked = f"testing-dda0-bare-{_TAG}"
    home = os.path.expanduser("~")
    # the unit is handed only what a bare shell would carry: the account HOME, PATH, the repo
    env = {"HOME": home, "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": str(ROOT)}
    from cairn.tools.scratch.scratch import scratch_dir
    bare = scratch_dir("cairn-proof-dda0-bare-") / "proofs" / "test_dda0_bare.py"   # a proof, by its file
    bare.parent.mkdir(parents=True)
    bare.write_text(_BARE % (str(ROOT), marked))
    r = _outside(["python3", str(bare)], env=env)
    listed = [line.split(" ")[0] for line in _live_listing()]
    if marked in listed or "WROTE" in r.stdout:
        _LIVE_LEFTOVERS.append(marked)
    assert marked not in listed, (f"a bare run outside the seal entered the scratch door and wrote live "
                                  f"~/.cairn/devices/{marked} (rc {r.returncode})")
    out = (r.stdout + r.stderr).lower()
    assert r.returncode != 0 and "seal" in out, (f"a bare run outside the seal was not refused by name: "
                                                 f"rc {r.returncode}, output {out[-300:]!r}")


def _loops_of_this_run() -> list[int]:
    me, test_id = os.getpid(), os.environ["CAIRN_TESTER_TEST_ID"]
    found = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit() or int(p.name) == me:
            continue
        try:
            cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            env = (p / "environ").read_bytes().split(b"\0")
        except OSError:
            continue
        if _LOOP_MODULE in cmd and f"CAIRN_TESTER_TEST_ID={test_id}".encode() in env:
            found.append(int(p.name))
    return found


def test_a_loop_a_sealed_run_spawns_sees_the_swap():
    _require_the_seal()
    unit = f"cairn-proof-dda0-loop-{_TAG}"
    _UNITS.append(unit)
    from cairn.tools.scratch.scratch import scratch_dir
    log = scratch_dir("cairn-proof-dda0-loop-") / "loop.log"
    lock_home = _CAIRN / "devices" / "cairn" / "0" / "machines" / "ground_loop"
    call = ("import json, sys; sys.path.insert(0, %r); from pathlib import Path; "
            "from cairn.tools.base.shim import ensure_ground_loop; "
            "print(json.dumps(ensure_ground_loop(home=Path(%r), log=Path(%r))))") % (str(ROOT), str(lock_home), str(log))
    r = subprocess.run([sys.executable, "-c", call], capture_output=True, text=True, timeout=60,
                       env={**os.environ, "CAIRN_GROUND_LOOP_UNIT": unit, "PYTHONPATH": str(ROOT)})
    assert r.returncode == 0, f"ensure_ground_loop crashed: {r.stderr[-400:]}"
    said = json.loads(r.stdout.strip().splitlines()[-1])
    pids: list[int] = []
    for _ in range(40):
        pids = _loops_of_this_run()
        if pids:
            break
        time.sleep(0.25)
    _PIDS.extend(pids)
    assert pids, (f"no ground loop carrying this run's id is a process this run can see: the spawn said "
                  f"{said} — a unit on the user manager runs outside the seal, on the live tree")
    my_ns, swap_dev = os.readlink("/proc/self/ns/mnt"), os.stat(_CAIRN).st_dev
    for pid in pids:
        ns = os.readlink(f"/proc/{pid}/ns/mnt")
        dev = os.stat(f"/proc/{pid}/root{_CAIRN}").st_dev
        assert ns == my_ns and dev == swap_dev, (f"loop pid {pid} (spawn said {said}) runs in mount namespace "
                                                 f"{ns}, ~/.cairn st_dev {dev}; this run's are {my_ns}, {swap_dev}")


def test_the_proof_reads_the_seal_without_reaching_into_the_tester():
    # 973ead3631e1: RULE 1 — this file tells a sealed run by the tester's env marker, never by
    # importing cairn.devices.tester; build_inspector's device-path check names no row for it
    from cairn.machines.build_inspector.inspector import encapsulation_breaches
    mine = Path(__file__).resolve().relative_to(ROOT).as_posix()
    rows = [b for b in encapsulation_breaches(str(ROOT)) if b["file"] == mine]
    assert not rows, f"{mine} breaches encapsulation: {rows}"


def _cleanup() -> None:
    for pid in _PIDS:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    for marked in _LIVE_LEFTOVERS:   # only the folder this proof named, only if it wrote it
        _outside(["python3", "-c", "import os, shutil; shutil.rmtree(os.path.join("
                  f"os.path.expanduser('~/.cairn/devices'), {marked!r}), ignore_errors=True)"])
    for u in _UNITS:
        for verb in ("stop", "reset-failed"):
            subprocess.run(["systemctl", "--user", verb, f"{u}.service"], capture_output=True, timeout=30)


def main() -> int:
    fails = 0
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    try:
        for name, fn in tests:
            try:
                fn()
                print(f"  ok   {name}")
            except Exception as exc:  # noqa: BLE001
                fails += 1
                print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    finally:
        _cleanup()
    print(f"\n{'GREEN' if not fails else 'RED'} — {len(tests) - fails}/{len(tests)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

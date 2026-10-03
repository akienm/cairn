"""THE WIRING NEEDS NO LOOP — ticket efb670ff1dd8 (2026-09-30).

bae622881f03 made the ground loop a heartbeat and nothing else, and left one thing standing:
``bus_client._wire`` still built a GroundLoop device inside every client (``connect_bus``,
``connect_system``, ``reach``). So there were two ground loops, the resident heartbeat and a
private one in each client, and the web server's start paid a whole old-style beat. This
proof holds the four clauses of the ticket's falsifier:

  (1) calling reach / connect_bus / connect_system never imports the old loop module
      (checked in a fresh subprocess, so nothing this runner imported can hide it);
  (2) connect_system returns a roster whose device list equals deviceness membership;
  (3) reach('ground_loop') wires delivery so a request answers, not a timeout: the heartbeat's
      page loads from disk like every other device's shim, with no loop handed to it;
  (4) loop.py and staleness.py do not exist, and the ticket's grep over cairn/, bin/ and
      skills/ *.py is empty;
  (5) the web server's start (listener.main) holds no ground_loop shim in its own roster — a
      held shim is pulsed with the roster, so holding the heartbeat's shim IS a private loop
      (FIXME 2, measured 2026-10-03: the hollow reverted listener.py and no tooth redded).

The grep's pattern is assembled from pieces, so this file is not its own hit. Every face is
called inside a tooth, never at import, so a build taken away reds teeth instead of crashing
the runner.

Run:  python3 cairn/tools/bus_client/proofs/test_the_wiring_needs_no_loop.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"efb670ff1dd8": {
    "1": "the three faces never import the old loop module",
    "2": "connect_system's roster lists exactly the deviceness members",
    "3": "reach of the heartbeat's own shim answers a request",
    "4": "loop.py and staleness.py are gone and nothing names them",
    "5": "the web server's start holds no heartbeat shim of its own",
}}
GL = _REPO / "cairn" / "devices" / "cairn" / "machines" / "ground_loop"
OLD_LOOP = "cairn.devices.cairn.machines.ground_loop." + "loop"
PATTERN = "|".join(["GroundLoop" + "Device", "ground_loop" + ".loop", "ground_loop" + ".staleness"])
FAILURES: list[str] = []


def ok(name: str, passed: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if passed else 'RED '} {name}")
    if detail:
        print(f"         -> {detail}")
    if not passed:
        FAILURES.append(f"{name}: {detail}")


_CHILD = f"""
import sys
sys.path.insert(0, {str(_REPO)!r})
from cairn.tools.bus_client import connect_bus, connect_system, reach
errors = []
for face, call in (("reach", lambda: reach()),
                   ("connect_bus", lambda: connect_bus(beat=False)),
                   ("connect_system", lambda: connect_system(beat=False))):
    try:
        call()
    except Exception as exc:
        errors.append(f"{{face}}: {{type(exc).__name__}}: {{exc}}")
print("LOADED" if {OLD_LOOP!r} in sys.modules else "ABSENT")
print("ERRORS", errors)
"""


def tooth_1(T) -> None:
    try:
        out = subprocess.run([sys.executable, "-c", _CHILD], capture_output=True, text=True,
                             timeout=300, cwd=str(_REPO))
        lines = out.stdout.strip().splitlines()
        ok(T["1"], out.returncode == 0 and "ABSENT" in lines and "ERRORS []" in lines,
           f"rc={out.returncode} stdout={lines[-2:]} stderr={out.stderr.strip()[-300:]}")
    except Exception as e:  # noqa: BLE001
        ok(T["1"], False, f"{type(e).__name__}: {e}")


def tooth_2(T) -> None:
    try:
        from cairn.tools.base.deviceness import fitted_device_ids
        from cairn.tools.bus_client import connect_system
        _bus, roster = connect_system(beat=False)
        names = [d.get("device") for d in roster.roster().get("devices", [])]
        want = sorted(fitted_device_ids())
        ok(T["2"], names == want,
           f"missing={sorted(set(want) - set(names))} extra={sorted(set(names) - set(want))}")
    except Exception as e:  # noqa: BLE001
        ok(T["2"], False, f"{type(e).__name__}: {e}")


def tooth_3(T) -> None:
    try:
        from cairn.tools.bus_client import reach
        bus = reach("ground_loop")
        reply = bus.request(sender="test_the_wiring_needs_no_loop", to="ground_loop",
                            verb="liveness", why="proof: the heartbeat's page answers over reach",
                            body={}, timeout=20.0)
        body = reply.get("body") or {}
        ok(T["3"], "verdict" in body, f"body keys={sorted(body)[:8]}")
    except Exception as e:  # noqa: BLE001
        ok(T["3"], False, f"{type(e).__name__}: {e}")


def tooth_4(T) -> None:
    gone = [p.name for p in (GL / "loop.py", GL / "staleness.py") if p.exists()]
    try:
        out = subprocess.run(["grep", "-rlE", PATTERN, "--include=*.py", "cairn", "bin", "skills"],
                             capture_output=True, text=True, timeout=120, cwd=str(_REPO))
        hits = [h for h in out.stdout.split() if h]
        ok(T["4"], not gone and not hits and out.returncode in (0, 1),
           f"still standing={gone} grep hits={len(hits)} {hits[:6]}")
    except Exception as e:  # noqa: BLE001
        ok(T["4"], False, f"{type(e).__name__}: {e}")


_CHILD_LISTENER = f"""
import sys
sys.path.insert(0, {str(_REPO)!r})
import cairn.devices.web_server.listener as listener
real = listener.connect_system
def recording(*, devices=None, beat=True):
    bus, roster = real(devices=devices, beat=False)
    print("HELD", sorted(roster.held))
    raise SystemExit(0)
listener.connect_system = recording
listener.main(["--port", "0"])
print("NEVER_WIRED")
"""


def tooth_5(T) -> None:
    try:
        out = subprocess.run([sys.executable, "-c", _CHILD_LISTENER], capture_output=True,
                             text=True, timeout=300, cwd=str(_REPO))
        held = [ln for ln in out.stdout.splitlines() if ln.startswith("HELD ")]
        ok(T["5"], out.returncode == 0 and len(held) == 1 and "'ground_loop'" not in held[0],
           f"rc={out.returncode} {held} stderr={out.stderr.strip()[-300:]}")
    except Exception as e:  # noqa: BLE001
        ok(T["5"], False, f"{type(e).__name__}: {e}")


def main() -> int:
    print("the wiring needs no loop")
    T = PROVES["efb670ff1dd8"]
    tooth_1(T)
    tooth_2(T)
    tooth_3(T)
    tooth_4(T)
    tooth_5(T)
    return _verdict()


def _verdict() -> int:
    print()
    if FAILURES:
        print(f"RED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("GREEN — no private loop, the roster is deviceness, reach answers, the loop is gone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

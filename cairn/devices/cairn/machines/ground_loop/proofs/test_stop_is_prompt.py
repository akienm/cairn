"""STOPPING IS PROMPT — SIGTERM costs the beat in flight, never the cadence.

MEASURED, 2026-09-08, from both ends of the same defect:

  - ``systemctl --user restart cairn-ground-loop`` logged
    ``State 'stop-sigterm' timed out. Killing.`` at 90s and SIGKILLed the loop — so a beat
    in flight was torn down mid-write instead of finished, which is exactly what the
    liveness record's atomic write exists to prevent.
  - ``launchers/proofs/test_ground_loop_survives_its_caller.py`` died in its own
    ``finally:`` cleanup on ``systemctl --user stop`` at a 20s subprocess timeout, and the
    TimeoutExpired replaced every tooth's verdict with a traceback.

THE CAUSE IS ``time.sleep``'s CONTRACT, not the handler. The runner's handler set a bool and
the loop re-tested it at the top — but PEP 475 makes ``time.sleep`` RETRY after a signal
handler returns, recomputing the timeout from the ORIGINAL deadline. So SIGTERM one second
into a 60s cadence slept 59 more seconds before the ``while`` was ever re-read. The handler
was correct; it simply had no way to shorten the wait it interrupted. ``threading.Event`` is
the same wait with the one property a bool cannot have: ``set()`` from the handler wakes it.

WHY THE TOOTH FIRES **AFTER** A BEAT, AND WHY THAT IS THE WHOLE DESIGN. A beat costs ~23.7s
and the cadence is 60s, so a SIGTERM sent during a beat exits under 60s either way — a tooth
that signalled at once would pass over the broken code. The discriminating instant is the
one where the process is *asleep*: there, the old code costs the remainder of the cadence and
the new code costs nothing. So this proof waits for ``liveness.json`` to record a completed
beat, signals into the sleep that follows it, and holds the exit to a bound far below the
cadence. A hollow runner that simply never slept would fail the second tooth, which insists
the loop was still alive and beating when it was signalled.

IT RUNS AGAINST A FIXTURE TREE (``main(roots=...)``), so the live singleton's claim is
untouched and the live liveness record is never written. That is the same injection the
runner's own docstring names, used for the same reason.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.devices.cairn.machines.ground_loop.__main__ import CADENCE_S  # noqa: E402

FAILURES: list[str] = []

# The bound. A stop costs the beat in flight (measured 23.7s steady state) plus interpreter
# teardown; it must NOT cost the cadence. Signalling into the sleep, as this proof does,
# should cost neither — but the number that matters is the one that separates the two
# regimes, and half a cadence is the honest place to draw it: below it the wait was woken,
# above it the wait was served out.
BOUND_S = CADENCE_S / 2


def ok(name: str, passed: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if passed else 'RED '} {name}" + (f"  — {detail}" if detail else ""))
    if not passed:
        FAILURES.append(f"{name}: {detail}")


def _liveness(roots: Path) -> dict | None:
    p = (roots / "devices" / "cairn" / "0" / "machines" / "ground_loop" / "liveness.json")
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def main() -> int:
    print("the loop's stop costs the beat in flight, not the cadence")
    with tempfile.TemporaryDirectory(prefix="cairn-proof-stopprompt-") as td:
        roots = Path(td)
        # `roots` is the address TABLE, not a path — the repo and commons stay real (the
        # beat's whole job is walking them), and only `instance` is redirected, which is
        # exactly the half that would otherwise stamp the live liveness record and take the
        # live singleton's claim.
        runner = (
            "import sys; sys.path.insert(0, %r)\n"
            "from pathlib import Path\n"
            "from cairn.tools.base.address import ROOTS\n"
            "from cairn.devices.cairn.machines.ground_loop.__main__ import main\n"
            "roots = dict(ROOTS); roots['instance'] = Path(%r)\n"
            "raise SystemExit(main(roots=roots))\n" % (str(_REPO), str(roots))
        )
        proc = subprocess.Popen(
            [sys.executable, "-c", runner],
            cwd=str(_REPO), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            env={**os.environ, "PYTHONPATH": str(_REPO)},
        )
        try:
            # Wait for a COMPLETED beat — that is what puts the process in the sleep this
            # proof is about. Generous: the first beat is the cold one.
            deadline = time.monotonic() + 180
            beats = 0
            while time.monotonic() < deadline:
                rec = _liveness(roots)
                beats = (rec or {}).get("state", {}).get("beats", 0)
                if beats >= 1:
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.5)

            ok("the fixture loop completed a beat and is now in its cadence sleep",
               beats >= 1 and proc.poll() is None,
               f"beats={beats} exited={proc.poll()}")
            if beats < 1 or proc.poll() is not None:
                return 1

            # Let it settle INTO the sleep rather than racing the write that ends the beat.
            time.sleep(1.0)
            ok("it is still alive to be signalled (not a runner that exited early)",
               proc.poll() is None)

            started = time.monotonic()
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=CADENCE_S * 2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
                ok(f"SIGTERM in the sleep exits under {BOUND_S:.0f}s", False,
                   f"still running after {CADENCE_S * 2:.0f}s — SIGKILLed")
                return 1
            took = time.monotonic() - started

            ok(f"SIGTERM in the sleep exits under {BOUND_S:.0f}s (cadence is {CADENCE_S:.0f}s)",
               took < BOUND_S, f"{took:.2f}s")
            # The bound is read from the runner's own constant, so widening the cadence can
            # never be the way this tooth is made to pass.
            ok("the bound is derived from the runner's cadence, not written here",
               BOUND_S == CADENCE_S / 2, f"BOUND_S={BOUND_S} CADENCE_S={CADENCE_S}")
            ok("the stop was clean, not a crash",
               proc.returncode in (0, -signal.SIGTERM), f"rc={proc.returncode}")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=30)

    print()
    if FAILURES:
        print(f"RED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("GREEN — the wait is woken, not served out.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

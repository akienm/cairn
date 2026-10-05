"""Proof for ticket 13b26f206519 — nothing in launchers reaches into a device.

RULE 1 (Akien, 2026-10-01): every component talks to every other only through its public
interface, and a device's is the bus plus any client tool it publishes. On 2026-10-05
encapsulation_breaches measured exactly one row from launchers:
launchers/proofs/test_ground_loop_survives_its_caller.py:59 imported CADENCE_S from the cairn
device's ground_loop/__main__. The ruled cadence now lives in the liveness tool (ticket
c3b14029d6d8), so launchers reads it there.

This proof measures only launchers (RULE 1: a ticket's proofs measure its own component).

  1. LAUNCHERS REACH INTO NO DEVICE. No encapsulation_breaches row has a file under launchers/.

    python3 launchers/proofs/test_launchers_reach_into_no_device.py   # exit 0 = green
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 900  # the sieve walks the whole import graph to find launchers' edges (ticket 8383a32d20c5)

PROVES = {"13b26f206519": {"1": "launchers_reach_into_no_device"}}

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def launchers_reach_into_no_device():
    import importlib
    breaches = importlib.import_module("cairn.machines.build_inspector.inspector").encapsulation_breaches
    rows = [b for b in breaches(str(_REPO_ROOT)) if str(b["file"]).startswith("launchers/")]
    assert not rows, f"{len(rows)} reach(es) from launchers: " + \
        "; ".join(f"{b['file']}:{b['line']} -> {b['module']}" for b in rows[:8])


TEETH = [launchers_reach_into_no_device]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

"""Proof for ticket c3b14029d6d8 — the liveness tool defines the ruled heartbeat cadence.

CADENCE_S = 60.0 is Akien's ruling (2026-08-22): the ground loop beats once per minute. It was
spelled inside the cairn device (ground_loop/__main__.py), so a component that needed the beat
interval had to reach into a device for it — a RULE 1 breach (Akien, 2026-10-01). The liveness
tool already defines staleness as five missed ticks at that cadence, so the cadence berths here,
beside the threshold it sets, and every component reads it through this tool's public interface.

This proof measures only the liveness tool (RULE 1: a ticket's proofs measure its own component).

  1. THE TOOL DEFINES THE RULED CADENCE. cairn.tools.liveness.liveness.CADENCE_S == 60.0.
  2. STALENESS IS FIVE TICKS OF IT. STALENESS_THRESHOLD_S == 5 * CADENCE_S.

    python3 cairn/tools/liveness/proofs/test_the_tool_defines_the_ruled_cadence.py   # exit 0 = green
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class _Late:
    """The build's names resolve AT CALL TIME, so `cairn test --hollow` taking the build away
    reads as red teeth rather than an import that never ran."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_liveness = _Late("cairn.tools.liveness.liveness")

PROVES = {"c3b14029d6d8": {"1": "the_tool_defines_the_ruled_cadence",
                           "2": "staleness_is_five_ticks_of_it"}}

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


def the_tool_defines_the_ruled_cadence():
    assert _liveness.CADENCE_S == 60.0, f"CADENCE_S is {_liveness.CADENCE_S!r}, the ruling is 60.0"


def staleness_is_five_ticks_of_it():
    assert _liveness.STALENESS_THRESHOLD_S == 5 * _liveness.CADENCE_S, \
        f"staleness {_liveness.STALENESS_THRESHOLD_S} is not five ticks of {_liveness.CADENCE_S}"


TEETH = [the_tool_defines_the_ruled_cadence, staleness_is_five_ticks_of_it]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

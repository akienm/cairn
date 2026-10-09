"""Proof: a ticket standing at PROVED can be superseded, and still cannot be dropped.

Ticket c63d2e99039e (2026-10-08). Akien approved three PROVED tickets crossing PROVED ->
SUPERSEDED (open-0d44f8905e2e, "both look good to me"), and the door refused the first:
"PROVED -> SUPERSEDED is illegal for code-seam@v2 (legal from here: ['BUILDME', 'PROVEME',
'THINKME', 'TICKETME', 'WATCHME'])". Superseding is not an alternative to completing the work
(the reason test_transitions.py gives for refusing a disposition from a rest): a later proved
ticket replaces a proved one. Dropping is that alternative, so it stays refused.

Teeth, one per falsifier clause:

  1. From [PROVED], emit to SUPERSEDED lands: the string ends '-> PROVED -> [SUPERSEDED]',
     the cursor reads SUPERSEDED, and the journal records PROVED -> SUPERSEDED with
     direction 'disposition'.
  2. From [PROVED], emit to DROPPED is still refused.

The fixture is 481221f45884's workflow string and a scratch_dir world for the journal; the node classes
are read where the hollow can reach them (beside the repo, else the home commons).

    python3 cairn/tools/base/proofs/test_a_proved_ticket_can_be_superseded.py   # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.base import transitions  # noqa: E402
from cairn.tools.charter import projector  # noqa: E402

PROVES = {
    "c63d2e99039e": {
        "1": "test_a_proved_ticket_crosses_to_superseded",
        "2": "test_a_proved_ticket_still_cannot_be_dropped",
    },
}

# `cairn test --hollow` runs these teeth in a /tmp worktree with no commons beside it.
_CLASSES = (transitions._NODE_CLASSES if transitions._NODE_CLASSES.is_dir()
            else Path.home() / "dev" / "src" / "CairnCommons" / "node_classes")
# 481221f45884's own string, so the predict reproduces its refusal word for word.
_AT_PROVED = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
              "WATCHME(first_seal_isolation) -> [PROVED]")


def test_a_proved_ticket_crosses_to_superseded():
    d = scratch_dir("proved-superseded-")
    hist, state = d / "history.json", d / "state.json"
    new = transitions.emit(_AT_PROVED, "SUPERSEDED", history_path=str(hist),
                           state_path=str(state), node_class_root=_CLASSES)
    assert new.endswith("-> PROVED -> [SUPERSEDED]"), f"SUPERSEDED did not land after PROVED: {new}"
    assert transitions.parse_workflow(new).here == "SUPERSEDED", new
    rec = projector.read_history(str(hist))[-1]
    assert (rec["from"], rec["to"], rec["direction"]) == ("PROVED", "SUPERSEDED", "disposition"), rec


def test_a_proved_ticket_still_cannot_be_dropped():
    d = scratch_dir("proved-dropped-")
    try:
        transitions.emit(_AT_PROVED, "DROPPED", history_path=str(d / "history.json"),
                         state_path=str(d / "state.json"), node_class_root=_CLASSES)
    except transitions.IllegalTransition:
        assert not (d / "history.json").exists(), "a refused DROPPED journaled a crossing"
        return
    raise AssertionError("PROVED -> DROPPED landed: dropping is an alternative to completing, "
                         "and a proved ticket has completed")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

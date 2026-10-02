"""Proof: the workflow grammar knows FIXME — a ticket sent back to design, and held there.

Ticket 72d2f79daf0a (Akien, 2026-10-01, foreground item 1): "it becomes open work in
deisgn. it goes back to ticketing for improvement." / "FIXME. that's approved thru PROVED".
code-seam v2 declares ``repair_summons: {"FIXME": "BUILDME"}`` — FIXME is not on the
backbone; a back-edge from BUILDME or later inserts it immediately before BUILDME, and the
forward crossing out of it is refused while any entry of the ticket's ``fixme`` list has no
``FIXME <n>`` decision.

Teeth, one per falsifier clause:

  1. A back-edge into FIXME from PROVEME lands at FIXME placed before BUILDME, and the
     crossing's record journals the ``missing`` list.
  2. FIXME -> BUILDME is refused while a ``fixme`` entry is unanswered.
  3. It is admitted once every entry is answered (the FIXME gate called directly: the
     BUILDME entry gate behind it reds any fixture ticket that has no chart).
  4. A v2 string without FIXME conforms and keeps exactly the legal targets it had.

The fixture node-class root is a COPY of the live code-seam.json with the declaration set in
the copy, so the proof measures the reader, not whether the live write has landed. Every
build name is resolved inside its tooth, so a reverted build reds teeth instead of crashing
the import.

    python3 cairn/tools/base/proofs/test_fixme.py   # exit 0 = green
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.base import transitions  # noqa: E402

PROVES = {
    "72d2f79daf0a": {
        "1": "test_a_back_edge_lands_at_fixme_before_buildme",
        "2": "test_fixme_refuses_exit_while_an_entry_is_unanswered",
        "3": "test_fixme_admits_exit_once_every_entry_is_answered",
        "4": "test_a_v2_string_without_fixme_is_unchanged",
    },
}

# The live class, read where hollow.py reads the commons: beside the repo when it is there, else
# at the home path — `cairn test --hollow` runs these teeth in a /tmp worktree with no commons
# beside it, where the repo-relative path alone reads nothing and every tooth reds at HEAD.
_COMMONS_CLASSES = (transitions._NODE_CLASSES if transitions._NODE_CLASSES.is_dir()
                    else Path.home() / "dev" / "src" / "CairnCommons" / "node_classes")
_LIVE_CLASS = _COMMONS_CLASSES / "code-seam.json"
_AT_PROVEME = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
_AT_FIXME = "code-seam@v2: THINKME -> TICKETME -> [FIXME] -> BUILDME -> PROVEME -> PROVED"
_NAME = "fixme_fixture_ticket"


def _class_def() -> dict:
    d = json.loads(_LIVE_CLASS.read_text(encoding="utf-8"))
    d["workflow_versions"]["v2"]["repair_summons"] = {"FIXME": "BUILDME"}
    return d


def _class_root() -> Path:
    root = scratch_dir("fixme_fixture_node_classes_")
    (root / "code-seam.json").write_text(json.dumps(_class_def(), indent=2), encoding="utf-8")
    return root


def _component() -> tuple[str, str]:
    # NESTED ONE LEVEL, as test_emission_gate's _cross explains: the build gate censuses
    # the parent of the directory holding history.json, which must be the fixture's own.
    comp = scratch_dir("fixme_fixture_component_") / "comp"
    comp.mkdir()
    return str(comp / "history.json"), str(comp / "state.json")


class _Corpus:
    """Repoint the gate's ticket corpus at one fixture ticket for the length of a tooth."""

    def __init__(self, body: dict):
        self._body = body

    def __enter__(self):
        d = scratch_dir("fixme_fixture_tickets_")
        (d / f"{_NAME}.json").write_text(json.dumps(self._body), encoding="utf-8")
        self._saved = transitions._TICKETS
        transitions._TICKETS = d
        return d

    def __exit__(self, *a):
        transitions._TICKETS = self._saved
        return False


def test_a_back_edge_lands_at_fixme_before_buildme():
    from cairn.tools.base.transitions import emit, parse_workflow
    from cairn.tools.charter import projector
    hist, state = _component()
    missing = ["the receiver is unnamed"]
    new = emit(_AT_PROVEME, "FIXME", history_path=hist, state_path=state,
               node_class_root=_class_root(), ticket=_NAME, missing=missing)
    wf = parse_workflow(new)
    assert wf.here == "FIXME", new
    assert wf.cursor == wf.path.index("BUILDME") - 1, new
    last = projector.read_history(hist)[-1]
    assert last.get("missing") == missing, last
    assert last.get("direction") == "back", last


def test_fixme_refuses_exit_while_an_entry_is_unanswered():
    from cairn.tools.base.transitions import FixmeGateRed, emit
    hist, state = _component()
    body = {"fixme": ["a", "b"], "decisions": [{"step": "FIXME 1", "text": "answered"}]}
    with _Corpus(body):
        try:
            emit(_AT_FIXME, "BUILDME", history_path=hist, state_path=state,
                 node_class_root=_class_root(), ticket=_NAME)
        except FixmeGateRed as e:
            assert "2" in str(e), f"the refusal must name the unanswered entry: {e}"
            return
    raise AssertionError("FIXME -> BUILDME crossed with entry 2 unanswered")


def test_fixme_admits_exit_once_every_entry_is_answered():
    from cairn.tools.base.transitions import _fixme_gate
    body = {"fixme": ["a", "b"], "decisions": [{"step": "FIXME 1", "text": "answered"},
                                               {"step": "FIXME 2", "text": "answered too"}]}
    with _Corpus(body):
        note, record = _fixme_gate(_NAME)
    assert record and all(r.get("expected") == r.get("actual") for r in record), record


def test_a_v2_string_without_fixme_is_unchanged():
    from cairn.tools.base.transitions import legal_targets, parse_workflow
    with_fix = _class_def()
    without = copy.deepcopy(with_fix)
    del without["workflow_versions"]["v2"]["repair_summons"]
    path = with_fix["workflow_versions"]["v2"]["path"]
    for i in range(len(path)):
        s = "code-seam@v2: " + " -> ".join(f"[{p}]" if j == i else p for j, p in enumerate(path))
        wf = parse_workflow(s)
        assert legal_targets(wf, class_def=with_fix) == legal_targets(wf, class_def=without), s


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

"""Proof for ticket c01503edd010 — the PROVEME door refuses a proof name that resolves to no file.

Measured 2026-10-07 on 41202d4c8d3b: its PROVEME crossing named proven_by
``test_sail_sweeps_the_tree_first.py`` — a bare name, no file at the cairn root — and the
proof-named seat recorded "clean — proof named". PROVED reads a name the way
``proof_coverage.lacks`` does (absolute as is, else the cairn root / name) and would have
refused it as [proof_on_disk], by which time the only repair was a kick-back.

Three teeth, one per falsifier clause:
  (1) a bare name that resolves to no file is refused by name, nothing written;
  (2) a real path crosses, repo-relative or absolute; a mixed list names only the dead one;
  (3) a dead name on a crossing since the latest forward BUILDME is refused too — the
      union is what PROVED reads.

THE FIXTURE: as in test_proveme_names_its_proof.py, ``transitions._entry_gate`` and
``transitions._stamp_sail`` are pretended (the seat sits after the entry gate, and a
fixture ticket must not claim the live sail record). The node-class table is copied
into a scratch dir and passed as ``node_class_root`` (F18: the hollow's worktree has no
CairnCommons beside it). Tooth 3 substitutes the READ the union rests on —
``crossings.ROOTS`` — with a fixture world, restored in ``finally``.

``ProofNamedRed`` and ``inspect_proof_named`` are bound at CALL time, so a reverted
transitions.py reds the teeth instead of breaking the runner at import.

Run:
    PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_dead_proof_name_is_refused_at_proveme.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import crossings, transitions  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "c01503edd010": {
        "1": "test_a_bare_name_that_resolves_to_no_file_is_refused",
        "2": "test_a_real_path_crosses_and_a_mixed_list_names_only_the_dead",
        "3": "test_a_dead_name_since_buildme_is_refused",
    },
}

_AT_BUILDME = "bug@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"
_FIXTURE_TICKET = "fixture-c015-dead-proof-name-no-journal-carries-this-id"
_LANE = "the_proveme_crossing_names_its_proof"
_THIS_PROOF = "cairn/tools/base/proofs/test_a_dead_proof_name_is_refused_at_proveme.py"
_BARE = Path(_THIS_PROOF).name          # exists in proofs/, never at the cairn root: the 8y shape
_GONE = "p/gone-c015-this-proof-names-no-file.py"

_LIVE_NODE_CLASSES = next((c / "node_classes" for c in (_REPO_ROOT.parent / "CairnCommons",
                                                        Path.home() / "dev" / "src" / "CairnCommons")
                           if (c / "node_classes" / "bug.json").is_file()), None)


def _node_classes() -> Path:
    assert _LIVE_NODE_CLASSES is not None, "no CairnCommons/node_classes beside the repo or under $HOME"
    root = scratch_dir("dead-proof-name-node-classes-") / "node_classes"
    root.mkdir()
    (root / "bug.json").write_bytes((_LIVE_NODE_CLASSES / "bug.json").read_bytes())
    return root


class _PretendCharted:
    """Pretend the fixture ticket is charted and keep the live sail record untouched."""

    def __enter__(self):
        self._saved = (transitions._entry_gate, transitions._stamp_sail)
        transitions._entry_gate = lambda _t: ("clean — fixture chart", [])
        transitions._stamp_sail = lambda _t, _s: None
        return self

    def __exit__(self, *_exc):
        transitions._entry_gate, transitions._stamp_sail = self._saved
        return False


def _component(prefix: str) -> tuple[str, str]:
    comp = scratch_dir(prefix) / "fixture_component"
    comp.mkdir()
    return str(comp / "history.json"), str(comp / "state.json")


def _cross(hist: str, state: str, proven_by, classes: Path) -> str:
    with _PretendCharted():
        return transitions.emit(_AT_BUILDME, "PROVEME", history_path=hist, state_path=state,
                                ticket=_FIXTURE_TICKET, actor="proof", note="c015 fixture",
                                proven_by=proven_by, node_class_root=classes)


def _refused(proven_by, classes: Path, prefix: str) -> Exception:
    red = getattr(transitions, "ProofNamedRed", None)
    assert red is not None, "transitions.py carries no ProofNamedRed — the seat is not built"
    hist, state = _component(prefix)
    try:
        _cross(hist, state, proven_by, classes)
    except red as e:
        assert not Path(hist).exists(), "a REFUSED crossing must write no record of truth"
        assert not Path(state).exists(), "a REFUSED crossing must write no state"
        assert "proven_by" in str(e) and _FIXTURE_TICKET in str(e), \
            f"the refusal names proven_by and the ticket: {e}"
        lanes = [f for f in getattr(e, "findings", []) if f.get("method") == _LANE]
        assert len(lanes) == 1 and lanes[0]["expected"] != lanes[0]["actual"], e.findings
        return e
    raise AssertionError(f"a PROVEME crossing naming {proven_by!r} crossed ungated")


def _lane(proven_by) -> dict:
    inspect = getattr(transitions, "inspect_proof_named", None)
    assert inspect is not None, "transitions.py carries no inspect_proof_named"
    record = inspect(_FIXTURE_TICKET, {"proven_by": proven_by})
    assert len(record) == 1 and record[0]["identity"] == _LANE, \
        f"the seat stays ONE lane (7203's sealed proof counts it): {record}"
    return record[0]


def _no_live_journal_carries_the_fixture():
    assert crossings.proven_by_since_buildme(_FIXTURE_TICKET) == [], \
        "the fixture ticket id is carried by a live journal — pick another"


def test_a_bare_name_that_resolves_to_no_file_is_refused():
    _no_live_journal_carries_the_fixture()
    assert not (_REPO_ROOT / _BARE).exists() and (_REPO_ROOT / _THIS_PROOF).is_file()
    e = _refused(_BARE, _node_classes(), "dead-proof-name-bare-")
    assert _BARE in str(e) and "no file" in str(e), f"the refusal names the dead name: {e}"
    lane = _lane(_BARE)
    assert lane["expected"] != lane["actual"], lane
    assert lane["values"].get("dead") == [{"name": _BARE, "from": "this crossing"}], lane["values"]


def test_a_real_path_crosses_and_a_mixed_list_names_only_the_dead():
    _no_live_journal_carries_the_fixture()
    classes = _node_classes()
    for name, prefix in ((_THIS_PROOF, "dead-proof-name-relative-crosses-"),
                         (str(_REPO_ROOT / _THIS_PROOF), "dead-proof-name-absolute-crosses-")):
        hist, _state = _component(prefix)
        new = _cross(hist, _state, name, classes)
        assert transitions.parse_workflow(new).here == "PROVEME", new
        rec = json.loads(Path(hist).read_text())
        rec = (rec.get("entries") or rec.get("crossings") or rec.get("history")) if isinstance(rec, dict) else rec
        lanes = [f for f in rec[-1]["proved"] if f.get("identity") == _LANE]
        assert len(lanes) == 1 and lanes[0]["expected"] == lanes[0]["actual"], lanes
        assert lanes[0]["values"].get("dead") == [], lanes[0]["values"]
    e = _refused([_THIS_PROOF, _GONE], classes, "dead-proof-name-mixed-list-")
    assert _GONE in str(e), f"the refusal names the dead one: {e}"
    assert _lane([_THIS_PROOF, _GONE])["values"].get("dead") == [{"name": _GONE, "from": "this crossing"}]


def test_a_dead_name_since_buildme_is_refused():
    world = scratch_dir("dead-proof-name-since-buildme-world-")
    repo, commons = world / "repo", world / "commons"
    (repo / "fx").mkdir(parents=True)
    commons.mkdir()
    (repo / "fx" / "history.json").write_text(json.dumps({"entries": [{
        "from": "TICKETME", "to": "BUILDME", "direction": "forward", "ticket": _FIXTURE_TICKET,
        "proven_by": _GONE, "at": "2026-01-01T10:00:00", "seq": 1}]}))
    saved = crossings.ROOTS
    crossings.ROOTS = {"repo": repo, "commons": commons}
    crossings._CACHE.clear()
    try:
        assert crossings.proven_by_since_buildme(_FIXTURE_TICKET) == [_GONE], \
            "the fixture world's BUILDME crossing does not reach the union"
        e = _refused(_THIS_PROOF, _node_classes(), "dead-proof-name-since-buildme-")
        assert _GONE in str(e), f"the refusal names the dead name from the union: {e}"
        assert _lane(_THIS_PROOF)["values"].get("dead") == [{"name": _GONE, "from": "since BUILDME"}]
    finally:
        crossings.ROOTS = saved
        crossings._CACHE.clear()


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

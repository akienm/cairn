"""Teeth for ticket 11cd253f10bc — a crossing into PROVEME refuses while either tree is dirty.

A forward crossing INTO PROVEME that journals (history_path and state_path given) runs the
build_inspector's working_tree_clean sieve over the crossing component: the repo holding it
and that repo's sibling CairnCommons (c1cca2e3dc23). Any uncommitted change in either tree
refuses the crossing with ``WorkingTreeDirtyRed`` naming every dirty path, BEFORE anything is
written; both clean, the crossing lands and its record carries a ``working_tree_clean`` lane; a dir
NO repo holds crosses with no lane and ``tree_gate`` "not_checked: no git repo holds <dir>" (F16).
Ruling 8t survives here and at /sail's clean start (92e0d158b1bc); cleared by Akien (8x).

Hermetic: each tooth builds <tmp>/cairn (holding comp/ with its charter, history.json and
state.json) and a sibling <tmp>/CairnCommons under scratch_dir, both committed clean with an
inline identity, and crosses ticketless — no live journal, chart or sail record is read.
``WorkingTreeDirtyRed`` is looked up at CALL time, so a reverted transitions.py reds the
teeth instead of breaking the runner at import.

Run:
    PYTHONPATH=. python3 cairn/tools/base/proofs/test_proveme_entry_needs_a_clean_tree.py   # exit 0 = green
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 120

from cairn.tools.base import transitions  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "11cd253f10bc": {
        "1": "test_dirt_in_cairn_outside_the_component_refuses_and_writes_nothing",
        "2": "test_dirt_only_in_the_commons_refuses_naming_it",
        "3": "test_both_trees_clean_cross_with_a_working_tree_clean_lane",
        "4": "test_a_dir_no_repo_holds_crosses_not_checked_with_no_lane",
    },
}

_AT_BUILDME = "bug@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True).stdout


def _world() -> tuple[Path, Path, Path]:
    """<tmp>/cairn holding comp/, and <tmp>/CairnCommons beside it — both committed clean."""
    tmp = scratch_dir("proveme-entry-clean-tree-proof-")
    cairn, commons = tmp / "cairn", tmp / "CairnCommons"
    comp = cairn / "comp"
    comp.mkdir(parents=True)
    (comp / "intention+why.json").write_text(json.dumps({"component": "comp"}) + "\n")
    (comp / "history.json").write_text("[]\n")
    (comp / "state.json").write_text("{}\n")
    (cairn / "kept.txt").write_text("cairn committed\n")
    commons.mkdir()
    (commons / "ledger.txt").write_text("commons committed\n")
    for repo in (cairn, commons):
        _git(repo, "init", "-q")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "init")
    return cairn, commons, comp


def _cross(comp: Path, note: str) -> str:
    return transitions.emit(_AT_BUILDME, "PROVEME", history_path=str(comp / "history.json"),
                            state_path=str(comp / "state.json"), actor="proof", note=note)


def _refused_naming(comp: Path, repo: Path, rel: str) -> None:
    red = getattr(transitions, "WorkingTreeDirtyRed", None)
    assert red is not None, "transitions.py carries no WorkingTreeDirtyRed — the seat is not built"
    assert issubclass(red, transitions.IllegalTransition) and red is not transitions.IllegalTransition
    before = {n: (comp / n).read_bytes() for n in ("history.json", "state.json")}
    try:
        _cross(comp, f"dirty: {rel}")
    except red as e:
        assert rel in str(e) and str(repo) in str(e), f"the refusal must name {rel} under {repo}: {e}"
        assert e.findings and e.findings[0].get("method") == "working_tree_clean", e.findings
    else:
        raise AssertionError(f"a PROVEME crossing with {rel} uncommitted crossed ungated")
    after = {n: (comp / n).read_bytes() for n in ("history.json", "state.json")}
    assert after == before, "a REFUSED crossing must leave history.json and state.json byte-unchanged"


def test_dirt_in_cairn_outside_the_component_refuses_and_writes_nothing():
    cairn, _commons, comp = _world()
    (cairn / "loose.txt").write_text("untracked, outside comp/\n")
    _refused_naming(comp, cairn, "loose.txt")


def test_dirt_only_in_the_commons_refuses_naming_it():
    _cairn, commons, comp = _world()
    (commons / "ledger.txt").write_text("commons modified\n")
    _refused_naming(comp, commons, "ledger.txt")


def test_both_trees_clean_cross_with_a_working_tree_clean_lane():
    _cairn, _commons, comp = _world()
    new = _cross(comp, "both clean")
    assert transitions.parse_workflow(new).here == "PROVEME", new
    rec = json.loads((comp / "history.json").read_text())[-1]
    assert rec["to"] == "PROVEME", rec
    lanes = [f for f in rec["proved"] if f.get("identity") == "working_tree_clean"]
    assert len(lanes) == 1, f"exactly one working_tree_clean lane on the record: {rec['proved']}"
    assert lanes[0]["expected"] == lanes[0]["actual"], lanes[0]


def test_a_dir_no_repo_holds_crosses_not_checked_with_no_lane():
    """F16: a dir NO repo holds has nothing to commit into — the seat writes no lane (a pass over
    input it never read is the vacuous green 316b named) and records why it did not check."""
    comp = scratch_dir("proveme-entry-no-repo-proof-") / "comp"
    comp.mkdir()
    assert not any((d / ".git").exists() for d in (comp, *comp.parents)), \
        f"the fixture must sit under no repo at all: {comp}"
    (comp / "history.json").write_text("[]\n")
    (comp / "state.json").write_text("{}\n")
    new = _cross(comp, "no repo")
    assert transitions.parse_workflow(new).here == "PROVEME", new
    rec = json.loads((comp / "history.json").read_text())[-1]
    assert not [f for f in rec["proved"] if f.get("identity") == "working_tree_clean"], \
        f"no repo was read, so no working_tree_clean lane may stand: {rec['proved']}"
    assert str(rec.get("tree_gate", "")).startswith("not_checked: no git repo holds"), rec


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))

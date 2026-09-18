"""Proof for ticket c2460ae6c3d1 — a PROVED crossing closes over PUSHED stones.

The falsifier is one unnumbered clause, so one composite tooth (PROVES keys follow the
falsifier markers): the exit gate's second lane, ``the_stones_are_pushed``, refuses a
forward crossing into PROVED when a repo the crossing's own records live in is ahead of
its upstream — naming the repo, the count and the push — writes nothing, and ledgers the
refusal; a crossing over pushed stones lands with the lane clean and the working-tree
dirt journaled, never refused; a root with no ``.git`` above it and a repo with no
upstream are journaled as unmeasured, never refused; and the measurement is
``cairn.tools.orient.orient.repo_truth`` COMPOSED by import, never a second ``git``
shelled from transitions.py.

THE FIXTURE (D5): two real git repos with bare origins inside one tempdir — ``code``
(holding the fixture component whose ``history.json`` the crossing writes) and
``commons`` (holding ``tickets/widget.json`` and the chart berths in
``test_transitions._exit_world``'s shape, with an answering verdict so the chart lane is
clean and ONLY the durability lane decides). The chokepoint globals ``_TICKETS`` and
``build_inspector._CHART_BERTHS`` are repointed at the fixture; ``_stamp_sail`` and
``_ledger_durability_refusal`` are replaced by stubs that RECORD their calls (a fixture
ticket must not claim the live sail record, and the live refusal ledger is what the
WATCHME probe reads for the first REAL bite). All restored in ``finally``. The lane, the
gate, the red class, the clearance witness and the history write are all REAL.

``inspect_durability`` is bound at CALL time via getattr, so a hollow reversion of
transitions.py reds this tooth instead of crashing the runner at import.

Run:
    PYTHONPATH=. python3 cairn/tools/base/proofs/test_the_stones_are_pushed.py   # exit 0 = green
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.tools.base import transitions  # noqa: E402
from cairn.tools.charter import projector  # noqa: E402

PROVES = {"c2460ae6c3d1": {"all": "test_a_proved_crossing_over_unpushed_stones_is_refused_and_dirt_is_journaled"}}

_AT_LEARN = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> [LEARNME] -> PROVED"
_LANE = "the_stones_are_pushed"
_FIXTURE_SEAL_DATE = "2026-08-10T00:00:00"

# THE NODE-CLASS TABLE IS THE ONE THING THE FIXTURE BORROWS FROM THE LIVE COMMONS, and it is
# borrowed by COPY, never by path. `cairn test --hollow` runs this tooth from a git worktree
# under /tmp with no CairnCommons beside it, so transitions' repo-relative _NODE_CLASSES points
# at nothing there (measured 2026-09-18: "unknown node-class 'code-seam'" at HEAD inside the
# hollow worktree, green everywhere else). The table is live SPEC, not live state — copying
# code-seam.json into the fixture commons and handing emit `node_class_root=` keeps the
# crossing off every live path. Resolution order is hollow.py's own: beside the repo, else $HOME.
_LIVE_NODE_CLASSES = next((c / "node_classes" for c in (_REPO.parent / "CairnCommons",
                                                        Path.home() / "dev" / "src" / "CairnCommons")
                           if (c / "node_classes" / "code-seam.json").is_file()), None)

_ANSWERED = {
    "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                  "evidence": "seen: exit 0 twice",
                  "discriminating_observation": "reverted the fix; the instrument exits 1"}],
    "dispositions": [{"piece": "p1", "expect": "e1", "disposition": "confirmed",
                      "by": "the run observed"}],
}


def _git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", *a],
                          cwd=str(cwd), check=True, capture_output=True, text=True).stdout


def _repo(root: Path, name: str) -> Path:
    """A working repo with one pushed commit and a bare 'origin' beside it."""
    work = root / name
    bare = root / (name + ".git")
    work.mkdir()
    bare.mkdir()
    _git(bare, "init", "--bare", "-q")
    _git(work, "init", "-q", "-b", "main")
    (work / "README").write_text(name + "\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "seed")
    _git(work, "remote", "add", "origin", str(bare))
    _git(work, "push", "-q", "-u", "origin", "main")
    return work


def _berths(commons: Path) -> Path:
    """The chart berths of test_transitions._exit_world's shape, answered, under the commons."""
    packets = commons / "berths" / "0" / "packets"
    packets.mkdir(parents=True)
    hyp = packets / "hypothesize-20260729T000000-feed.json"
    hyp.write_text(json.dumps({"hypotheses": [
        {"piece": "p1", "expect": "e1", "falsifier": "f", "instrument": "i"}]}))
    val = packets / "validate-20260729T000001-feed.json"
    val.write_text(json.dumps({"ticket": "widget", "hypothesize_ref": str(hyp),
                               "criteria": [{"claim": "c1", "instrument": "cmd", "covers": ["p1"]}]}))
    (packets / "verdict-20260729T000002-feed.json").write_text(json.dumps(
        {"ticket": "widget", "validate_ref": str(val), **_ANSWERED}))
    return commons / "berths"


def _cleared(d: Path, **extra) -> dict:
    """Copied from test_transitions._cleared: a REAL seal minted in the fixture's tempdir, so
    the clearance gate's re-read of the world passes and the durability lane alone decides."""
    from cairn.devices.tester.validation_store import persist_validation, source_fingerprint
    proof = d / "proofs" / "sealed_fixture.py"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("# a real source file, so the fingerprint is a real fingerprint\n")
    persist_validation({
        "claim": "the fixture component's code is proven",
        "caller": "cairn/tools/base/proofs/test_the_stones_are_pushed.py",
        "date": _FIXTURE_SEAL_DATE,
        "method": "fixture seal — the trail is real, the code it seals is a stub",
        "verdict": "green",
        "evidence": {"source_fingerprint": source_fingerprint(str(proof)), "teeth_green": ["test_the_fixture"]},
        "falsifier": "the component's source fingerprint moves",
        "horizon": "until any .py under the component root changes",
    }, proof_path=str(proof))
    return {"cleared_by": "fixture-owner", "proven_by": str(proof),
            "proven_seal_date": _FIXTURE_SEAL_DATE, **extra}


def _node_classes(commons: Path) -> Path:
    """The fixture commons' own node-class table: code-seam.json copied from the live spec."""
    assert _LIVE_NODE_CLASSES is not None, "no CairnCommons/node_classes beside the repo or under $HOME"
    root = commons / "node_classes"
    root.mkdir(exist_ok=True)
    (root / "code-seam.json").write_bytes((_LIVE_NODE_CLASSES / "code-seam.json").read_bytes())
    return root


def _cross(comp: Path, witness: dict, node_class_root: Path) -> tuple[str, str, str]:
    hist, state = str(comp / "history.json"), str(comp / "state.json")
    new = transitions.emit(_AT_LEARN, "PROVED", history_path=hist, state_path=state,
                           ticket="widget", node_class_root=node_class_root, **witness)
    return new, hist, state


def _lane_of(rec: dict) -> dict:
    lanes = [f for f in rec["proved"] if f.get("identity") == _LANE]
    assert len(lanes) == 1, f"exactly one durability lane on the record: {rec['proved']}"
    return lanes[0]


def _reading(lane: dict, **match) -> dict:
    hits = [r for r in lane["values"]["repos"] if all(r.get(k) == v for k, v in match.items())]
    assert len(hits) == 1, f"one reading matching {match}: {lane['values']['repos']}"
    return hits[0]


def test_a_proved_crossing_over_unpushed_stones_is_refused_and_dirt_is_journaled():
    inspect = getattr(transitions, "inspect_durability", None)
    assert inspect is not None, "transitions.py carries no inspect_durability — the lane is not built"
    import cairn.machines.build_inspector.inspector as _insp

    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        code = _repo(base, "code")
        commons = _repo(base, "commons")
        (commons / "tickets").mkdir()
        (commons / "tickets" / "widget.json").write_text("{}")
        classes = _node_classes(commons)
        berths = _berths(commons)
        comp = code / "fixture_component"
        comp.mkdir()
        witness = _cleared(comp)

        saved = (transitions._TICKETS, _insp._CHART_BERTHS,
                 transitions._stamp_sail, transitions._ledger_durability_refusal)
        ledgered: list[dict] = []
        transitions._TICKETS, _insp._CHART_BERTHS = commons / "tickets", berths
        transitions._stamp_sail = lambda _t, _s: None
        transitions._ledger_durability_refusal = lambda entry: ledgered.append(entry)
        try:
            # (a) one commit in 'code' not pushed -> refused by name, nothing written, ledgered once
            (code / "stone").write_text("unpushed\n")
            _git(code, "add", "-A")
            _git(code, "commit", "-q", "-m", "unpushed")
            hist_a, state_a = str(comp / "history.json"), str(comp / "state.json")
            try:
                _cross(comp, witness, classes)
            except transitions.ExitGateRed as e:
                msg = str(e)
                for needle in ("code", "1 commit(s) ahead", "git -C", "Law 8"):
                    assert needle in msg, f"the refusal must name {needle!r}: {msg}"
                lanes = [f for f in getattr(e, "findings", []) if f.get("method") == _LANE]
                assert len(lanes) == 1, f"the refusal carries exactly one durability lane: {e.findings}"
                assert not [f for f in e.findings if f.get("method") == "the_claiming_chart_is_answered"], \
                    f"the chart lane must be clean — only durability decides here: {e.findings}"
            else:
                raise AssertionError("a PROVED crossing over an unpushed commit crossed ungated")
            assert not Path(hist_a).exists(), "a REFUSED crossing must write no record of truth"
            assert not Path(state_a).exists(), "a REFUSED crossing must write no state"
            assert len(ledgered) == 1 and ledgered[0]["ticket"] == "widget", ledgered
            assert any(r.get("repo") == "code" and r.get("ahead_of_upstream") == 1
                       for r in ledgered[0]["repos"]), ledgered[0]
            direct = inspect("widget", history_path=hist_a)
            assert len(direct) == 1 and direct[0]["expected"] != direct[0]["actual"], direct
            assert direct[0]["code"] == "transitions.py::inspect_durability", direct[0]

            # (b) push, then untracked dirt -> lands; the lane is clean and the dirt is journaled
            _git(code, "push", "-q")
            (code / "dirt").write_text("untracked\n")
            new, hist, _ = _cross(comp, witness, classes)
            assert "[PROVED]" in new, new
            rec = projector.read_history(hist)[-1]
            assert rec["exit_gate"].startswith("clean —") and "stones pushed:" in rec["exit_gate"], rec["exit_gate"]
            lane = _lane_of(rec)
            assert lane["expected"] == lane["actual"], lane
            r_code = _reading(lane, repo="code", measured=True)
            assert r_code["ahead_of_upstream"] == 0 and r_code["dirty_paths"] >= 1, r_code
            r_commons = _reading(lane, repo="commons", measured=True)
            assert r_commons["ahead_of_upstream"] == 0, r_commons
            assert len(ledgered) == 1, f"a landed crossing ledgers nothing: {ledgered}"

            # (c) a component with no .git above its history dir -> lands, journaled unmeasured
            plain = base / "plain_component"
            plain.mkdir()
            new, hist, _ = _cross(plain, witness, classes)
            assert "[PROVED]" in new, new
            lane = _lane_of(projector.read_history(hist)[-1])
            assert lane["expected"] == lane["actual"], lane
            r_plain = _reading(lane, root=str(plain.resolve()))
            assert r_plain["measured"] is False and "no .git above" in r_plain["why"], r_plain

            # (d) the remote removed, so @{u} fails -> lands, upstream and ahead journaled None
            _git(code, "remote", "remove", "origin")
            comp_d = code / "fixture_component_d"
            comp_d.mkdir()
            new, hist, _ = _cross(comp_d, witness, classes)
            assert "[PROVED]" in new, new
            lane = _lane_of(projector.read_history(hist)[-1])
            assert lane["expected"] == lane["actual"], lane
            r_code = _reading(lane, repo="code", measured=True)
            assert r_code["upstream"] is None and r_code["ahead_of_upstream"] is None, r_code
            assert len(ledgered) == 1, f"no landed crossing ledgers: {ledgered}"
        finally:
            (transitions._TICKETS, _insp._CHART_BERTHS,
             transitions._stamp_sail, transitions._ledger_durability_refusal) = saved

    # (e) composition: the lane imports repo_truth from orient and shells no git of its own
    tree = ast.parse(Path(transitions.__file__).read_text())
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "inspect_durability"), None)
    assert fn is not None, "no FunctionDef inspect_durability in transitions.py"
    imports = [n for n in ast.walk(fn) if isinstance(n, ast.ImportFrom)
               and n.module == "cairn.tools.orient.orient"
               and any(a.name == "repo_truth" for a in n.names)]
    assert imports, "inspect_durability must import repo_truth from cairn.tools.orient.orient"
    shelled = [n for n in ast.walk(fn)
               if (isinstance(n, ast.Name) and n.id == "subprocess")
               or (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "subprocess")]
    assert not shelled, "inspect_durability composes repo_truth — it shells no git of its own"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

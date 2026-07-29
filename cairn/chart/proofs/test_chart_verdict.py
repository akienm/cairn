"""Proof: the verdict — the answer a voyage owes its chart (ticket
proved-answers-the-chart, 2026-07-29), and the ONE validator behind the exit
gate's two mouths.

Teeth a hollow build could not pass:
  - THE SHAPE GATE REFUSES NARRATION: a verdict without its instrument or its
    evidence, a disposition without the deciding observation, an off-vocabulary
    outcome/disposition — each refused with the field named.
  - COVERAGE IS COMPLETE ON FIRST PASS: an unanswered criterion, an
    answered-and-FAILED one, an undispositioned hypothesis — one line each; an
    unreadable chain REFUSES, it does not vanish (Law 8).
  - ONE VALIDATOR, TWO MOUTHS, BY IDENTITY: the inspector's exit gate composes
    THIS module's verdict_error/unanswered — the same artifact admits or
    refuses identically at the gate and at the door, because there is exactly
    one implementation.
  - THE BERTH LANDS AND ROUND-TRIPS; a partial or unclaimed artifact leaves
    nothing behind the door.
  - THE RENDERING CARRIES THE KILL AND ITS EVIDENCE: every piece, its
    disposition, and the deciding observation verbatim — a narrated kill
    cannot render.
  - THE DEPOSIT FACE IS GATED (refusals leave the tree standing) and lands
    with the berth as provenance.
  - TREE-FREE BY IMPORT: verdict.py's allowlist is stdlib + chart.orient only —
    the fire path from the chokepoint may never reach tree machinery.

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/chart/proofs/test_chart_verdict.py     # exit 0 = green
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import cairn.build_inspector.inspector as inspector_mod
from cairn.chart import verdict as verdict_mod
from cairn.chart.verdict import (
    VerdictRefused, unanswered, validate_verdict, verdict_error,
    verdict_node_content, write_verdict,
)
from cairn.chart.live import deposit_verdict
from cairn.chart.tree import nexus_table
from cairn.db_domain import store
from cairn.librarian import trees

_NEXUS = f"verdict_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"


def make_root():
    """A synthetic world: a filed ticket, a claiming chain (hypothesize <-
    validate), berthed where the exit gate globs."""
    tmp = tempfile.mkdtemp(prefix="chart_verdict_proof_")
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    tickets = os.path.join(tmp, "CairnCommons", "tickets")
    os.makedirs(tickets)
    with open(os.path.join(tickets, "sworn.json"), "w") as fh:
        fh.write("{}")
    berths = os.path.join(tmp, "berths")
    packets = os.path.join(berths, "0", "packets")
    os.makedirs(packets)
    hyp = os.path.join(packets, "hypothesize-20260729T000000-feedfeedfeed.json")
    with open(hyp, "w") as fh:
        json.dump({"hypotheses": [
            {"piece": "build the alpha splitter",
             "expect": "the splitter's teeth pass twice",
             "falsifier": "any tooth red on either run",
             "instrument": "python3 proofs/test_splitter.py, twice"},
            {"piece": "compose the settled machinery",
             "expect": "the composed door refuses a phantom ref",
             "falsifier": "a phantom ref berths",
             "instrument": "the door's own gate, fixture ref"}]}, fh)
    val = os.path.join(packets, "validate-20260729T000001-cafecafecafe.json")
    with open(val, "w") as fh:
        json.dump({"ticket": "sworn", "hypothesize_ref": hyp,
                   "criteria": [
                       {"claim": "the splitter is green twice",
                        "instrument": "python3 proofs/test_splitter.py, twice",
                        "covers": ["build the alpha splitter"]},
                       {"claim": "the door refuses the phantom",
                        "instrument": "the door's own gate",
                        "covers": ["compose the settled machinery"]}]}, fh)
    return root, berths, val


def good_artifact(val):
    return {
        "ticket": "sworn",
        "validate_ref": val,
        "verdicts": [
            {"claim": "the splitter is green twice",
             "instrument": "python3 proofs/test_splitter.py, twice",
             "outcome": "pass", "evidence": "exit 0 on both runs"},
            {"claim": "the door refuses the phantom",
             "instrument": "the door's own gate",
             "outcome": "pass", "evidence": "VerdictRefused raised, tree untouched"},
        ],
        "dispositions": [
            {"piece": "build the alpha splitter",
             "expect": "the splitter's teeth pass twice",
             "disposition": "confirmed", "by": "exit 0 on both runs"},
            {"piece": "compose the settled machinery",
             "expect": "the composed door refuses a phantom ref",
             "disposition": "killed", "by": "the phantom berthed on run one"},
        ],
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except VerdictRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected VerdictRefused mentioning %r, got none" % needle)


def test_the_shape_gate_refuses_narration(root, berths, val):
    a = good_artifact(val)
    assert verdict_error(a) is None
    assert verdict_error([]) and "must be a dict" in verdict_error([])
    for hollow, needle in [
        (dict(a, ticket=""), "ticket"),
        ({k: v for k, v in a.items() if k != "validate_ref"}, "validate_ref"),
        (dict(a, verdicts=[dict(a["verdicts"][0], evidence="")]), "narration"),
        (dict(a, verdicts=[dict(a["verdicts"][0], instrument=" ")]), "narration"),
        (dict(a, verdicts=[dict(a["verdicts"][0], outcome="maybe")]), "pass|fail"),
        (dict(a, dispositions=[dict(a["dispositions"][0], by="")]), "narration"),
        (dict(a, dispositions=[dict(a["dispositions"][0], disposition="shrugged")]),
         "confirmed|killed"),
    ]:
        err = verdict_error(hollow)
        assert err and needle in err, (needle, err)


def test_coverage_is_complete_on_first_pass(root, berths, val):
    a = good_artifact(val)
    assert unanswered(a) == []
    # one line each: a dropped answer, a FAILED one, a silent hypothesis
    partial = dict(a, verdicts=[dict(a["verdicts"][0], outcome="fail",
                                     evidence="tooth 3 red")],
                   dispositions=a["dispositions"][:1])
    items = unanswered(partial)
    assert len(items) == 3, items
    assert "FAILED" in items[0] and "kick-back" in items[0], items[0]
    assert "unanswered" in items[1] and "the door refuses the phantom" in items[1]
    assert "undispositioned" in items[2] and "compose the settled machinery" in items[2]
    # an unreadable chain refuses, it does not vanish
    ghost = unanswered(dict(a, validate_ref=val + ".gone"))
    assert len(ghost) == 1 and "cannot be read" in ghost[0], ghost


def test_one_validator_two_mouths_by_identity(root, berths, val):
    assert inspector_mod.verdict_error is verdict_mod.verdict_error
    assert inspector_mod.unanswered is verdict_mod.unanswered
    # the same artifact admits at both mouths...
    a = good_artifact(val)
    assert inspector_mod.proved_answers_the_chart("sworn", berths_root=Path(berths))
    packets = os.path.join(berths, "0", "packets")
    art = os.path.join(packets, "verdict-20260729T000002-beefbeefbeef.json")
    with open(art, "w") as fh:
        json.dump(a, fh)
    assert inspector_mod.proved_answers_the_chart("sworn", berths_root=Path(berths)) == []
    assert validate_verdict(a, root=root) is a
    # ...and the same mutation refuses at both
    with open(art, "w") as fh:
        json.dump(dict(a, dispositions=a["dispositions"][:1]), fh)
    gate = inspector_mod.proved_answers_the_chart("sworn", berths_root=Path(berths))
    assert gate and "undispositioned" in gate[0]["finding"], gate
    expect_refusal(lambda: validate_verdict(dict(a, dispositions=a["dispositions"][:1]),
                                            root=root), "undispositioned")
    os.unlink(art)


def test_the_berth_lands_and_the_door_holds(root, berths, val):
    berth_dir = os.path.join(root, "instance", "verdict_berth")
    a = good_artifact(val)
    path = write_verdict(a, instance_dir=berth_dir, root=root)
    assert os.path.basename(path).startswith("verdict-")
    with open(path) as fh:
        assert json.load(fh) == a, "the berthed artifact round-trips whole"
    expect_refusal(lambda: write_verdict(dict(a, verdicts=[]),
                                         instance_dir=berth_dir, root=root),
                   "not yet answered")
    expect_refusal(lambda: write_verdict(dict(a, ticket="never-filed"),
                                         instance_dir=berth_dir, root=root),
                   "no ticket on file")
    assert len(os.listdir(berth_dir)) == 1, \
        "a refused artifact leaves nothing behind the door"


def test_the_rendering_carries_the_kill_and_its_evidence(root, berths, val):
    a = good_artifact(val)
    content = verdict_node_content(a)
    assert content.startswith("VERDICT for ticket sworn")
    for needle in ("build the alpha splitter", "compose the settled machinery",
                   "CONFIRMED", "KILLED", "the phantom berthed on run one",
                   "exit 0 on both runs", "the splitter is green twice", "pass"):
        assert needle in content, "the rendering dropped %r: %s" % (needle, content)


def test_the_deposit_face_is_gated(root, berths, val):
    berth_dir = os.path.join(root, "instance", "deposit_berth")
    a = good_artifact(val)
    berth = write_verdict(a, instance_dir=berth_dir, root=root)
    table = nexus_table(_NEXUS)
    before = trees.tree_state(_NEXUS, table=table, owner="chart")
    expect_refusal(lambda: deposit_verdict(a, [1.0, 0.0, 0.0],
                                           berth_path=berth + ".gone", root=root),
                   "does not exist")
    expect_refusal(lambda: deposit_verdict(dict(a, dispositions=[]), [1.0, 0.0, 0.0],
                                           berth_path=berth, root=root),
                   "undispositioned")
    assert trees.tree_state(_NEXUS, table=table, owner="chart") == before, \
        "a refused deposit leaves the tree standing"
    # The real landing, with the berth as provenance (scratch corpus, as the
    # sibling proofs: the LIVE hypothesize tree is never a fixture).
    content = verdict_node_content(a)
    r = trees.deposit(content, [1.0, 0.0, 0.0],
                      {"source": berth, "validate_ref": a["validate_ref"],
                       "ticket": a["ticket"]},
                      tree=_NEXUS, table=table, owner="chart")
    rows = store.read(table, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == content
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["provenance"]["ticket"] == "sworn"


def test_import_allowlist_tree_free(root, berths, val):
    # Composed over orient's import_map: verdict.py is TREE-FREE like
    # chart.orient — the exit gate's fire path can never reach the trees.
    from cairn.orient.orient import import_map
    allow = ("__future__", "hashlib", "json", "os", "time", "cairn.chart.orient")
    seen = import_map(verdict_mod.__file__)["measured"]["imports"]
    offenders = [m for m in seen
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"verdict.py imports outside its allowlist: {offenders} — the one "
        "validator stays tree-free; the deposit face lives on the tree side "
        "(live.py), not here")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            t = nexus_table(_NEXUS)
            cur.execute(f'DROP TABLE IF EXISTS "{t}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
    finally:
        conn.close()


def _main() -> int:
    root, berths, val = make_root()
    checks = [
        test_the_shape_gate_refuses_narration,
        test_coverage_is_complete_on_first_pass,
        test_one_validator_two_mouths_by_identity,
        test_the_berth_lands_and_the_door_holds,
        test_the_rendering_carries_the_kill_and_its_evidence,
        test_the_deposit_face_is_gated,
        test_import_allowlist_tree_free,
    ]
    try:
        for check in checks:
            check(root, berths, val)
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
        shutil.rmtree(os.path.dirname(root), ignore_errors=True)
    print("green — chart/verdict: the shape gate refuses narration, coverage is "
          "complete on first pass (an unreadable chain refuses, never vanishes), "
          "the exit gate and the deposit face are ONE validator by identity, the "
          "berth round-trips, the rendering carries every kill with its deciding "
          "observation, the deposit face is gated, and the validator is tree-free "
          "by import — the answer a voyage owes its chart has physics")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

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

And since 2026-07-29 (ticket the-deposit-rides-the-read) the deposit itself is
physics, so its two halves have teeth here too:

  - THE LEDGER IS APPEND-ONLY AND PENDING DERIVES BY READ: an enqueue appends,
    a deposit appends the second kind, and the earlier bytes are a PREFIX of the
    later file — nothing is ever edited, truncated, or removed; a berth already
    deposited never becomes pending again (idempotence by the record, not by
    mutation); an unparseable line is named, never silently dropped.
  - THE ENQUEUE KEYS ON THE ARTIFACT, NEVER ON THE NOTE: a ticket no verdict
    artifact claims enqueues nothing and leaves no ledger behind.
  - THE LATEST-CLAIMER RULE HAS ONE IMPLEMENTATION: the gate and the enqueue
    read the same function BY IDENTITY, so they cannot disagree about which
    artifact answered.
  - THE DRAIN LANDS THROUGH THE ONE DOOR, ONCE: a pending verdict deposits with
    its berth as provenance and is marked; a second drain finds nothing and the
    tree stands still; a FAILED deposit leaves its entry standing, names itself,
    and does not stop the drain from returning.

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
    VerdictRefused, claiming_packets, enqueue_verdict, latest_claiming_artifact,
    mark_deposited, pending, read_ledger, unanswered, validate_verdict,
    verdict_error, verdict_node_content, write_verdict,
)
from cairn.chart.live import deposit_verdict, drain_pending
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


def _berth_a_verdict(berths, artifact, stamp):
    """Land a verdict artifact where the latest-claimer rule globs, with a stamp we
    choose (the filename carries the order — sorted IS chronological)."""
    path = os.path.join(berths, "0", "packets", "verdict-%s-feedfeedfeed.json" % stamp)
    with open(path, "w") as fh:
        json.dump(artifact, fh)
    return path


def test_the_ledger_is_append_only_and_pending_derives_by_read(root, berths, val):
    """The record-of-truth discipline at the ledger (Law 7): every motion is an
    APPEND, so the file's earlier bytes are always a prefix of its later bytes, and
    'drained' is a second record kind — never an edit, a removal, or a truncation.
    Pending is therefore a READ (enqueued minus deposited), which is also why a
    re-enqueue of an already-deposited berth cannot resurrect it."""
    ledger = os.path.join(root, "instance", "ledger", "verdict-deposits.jsonl")
    art = _berth_a_verdict(berths, good_artifact(val), "20260729T010000")
    berth = enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger)
    assert berth == art, (berth, art)
    after_enqueue = open(ledger).read()
    entries = pending(ledger_path=ledger)
    assert len(entries) == 1 and entries[0]["berth"] == art, entries
    assert entries[0]["kind"] == "enqueued" and entries[0]["ticket"] == "sworn"
    mark_deposited(art, "node-abc", ledger_path=ledger)
    after_deposit = open(ledger).read()
    assert after_deposit.startswith(after_enqueue), \
        "the ledger is append-only — an earlier read must be a PREFIX of a later one"
    assert len(after_deposit) > len(after_enqueue), "the deposited record must land"
    assert pending(ledger_path=ledger) == [], "a deposited berth is no longer pending"
    kinds = [r["kind"] for r in read_ledger(ledger_path=ledger)]
    assert kinds == ["enqueued", "deposited"], kinds
    # a re-enqueue of a deposited berth never becomes pending again — idempotence
    # by the deposited RECORD, not by mutating anything
    enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger)
    assert pending(ledger_path=ledger) == [], \
        "a berth already deposited must never be pending again (idempotence by record)"
    assert open(ledger).read().startswith(after_deposit), "still append-only"
    # an unparseable line is NAMED, never silently dropped, and never edited away
    with open(ledger, "a") as fh:
        fh.write("{not json at all\n")
    named = [r for r in read_ledger(ledger_path=ledger) if r["kind"] == "unreadable"]
    assert len(named) == 1 and "not json" in named[0]["raw"], named
    assert pending(ledger_path=ledger) == [], "a bad line must not break the read"
    os.unlink(art)
    os.unlink(ledger)


def test_the_enqueue_keys_on_the_artifact_never_on_the_note(root, berths, val):
    """The kill the exit stone taught, honored as physics: the gate's note is CLEAN
    both when a chart was answered and when NO chart claims the ticket at all — so
    an enqueue keyed on the note would file a pending deposit for an artifact that
    does not exist. Keyed on the artifact, an unclaimed ticket enqueues nothing and
    leaves no ledger behind at all."""
    ledger = os.path.join(root, "instance", "ledger2", "verdict-deposits.jsonl")
    assert enqueue_verdict("never-charted", berths_root=berths, ledger_path=ledger) is None
    assert not os.path.exists(ledger), \
        "an enqueue with no artifact must write nothing — not even an empty ledger"


def test_the_latest_claimer_rule_has_exactly_one_implementation(root, berths, val):
    """One implementation, two mouths, BY IDENTITY: the exit gate locates the
    artifact that stands with the same function the crossing's enqueue calls. A gate
    that judged one artifact while the enqueue deposited another would be the
    two-mouths defect in the one place nobody would look for it."""
    assert inspector_mod.claiming_packets is claiming_packets
    ledger = os.path.join(root, "instance", "ledger3", "verdict-deposits.jsonl")
    older = _berth_a_verdict(berths, good_artifact(val), "20260729T020000")
    later = dict(good_artifact(val))
    later["verdicts"] = [dict(v, evidence=v["evidence"] + " (the second answer)")
                         for v in later["verdicts"]]
    newer = _berth_a_verdict(berths, later, "20260729T030000")
    found = claiming_packets("sworn", "verdict", berths_root=berths)
    assert [p for p, _ in found] == [older, newer], found
    assert latest_claiming_artifact("sworn", berths_root=berths)[0] == newer
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == newer, \
        "the enqueue files the LATEST claiming artifact — the answer that stands"
    os.unlink(older)
    os.unlink(newer)
    os.unlink(ledger)


def test_the_drain_lands_through_the_one_door_and_never_twice(root, berths, val):
    """The read is the event: a pending verdict deposits through deposit_verdict
    (the ONE door — no parallel writer), lands with its berth as provenance, is
    marked deposited, and a SECOND drain finds nothing pending, so the tree stands
    exactly still. Scratch nexus, fixed vector: the LIVE hypothesize tree is never
    a fixture and no embed host is on this tooth's path."""
    ledger = os.path.join(root, "instance", "ledger4", "verdict-deposits.jsonl")
    # Its OWN artifact text: the deposit door dedups by (tree, content), so reusing
    # the gated-face tooth's artifact would land a DUPLICATE carrying that tooth's
    # provenance — a green that proved nothing about this drain (measured on the
    # first run of this tooth, 2026-07-29).
    drained_artifact = dict(good_artifact(val))
    drained_artifact["verdicts"] = [dict(v, evidence=v["evidence"] + " — drained")
                                    for v in drained_artifact["verdicts"]]
    art = _berth_a_verdict(berths, drained_artifact, "20260729T040000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == art
    table = nexus_table(_NEXUS)
    drained = drain_pending(root=root, nexus=_NEXUS, embed=lambda text: [0.0, 1.0, 0.0],
                            ledger_path=ledger)
    assert len(drained) == 1 and drained[0]["berth"] == art, drained
    assert "failed" not in drained[0] and drained[0]["duplicate"] is False, drained
    node_id = drained[0]["deposited"]
    rows = store.read(table, where="node_id = %s", params=(node_id,))
    assert rows and rows[0]["provenance"]["source"] == art, rows
    assert rows[0]["provenance"]["ticket"] == "sworn"
    assert rows[0]["content"] == verdict_node_content(drained_artifact)
    assert pending(ledger_path=ledger) == [], "the landed berth is marked, not pending"
    standing = trees.tree_state(_NEXUS, table=table, owner="chart")
    assert drain_pending(root=root, nexus=_NEXUS, embed=lambda text: [0.0, 1.0, 0.0],
                         ledger_path=ledger) == [], "a second drain has nothing to do"
    assert trees.tree_state(_NEXUS, table=table, owner="chart") == standing, \
        "a re-drain must never double-deposit — the tree stands exactly still"
    os.unlink(art)


def test_a_failed_deposit_stands_pending_and_is_named(root, berths, val):
    """Law 7 at this seam: the deposit refuses (the artifact stopped validating),
    so the ENQUEUED line stands — the obligation is permanent in the record — while
    the failure is named in what the door serves. The drain RETURNS instead of
    raising: a counsel read must still serve, and the tree is untouched."""
    ledger = os.path.join(root, "instance", "ledger5", "verdict-deposits.jsonl")
    bad = _berth_a_verdict(berths, dict(good_artifact(val), dispositions=[]),
                           "20260729T050000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == bad
    table = nexus_table(_NEXUS)
    before = trees.tree_state(_NEXUS, table=table, owner="chart")
    drained = drain_pending(root=root, nexus=_NEXUS, embed=lambda text: [0.0, 0.0, 1.0],
                            ledger_path=ledger)
    assert len(drained) == 1 and "failed" in drained[0], drained
    assert "undispositioned" in drained[0]["failed"], drained
    assert drained[0]["still_pending"] is True
    assert [e["berth"] for e in pending(ledger_path=ledger)] == [bad], \
        "a failed deposit leaves its entry STANDING — nothing vanishes"
    assert not [r for r in read_ledger(ledger_path=ledger) if r["kind"] == "deposited"], \
        "nothing may claim a landing that did not happen"
    assert trees.tree_state(_NEXUS, table=table, owner="chart") == before, \
        "a refused deposit leaves the tree standing"
    os.unlink(bad)
    os.unlink(ledger)


def test_import_allowlist_tree_free(root, berths, val):
    # Composed over orient's import_map: verdict.py is TREE-FREE like
    # chart.orient — the exit gate's fire path can never reach the trees. ``glob``
    # joined 2026-07-29 with the latest-claimer rule (stdlib; the ledger and the
    # locator are files, by the netns constraint that split the deposit in two).
    from cairn.orient.orient import import_map
    allow = ("__future__", "glob", "hashlib", "json", "os", "time", "cairn.chart.orient")
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
        test_the_ledger_is_append_only_and_pending_derives_by_read,
        test_the_enqueue_keys_on_the_artifact_never_on_the_note,
        test_the_latest_claimer_rule_has_exactly_one_implementation,
        test_the_drain_lands_through_the_one_door_and_never_twice,
        test_a_failed_deposit_stands_pending_and_is_named,
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
          "by import — the answer a voyage owes its chart has physics; and THE "
          "DEPOSIT RIDES THE READ (ticket the-deposit-rides-the-read): the pending "
          "ledger is append-only with pending derived by read (a re-enqueue of a "
          "deposited berth never resurrects it; a bad line is named, never dropped), "
          "the enqueue keys on the ARTIFACT never the clean note, the latest-claimer "
          "rule has exactly one implementation (gate and enqueue by identity), and "
          "the drain lands through the ONE door exactly once — a failed deposit "
          "stands pending, names itself, and still lets the door serve")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

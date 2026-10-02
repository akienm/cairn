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

THE DEPOSIT FACE'S TEETH (the gated face, the drain, part-by-part landing, the
refused part, no character ceiling, the artifact-named nexus) moved with the code
to cairn/devices/codemother/proofs/test_deposit.py (ticket e8fe361a5b2f, RULE 1:
a proof measures its own component; the deposit is codemother's, not this machine's).

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/devices/codemother/machines/verdict/proofs/test_chart_verdict.py     # exit 0 = green
"""
from __future__ import annotations

import contextlib
import json
import os
import pytest
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import cairn.machines.build_inspector.inspector as inspector_mod
from cairn.devices.codemother.machines.verdict import verdict as verdict_mod
from cairn.devices.codemother.machines.verdict.verdict import (
    VerdictRefused, claiming_packets, enqueue_verdict, latest_claiming_artifact,
    mark_deposited, pending, read_ledger, unanswered, validate_verdict,
    verdict_error, verdict_node_content, verdict_node_parts, write_verdict,
)
from cairn.tools.tree.tree import nexus_table, scratch_nexus
from cairn.devices.db_domain.tools.client import store
from cairn.devices.librarian import trees
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

_SCRATCH = contextlib.ExitStack()   # the nexus tables this run mints ride store.scratch(): dropped at close, swept by pid if not
_HELD: list[str] = []


def _nexus() -> str:
    """This run's own nexus, minted on first use through tree.scratch_nexus()."""
    if not _HELD:
        _HELD.append(_SCRATCH.enter_context(scratch_nexus("verdict")))
    return _HELD[0]


def make_root():
    """A synthetic world: a filed ticket, a claiming chain (hypothesize <-
    validate), berthed where the exit gate globs."""
    tmp = str(scratch_dir("chart_verdict_proof_"))
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    # TWO REAL INSTRUMENTS (ticket 8e5db5f3edb2). The door RUNS what it is handed,
    # so a fixture whose instruments are prose exercises the refusal path and
    # nothing else. These are the smallest honest commands: one exits 0, one exits
    # 7, and the second is here so `expect_exit` is a DECLARATION the door reads
    # rather than a zero it assumes.
    os.makedirs(os.path.join(root, "proofs"))
    for name, body in (("splitter.sh", "echo 'splitter: 2 runs, 0 red'\nexit 0\n"),
                       ("phantom.sh", "echo 'phantom ref refused'\nexit 7\n")):
        with open(os.path.join(root, "proofs", name), "w") as fh:
            fh.write(body)
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
                        "instrument": "the splitter's teeth, twice: `bash proofs/splitter.sh`",
                        "expect_exit": 0,
                        "covers": ["build the alpha splitter"]},
                       {"claim": "the door refuses the phantom",
                        "instrument": "bash proofs/phantom.sh",
                        "expect_exit": 7,
                        "covers": ["compose the settled machinery"]}]}, fh)
    return root, berths, val


@pytest.fixture
def _world():
    return make_root()


@pytest.fixture
def root(_world):
    return _world[0]


@pytest.fixture
def berths(_world):
    return _world[1]


@pytest.fixture
def val(_world):
    return _world[2]


def good_artifact(val):
    return {
        "ticket": "sworn",
        "validate_ref": val,
        "verdicts": [
            {"claim": "the splitter is green twice",
             "instrument": "the splitter's teeth, twice: `bash proofs/splitter.sh`",
             "outcome": "pass", "evidence": "exit 0 on both runs",
             "discriminating_observation": "reverted the fix; the same instrument exits 1"},
            {"claim": "the door refuses the phantom",
             "instrument": "bash proofs/phantom.sh",
             "outcome": "pass", "evidence": "VerdictRefused raised, tree untouched",
             "discriminating_observation": "removed the ref check; the phantom berths"},
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


def test_a_hollow_instrument_is_refused_at_the_write_gate(root, berths, val):
    """The discriminating_observation is checked at the WRITE gate (inspect_verdict /
    validate_verdict), not at verdict_error — so existing artifacts on disk without
    the field are not retroactively refused by the exit gate, but new artifacts
    going through the door are."""
    a = good_artifact(val)
    for hollow in [
        dict(a, verdicts=[dict(a["verdicts"][0], discriminating_observation="")]),
        dict(a, verdicts=[{k: v for k, v in a["verdicts"][0].items()
                            if k != "discriminating_observation"}]),
    ]:
        assert verdict_error(hollow) is None, \
            "verdict_error must NOT check discriminating_observation — the exit gate reads it"
        expect_refusal(
            lambda h=hollow: validate_verdict(h, root=root),
            "discriminating_observation")


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
    assert gate and "undispositioned" in gate[0]["about"], gate
    expect_refusal(lambda: validate_verdict(dict(a, dispositions=a["dispositions"][:1]),
                                            root=root), "undispositioned")
    os.unlink(art)


def test_the_berth_lands_and_the_door_holds(root, berths, val):
    berth_dir = os.path.join(root, "instance", "verdict_berth")
    a = good_artifact(val)
    path = write_verdict(a, instance_dir=berth_dir, root=root)
    assert os.path.basename(path).startswith("verdict-")
    with open(path) as fh:
        berthed = json.load(fh)
    # WHAT THE DOOR OBSERVED LANDS IN THE RECORD (ticket 8e5db5f3edb2 clause 5).
    # The artifact round-trips whole and carries one key more than it was handed:
    # the run the door took for itself, so a reader who doubts the verdict can
    # re-run the very string the door ran instead of taking its word.
    stamp = berthed.pop("observed_runs")
    assert berthed == a, "the berthed artifact round-trips whole"
    assert [o["run"]["command"] for o in stamp] == ["bash proofs/splitter.sh",
                                                    "bash proofs/phantom.sh"]
    assert [o["run"]["exit"] for o in stamp] == [0, 7]
    assert [o["expect_exit"] for o in stamp] == [0, 7], \
        "expect_exit is READ from the validate berth, not assumed to be zero"
    assert "phantom ref refused" in stamp[1]["run"]["tail"], \
        "the output tail lands beside the exit, or a reader has a verdict and no evidence"
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


# The rendering this fixture produced on 2026-07-29, pinned VERBATIM. Criterion 1 of
# the a-node-holds-one-claim chart asks that the whole survive the split byte-identical
# — so the tooth is a golden string over FIXTURE data (never live data: a snapshot of
# something that legitimately moves is a spurious red waiting to happen). If a renderer
# change is intended, this literal changes in the same commit and says so.
# CHANGED 2026-09-11 IN THE SAME COMMIT AS THE RENDERER'S INPUT, which is what the
# paragraph above asks for: ticket 8e5db5f3edb2 made the door RUN the instrument it is
# handed, so the fixture's two instruments became real commands. The renderer itself was
# not touched — it is a pure join over the same parts — and the diff between the two
# literals is exactly the two instrument strings and nothing else.
_GOLDEN_WHOLE = (
    "VERDICT for ticket sworn — the chart answered at PROVED. CRITERIA: the splitter "
    "is green twice -> pass [by the splitter's teeth, twice: `bash proofs/splitter.sh`: "
    "exit 0 on both runs]; the door refuses the phantom -> pass [by bash "
    "proofs/phantom.sh: VerdictRefused raised, tree untouched]. HYPOTHESES: CONFIRMED: "
    "build the alpha splitter — decided by: exit 0 on both runs; KILLED: compose the "
    "settled machinery — decided by: the phantom berthed on run one"
)


def test_a_node_holds_one_claim(root, berths, val):
    """THE PARTS RENDERER (ticket a-node-holds-one-claim, 2026-07-29): one part per
    criterion verdict and one per hypothesis disposition, each carrying its OWN claim
    and nothing else — which is the whole point. A node that carries four claims can
    only ever be retrieved as an average of four things, and the walk that reaches for
    one of them gets a vector aimed between them all.

    And ONE RENDERING, not two: the whole is a pure JOIN over these exact strings, so
    the two renderings cannot drift into the two-mouths defect. The golden literal
    proves the split changed no bytes."""
    a = good_artifact(val)
    parts = verdict_node_parts(a)
    assert [k for k, _ in parts] == ["criterion", "criterion",
                                     "disposition", "disposition"], parts
    assert len(parts) == len(a["verdicts"]) + len(a["dispositions"])
    # one claim each: no part carries another part's deciding observation
    for i, (_, content) in enumerate(parts):
        others = [c for j, (_, c) in enumerate(parts) if j != i]
        for other in others:
            assert other not in content, "a part swallowed another: %r" % content
    assert "the phantom berthed on run one" in parts[3][1]
    assert "the phantom berthed on run one" not in parts[2][1]
    # BARE ON PURPOSE: no ticket, no berth, no framing prose in a part. node_id is a
    # content hash, so attribution baked into content would make every part unique BY
    # CONSTRUCTION — the exact property that makes a monolith undedupable.
    for _, content in parts:
        assert "sworn" not in content and "VERDICT for ticket" not in content, content
        assert val not in content, content
    # the whole is derived, and derived changed nothing
    whole = verdict_node_content(a)
    assert whole == _GOLDEN_WHOLE, "the split moved the whole's bytes:\n%r" % whole
    for _, content in parts:
        assert content in whole, "the whole is not a join over the parts: %r" % content


def test_the_ledger_expresses_a_many_node_landing(root, berths, val):
    """THE LEDGER'S MANY-NODE LANDING: a berth becomes N nodes, so the record that
    CLOSES it must name them all. Two things have teeth here — that a landing which
    names nothing is refused (a 'deposited' record is what stops pending() returning
    the berth, so an empty landing would close a verdict that never reached the tree),
    and that records written before this change, carrying node_id SINGULAR, still
    close their berths forever. pending() has only ever keyed on kind+berth, and this
    tooth is what keeps that true."""
    ledger = os.path.join(root, "instance", "ledger6", "verdict-deposits.jsonl")
    art = _berth_a_verdict(berths, good_artifact(val), "20260729T060000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == art
    expect_refusal(lambda: mark_deposited(art, [], ledger_path=ledger), "landed no node ids")
    expect_refusal(lambda: mark_deposited(art, ["n1", "  "], ledger_path=ledger),
                   "landed no node ids")
    assert [e["berth"] for e in pending(ledger_path=ledger)] == [art], \
        "a refused landing leaves the berth STANDING pending"
    assert not [r for r in read_ledger(ledger_path=ledger) if r["kind"] == "deposited"]
    rec = mark_deposited(art, ["n1", "n2", "n3"], ledger_path=ledger)
    assert rec["node_ids"] == ["n1", "n2", "n3"], rec
    assert pending(ledger_path=ledger) == [], "a fully-landed berth is no longer pending"
    # the OLD shape, hand-written as it was written before 2026-07-29, still closes
    old = _berth_a_verdict(berths, dict(good_artifact(val), ticket="sworn"),
                           "20260729T070000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == old
    with open(ledger, "a") as fh:
        fh.write(json.dumps({"kind": "deposited", "berth": old,
                             "node_id": "legacy-single", "at": "2026-07-28T00:00:00Z"}) + "\n")
    assert pending(ledger_path=ledger) == [], \
        "a pre-2026-07-29 single-id record must still close its berth — records of " \
        "truth are read forever, never migrated in place (Law 7)"
    # a single id is still accepted at the door, so the old callers are not broken
    assert mark_deposited(art, "n-solo", ledger_path=ledger)["node_ids"] == ["n-solo"]
    os.unlink(art)
    os.unlink(old)
    os.unlink(ledger)


def test_the_hollow_renderer_goes_red(root, berths, val):
    """Law 8, self-applied: a suite that passes both the real implementation AND a
    deliberately hollowed one has measured nothing. Here the hollow build is the
    obvious one — a parts renderer that returns the whole as a single part, which is
    exactly today-before-this-stone wearing the new interface. The granularity tooth
    must go RED against it, and this tooth fails if it does not."""
    real = verdict_mod.verdict_node_parts
    hollow = lambda artifact: [("criterion", _GOLDEN_WHOLE)]  # noqa: E731
    # BOTH bindings, deliberately: the module's (which is what verdict_node_content
    # itself resolves through) and this proof's own import. Patching only the module
    # would leave the tooth reading the REAL renderer and going red for an incidental
    # reason — a hollow-build check that passes by accident is itself hollow.
    verdict_mod.verdict_node_parts = hollow
    globals()["verdict_node_parts"] = hollow
    try:
        try:
            test_a_node_holds_one_claim(root, berths, val)
        except AssertionError:
            pass  # the tooth bit, as it must
        else:
            raise AssertionError(
                "THE TEETH ARE HOLLOW: a renderer returning the whole as one part "
                "passed the granularity tooth — the stone would be undetectable")
    finally:
        verdict_mod.verdict_node_parts = real
        globals()["verdict_node_parts"] = real
    assert verdict_mod.verdict_node_parts is real and verdict_node_parts is real


def test_import_allowlist_tree_free(root, berths, val):
    # Composed over orient's import_map: verdict.py is TREE-FREE like
    # chart.orient — the exit gate's fire path can never reach the trees. ``glob``
    # joined 2026-07-29 with the latest-claimer rule (stdlib; the ledger and the
    # locator are files, by the netns constraint that split the deposit in two).
    # ``re`` joined 2026-07-30 with the falsifier form (stdlib; segmenting a
    # ticket's numbered RED clauses — still a file read, still no tree).
    from cairn.tools.orient.orient import import_map
    from cairn.tools.gate import gate
    # ``cairn.tools.gate`` joined 2026-08-13 with this stage's own gate (ruling
    # every-machine-carries-its-own-inspector-and-gate). It does not weaken the
    # tree-free claim and the claim is MEASURED, not asserted: gate.py's own
    # import_map reads ['__future__', 'json'] — stdlib, no db, no embed host, no
    # inference. Gate-ness is a DIRECT-import fact, which is how `cairn determinism`
    # and `cairnmap --gate` see this stage from outside without being told.
    # cairn.tools.chain.chain joined 2026-09-02 (device isolation): chain
    # resolution functions (claiming_packets, chain_for_ticket, verdict_error
    # et al.) factored from verdict.py to the chain tool. Still tree-free:
    # chain.py reads berth files, no db or embed host.
    # shlex/shutil/subprocess joined 2026-09-11 (ticket 8e5db5f3edb2): the door RUNS
    # the instrument it is handed. All three are stdlib and none reaches a tree, the
    # db or the embed host — the tree-free claim is untouched, and so is the PURE
    # DETERMINISTIC grade: `cairn determinism` excludes subprocess from its oracle
    # walk by name (determinism.py:156) under Akien's ruling that deterministic code
    # may call other scripts. A run is a fork, never an ask.
    # cairn.tools.chain.verdict_contract joined 2026-10-02 (ticket d8e8a2dc1176, RULE 1): the
    # coverage reader and the ledger moved down a rung to the chain tool. MEASURED tree-free
    # below like the gate: its own imports are stdlib plus the chain tool's two modules.
    allow = ("__future__", "hashlib", "json", "os", "re", "shlex", "shutil",
             "subprocess", "time",
             "cairn.tools.chain.chain", "cairn.tools.chain.grammar",
             "cairn.tools.chain.verdict_contract", "cairn.tools.gate.gate")
    import cairn.tools.chain.verdict_contract as _contract
    assert sorted(import_map(_contract.__file__)["measured"]["imports"]) == [
        "__future__", "cairn.tools.chain.chain", "cairn.tools.chain.grammar", "json", "os",
        "re", "time"], "the chain contract grew an import — the tree-free claim is measured"
    assert sorted(import_map(gate.__file__)["measured"]["imports"]) == ["__future__", "json"], \
        "the gate tool grew an import — the tree-free claim above is measured, not assumed"
    seen = import_map(verdict_mod.__file__)["measured"]["imports"]
    offenders = [m for m in seen
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"verdict.py imports outside its allowlist: {offenders} — the one "
        "validator stays tree-free; the deposit face lives on the tree side "
        "(deposit.py), not here")


def _main() -> int:
    root, berths, val = make_root()
    checks = [
        test_the_shape_gate_refuses_narration,
        test_coverage_is_complete_on_first_pass,
        test_one_validator_two_mouths_by_identity,
        test_the_berth_lands_and_the_door_holds,
        test_the_rendering_carries_the_kill_and_its_evidence,
        test_a_node_holds_one_claim,
        test_the_ledger_expresses_a_many_node_landing,
        test_the_hollow_renderer_goes_red,
        test_the_ledger_is_append_only_and_pending_derives_by_read,
        test_the_enqueue_keys_on_the_artifact_never_on_the_note,
        test_the_latest_claimer_rule_has_exactly_one_implementation,
        test_import_allowlist_tree_free,
    ]
    try:
        for check in checks:
            check(root, berths, val)
            print(f"  PASS  {check.__name__}")
    finally:
        _SCRATCH.close()
        shutil.rmtree(os.path.dirname(root), ignore_errors=True)
    print("green — chart/verdict: the shape gate refuses narration, coverage is "
          "complete on first pass (an unreadable chain refuses, never vanishes), "
          "the exit gate and the deposit face are ONE validator by identity, the "
          "berth round-trips, the rendering carries every kill with its deciding "
          "observation, the validator is tree-free by import, the pending ledger "
          "is append-only with pending derived by read, the enqueue keys on the "
          "artifact, the latest-claimer rule has one implementation, a verdict "
          "lands as one node per claim, and the granularity tooth goes RED "
          "against a hollowed renderer (the deposit face's teeth: "
          "cairn/devices/codemother/proofs/test_deposit.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

"""Proof: the decompose brick — the third stackable learning brick built UNDER
pre-installed judges (decompose-filters, PROVED before this module existed —
the judges-before-the-judged ordering, routine since survey-filters proved it).

Teeth a hollow build could not pass:
  - THE CHAIN IS PHYSICS AT DEPTH 4: stage 4 refuses without a berthed, readable
    stage-3 packet — AND refuses when any link below it (constrain, orient) is
    gone or unreadable. The deep links are checked by COMPOSING survey's own
    chain reader (one implementation of 'the chain holds'), asserted by
    identity, not parallel behavior.
  - THE FLOOR HANDS THE JUDGES' VOCABULARIES VERBATIM: holding addresses (what
    a compose piece may use) and absence whats (what a build piece may fill)
    travel from the survey berth exactly — template-fill as physics; the floor
    never decides the split.
  - THE SCHEMA GATE REFUSES what a hollow build would emit: missing fields, bad
    confidence, uncovered provenance, an unfiled ticket claim.
  - THE DOOR COMPOSES THE INSTALLED JUDGES: a compose outside the holdings, a
    build outside the measured absences, a why-less piece — each refused AT THE
    BERTH by the same judge_decompose the promotion gate runs — asserted by
    identity. And the inspector never imports decompose.
  - EVERY PIECE NAMES WHERE IT WRITES: the door refuses a packet whose piece
    carries no non-empty in-repo `writes_to` — and does NOT require the address
    to exist, because a build piece names the file it is about to create. The
    entry is ABSENT (not passed) for a packet with no pieces.
  - THE BERTH LANDS AND ROUND-TRIPS; a refused packet leaves nothing behind.
  - THE DEPOSIT-BACK IS GATED: content is the ONE rendering (intent + the
    split, kinds visible), the berth must exist on disk, refusals leave the
    tree standing.
  - IMPORT ALLOWLIST over orient's import_map: decompose.py composes exactly
    four cairn doors — the inspector's judge, chart's settled orient machinery,
    chart's survey chain reader, and chart's tree verbs. No census re-scan (the
    territory was measured in stage 3), no db, no network.

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/devices/codemother/machines/decompose/proofs/test_chart_decompose.py     # exit 0 = green
"""
from __future__ import annotations

import json
import os
import pytest
import shutil
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import cairn.machines.build_inspector.inspector as inspector_mod
import cairn.devices.codemother.machines.survey.survey as survey_mod
from cairn.devices.codemother.machines.decompose import decompose as decompose_mod
from cairn.devices.codemother.machines.decompose.decompose import (
    DecomposeRefused, decompose_floor, decompose_node_content,
    deposit_decompose, validate_decompose, write_decompose,
)
from cairn.tools.tree.tree import nexus_table
from cairn.devices.db_domain import store
from cairn.devices.librarian import trees
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

_NEXUS = f"decompose_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"


def make_root():
    """A synthetic world: the three-link chain stage 4 fills through — a berthed
    orient packet, a constrain packet chained to it, and a survey packet chained
    to that, holding one address and measuring one absence."""
    tmp = str(scratch_dir("chart_decompose_proof_"))
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    berth_dir = os.path.join(root, "instance", "packets")
    os.makedirs(berth_dir)
    orient_berth = os.path.join(berth_dir, "orient-20260728T170000-feedfeedfeed.json")
    with open(orient_berth, "w") as fh:
        json.dump({"intent": "split the alpha work", "refs": ["chart"]}, fh)
    constrain_berth = os.path.join(berth_dir, "constrain-20260728T170001-cafecafecafe.json")
    with open(constrain_berth, "w") as fh:
        json.dump({"intent_ref": orient_berth,
                   "bounds": {"in": ["alpha"], "out": ["beta"]}}, fh)
    survey_berth = os.path.join(berth_dir, "survey-20260728T170002-beefbeefbeef.json")
    with open(survey_berth, "w") as fh:
        json.dump({"constrain_ref": constrain_berth,
                   "sought": ["the alpha territory"],
                   # The address is REAL-world resolvable — judges are root-blind
                   # by design (same shape as the survey proof's 'chart').
                   "holdings": [{"what": "the settled chart machinery",
                                 "address": "chart"}],
                   "absences": [{"what": "an alpha splitter",
                                 "measure": "path check, absent"}]}, fh)
    return root, orient_berth, constrain_berth, survey_berth


@pytest.fixture
def _world():
    return make_root()


@pytest.fixture
def root(_world):
    return _world[0]


@pytest.fixture
def orient_berth(_world):
    return _world[1]


@pytest.fixture
def constrain_berth(_world):
    return _world[2]


@pytest.fixture
def survey_berth(_world):
    return _world[3]


def good_packet(survey_berth):
    return {
        "survey_ref": survey_berth,
        "sub_problems": [
            {"what": "compose the settled chart machinery", "why": "it is held",
             "kind": "compose", "uses": ["chart"],
             "writes_to": ["chart/composed.py"]},
            {"what": "build the alpha splitter", "why": "measured absent",
             "kind": "build", "fills": "an alpha splitter",
             # NOT a holding, and it does not exist — that is the whole point of the
             # field: a build piece names the file it is about to create.
             "writes_to": ["chart/alpha_splitter.py"]},
        ],
        "unknowns": ["whether the splitter needs a second seam"],
        "confidence": 0.7,
        "provenance": {"survey_ref": "floor", "sub_problems": "cc",
                       "unknowns": "cc"},
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except DecomposeRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected DecomposeRefused mentioning %r, got none" % needle)


def test_the_chain_is_physics_at_depth_4(root, orient_berth, constrain_berth,
                                         survey_berth):
    expect_refusal(lambda: decompose_floor(os.path.join(root, "no-berth.json")),
                   "not a berthed packet")
    not_survey = os.path.join(root, "not_survey.json")
    with open(not_survey, "w") as fh:
        json.dump({"weird": True}, fh)
    expect_refusal(lambda: decompose_floor(not_survey), "not a survey berth")
    # The deep links: a survey berth whose constrain berth is GONE refuses —
    # through survey's OWN reader, composed (identity below), never a shallow fill.
    orphan = os.path.join(root, "orphan_survey.json")
    with open(orphan, "w") as fh:
        json.dump({"constrain_ref": os.path.join(root, "gone.json"),
                   "holdings": [], "absences": []}, fh)
    expect_refusal(lambda: decompose_floor(orphan), "the chain broke")
    # ...and a chain whose ORIENT link snapped refuses just as loudly (depth 4).
    snapped_constrain = os.path.join(root, "snapped_constrain.json")
    with open(snapped_constrain, "w") as fh:
        json.dump({"intent_ref": os.path.join(root, "gone_orient.json"),
                   "bounds": {"in": ["x"], "out": ["y"]}}, fh)
    snapped = os.path.join(root, "snapped_survey.json")
    with open(snapped, "w") as fh:
        json.dump({"constrain_ref": snapped_constrain,
                   "holdings": [], "absences": []}, fh)
    expect_refusal(lambda: decompose_floor(snapped), "the chain broke")
    # The composition is BY IDENTITY: decompose's deep-link reader IS survey's.
    assert decompose_mod._read_constrain_berth is survey_mod._read_constrain_berth
    p = good_packet(survey_berth)
    p["survey_ref"] = os.path.join(root, "no-berth.json")
    expect_refusal(lambda: validate_decompose(p, root=root), "not a berthed packet")


def test_floor_hands_the_judges_vocabularies_verbatim(root, orient_berth,
                                                      constrain_berth, survey_berth):
    facts = decompose_floor(survey_berth, root=root)
    assert facts["stratum"] == "floor"
    assert facts["intent"] == "split the alpha work", \
        "the chain carries the upstream intent through all three links"
    assert facts["bounds"] == {"in": ["alpha"], "out": ["beta"]}, \
        "the split happens inside stage 2's bounds — they travel with the floor"
    assert facts["holdings"] == [{"what": "the settled chart machinery",
                                  "address": "chart"}], \
        "holdings travel VERBATIM from the survey berth"
    assert facts["holding_addresses"] == ["chart"], \
        "the compose vocabulary is exactly what the judges will check"
    assert facts["absence_whats"] == ["an alpha splitter"], \
        "the build vocabulary is exactly what the judges will check"


def test_schema_gate_refuses_hollow_shapes(root, orient_berth, constrain_berth,
                                           survey_berth):
    missing = good_packet(survey_berth)
    del missing["sub_problems"]
    expect_refusal(lambda: validate_decompose(missing, root=root), "sub_problems")
    unlisted = dict(good_packet(survey_berth), unknowns="not a list")
    expect_refusal(lambda: validate_decompose(unlisted, root=root), "must be a list")
    over = dict(good_packet(survey_berth), confidence=2.0)
    expect_refusal(lambda: validate_decompose(over, root=root), "confidence")
    uncovered = good_packet(survey_berth)
    del uncovered["provenance"]["sub_problems"]
    expect_refusal(lambda: validate_decompose(uncovered, root=root), "sub_problems")
    minted_ticket = dict(good_packet(survey_berth), ticket="no-such-ticket")
    expect_refusal(lambda: validate_decompose(minted_ticket, root=root),
                   "no-such-ticket")


def test_the_door_composes_the_installed_judges(root, orient_berth,
                                                constrain_berth, survey_berth):
    # Identity first: the door's judge IS the inspector's — one implementation,
    # two mouths, nothing to drift between.
    assert decompose_mod.judge_decompose is inspector_mod.judge_decompose
    rebuilt = dict(good_packet(survey_berth), sub_problems=[
        {"what": "compose a phantom", "why": "it is not held",
         "kind": "compose", "uses": ["no/such/thing.py"],
         "writes_to": ["chart/x.py"]}])
    expect_refusal(lambda: validate_decompose(rebuilt, root=root),
                   "decompose_composes_holdings")
    invented = dict(good_packet(survey_berth), sub_problems=[
        {"what": "build a whim", "why": "nobody measured it",
         "kind": "build", "fills": "a thing never sought",
         "writes_to": ["chart/x.py"]}])
    expect_refusal(lambda: validate_decompose(invented, root=root),
                   "decompose_builds_absences")
    whyless = dict(good_packet(survey_berth), sub_problems=[
        {"what": "a piece with no why", "why": "", "kind": "compose",
         "uses": ["chart"], "writes_to": ["chart/x.py"]}])
    expect_refusal(lambda: validate_decompose(whyless, root=root),
                   "decompose_composes_holdings")
    # And the inspector never imports decompose — the module cannot shape its judge.
    inspector_src = Path(inspector_mod.__file__).read_text(encoding="utf-8")
    assert "cairn.devices.codemother.machines.decompose.decompose" not in inspector_src, \
        "direction inversion: the judge's owner must never import the judged"


def test_every_piece_names_where_it_writes(root, orient_berth, constrain_berth,
                                           survey_berth):
    """Ticket a-piece-names-where-its-output-lands: the HARD half, and it lives here.

    `uses` cannot carry an output address by construction — it names survey HOLDINGS,
    things that exist — so a build piece's target is excluded from it by definition. The
    door demands `writes_to`; the promotion judge (the other mouth, over the standing
    corpus) deliberately does not.
    """
    from cairn.devices.codemother.machines.decompose.decompose import inspect_decompose

    naked = dict(good_packet(survey_berth), sub_problems=[
        {"what": "build the alpha splitter", "why": "measured absent",
         "kind": "build", "fills": "an alpha splitter"}])
    expect_refusal(lambda: validate_decompose(naked, root=root), "`writes_to`")
    empty = dict(good_packet(survey_berth), sub_problems=[
        {"what": "build the alpha splitter", "why": "measured absent",
         "kind": "build", "fills": "an alpha splitter", "writes_to": []}])
    expect_refusal(lambda: validate_decompose(empty, root=root), "no non-empty `writes_to`")
    blank = dict(good_packet(survey_berth), sub_problems=[
        {"what": "build the alpha splitter", "why": "measured absent",
         "kind": "build", "fills": "an alpha splitter", "writes_to": ["   "]}])
    expect_refusal(lambda: validate_decompose(blank, root=root), "not a non-empty string")
    outside = dict(good_packet(survey_berth), sub_problems=[
        {"what": "build the alpha splitter", "why": "measured absent",
         "kind": "build", "fills": "an alpha splitter",
         "writes_to": ["/etc/passwd"]}])
    expect_refusal(lambda: validate_decompose(outside, root=root), "outside the cairn repo")
    escaping = dict(good_packet(survey_berth), sub_problems=[
        {"what": "build the alpha splitter", "why": "measured absent",
         "kind": "build", "fills": "an alpha splitter",
         "writes_to": ["../../elsewhere.py"]}])
    expect_refusal(lambda: validate_decompose(escaping, root=root),
                   "outside the cairn repo")

    # THE DISTINCTION THE FIELD EXISTS FOR: the address does NOT have to exist. A build
    # piece names the file it is about to create, and a door that demanded existence
    # would forbid exactly the case the field was added to carry.
    assert not os.path.exists(os.path.join(root, "chart", "alpha_splitter.py"))
    validate_decompose(good_packet(survey_berth), root=root)

    # A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED: no pieces, no entry — the record
    # gets SHORTER, never cleaner, and required_fields_present has already closed the gate.
    ids = lambda p: [e["identity"] for e in inspect_decompose(p, root=root)]
    no_split = good_packet(survey_berth)
    del no_split["sub_problems"]
    assert "every_piece_names_where_it_writes" not in ids(no_split)
    assert "every_piece_names_where_it_writes" in ids(good_packet(survey_berth))

    # And the lack rides the SAME one-pass refusal as any other shape lack.
    both = dict(good_packet(survey_berth), confidence=2.0, sub_problems=[
        {"what": "build the alpha splitter", "why": "measured absent",
         "kind": "build", "fills": "an alpha splitter"}])
    try:
        validate_decompose(both, root=root)
        raise AssertionError("a doubly-defective packet passed the gate")
    except DecomposeRefused as e:
        assert "confidence" in str(e) and "`writes_to`" in str(e), str(e)


def test_the_berth_lands_and_the_door_holds(root, orient_berth, constrain_berth,
                                            survey_berth):
    berth_dir = os.path.join(root, "instance", "decompose_berth")
    packet = good_packet(survey_berth)
    path = write_decompose(packet, instance_dir=berth_dir, root=root)
    assert os.path.basename(path).startswith("decompose-")
    with open(path) as fh:
        assert json.load(fh) == packet, "the berthed packet round-trips whole"
    refused = dict(packet, sub_problems=[])
    try:
        write_decompose(refused, instance_dir=berth_dir, root=root)
        raise AssertionError("the door passed what the judges red")
    except DecomposeRefused:
        pass
    assert len(os.listdir(berth_dir)) == 1, \
        "a refused packet leaves nothing behind the door"


def test_deposit_back_is_gated(root, orient_berth, constrain_berth, survey_berth):
    berth_dir = os.path.join(root, "instance", "deposit_berth")
    packet = good_packet(survey_berth)
    berth = write_decompose(packet, instance_dir=berth_dir, root=root)
    content = decompose_node_content(packet)
    assert content.startswith("split the alpha work — SPLIT: ") \
        and "compose: compose the settled chart machinery" in content \
        and "build: build the alpha splitter" in content, \
        "the node content is the ONE rendering: upstream intent + the split, kinds visible"
    # A berth that does not exist refuses, tree untouched.
    table = nexus_table(_NEXUS)
    before = trees.tree_state(_NEXUS, table=table, owner="chart")
    expect_refusal(lambda: deposit_decompose(packet, [1.0, 0.0, 0.0],
                                             berth_path=berth + ".gone", root=root),
                   "does not exist")
    assert trees.tree_state(_NEXUS, table=table, owner="chart") == before
    # The real deposit lands in the decompose corpus with the berth as provenance.
    unique = content + f" [{_NEXUS}]"
    r = trees.deposit(unique, [1.0, 0.0, 0.0],
                      {"source": berth, "survey_ref": packet["survey_ref"],
                       "confidence": packet["confidence"]},
                      tree=_NEXUS, table=table, owner="chart")
    rows = store.read(trees.NODES_TABLE, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == unique
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["standing"] == "hypothesis"


def test_import_allowlist(root, orient_berth, constrain_berth, survey_berth):
    # Composed over orient's import_map: the allowlist matches the module that
    # ACTUALLY ENTERS, not the spelling.
    from cairn.tools.orient.orient import import_map
    allow = ("__future__", "hashlib", "json", "os", "time",
             "cairn.machines.build_inspector.inspector", "cairn.tools.chain.grammar",
             "cairn.devices.codemother.machines.survey.survey", "cairn.tools.tree.tree",
             # cairn.tools.gate joined 2026-08-13 (ruling every-machine-carries-
             # its-own-inspector-and-gate): this stage now holds its own gate, and
             # gate-ness is a DIRECT-import fact — which is how `cairn determinism`
             # and `cairnmap --gate` see it from outside without being told.
             "cairn.tools.gate.gate")
    seen = import_map(decompose_mod.__file__)["measured"]["imports"]
    offenders = [m for m in seen
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"decompose.py imports outside its allowlist: {offenders} — four composed "
        "doors only: the inspector's judge, chart's settled orient machinery, "
        "survey's chain reader, and chart's tree verbs (no census re-scan — the "
        "territory was measured in stage 3)")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            t = nexus_table(_NEXUS)
            cur.execute(f'DROP TABLE IF EXISTS "{t}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
    finally:
        conn.close()



def test_refusal_is_one_pass_complete(root, orient_berth, constrain_berth, survey_berth):
    """Ticket chart-doors-refuse-in-one-pass: a multi-defective packet learns EVERY
    shape lack in ONE refusal, a second identical firing names the identical set
    (no whack-a-mole), and a broken chain read names its remediation."""
    bad = good_packet(survey_berth)
    del bad["sub_problems"]
    bad["confidence"] = 2.0
    bad["provenance"] = dict(bad["provenance"], intruder="martian")

    def lack_set():
        try:
            validate_decompose(bad, root=root)
        except DecomposeRefused as e:
            msg = str(e)
            assert "all named on this one pass" in msg, msg
            return frozenset(l.strip() for l in msg.splitlines()
                             if l.strip().startswith("- "))
        raise AssertionError("multi-defective packet passed the gate")

    first, second = lack_set(), lack_set()
    assert first == second, (first, second)
    assert len(first) >= 3, first
    joined = " ".join(first)
    for needle in ("missing fields", "confidence", "stratum"):
        assert needle in joined, (needle, joined)
    try:
        decompose_floor(os.path.join(root, "no-such-berth.json"))
        raise AssertionError("floor read a berth that does not exist")
    except DecomposeRefused as e:
        assert "REMEDIATION" in str(e), str(e)



def test_request_identity_is_physics(root, orient_berth, constrain_berth, survey_berth):
    """Tickets berths-carry-request-identity + the-claim-rides-every-link: a packet
    claiming ticket A over a berth claiming ticket B is refused (MISMATCH), and a
    CLAIMLESS packet over that same claimed berth is refused (VANISH — Akien's
    verdict on cbbadb13530f: no warns, refuse and send back) — both named in the
    one-pass refusal."""
    foreign_doc = json.load(open(survey_berth))
    foreign_doc["ticket"] = "tkt-b"
    foreign = os.path.join(root, "foreign-decompose-ref.json")
    with open(foreign, "w") as fh:
        json.dump(foreign_doc, fh)
    bad = good_packet(survey_berth)
    bad["ticket"] = "tkt-a"
    bad["survey_ref"] = foreign
    try:
        validate_decompose(bad, root=root)
        raise AssertionError("claim-A packet passed over a claim-B berth")
    except DecomposeRefused as e:
        msg = str(e)
        assert "request-identity mismatch" in msg and "tkt-b" in msg, msg
    silent = good_packet(survey_berth)
    silent.pop("ticket", None)
    silent["survey_ref"] = foreign
    try:
        validate_decompose(silent, root=root)
        raise AssertionError("claimless packet passed over a claimed berth")
    except DecomposeRefused as e:
        msg = str(e)
        assert "request-identity vanished" in msg and "tkt-b" in msg, msg


def _main() -> int:
    root, orient_berth, constrain_berth, survey_berth = make_root()
    checks = [
        test_request_identity_is_physics,
        test_refusal_is_one_pass_complete,
        test_the_chain_is_physics_at_depth_4,
        test_floor_hands_the_judges_vocabularies_verbatim,
        test_schema_gate_refuses_hollow_shapes,
        test_the_door_composes_the_installed_judges,
        test_every_piece_names_where_it_writes,
        test_the_berth_lands_and_the_door_holds,
        test_deposit_back_is_gated,
        test_import_allowlist,
    ]
    try:
        for check in checks:
            check(root, orient_berth, constrain_berth, survey_berth)
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
        shutil.rmtree(os.path.dirname(root), ignore_errors=True)
    print("green — chart/decompose: stage 4 fills only through an unbroken "
          "three-link chain (survey's reader composed by identity), the floor "
          "hands the judges' vocabularies verbatim, the schema gate refuses "
          "hollow shapes, the door composes the inspector's own judges (by "
          "identity), the berth round-trips, the deposit-back is gated, and the "
          "brick's doors are exactly the four composed ones")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

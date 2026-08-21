"""Proof: the triage brick — the fourth stackable learning brick built UNDER
pre-installed judges (triage-filters, PROVED before this module existed).

Teeth a hollow build could not pass:
  - THE CHAIN IS PHYSICS AT DEPTH 5: stage 5 refuses without a berthed, readable
    stage-4 packet — AND refuses when any link below it (survey, constrain,
    orient) is gone or unreadable. The deep links are checked by COMPOSING
    decompose's own chain reader (one implementation of 'the chain holds'),
    asserted by identity, not parallel behavior.
  - THE FLOOR HANDS THE COVERAGE VOCABULARY VERBATIM: the pieces (what/why/kind
    and their evidence), the split's unknowns, and piece_whats — the exact
    multiset the order must cover — travel from the decompose berth exactly;
    the floor never decides the order.
  - THE SCHEMA GATE REFUSES what a hollow build would emit: missing fields, bad
    confidence, uncovered provenance, an unfiled ticket claim.
  - THE DOOR COMPOSES THE INSTALLED JUDGES: an order that drops a piece, ranks
    an invented one, or carries no why_now — each refused AT THE BERTH by the
    same judge_triage the promotion gate runs — asserted by identity. And the
    inspector never imports triage.
  - THE BERTH LANDS AND ROUND-TRIPS; a refused packet leaves nothing behind.
  - THE DEPOSIT-BACK IS GATED: content is the ONE rendering (intent + the
    order, positions visible), the berth must exist on disk, refusals leave the
    tree standing.
  - IMPORT ALLOWLIST over orient's import_map: triage.py composes exactly four
    cairn doors — the inspector's judge, chart's settled orient machinery,
    chart's decompose chain reader, and chart's tree verbs. No census re-scan,
    no db, no network.

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/devices/builder/machines/triage/proofs/test_chart_triage.py     # exit 0 = green
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
import cairn.devices.builder.machines.decompose.decompose as decompose_mod
from cairn.devices.builder.machines.triage import triage as triage_mod
from cairn.devices.builder.machines.triage.triage import (
    TriageRefused, deposit_triage, triage_floor, triage_node_content,
    validate_triage, write_triage,
)
from cairn.tools.tree.tree import nexus_table
from cairn.devices.db_domain import store
from cairn.devices.librarian import trees
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

_NEXUS = f"triage_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"


def make_root():
    """A synthetic world: the four-link chain stage 5 fills through — orient,
    constrain, survey (holding one address, measuring one absence), and a
    decompose berth splitting the work into one compose + one build piece."""
    tmp = str(scratch_dir("chart_triage_proof_"))
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    berth_dir = os.path.join(root, "instance", "packets")
    os.makedirs(berth_dir)
    orient_berth = os.path.join(berth_dir, "orient-20260728T180000-feedfeedfeed.json")
    with open(orient_berth, "w") as fh:
        json.dump({"intent": "rank the alpha work", "refs": ["chart"]}, fh)
    constrain_berth = os.path.join(berth_dir, "constrain-20260728T180001-cafecafecafe.json")
    with open(constrain_berth, "w") as fh:
        json.dump({"intent_ref": orient_berth,
                   "bounds": {"in": ["alpha"], "out": ["beta"]}}, fh)
    survey_berth = os.path.join(berth_dir, "survey-20260728T180002-beefbeefbeef.json")
    with open(survey_berth, "w") as fh:
        json.dump({"constrain_ref": constrain_berth,
                   "sought": ["the alpha territory"],
                   "holdings": [{"what": "the settled chart machinery",
                                 "address": "chart"}],
                   "absences": [{"what": "an alpha splitter",
                                 "measure": "path check, absent"}]}, fh)
    decompose_berth = os.path.join(berth_dir, "decompose-20260728T180003-d00dd00dd00d.json")
    with open(decompose_berth, "w") as fh:
        json.dump({"survey_ref": survey_berth,
                   "sub_problems": [
                       {"what": "compose the settled chart machinery",
                        "why": "it is held", "kind": "compose", "uses": ["chart"]},
                       {"what": "build the alpha splitter",
                        "why": "measured absent", "kind": "build",
                        "fills": "an alpha splitter"}],
                   "unknowns": ["whether the splitter needs a second seam"]}, fh)
    return root, survey_berth, decompose_berth


@pytest.fixture
def _world():
    return make_root()


@pytest.fixture
def root(_world):
    return _world[0]


@pytest.fixture
def survey_berth(_world):
    return _world[1]


@pytest.fixture
def decompose_berth(_world):
    return _world[2]


def good_packet(decompose_berth):
    return {
        "decompose_ref": decompose_berth,
        "order": [
            {"what": "build the alpha splitter",
             "why_now": "the layer below solidifies first"},
            {"what": "compose the settled chart machinery",
             "why_now": "rides on the splitter once it stands"},
        ],
        "unknowns": ["whether the splitter's seam question surfaces mid-build"],
        "confidence": 0.7,
        "provenance": {"decompose_ref": "floor", "order": "claude",
                       "unknowns": "claude"},
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except TriageRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected TriageRefused mentioning %r, got none" % needle)


def test_the_chain_is_physics_at_depth_5(root, survey_berth, decompose_berth):
    expect_refusal(lambda: triage_floor(os.path.join(root, "no-berth.json")),
                   "not a berthed packet")
    not_decompose = os.path.join(root, "not_decompose.json")
    with open(not_decompose, "w") as fh:
        json.dump({"weird": True}, fh)
    expect_refusal(lambda: triage_floor(not_decompose), "not a decompose berth")
    # The deep links: a decompose berth whose survey berth is GONE refuses —
    # through decompose's OWN reader, composed (identity below), never a
    # shallow fill.
    orphan = os.path.join(root, "orphan_decompose.json")
    with open(orphan, "w") as fh:
        json.dump({"survey_ref": os.path.join(root, "gone.json"),
                   "sub_problems": [], "unknowns": []}, fh)
    expect_refusal(lambda: triage_floor(orphan), "the chain broke")
    # ...and a chain whose CONSTRAIN link snapped two levels down refuses just
    # as loudly (depth 5).
    snapped_survey = os.path.join(root, "snapped_survey.json")
    with open(snapped_survey, "w") as fh:
        json.dump({"constrain_ref": os.path.join(root, "gone_constrain.json"),
                   "holdings": [], "absences": []}, fh)
    snapped = os.path.join(root, "snapped_decompose.json")
    with open(snapped, "w") as fh:
        json.dump({"survey_ref": snapped_survey,
                   "sub_problems": [], "unknowns": []}, fh)
    expect_refusal(lambda: triage_floor(snapped), "the chain broke")
    # The composition is BY IDENTITY: triage's deep-link reader IS decompose's.
    assert triage_mod._read_survey_berth is decompose_mod._read_survey_berth
    p = good_packet(decompose_berth)
    p["decompose_ref"] = os.path.join(root, "no-berth.json")
    expect_refusal(lambda: validate_triage(p, root=root), "not a berthed packet")


def test_floor_hands_the_coverage_vocabulary_verbatim(root, survey_berth,
                                                      decompose_berth):
    facts = triage_floor(decompose_berth, root=root)
    assert facts["stratum"] == "floor"
    assert facts["intent"] == "rank the alpha work", \
        "the chain carries the upstream intent through all four links"
    assert facts["bounds"] == {"in": ["alpha"], "out": ["beta"]}, \
        "the ranking happens inside stage 2's bounds — they travel with the floor"
    assert [sp["what"] for sp in facts["sub_problems"]] == \
        ["compose the settled chart machinery", "build the alpha splitter"], \
        "the pieces travel VERBATIM from the decompose berth"
    assert facts["split_unknowns"] == ["whether the splitter needs a second seam"], \
        "the split's unknowns ride the floor into the ranking"
    assert facts["piece_whats"] == ["build the alpha splitter",
                                    "compose the settled chart machinery"], \
        "the coverage vocabulary is exactly the multiset the judges will check"


def test_schema_gate_refuses_hollow_shapes(root, survey_berth, decompose_berth):
    missing = good_packet(decompose_berth)
    del missing["order"]
    expect_refusal(lambda: validate_triage(missing, root=root), "order")
    unlisted = dict(good_packet(decompose_berth), unknowns="not a list")
    expect_refusal(lambda: validate_triage(unlisted, root=root), "must be a list")
    over = dict(good_packet(decompose_berth), confidence=2.0)
    expect_refusal(lambda: validate_triage(over, root=root), "confidence")
    uncovered = good_packet(decompose_berth)
    del uncovered["provenance"]["order"]
    expect_refusal(lambda: validate_triage(uncovered, root=root), "order")
    minted_ticket = dict(good_packet(decompose_berth), ticket="no-such-ticket")
    expect_refusal(lambda: validate_triage(minted_ticket, root=root),
                   "no-such-ticket")


def test_the_door_composes_the_installed_judges(root, survey_berth,
                                                decompose_berth):
    # Identity first: the door's judge IS the inspector's — one implementation,
    # two mouths, nothing to drift between.
    assert triage_mod.judge_triage is inspector_mod.judge_triage
    dropped = dict(good_packet(decompose_berth),
                   order=good_packet(decompose_berth)["order"][:1])
    expect_refusal(lambda: validate_triage(dropped, root=root),
                   "triage_covers_the_split")
    invented = dict(good_packet(decompose_berth),
                    order=good_packet(decompose_berth)["order"] + [
                        {"what": "polish a whim", "why_now": "it would be nice"}])
    expect_refusal(lambda: validate_triage(invented, root=root),
                   "triage_covers_the_split")
    unreasoned = good_packet(decompose_berth)
    unreasoned["order"][0] = dict(unreasoned["order"][0], why_now="")
    expect_refusal(lambda: validate_triage(unreasoned, root=root),
                   "triage_reasons_the_order")
    # And the inspector never imports triage — the module cannot shape its judge.
    inspector_src = Path(inspector_mod.__file__).read_text(encoding="utf-8")
    assert "cairn.devices.builder.machines.triage.triage" not in inspector_src, \
        "direction inversion: the judge's owner must never import the judged"


def test_the_berth_lands_and_the_door_holds(root, survey_berth, decompose_berth):
    berth_dir = os.path.join(root, "instance", "triage_berth")
    packet = good_packet(decompose_berth)
    path = write_triage(packet, instance_dir=berth_dir, root=root)
    assert os.path.basename(path).startswith("triage-")
    with open(path) as fh:
        assert json.load(fh) == packet, "the berthed packet round-trips whole"
    refused = dict(packet, order=[])
    try:
        write_triage(refused, instance_dir=berth_dir, root=root)
        raise AssertionError("the door passed what the judges red")
    except TriageRefused:
        pass
    assert len(os.listdir(berth_dir)) == 1, \
        "a refused packet leaves nothing behind the door"


def test_deposit_back_is_gated(root, survey_berth, decompose_berth):
    berth_dir = os.path.join(root, "instance", "deposit_berth")
    packet = good_packet(decompose_berth)
    berth = write_triage(packet, instance_dir=berth_dir, root=root)
    content = triage_node_content(packet)
    assert content.startswith("rank the alpha work — ORDER: ") \
        and "1. build the alpha splitter" in content \
        and "2. compose the settled chart machinery" in content, \
        "the node content is the ONE rendering: upstream intent + the order, positions visible"
    # A berth that does not exist refuses, tree untouched.
    table = nexus_table(_NEXUS)
    before = trees.tree_state(_NEXUS, table=table, owner="chart")
    expect_refusal(lambda: deposit_triage(packet, [1.0, 0.0, 0.0],
                                          berth_path=berth + ".gone", root=root),
                   "does not exist")
    assert trees.tree_state(_NEXUS, table=table, owner="chart") == before
    # The real deposit lands in the triage corpus with the berth as provenance.
    unique = content + f" [{_NEXUS}]"
    r = trees.deposit(unique, [1.0, 0.0, 0.0],
                      {"source": berth, "decompose_ref": packet["decompose_ref"],
                       "confidence": packet["confidence"]},
                      tree=_NEXUS, table=table, owner="chart")
    rows = store.read(trees.NODES_TABLE, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == unique
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["standing"] == "hypothesis"


def test_import_allowlist(root, survey_berth, decompose_berth):
    # Composed over orient's import_map: the allowlist matches the module that
    # ACTUALLY ENTERS, not the spelling.
    from cairn.tools.orient.orient import import_map
    allow = ("__future__", "hashlib", "json", "os", "time",
             "cairn.machines.build_inspector.inspector", "cairn.devices.builder.machines.decompose.decompose",
             "cairn.tools.chain.grammar", "cairn.tools.tree.tree",
             # cairn.tools.gate joined 2026-08-13 (ruling every-machine-carries-
             # its-own-inspector-and-gate): this stage now holds its own gate, and
             # gate-ness is a DIRECT-import fact — which is how `cairn determinism`
             # and `cairnmap --gate` see it from outside without being told.
             "cairn.tools.gate.gate")
    seen = import_map(triage_mod.__file__)["measured"]["imports"]
    offenders = [m for m in seen
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"triage.py imports outside its allowlist: {offenders} — four composed "
        "doors only: the inspector's judge, decompose's chain reader, chart's "
        "settled orient machinery, and chart's tree verbs (the territory was "
        "measured in stage 3; the split in stage 4)")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            t = nexus_table(_NEXUS)
            cur.execute(f'DROP TABLE IF EXISTS "{t}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
    finally:
        conn.close()



def test_refusal_is_one_pass_complete(root, survey_berth, decompose_berth):
    """Ticket chart-doors-refuse-in-one-pass: a multi-defective packet learns EVERY
    shape lack in ONE refusal, a second identical firing names the identical set
    (no whack-a-mole), and a broken chain read names its remediation."""
    bad = good_packet(decompose_berth)
    del bad["order"]
    bad["confidence"] = 2.0
    bad["provenance"] = dict(bad["provenance"], intruder="martian")

    def lack_set():
        try:
            validate_triage(bad, root=root)
        except TriageRefused as e:
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
        triage_floor(os.path.join(root, "no-such-berth.json"))
        raise AssertionError("floor read a berth that does not exist")
    except TriageRefused as e:
        assert "REMEDIATION" in str(e), str(e)



def test_request_identity_is_physics(root, survey_berth, decompose_berth):
    """Tickets berths-carry-request-identity + the-claim-rides-every-link: a packet
    claiming ticket A over a berth claiming ticket B is refused (MISMATCH), and a
    CLAIMLESS packet over that same claimed berth is refused (VANISH — Akien's
    verdict on cbbadb13530f: no warns, refuse and send back) — both named in the
    one-pass refusal."""
    foreign_doc = json.load(open(decompose_berth))
    foreign_doc["ticket"] = "tkt-b"
    foreign = os.path.join(root, "foreign-triage-ref.json")
    with open(foreign, "w") as fh:
        json.dump(foreign_doc, fh)
    bad = good_packet(decompose_berth)
    bad["ticket"] = "tkt-a"
    bad["decompose_ref"] = foreign
    try:
        validate_triage(bad, root=root)
        raise AssertionError("claim-A packet passed over a claim-B berth")
    except TriageRefused as e:
        msg = str(e)
        assert "request-identity mismatch" in msg and "tkt-b" in msg, msg
    silent = good_packet(decompose_berth)
    silent.pop("ticket", None)
    silent["decompose_ref"] = foreign
    try:
        validate_triage(silent, root=root)
        raise AssertionError("claimless packet passed over a claimed berth")
    except TriageRefused as e:
        msg = str(e)
        assert "request-identity vanished" in msg and "tkt-b" in msg, msg


def _main() -> int:
    root, survey_berth, decompose_berth = make_root()
    checks = [
        test_request_identity_is_physics,
        test_refusal_is_one_pass_complete,
        test_the_chain_is_physics_at_depth_5,
        test_floor_hands_the_coverage_vocabulary_verbatim,
        test_schema_gate_refuses_hollow_shapes,
        test_the_door_composes_the_installed_judges,
        test_the_berth_lands_and_the_door_holds,
        test_deposit_back_is_gated,
        test_import_allowlist,
    ]
    try:
        for check in checks:
            check(root, survey_berth, decompose_berth)
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
        shutil.rmtree(os.path.dirname(root), ignore_errors=True)
    print("green — chart/triage: stage 5 fills only through an unbroken "
          "four-link chain (decompose's reader composed by identity), the floor "
          "hands the coverage vocabulary verbatim, the schema gate refuses "
          "hollow shapes, the door composes the inspector's own judges (by "
          "identity), the berth round-trips, the deposit-back is gated, and the "
          "brick's doors are exactly the four composed ones")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

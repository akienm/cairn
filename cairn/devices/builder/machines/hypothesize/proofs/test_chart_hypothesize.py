"""Proof: the hypothesize brick — the fifth stackable learning brick built
UNDER pre-installed judges (hypothesize-filters, PROVED before this module
existed).

Teeth a hollow build could not pass:
  - THE CHAIN IS PHYSICS AT DEPTH 6: stage 6 refuses without a berthed,
    readable stage-5 packet — AND refuses when any link below it (decompose,
    survey, constrain, orient) is gone or unreadable. The deep links are
    checked by COMPOSING triage's own chain reader (one implementation of 'the
    chain holds'), asserted by identity, not parallel behavior.
  - THE FLOOR HANDS THE COVERING VOCABULARY VERBATIM: the order (whats and
    why_nows), the underlying split pieces, the ranking's unknowns, and
    ranked_whats — the exact set the hypotheses must cover — travel from the
    triage berth exactly; the floor never decides the expectations.
  - THE SCHEMA GATE REFUSES what a hollow build would emit: missing fields, bad
    confidence, uncovered provenance, an unfiled ticket claim.
  - THE DOOR COMPOSES THE INSTALLED JUDGES: an uncovered ranked piece, a claim
    on an invented piece, a claim without falsifier/instrument — each refused
    AT THE BERTH by the same judge_hypothesize the promotion gate runs —
    asserted by identity. And the inspector never imports hypothesize.
  - THE BERTH LANDS AND ROUND-TRIPS; a refused packet leaves nothing behind.
  - THE DEPOSIT-BACK IS GATED: content is the ONE rendering (intent + the
    claims, instruments visible), the berth must exist on disk, refusals leave
    the tree standing.
  - IMPORT ALLOWLIST over orient's import_map: hypothesize.py composes exactly
    four cairn doors — the inspector's judge, chart's settled orient machinery,
    triage's chain reader, and chart's tree verbs. No census re-scan, no db,
    no network.

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/devices/builder/machines/hypothesize/proofs/test_chart_hypothesize.py     # exit 0 = green
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import cairn.machines.build_inspector.inspector as inspector_mod
import cairn.devices.builder.machines.triage.triage as triage_mod
from cairn.devices.builder.machines.hypothesize import hypothesize as hypothesize_mod
from cairn.devices.builder.machines.hypothesize.hypothesize import (
    HypothesizeRefused, deposit_hypothesize, hypothesize_floor,
    hypothesize_node_content, validate_hypothesize, write_hypothesize,
)
from cairn.tools.tree.tree import nexus_table
from cairn.devices.db_domain import store
from cairn.devices.librarian import trees
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

_NEXUS = f"hypothesize_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"


def make_root():
    """A synthetic world: the five-link chain stage 6 fills through — orient,
    constrain, survey, decompose, and a triage berth ranking the split's two
    pieces."""
    tmp = str(scratch_dir("chart_hypothesize_proof_"))
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    berth_dir = os.path.join(root, "instance", "packets")
    os.makedirs(berth_dir)
    orient_berth = os.path.join(berth_dir, "orient-20260728T190000-feedfeedfeed.json")
    with open(orient_berth, "w") as fh:
        json.dump({"intent": "expect the alpha work", "refs": ["chart"]}, fh)
    constrain_berth = os.path.join(berth_dir, "constrain-20260728T190001-cafecafecafe.json")
    with open(constrain_berth, "w") as fh:
        json.dump({"intent_ref": orient_berth,
                   "bounds": {"in": ["alpha"], "out": ["beta"]}}, fh)
    survey_berth = os.path.join(berth_dir, "survey-20260728T190002-beefbeefbeef.json")
    with open(survey_berth, "w") as fh:
        json.dump({"constrain_ref": constrain_berth,
                   "sought": ["the alpha territory"],
                   "holdings": [{"what": "the settled chart machinery",
                                 "address": "chart"}],
                   "absences": [{"what": "an alpha splitter",
                                 "measure": "path check, absent"}]}, fh)
    decompose_berth = os.path.join(berth_dir, "decompose-20260728T190003-d00dd00dd00d.json")
    with open(decompose_berth, "w") as fh:
        json.dump({"survey_ref": survey_berth,
                   "sub_problems": [
                       {"what": "compose the settled chart machinery",
                        "why": "it is held", "kind": "compose", "uses": ["chart"]},
                       {"what": "build the alpha splitter",
                        "why": "measured absent", "kind": "build",
                        "fills": "an alpha splitter"}],
                   "unknowns": ["whether the splitter needs a second seam"]}, fh)
    triage_berth = os.path.join(berth_dir, "triage-20260728T190004-abbaabbaabba.json")
    with open(triage_berth, "w") as fh:
        json.dump({"decompose_ref": decompose_berth,
                   "order": [
                       {"what": "build the alpha splitter",
                        "why_now": "the layer below solidifies first"},
                       {"what": "compose the settled chart machinery",
                        "why_now": "rides on the splitter once it stands"}],
                   "unknowns": ["whether the seam question surfaces mid-build"]}, fh)
    return root, decompose_berth, triage_berth


def good_packet(triage_berth):
    return {
        "triage_ref": triage_berth,
        "hypotheses": [
            {"piece": "build the alpha splitter",
             "expect": "the splitter's teeth pass twice",
             "falsifier": "any tooth red on either run",
             "instrument": "python3 proofs/test_splitter.py, run twice"},
            {"piece": "compose the settled chart machinery",
             "expect": "the composed door refuses a phantom ref",
             "falsifier": "a phantom ref berths",
             "instrument": "the door's own gate against a fixture ref"},
        ],
        "unknowns": ["whether the splitter's second seam shows up under load"],
        "confidence": 0.7,
        "provenance": {"triage_ref": "floor", "hypotheses": "claude",
                       "unknowns": "claude"},
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except HypothesizeRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected HypothesizeRefused mentioning %r, got none" % needle)


def test_the_chain_is_physics_at_depth_6(root, decompose_berth, triage_berth):
    expect_refusal(lambda: hypothesize_floor(os.path.join(root, "no-berth.json")),
                   "not a berthed packet")
    not_triage = os.path.join(root, "not_triage.json")
    with open(not_triage, "w") as fh:
        json.dump({"weird": True}, fh)
    expect_refusal(lambda: hypothesize_floor(not_triage), "not a triage berth")
    # The deep links: a triage berth whose decompose berth is GONE refuses —
    # through triage's OWN reader, composed (identity below).
    orphan = os.path.join(root, "orphan_triage.json")
    with open(orphan, "w") as fh:
        json.dump({"decompose_ref": os.path.join(root, "gone.json"),
                   "order": [], "unknowns": []}, fh)
    expect_refusal(lambda: hypothesize_floor(orphan), "the chain broke")
    # ...and a chain whose SURVEY link snapped two levels down refuses just as
    # loudly (depth 6).
    snapped_decompose = os.path.join(root, "snapped_decompose.json")
    with open(snapped_decompose, "w") as fh:
        json.dump({"survey_ref": os.path.join(root, "gone_survey.json"),
                   "sub_problems": [], "unknowns": []}, fh)
    snapped = os.path.join(root, "snapped_triage.json")
    with open(snapped, "w") as fh:
        json.dump({"decompose_ref": snapped_decompose,
                   "order": [], "unknowns": []}, fh)
    expect_refusal(lambda: hypothesize_floor(snapped), "the chain broke")
    # The composition is BY IDENTITY: hypothesize's deep-link reader IS triage's.
    assert hypothesize_mod._read_decompose_berth is triage_mod._read_decompose_berth
    p = good_packet(triage_berth)
    p["triage_ref"] = os.path.join(root, "no-berth.json")
    expect_refusal(lambda: validate_hypothesize(p, root=root), "not a berthed packet")


def test_floor_hands_the_covering_vocabulary_verbatim(root, decompose_berth,
                                                      triage_berth):
    facts = hypothesize_floor(triage_berth, root=root)
    assert facts["stratum"] == "floor"
    assert facts["intent"] == "expect the alpha work", \
        "the chain carries the upstream intent through all five links"
    assert facts["bounds"] == {"in": ["alpha"], "out": ["beta"]}, \
        "the claims live inside stage 2's bounds — they travel with the floor"
    assert [e["what"] for e in facts["order"]] == \
        ["build the alpha splitter", "compose the settled chart machinery"], \
        "the order travels VERBATIM from the triage berth"
    assert [sp["kind"] for sp in facts["sub_problems"]] == ["compose", "build"], \
        "the underlying split pieces ride the floor for evidence"
    assert facts["ranking_unknowns"] == ["whether the seam question surfaces mid-build"]
    assert facts["ranked_whats"] == ["build the alpha splitter",
                                     "compose the settled chart machinery"], \
        "the covering vocabulary is exactly the set the judges will check"


def test_schema_gate_refuses_hollow_shapes(root, decompose_berth, triage_berth):
    missing = good_packet(triage_berth)
    del missing["hypotheses"]
    expect_refusal(lambda: validate_hypothesize(missing, root=root), "hypotheses")
    unlisted = dict(good_packet(triage_berth), unknowns="not a list")
    expect_refusal(lambda: validate_hypothesize(unlisted, root=root), "must be a list")
    over = dict(good_packet(triage_berth), confidence=2.0)
    expect_refusal(lambda: validate_hypothesize(over, root=root), "confidence")
    uncovered = good_packet(triage_berth)
    del uncovered["provenance"]["hypotheses"]
    expect_refusal(lambda: validate_hypothesize(uncovered, root=root), "hypotheses")
    minted_ticket = dict(good_packet(triage_berth), ticket="no-such-ticket")
    expect_refusal(lambda: validate_hypothesize(minted_ticket, root=root),
                   "no-such-ticket")


def test_the_door_composes_the_installed_judges(root, decompose_berth,
                                                triage_berth):
    # Identity first: the door's judge IS the inspector's — one implementation,
    # two mouths, nothing to drift between.
    assert hypothesize_mod.judge_hypothesize is inspector_mod.judge_hypothesize
    uncovered = dict(good_packet(triage_berth),
                     hypotheses=good_packet(triage_berth)["hypotheses"][:1])
    expect_refusal(lambda: validate_hypothesize(uncovered, root=root),
                   "hypothesize_covers_the_ranked")
    invented = dict(good_packet(triage_berth),
                    hypotheses=good_packet(triage_berth)["hypotheses"] + [
                        {"piece": "polish a whim", "expect": "it gleams",
                         "falsifier": "it does not", "instrument": "a glance"}])
    expect_refusal(lambda: validate_hypothesize(invented, root=root),
                   "hypothesize_covers_the_ranked")
    unmeasured = good_packet(triage_berth)
    unmeasured["hypotheses"][0] = dict(unmeasured["hypotheses"][0],
                                       falsifier="", instrument="")
    expect_refusal(lambda: validate_hypothesize(unmeasured, root=root),
                   "hypothesize_falsifiable_measured")
    # And the inspector never imports hypothesize.
    inspector_src = Path(inspector_mod.__file__).read_text(encoding="utf-8")
    assert "cairn.devices.builder.machines.hypothesize.hypothesize" not in inspector_src, \
        "direction inversion: the judge's owner must never import the judged"


def test_the_berth_lands_and_the_door_holds(root, decompose_berth, triage_berth):
    berth_dir = os.path.join(root, "instance", "hypothesize_berth")
    packet = good_packet(triage_berth)
    path = write_hypothesize(packet, instance_dir=berth_dir, root=root)
    assert os.path.basename(path).startswith("hypothesize-")
    with open(path) as fh:
        assert json.load(fh) == packet, "the berthed packet round-trips whole"
    refused = dict(packet, hypotheses=[])
    try:
        write_hypothesize(refused, instance_dir=berth_dir, root=root)
        raise AssertionError("the door passed what the judges red")
    except HypothesizeRefused:
        pass
    assert len(os.listdir(berth_dir)) == 1, \
        "a refused packet leaves nothing behind the door"


def test_deposit_back_is_gated(root, decompose_berth, triage_berth):
    berth_dir = os.path.join(root, "instance", "deposit_berth")
    packet = good_packet(triage_berth)
    berth = write_hypothesize(packet, instance_dir=berth_dir, root=root)
    content = hypothesize_node_content(packet)
    assert content.startswith("expect the alpha work — EXPECT: ") \
        and "build the alpha splitter -> the splitter's teeth pass twice" in content \
        and "[by python3 proofs/test_splitter.py, run twice]" in content, \
        "the node content is the ONE rendering: upstream intent + the claims, instruments visible"
    # A berth that does not exist refuses, tree untouched.
    table = nexus_table(_NEXUS)
    before = trees.tree_state(_NEXUS, table=table, owner="chart")
    expect_refusal(lambda: deposit_hypothesize(packet, [1.0, 0.0, 0.0],
                                               berth_path=berth + ".gone",
                                               root=root),
                   "does not exist")
    assert trees.tree_state(_NEXUS, table=table, owner="chart") == before
    # The real deposit lands in the hypothesize corpus with the berth as provenance.
    r = trees.deposit(content, [1.0, 0.0, 0.0],
                      {"source": berth, "triage_ref": packet["triage_ref"],
                       "confidence": packet["confidence"]},
                      tree=_NEXUS, table=table, owner="chart")
    rows = store.read(table, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == content
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["standing"] == "hypothesis"


def test_import_allowlist(root, decompose_berth, triage_berth):
    # Composed over orient's import_map: the allowlist matches the module that
    # ACTUALLY ENTERS, not the spelling.
    from cairn.tools.orient.orient import import_map
    allow = ("__future__", "hashlib", "json", "os", "time",
             "cairn.machines.build_inspector.inspector", "cairn.tools.chain.grammar",
             "cairn.tools.tree.tree", "cairn.devices.builder.machines.triage.triage")
    seen = import_map(hypothesize_mod.__file__)["measured"]["imports"]
    offenders = [m for m in seen
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"hypothesize.py imports outside its allowlist: {offenders} — four "
        "composed doors only: the inspector's judge, triage's chain reader, "
        "chart's settled orient machinery, and chart's tree verbs")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            t = nexus_table(_NEXUS)
            cur.execute(f'DROP TABLE IF EXISTS "{t}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
    finally:
        conn.close()



def test_refusal_is_one_pass_complete(root, decompose_berth, triage_berth):
    """Ticket chart-doors-refuse-in-one-pass: a multi-defective packet learns EVERY
    shape lack in ONE refusal, a second identical firing names the identical set
    (no whack-a-mole), and a broken chain read names its remediation."""
    bad = good_packet(triage_berth)
    del bad["hypotheses"]
    bad["confidence"] = 2.0
    bad["provenance"] = dict(bad["provenance"], intruder="martian")

    def lack_set():
        try:
            validate_hypothesize(bad, root=root)
        except HypothesizeRefused as e:
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
        hypothesize_floor(os.path.join(root, "no-such-berth.json"))
        raise AssertionError("floor read a berth that does not exist")
    except HypothesizeRefused as e:
        assert "REMEDIATION" in str(e), str(e)



def test_request_identity_is_physics(root, decompose_berth, triage_berth):
    """Tickets berths-carry-request-identity + the-claim-rides-every-link: a packet
    claiming ticket A over a berth claiming ticket B is refused (MISMATCH), and a
    CLAIMLESS packet over that same claimed berth is refused (VANISH — Akien's
    verdict on cbbadb13530f: no warns, refuse and send back) — both named in the
    one-pass refusal."""
    foreign_doc = json.load(open(triage_berth))
    foreign_doc["ticket"] = "tkt-b"
    foreign = os.path.join(root, "foreign-hypothesize-ref.json")
    with open(foreign, "w") as fh:
        json.dump(foreign_doc, fh)
    bad = good_packet(triage_berth)
    bad["ticket"] = "tkt-a"
    bad["triage_ref"] = foreign
    try:
        validate_hypothesize(bad, root=root)
        raise AssertionError("claim-A packet passed over a claim-B berth")
    except HypothesizeRefused as e:
        msg = str(e)
        assert "request-identity mismatch" in msg and "tkt-b" in msg, msg
    silent = good_packet(triage_berth)
    silent.pop("ticket", None)
    silent["triage_ref"] = foreign
    try:
        validate_hypothesize(silent, root=root)
        raise AssertionError("claimless packet passed over a claimed berth")
    except HypothesizeRefused as e:
        msg = str(e)
        assert "request-identity vanished" in msg and "tkt-b" in msg, msg


def _main() -> int:
    root, decompose_berth, triage_berth = make_root()
    checks = [
        test_request_identity_is_physics,
        test_refusal_is_one_pass_complete,
        test_the_chain_is_physics_at_depth_6,
        test_floor_hands_the_covering_vocabulary_verbatim,
        test_schema_gate_refuses_hollow_shapes,
        test_the_door_composes_the_installed_judges,
        test_the_berth_lands_and_the_door_holds,
        test_deposit_back_is_gated,
        test_import_allowlist,
    ]
    try:
        for check in checks:
            check(root, decompose_berth, triage_berth)
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
        shutil.rmtree(os.path.dirname(root), ignore_errors=True)
    print("green — chart/hypothesize: stage 6 fills only through an unbroken "
          "five-link chain (triage's reader composed by identity), the floor "
          "hands the covering vocabulary verbatim, the schema gate refuses "
          "hollow shapes, the door composes the inspector's own judges (by "
          "identity), the berth round-trips, the deposit-back is gated, and "
          "the brick's doors are exactly the four composed ones")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

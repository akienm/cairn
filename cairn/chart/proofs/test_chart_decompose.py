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
  - THE BERTH LANDS AND ROUND-TRIPS; a refused packet leaves nothing behind.
  - THE DEPOSIT-BACK IS GATED: content is the ONE rendering (intent + the
    split, kinds visible), the berth must exist on disk, refusals leave the
    tree standing.
  - IMPORT ALLOWLIST over orient's import_map: decompose.py composes exactly
    four cairn doors — the inspector's judge, chart's settled orient machinery,
    chart's survey chain reader, and chart's tree verbs. No census re-scan (the
    territory was measured in stage 3), no db, no network.

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/chart/proofs/test_chart_decompose.py     # exit 0 = green
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
import cairn.chart.survey as survey_mod
from cairn.chart import decompose as decompose_mod
from cairn.chart.decompose import (
    DecomposeRefused, decompose_floor, decompose_node_content,
    deposit_decompose, validate_decompose, write_decompose,
)
from cairn.chart.tree import nexus_table
from cairn.db_domain import store
from cairn.librarian import trees

_NEXUS = f"decompose_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"


def make_root():
    """A synthetic world: the three-link chain stage 4 fills through — a berthed
    orient packet, a constrain packet chained to it, and a survey packet chained
    to that, holding one address and measuring one absence."""
    tmp = tempfile.mkdtemp(prefix="chart_decompose_proof_")
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


def good_packet(survey_berth):
    return {
        "survey_ref": survey_berth,
        "sub_problems": [
            {"what": "compose the settled chart machinery", "why": "it is held",
             "kind": "compose", "uses": ["chart"]},
            {"what": "build the alpha splitter", "why": "measured absent",
             "kind": "build", "fills": "an alpha splitter"},
        ],
        "unknowns": ["whether the splitter needs a second seam"],
        "confidence": 0.7,
        "provenance": {"survey_ref": "floor", "sub_problems": "claude",
                       "unknowns": "claude"},
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
         "kind": "compose", "uses": ["no/such/thing.py"]}])
    expect_refusal(lambda: validate_decompose(rebuilt, root=root),
                   "decompose_composes_holdings")
    invented = dict(good_packet(survey_berth), sub_problems=[
        {"what": "build a whim", "why": "nobody measured it",
         "kind": "build", "fills": "a thing never sought"}])
    expect_refusal(lambda: validate_decompose(invented, root=root),
                   "decompose_builds_absences")
    whyless = dict(good_packet(survey_berth), sub_problems=[
        {"what": "a piece with no why", "why": "", "kind": "compose",
         "uses": ["chart"]}])
    expect_refusal(lambda: validate_decompose(whyless, root=root),
                   "decompose_composes_holdings")
    # And the inspector never imports decompose — the module cannot shape its judge.
    inspector_src = Path(inspector_mod.__file__).read_text(encoding="utf-8")
    assert "cairn.chart.decompose" not in inspector_src, \
        "direction inversion: the judge's owner must never import the judged"


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
    r = trees.deposit(content, [1.0, 0.0, 0.0],
                      {"source": berth, "survey_ref": packet["survey_ref"],
                       "confidence": packet["confidence"]},
                      tree=_NEXUS, table=table, owner="chart")
    rows = store.read(table, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == content
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["standing"] == "hypothesis"


def test_import_allowlist(root, orient_berth, constrain_berth, survey_berth):
    # Composed over orient's import_map: the allowlist matches the module that
    # ACTUALLY ENTERS, not the spelling.
    from cairn.orient.orient import import_map
    allow = ("__future__", "hashlib", "json", "os", "time",
             "cairn.build_inspector.inspector", "cairn.chart.orient",
             "cairn.chart.survey", "cairn.chart.tree")
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


def _main() -> int:
    root, orient_berth, constrain_berth, survey_berth = make_root()
    checks = [
        test_the_chain_is_physics_at_depth_4,
        test_floor_hands_the_judges_vocabularies_verbatim,
        test_schema_gate_refuses_hollow_shapes,
        test_the_door_composes_the_installed_judges,
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

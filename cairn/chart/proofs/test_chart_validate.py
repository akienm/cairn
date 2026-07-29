"""Proof: the validate brick — the sixth stackable learning brick built UNDER
pre-installed judges (validate-filters, PROVED before this module existed) and
the stone plan's LAST stage.

Teeth a hollow build could not pass:
  - THE CHAIN IS PHYSICS AT DEPTH 7: stage 7 refuses without a berthed,
    readable stage-6 packet — AND refuses when any link below it is gone or
    unreadable. The deep links are checked by COMPOSING hypothesize's own
    chain reader, asserted by identity, not parallel behavior.
  - THE FLOOR HANDS THE ACCEPTANCE VOCABULARY VERBATIM: the hypotheses (whose
    instruments criteria may compose), the order, the expectations' unknowns,
    and claimed_pieces — the exact set covers must exhaust — travel from the
    hypothesize berth exactly; the floor never decides what done means.
  - THE SCHEMA GATE REFUSES what a hollow build would emit: missing fields,
    bad confidence, uncovered provenance, an unfiled ticket claim.
  - THE DOOR COMPOSES THE INSTALLED JUDGES: an instrument-less criterion, a
    covers entry on an unclaimed piece, a claimed piece left uncovered — each
    refused AT THE BERTH by the same judge_validate the promotion gate runs —
    asserted by identity. And the inspector never imports validate.
  - THE BERTH LANDS AND ROUND-TRIPS; a refused packet leaves nothing behind.
  - THE DEPOSIT-BACK IS GATED: content is the ONE rendering (intent + the
    criteria, instruments visible), the berth must exist on disk, refusals
    leave the tree standing.
  - IMPORT ALLOWLIST over orient's import_map: validate.py composes exactly
    four cairn doors — the inspector's judge, hypothesize's chain reader,
    chart's settled orient machinery, and chart's tree verbs.

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/chart/proofs/test_chart_validate.py     # exit 0 = green
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
import cairn.chart.hypothesize as hypothesize_mod
from cairn.chart import validate as validate_mod
from cairn.chart.validate import (
    ValidateRefused, deposit_validate, validate_floor, validate_node_content,
    validate_validate, write_validate,
)
from cairn.chart.tree import nexus_table
from cairn.db_domain import store
from cairn.librarian import trees

_NEXUS = f"validate_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"


def make_root():
    """A synthetic world: the six-link chain stage 7 fills through — orient,
    constrain, survey, decompose, triage, and a hypothesize berth claiming
    both ranked pieces."""
    tmp = tempfile.mkdtemp(prefix="chart_validate_proof_")
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    berth_dir = os.path.join(root, "instance", "packets")
    os.makedirs(berth_dir)
    orient_berth = os.path.join(berth_dir, "orient-20260728T200000-feedfeedfeed.json")
    with open(orient_berth, "w") as fh:
        json.dump({"intent": "accept the alpha work", "refs": ["chart"]}, fh)
    constrain_berth = os.path.join(berth_dir, "constrain-20260728T200001-cafecafecafe.json")
    with open(constrain_berth, "w") as fh:
        json.dump({"intent_ref": orient_berth,
                   "bounds": {"in": ["alpha"], "out": ["beta"]}}, fh)
    survey_berth = os.path.join(berth_dir, "survey-20260728T200002-beefbeefbeef.json")
    with open(survey_berth, "w") as fh:
        json.dump({"constrain_ref": constrain_berth,
                   "sought": ["the alpha territory"],
                   "holdings": [{"what": "the settled chart machinery",
                                 "address": "chart"}],
                   "absences": [{"what": "an alpha splitter",
                                 "measure": "path check, absent"}]}, fh)
    decompose_berth = os.path.join(berth_dir, "decompose-20260728T200003-d00dd00dd00d.json")
    with open(decompose_berth, "w") as fh:
        json.dump({"survey_ref": survey_berth,
                   "sub_problems": [
                       {"what": "compose the settled chart machinery",
                        "why": "it is held", "kind": "compose", "uses": ["chart"]},
                       {"what": "build the alpha splitter",
                        "why": "measured absent", "kind": "build",
                        "fills": "an alpha splitter"}],
                   "unknowns": []}, fh)
    triage_berth = os.path.join(berth_dir, "triage-20260728T200004-abbaabbaabba.json")
    with open(triage_berth, "w") as fh:
        json.dump({"decompose_ref": decompose_berth,
                   "order": [
                       {"what": "build the alpha splitter",
                        "why_now": "the layer below solidifies first"},
                       {"what": "compose the settled chart machinery",
                        "why_now": "rides on the splitter once it stands"}],
                   "unknowns": []}, fh)
    hypothesize_berth = os.path.join(berth_dir, "hypothesize-20260728T200005-c0dec0dec0de.json")
    with open(hypothesize_berth, "w") as fh:
        json.dump({"triage_ref": triage_berth,
                   "hypotheses": [
                       {"piece": "build the alpha splitter",
                        "expect": "the splitter's teeth pass twice",
                        "falsifier": "any tooth red on either run",
                        "instrument": "python3 proofs/test_splitter.py, twice"},
                       {"piece": "compose the settled chart machinery",
                        "expect": "the composed door refuses a phantom ref",
                        "falsifier": "a phantom ref berths",
                        "instrument": "the door's own gate, fixture ref"}],
                   "unknowns": ["whether the seam question surfaces"]}, fh)
    return root, triage_berth, hypothesize_berth


def good_packet(hypothesize_berth):
    return {
        "hypothesize_ref": hypothesize_berth,
        "criteria": [
            {"claim": "the splitter is green under the tester's seal, twice",
             "instrument": "python3 proofs/test_splitter.py, twice (composing the hypothesis's instrument)",
             "covers": ["build the alpha splitter"]},
            {"claim": "the composed machinery holds at promotion",
             "instrument": "inspect(component=alpha), clean",
             "covers": ["compose the settled chart machinery"]},
        ],
        "unknowns": ["whether acceptance wants a third, whole-system criterion"],
        "confidence": 0.7,
        "provenance": {"hypothesize_ref": "floor", "criteria": "claude",
                       "unknowns": "claude"},
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except ValidateRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected ValidateRefused mentioning %r, got none" % needle)


def test_the_chain_is_physics_at_depth_7(root, triage_berth, hypothesize_berth):
    expect_refusal(lambda: validate_floor(os.path.join(root, "no-berth.json")),
                   "not a berthed packet")
    not_hyp = os.path.join(root, "not_hypothesize.json")
    with open(not_hyp, "w") as fh:
        json.dump({"weird": True}, fh)
    expect_refusal(lambda: validate_floor(not_hyp), "not a hypothesize berth")
    # The deep links: a hypothesize berth whose triage berth is GONE refuses —
    # through hypothesize's OWN reader, composed (identity below).
    orphan = os.path.join(root, "orphan_hypothesize.json")
    with open(orphan, "w") as fh:
        json.dump({"triage_ref": os.path.join(root, "gone.json"),
                   "hypotheses": [], "unknowns": []}, fh)
    expect_refusal(lambda: validate_floor(orphan), "the chain broke")
    # ...and a chain whose DECOMPOSE link snapped two levels down refuses just
    # as loudly (depth 7).
    snapped_triage = os.path.join(root, "snapped_triage.json")
    with open(snapped_triage, "w") as fh:
        json.dump({"decompose_ref": os.path.join(root, "gone_decompose.json"),
                   "order": [], "unknowns": []}, fh)
    snapped = os.path.join(root, "snapped_hypothesize.json")
    with open(snapped, "w") as fh:
        json.dump({"triage_ref": snapped_triage,
                   "hypotheses": [], "unknowns": []}, fh)
    expect_refusal(lambda: validate_floor(snapped), "the chain broke")
    # The composition is BY IDENTITY: validate's deep-link reader IS hypothesize's.
    assert validate_mod._read_triage_berth is hypothesize_mod._read_triage_berth
    p = good_packet(hypothesize_berth)
    p["hypothesize_ref"] = os.path.join(root, "no-berth.json")
    expect_refusal(lambda: validate_validate(p, root=root), "not a berthed packet")


def test_floor_hands_the_acceptance_vocabulary_verbatim(root, triage_berth,
                                                        hypothesize_berth):
    facts = validate_floor(hypothesize_berth, root=root)
    assert facts["stratum"] == "floor"
    assert facts["intent"] == "accept the alpha work", \
        "the chain carries the upstream intent through all six links"
    assert facts["bounds"] == {"in": ["alpha"], "out": ["beta"]}, \
        "acceptance lives inside stage 2's bounds — they travel with the floor"
    assert [h["piece"] for h in facts["hypotheses"]] == \
        ["build the alpha splitter", "compose the settled chart machinery"], \
        "the hypotheses travel VERBATIM — their instruments are composable"
    assert [e["what"] for e in facts["order"]] == \
        ["build the alpha splitter", "compose the settled chart machinery"], \
        "the order rides the floor for the acceptance run's sequencing"
    assert facts["expectation_unknowns"] == ["whether the seam question surfaces"]
    assert facts["claimed_pieces"] == ["build the alpha splitter",
                                       "compose the settled chart machinery"], \
        "the acceptance vocabulary is exactly the set covers must exhaust"


def test_schema_gate_refuses_hollow_shapes(root, triage_berth, hypothesize_berth):
    missing = good_packet(hypothesize_berth)
    del missing["criteria"]
    expect_refusal(lambda: validate_validate(missing, root=root), "criteria")
    unlisted = dict(good_packet(hypothesize_berth), unknowns="not a list")
    expect_refusal(lambda: validate_validate(unlisted, root=root), "must be a list")
    over = dict(good_packet(hypothesize_berth), confidence=2.0)
    expect_refusal(lambda: validate_validate(over, root=root), "confidence")
    uncovered = good_packet(hypothesize_berth)
    del uncovered["provenance"]["criteria"]
    expect_refusal(lambda: validate_validate(uncovered, root=root), "criteria")
    minted_ticket = dict(good_packet(hypothesize_berth), ticket="no-such-ticket")
    expect_refusal(lambda: validate_validate(minted_ticket, root=root),
                   "no-such-ticket")


def test_the_door_composes_the_installed_judges(root, triage_berth,
                                                hypothesize_berth):
    # Identity first: the door's judge IS the inspector's — one implementation,
    # two mouths, nothing to drift between.
    assert validate_mod.judge_validate is inspector_mod.judge_validate
    unmeasured = good_packet(hypothesize_berth)
    unmeasured["criteria"][0] = dict(unmeasured["criteria"][0], instrument="")
    expect_refusal(lambda: validate_validate(unmeasured, root=root),
                   "validate_measures_done")
    partial = dict(good_packet(hypothesize_berth),
                   criteria=good_packet(hypothesize_berth)["criteria"][:1])
    expect_refusal(lambda: validate_validate(partial, root=root),
                   "validate_covers_the_build")
    unclaimed = dict(good_packet(hypothesize_berth),
                     criteria=good_packet(hypothesize_berth)["criteria"] + [
                         {"claim": "a whim gleams", "instrument": "a glance",
                          "covers": ["polish a whim"]}])
    expect_refusal(lambda: validate_validate(unclaimed, root=root),
                   "validate_covers_the_build")
    # And the inspector never imports validate.
    inspector_src = Path(inspector_mod.__file__).read_text(encoding="utf-8")
    assert "cairn.chart.validate" not in inspector_src, \
        "direction inversion: the judge's owner must never import the judged"


def test_the_berth_lands_and_the_door_holds(root, triage_berth, hypothesize_berth):
    berth_dir = os.path.join(root, "instance", "validate_berth")
    packet = good_packet(hypothesize_berth)
    path = write_validate(packet, instance_dir=berth_dir, root=root)
    assert os.path.basename(path).startswith("validate-")
    with open(path) as fh:
        assert json.load(fh) == packet, "the berthed packet round-trips whole"
    refused = dict(packet, criteria=[])
    try:
        write_validate(refused, instance_dir=berth_dir, root=root)
        raise AssertionError("the door passed what the judges red")
    except ValidateRefused:
        pass
    assert len(os.listdir(berth_dir)) == 1, \
        "a refused packet leaves nothing behind the door"


def test_deposit_back_is_gated(root, triage_berth, hypothesize_berth):
    berth_dir = os.path.join(root, "instance", "deposit_berth")
    packet = good_packet(hypothesize_berth)
    berth = write_validate(packet, instance_dir=berth_dir, root=root)
    content = validate_node_content(packet)
    assert content.startswith("accept the alpha work — DONE MEANS: ") \
        and "the splitter is green under the tester's seal, twice" in content \
        and "[by inspect(component=alpha), clean]" in content, \
        "the node content is the ONE rendering: upstream intent + the criteria, instruments visible"
    # A berth that does not exist refuses, tree untouched.
    table = nexus_table(_NEXUS)
    before = trees.tree_state(_NEXUS, table=table, owner="chart")
    expect_refusal(lambda: deposit_validate(packet, [1.0, 0.0, 0.0],
                                            berth_path=berth + ".gone", root=root),
                   "does not exist")
    assert trees.tree_state(_NEXUS, table=table, owner="chart") == before
    # The real deposit lands in the validate corpus with the berth as provenance.
    r = trees.deposit(content, [1.0, 0.0, 0.0],
                      {"source": berth, "hypothesize_ref": packet["hypothesize_ref"],
                       "confidence": packet["confidence"]},
                      tree=_NEXUS, table=table, owner="chart")
    rows = store.read(table, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == content
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["standing"] == "hypothesis"


def test_import_allowlist(root, triage_berth, hypothesize_berth):
    # Composed over orient's import_map: the allowlist matches the module that
    # ACTUALLY ENTERS, not the spelling.
    from cairn.orient.orient import import_map
    allow = ("__future__", "hashlib", "json", "os", "time",
             "cairn.build_inspector.inspector", "cairn.chart.hypothesize",
             "cairn.chart.orient", "cairn.chart.tree")
    seen = import_map(validate_mod.__file__)["measured"]["imports"]
    offenders = [m for m in seen
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"validate.py imports outside its allowlist: {offenders} — four "
        "composed doors only: the inspector's judge, hypothesize's chain "
        "reader, chart's settled orient machinery, and chart's tree verbs")


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
    root, triage_berth, hypothesize_berth = make_root()
    checks = [
        test_the_chain_is_physics_at_depth_7,
        test_floor_hands_the_acceptance_vocabulary_verbatim,
        test_schema_gate_refuses_hollow_shapes,
        test_the_door_composes_the_installed_judges,
        test_the_berth_lands_and_the_door_holds,
        test_deposit_back_is_gated,
        test_import_allowlist,
    ]
    try:
        for check in checks:
            check(root, triage_berth, hypothesize_berth)
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
        shutil.rmtree(os.path.dirname(root), ignore_errors=True)
    print("green — chart/validate: stage 7 fills only through an unbroken "
          "six-link chain (hypothesize's reader composed by identity), the "
          "floor hands the acceptance vocabulary verbatim, the schema gate "
          "refuses hollow shapes, the door composes the inspector's own judges "
          "(by identity), the berth round-trips, the deposit-back is gated, "
          "and the brick's doors are exactly the four composed ones — the "
          "stone plan's chain is WHOLE")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

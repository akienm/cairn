"""Proof: the constrain brick — the first stackable learning brick built UNDER
pre-installed judges (constrain-filters, PROVED before this module existed).

Teeth a hollow build could not pass:
  - THE TEMPLATE-FILL LINKAGE IS PHYSICS: stage 2 refuses without a berthed,
    readable stage-1 packet on disk (a missing intent_ref, a non-packet file).
  - THE FLOOR SURFACES CHARTERS VERBATIM: falsifier/gates/owner text travels
    unedited with its address; a ref that is not a component is reported apart;
    an unreadable charter is named, never skipped. What-exists only.
  - THE SCHEMA GATE REFUSES what a hollow build would emit: missing fields, empty
    constraints, a constraint without text/source/kind, bad confidence, uncovered
    provenance, an unfiled ticket claim.
  - THE DOOR COMPOSES THE INSTALLED JUDGES: a packet with an unresolvable source
    or an empty bounds.out is refused AT THE BERTH by the same judge_constrain the
    promotion gate runs — asserted by identity (it IS the inspector's function),
    not by parallel behavior.
  - THE BERTH LANDS AND ROUND-TRIPS; a refused packet leaves nothing behind.
  - THE DEPOSIT-BACK IS GATED: content is the ONE rendering (intent + bounds),
    the berth must exist on disk, refusals leave the tree standing.
  - IMPORT ALLOWLIST: constrain.py composes exactly three cairn doors — the
    inspector's judge, chart's settled orient machinery, chart's tree verbs. No
    parallel scan, no db, no network. And the direction holds: the inspector
    never imports constrain (the module cannot shape its judge).

DB teeth need the one-time provisioning (as the tree proof). Self-cleaning.

    python3 cairn/chart/proofs/test_chart_constrain.py     # exit 0 = green
"""
from __future__ import annotations

import ast
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
from cairn.chart import constrain as constrain_mod
from cairn.chart.constrain import (
    AUTHORED_FIELDS, ConstrainRefused, constrain_floor, constrain_node_content,
    deposit_constrain, validate_constrain, write_constrain,
)
from cairn.chart.tree import nexus_table
from cairn.db_domain import store
from cairn.librarian import trees

_NEXUS = f"constrain_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"


def make_root():
    """A synthetic world: two chartered components (alpha with falsifier/gates/owner,
    beta with a broken charter) plus a berthed orient packet to fill from."""
    root = tempfile.mkdtemp(prefix="chart_constrain_proof_")
    for comp in ("alpha", "beta"):
        os.makedirs(os.path.join(root, "cairn", comp))
        with open(os.path.join(root, "cairn", comp, comp + ".py"), "w") as fh:
            fh.write("x = 1\n")
    with open(os.path.join(root, "cairn", "alpha", "intention+why.json"), "w") as fh:
        json.dump({"component": "alpha",
                   "falsifier": "RED if alpha ever writes outside its own table",
                   "gates": "proof gate under the tester",
                   "owner": "CC owns code; Akien owns design"}, fh)
    with open(os.path.join(root, "cairn", "beta", "intention+why.json"), "w") as fh:
        fh.write("{broken json")
    berth_dir = os.path.join(root, "instance", "packets")
    os.makedirs(berth_dir)
    orient_berth = os.path.join(berth_dir, "orient-20260728T170000-feedfeedfeed.json")
    with open(orient_berth, "w") as fh:
        json.dump({"intent": "bound the alpha gate work",
                   "domain": "alpha", "scope": "IN: alpha. OUT: beta.",
                   "refs": ["alpha", "beta", "cairn/alpha/alpha.py"],
                   "unknowns": [], "confidence": 0.8,
                   "provenance": {"intent": "claude", "domain": "claude",
                                  "scope": "claude", "refs": "floor",
                                  "unknowns": "claude"}}, fh)
    return root, orient_berth


def good_packet(orient_berth):
    return {
        "intent_ref": orient_berth,
        "constraints": [
            {"text": "alpha may write only its own table",
             "source": "chart", "kind": "charter"},
        ],
        "bounds": {"in": ["alpha's gate"], "out": ["beta", "the network"]},
        "unknowns": ["whether beta consumes alpha's output"],
        "confidence": 0.75,
        "provenance": {"intent_ref": "floor", "constraints": "claude",
                       "bounds": "claude", "unknowns": "claude"},
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except ConstrainRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected ConstrainRefused mentioning %r, got none" % needle)


def test_template_fill_linkage_is_physics(root, orient_berth):
    expect_refusal(lambda: constrain_floor(os.path.join(root, "no-berth.json")),
                   "not a berthed packet")
    not_a_packet = os.path.join(root, "not_a_packet.json")
    with open(not_a_packet, "w") as fh:
        json.dump({"weird": True}, fh)
    expect_refusal(lambda: constrain_floor(not_a_packet), "not an orient berth")
    p = good_packet(orient_berth)
    p["intent_ref"] = os.path.join(root, "no-berth.json")
    expect_refusal(lambda: validate_constrain(p, root=root), "not a berthed packet")


def test_floor_surfaces_charters_verbatim(root, orient_berth):
    facts = constrain_floor(orient_berth, root=root)
    assert facts["stratum"] == "floor"
    assert facts["intent"] == "bound the alpha gate work"
    by_comp = {c["component"]: c for c in facts["charter_constraints"]}
    assert by_comp["alpha"]["falsifier"] == \
        "RED if alpha ever writes outside its own table", \
        "the falsifier travels VERBATIM — a paraphrase is laundered provenance"
    assert by_comp["alpha"]["owner"].startswith("CC owns code")
    assert by_comp["alpha"]["charter"].endswith("alpha/intention+why.json"), \
        "the text travels with its address"
    assert "unreadable" in by_comp["beta"], \
        "a broken charter is named, never silently skipped"
    assert facts["refs_not_components"] == ["cairn/alpha/alpha.py"], \
        "non-component refs are reported apart, not dropped"


def test_schema_gate_refuses_hollow_shapes(root, orient_berth):
    missing = good_packet(orient_berth)
    del missing["bounds"]
    expect_refusal(lambda: validate_constrain(missing, root=root), "bounds")
    empty = dict(good_packet(orient_berth), constraints=[])
    expect_refusal(lambda: validate_constrain(empty, root=root), "non-empty")
    unshaped = dict(good_packet(orient_berth),
                    constraints=[{"text": "a rule", "source": "chart"}])
    expect_refusal(lambda: validate_constrain(unshaped, root=root), "kind")
    over = dict(good_packet(orient_berth), confidence=2.0)
    expect_refusal(lambda: validate_constrain(over, root=root), "confidence")
    uncovered = good_packet(orient_berth)
    del uncovered["provenance"]["bounds"]
    expect_refusal(lambda: validate_constrain(uncovered, root=root), "bounds")
    minted_ticket = dict(good_packet(orient_berth), ticket="no-such-ticket")
    expect_refusal(lambda: validate_constrain(minted_ticket, root=root), "no-such-ticket")


def test_the_door_composes_the_installed_judges(root, orient_berth):
    # Identity first: the door's judge IS the inspector's — one implementation,
    # two mouths, nothing to drift between.
    assert constrain_mod.judge_constrain is inspector_mod.judge_constrain
    minted = dict(good_packet(orient_berth),
                  constraints=[{"text": "obey the minted rule",
                                "source": "no/such/charter.json", "kind": "charter"}])
    expect_refusal(lambda: validate_constrain(minted, root=root), "constraint_traces")
    unbounded = dict(good_packet(orient_berth),
                     bounds={"in": ["alpha's gate"], "out": []})
    expect_refusal(lambda: validate_constrain(unbounded, root=root),
                   "constraint_bounds_complete")
    # And the inspector never imports constrain — the module cannot shape its judge.
    inspector_src = Path(inspector_mod.__file__).read_text(encoding="utf-8")
    assert "cairn.chart.constrain" not in inspector_src, \
        "direction inversion: the judge's owner must never import the judged"


def test_the_berth_lands_and_the_door_holds(root, orient_berth):
    berth_dir = os.path.join(root, "instance", "constrain_berth")
    packet = good_packet(orient_berth)
    path = write_constrain(packet, instance_dir=berth_dir, root=root)
    assert os.path.basename(path).startswith("constrain-")
    with open(path) as fh:
        assert json.load(fh) == packet, "the berthed packet round-trips whole"
    refused = dict(packet, bounds={"in": ["x"], "out": []})
    try:
        write_constrain(refused, instance_dir=berth_dir, root=root)
        raise AssertionError("the door passed what the judges red")
    except ConstrainRefused:
        pass
    assert len(os.listdir(berth_dir)) == 1, \
        "a refused packet leaves nothing behind the door"
    return path


def test_deposit_back_is_gated(root, orient_berth):
    berth_dir = os.path.join(root, "instance", "deposit_berth")
    packet = good_packet(orient_berth)
    berth = write_constrain(packet, instance_dir=berth_dir, root=root)
    content = constrain_node_content(packet)
    assert content.startswith("bound the alpha gate work — IN: ") and "OUT: beta" in content, \
        "the node content is the ONE rendering: upstream intent + the bounds"
    # A berth that does not exist refuses, tree untouched.
    table = nexus_table(_NEXUS)
    before = trees.tree_state(_NEXUS, table=table, owner="chart")
    expect_refusal(lambda: deposit_constrain(packet, [1.0, 0.0, 0.0],
                                             berth_path=berth + ".gone", root=root),
                   "does not exist")
    assert trees.tree_state(_NEXUS, table=table, owner="chart") == before
    # The real deposit lands in the constrain corpus with the berth as provenance.
    r = trees.deposit(content, [1.0, 0.0, 0.0],
                      {"source": berth, "intent_ref": packet["intent_ref"],
                       "confidence": packet["confidence"]},
                      tree=_NEXUS, table=table, owner="chart")
    rows = store.read(table, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == content
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["standing"] == "hypothesis"


def test_import_allowlist(root, orient_berth):
    # Composed over orient's import_map (installed 2026-07-28, seeded by the red
    # this proof's build fired): the allowlist matches the module that ACTUALLY
    # ENTERS, not the spelling.
    from cairn.orient.orient import import_map
    allow = ("__future__", "hashlib", "json", "os", "time",
             "cairn.build_inspector.inspector", "cairn.chart.orient",
             "cairn.chart.tree")
    seen = import_map(constrain_mod.__file__)["measured"]["imports"]
    offenders = [m for m in seen
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"constrain.py imports outside its allowlist: {offenders} — three composed "
        "doors only: the inspector's judge, chart's settled orient machinery, "
        "chart's tree verbs")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            t = nexus_table(_NEXUS)
            cur.execute(f'DROP TABLE IF EXISTS "{t}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
    finally:
        conn.close()



def test_refusal_is_one_pass_complete(root, orient_berth):
    """Ticket chart-doors-refuse-in-one-pass: a multi-defective packet learns EVERY
    shape lack in ONE refusal, a second identical firing names the identical set
    (no whack-a-mole), and a broken chain read names its remediation."""
    bad = good_packet(orient_berth)
    del bad["bounds"]
    bad["confidence"] = 2.0
    bad["provenance"] = dict(bad["provenance"], intruder="martian")

    def lack_set():
        try:
            validate_constrain(bad, root=root)
        except ConstrainRefused as e:
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
        constrain_floor(os.path.join(root, "no-such-berth.json"))
        raise AssertionError("floor read a berth that does not exist")
    except ConstrainRefused as e:
        assert "REMEDIATION" in str(e), str(e)



def test_request_identity_is_physics(root, orient_berth):
    """Ticket berths-carry-request-identity: a packet claiming ticket A over a berth
    claiming ticket B is refused with the mismatch named in the one-pass refusal."""
    foreign_doc = json.load(open(orient_berth))
    foreign_doc["ticket"] = "tkt-b"
    foreign = os.path.join(root, "foreign-constrain-ref.json")
    with open(foreign, "w") as fh:
        json.dump(foreign_doc, fh)
    bad = good_packet(orient_berth)
    bad["ticket"] = "tkt-a"
    bad["intent_ref"] = foreign
    try:
        validate_constrain(bad, root=root)
        raise AssertionError("claim-A packet passed over a claim-B berth")
    except ConstrainRefused as e:
        msg = str(e)
        assert "request-identity mismatch" in msg and "tkt-b" in msg, msg


def _main() -> int:
    root, orient_berth = make_root()
    checks = [
        test_request_identity_is_physics,
        test_refusal_is_one_pass_complete,
        test_template_fill_linkage_is_physics,
        test_floor_surfaces_charters_verbatim,
        test_schema_gate_refuses_hollow_shapes,
        test_the_door_composes_the_installed_judges,
        test_the_berth_lands_and_the_door_holds,
        test_deposit_back_is_gated,
        test_import_allowlist,
    ]
    try:
        for check in checks:
            check(root, orient_berth)
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
        shutil.rmtree(root, ignore_errors=True)
    print("green — chart/constrain: stage 2 fills only from a berthed stage 1, the "
          "floor surfaces charter text verbatim with its address, the schema gate "
          "refuses hollow shapes, the door composes the inspector's own judges (by "
          "identity), the berth round-trips, the deposit-back is gated, and the "
          "brick's doors are exactly the three composed ones")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

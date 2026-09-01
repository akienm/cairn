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

    python3 cairn/devices/builder/machines/constrain/proofs/test_chart_constrain.py     # exit 0 = green
"""
from __future__ import annotations

import ast
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
from cairn.devices.builder.machines.constrain import constrain as constrain_mod
from cairn.devices.builder.machines.constrain.constrain import (
    AUTHORED_FIELDS, ConstrainRefused, constrain_floor, constrain_node_content,
    deposit_constrain, validate_constrain, write_constrain,
)
from cairn.tools.tree.tree import nexus_table
from cairn.devices.db_domain import store
from cairn.devices.librarian import trees
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

_NEXUS = f"constrain_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"


ALPHA_HOME = os.path.join("cairn", "tools", "alpha")
BETA_HOME = os.path.join("cairn", "tools", "beta")
NESTED_HOME = os.path.join("cairn", "devices", "holder", "machines", "nested")


def make_root():
    """A synthetic world at the house's REAL shape: components on their rungs, one of
    them NESTED under a holder, plus a berthed orient packet to fill from.

    THE FIXTURE WAS FLAT UNTIL 2026-08-14 — ``cairn/<name>/``, the shape the house
    stopped having on 2026-08-13 — and nothing redded, because the top-level branch of
    ``component_dirs`` still finds a directory that is not a rung. So the fixture kept
    passing while testing a world that no longer existed, and the path-ref defect this
    build closes could not have been caught here: with everything one level down, a path
    ref and its component were never more than one hop apart. ``holder/machines/nested``
    is here so the DEEPEST-OWNER rule has something to be wrong about.
    """
    root = str(scratch_dir("chart_constrain_proof_"))
    for home in (ALPHA_HOME, BETA_HOME, NESTED_HOME):
        os.makedirs(os.path.join(root, home))
        name = os.path.basename(home)
        with open(os.path.join(root, home, name + ".py"), "w") as fh:
            fh.write("x = 1\n")
    # The HOLDER is a component in its own right and an ancestor of ``nested`` — which is
    # the whole point of it: a path inside nested sits under both, and only one of them is
    # its address.
    with open(os.path.join(root, "cairn", "devices", "holder", "holder.py"), "w") as fh:
        fh.write("x = 1\n")
    with open(os.path.join(root, "cairn", "devices", "holder",
                           "intention+why.json"), "w") as fh:
        json.dump({"component": "holder",
                   "falsifier": "RED if the holder answers for its machines",
                   "gates": "proof gate under the tester",
                   "owner": "CC owns code; Akien owns design"}, fh)
    with open(os.path.join(root, ALPHA_HOME, "intention+why.json"), "w") as fh:
        json.dump({"component": "alpha",
                   "falsifier": "RED if alpha ever writes outside its own table",
                   "gates": "proof gate under the tester",
                   "owner": "CC owns code; Akien owns design"}, fh)
    with open(os.path.join(root, NESTED_HOME, "intention+why.json"), "w") as fh:
        json.dump({"component": "nested",
                   "falsifier": "RED if nested is attributed to its holder",
                   "gates": "proof gate under the tester",
                   "owner": "CC owns code; Akien owns design"}, fh)
    with open(os.path.join(root, BETA_HOME, "intention+why.json"), "w") as fh:
        fh.write("{broken json")
    berth_dir = os.path.join(root, "instance", "packets")
    os.makedirs(berth_dir)
    orient_berth = os.path.join(berth_dir, "orient-20260728T170000-feedfeedfeed.json")
    with open(orient_berth, "w") as fh:
        json.dump({"intent": "bound the alpha gate work",
                   "domain": "alpha", "scope": "IN: alpha. OUT: beta.",
                   # A NAME, a broken-charter name, a PATH into a component, a path into a
                   # NESTED component, and a path that resolves to nothing. Every shape an
                   # orient packet actually carries — measured over the 45 live berths,
                   # where 266 of 310 refs are paths.
                   "refs": ["alpha", "beta",
                            os.path.join(ALPHA_HOME, "alpha.py"),
                            os.path.join(NESTED_HOME, "nested.py"),
                            os.path.join("cairn", "nowhere", "gone.py")],
                   "unknowns": [], "confidence": 0.8,
                   "provenance": {"intent": "cc", "domain": "cc",
                                  "scope": "cc", "refs": "floor",
                                  "unknowns": "cc"}}, fh)
    return root, orient_berth


@pytest.fixture
def _world():
    return make_root()


@pytest.fixture
def root(_world):
    return _world[0]


@pytest.fixture
def orient_berth(_world):
    return _world[1]


def good_packet(orient_berth):
    return {
        "intent_ref": orient_berth,
        "constraints": [
            {"text": "alpha may write only its own table",
             # A LIVE component name: judge_constrain resolves a source against the
             # real roster (ref_exists, default root), so a fixture source has to be
             # something that exists. "chart" stood here until 2026-08-13, when the
             # decomposition made it a skill and not a component.
             "source": "base", "kind": "charter"},
        ],
        "bounds": {"in": ["alpha's gate"], "out": ["beta", "the network"]},
        "unknowns": ["whether beta consumes alpha's output"],
        "confidence": 0.75,
        "provenance": {"intent_ref": "floor", "constraints": "cc",
                       "bounds": "cc", "unknowns": "cc"},
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
    assert by_comp["alpha"]["charter"].endswith(
        os.path.join("alpha", "intention+why.json")), \
        "the text travels with its address"
    assert "unreadable" in by_comp["beta"], \
        "a broken charter is named, never silently skipped"


def test_a_path_ref_reaches_its_component(root, orient_berth):
    """THE 86% TOOTH. Until 2026-08-14 the floor tested each ref for membership in the
    component ROSTER — a set of bare NAMES — so a path-shaped ref matched nothing and was
    discarded. Measured across the 45 live orient berths: 266 of 310 refs are paths, so
    the floor threw away 86% of its own input and emitted an EMPTY constraint list, which
    is a legal list and redded nothing anywhere. A hollow build passes the verbatim tooth
    above and fails this one."""
    facts = constrain_floor(orient_berth, root=root)
    by_comp = {c["component"]: c for c in facts["charter_constraints"]}
    assert "alpha" in by_comp, "a path ref into a component must reach that component"
    assert "nested" in by_comp, \
        "a path ref into a NESTED component must reach it too — the rungs are read, " \
        "not assumed, at every depth"
    unreached = [m["ref"] for m in facts["refs_not_components"]]
    assert unreached == [os.path.join("cairn", "nowhere", "gone.py")], \
        "only the ref that resolves to nothing is reported apart; " \
        "reported apart: %r" % (unreached,)
    assert all(m["why"] for m in facts["refs_not_components"]), \
        "a ref the floor could not ground carries WHY — 'not a component' is four " \
        "different findings wearing one sentence"


def test_the_deepest_owner_wins_never_the_holder(root, orient_berth):
    """A path inside ``holder/machines/nested`` sits under BOTH components, and only one
    of them is its address. Answering with the holder would attribute a machine's code to
    the device that assembles it — and it is the answer a shallowest-match or
    first-match implementation gives, which is why this is its own tooth."""
    facts = constrain_floor(orient_berth, root=root)
    by_comp = {c["component"]: c for c in facts["charter_constraints"]}
    assert by_comp["nested"]["falsifier"] == \
        "RED if nested is attributed to its holder"
    assert "holder" not in by_comp, \
        "the holder is a component and an ancestor, and it is NOT the address of " \
        "the code inside its machine"


def test_the_floor_authors_constraints_and_unknowns(root, orient_berth):
    """The floor AUTHORS, it does not merely report. Three constraints per readable
    charter — falsifier, gates, owner — each carrying the address it was read from, and
    every failure to ground riding out as an unknown rather than vanishing."""
    fl = constrain_mod.floor_packet(orient_berth, root=root)
    assert fl["stratum"] == "floor"
    by_kind = {c["kind"] for c in fl["constraints"]}
    assert by_kind == {"charter"}, "the floor authors charter constraints and nothing else"
    texts = {c["text"] for c in fl["constraints"]}
    assert "RED if alpha ever writes outside its own table" in texts, \
        "the authored constraint carries the charter's text VERBATIM"
    assert all(c["source"].endswith("intention+why.json") for c in fl["constraints"]), \
        "the source is the charter PATH — resolvable by the same rule the berth gate " \
        "uses, not a string with a fragment packed into it"
    assert {c["field"] for c in fl["constraints"]} == {"falsifier", "gates", "owner"}, \
        "the field the text came from rides in its own key"
    assert len(fl["constraints"]) == 6, \
        "two readable charters x three bounding fields; got %d" % len(fl["constraints"])
    # ONE ENTRY PER COMPONENT, NOT PER REF: the fixture names alpha TWICE, once as a bare
    # name and once as a path into it, and a component ref'd twice must not have its
    # charter surfaced twice. This count is the only thing that catches it — the texts are
    # identical, so a duplicate reads as a longer list of correct constraints.
    assert len({(c["source"], c["field"]) for c in fl["constraints"]}) == 6, \
        "a component ref'd by BOTH name and path is one component, not two"
    unknowns = " ".join(fl["unknowns"])
    assert "gone.py" in unknowns, "a ref that grounds to nothing becomes an unknown"
    assert "beta" in unknowns, "an unreadable charter becomes an unknown, never a silence"


def test_an_empty_floor_is_None_and_not_an_empty_list(root, orient_berth):
    """``None`` and ``[]`` are different claims and the difference is load-bearing: an
    empty list says the floor looked and found this request unbounded, which is a sentence
    no Cairn request can truthfully carry. ``None`` says the floor could not tell, and
    provenance then says the ceiling authored the field."""
    bare = os.path.join(root, "instance", "packets", "orient-bare.json")
    with open(bare, "w") as fh:
        json.dump({"intent": "no refs at all", "refs": [], "unknowns": [],
                   "confidence": 0.5, "provenance": {}}, fh)
    fl = constrain_mod.floor_packet(bare, root=root)
    assert fl["constraints"] is None and fl["unknowns"] is None, \
        "an empty floor answers None, never an empty collection"


def test_schema_gate_refuses_hollow_shapes(root, orient_berth):
    missing = good_packet(orient_berth)
    del missing["bounds"]
    expect_refusal(lambda: validate_constrain(missing, root=root), "bounds")
    empty = dict(good_packet(orient_berth), constraints=[])
    expect_refusal(lambda: validate_constrain(empty, root=root), "non-empty")
    unshaped = dict(good_packet(orient_berth),
                    constraints=[{"text": "a rule", "source": "base"}])
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
    assert "cairn.devices.builder.machines.constrain.constrain" not in inspector_src, \
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
    unique = content + f" [{_NEXUS}]"
    r = trees.deposit(unique, [1.0, 0.0, 0.0],
                      {"source": berth, "intent_ref": packet["intent_ref"],
                       "confidence": packet["confidence"]},
                      tree=_NEXUS, table=table, owner="chart")
    rows = store.read(trees.NODES_TABLE, where="node_id = %s", params=(r["node_id"],))
    assert rows and rows[0]["content"] == unique
    assert rows[0]["provenance"]["source"] == berth
    assert rows[0]["standing"] == "hypothesis"


def test_import_allowlist(root, orient_berth):
    # Composed over orient's import_map (installed 2026-07-28, seeded by the red
    # this proof's build fired): the allowlist matches the module that ACTUALLY
    # ENTERS, not the spelling.
    from cairn.tools.orient.orient import import_map
    allow = ("__future__", "hashlib", "json", "os", "time",
             "cairn.machines.build_inspector.inspector", "cairn.tools.chain.grammar",
             "cairn.tools.tree.tree", "cairn.tools.base.address",
             # cairn.tools.gate joined 2026-08-13 (ruling every-machine-carries-
             # its-own-inspector-and-gate): this stage now holds its own gate, and
             # gate-ness is a DIRECT-import fact — which is how `cairn determinism`
             # and `cairnmap --gate` see it from outside without being told.
             "cairn.tools.gate.gate",
             # THE TESTER JOINED 2026-08-14, AND THIS TOOTH FIRED RED TO ADMIT IT —
             # recorded because a widened allowlist with no note is the drift this
             # tooth exists to catch. Akien's ruling on constrain's intention that
             # day: the floor "discovers the instruments that will refuse this
             # build ... runs them, and reports their state". Running an instrument
             # IS reaching the tester; no spelling of the ruled design avoids it, so
             # the tooth was wrong the moment the ruling landed rather than the code
             # being wrong. What is admitted is deliberately narrow and each entry
             # earns itself: `cli` for the proof-discovery convention (COMPOSED, so
             # constrain and the tester cannot disagree about what a proof is),
             # `device` to run one, `validation_store` for the source fingerprint
             # that keys the run cache. The floor READS these and gates nothing —
             # Law 6 is untouched, and `run_proof` persists nothing, measured in its
             # own source before this import was added.
             "cairn.devices.tester.cli",
             "cairn.devices.tester.device",
             "cairn.devices.tester.validation_store")
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
    """Tickets berths-carry-request-identity + the-claim-rides-every-link: a packet
    claiming ticket A over a berth claiming ticket B is refused (MISMATCH), and a
    CLAIMLESS packet over that same claimed berth is refused (VANISH — Akien's
    verdict on cbbadb13530f: no warns, refuse and send back) — both named in the
    one-pass refusal."""
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
    silent = good_packet(orient_berth)
    silent.pop("ticket", None)
    silent["intent_ref"] = foreign
    try:
        validate_constrain(silent, root=root)
        raise AssertionError("claimless packet passed over a claimed berth")
    except ConstrainRefused as e:
        msg = str(e)
        assert "request-identity vanished" in msg and "tkt-b" in msg, msg


def _floor_true_packet(root, orient_berth):
    """A packet a well-behaved ceiling would emit: the floor's constraints carried through
    UNCHANGED, plus one the floor cannot reach, plus the floor's unknowns."""
    fl = constrain_mod.floor_packet(orient_berth, root=root)
    p = good_packet(orient_berth)
    p["constraints"] = list(fl["constraints"]) + [
        {"text": "Law 9 — red is the default", "source": "base", "kind": "law"}]
    p["unknowns"] = list(fl["unknowns"])
    # The sender still declares the fields the floor does not author — ``intent_ref`` and
    # ``bounds``. Only the FLOOR_AUTHORED keys are the door's to write, and dropping the
    # rest would leave provenance uncovered, which is a different refusal entirely.
    p["provenance"] = {"intent_ref": "floor", "bounds": "cc"}
    return p, fl


def test_provenance_is_measured_not_declared(root, orient_berth):
    """A field earns ``floor`` only when re-running the floor over the packet's own
    ``intent_ref`` REPRODUCES it. The label the sender wrote is never taken.

    THE DEFECT, MEASURED over the 41 live constrain berths: 24 declared
    ``constraints: floor`` while the floor produced zero charter constraints for that same
    input in 24 cases. The number the staircase is steered by was computed by the party
    being measured — the same finding orient's floor build closed one stage up."""
    p, _ = _floor_true_packet(root, orient_berth)
    validate_constrain(p, root=root)
    assert p["provenance"]["constraints"] == "floor", \
        "a ceiling that carries the floor through unchanged EARNS floor"
    assert p["provenance"]["unknowns"] == "floor"


def test_the_floor_label_is_reachable_and_both_mutations_red(root, orient_berth):
    """THE AGREEMENT CHECK PROVES BOTH HALVES CAN RED — mutation testing (ticket
    an-agreement-check-proves-both-halves-can-red), applied here by hand because this is
    the first two-input check built since it was cast.

    REACHABILITY IS HALF THE TOOTH, and it is the half that was nearly lost. Set equality
    — orient's rule — would have made ``floor`` structurally unreachable here, because any
    law the ceiling correctly adds would demote the field. A label that can only ever read
    one value is not a measurement, it is a constant, and the dial that watches for a
    nexus compiling would have been blind to the thing it was built to see.

    MUTATION A (drop): the ceiling silently loses one of the floor's constraints.
    MUTATION B (forge): the ceiling invents a ``charter``-kind constraint of its own and
    rides the floor's label with it. Survival alone catches A and NOT B, so a harness that
    reported one boolean would call this check healthy while half of it was dead."""
    honest, fl = _floor_true_packet(root, orient_berth)
    assert constrain_mod.measured_provenance(honest, root=root)["constraints"] == "floor"

    dropped = dict(honest, constraints=honest["constraints"][1:])
    assert constrain_mod.measured_provenance(dropped, root=root)["constraints"] == "cc", \
        "MUTATION A undetected: a floor constraint went missing and the field kept 'floor'"

    forged = dict(honest, constraints=honest["constraints"] + [
        {"text": "invented", "source": "base", "kind": "charter"}])
    assert constrain_mod.measured_provenance(forged, root=root)["constraints"] == "cc", \
        "MUTATION B undetected: the ceiling forged a charter-kind constraint the floor " \
        "never produced and wore the floor's label for it"

    added = dict(honest, constraints=honest["constraints"] + [
        {"text": "a ticket bound", "source": "base", "kind": "ticket"}])
    assert constrain_mod.measured_provenance(added, root=root)["constraints"] == "floor", \
        "a constraint in a kind the floor cannot reach is the CEILING doing its own " \
        "job — demoting the field for it is what made the label unreachable"


def test_a_misdeclared_floor_label_is_refused_not_corrected(root, orient_berth):
    """A sender that labels its own floor-authored provenance and gets it WRONG is
    refused. A silent overwrite would leave the sender believing it still labels its own
    work, and the next stage would be written from that belief — the propagation vector
    that put one wrong sentence into eight charters.

    AGREEING IS NOT DECLARING: a label matching the measurement passes, because the berth
    and the deposit both run this door over the same object, and a refuse-on-presence rule
    would make the berth's own output illegal one line later."""
    p, _ = _floor_true_packet(root, orient_berth)
    lying = dict(p, constraints=p["constraints"][1:],
                 provenance={"intent_ref": "floor", "constraints": "floor",
                             "bounds": "cc", "unknowns": "cc"})
    try:
        validate_constrain(lying, root=root)
        raise AssertionError("a packet declaring an unreproducible 'floor' passed")
    except ConstrainRefused as e:
        assert "declares its own provenance" in str(e) and "constraints" in str(e), str(e)

    agreeing, _ = _floor_true_packet(root, orient_berth)
    validate_constrain(agreeing, root=root)
    again = json.loads(json.dumps(agreeing))
    validate_constrain(again, root=root), \
        "the door must accept the packet it just wrote — both exit doors run it"


def _plant(root, **files):
    """Write proof files into a REF'D component's ``proofs/`` and hand back a remover.

    Planted at ``alpha`` because the fixture's orient berth refs it — twice, by name and by
    path — so the planting exercises the same resolution the live chain uses. Every tooth
    below removes what it planted: the teeth above this line count the floor's constraints
    exactly, and a leftover proof file would red them from a distance with a message about
    charters."""
    home = os.path.join(root, ALPHA_HOME, "proofs")
    os.makedirs(home, exist_ok=True)
    for name, body in files.items():
        with open(os.path.join(home, name + ".py"), "w") as fh:
            fh.write(body)
    return lambda: shutil.rmtree(home, ignore_errors=True)


def test_the_check_set_is_discovered_never_enumerated(root, orient_berth):
    """AKIEN'S CLAUSE 3 AS PHYSICS — "to keep learning, not to become fixed". A proof file
    planted at a ref'd address appears in the floor's output with NO code change.

    This is the tooth a hand-written check list fails and nothing else does. The whole
    build could be green on every other tooth while the check-set was a constant someone
    typed, and every one of those teeth would still pass — they measure that what is
    reported is honest, not that what is reported was found.

    THE BEFORE-READING IS HALF THE TOOTH. Asserting only that the planted file appears
    would pass for a floor that reports every proof in the repo regardless of the refs;
    the empty before-set is what makes the appearance mean the planting caused it."""
    assert constrain_mod.discovered_instruments(orient_berth, root=root) == [], \
        "the fixture has no proofs yet — a non-empty before-set means discovery is " \
        "reaching outside the ref'd components and the after-reading proves nothing"
    remove = _plant(root, test_planted_green="raise SystemExit(0)\n")
    try:
        after = constrain_mod.discovered_instruments(orient_berth, root=root)
        assert after == [os.path.join(ALPHA_HOME, "proofs", "test_planted_green.py")], \
            "a proof planted at a ref'd address must appear with no code change; got %r" \
            % (after,)
        # AND THE TESTER AGREES, SET FOR SET — the corpus has one idea of what a proof is.
        # By identity, not by coincidence: ``discovered_instruments`` composes ``discover``,
        # so this asserts the composition is still in place rather than re-derived.
        from cairn.devices.tester.cli import discover
        theirs = {str(Path(p).relative_to(root))
                  for p in discover([os.path.join(root, ALPHA_HOME)])}
        assert set(after) == theirs, \
            "constrain and the tester disagree about which files are proofs: %r vs %r" \
            % (sorted(after), sorted(theirs))
    finally:
        remove()


def test_a_named_check_is_never_reported_unrun(root, orient_berth):
    """THE FIRST HOLLOW PASS THE TICKET NAMES: a floor that lists the checks by name and
    calls that a report. The direct instrument is a proof planted to FAIL — a namer wearing
    a verdict says green, because green is what a name defaults to.

    AND THE MISSING FILE IS THE SAME FAILURE FROM THE OTHER SIDE. It is reported
    ``unrunnable``, never green and never dropped: 'nothing to run' is a state to report,
    and letting it fall out of the list shrinks the denominator, which makes the remaining
    greens look total (leak-scan coin-toss-red, measured in this corpus)."""
    remove = _plant(root, test_planted_red="raise SystemExit(1)\n")
    try:
        checks, cost = constrain_mod.instrument_constraints(orient_berth, root=root)
        assert [c["verdict"] for c in checks] == ["red"], \
            "a planted FAILING proof was reported %r — a report that cannot say red was " \
            "never produced by a run" % ([c["verdict"] for c in checks],)
        assert cost["instruments"] == len(checks), \
            "the denominator must be the discovered count: %r reported of %r discovered" \
            % (len(checks), cost["instruments"])
        assert cost["seconds"] > 0, "a run that took no time did not happen"
    finally:
        remove()
    gone = constrain_mod._run_instrument(
        os.path.join(ALPHA_HOME, "proofs", "test_gone.py"), root=root)
    assert gone["verdict"] == "unrunnable" and "not there" in gone["how"], \
        "a discovered file that vanished before the run must be reported unrunnable with " \
        "the reason, not carried as a verdict nobody read: %r" % (gone,)


def test_one_red_check_does_not_blanket_the_report(root, orient_berth):
    """THE THIRD HOLLOW PASS: a per-check state replaced by a blanket verdict. Three
    instruments, three different outcomes, in one firing — the report discriminates or it
    is not a report.

    AND EVERY RED RIDES OUT AS AN UNKNOWN. A check already failing before this build starts
    is not a bound the build can be judged against, and the floor saying so is what keeps
    the state from being read as a bound that was met."""
    remove = _plant(root,
                    test_planted_green="raise SystemExit(0)\n",
                    test_planted_red="raise SystemExit(1)\n",
                    test_planted_broken="def (\n")
    try:
        fl = constrain_mod.floor_packet(orient_berth, root=root)
        by_verdict = {}
        for c in fl["constraints"]:
            if c["kind"] == "check":
                by_verdict.setdefault(c["verdict"], []).append(c["source"])
        assert sorted(by_verdict) == ["green", "red"], \
            "three instruments in three states collapsed to %r" % (sorted(by_verdict),)
        assert len(by_verdict["green"]) == 1 and len(by_verdict["red"]) == 2, \
            "the split is wrong: %r" % (by_verdict,)
        # The charter constraints are untouched by the run half — the floor gained a kind,
        # it did not lose one.
        assert len([c for c in fl["constraints"] if c["kind"] == "charter"]) == 6
        unknowns = " ".join(fl["unknowns"])
        for red in by_verdict["red"]:
            assert red in unknowns, \
                "the red instrument %s is reported and then not carried into unknowns — " \
                "a failing bound that reads as a satisfied one" % red
        assert fl["cost"]["instruments"] == 3, \
            "the cost report is this firing's own work: %r" % (fl["cost"],)
    finally:
        remove()


def test_a_check_source_must_name_the_instrument_not_merely_resolve(root, orient_berth):
    """A source that RESOLVES but does not IDENTIFY is laundered provenance in a new place.

    THIS TOOTH EXISTS BECAUSE THE ACCEPTANCE RUN FOUND THE HOLE, not because anyone
    predicted it would hold. The chain's hypothesis said the serious falsification here
    would be the judges PASSING a corrupted source; run against the live chain on
    2026-08-14 that is what they did — ``constraint_traces`` asks only that a source
    resolve, so a proof path swapped for the component DIRECTORY it sits in left every
    installed judge silent. The judge is shared by every constrain packet ever written and
    widening it is out of this ticket's bounds; the ``check`` kind is this build's own, so
    the rule about what earns it sits at this machine's door.

    THE HONEST PACKET MUST STILL PASS THIS ENTRY, and that half is not decoration: a rule
    that refused the floor's own output one line after it wrote it would be a door nothing
    can walk through, which is how a check goes red at the moment its condition is
    satisfied. It is read off the RECORD rather than the gate, because the fixture cannot
    reach the gate — ``constraint_traces`` resolves every source against the REAL cairn
    root (the same reason ``good_packet`` sources a live component name), so a fixture proof
    path is unresolvable there no matter how honest it is. Live, those same nine check
    sources pass that judge with no findings, measured at acceptance the same day."""
    remove = _plant(root, test_planted_green="raise SystemExit(0)\n")
    try:
        honest, fl = _floor_true_packet(root, orient_berth)
        assert any(c["kind"] == "check" for c in honest["constraints"]), \
            "the fixture must carry a check for this tooth to mean anything"
        entries = [e for e in constrain_mod.inspect_constrain(honest, root=root)
                   if e.get("identity") == "every_check_names_a_discovered_instrument"]
        assert len(entries) == 1 and constrain_mod.gate.passed(entries[0]), \
            "the floor's own checks must pass the rule the floor's own door applies: %r" \
            % (entries,)

        laundered = json.loads(json.dumps(honest))
        for c in laundered["constraints"]:
            if c["kind"] == "check":
                # A REAL path that a resolver is happy with — the component directory the
                # proof sits in. Not an invented one: an invented source is already caught
                # by constraint_traces, and catching it again would prove nothing.
                c["source"] = ALPHA_HOME
                break
        expect_refusal(lambda: validate_constrain(laundered, root=root),
                       "not one of the instruments discovered for this request")
    finally:
        remove()


def test_floor_kinds_names_every_kind_the_floor_emits(root, orient_berth):
    """THE DECLARATION CANNOT DRIFT FROM THE CODE BENEATH IT — promised verbatim in the
    ``FLOOR_KINDS`` comment, and this is the promise kept.

    ``FLOOR_KINDS`` is a DECLARATION and deliberately not a derivation: deriving it from a
    firing would shrink the set exactly when a run reached no instruments, which is when
    the answer matters most. The price of declaring is that it can go stale, and this tooth
    is the price paid. EQUALITY, not containment, in both directions: an emitted kind
    missing from the tuple silently moves the line ``crowding_out`` is drawn on, and a
    declared kind the floor never emits inflates the same line with a fiction."""
    remove = _plant(root, test_planted_green="raise SystemExit(0)\n")
    try:
        fl = constrain_mod.floor_packet(orient_berth, root=root)
        emitted = {c["kind"] for c in fl["constraints"]}
        assert emitted == set(constrain_mod.FLOOR_KINDS), \
            "FLOOR_KINDS declares %r and the floor emits %r — the probe that asks the " \
            "floor for its kinds is reading a stale answer" \
            % (sorted(constrain_mod.FLOOR_KINDS), sorted(emitted))
    finally:
        remove()


def _main() -> int:
    root, orient_berth = make_root()
    checks = [
        test_request_identity_is_physics,
        test_refusal_is_one_pass_complete,
        test_template_fill_linkage_is_physics,
        test_floor_surfaces_charters_verbatim,
        test_a_path_ref_reaches_its_component,
        test_the_deepest_owner_wins_never_the_holder,
        test_the_floor_authors_constraints_and_unknowns,
        test_an_empty_floor_is_None_and_not_an_empty_list,
        test_the_check_set_is_discovered_never_enumerated,
        test_a_named_check_is_never_reported_unrun,
        test_one_red_check_does_not_blanket_the_report,
        test_a_check_source_must_name_the_instrument_not_merely_resolve,
        test_floor_kinds_names_every_kind_the_floor_emits,
        test_provenance_is_measured_not_declared,
        test_the_floor_label_is_reachable_and_both_mutations_red,
        test_a_misdeclared_floor_label_is_refused_not_corrected,
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
    # The summary names WHAT WAS PROVED and is rewritten whenever the teeth change. It is
    # the last line of the sealed record's stdout, so a reader of a validation trail meets
    # this sentence and nothing else — a stale one describes a build that no longer exists
    # while every tooth beneath it passes. This one went stale once already: it survived
    # the seven teeth added on 2026-08-14 unchanged.
    print(f"green — chart/constrain, {len(checks)} teeth: stage 2 fills only from a "
          "berthed stage 1; a ref reaches its component BY NAME OR BY PATH and the "
          "DEEPEST owner wins, never the holder; the floor AUTHORS constraints (charter "
          "falsifier/gates/owner, verbatim, with their address) and unknowns (with the "
          "why), and returns None rather than an empty list when it has nothing; "
          "the floor DISCOVERS the instruments that judge the ref'd components (composing "
          "the tester's own collector, agreeing with it set for set) and RUNS them — a "
          "proof planted at a ref'd address appears with no code change, a failing one is "
          "reported red and rides out as an unknown, a vanished one is reported unrunnable "
          "rather than dropped, three instruments in three states never collapse to one "
          "verdict, a check whose source RESOLVES but does not name a discovered "
          "instrument is refused, and every kind the floor emits is named in FLOOR_KINDS; "
          "provenance for those two is MEASURED by re-running the floor, the 'floor' "
          "label is reachable and BOTH mutations (drop one, forge one) red it, and a "
          "misdeclared label is refused rather than quietly corrected; the schema gate "
          "refuses hollow shapes, the door composes the inspector's own judges (by "
          "identity), the berth round-trips, the deposit-back is gated, and the brick's "
          "doors are exactly the three composed ones")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

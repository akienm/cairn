"""Proof: the orient nexus v0 — the floor reports only what EXISTS, the schema gate
refuses what a hollow build would emit, provenance travels per-field, and the packet
berths gated in instance-space.

Hermetic where it mutates (a fabricated temp root — no live snapshot values are
pinned); the two live-root teeth assert MEMBERSHIP invariants only. Exit 0 = green.
"""
import ast
import json
import os
import pytest
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")))

from cairn.tools.chain.grammar import (component_roster, ref_exists)
from cairn.devices.codemother.machines.orient.orient import (AUTHORED_FIELDS, FLOOR_AUTHORED, OrientRefused, deposit_orient, floor_facts, floor_packet, validate_orient, write_packet)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

PROVES = {
    # 2026-09-10, ticket 4c022c44de53 — the deposit door reads the provenance the write
    # door derived. Lettered clauses because that ticket's falsifier enumerates (a)..(e).
    # Clauses (a), (b) and (d) are also declared at the constrain end of the same seam;
    # a clause covered in two proofs is two teeth for it, not a conflict.
    "4c022c44de53": {
        "a": "test_measuring_is_the_default_so_an_unlabelled_caller_is_the_strict_one",
        "b": "test_the_write_door_measures_the_label_and_the_deposit_door_reads_it",
        "c": "test_a_berth_whose_floor_moved_underneath_it_still_deposits",
        "d": "test_reading_the_stored_label_is_not_skipping_the_gate",
        "e": "test_the_leave_those_keys_out_sentence_reaches_only_the_sender_who_wrote_them",
    },
}

ORIENT_PY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orient.py"))
# The rule this tooth holds is "stdlib plus the doors a LEG needs, and no leg reaches
# another leg". Its history is a narrowing, not a widening: through 2026-08-12 stage 1
# carried the chain's shared grammar, so it also carried cairn.tools.base.address (the
# one owner of the instance address, admitted to end ten hand-spellings of
# ~/.cairn/devices/chart/0/packets) and cairn.tools.orient.orient (the settled measurer).
# On 2026-08-13 the grammar moved to cairn/tools/chain/ and took both of those with it —
# stage 1 now speaks the grammar and reaches the instrument only THROUGH it. So the
# allowlist below is strictly smaller than the one it replaces, which is the measurable
# claim the extraction makes about itself: the seven sibling stages stopped importing
# stage 1, and stage 1 stopped being a door into the house.
ALLOWED_IMPORTS = {"__future__", "hashlib", "json", "os", "re", "time",
                   # Stage 1 is now a leg like any other: it speaks the chain grammar
                   # (which composes the orient INSTRUMENT and the address tool on its
                   # behalf) and it holds its own deposit door, which is what brings the
                   # tree verbs in — every sibling stage already admits exactly these two.
                   "cairn.tools.chain.grammar", "cairn.tools.tree.tree",
                   # cairn.tools.gate joined 2026-08-13 (ruling every-machine-carries-
                   # its-own-inspector-and-gate): stage 1 now holds its own gate, and
                   # gate-ness is a DIRECT-import fact — which is how `cairn determinism`
                   # and `cairnmap --gate` see it from outside without being told.
                   "cairn.tools.gate.gate"}


def make_root():
    root = str(scratch_dir("chart_orient_proof_"))
    # gamma carries code but NO charter — the census sees it, the roster must not.
    #
    # THE FIXTURE SITS ON REAL RUNGS since 2026-08-14, and it did not before: it built
    # ``cairn/<name>/``, a shape the repo stopped having on 2026-08-13 when the
    # complexity axis became an address (tools -> machines -> devices). Nothing was red,
    # because nothing yet read the rung — and then ``domain`` started being DERIVED from
    # where a ref sits, and a fixture off the axis produced no domain at all. A fixture
    # that models a layout the house no longer has is a green that stops meaning anything.
    for rung, comp in (("tools", "alpha"), ("devices", "beta"), ("tools", "gamma")):
        home = os.path.join(root, "cairn", rung, comp)
        os.makedirs(home)
        with open(os.path.join(home, comp + ".py"), "w") as fh:
            fh.write("x = 1\n")
        if comp != "gamma":
            with open(os.path.join(home, "intention+why.json"), "w") as fh:
                fh.write("{}\n")
    # A SKILL IS A DIRECTORY WITH A SKILL.md, not just a directory (skill_roster,
    # 2026-08-13) — the fixture has to build the artifact the floor looks for.
    os.makedirs(os.path.join(root, "skills", "chart"))
    with open(os.path.join(root, "skills", "chart", "SKILL.md"), "w") as fh:
        fh.write("# /chart\n")
    return root


@pytest.fixture
def root():
    return make_root()


def good_packet():
    """A ceiling-authored packet: it writes all five fields and declares provenance for
    the two the door does not measure.

    IT USED TO DECLARE ``floor`` FOR domain AND refs and that is precisely what stopped
    being legal on 2026-08-14 (ticket orient-floor-authors-and-provenance-is-measured) —
    the fixture was itself an instance of the defect, a sender labelling its own work,
    and the door now refuses the label rather than believing it. Nothing here is
    floor-authored (the refs are hand-picked and do not reproduce), so the door writes
    ``claude`` for all three, which is the honest reading of exactly this packet."""
    return {
        "request": "close alpha's gate against hollow input",
        "intent": "close alpha's gate against hollow input",
        "domain": "alpha",
        "scope": "the gate only, not beta's consumption of it",
        "refs": ["alpha", "cairn/tools/alpha/intention+why.json"],
        "unknowns": ["whether beta consumes the gated output"],
        "confidence": 0.8,
        "provenance": {"intent": "cc", "scope": "cc"},
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except OrientRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected OrientRefused mentioning %r, got none" % needle)


def test_empty_request_refuses(root):
    expect_refusal(lambda: floor_facts("   ", root=root), "empty")


def test_floor_reports_only_what_exists(root):
    facts = floor_facts(
        "fix alpha using cairn/tools/alpha/intention+why.json and bogus/nowhere.py", root=root)
    assert facts["stratum"] == "floor"
    assert facts["components_mentioned"] == ["alpha"]
    assert "cairn/tools/alpha/intention+why.json" in facts["paths_found"]
    assert "bogus/nowhere.py" in facts["paths_missing"]
    assert not set(facts["paths_found"]) & set(facts["paths_missing"]), \
        "found and missing must stay separate, never merged"


def test_floor_slash_verb_is_a_skill_not_a_path(root):
    facts = floor_facts("run /chart on beta", root=root)
    assert facts["skills_mentioned"] == ["chart"]
    assert "/chart" not in facts["paths_missing"], \
        "a known slash-verb is a skill mention, not a missing-path claim"
    assert facts["components_mentioned"] == ["beta"]


def test_schema_gate_refuses_missing_fields(root):
    packet = good_packet()
    del packet["scope"]
    expect_refusal(lambda: validate_orient(packet, root=root), "scope")


def test_schema_gate_refuses_bad_confidence(root):
    over = dict(good_packet(), confidence=1.5)
    expect_refusal(lambda: validate_orient(over, root=root), "confidence")
    boolean = dict(good_packet(), confidence=True)
    expect_refusal(lambda: validate_orient(boolean, root=root), "confidence")


def test_invented_ref_refuses(root):
    packet = good_packet()
    packet["refs"] = list(packet["refs"]) + ["minted/place.py"]
    expect_refusal(lambda: validate_orient(packet, root=root), "minted/place.py")


def test_provenance_must_cover_authored_fields(root):
    """Coverage is still the sender's obligation for the fields the door does NOT
    measure. It names ``intent`` rather than ``refs`` since 2026-08-14: the three
    floor-authored fields can no longer be uncovered, because the door fills them in
    whether the sender likes it or not — removing that key is not a defect any more, it
    is the required shape."""
    uncovered = good_packet()
    del uncovered["provenance"]["intent"]
    expect_refusal(lambda: validate_orient(uncovered, root=root), "intent")
    vibes = good_packet()
    vibes["provenance"]["scope"] = "vibes"
    expect_refusal(lambda: validate_orient(vibes, root=root), "vibes")


def test_a_declared_floor_provenance_is_refused_not_believed(root):
    """THE TOOTH THE TICKET NAMES, and the one a hollow build fails by doing what the
    door did until 2026-08-14: accepting the sender's dict. The packet below hand-writes
    ``domain`` and then labels it ``floor``, which is the exact shape of the defect that
    made the dial read orient at 0.40 — 45 berthed packets, 18 of them declaring
    ``domain: floor``, 14 floor-labelled values over 200 characters of prose, and not one
    of them reproducible. Refused, not corrected: a silent overwrite would leave the
    sender believing it still labels its own work."""
    liar = good_packet()
    liar["domain"] = "broadly speaking, the alpha area of the system"
    liar["provenance"]["domain"] = "floor"
    expect_refusal(lambda: validate_orient(liar, root=root), "declared 'floor'")

    # ...and the same packet WITHOUT the label sails, carrying the measured one.
    honest = good_packet()
    honest["domain"] = liar["domain"]
    validate_orient(honest, root=root)
    assert honest["provenance"]["domain"] == "cc", honest["provenance"]
    assert honest["provenance"]["refs"] == "cc", honest["provenance"]


def test_floor_authored_fields_earn_floor_by_reproducing(root):
    """The other end of the same claim: a field earns ``floor`` only when re-running the
    floor from the packet's own ``request`` produces it again. So the ceiling's way to
    get a ``floor`` label is to carry the floor's answer through unchanged — there is no
    other way, and that is the incentive the whole build is made of."""
    request = "close alpha's gate, see cairn/devices/beta/beta.py and run /chart"
    fp = floor_packet(request, root=root)
    assert fp["refs"] and fp["domain"], fp

    packet = dict(good_packet(), request=request, refs=fp["refs"],
                  domain=fp["domain"], unknowns=fp["unknowns"] or ["nothing ungrounded"])
    validate_orient(packet, root=root)
    assert packet["provenance"]["refs"] == "floor", packet["provenance"]
    assert packet["provenance"]["domain"] == "floor", packet["provenance"]

    # A REORDER IS NOT AN EDIT. refs is a collection, and calling a shuffle "the ceiling
    # added something" would understate the floor by the cost of a cosmetic difference.
    shuffled = dict(packet, refs=list(reversed(packet["refs"])),
                    provenance={"intent": "cc", "scope": "cc"})
    validate_orient(shuffled, root=root)
    assert shuffled["provenance"]["refs"] == "floor", shuffled["provenance"]

    # One added ref and it is the ceiling's field again — the whole value, not a fraction.
    widened = dict(packet, refs=list(packet["refs"]) + ["alpha"],
                   provenance={"intent": "cc", "scope": "cc"})
    validate_orient(widened, root=root)
    assert widened["provenance"]["refs"] == "cc", widened["provenance"]


def test_a_packet_without_a_request_cannot_earn_floor(root):
    """No evidence, no claim. The request is what the door re-runs, so a packet that
    does not carry one has nothing to reproduce and every floor-authored field reads
    ``claude``. Deliberately an incentive and not a required field: 45 packets berthed
    before this rule and none of them becomes retroactively malformed (Law 7)."""
    request = "close alpha's gate, see cairn/devices/beta/beta.py"
    fp = floor_packet(request, root=root)
    blind = dict(good_packet(), refs=fp["refs"], domain=fp["domain"],
                 unknowns=fp["unknowns"] or ["nothing ungrounded"])
    del blind["request"]
    validate_orient(blind, root=root)
    assert set(blind["provenance"][f] for f in FLOOR_AUTHORED) == {"cc"}, \
        blind["provenance"]


def test_the_floor_never_invents_a_ref(root):
    """THE SECOND TOOTH THE TICKET NAMES, and the worst failure available to this build:
    a ref the floor made up carries a MEASUREMENT's provenance, which is a fabrication
    wearing the one label nobody downstream is supposed to have to check. A path that is
    not there lands in unknowns; a name two rungs answer to lands in unknowns; neither
    ever lands in refs."""
    fp = floor_packet("read cairn/tools/alpha/nope.py and /nosuchskill, then fix beta",
                      root=root)
    assert "cairn/tools/alpha/nope.py" not in (fp["refs"] or [])
    assert any("cairn/tools/alpha/nope.py" in u for u in fp["unknowns"]), fp["unknowns"]
    assert any("/nosuchskill" in u for u in fp["unknowns"]), fp["unknowns"]
    assert "cairn/devices/beta" in fp["refs"], fp["refs"]
    for ref in fp["refs"]:
        assert ref_exists(ref, root), "the floor authored a ref that does not exist: %s" % ref

    # A slash-verb that is not installed is ONE unknown, not two. It used to fall through
    # the verb filter into the path scan and be reported as a missing path as well —
    # two unknowns about one fact, which is a floor overstating what it failed to ground.
    assert sum("nosuchskill" in u for u in fp["unknowns"]) == 1, fp["unknowns"]


def test_an_ambiguous_name_becomes_an_unknown_never_a_guess(root):
    """The homonym, on the live tree because that is where it exists: ``orient`` is a
    tool AND this machine. The floor says it found the name twice and cannot tell, which
    is a measurement; picking one would be a fabrication. An invariant about MEMBERSHIP
    and the shape of the answer, never a snapshot of how many homes exist today."""
    fp = floor_packet("build out orient's floor")
    hits = [u for u in (fp["unknowns"] or []) if "'orient'" in u]
    assert len(hits) == 1, fp["unknowns"]
    assert "cairn/tools/orient" in hits[0] and "machines/orient" in hits[0], hits[0]
    assert not any(r.endswith("/orient") for r in (fp["refs"] or [])), fp["refs"]


def test_good_packet_validates_and_berths(root):
    berth = os.path.join(root, "instance", "packets")
    packet = good_packet()
    assert validate_orient(packet, root=root) is packet
    path = write_packet(packet, instance_dir=berth, root=root)
    assert os.path.basename(path).startswith("orient-")
    with open(path) as fh:
        assert json.load(fh) == packet, "the berthed packet must round-trip whole"


def test_write_door_is_gated(root):
    berth = os.path.join(root, "instance", "gated")
    hollow = dict(good_packet(), intent="   ")
    expect_refusal(lambda: write_packet(hollow, instance_dir=berth, root=root), "intent")
    assert not os.path.isdir(berth) or not os.listdir(berth), \
        "a refused packet must leave nothing behind the door"


def test_live_roster_carries_charter_bearing_components(root):
    """A MEMBERSHIP invariant over the live tree, never a snapshot count. It named
    "chart" until 2026-08-13, when the decomposition made chart a SKILL and the tooth
    went red for the right reason — a roster of components correctly stopped carrying
    something that is not one. Now it names this machine and the librarian: one either
    side of the reorganisation, both charter-bearing, neither about to stop being a
    component. And the roster is a SET — ``orient`` has two homes (the tool and this
    machine) and must still appear once, or roster_size is arithmetic about nothing."""
    live = component_roster()
    assert "orient" in live and "librarian" in live, \
        "membership invariant: components with charters ride the roster"
    assert live.count("orient") == 1, \
        "two rungs answer to 'orient'; the roster is membership, not multiplicity"
    assert len(live) == len(set(live)), "the roster carries a duplicate"
    assert set(AUTHORED_FIELDS) == {"intent", "domain", "scope", "refs", "unknowns"}


def test_floor_composes_the_orient_instrument(root):
    """The roster comes from the orient instrument's census, filtered to
    charter-on-disk — never a parallel territory scan. gamma has code but no
    charter: the census sees it, the roster must not (a component without an
    intention doesn't run). Provenance of this tooth: the nexus's first live
    fire, 2026-07-28 — the floor's own parallel roster caught its builder
    having never surveyed cairn/tools/orient."""
    assert component_roster(root) == ["alpha", "beta"]


def test_ticket_claim_is_gated(root):
    """A packet may claim its ticket only if the ticket is ON FILE in
    CairnCommons/tickets/ (packet-inspector-wire, 2026-07-28) — a packet claiming
    an unfiled ticket is fabricated attribution (the 2026-07-26 class). The
    synthetic root has no commons beside it, so any claim there refuses; the
    live-root pass is a membership invariant against a committed ticket."""
    minted = dict(good_packet(), ticket="no-such-ticket")
    expect_refusal(lambda: validate_orient(minted, root=root), "no-such-ticket")
    hollow = dict(good_packet(), ticket="")
    expect_refusal(lambda: validate_orient(hollow, root=root), "ticket")
    live = dict(good_packet(), refs=["orient"], ticket="moreabout")
    assert validate_orient(live) is live, \
        "a claim naming a filed ticket passes (moreabout.json is committed)"
    assert ref_exists("orient") and not ref_exists("minted/nowhere.py"), \
        "the public ref semantics are the gate's own (one implementation, two mouths)"


def test_import_allowlist(root):
    """Stdlib plus the two doors a leg is allowed: the chain grammar and its own
    deposit's tree verbs. Any other cairn import is a third door or a re-derivation —
    and an import of a SIBLING STAGE would be the coupling the 2026-08-13 extraction
    removed, growing back. Composed over the orient instrument's import_map (installed
    2026-07-28): the allowlist matches the module that ACTUALLY ENTERS, not the
    spelling."""
    from cairn.tools.orient.orient import import_map
    seen = import_map(ORIENT_PY)["measured"]["imports"]
    stray = [m for m in seen
             if not any(m == p or m.startswith(p + ".") for p in ALLOWED_IMPORTS)]
    assert not stray, "orient.py imports outside its allowlist: %s" % sorted(stray)



def test_refusal_is_one_pass_complete(root):
    """Ticket chart-doors-refuse-in-one-pass: a multi-defective packet learns EVERY
    shape lack in ONE refusal, a second identical firing names the identical set
    (no whack-a-mole), and a broken chain read names its remediation."""
    bad = good_packet()
    del bad["domain"]
    bad["confidence"] = 2.0
    bad["provenance"] = dict(bad["provenance"], intruder="martian")

    def lack_set():
        try:
            validate_orient(bad, root=root)
        except OrientRefused as e:
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



def a_packet_whose_stored_label_the_floor_will_not_reproduce():
    """ONE object, and the whole pair turns on it being one.

    It declares ``floor`` for ``refs``. The refs are hand-picked, so re-running the floor
    over its own request produces something else and the write door refuses the label —
    which is exactly right for a packet arriving from outside. The same object is what a
    berth holds AFTER the write door has stamped it and the world has since moved: a
    label this door derived, that this door can no longer reproduce. Nothing about the
    packet distinguishes those two cases, which is why the door cannot tell them apart by
    inspection and needs the caller to say which door it is."""
    packet = good_packet()
    packet["provenance"] = {"intent": "cc", "scope": "cc", "domain": "cc",
                            "refs": "floor", "unknowns": "cc"}
    return packet


def test_the_write_door_measures_the_label_and_the_deposit_door_reads_it(root):
    """THE DEFECT, AS A PAIR ON ONE OBJECT (ticket 4c022c44de53).

    Before this build both doors re-measured, so a packet the write door had labelled and
    stamped was refused at the deposit door the moment the floor's answer moved
    underneath it — measured at 286 of 356 berthed orient packets and 293 of 348
    constrain ones. The pair below is what stops that: the same object, refused where the
    label is a claim and accepted where it is a record."""
    packet = a_packet_whose_stored_label_the_floor_will_not_reproduce()
    expect_refusal(lambda: validate_orient(dict(packet), root=root),
                   "declares its own provenance")
    assert validate_orient(dict(packet), root=root, measure_provenance=False) is not None


def test_the_deposit_door_itself_reads_rather_than_measures(root):
    """THE WIRING, BEHAVIOURALLY — not by reading the call site.

    ``deposit_orient`` is fired on the packet the write door would refuse, with a berth
    path that does not exist. It must fall through the provenance question entirely and
    refuse for the BERTH, because reaching that refusal is only possible if the packet
    already passed the gate in read mode. A deposit door that still measured would refuse
    one line earlier and never mention the berth at all."""
    packet = a_packet_whose_stored_label_the_floor_will_not_reproduce()
    expect_refusal(
        lambda: deposit_orient(packet, [0.0], berth_path="/nonexistent/berth.json",
                               root=root),
        "does not exist on disk")


def test_reading_the_stored_label_is_not_skipping_the_gate(root):
    """THE GUARD — the switch chooses the label's SOURCE, never whether the gate runs.

    This is the tooth that says what the ticket's falsifier calls the wrong intent: a
    read-mode door that waved malformed provenance through would have turned a
    measurement question into a hole. Each packet below is refused in READ mode, where
    there is no measurement to catch it and only the gate stands."""
    missing = a_packet_whose_stored_label_the_floor_will_not_reproduce()
    missing["provenance"] = {k: v for k, v in missing["provenance"].items()
                             if k != "unknowns"}
    expect_refusal(lambda: validate_orient(missing, root=root,
                                           measure_provenance=False),
                   "provenance")

    martian = a_packet_whose_stored_label_the_floor_will_not_reproduce()
    martian["provenance"]["unknowns"] = "martian"
    expect_refusal(lambda: validate_orient(martian, root=root,
                                           measure_provenance=False),
                   "stratum")

    invented = a_packet_whose_stored_label_the_floor_will_not_reproduce()
    invented["refs"] = ["cairn/tools/nowhere/nowhere.py"]
    expect_refusal(lambda: validate_orient(invented, root=root,
                                           measure_provenance=False),
                   "refs")

    nonsense = a_packet_whose_stored_label_the_floor_will_not_reproduce()
    nonsense["confidence"] = "very"
    expect_refusal(lambda: validate_orient(nonsense, root=root,
                                           measure_provenance=False),
                   "confidence")


def test_measuring_is_the_default_so_an_unlabelled_caller_is_the_strict_one(root):
    """THE DEFAULT IS THE STRICT SIDE. Every caller that does not name the switch gets the
    behaviour that existed before this build, so the change is opt-in at exactly two
    production call sites and nowhere else."""
    packet = a_packet_whose_stored_label_the_floor_will_not_reproduce()
    expect_refusal(lambda: validate_orient(dict(packet), root=root),
                   "declares its own provenance")



def test_the_deposit_takes_the_berths_label_and_refuses_a_forged_one(root):
    """CLAUSE (8) OF THE CHARTER, HELD BY A DIFFERENT MECHANISM.

    While both doors measured, "no packet reaches the tree carrying a label its sender
    wrote" held by re-derivation. The read door cannot hold it that way, so it holds it by
    ANCHOR: the deposit accepts exactly the provenance the write door stamped into the
    berth it is pointing at. A real berth path beside a forged label is the route this
    closes, and it is a route the pre-build code did not have to close."""
    # The berth dir hangs off ``root`` rather than pytest's tmp_path: this module is also
    # run by its own ``main()`` — which is how the TESTER runs it — and main() hands each
    # tooth exactly one argument. A tooth that only works under pytest is a tooth the seal
    # cannot reach.
    packet = good_packet()
    berth = write_packet(packet, instance_dir=os.path.join(root, "berths"), root=root)

    forged = json.load(open(berth, encoding="utf-8"))
    forged["provenance"] = dict(forged["provenance"], refs="floor")
    expect_refusal(lambda: deposit_orient(forged, [0.0], berth_path=berth, root=root),
                   "not the one the berth carries")

    honest = json.load(open(berth, encoding="utf-8"))
    try:
        deposit_orient(honest, [0.0], berth_path=berth, root=root)
    except OrientRefused as err:
        raise AssertionError("the berth's own packet was refused at its own deposit: %s"
                             % err)
    except Exception:
        # Past the gate and into the tree write, which is what this tooth is asserting;
        # the store is not part of the claim.
        pass



def test_a_berth_whose_floor_moved_underneath_it_still_deposits(root):
    """CLAUSE (c), AS AN INVARIANT RATHER THAN AS THE ONE BERTH THAT RAISED IT.

    The trouble named orient-20260909T215820-6525fe88f4a3.json: a berth written honestly
    on 2026-09-09 and refused at the deposit door on 2026-09-10, because a file moved in
    between. Pinning that berth would pin a snapshot of instance-space, so this tooth
    MAKES THE WORLD MOVE instead. The packet earns ``floor`` for refs and unknowns from
    the live floor, the write door stamps that label into the berth, and then the fixture
    creates the file the floor had reported ungrounded. Nothing about the packet changed;
    only the corpus did. The write door must now refuse the very label it wrote — that is
    the correct answer to "is this sender honest?" asked of a berth — and the deposit door
    must take it, which is the correct answer to "is this the label this door derived?".
    """
    request = "close alpha's gate and read cairn/tools/alpha/later.py"
    fp = floor_packet(request, root=root)
    assert fp["refs"] and fp["unknowns"], fp
    packet = dict(good_packet(), request=request, refs=fp["refs"],
                  domain=fp["domain"], unknowns=fp["unknowns"])
    berth = write_packet(packet, instance_dir=os.path.join(root, "berths"), root=root)
    stored = json.load(open(berth, encoding="utf-8"))
    assert stored["provenance"]["refs"] == "floor", stored["provenance"]
    assert stored["provenance"]["unknowns"] == "floor", stored["provenance"]

    with open(os.path.join(root, "cairn", "tools", "alpha", "later.py"), "w") as fh:
        fh.write("x = 1\n")

    expect_refusal(lambda: validate_orient(dict(stored), root=root),
                   "declares its own provenance")
    assert validate_orient(dict(stored), root=root, measure_provenance=False) is not None


def test_the_leave_those_keys_out_sentence_reaches_only_the_sender_who_wrote_them(root):
    """CLAUSE (e). THE FIX IS NOT THE WORDING — IT IS WHICH DOOR CAN SAY IT.

    The sentence tells its reader to leave the floor-authored keys out because THIS DOOR
    writes them. That is true advice for a packet arriving from a ceiling, whose label is
    a claim; it is nonsense said to a berth, whose keys this door already wrote, and
    obeying it would strip a stored measurement to get past a gate. Rewording it would
    have changed nothing, so this tooth does not read the wording: it asserts the sentence
    is REACHABLE at the write door and UNREACHABLE at the deposit door, on one object.
    """
    packet = a_packet_whose_stored_label_the_floor_will_not_reproduce()
    try:
        validate_orient(dict(packet), root=root)
        raise AssertionError("the write door accepted a misdeclared label")
    except OrientRefused as err:
        assert "keys out" in str(err) and "this door" in str(err), str(err)

    # Same object, read mode: the packet passes, so there is no sentence at all. Asserting
    # on the accepted return rather than on a captured string is deliberate — a door that
    # merely softened the wording would still fail here.
    assert validate_orient(dict(packet), root=root, measure_provenance=False) is not None

    # And the deposit door is wired to the read side: its refusal is about the BERTH, a
    # sentence it can only reach by having already passed the provenance question.
    expect_refusal(
        lambda: deposit_orient(packet, [0.0], berth_path="/nonexistent/berth.json",
                               root=root),
        "does not exist on disk")


def main():
    """EVERY TOOTH RUNS, AND A FAILING ONE PRINTS ITS OWN NAME BESIDE THE WORD RED.

    This used to stop at the first failure, and that made the reading of this proof
    depend on ALPHABETICAL ORDER. Measured 2026-09-10: reverting ``orient.py`` under
    ``cairn test --hollow`` redded ``test_a_berth_whose_floor_moved_underneath_it_...``,
    which sorts first, so the run died before printing a single line and the hollow
    reader saw a proof that "printed no teeth at all" — UNRAN, the verdict that means
    *nothing here says whether a tooth checks this file*. The same revert against a
    proof whose first tooth happened to survive would have read fine. A gate whose
    answer turns on a function name's first letter is not measuring what it claims to.

    So a red is REPORTED, not raised: the run continues, the tooth's name goes out on a
    red-marked line (``teeth_printed`` reads the marker word beside the name), and the
    process still exits non-zero at the end. Nothing gets softer — a red proof is still
    a red proof — but the record now names WHICH teeth redded instead of losing the
    whole roster to the first one.
    """
    root = make_root()
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_")]
    failures = []
    try:
        for tooth in teeth:
            try:
                tooth(root)
            except BaseException as err:  # noqa: BLE001 — a red is data here, not control flow
                failures.append((tooth.__name__, err))
                print("RED %s :: %s: %s" % (tooth.__name__, type(err).__name__, err))
            else:
                print("PASS %s" % tooth.__name__)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    if failures:
        print("red: %d of %d teeth" % (len(failures), len(teeth)))
        return 1
    print("green: %d teeth" % len(teeth))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Proof: the orient nexus v0 — the floor reports only what EXISTS, the schema gate
refuses what a hollow build would emit, provenance travels per-field, and the packet
berths gated in instance-space.

Hermetic where it mutates (a fabricated temp root — no live snapshot values are
pinned); the two live-root teeth assert MEMBERSHIP invariants only. Exit 0 = green.
"""
import ast
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")))

from cairn.tools.chain.grammar import (component_roster, ref_exists)
from cairn.devices.builder.machines.orient.orient import (AUTHORED_FIELDS, FLOOR_AUTHORED, OrientRefused, floor_facts, floor_packet, validate_orient, write_packet)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

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
        "provenance": {"intent": "claude", "scope": "claude"},
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
    assert honest["provenance"]["domain"] == "claude", honest["provenance"]
    assert honest["provenance"]["refs"] == "claude", honest["provenance"]


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
                    provenance={"intent": "claude", "scope": "claude"})
    validate_orient(shuffled, root=root)
    assert shuffled["provenance"]["refs"] == "floor", shuffled["provenance"]

    # One added ref and it is the ceiling's field again — the whole value, not a fraction.
    widened = dict(packet, refs=list(packet["refs"]) + ["alpha"],
                   provenance={"intent": "claude", "scope": "claude"})
    validate_orient(widened, root=root)
    assert widened["provenance"]["refs"] == "claude", widened["provenance"]


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
    assert set(blind["provenance"][f] for f in FLOOR_AUTHORED) == {"claude"}, \
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



def main():
    root = make_root()
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_")]
    try:
        for tooth in teeth:
            tooth(root)
            print("PASS %s" % tooth.__name__)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("green: %d teeth" % len(teeth))


if __name__ == "__main__":
    main()

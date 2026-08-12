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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from cairn.chart.orient import (AUTHORED_FIELDS, OrientRefused, component_roster,
                                floor_facts, ref_exists, validate_orient, write_packet)
from cairn.tester.scratch import scratch_dir  # noqa: E402

ORIENT_PY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orient.py"))
# cairn.base.address joined 2026-08-12 (one-owner-for-the-instance-address). This tooth's
# rule is "stdlib plus EXACTLY ONE door", and its stated why is that any other cairn import
# is "a second door or a RE-DERIVATION" — so the admission has to answer the harder half.
# It does: INSTANCE_DIR spelled ~/.cairn/devices/chart/0/packets by hand, which was itself
# one of ten independent re-derivations of an address the 2026-08-12 four-rung ruling
# settled, and the import is what ENDS that re-derivation. What it is not is a reach:
# address.py imports pathlib and nothing else (measured: import_map says ['__future__',
# 'pathlib']), so it opens no tree, no DB and no host, and the transitive tree-free
# condition the inspector-nexus tooth holds over this module is untouched. Two doors now,
# and the second one is a door OUT of a duplication. Admitted by name and dated, per the
# precedent every prior widening in this corpus followed.
ALLOWED_IMPORTS = {"__future__", "hashlib", "json", "os", "re", "time", "pathlib",
                   "cairn.base.address", "cairn.orient.orient"}


def make_root():
    root = str(scratch_dir("chart_orient_proof_"))
    # gamma carries code but NO charter — the census sees it, the roster must not
    for comp in ("alpha", "beta", "gamma"):
        os.makedirs(os.path.join(root, "cairn", comp))
        with open(os.path.join(root, "cairn", comp, comp + ".py"), "w") as fh:
            fh.write("x = 1\n")
        if comp != "gamma":
            with open(os.path.join(root, "cairn", comp, "intention+why.json"), "w") as fh:
                fh.write("{}\n")
    os.makedirs(os.path.join(root, "skills", "chart"))
    return root


def good_packet():
    return {
        "intent": "close alpha's gate against hollow input",
        "domain": "alpha",
        "scope": "the gate only, not beta's consumption of it",
        "refs": ["alpha", "cairn/alpha/intention+why.json"],
        "unknowns": ["whether beta consumes the gated output"],
        "confidence": 0.8,
        "provenance": {"intent": "claude", "domain": "floor", "scope": "claude",
                       "refs": "floor", "unknowns": "claude"},
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
        "fix alpha using cairn/alpha/intention+why.json and bogus/nowhere.py", root=root)
    assert facts["stratum"] == "floor"
    assert facts["components_mentioned"] == ["alpha"]
    assert "cairn/alpha/intention+why.json" in facts["paths_found"]
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
    uncovered = good_packet()
    del uncovered["provenance"]["refs"]
    expect_refusal(lambda: validate_orient(uncovered, root=root), "refs")
    vibes = good_packet()
    vibes["provenance"]["scope"] = "vibes"
    expect_refusal(lambda: validate_orient(vibes, root=root), "vibes")


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


def test_live_roster_carries_chart(root):
    live = component_roster()
    assert "chart" in live and "librarian" in live, \
        "membership invariant: components with charters ride the roster"
    assert set(AUTHORED_FIELDS) == {"intent", "domain", "scope", "refs", "unknowns"}


def test_floor_composes_the_orient_instrument(root):
    """The roster comes from the orient instrument's census, filtered to
    charter-on-disk — never a parallel territory scan. gamma has code but no
    charter: the census sees it, the roster must not (a component without an
    intention doesn't run). Provenance of this tooth: the nexus's first live
    fire, 2026-07-28 — the floor's own parallel roster caught its builder
    having never surveyed cairn/orient."""
    assert component_roster(root) == ["alpha", "beta"]


def test_the_roster_is_measured_ONCE_per_process_and_forgetting_re_measures(root):
    """Ticket residue of the 2026-08-05 measurement: ``ref_exists`` asked
    ``component_roster`` on EVERY ref, and the roster ran a full-tree
    ``device_census`` every time — 168 censuses for ONE ``inspect(component='base')``,
    15,960 ``ast.parse`` calls, 30.3s of wall clock, 99.3% of the profile under one
    line. The lived symptom was ``cairn/build_inspector``: the only proof in the corpus
    the tester could not finish, RED at its 120s wall, every tooth green when run alone.

    The tooth measures the two halves of the fix as PHYSICS, not as speed: the census
    is taken once per root per process (so a judge cannot re-derive its world between
    two of its own findings and contradict itself), and ``forget_roster`` really
    re-measures (so the memo has a door, and the residue is a named IOU rather than a
    trap). It counts CALLS INTO the measurer — the receiver, not the clock — because a
    timing assertion would go red on a slow box and green on a fast one holding the
    identical defect."""
    import cairn.chart.orient as orient_mod
    calls = []
    real = orient_mod.device_census

    def counted(**kwargs):
        calls.append(kwargs.get("root"))
        return real(**kwargs)

    orient_mod.device_census = counted
    try:
        orient_mod.forget_roster(root)
        first = orient_mod.component_roster(root)
        again = orient_mod.component_roster(root)
        third = orient_mod.component_roster(root)
        assert first == again == third == ["alpha", "beta"], (first, again, third)
        assert len(calls) == 1, \
            "three asks, %d censuses — the roster is re-deriving the settled" % len(calls)

        orient_mod.forget_roster(root)
        after = orient_mod.component_roster(root)
        assert after == first and len(calls) == 2, \
            "forget_roster must re-measure, else the memo has no door out"

        # A HANDED-BACK LIST IS A COPY. A caller that mutates what it got must not be
        # editing every later caller's world — the memo is a record, not shared mutable
        # state (Law 6: one owner, and this one gates its own writes).
        after.append("intruder")
        assert orient_mod.component_roster(root) == first, \
            "a caller mutating its copy reached into the memo"
    finally:
        orient_mod.device_census = real
        orient_mod.forget_roster(root)


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
    live = dict(good_packet(), refs=["chart"], ticket="moreabout")
    assert validate_orient(live) is live, \
        "a claim naming a filed ticket passes (moreabout.json is committed)"
    assert ref_exists("chart") and not ref_exists("minted/nowhere.py"), \
        "the public ref semantics are the gate's own (one implementation, two mouths)"


def test_import_allowlist(root):
    """Stdlib plus EXACTLY ONE door into the house: cairn.orient.orient (the
    settled measurer). Any other cairn import is a second door or a re-derivation.
    Composed over that same measurer's import_map (installed 2026-07-28): the
    allowlist matches the module that ACTUALLY ENTERS, not the spelling."""
    from cairn.orient.orient import import_map
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



def test_request_identity_helper(root):
    """Tickets berths-carry-request-identity + the-claim-rides-every-link:
    MISMATCH (both claim, disagree) names both tickets and the resolver;
    VANISH (upstream claims, packet silent) names the upstream claim and the
    one-field fix — INVERTED 2026-08-03 from the old both-sides-claim None by
    Akien's verdict on cbbadb13530f ('no warns, refuse and send back');
    claim ENTRY (packet claims, upstream silent) and unclaimed links stay None."""
    from cairn.chart.orient import identity_lack
    msg = identity_lack({"ticket": "tkt-a"}, {"ticket": "tkt-b"}, "intent_ref")
    assert msg and "tkt-a" in msg and "tkt-b" in msg and "chain tkt-a" in msg, msg
    vanish = identity_lack({}, {"ticket": "tkt-b"}, "intent_ref")
    assert vanish and "vanished" in vanish and "tkt-b" in vanish \
        and "chain tkt-b" in vanish, vanish
    assert identity_lack({"ticket": ""}, {"ticket": "tkt-b"}, "intent_ref"), \
        "an empty-string claim is silence, not a claim"
    assert identity_lack({"ticket": "tkt-a"}, {"ticket": "tkt-a"}, "intent_ref") is None
    assert identity_lack({"ticket": "tkt-a"}, {}, "intent_ref") is None
    assert identity_lack({"ticket": "tkt-a"}, None, "intent_ref") is None
    assert identity_lack({}, {}, "intent_ref") is None


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

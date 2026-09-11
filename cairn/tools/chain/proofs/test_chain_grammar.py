"""Proof: the chain grammar — the shared vocabulary every leg of the chart chain
speaks. The roster is measured ONCE per root per process and forgetting really
re-measures; ref resolution and ticket claims answer the same way at every leg;
identity mismatch and vanish name their remediation; and the tool imports nothing
above its own rung.

Born 2026-08-13 with the grammar itself: these teeth were written against
``cairn/machines/chart/orient.py`` when stage 1 carried the shared parts, and they
moved here with what they measure. A tooth that outlives the module it was pointed
at is measuring something else by accident.

Hermetic (a fabricated temp root — no live snapshot values are pinned); the
live-root assertions are MEMBERSHIP invariants only. Exit 0 = green.
"""
import pathlib
import os
import pytest
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from cairn.tools.chain.grammar import (component_of, identity_lack,  # noqa: E402
                                       ref_exists, ticket_path, ticket_spellings)
from cairn.tools.chain.grammar import _HEX_ID_RE

# The live commons, because this tooth's subject is what happens to a REAL ticket when it
# is retitled — a synthetic root has no tickets/ for a renamed citation to miss.
from cairn.tools.chain.grammar import CAIRN_ROOT as _CR
TICKETS = os.path.join(os.path.dirname(_CR), "CairnCommons", "tickets")
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

GRAMMAR_PY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "grammar.py"))

# A TOOL MAY NOT IMPORT A MACHINE, and this allowlist is where that stops being a
# sentence in CLAUDE.md and becomes physics (Law 4). The rung inversion is not
# hypothetical: on the day the grammar was carved out, ``cairn/tools/tree/tree.py``
# was found importing ``cairn.devices.codemother.machines.orient.orient``, and the first draft of this
# very folder held a ``dial.py`` that imported all seven stage machines. Both were
# fixed by moving code, not by remembering. What the grammar may reach is stdlib,
# the address tool (the one owner of the instance address), and the orient
# INSTRUMENT (the settled measurer it composes) — nothing at machines/ or skills/.
# cairn.tools.gate joined 2026-08-13 under the every-machine-carries-its-own-inspector-
# and-gate ruling: the shared half of every stage inspector emits a PROOF RECORD, and the
# record's vocabulary is the gate tool's. Still a TOOL importing a TOOL — the rung holds.
ALLOWED_IMPORTS = {"__future__", "os", "re", "pathlib", "glob",
                   "cairn.tools.base.address", "cairn.tools.gate.gate",
                   "cairn.tools.orient.orient"}


def make_root():
    root = str(scratch_dir("chain_grammar_proof_"))
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


@pytest.fixture
def root():
    return make_root()


def test_the_roster_is_measured_ONCE_per_process_and_forgetting_re_measures(root):
    """Ticket residue of the 2026-08-05 measurement: ``ref_exists`` asked
    ``component_roster`` on EVERY ref, and the roster ran a full-tree
    ``device_census`` every time — 168 censuses for ONE ``inspect(component='base')``,
    15,960 ``ast.parse`` calls, 30.3s of wall clock, 99.3% of the profile under one
    line. The lived symptom was ``cairn/machines/build_inspector``: the only proof in
    the corpus the tester could not finish, RED at its 120s wall, every tooth green
    when run alone.

    The tooth measures the two halves of the fix as PHYSICS, not as speed: the census
    is taken once per root per process (so a judge cannot re-derive its world between
    two of its own findings and contradict itself), and ``forget_roster`` really
    re-measures (so the memo has a door, and the residue is a named IOU rather than a
    trap). It counts CALLS INTO the measurer — the receiver, not the clock — because a
    timing assertion would go red on a slow box and green on a fast one holding the
    identical defect."""
    import cairn.tools.chain.grammar as grammar
    calls = []
    real = grammar.device_census

    def counted(**kwargs):
        calls.append(kwargs.get("root"))
        return real(**kwargs)

    grammar.device_census = counted
    try:
        grammar.forget_roster(root)
        first = grammar.component_roster(root)
        again = grammar.component_roster(root)
        third = grammar.component_roster(root)
        assert first == again == third == ["alpha", "beta"], (first, again, third)
        assert len(calls) == 1, \
            "three asks, %d censuses — the roster is re-deriving the settled" % len(calls)

        grammar.forget_roster(root)
        after = grammar.component_roster(root)
        assert after == first and len(calls) == 2, \
            "forget_roster must re-measure, else the memo has no door out"

        # A HANDED-BACK LIST IS A COPY. A caller that mutates what it got must not be
        # editing every later caller's world — the memo is a record, not shared mutable
        # state (Law 6: one owner, and this one gates its own writes).
        after.append("intruder")
        assert grammar.component_roster(root) == first, \
            "a caller mutating its copy reached into the memo"
    finally:
        grammar.device_census = real
        grammar.forget_roster(root)


def test_ref_semantics_are_one_implementation(root):
    """Every leg asks the same question of a ref and gets the same answer — that is
    the whole reason the grammar is one module and not nine near-copies. A component
    name resolves; a path to nothing does not."""
    assert ref_exists("chain"), "a live component name must resolve"
    assert ref_exists("skills/chart"), "a live path must resolve"
    assert not ref_exists("minted/nowhere.py"), "a path to nothing must not resolve"
    assert not ref_exists("chart"), \
        "chart is a SKILL, not a component — a bare name resolves against the " \
        "component roster, and a skill is reached by its path"


def test_ticket_path_answers_only_for_a_filed_ticket(root):
    """A packet may claim its ticket only if the ticket is ON FILE in
    CairnCommons/tickets/ (packet-inspector-wire, 2026-07-28) — a claim on an unfiled
    ticket is fabricated attribution (the 2026-07-26 class). The synthetic root has no
    commons beside it, so every claim there answers None; the live-root pass is a
    membership invariant against a committed ticket."""
    assert ticket_path("no-such-ticket", root) is None
    assert ticket_path("moreabout") is not None, \
        "moreabout.json is committed — a filed ticket must resolve"
    assert ticket_path("", root) is None and ticket_path(None, root) is None, \
        "an empty or absent claim is silence, not a claim on a ticket named ''"


def test_a_filed_ticket_answers_to_every_spelling_the_door_admits(root):
    """``ticket_path`` admits a slug or a hex id for the same file; a reader that then
    matched the packet's claim by string equality split one ticket into two (measured
    2026-09-06: five complete chains berthed under their slug, invisible to a hex-id
    lookup). ``ticket_spellings`` is the one set both sides read. Live-root pass against
    a committed hex-slug ticket; synthetic root has no commons, so an unfiled claim
    answers only itself — widening, never narrowing."""
    both = ticket_spellings("6a657e22db6f")
    assert {"6a657e22db6f", "ticket-and-task", "6a657e22db6f-ticket-and-task"} <= both, both
    assert ticket_spellings("ticket-and-task") == both, \
        "the slug and the hex id must resolve to the SAME set, or the gate has two mouths"
    assert ticket_spellings("no-such-ticket", root) == frozenset({"no-such-ticket"}), \
        "an unfiled claim still matches its own packets exactly as before"
    assert ticket_spellings("", root) == frozenset() and ticket_spellings(None, root) == frozenset()


def test_a_slug_claim_must_be_the_WHOLE_slug_and_never_a_TAIL_of_one(root):
    """THE GLOB WAS SWALLOWING WHATEVER IT HAD TO. A slug claim resolves through
    ``*-<claim>.json``, and nothing checked that the part the ``*`` ate was only the hex
    id — so ``ticket_path("it")`` answered with a real ticket whose slug merely ENDS in
    "it", and so did "one", "door", "cast", "ruling" and "ticket". ``_TICKET_RE`` could
    never have caught it: a slug IS a lowercase word list, so the pattern that admits a
    slug admits any word.

    THE COST WAS PAID BY ``reason_has_referent``, which splits an exemption's PROSE into
    words and asks this function about each one. "none, because we talked about it" was
    therefore a reason pointing at something checkable. Measured over the ticket corpus
    the day this was fixed (2026-09-09, voyage 8754ae677af6): 326 ``none, because <X>``
    reasons, 321 passing the floor, 95 passing it honestly.

    Synthetic tickets dir, so the tooth asserts the RULE and not the accident that some
    live slug ends in a common English word — that accident is exactly what could be
    tidied away tomorrow, taking the coverage with it."""
    tickets = pathlib.Path(root) / "synthetic-commons" / "tickets"
    tickets.mkdir(parents=True, exist_ok=True)
    (tickets / "abcdef012345-a-thing-that-ends-in-it.json").write_text("{}")
    (tickets / "abcdef012346-moreabout.json").write_text("{}")
    kw = {"tickets_dir": str(tickets)}

    assert ticket_path("it", **kw) is None, \
        "a TAIL of a slug still resolves — the glob is still swallowing the slug body"
    assert ticket_path("ends-in-it", **kw) is None, \
        "a multi-word tail resolves — the check must compare against the WHOLE slug"
    assert ticket_path("a-thing-that-ends-in-it", **kw) is not None, \
        "the whole slug stopped resolving — the narrowing broke the lookup it was guarding"
    assert ticket_path("abcdef012345", **kw) is not None, \
        "a hex id stopped resolving"
    assert ticket_path("moreabout", **kw) is not None, \
        "a one-word slug is still a WHOLE slug and must resolve"
    assert ticket_path("about", **kw) is None, \
        "a tail of a one-word slug must not resolve"


def test_identity_lack_names_its_remediation(root):
    """Tickets berths-carry-request-identity + the-claim-rides-every-link:
    MISMATCH (both claim, disagree) names both tickets and the resolver;
    VANISH (upstream claims, packet silent) names the upstream claim and the
    one-field fix — INVERTED 2026-08-03 from the old both-sides-claim None by
    Akien's verdict on cbbadb13530f ('no warns, refuse and send back');
    claim ENTRY (packet claims, upstream silent) and unclaimed links stay None."""
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



def test_component_of_reads_a_path_the_orient_floor_would_author(root):
    """THE HOLE THIS CLOSES, and it stayed open for three days: since 2026-08-14 the
    orient floor authors refs as repo-relative PATHS, while every leg downstream keyed
    measured state by BARE NAME. ``survey_floor`` tested ``ref in roster``, a path never
    matched, and the miss fell through to ``ref_exists`` — which PASSES. So the whole
    deterministic stratum was dead and the packet still looked healthy.

    The tooth is the ROUND TRIP, not a string: a bare name answers itself, the path of
    a real component answers its name, and a name that only LOOKS right — a path whose
    last segment matches a component that does not live there — answers None. Pinning
    'cairn/alpha' -> 'alpha' would re-assert today's layout; this asserts the relation.
    """
    for name in ("alpha", "beta"):
        assert component_of(name, root) == name, \
            "a bare roster name must answer itself — the pre-2026-08-14 dialect is " \
            "still spoken by hand-written packets and must not stop resolving"
        assert component_of(os.path.join("cairn", name), root) == name, \
            "the shape the orient floor AUTHORS must resolve — this is the whole hole"

    assert component_of("cairn/gamma", root) is None, \
        "gamma has code and no charter, so it is not on the roster — a census row " \
        "keyed by it would not exist, and a name for it would be a false hit"
    assert component_of("nowhere/alpha", root) is None, \
        "THE LOOK-ALIKE: the basename is a real component, but nothing lives at that " \
        "path. Matching on the tail alone would let any path claim any component."
    assert component_of("cairn/alpha/alpha.py", root) is None, \
        "a FILE inside a component is not the component — it is a plain ref, and " \
        "existence-measuring it is ref_exists's job, not this one's"
    for junk in ("", "   ", None, 7, []):
        assert component_of(junk, root) is None, \
            "a non-ref answers None rather than raising — the floor loops over " \
            "whatever a packet carried, and a crash there is a dead stage"

def test_a_ref_at_a_tickets_OLD_filename_still_resolves_by_id(root):
    """A RETITLED TICKET DOES NOT FABRICATE ITS OWN CITATIONS.

    A ticket file is ``<12-hex id>-<slug>.json``, and only the id is stable — the slug
    is the title, and a title changes whenever work is rescoped. Measured on voyage
    548dd13fb4db (2026-09-11): Akien's mid-voyage correction retitled the ticket, and in
    the same act every berthed packet that had cited it BY PATH stopped resolving.
    ``constraint_traces`` then read those berthed constraints as fabricated attribution —
    a bound citing nothing — when the bound cited a real ticket someone had renamed.

    The berthed packet is a record of truth and may not be rewritten (Law 7), so the
    repair lives in resolution. This tooth pins BOTH halves: the old spelling resolves,
    and the narrowness that keeps it from resolving anything else.
    """
    live = [f for f in os.listdir(TICKETS) if _HEX_ID_RE.match(f.split("-", 1)[0])]
    assert live, "no filed ticket to measure against"
    real = os.path.join(TICKETS, sorted(live)[0])
    tid = os.path.basename(real).split("-", 1)[0]
    assert ref_exists(real), "the ticket's CURRENT path must resolve literally"

    renamed = os.path.join(TICKETS, tid + "-a-title-this-ticket-has-never-carried.json")
    assert not os.path.exists(renamed), "the fixture path must not actually exist"
    assert ref_exists(renamed), \
        "a ref at a ticket's old filename must still resolve — the id is what the " \
        "citation always meant, and the slug was never the referent"

    assert not ref_exists(os.path.join(TICKETS, "ffffffffffff-no-such-ticket.json")), \
        "AN UNFILED ID MUST STILL REFUSE. If any hex-looking name resolved, the " \
        "fallback would certify fabricated attribution instead of catching it"
    assert not ref_exists(os.path.join(TICKETS, "not-a-hex-id-at-all.json")), \
        "a non-hex stem is not a ticket id and gets no fallback"
    assert not ref_exists(os.path.join(os.path.dirname(TICKETS), "decisions",
                                       tid + "-somewhere-else.json")), \
        "THE NARROWNESS: the fallback fires only for a path under tickets/. A real id " \
        "under another directory names a file that does not exist, and must say so"


def test_import_allowlist(root):
    """The rung holds: stdlib plus the two tools the grammar composes, and nothing
    from a rung above. Composed over the orient instrument's own ``import_map`` —
    the allowlist matches the module that ACTUALLY ENTERS, not the spelling."""
    from cairn.tools.orient.orient import import_map
    seen = import_map(GRAMMAR_PY)["measured"]["imports"]
    stray = [m for m in seen
             if not any(m == p or m.startswith(p + ".") for p in ALLOWED_IMPORTS)]
    assert not stray, "grammar.py imports outside its allowlist: %s" % sorted(stray)
    above = [m for m in seen if m.startswith("cairn.machines.") or m.startswith("skills.")]
    assert not above, \
        "a TOOL is importing a MACHINE — the rung is inverted: %s" % sorted(above)


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

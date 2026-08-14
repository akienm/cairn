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
import os
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from cairn.tools.chain.grammar import (identity_lack, ref_exists,  # noqa: E402
                                       ticket_path)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

GRAMMAR_PY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "grammar.py"))

# A TOOL MAY NOT IMPORT A MACHINE, and this allowlist is where that stops being a
# sentence in CLAUDE.md and becomes physics (Law 4). The rung inversion is not
# hypothetical: on the day the grammar was carved out, ``cairn/tools/tree/tree.py``
# was found importing ``cairn.devices.builder.machines.orient.orient``, and the first draft of this
# very folder held a ``dial.py`` that imported all seven stage machines. Both were
# fixed by moving code, not by remembering. What the grammar may reach is stdlib,
# the address tool (the one owner of the instance address), and the orient
# INSTRUMENT (the settled measurer it composes) — nothing at machines/ or skills/.
# cairn.tools.gate joined 2026-08-13 under the every-machine-carries-its-own-inspector-
# and-gate ruling: the shared half of every stage inspector emits a PROOF RECORD, and the
# record's vocabulary is the gate tool's. Still a TOOL importing a TOOL — the rung holds.
ALLOWED_IMPORTS = {"__future__", "os", "re", "pathlib",
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

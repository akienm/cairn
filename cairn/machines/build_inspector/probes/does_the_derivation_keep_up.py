"""PROBE — the_derivation_keeps_up_with_the_corpus: does git's rename record still
answer where the world went, or has a hand quietly gone back to transcribing it?

Berth for the WATCHME that ticket
``a-bulk-move-forwards-itself-from-gits-own-rename-record`` carries, at the path that
ticket's spec names. Berthed beside ``cairn/machines/build_inspector`` because that is
WHAT IT WATCHES — the three address sieves' successor door, where a derivation can stop
answering without one file changing colour, and where
``probes/does_the_address_gate_bite.py`` already watches the neighbouring question of
whether a registered sieve still bites.

THE THING THIS WATCH IS FOR, and it is not "did the code run". The claim the ticket
makes is that the forwarding a bulk move needs is DERIVED — that nobody ever again
transcribes 40 entries out of ``git log`` by hand. That claim can fail silently in
three different directions, and a count of findings tells them apart from none of them:

  - THE RESIDUE GREW. Some address a berthed packet charted resolves in no world: not
    on disk, not through git's transitive rename record, not through a directory
    plurality, and not through a hand-authored order. That is the set a hand still
    owes, and gate (4) of the ticket says it is reported as a NAMED LIST rather than a
    number, because a residue nobody can enumerate is a residue nobody owes.
  - THE DERIVATION LAUNDERED SOMETHING. An address was forwarded to a target that is
    not there (wrong-intent clause 3). A tolerance that disposes a finding by pointing
    at a hole is worse than the red it replaced.
  - THE INSTRUMENT STOPPED. The rename reader answered zero. 444 records stood the day
    this was built, so a reading of zero means git stopped answering, not that the
    corpus stopped moving — and zero renames and a perfectly clean corpus report the
    same number.

THE ASYMMETRY IS THE TICKET'S, TRANSCRIBED. ONE laundered forward satisfies ``enough``
alone: it is strong falsification, because a green tolerance is leaned on where a red
is distrusted by construction (Law 8). CONFIRMATION is weak and needs THREE non-vacuous
sweeps at zero-residue-beyond-the-hand-named, AT LEAST ONE TAKEN AFTER A BULK MOVE —
because a derivation that has never watched the corpus move is the misaimed census this
system has already met once, and keeping up is the entire claim.

WHAT IS ENFORCED HERE AND WHAT IS DECLARED DEBT. The reading half is measured every
time: the residue with every member named, the answered count, the size of the rename
record, and whether any answer points at a hole. The CONSECUTIVE-SWEEPS half needs a
pulse history this probe cannot see from here — nothing beats build_inspector's shim on
a cadence yet — so the confirmation branch reads its history out of ``context`` and,
absent one, declines to clear. Declining is the honest answer: it means the watch stays
open, which is what a watch is for.

AND THE AFTER-A-BULK-MOVE CLAUSE IS MEASURED, NOT ASSUMED. The reading carries the
rename record's size, so a later reading can see that the corpus moved between two
sweeps. Without that number the "at least one after a bulk move" condition would be a
sentence in a docstring that nothing could ever check.

AUTHORITY: none, by construction. This probe deposits and pokes. Re-opening the node
when its intention did not work is build_inspector's act at the register (Law 6).
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "a-bulk-move-forwards-itself-from-gits-own-rename-record"

#: THE HAND-NAMED DISSOLUTIONS — the addresses no rename record and no plurality can
#: ever reach, because the thing did not MOVE, it came apart. The residue is judged
#: against this set, not against zero: a directory whose files scattered has no
#: successor, and answering one anyway is wrong-intent clause (5).
#:
#: Named here so the watch measures the RIGHT zero. Growing this list is how this probe
#: would be made to go green while the claim rotted, so a member arriving without a
#: hand-authored forwarding order behind it on the ticket that charted it is itself the
#: finding — which is why the carry reports the set and its size every time.
#: ALL FOUR ARE ONE EVENT: the chart machine came apart on 2026-08-13 (cairn bf80d5d
#: and ba50814). Its 40 tracked files went to roughly ten different homes — seven
#: builder machines, two tools, two skills — which is why no plurality can name a
#: successor and why answering one anyway would be wrong-intent clause (5). Measured,
#: not asserted: ``_successor_index`` shows cairn/chart/chain.py going to tools/chain,
#: constrain.py to the builder, dial.py to skills/chart, moreabout.py to skills/moreabout.
#:
#: A FORWARDING ORDER CANNOT SAY THIS. Every entry needs a ``to`` that resolves, and a
#: thing that came apart has none — so these cannot be hand-forwarded either, only
#: NAMED, which is what the ticket's falsifier asks for and what this set is.
_HAND_NAMED = frozenset({
    "chart",
    "cairn/chart",
    "cairn/chart/proofs",
    "cairn/chart/intention+why.json",
    "/home/akien/dev/src/cairn/cairn/chart/intention+why.json",
})

#: Measured at this ticket's PROVED crossing, 2026-08-17, by the same read this probe
#: runs. Provenance, not a tunable — a count with nothing to be a delta against says
#: nothing, and this is what the claim was handed over at. The unit is the
#: (address, ticket) PAIR, which is why `asked` is 423 rather than 112: the sieve asks
#: the CHARTING ticket's order, so one address charted by eleven tickets is eleven
#: questions. `answered` is a pair count for the same reason; `answer_index` is the
#: address-keyed collapse of it, and the gap between 406 and 172 IS the eleven-tickets
#: fact — recorded so a later reader comparing the wrong two numbers finds out here.
_AT_PROVED = {"asked": 423, "answered": 406, "answer_index": 172,
              "residue_pairs": 17,
              "residue_addresses": 5, "rename_records": 444,
              # The three-way decomposition, measured at the crossing by disabling each
              # door in turn — because "271 -> 6" cannot say which door did the work,
              # and the whole claim of this ticket is that the DERIVED one did.
              "corpus_address_findings_no_door": 362,
              "corpus_address_findings_hand_door_only": 264,
              "corpus_address_findings_both_doors": 6,
              "hand_entries_written": 14}

#: The confirmation branch's denominator, per the spec. A hand-set constant is a
#: learns-its-gates IOU named at the owning ticket's horizon rather than solved here —
#: the same debt, and the same disclosure, as the sibling probes.
_ENOUGH_SWEEPS = 3


def survey_the_derivation() -> dict:
    """Both halves in one read: what the corpus still cannot forward, and whether the
    instrument that answers is alive.

    Imported inside the function, and that is not style. ``inspector`` walks the census
    and shells out to git; importing it at module scope would put that whole cost on
    anything that merely enumerates probes (``bin/cmd/probescan`` walks every one), and
    it would make this module's own reach a fact about the fire path it is not.
    """
    from cairn.machines.build_inspector.inspector import (
        GitUnreadable, forwarding_residue, ref_exists, rename_records,
    )

    try:
        records = len(rename_records())
    except GitUnreadable as e:
        return {"reader_failed": str(e), "records": 0, "asked": 0, "answered": 0,
                "residue": [], "laundered": [], "beyond_hand_named": []}

    r = forwarding_residue()
    # WRONG-INTENT CLAUSE (3), CHECKED AT THE PROBE AND NOT ONLY AT THE GATE. The gate
    # cannot forward into a hole by construction — but "by construction" is a claim
    # about code, and this is the watch that could catch the construction changing.
    laundered = [{"from": src, "to": dst}
                 for src, dst in sorted(r["answers"].items()) if not ref_exists(dst)]
    residue = [e["address"] for e in r["unanswered"]]
    return {
        "reader_failed": r["reader_failed"],
        "records": records,
        "asked": r["asked"],
        "answered": r["answered"],
        "residue": residue,
        "beyond_hand_named": sorted(a for a in residue if a not in _HAND_NAMED),
        "laundered": laundered,
        "charted_by": {e["address"]: e["charted_by"] for e in r["unanswered"]},
    }


def judge(survey: dict) -> dict:
    """The pure judgement, separable from the read so a proof can feed it fixtures."""
    vacuous = bool(survey["reader_failed"]) or survey["records"] == 0
    return {
        "vacuous": vacuous,
        "reader_failed": survey["reader_failed"],
        # THE STRONG SIGNAL: an answer that points at nothing. Kept apart from a grown
        # residue because they are opposite failures — one forwarded too much, the
        # other too little — and they want different answers.
        "laundered": survey["laundered"],
        "residue_grew": bool(not vacuous and survey["beyond_hand_named"]),
        "beyond_hand_named": survey["beyond_hand_named"],
        "residue": survey["residue"],
        "asked": survey["asked"],
        "answered": survey["answered"],
        "records": survey["records"],
        "hand_named": sorted(_HAND_NAMED),
        "at_proved": dict(_AT_PROVED),
    }


def _seen(context: dict) -> dict:
    return context.get("judged") or judge(context.get("survey") or survey_the_derivation())


def _trigger(now, context: dict) -> bool:
    """TRUE on any of the three things worth waking somebody for: an answer that points
    at a hole, a residue beyond the hand-named dissolutions, or a vacuous reading.

    THE VACUOUS BRANCH IS NOT DECORATION. A rename reader that answered nothing makes
    every address unresolvable and the residue maximal — which reads as "the corpus owes
    a hundred hand entries" at exactly the moment the instrument has stopped working.
    """
    j = _seen(context)
    return bool(j["laundered"]) or j["residue_grew"] or j["vacuous"]


def _enough(context: dict) -> bool:
    """The asymmetric pair, per the ticket's spec.

    STRONG falsification — one laundered forward — satisfies alone. WEAK confirmation
    needs ``_ENOUGH_SWEEPS`` non-vacuous sweeps at zero-beyond-the-hand-named, at least
    one of them taken after the corpus moved; this probe cannot count sweeps from here,
    so it reads them out of ``context["readings"]`` (the shim's memory, since a Probe is
    frozen and holds none) and declines to clear without them. A vacuous reading counts
    toward neither.
    """
    j = _seen(context)
    if j["vacuous"]:
        return False
    if j["laundered"]:
        return True                        # strong falsification, and one is enough
    if j["residue_grew"]:
        return False
    clean = [r for r in (context.get("readings") or [])
             if r.get("records", 0) > 0 and not r.get("beyond_hand_named")]
    if len(clean) < _ENOUGH_SWEEPS:
        return False
    # AT LEAST ONE READING AFTER A BULK MOVE — measured as the rename record having
    # grown between two clean readings, which is what "the corpus moved" means to an
    # instrument that reads git. Without this the confirmation is a derivation that
    # never had to keep up with anything.
    sizes = [r.get("records", 0) for r in clean]
    return max(sizes) > min(sizes)


def _carry(context: dict) -> dict:
    j = _seen(context)
    if j["vacuous"]:
        finding = ("the reading is VACUOUS — the rename reader answered %d records%s, "
                   "so the residue is not a measurement and counts toward neither branch"
                   % (j["records"],
                      " (%s)" % j["reader_failed"] if j["reader_failed"] else ""))
    elif j["laundered"]:
        finding = ("THE DERIVATION LAUNDERED %d ADDRESS(ES) — forwarded to a target that "
                   "is not on disk: %s. A tolerance that disposes a finding by pointing "
                   "at a hole is worse than the red it replaced (wrong-intent clause 3)"
                   % (len(j["laundered"]),
                      ", ".join("%s -> %s" % (x["from"], x["to"]) for x in j["laundered"])))
    elif j["residue_grew"]:
        finding = ("THE RESIDUE GREW BEYOND THE HAND-NAMED DISSOLUTIONS — %d address(es) "
                   "resolve in no world and no ticket says where they went: %s. Each is "
                   "an entry a hand now owes, or a case the derivation should have "
                   "reached and did not"
                   % (len(j["beyond_hand_named"]), ", ".join(j["beyond_hand_named"])))
    else:
        finding = ("clean: %d of %d charted addresses answered, residue %d and every "
                   "member a hand-named dissolution, over %d rename records"
                   % (j["answered"], j["asked"], len(j["residue"]), j["records"]))
    return {
        "finding": finding,
        "judged": j,
        # GATE (4) OF THE TICKET, LITERALLY: the two numbers, and the residue as a NAMED
        # LIST rather than a count a reader can round down.
        "resolved_by_derivation": j["answered"],
        "residue_named": j["residue"],
        "sweeps_needed_to_confirm": _ENOUGH_SWEEPS,
        "sweeps_seen": len([r for r in (context.get("readings") or [])
                            if r.get("records", 0) > 0 and not r.get("beyond_hand_named")]),
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's: DONE when a shake of the nest over the whole "
                             "census reports the reorg residue as ZERO without any "
                             "hand-authored entry for a moved-not-dissolved address, AND "
                             "the two genuine dissolutions are named on a ticket by a "
                             "hand. The seeded half is proved at "
                             "cairn/machines/build_inspector/proofs/"
                             "test_forwarding_derivation.py; this watch is the live half "
                             "of the same question — whether it KEEPS UP",
        "suggests": ("repair the instrument — a rename reader that answered nothing "
                     "cannot report anything, and its zero looks exactly like a clean "
                     "corpus" if j["vacuous"] else
                     "read the forward: either the target moved again and the follow "
                     "stopped short, or the world deleted it — and those want different "
                     "answers. Do NOT widen the rule to make it go away"
                     if j["laundered"] else
                     "read each address: a MOVE the derivation should have reached is a "
                     "defect in the derivation; a DISSOLUTION is a hand-authored "
                     "forwarding entry on the ticket that charted it, and only then a "
                     "member of this probe's _HAND_NAMED"
                     if j["residue_grew"] else
                     "nothing to do; the confirmation branch wants sweeps taken AFTER "
                     "the corpus moves — a derivation that never had to keep up with "
                     "anything has not been tested at its claim"),
    }


# Same placeholder horizon, same tracked debt, as every sibling: PULSES, because the
# shim counts pulses and a clock is bounded out — and nothing beats this machine's shim
# on a cadence today, so loudness rides BaseShim.overdue() alone. Honest as a
# placeholder, dishonest as a measurement; re-tune when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="the forwarding a bulk move needs became DERIVED from git's own rename record, "
        "so nobody transcribes 40 entries out of `git log` by hand again — and that "
        "claim fails silently three ways a finding count cannot tell apart: the residue "
        "grows and a hand quietly starts transcribing again, the derivation forwards "
        "into a hole and disposes a real finding, or the reader answers zero and its "
        "silence reads as a clean corpus. This watch reads all three together, and "
        "treats one laundered forward as strong falsification: a green tolerance is "
        "leaned on, which is worse than the red it replaced",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "the_derivation_keeps_up_with_the_corpus"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_derivation()
    j = judge(s)
    print(json.dumps({"survey": s, "would_trigger": _trigger(None, {"judged": j}),
                      "enough": _enough({"judged": j}), "carry": _carry({"judged": j})},
                     indent=2, default=str))

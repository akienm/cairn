"""PROBE — the_address_gate_bites: is the sieve still there, and is the corpus still clean?

Berth for the WATCHME that ticket ``the-instance-address-is-resolved-never-spelled``
carries, at the path that ticket's spec names. Berthed beside ``cairn/machines/build_inspector``
because that is WHAT IT WATCHES — the sieve registry, where a rule can vanish without a
single file changing colour, and where ``probes/does_the_denied_set_stay_put.py`` already
watches the neighbouring question of whether a denied set stays denied.

WHY IT IS NOT THE SIBLING PROBE. ``cairn/tools/base/probes/hand_spelled_instance_paths.py``
reads the CORPUS half of the same question and has no authority and no view of the gate.
This one reads the GATE half, and the spec says why in as many words: "a rule deleted from
the registry leaves the corpus clean and the gate absent, and those two facts read
identically from a count alone." Zero sites is the answer both a working gate and a
deleted one produce. So this probe asks the registry directly — ``SIEVES`` is a dict, and
membership in it is what makes a sieve run — rather than inferring health from a number.

THE PAIR IS DELIBERATELY ASYMMETRIC, and the asymmetry is the ticket's, transcribed:

  - ONE hand-spelled site standing, on a non-vacuous reading, is STRONG FALSIFICATION and
    satisfies ``enough`` alone. It says the gate is PRESENT AND DID NOT BITE, which is
    worse than no gate at all, because a green gate is leaned on (Law 8: a false green gets
    leaned on by a peer, and a red is distrusted by construction).
  - THREE consecutive non-vacuous readings at zero, at least one of them taken after a
    component that needed instance state was built, is WEAK CONFIRMATION and also satisfies
    it. Weak, because a clean corpus that never had the chance to get dirty is the misaimed
    census this system has already met once.

WHAT IS ENFORCED HERE AND WHAT IS DECLARED DEBT. The reading half is measured every time:
the count, its denominator, and the registry. The CONSECUTIVE-READINGS half needs a pulse
history this probe cannot see from here — nothing beats build_inspector's shim on a cadence
yet — so the confirmation branch reads its history out of ``context`` and, absent one,
declines to clear. Declining is the honest answer: it means the watch stays open, which is
what a watch is for. The debt is named rather than lowered into an ``enough`` that clears
on a single quiet look.

A VACUOUS READING COUNTS TOWARD NEITHER AND IS ITSELF A RED. ``address_rule.scan`` raises
``HollowScan`` when it read zero files, and this catches it rather than letting it out: a
probe that raises on a pulse takes the beat of everything else hanging off that shim with
it, and "the instrument stopped working" belongs in a loud carry, not in somebody else's
traceback.

AUTHORITY: none, by construction. This probe deposits and pokes. Re-opening the node when
its intention did not work is build_inspector's act at the register (Law 6).
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-instance-address-is-resolved-never-spelled"

#: The sieve whose presence IS the gate. Named once, here, and asked of the live registry —
#: a probe carrying its own copy of the rule would go green against itself.
_SIEVE = "address_is_resolved_never_spelled"

#: Measured at this ticket's PROVED crossing, 2026-08-17, by the same scan this probe runs:
#: 0 hand-spelled sites over 274 files, with THREE FILES bearing the weight of a TWO-MEMBER
#: rule — cairn/tools/base/address.py:94 (the module that owns the address) plus two proofs,
#: aider_shim/proofs/test_fence.py:285 and inference_domain/proofs/test_route.py:128,130.
#: The count is of files, not of rule members, and the distinction is the ticket's WRONG-INTENT
#: clause: a fourth member that cannot be said as "a file whose job is to name or to assert the
#: rule" would mean the sieve had become a hand-widened allowlist. Provenance, not a tunable —
#: a count with nothing to be a delta against says nothing, and this is what it was handed over at.
_AT_PROVED = {"sites": 0, "files_read": 274, "exemptions_bearing_weight": 3}

#: The confirmation branch's denominator. Three readings, per the spec, and a hand-set
#: constant is a learns-its-gates IOU named at the owning ticket's horizon rather than
#: solved here — the same debt, and the same disclosure, as the sibling probes.
_ENOUGH_READINGS = 3


def survey_the_gate() -> dict:
    """Both halves in one read: what the corpus holds, and whether the gate is registered.

    Imported inside the function, and that is not style. ``inspector`` walks the census and
    is the component this probe watches; importing it at module scope would put the gate's
    whole import cost on anything that merely enumerates probes (``bin/cmd/probescan`` walks
    every one of them), and it would make this module's own reach a fact about the fire path
    it is not.
    """
    from cairn.machines.build_inspector.inspector import SIEVES
    from cairn.tools.base import address_rule
    from cairn.tools.import_sieve import HollowScan

    registered = _SIEVE in SIEVES
    try:
        found = address_rule.scan()
    except HollowScan as e:
        return {"registered": registered, "sites": [], "count": 0, "files_read": 0,
                "exempted": [], "hollow": str(e)}
    return {"registered": registered,
            "sites": [s["site"] for s in found["sites"]],
            "count": found["count"],
            "files_read": found["files_read"],
            "exempted": found["exempted"],
            "hollow": None}


def judge(survey: dict) -> dict:
    """The pure judgement, separable from the read so a proof can feed it fixtures."""
    vacuous = bool(survey["hollow"]) or survey["files_read"] == 0
    return {
        "vacuous": vacuous,
        "gate_absent": not survey["registered"],
        # THE STRONG SIGNAL: the gate is registered and a site stands anyway. A site found
        # while the gate is ABSENT is a different fact — it is the gate missing, not the
        # gate failing — and the two want different answers, so they are two keys.
        "gate_did_not_bite": bool(survey["registered"] and not vacuous
                                  and survey["count"] > 0),
        "count": survey["count"],
        "files_read": survey["files_read"],
        "sites": survey["sites"],
        "exemptions_bearing_weight": len(survey["exempted"]),
        "at_proved": dict(_AT_PROVED),
    }


def _seen(context: dict) -> dict:
    return context.get("judged") or judge(context.get("survey") or survey_the_gate())


def _trigger(now, context: dict) -> bool:
    """TRUE on any of the three things that are worth waking somebody for: the gate is gone,
    the gate is present and a site stands anyway, or the reading was vacuous.

    THE VACUOUS BRANCH IS NOT DECORATION. A scan that read nothing reports zero, which is
    indistinguishable from a clean corpus at exactly the moment the instrument has stopped
    working — so it fires the probe rather than clearing it.
    """
    j = _seen(context)
    return j["gate_absent"] or j["gate_did_not_bite"] or j["vacuous"]


def _enough(context: dict) -> bool:
    """The asymmetric pair, per the ticket's spec.

    STRONG falsification — one standing site with the gate present — satisfies alone. WEAK
    confirmation needs ``_ENOUGH_READINGS`` non-vacuous zero readings, which this probe
    cannot count from here; it reads them out of ``context["readings"]`` (the shim's memory,
    since a Probe is frozen and holds none) and declines to clear without them. A vacuous
    reading counts toward neither.
    """
    j = _seen(context)
    if j["vacuous"]:
        return False
    if j["gate_did_not_bite"]:
        return True                       # strong falsification, and one is enough
    if j["gate_absent"]:
        return False                      # the gate is missing; a clean count proves nothing
    clean = [r for r in (context.get("readings") or [])
             if r.get("files_read", 0) > 0 and r.get("count") == 0]
    return len(clean) >= _ENOUGH_READINGS


def _carry(context: dict) -> dict:
    j = _seen(context)
    if j["vacuous"]:
        finding = ("the reading is VACUOUS — the address rule read zero files, so the count "
                   "is not a measurement and counts toward neither branch")
    elif j["gate_absent"]:
        finding = (f"THE GATE IS ABSENT — {_SIEVE} is not in build_inspector.SIEVES. A sieve "
                   "that is not registered judges nothing, and the corpus reads clean for "
                   "exactly the wrong reason")
    elif j["gate_did_not_bite"]:
        finding = (f"THE GATE DID NOT BITE — {j['count']} hand-spelled site(s) stand with "
                   f"{_SIEVE} registered and shaken. A green gate is leaned on; this is "
                   "worse than no gate")
    else:
        finding = (f"clean: 0 hand-spelled sites over {j['files_read']} files, gate "
                   "registered")
    return {
        "finding": finding,
        "judged": j,
        "readings_needed_to_confirm": _ENOUGH_READINGS,
        "readings_seen": len([r for r in (context.get("readings") or [])
                              if r.get("files_read", 0) > 0 and r.get("count") == 0]),
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's (c): A PLANTED EIGHTH SPELLING REDS THE "
                             "INSPECTION — 'a sieve that never fires is indistinguishable "
                             "from no sieve, and after a successful conversion the corpus "
                             "offers no live offender to demonstrate it on'. The planted "
                             "case is proved at "
                             "cairn/machines/build_inspector/proofs/test_address_sieve.py; "
                             "this watch is the live half of the same question",
        "suggests": ("register the sieve, or find the commit that removed it — a rule "
                     "deleted from the registry leaves the corpus clean and the gate absent"
                     if j["gate_absent"] else
                     "read the site: either it is a shape the resolver has no rung for "
                     "(escalate, do not widen the rule), or it is a caller that did not "
                     "compose cairn.tools.base.address, and those want different answers"
                     if j["gate_did_not_bite"] else
                     "repair the instrument — a vacuous scan cannot report anything"
                     if j["vacuous"] else
                     "nothing to do; the confirmation branch wants readings taken AFTER a "
                     "component that needed instance state was built"),
    }


# Same placeholder horizon, same tracked debt, as every sibling: PULSES, because the shim
# counts pulses and a clock is bounded out — and nothing beats this machine's shim on a
# cadence today, so loudness rides BaseShim.overdue() alone. Honest as a placeholder,
# dishonest as a measurement; re-tune when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="the instance address got ONE owner and then a gate that reds a second spelling — "
        "but a count alone cannot tell a working gate from a deleted one, since both leave "
        "the corpus reading clean. This watch reads the registry and the corpus together, "
        "and treats a site standing while the gate is present as strong falsification: a "
        "green gate is leaned on, which is worse than no gate at all",
    trigger=_trigger,
    to="harbor_master",
    # THE TICKET RIDES AS AN ADDRESS, NEVER AS A BARE ID — ruled 2026-08-05, and caught HERE
    # on 2026-08-17 by test_probe_carry's corpus tooth, which is what that ruling was turned
    # into. This body first carried `_OWNING_TICKET` raw; a receiver holding an id has to know
    # where tickets live to do anything with it, and seven probes once re-derived exactly that.
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET), "object": "the_address_gate_bites"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_gate()
    j = judge(s)
    print(json.dumps({"survey": s, "would_trigger": _trigger(None, {"judged": j}),
                      "enough": _enough({"judged": j}), "carry": _carry({"judged": j})},
                     indent=2, default=str))

"""PROBE — is ``persist_validation`` the only path into a validation record IN PRACTICE?

Berth for the WATCHME that ticket ``standing-gates-the-newest-link-and-run-proof-names-its-sink``
carries. Berthed here, beside the tester, because that is WHAT IT WATCHES: the door it asks
about is ``cairn/devices/tester/validation_store.persist_validation``, and the hand that would
route around it is a caller of ``TesterDevice.run_proof``. The ticket it was compiled from
lives in CairnCommons and this probe deliberately does not follow it there.

THE EFFICACY QUESTION, AND WHY IT IS THIS ONE AND NOT "DOES THE DOOR WORK".

The door already worked. It was sealed on 2026-08-05 with three physics layers (ticket
``validation-store-door-is-the-only-path``) and its proofs went green and stayed green. Then,
on 2026-08-07 and 2026-08-08, two and three days later, two voyages wrote six validation
trails around it anyway. Every layer held. The corpus routed around them, because nothing in
``cairn test`` or ``run_proof`` could land a seal at all, so a builder who needed one reached
past the physics rather than through it.

So the question a tooth cannot ask is the one worth a probe: not whether the door refuses a
bypass — proofs settle that in a fixture — but whether, ACROSS REAL VOYAGES, anybody still
needs to go around. That is a question about live traffic over time, and the only honest
instrument for it is the records themselves.

THE INSTRUMENT CHANGED ON 2026-08-16 AND THE QUESTION DID NOT (ticket
a-validation-is-one-current-record-not-a-trail). This probe used to count entries carrying no
``trail_link``. The chain retired with the append-only-ness it protected, so that key is
written by nothing and counting it would measure a corpus-wide zero forever — the failure this
file's own comment anticipated when it imported the key rather than spelling it ("a rename
cannot leave this probe quietly measuring a key nothing writes any more"). This is that case,
arriving as a retirement rather than a rename.

WHAT REPLACES IT IS STRICTLY HARDER TO FORGE. ``persist_validation`` now writes a
ONE-ELEMENT list, always, and the one-time collapse left every one of the 90 files at length
one. So a validations file holding two or more records is a write that did not come through
this door — and unlike a link, that is not a number a bypassing hand can compute its way past;
producing it requires doing the exact thing the probe is watching for. The old instrument
could be satisfied by a forger who bothered to import ``_link_for``; this one cannot be
satisfied at all.

THE OBSERVATION IS NOT COMPUTED HERE. ``the_collapse_holds_in_live_traffic``, beside this
file, is armed against the same measurement for a different question — does the collapse HOLD,
rather than does anybody still NEED to go around — and its ticket is the one that specified
the instrument, so the survey lives there and this probe imports it. Two probes computing one
number separately is two numbers that can drift, and the drifting one is invisible. Whether
the corpus should carry both watches at all is the OWNER's call (Law 6), recorded as a finding
rather than decided by either probe.

THE POST-FIX CUTOFF IS THE WHOLE MEASUREMENT. Counting anything that predates the collapse
would make this probe fire forever on a question already answered. Counting only what stands
AFTER it is what makes the answer falsifiable.

WHAT THIS PROBE PARTLY WATCHES IS THE VOYAGE THAT ARMED IT, and that is said out loud rather
than glossed: the seals this build lands are among the first post-fix records it will count.
They are honest evidence — they went through the door, by the route the fix built — but they
are the author's own participation, and at n=2 out of 20 they cannot carry the answer alone.
The floor is what keeps that true.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that re-opens
a node whose intention did not work is the OWNER's act (Law 6).

FILES ONLY — no device, no bus, no network, so it stays cheap enough to sit on a pulse.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

# Class-space root: this file is cairn/devices/tester/probes/<name>.py.
_CLASS_SPACE = Path(__file__).resolve().parents[4]

# The date the collapse landed. Records dated at or after it are the population; everything
# below it predates the one-record rule and is read past, never counted and never touched. An
# ISO-8601 prefix compares correctly as a string against the record's `date`, which is
# `datetime.isoformat(timespec="seconds")`.
_FIX_LANDED = "2026-08-16"  # kept for the record; the shared survey owns the cutoff

# The sample size below which the question cannot be answered at all. Two or three post-fix
# records all landing singly is a plausible run; twenty is a pattern. It is a round number
# honestly chosen and not derived, which is the same debt does_optional_mean_never_carried
# carries at its own floor — re-tune it when the seal rate is a measured number rather than a
# guess.
_ENOUGH = 20

# The node this probe was compiled from. A bare id because it is an IDENTITY; `owning_ticket`
# builds the address that rides in the payload (ruling 2026-08-05, "the file path is the link").
_OWNING_TICKET = "standing-gates-the-newest-link-and-run-proof-names-its-sink"


def survey_the_corpus() -> dict:
    """The shared observation, borrowed rather than re-derived (Law 1).

    ``the_collapse_holds_in_live_traffic.survey_the_corpus`` counts, over every validations
    file in class-space, how many records stand at or after 2026-08-16 and how many files hold
    more than one — the shape ``persist_validation`` cannot write. That is exactly the datum
    this probe needs, so it is imported, not copied. Only the key name is adapted: this probe
    has always spoken of the population as post-FIX (the fix being the door's affordances,
    2026-08-16's collapse being the second one it has outlived).
    """
    from cairn.devices.tester.probes.the_collapse_holds_in_live_traffic import (
        survey_the_corpus as shared)
    s = shared()
    return {"post_fix": s["post_collapse"], "multi": s["multi"],
            "multi_count": s["multi_count"], "unreadable": s["unreadable"]}


def _trigger(now, context: dict) -> bool:
    """TRUE when enough has landed since the fix to judge AND at least one entry still
    arrived around the door. Both clauses carry weight: firing on a thin corpus pokes the
    owner about noise, and firing on zero such files pokes about a mechanism that is
    working."""
    s = context.get("corpus") or survey_the_corpus()
    return s["post_fix"] >= _ENOUGH and s["multi_count"] > 0


def _enough(context: dict) -> bool:
    """CLEARED once enough has landed since the fix to judge AND every one of those entries
    came through the door. At that moment the question is answered — the affordance is being
    used and nobody is routing around it — and a standing watch on a settled question is the
    re-derivation Law 1 refuses.

    THE FLOOR SITS ON THIS CLAUSE TOO, and that is not symmetry for its own sake. Without it
    this clears at n=0: an empty post-fix corpus has no multi-record files in it, so the watch
    would retire on its very first pulse, before a single seal had been written — the exact
    asymmetry that made ``does_optional_mean_never_carried`` clear at n=1 against a corpus
    of one ticket, which was itself. A watch that can clear before it can fire is not a
    watch.
    """
    s = context.get("corpus") or survey_the_corpus()
    return s["post_fix"] >= _ENOUGH and s["multi_count"] == 0


def _carry(context: dict) -> dict:
    """The datum that rides back: the counts, the offending addresses WITH every caller that
    wrote into each, and a pointer to the ticket the finding is against (Law 6 — the ticket is
    the commons', not ours)."""
    s = context.get("corpus") or survey_the_corpus()
    return {"finding": f"{s['multi_count']} validations file"
                       f"{'' if s['multi_count'] == 1 else 's'} hold more than one record "
                       f"after the collapse — a shape persist_validation cannot write",
            "post_fix_records": s["post_fix"],
            "multi_record_files": s["multi"],
            "unreadable_trails": s["unreadable"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the door was made reachable (run_proof's required sink, "
                                 "`cairn test --seal`) and a caller went around it anyway — "
                                 "so reachability was not what was missing",
            "suggests": "read every `caller` in each named file and ask what it needed that "
                        "the sink does not offer. The 2026-08-05 fix answered a bypass with a "
                        "fourth lock and the corpus routed around it within two days; the "
                        "finding to look for here is an UNSERVED NEED, not a missing refusal"}


# THE HORIZON. Same unit and same honest placeholder as the sibling probe at
# cairn/tools/base/probes/does_optional_mean_never_carried.py: the unit is PULSES because the
# shim counts pulses, the wall-clock beat that would drive them is a filed edge rather than a
# built one, so nothing pulses this shim today and the loudness rides the read-side door
# (`BaseShim.overdue()`) alone. 1000 is "clearly a long standing" against any beat rate we
# would plausibly pick. It is honest as a placeholder and dishonest as a measurement, and it
# must be re-tuned when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="the door was sealed with physics layers and the corpus wrote around it "
        "anyway, two days later, because no reachable path could land a seal — so the "
        "question is not whether the door refuses a bypass but whether anybody still needs "
        "one now that run_proof takes a sink and `cairn test` takes --seal",
    trigger=_trigger,
    to="tester",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

"""PROBE — do the things that CLAIM to be devices match the things that are ruled devices?

Berth for the WATCHME that ticket ``device-ness-is-decided-at-the-shim`` carries. Berthed
here, beside ``cairn/tools/base``, for two reasons that happen to coincide: this is WHAT IT
WATCHES (``BaseDevice`` lives one directory up and is the artifact whose claim this
question is about), and ``cairn/tools/base`` is ITSELF a discovered device — it holds this
``probes/`` folder — so the discovery pass arms this file with no hand-registration. The
ticket it was compiled from stays in CairnCommons and the probe deliberately does not
follow it there.

THE EFFICACY QUESTION. Akien ruled device-ness twice on 2026-08-11 — "a shim fits TO the
device" and "the unit is the folder, not the registration" — and the second ruling SHIPPED
the same day (``cairn/devices/ground_loop/discovery.py``, commit 2081efa). So the mechanism is not
what is missing. What is missing is anything LOUD: the old axis (subclass ``BaseDevice``)
and the ruled axis (a ``probes/`` directory) disagree about NINETEEN of a twenty-member
union, and nothing anywhere says so. An empty disagreement and an unmeasured disagreement
have byte-identical resting states — which is the exact failure ``discovery.py``'s own
header records about the stale subscribe list, repeating one layer up.

IT NAMES NAMES, NEVER A COUNT. A count is what lets a divergence sit still: "19" reads the
same in a report whether it is the same nineteen every week or a different nineteen. The
carrier ships the per-component lists, so the first thing a reader sees is that ``bus`` and
``ground_loop`` — the spine — are not devices under the ruling, and that ``cairn/tools/base``
itself is a device under the ruling and not under its own class.

THE DIVERGENCE IS NOT A BUG REPORT ABOUT THE INHERITORS. Eleven components are ruled
devices while subclassing nothing — the CALIBRE SHAPE, which the old axis could not
represent at all. That half of the number is the ruling working. The probe reports both
halves separately rather than summing them into one alarming integer.

WHAT THIS PROBE FIRES ON, STATED AGAINST THE FIRER. ``BaseShim._was_true`` starts empty, so
a trigger that is TRUE at the first pulse is a CROSSING and pokes — the resting state here
is a live crossing, not a quiet watch. ONE RESIDUAL IS NAMED RATHER THAN GLOSSED: the
crossing memory is per-shim-instance and in-process, so every restart of the ground loop
re-pokes this once; that is honest noise, not a flood, and damping it blind would be
guessing at a width nobody has measured.

CORRECTED AT THE LIVE FIRE, 2026-08-11, and the superseded words are kept because they were
a claim about the world that the world refused. This paragraph carried a second residual:

    "(b) NOTHING PULSES THIS SHIM TODAY. The live trouble
     ``the-runtime-spine-has-never-run`` is the standing condition, so this probe is
     ARMED and — until a heartbeat runs — has NEVER FIRED."

IT HAD ALREADY FIRED WHEN THAT WAS WRITTEN. Measured at /sail step 5: ``python3 -m
cairn.devices.ground_loop`` is running (pid 109150, up since 13:37:45), 1344 beats, pulsing 13
subscribers of which ``base`` is one, and this probe's poke is ON THE BUS — envelope
``a813b9fd37964d42a99bd93321c22a4a``, ``base -> harbor_master``, 2026-08-11T14:20:07,
carrying the nineteen-way divergence by name. So the beat runs, the shim is pulsed, the
crossing was detected, the carrier ran, the bus took it, and it landed — six links, none of
them my hand. THE HORIZON BELOW IS THEREFORE A REAL NUMBER NOW, not a placeholder against a
counter that could never move.

WHY THE SENTENCE WAS WRITTEN AT ALL, since that is the reusable part: it was inherited from
a LIVE TROUBLE rather than measured. ``the-runtime-spine-has-never-run`` (opened 2026-07-30)
still stands in the inbox, and its finding 1 — "zero live callers of ``.beat(``" — was true
when written and was retired on 2026-08-09 by ``ground_loop/__main__.py`` (ticket
ground-loop-writes-its-own-liveness), which ``loop.py``'s own docstring records. Nothing
re-measured the trouble when the thing it described was built, so a correct-when-written
record aged into a false standing condition, and I copied it forward as a present-tense fact
about my own artifact. That is this corpus's characteristic failure — an honest note aging
into an assumed-built — running in the opposite direction: an honest note aging into an
assumed-BROKEN. Both are the same defect, which is a record of the world that nothing
re-reads against the world.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that re-opens
a node whose intention did not work is the OWNER's act (Law 6). It does not rewrite a single
component to conform, and the chart's bounds put that work explicitly out.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.deviceness import HEALTH_QUERY_CLAUSE, divergence
from cairn.tools.base.probe import Probe, owning_ticket

_TICKETS = Path(__file__).resolve().parents[4].parent / "CairnCommons" / "tickets"

# The node this probe was compiled from. A bare id because it is an IDENTITY; what RIDES is
# the path ``owning_ticket`` builds from it (Akien 2026-08-05, "the file path is the link").
_OWNING_TICKET = "device-ness-is-decided-at-the-shim"

# The sibling ticket that RULES the axis. Its ratification is this watch's stopping
# condition — see ``_enough``, where the reason is argued rather than asserted.
_RULING_TICKET = "runtime-role-is-a-second-axis"


def measure(context: dict | None = None) -> dict:
    """The three axes, per component, from the one shared predicate.

    Composed from ``cairn.tools.base.deviceness`` rather than re-derived here. A probe that
    reimplemented the predicate would be the fifth hand-written answer to the question this
    whole ticket exists to answer once — and it would be the one answer nobody reads as a
    decision, because it would be buried in a trigger body.
    """
    if context and isinstance(context.get("deviceness"), dict):
        return context["deviceness"]
    return divergence()


def _trigger(now, context: dict) -> bool:
    """TRUE while the ruled axis and the inheritance axis disagree about any component.

    One clause, no sample floor, and that is deliberate: this is not a survey over an
    accumulating corpus (where n=1 would be noise), it is a census of a fixed set that is
    complete on every read. A floor here would only delay a finding that is already whole.
    """
    return measure(context)["symmetric_difference_ruled_vs_inherited"] > 0


def _enough(context: dict) -> bool:
    """CLEARED once the AXIS ITSELF HAS BEEN RULED — not once the divergence reaches zero.

    THE TICKET'S OWN ``enough`` IS UNREACHABLE AND THIS IS THE CORRECTION, made at the build
    and recorded on the ticket rather than quietly swapped. The cast wrote: "symmetric
    difference zero across three consecutive pokes." A poke only happens when the difference
    is NON-zero (``_trigger`` above, and ``enough`` is asked ONLY AFTER A FIRE — see
    ``BaseShim.on_pulse``). So "zero across three pokes" describes a state that produces no
    pokes at all: the watch could never clear, by construction. This is the failure shape my
    own record calls *the check goes red at the moment its condition is satisfied*, inverted
    — a clear that goes unreachable at the moment its condition is satisfiable.

    THE TICKET'S OWN ``consumer`` FIELD ALREADY CONTRADICTED ITS ``enough``, in the same
    block: "a divergence PERSISTING PAST 'enough' raises to the trouble lane." That sentence
    only parses if enough is reachable while the divergence still stands. The consumer clause
    is the coherent half and this predicate implements it.

    SO WHAT IS THE STOPPING CONDITION? The question "do the claims match the shims?" stops
    being a finding when the axis is RULED — when a decision exists saying which axis wins
    and what the other one means. That ruling is the sibling ticket's, gated at Akien's
    signature (the chart's bounds put naming the axis explicitly OUT of this ticket). Once it
    rests at PROVED, a standing watch on the disagreement is a settled question re-derived on
    a cadence, which is Law 1's defect. Until then the watch stands — which is the honest
    answer, because the disagreement is real and unratified.

    THE SECOND CLAUSE OF THE CAST'S ``enough`` SURVIVES INTACT and is satisfied by
    construction: "every component carrying the device role exercised by the predicate at
    least once." ``divergence()`` calls the predicate over the whole union on every read, so
    no firing of this probe can report a set it did not exercise — the vacuous green that
    clause exists to refuse is unreachable here rather than merely avoided.
    """
    path = _TICKETS / f"{_RULING_TICKET}.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8")).get("state")
    except Exception:  # noqa: BLE001 — a ticket this probe cannot read is not a ruling
        return False
    return isinstance(state, str) and "[PROVED]" in state


def _carry(context: dict) -> dict:
    """The datum that rides back: both axes named PER COMPONENT, and the ticket the finding
    is against — a pointer to it, not a copy (Law 6: the ticket is the commons', not ours)."""
    m = measure(context)
    return {
        "finding": (
            f"device-ness disagrees about {m['symmetric_difference_ruled_vs_inherited']} "
            f"components: {len(m['inherits_but_not_ruled'])} inherit BaseDevice and are not "
            f"on the roster the beat reads, {len(m['ruled_but_inherits_nothing'])} are ruled "
            f"devices with no device class at all"
        ),
        "ruled_devices": m["ruled_devices"],
        "claims_device_by_inheritance": m["claims_device_by_inheritance"],
        "inherits_but_not_ruled": m["inherits_but_not_ruled"],
        "ruled_but_inherits_nothing": m["ruled_but_inherits_nothing"],
        "on_all_three_axes": m["on_all_three"],
        "the_spine_is_not_a_device": [
            c for c in ("bus", "ground_loop") if c in m["inherits_but_not_ruled"]
        ],
        "predicate_is_half_built": HEALTH_QUERY_CLAUSE,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "'is X a device?' is answered by ASKING X. It is not: the fitted clause is "
            "answered from disk and the health-query clause names nothing that exists. The "
            "Calibre-shaped half of the falsifier passes eleven times over; the asking half "
            "is unbuilt and this payload says so on every firing."
        ),
        "suggests": (
            "rule the axis (ticket runtime-role-is-a-second-axis, at Akien's signature gate) "
            "— the divergence cannot be dispositioned component-by-component until it is "
            "known which axis wins and what the loser means"
        ),
    }


# THE HORIZON. The unit is PULSES because the shim counts pulses, and 100 rather than the 1000
# its siblings carry: this trigger is TRUE right now, so an honest horizon is "if this has not
# poked within a hundred pulses of being seen, the firing path is broken, not the world" — a
# shorter number because a probe whose trigger is already true has no innocent explanation for
# silence.
#
# CORRECTED AT THE LIVE FIRE, 2026-08-11 — superseded words kept, they were the load-bearing
# part: this comment read "TODAY NOTHING PULSES THIS SHIM ... no beat will move this counter",
# and called 100 "dishonest as a measurement and honest as a placeholder", carrying a re-tune
# as tracked debt "when the beat becomes a real number." THE BEAT WAS ALREADY A REAL NUMBER.
# The loop has 1344 beats behind it and this probe poked at its FIRST opportunity, so the
# silence clause never had to arbitrate anything. THE DEBT IS DISCHARGED RATHER THAN RE-TUNED,
# and the reason is worth more than the number: 100 was chosen as a placeholder against a dead
# counter, and it turns out to mean roughly 100 seconds against a live one-second beat. That is
# a defensible width for "the firing path is broken" — but it is defensible by luck, not by
# derivation, and this comment says so rather than letting a lucky constant pass as a measured
# one. A hand-set constant in a gate is a learned value stranded in a human's head; what would
# retire it is the horizon being derived from observed poke latency, which is the learning
# question ``cairn/tools/base``'s charter owes and nothing here pretends to answer.
_HORIZON = 100

PROBE = Probe(
    why="do the things that CLAIM device-hood match the things that ARE devices? — the "
        "divergence Akien's ruling created and nothing announces",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

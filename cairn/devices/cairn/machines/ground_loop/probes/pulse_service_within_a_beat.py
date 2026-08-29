"""PROBE — does a dropped (or removed) pulse.py actually get served within a beat?

Berth for the WATCHME that ticket ``the-pulse-file-is-the-subscription`` carries. Berthed
beside ``cairn/devices/cairn/machines/ground_loop`` because that is WHAT IT WATCHES: the pulse half of
``loop._reconcile`` and the ``PulseCache`` in ``discovery.py``.

THE CLAIM UNDER WATCH. The design's whole promise is that presence IS the subscription:
place ``groundloop/pulse.py`` and the running loop activates it within a beat; remove it and
the loop deactivates and unloads it within a beat — same pid throughout, nothing registered,
nothing restarted. The proofs pin that in a fixture world; this probe watches it hold in the
LIVE one, where the 2026-08-14 lesson lives (a loop that measured itself older than its own
code nine times overnight — the staleness this design exists to make impossible).

WHAT IT READS: the loop's own liveness record (``~/.cairn/devices/cairn/machines/ground_loop/0/
liveness.json``) — ``state.pulse_events``, the bounded in-memory ring ``state()`` rides
into the record every beat. No new file, no new firing path: this probe rides its own
device's shim pulse like every probe in the corpus, and reads the record the loop already
writes (constrain's no-new-durable-record bound, honored by construction).

THE MEASUREMENT, honestly bounded. An ACTIVATION event carries the file's mtime and the
beat's clock, so (served_at - mtime) is a real latency reading; "within 2 beats" needs
seconds-per-beat, which the event stream itself yields whenever two events landed on
different beats (Law 10 — a coarse measurement to sharpen, never "unmeasurable"). A
DEACTIVATION carries no mtime — the file is gone, and nothing stamps the moment of the
``rm`` — so its within-a-beat reading is structural: the event exists in a ring that lives
and dies with the process, stamped with the beat that served it. Both counts ride the carry,
labeled apart, because they are different strengths of evidence.

ZERO RESTARTS ACROSS THE EVENTS is structural too, and that is the point: the ring is
in-memory state surfaced through ``state()``, so every event in one record was witnessed by
the pid that record names. A restart empties the ring — the count starts over, which is
exactly what "zero loop restarts across them" demands.

AUTHORITY: none. This probe deposits and pokes; re-opening the node is the owner's act
(Law 6). A fire means the design is being exercised live — read the carry's events against
the ticket's falsifier.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-pulse-file-is-the-subscription"

# Same placeholder horizon, same tracked debt, as the sibling probes: the beat rate is not
# yet a real number.
_HORIZON = 1000

# The ticket's bound, in beats: (served_at - file_mtime) at most 2 beats.
_BEAT_BOUND = 2

# The coarse fallback when the event stream cannot yet yield seconds-per-beat (fewer than
# two events on distinct beats): the ruled cadence is 1s and the measured beat overspends
# to ~2.5s (ticket the-beat-spends-2500ms-on-triggers-against-a-1s-cadence), so 2 beats is
# bounded above by 10s with slack. A reading against this fallback is labeled as such in
# the carry — a coarse measurement to sharpen, not a hidden assumption.
_FALLBACK_BOUND_S = 10.0


def survey_the_record() -> dict:
    """The live read: the loop's own liveness record, taken whole. One small JSON read."""
    from cairn.devices.cairn.machines.ground_loop.liveness import read_liveness
    return read_liveness(datetime.now(timezone.utc).astimezone())


def judge(survey: dict) -> dict:
    """The pure judgement, separable from the read so the proof can feed it fixtures."""
    record = survey.get("record") or {}
    state = record.get("state") or {}
    events = state.get("pulse_events") or []

    # seconds-per-beat, measured from the stream itself when it can be.
    stamped = []
    for ev in events:
        if ev.get("at") is None or ev.get("beat") is None:
            continue
        try:
            stamped.append((ev["beat"], datetime.fromisoformat(ev["at"]).timestamp()))
        except (ValueError, TypeError):
            continue
    seconds_per_beat = None
    distinct = sorted(set(stamped))
    if len({b for b, _ in distinct}) >= 2:
        (b1, t1), (b2, t2) = distinct[0], distinct[-1]
        if b2 > b1 and t2 > t1:
            seconds_per_beat = (t2 - t1) / (b2 - b1)

    bound_s = (seconds_per_beat * _BEAT_BOUND) if seconds_per_beat else _FALLBACK_BOUND_S

    activations_within, activations_late = [], []
    for ev in events:
        if ev.get("event") != "activated" or ev.get("mtime") is None or ev.get("at") is None:
            continue
        try:
            served = datetime.fromisoformat(ev["at"]).timestamp()
        except (ValueError, TypeError):
            continue
        gap = served - float(ev["mtime"])
        reading = {"device": ev.get("device"), "path": ev.get("path"),
                   "beat": ev.get("beat"), "gap_s": round(gap, 3)}
        (activations_within if gap <= bound_s else activations_late).append(reading)

    deactivations = [{"device": ev.get("device"), "path": ev.get("path"),
                      "beat": ev.get("beat")}
                     for ev in events if ev.get("event") == "deactivated"]

    return {
        "verdict": survey.get("verdict"),
        "pid": record.get("pid"),
        "beats": state.get("beats"),
        "events_total": len(events),
        "seconds_per_beat": seconds_per_beat,
        "bound_s": bound_s,
        "bound_is_fallback": seconds_per_beat is None,
        "activations_within_bound": activations_within,
        "activations_late": activations_late,
        "deactivations_served": deactivations,
        "measured_within_a_beat": len(activations_within) + len(deactivations),
        "refusals": state.get("pulse_refusals") or [],
        "services_live": state.get("pulse_services") or [],
    }


def _seen(context: dict) -> dict:
    return context.get("judged") or judge(context.get("survey") or survey_the_record())


def _trigger(now, context: dict) -> bool:
    """TRUE when the record shows pulse service actually happening — an activation served
    within the bound, or a deactivation served (its within-a-beat reading is structural).
    An empty surface is FALSE, never a raise: a system with no pulse files yet is healthy
    and untested, not broken (Law 9 — silence is untested, not evidence)."""
    s = _seen(context)
    return s["measured_within_a_beat"] > 0


def _enough(context: dict) -> bool:
    """CLEARED at the ticket's own number: 10 add-or-remove events measured within the
    bound, all inside ONE record — which is what makes 'zero restarts across them' true by
    construction, because the event ring lives and dies with the pid the record names. A
    late activation anywhere in the ring blocks the clear: the watch has found what it
    watches for and must keep standing."""
    s = _seen(context)
    return s["measured_within_a_beat"] >= 10 and not s["activations_late"]


def _carry(context: dict) -> dict:
    s = _seen(context)
    return {
        "finding": "the live loop is serving pulse files by presence alone — activations "
                   "and deactivations observed in its own record, same pid, no restart",
        "pid": s["pid"],
        "beats": s["beats"],
        "seconds_per_beat": s["seconds_per_beat"],
        "bound_s": s["bound_s"],
        "bound_is_fallback": s["bound_is_fallback"],
        "activations_within_bound": s["activations_within_bound"],
        "activations_late": s["activations_late"],
        "deactivations_served": s["deactivations_served"],
        "measured_within_a_beat": s["measured_within_a_beat"],
        "refusals": s["refusals"],
        "services_live": s["services_live"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's clause, verbatim: 'Any of those requiring a "
                             "loop restart, a hand-maintained list, or a registration act "
                             "falsifies the intent.' A late activation in this carry is "
                             "that clause failing live; read activations_late first.",
    }


PROBE = Probe(
    why="the design's whole promise is that presence IS the subscription — pulse.py "
        "dropped at a component's address is served within a beat and removed is unloaded "
        "within a beat, same pid, nothing registered, nothing restarted; the proofs pin "
        "this in a fixture world and this watch is where the live loop either keeps that "
        "promise ten times or is caught breaking it",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the live record and what the pair would do with it now.
    s = survey_the_record()
    j = judge(s)
    print(json.dumps({"judged": j,
                      "would_trigger": _trigger(None, {"judged": j}),
                      "enough": _enough({"judged": j})}, indent=2, default=str))

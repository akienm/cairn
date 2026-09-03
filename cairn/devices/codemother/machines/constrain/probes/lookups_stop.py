"""PROBE — is the floor discovering the instruments, or discovering nothing?

Berth for the WATCHME that ticket
``constrain-discovers-and-runs-the-instruments-that-will-judge-the-build`` carries (object
``the-lookups-actually-stop``). Berthed here, beside the machine, because that is WHAT IT
WATCHES; the ticket it was compiled from lives in CairnCommons and this probe deliberately
does not follow it there.

THE FAILURE THIS WATCHES, and it is the one the code cannot see about itself. A floor that
discovers nothing and a floor that had little to find emit the SAME packet — zero checks,
no error, no unknown, every tooth green. The teeth beside this probe prove that what IS
reported was run and is honest; not one of them can tell whether anything was reported at
all on a real request, because a fixture with a planted proof always has something to find.
Only the corpus separates the two, and only over enough berths to have a median.

WHAT IS MEASURED AND WHAT IS NOT — stated because the gap is the whole honesty of this
watch. Akien's measure is that the LOOKUPS STOP: a build that reads the packet instead of
reaching for the proofs and the gates by hand. Nothing in this system counts a build's tool
calls yet (ticket ``the-builds-tool-calls-are-evidence-about-the-chart``), so the observable
here is CARRIAGE — the checks the floor discovered, surviving into the berthed packet. That
is a NECESSARY condition and not the sufficient one: checks that never reach the packet
cannot possibly have replaced a lookup, so a corpus of empty packets falsifies the node
outright, while a corpus of full ones leaves the builder's behaviour still unmeasured. This
probe fires on the first and is silent about the second, and the silence is declared rather
than discovered later.

THE POPULATION IS DERIVED FROM THE CROSSING, NEVER FROM A DATE SOMEONE TYPED. The cutoff is
the moment this machine's own ``history.json`` records the checks half arriving — the
crossing IS the event, so the number cannot be stale and no one has to remember to move it
(a hand-set constant in a gate is a learned value stranded in a human's head). Before that
crossing lands the population is EMPTY and the watch is not cleared, which is Law 9 read
correctly: green is earned, and a watch that reads green before the thing it watches has
had a chance to happen is measuring the absence of evidence.

THE RED TALLY IS AN EXISTENCE CLAIM AND IT IS WHY 'the packets got bigger' DOES NOT CLEAR
THIS. A report that has only ever said green is indistinguishable from a report that cannot
say anything else — the exact constant this component shipped once already and caught. So
clearing requires at least one check reported RED somewhere in the post-door corpus.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that
re-opens a node whose intention did not work is the OWNER's act (Law 6). A fire means check
the REF GROUNDING first — a floor whose refs reach no component discovers no checks, and
that is constrain's own prior defect resurfacing rather than this build failing, which is
why ``barren_refs`` rides the carry.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import median

from cairn.tools.base.probe import Probe, owning_ticket

# Instance-space, resolved per call and never captured at import — a probe that froze the
# path would keep reading a root the system had already left.
_BERTH_ENV = "CAIRN_CHART_PACKETS"
_BERTH_DEFAULT = Path.home() / ".cairn/devices/chart/0/packets"

_HISTORY = Path(__file__).resolve().parent.parent / "history.json"
_TICKET_ID = "constrain-discovers-and-runs-the-instruments-that-will-judge-the-build"
_TICKET = owning_ticket(_TICKET_ID)

# The spec's numbers, and each is the corpus's rather than a preference. TEN because a
# median over fewer berths moves with a single voyage. TWO because the smallest real build
# in this corpus touches one component with a ``proofs/`` peer and crosses one gate — a
# floor that cannot find those two on a median request found nothing.
_ENOUGH = 10
_BAR = 2


def _cutoff() -> str | None:
    """The berth stamp at which the checks half became possible, read off this machine's own
    crossing record. ``None`` until the crossing lands — and None means an EMPTY population,
    never an unfiltered one: a probe that fell back to judging the whole corpus would read
    its own pre-build history as the failure it watches for."""
    try:
        records = json.loads(_HISTORY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    stamps = [r.get("at") for r in records
              if isinstance(r, dict)
              and r.get("ticket") == _TICKET_ID
              and r.get("to") == "PROVED"
              and r.get("direction") == "forward"
              and isinstance(r.get("at"), str)]
    if not stamps:
        return None
    # '2026-08-14T17:12:57' -> '20260814T171257', the shape a berth filename carries.
    return min(stamps).replace("-", "").replace(":", "")


def _refd_components(packet: dict) -> set:
    """The component directories this packet's chain ref'd, read from the orient berth it
    points at. Used only to tell a barren ref from a barren corpus — the two look identical
    in the packet and need different fixes."""
    ref = packet.get("intent_ref")
    if not isinstance(ref, str):
        return set()
    try:
        orient = json.loads(Path(ref).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return set()
    out = set()
    for r in orient.get("refs") or []:
        if isinstance(r, str):
            out.add(r)
    return out


def survey_the_berths() -> dict:
    """One pass over the post-door corpus: how many packets, how many checks each carries,
    which instruments have ever been discovered, the green/red tally, and the refs that
    yielded nothing.

    A berth this probe cannot read is skipped rather than counted in either direction — the
    counts are a claim (Law 3), and a claim resting on a parse failure is worse than a
    smaller n.
    """
    berths = Path(os.environ.get(_BERTH_ENV) or _BERTH_DEFAULT)
    cutoff = _cutoff()
    per_packet: list[int] = []
    instruments: set = set()
    verdicts: dict = {}
    barren: list = []
    empty_named: list = []

    for path in sorted(berths.glob("constrain-*.json")) if (cutoff and berths.is_dir()) else []:
        stamp = path.name.split("-")[1] if path.name.count("-") >= 2 else ""
        if stamp < cutoff:
            continue
        try:
            packet = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(packet, dict):
            continue
        checks = [c for c in (packet.get("constraints") or [])
                  if isinstance(c, dict) and c.get("kind") == "check"]
        per_packet.append(len(checks))
        for c in checks:
            if isinstance(c.get("source"), str):
                instruments.add(c["source"])
            v = c.get("verdict")
            verdicts[v] = verdicts.get(v, 0) + 1
        if not checks:
            empty_named.append(path.name)
            # A ref that yields no instrument is either wrong or gone, and both are
            # findings — the consumer is told to check this before anything else.
            barren.extend(sorted(_refd_components(packet)))

    return {
        "cutoff": cutoff,
        "post_door_berths": len(per_packet),
        "checks_per_packet_median": median(per_packet) if per_packet else None,
        "checks_per_packet_min": min(per_packet) if per_packet else None,
        "distinct_instruments": len(instruments),
        "verdict_tally": verdicts,
        "reds_ever": verdicts.get("red", 0),
        "empty_berths": empty_named[:10],
        "empty_count": len(empty_named),
        "barren_refs": sorted(set(barren))[:20],
    }


def _trigger(now, context: dict) -> bool:
    """TRUE when enough packets have berthed under the shipped floor AND the median number
    of checks they carry is below the bar. Both clauses carry weight: firing on a small
    corpus pokes the owner about noise, and firing while packets are carrying checks pokes
    about a build that is working."""
    s = context.get("berths") or survey_the_berths()
    if s["post_door_berths"] < _ENOUGH:
        return False
    return (s["checks_per_packet_median"] or 0) < _BAR


def _enough(context: dict) -> bool:
    """CLEARED when the corpus is big enough to judge, the median holds at or above the bar,
    AND at least one check has been reported RED. The third clause is the existence claim —
    without it a floor hard-wired to say green would clear this watch by never disagreeing
    with anything."""
    s = context.get("berths") or survey_the_berths()
    return (s["post_door_berths"] >= _ENOUGH
            and (s["checks_per_packet_median"] or 0) >= _BAR
            and s["reds_ever"] >= 1)


def _carry(context: dict) -> dict:
    """The datum that rides back — every count needed to resolve it on the first pass, and a
    POINTER to the ticket rather than a copy of it (Law 6 — the ticket is the commons')."""
    s = context.get("berths") or survey_the_berths()
    return {
        "finding": "the floor that discovers and runs the instruments is berthing packets "
                   "that carry almost no checks — which is either a discovery convention "
                   "that stopped matching the house, refs that ground nowhere, or a corpus "
                   "with genuinely few checks near the work",
        "counts": s,
        "threshold": {"checks_per_packet_bar": _BAR, "berths_before_judging": _ENOUGH,
                      "derived_from": "the ticket's spec: the smallest real build in this "
                                      "corpus touches one component with a proofs/ peer "
                                      "and crosses one gate"},
        "ticket": _TICKET,
        "against_falsifier": "the node's DONE requires a packet berthing with checks the "
                             "floor DISCOVERED and RAN; a corpus whose median is below the "
                             "bar is that requirement failing in the field rather than at "
                             "the gate",
        "suggests": "read 'barren_refs' FIRST. A floor whose refs reach no component "
                    "discovers no checks, and that is constrain's own prior ref-grounding "
                    "defect resurfacing rather than this build failing — a different fix in "
                    "a different function. If the refs ground fine, compare "
                    "'distinct_instruments' against what 'cairn test' finds under the same "
                    "directories: agreement there means the corpus is genuinely thin, "
                    "disagreement means the discovery convention has drifted from the "
                    "tester's.",
        "not_measured": "whether the BUILDER's lookups actually stopped. Carriage is "
                        "necessary and not sufficient; the tool-call observer that would "
                        "close the gap is ticket "
                        "'the-builds-tool-calls-are-evidence-about-the-chart'.",
    }


# THE HORIZON, in pulses because the shim counts pulses. Nothing pulses this shim yet (the
# wall-clock backing is a filed edge in cairn/devices/cairn/machines/ground_loop/loop.py, not built), so the
# loudness rides the read-side door (``BaseShim.overdue()``) alone. Honest as a placeholder,
# dishonest as a measurement, and MUST be re-tuned when the beat is real. Longer than
# crowding_out's because this watch needs ten VOYAGES, not ten reads.
_HORIZON = 2000

PROBE = Probe(
    why="is the floor discovering the instruments, or discovering nothing? — a floor that "
        "finds nothing and a floor with nothing to find emit the same empty packet, and no "
        "tooth beside this probe can tell them apart because a fixture always has something "
        "planted in it. Cleared when ten post-door packets carry a median of at least two "
        "checks AND at least one of those checks has been reported RED — the existence "
        "claim a report that only ever says green cannot make about itself.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

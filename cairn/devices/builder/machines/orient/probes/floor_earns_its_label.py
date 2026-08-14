"""PROBE — does any field ever actually EARN the ``floor`` label?

Berth for the WATCHME that ticket ``orient-floor-authors-and-provenance-is-measured``
carries (object ``orient-provenance-is-derived-not-declared``). Berthed here, beside the
machine, because that is WHAT IT WATCHES; the ticket it was compiled from lives in
CairnCommons and this probe deliberately does not follow it there.

THE EFFICACY QUESTION, and why it is this one rather than the obvious one. On 2026-08-14
provenance for ``refs``/``domain``/``unknowns`` stopped being the sender's to write: the
door re-runs the floor over the packet's own ``request`` and a field claims ``floor``
only if that answer can be REPRODUCED. Proofs already show the door refuses a
misdeclaration and derives the label — that half is settled and a standing watch on it
would be the re-derivation Law 1 refuses.

What proofs cannot show is whether the change did anything. The measured starting point
is stark: over 45 berthed packets, 44 declared ``refs: floor`` and 18 declared
``domain: floor``, and re-running the floor reproduced NOT ONE of them — a real
code-produced fraction of 0.00 against a dial reading 0.40. If the ceiling never carries
the floor's answer through, the new door writes ``claude`` on every packet forever, the
dial honestly reads 0.00, and the only thing the build accomplished was to stop lying.
That is a better place to stand than the old one and it is not the point: the point was
to make the floor's answer REUSABLE, which is a claim about live packets and nothing else
can answer it.

WHY NOT THE DISAGREEMENT CHECK, which is the one this probe was first drafted as. The
tempting instrument is "re-derive every berth's provenance and red on any berth whose
label disagrees" — it aims straight at the ticket's drift (a later change that lets a
caller pass provenance through again). It is unsound over time, and the unsoundness is
the snapshot trap: re-derivation reads TODAY's tree, so a packet berthed when
``cairn/tools/chain/grammar.py`` existed and re-derived after it moved disagrees for a
reason that is about the world moving, not about the door. The disagreement table still
rides in ``carry`` as diagnostic data, with that caveat attached — a reader deciding what
to do wants it — but nothing FIRES on it.

THE POPULATION IS POST-BUILD BERTHS ONLY, by filename stamp. The 45 that predate the door
declared their own labels because that was the legal shape when they were written; Law 7
says a record of truth is not rewritten by a later rule, and counting them here would
retro-red an honest corpus and guarantee the watch fires forever.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that
re-opens a node whose intention did not work is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket
from cairn.devices.builder.machines.orient.orient import (FLOOR_AUTHORED,
                                                          measured_provenance)

# Instance-space, resolved per call and never captured at import — a probe that froze the
# path would keep reading a root the system had already left.
_BERTH_ENV = "CAIRN_CHART_PACKETS"
_BERTH_DEFAULT = Path.home() / ".cairn/devices/chart/0/packets"

# The door landed on 2026-08-14. Berths are named ``orient-<YYYYmmddTHHMMSS>-<digest>``,
# so the stamp IS the population filter: everything at or after this is a packet written
# under the rule, everything before it is a packet written under the old one.
_DOOR_LANDED = "20260814T000000"

# The sample size below which "no field has earned floor" says nothing. The chart chain
# fires once per voyage and the corpus grew ~45 packets in three weeks, so fifteen
# post-build berths is roughly a working week of real voyages — enough that a run of
# ceiling-authored packets stops being plausible bad luck.
_ENOUGH = 15

_TICKET = owning_ticket("orient-floor-authors-and-provenance-is-measured")


def survey_the_berths() -> dict:
    """Over post-build orient berths: how many exist, how many carry a ``request`` (the
    evidence without which nothing CAN earn ``floor``), how many earned ``floor`` for at
    least one field, and the per-field tally.

    A berth this probe cannot read is skipped rather than counted in either direction —
    the counts are a claim (Law 3), and a claim resting on a parse failure is worse than
    a smaller n.
    """
    berths = Path(os.environ.get(_BERTH_ENV) or _BERTH_DEFAULT)
    total = with_request = earned_any = 0
    per_field = {f: 0 for f in FLOOR_AUTHORED}
    disagreements = []

    for path in sorted(berths.glob("orient-*.json")) if berths.is_dir() else []:
        stamp = path.name.split("-")[1] if path.name.count("-") >= 2 else ""
        if stamp < _DOOR_LANDED:
            continue
        try:
            packet = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(packet, dict):
            continue
        total += 1
        if isinstance(packet.get("request"), str) and packet["request"].strip():
            with_request += 1
        prov = packet.get("provenance") or {}
        if any(prov.get(f) == "floor" for f in FLOOR_AUTHORED):
            earned_any += 1
        for f in FLOOR_AUTHORED:
            if prov.get(f) == "floor":
                per_field[f] += 1
        # Diagnostic only, and never a trigger — see the module docstring on why
        # re-derivation against today's tree cannot carry a verdict.
        try:
            today = measured_provenance(packet)
        except Exception:  # a floor refusal on a stale request is not this probe's finding
            continue
        off = {f: [prov.get(f), today.get(f)] for f in FLOOR_AUTHORED
               if f in prov and prov[f] != today.get(f)}
        if off:
            disagreements.append({"berth": path.name, "declared_vs_today": off})

    return {"post_build_berths": total, "carrying_request": with_request,
            "earned_floor": earned_any, "per_field": per_field,
            "floor_fraction": round(earned_any / total, 2) if total else 0.0,
            "disagreements_today": disagreements[:10],
            "disagreement_count": len(disagreements)}


def _trigger(now, context: dict) -> bool:
    """TRUE when enough packets have been written under the new door and not one of them
    has earned ``floor`` for any field. Both clauses are load-bearing: firing on a small
    corpus pokes the owner about noise, and firing while fields ARE earning the label
    pokes about a build that is working."""
    s = context.get("berths") or survey_the_berths()
    return s["post_build_berths"] >= _ENOUGH and s["earned_floor"] == 0


def _enough(context: dict) -> bool:
    """CLEARED once the corpus is big enough to judge AND at least one field has earned
    ``floor`` — the floor's answer reached a packet unchanged, which is the whole claim.

    An EXISTENCE claim, so one witness settles it; the sample floor is here because the
    other half of the clear ("we have looked at enough packets to have asked") is a claim
    about a population and n=1 cannot support it. Clearing on the first earned label with
    no floor would retire the watch before it could bite, which is the sibling probe's
    measured bug and not one to repeat."""
    s = context.get("berths") or survey_the_berths()
    return s["post_build_berths"] >= _ENOUGH and s["earned_floor"] >= 1


def _carry(context: dict) -> dict:
    """The datum that rides back — the full counts in ONE report (a failure report
    delivers everything needed to resolve it on the first pass), and a POINTER to the
    ticket rather than a copy of it (Law 6 — the ticket is the commons')."""
    s = context.get("berths") or survey_the_berths()
    return {"finding": "no orient packet has earned the 'floor' provenance label since "
                       "the door started measuring it",
            "counts": s,
            "ticket": _TICKET,
            "against_falsifier": "the build replaced a self-reported 0.40 with a measured "
                                 "0.00 and stopped there — the label became honest and "
                                 "the floor's answer is still not reused, which was the "
                                 "point",
            "suggests": "read skills/chart/SKILL.md stage 1 first: the ceiling is "
                        "instructed to carry the floor's three fields through UNCHANGED, "
                        "so a zero here usually means the instruction is being read as a "
                        "suggestion, or floor_packet is returning None for the fields "
                        "(check 'carrying_request' — a packet with no request cannot "
                        "earn anything, and that is the cheaper failure to find)"}


# THE HORIZON, in pulses because the shim counts pulses. Nothing pulses this shim yet (the
# wall-clock backing is a filed edge in cairn/devices/ground_loop/loop.py, not built), so
# the loudness rides the read-side door (`BaseShim.overdue()`) alone. Honest as a
# placeholder, dishonest as a measurement, and MUST be re-tuned when the beat is real.
_HORIZON = 1000

PROBE = Probe(
    why="does any field ever actually EARN the 'floor' label? — the build made the number "
        "honest (0.40 self-reported became 0.00 measured); it is only WORTH anything if "
        "the floor's answer starts reaching packets unchanged. Cleared when at least one "
        "field earns it over a corpus big enough to have asked.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

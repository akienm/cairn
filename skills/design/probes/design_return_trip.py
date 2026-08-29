"""PROBE — is the return trip from /sorted ever recorded, or does it still vanish?

Berth for the WATCHME that ticket ``the-return-trip-is-countable`` carries. Berthed
here, beside ``skills/design/``, because that is WHAT IT WATCHES; the ticket it was
compiled from lives in CairnCommons and this probe deliberately does not follow it
there (the rule in ``cairn/tools/base/probe.py``: a probe berths with its subject).

THE EFFICACY QUESTION. /design's build claim is one sentence in its charter: "this door
is where that arrival becomes data" — the arrival being a node routed back from /sorted
on a completeness red, recorded as ``entering_from: sorted:<berth>``. That field is the
denominator /intent's charter names as missing ("which of /intent's questions are
failing to catch things"). The door can RECORD a return; only a live one shows the
return actually RIDES the door instead of being swallowed by conversation — which is
the exact lived symptom the charter opens with. Until one arrival is witnessed, the
claim is unfalsified, not proven.

THE CLEAR IS AN EXISTENCE CLAIM, AND HERE THAT IS HONEST — the deliberate asymmetry
against the sibling probe one directory over. /idea's watch had its existence question
settled by a live fire the day this spec was written, so its clear had to be a
population claim. This one's existence has NEVER been witnessed: zero ``sorted:``
arrivals stand in the berths (the door's only live rows are this build's own two first
passes). One witnessed arrival settles "the return trip is countable" completely — the
same shape as ``intent_door_refusals``' clear, where one witnessed refusal settles an
existence. The RATE of return trips per node is the downstream consumer's question
(the /intent-questions dial), not this watch's.

TRIGGER AND CLEAR ARE MUTUALLY EXCLUSIVE BY CONSTRUCTION: fire needs returns == 0,
clear needs returns >= 1 — the clear-before-fire bug the roster's first probe recorded
against itself cannot be rebuilt here by drift, only by an edit.

THE DENOMINATOR IS NODES, NOT FIRINGS. Five openings on one berth are one hungry node,
not five worked sessions; a firing count would let a single thrashing node age the
corpus into the trigger by itself.

THE ZERO IS KEPT HONEST BY THE NEIGHBOUR'S LEDGER. A zero here has three readings — the
corpus is young; /sorted's completeness gate never reds; returns happen but bypass the
door — and the survey reads /sorted's own berths for ``disposition: back-to-design`` to
split them: dispositions with no matching arrivals is the bypass reading, measured
rather than guessed. It rides in the CARRY, not the trigger: a red at /sorted today may
legitimately re-open at /design next week, and a lag tolerance is a number nobody has
measured yet (a hand-set one would be a guess wearing a gate's clothes).

AUTHORITY: none, by construction. This probe deposits and pokes; whatever the zero
turns out to mean, acting on it is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

# Env first, default second, resolved per call — the roster's rule: a probe that froze
# the path at import time would keep reading a root the system had already left.
_BERTH_ENV = "CAIRN_SKILL_BERTHS"
_BERTH_DEFAULT = Path.home() / ".cairn/devices/skill_block/0/berths"

# The sample below which "no return trip was ever recorded" says nothing. /design fires
# once per design SESSION, not once per turn, so twelve distinct nodes through the door
# is a real season of design work — enough that zero recorded returns is a pattern about
# the system, not a lull. A HAND-SET PRIOR, named as such on the ticket (learns-its-
# gates): an IOU against the door's real cadence once it has one.
_FLOOR = 12


def survey_the_arrivals() -> dict:
    """Count, over /design's live berths: openings, distinct nodes (by the berth each
    opening claims to work), and recorded returns (``entering_from: sorted:<berth>``) —
    plus, from /sorted's own berths, how many returns its dispositions PROMISED
    (``back-to-design``). Reads instance-space files only — no device, no bus, no
    network — so the probe stays cheap enough to sit on a pulse.

    An unreadable berth is skipped rather than counted: the counts a probe reports are
    a claim (Law 3), and a claim resting on a parse failure is worse than a smaller n.
    """
    root = Path(os.environ.get(_BERTH_ENV) or _BERTH_DEFAULT)

    openings = returns = 0
    nodes: set[str] = set()
    for p in sorted((root / "design").glob("*.json")) if (root / "design").is_dir() else []:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        answers = rec.get("answers") or {}
        openings += 1
        nodes.add(str(answers.get("intent_berth", "")).strip())
        if str(answers.get("entering_from", "")).strip().lower().startswith("sorted:"):
            returns += 1

    promised = 0
    for p in sorted((root / "sorted").glob("*.json")) if (root / "sorted").is_dir() else []:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        d = str((rec.get("answers") or {}).get("disposition", "")).strip()
        if d in ("back-to-design", "not-ready"):
            promised += 1

    return {"openings": openings, "nodes": len(nodes), "returns": returns,
            "promised_returns": promised}


def _trigger(now, context: dict) -> bool:
    """TRUE when there have been enough distinct nodes to judge AND no return trip has
    ever been recorded. Both clauses are load-bearing: firing on a small corpus pokes
    the owner about noise, and firing while a return exists pokes about a working
    field."""
    s = context.get("arrivals") or survey_the_arrivals()
    return s["nodes"] >= _FLOOR and s["returns"] == 0


def _enough(context: dict) -> bool:
    """CLEARED once ONE return trip is witnessed live: a design opening whose
    ``entering_from`` names a sorted berth. One arrival settles the existence claim —
    the return trip is countable, the route /sorted's charter points back here actually
    lands here — completely. The rate question that opens up next belongs to the
    consumer of the count, carried deliberately, not to this watch silently staying
    up (Law 1)."""
    s = context.get("arrivals") or survey_the_arrivals()
    return s["returns"] >= 1


def _carry(context: dict) -> dict:
    """The datum that rides back: the counts against the ticket's own falsifier, with
    the promised-vs-arrived split that turns the zero's three readings into a measured
    fork, and a POINTER to the ticket rather than a copy of it (Law 6)."""
    s = context.get("arrivals") or survey_the_arrivals()
    return {"finding": "no return trip from /sorted has ever been recorded at /design",
            "counts": s,
            "ticket": _TICKET,
            "against_falsifier": "the door's build claim — 'this door is where that "
                                 "arrival becomes data' — is standing unfalsified: the "
                                 "denominator for 'which of /intent's questions let "
                                 "things through' still has no rows",
            "suggests": "read counts.promised_returns first: back-to-design dispositions "
                        "at /sorted with zero arrivals here means returns are being "
                        "SWALLOWED between the doors (the conversation is still eating "
                        "the return trip — the door's own lived symptom); zero promised "
                        "AND zero arrived means /sorted's completeness gate has never "
                        "redded, which is the neighbouring vacuity question, one door "
                        "up. Both are the owner's call, not the probe's."}


_TICKET = owning_ticket("the-return-trip-is-countable")

# THE HORIZON — the roster's shared tracked debt, restated not re-derived: the unit is
# PULSES, nothing pulses this shim yet (cairn/devices/cairn/machines/ground_loop/loop.py's filed edge), so the
# loudness rides ``BaseShim.overdue()`` alone. 1000 is honest as a placeholder and
# dishonest as a measurement, and MUST be re-tuned when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="is the return trip from /sorted ever recorded, or does it still vanish into "
        "conversation? — the door exists to make that arrival data, and until one "
        "arrival is witnessed the claim is unfalsified. Fires when a season of design "
        "work shows zero returns; cleared by the first witnessed arrival.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

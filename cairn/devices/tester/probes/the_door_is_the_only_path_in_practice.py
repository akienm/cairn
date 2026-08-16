"""PROBE — is ``persist_validation`` the only path into a validation trail IN PRACTICE?

Berth for the WATCHME that ticket ``standing-gates-the-newest-link-and-run-proof-names-its-sink``
carries. Berthed here, beside the tester, because that is WHAT IT WATCHES: the door it asks
about is ``cairn/devices/tester/validation_store.persist_validation``, and the hand that would
route around it is a caller of ``TesterDevice.run_proof``. The ticket it was compiled from
lives in CairnCommons and this probe deliberately does not follow it there.

THE EFFICACY QUESTION, AND WHY IT IS THIS ONE AND NOT "DOES THE DOOR WORK".

The door already worked. It was sealed on 2026-08-05 with three physics layers (ticket
``validation-store-door-is-the-only-path``) — a 0444 mode bit, a hash chain, and a build-time
corpus scan for second writers — and its proofs went green and stayed green. Then, on
2026-08-07 and 2026-08-08, two and three days later, two voyages wrote six validation trails
around it anyway, and seven entries carry no ``trail_link`` to this day. Every layer held.
The corpus routed around them, because nothing in ``cairn test`` or ``run_proof`` could land
a seal at all, so a builder who needed one reached past the physics rather than through it.

So the question a tooth cannot ask is the one worth a probe: not whether the door refuses a
bypass — proofs settle that in a fixture — but whether, ACROSS REAL VOYAGES, anybody still
needs to go around. That is a question about live traffic over time, and the only honest
instrument for it is the trails themselves.

WHAT MAKES IT ANSWERABLE NOW AND NOT BEFORE: ``run_proof`` gained a required sink and
``cairn test`` gained ``--seal``, so the affordance exists. If entries STILL arrive unlinked
after that, the diagnosis is not "the door needs a fourth lock" — it is that some real need
is still unserved, and the fix is another affordance, not another refusal.

THE POST-FIX CUTOFF IS THE WHOLE MEASUREMENT. Seven unlinked entries sit in the corpus
today, and they are history: they are exactly the evidence that bore this ticket, and they
must not be repaired, adopted or deleted (Law 7 — a record of truth is not edited to look
consistent). Counting them would make this probe fire forever on a question already
answered. Counting only what lands AFTER the fix is what makes the answer falsifiable.

WHAT THIS PROBE PARTLY WATCHES IS THE VOYAGE THAT ARMED IT, and that is said out loud
rather than glossed: the two seals this build landed through ``--seal`` are among the first
post-fix entries it will count. They are honest evidence — they went through the door, by
the route the fix built, which is precisely the behaviour under test — but they are the
author's own participation, and at n=2 out of 20 they cannot carry the answer alone. The
floor is what keeps that true.

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

# The date this fix landed. Entries dated at or after it are the population; everything
# below is the history that bore the ticket, and it is read past, never counted and never
# touched. An ISO-8601 prefix compares correctly as a string against the record's `date`,
# which is `datetime.isoformat(timespec="seconds")`.
_FIX_LANDED = "2026-08-16"

# The sample size below which the question cannot be answered at all. Two or three post-fix
# entries all carrying links is a plausible run; twenty is a pattern. It is a round number
# honestly chosen and not derived, which is the same debt does_optional_mean_never_carried
# carries at its own floor — re-tune it when the trail-growth rate is a measured number
# rather than a guess.
_ENOUGH = 20

# The node this probe was compiled from. A bare id because it is an IDENTITY; `owning_ticket`
# builds the address that rides in the payload (ruling 2026-08-05, "the file path is the link").
_OWNING_TICKET = "standing-gates-the-newest-link-and-run-proof-names-its-sink"

# The store's own name for the link, imported rather than spelled, so a rename cannot leave
# this probe quietly measuring a key nothing writes any more.
from cairn.devices.tester.validation_store import TRAIL_LINK  # noqa: E402


def survey_the_corpus() -> dict:
    """Count, over every validation trail in class-space: how many entries landed after the
    fix, and how many of those carry no ``trail_link``.

    THE UNLINKED ONES ARE NAMED, NOT JUST COUNTED, and their `caller` rides along — because
    the finding this probe would deliver is useless without the answer to "who wrote it".
    That is the question the eight-day silence could not answer either: the trails recorded
    the breach correctly and nobody read them, so nobody knew which hand to look at.

    Reads files only. A trail this probe cannot parse is skipped rather than counted, and
    skipping is reported: a probe that quietly treats an unreadable file as clean is the
    vacuous green its own subject matter is about.
    """
    post_fix = 0
    unlinked: list[dict] = []
    unreadable: list[str] = []
    for trail_path in sorted(_CLASS_SPACE.glob("**/validations/*.json")):
        if "__pycache__" in str(trail_path):
            continue
        try:
            trail = json.loads(trail_path.read_text(encoding="utf-8"))
            if not isinstance(trail, list):
                raise ValueError("a trail is a list of records")
        except Exception as err:  # noqa: BLE001
            unreadable.append(f"{os.path.relpath(trail_path, _CLASS_SPACE)}: {err}")
            continue
        for index, entry in enumerate(trail):
            if not isinstance(entry, dict) or str(entry.get("date", "")) < _FIX_LANDED:
                continue
            post_fix += 1
            evidence = entry.get("evidence")
            if not isinstance(evidence, dict) or TRAIL_LINK not in evidence:
                unlinked.append({
                    "trail": os.path.relpath(trail_path, _CLASS_SPACE),
                    "entry": index,
                    "date": entry.get("date"),
                    "caller": entry.get("caller"),
                })
    return {"post_fix": post_fix, "unlinked": unlinked,
            "unlinked_count": len(unlinked), "unreadable": unreadable}


def _trigger(now, context: dict) -> bool:
    """TRUE when enough has landed since the fix to judge AND at least one entry still
    arrived around the door. Both clauses carry weight: firing on a thin corpus pokes the
    owner about noise, and firing on zero unlinked entries pokes about a mechanism that is
    working."""
    s = context.get("corpus") or survey_the_corpus()
    return s["post_fix"] >= _ENOUGH and s["unlinked_count"] > 0


def _enough(context: dict) -> bool:
    """CLEARED once enough has landed since the fix to judge AND every one of those entries
    came through the door. At that moment the question is answered — the affordance is being
    used and nobody is routing around it — and a standing watch on a settled question is the
    re-derivation Law 1 refuses.

    THE FLOOR SITS ON THIS CLAUSE TOO, and that is not symmetry for its own sake. Without it
    this clears at n=0: an empty post-fix corpus has no unlinked entries in it, so the watch
    would retire on its very first pulse, before a single seal had been written — the exact
    asymmetry that made ``does_optional_mean_never_carried`` clear at n=1 against a corpus
    of one ticket, which was itself. A watch that can clear before it can fire is not a
    watch.
    """
    s = context.get("corpus") or survey_the_corpus()
    return s["post_fix"] >= _ENOUGH and s["unlinked_count"] == 0


def _carry(context: dict) -> dict:
    """The datum that rides back: the counts, the offending addresses WITH the caller that
    wrote each, and a pointer to the ticket the finding is against (Law 6 — the ticket is
    the commons', not ours)."""
    s = context.get("corpus") or survey_the_corpus()
    return {"finding": f"{s['unlinked_count']} validation entr"
                       f"{'y' if s['unlinked_count'] == 1 else 'ies'} landed after the fix "
                       f"without coming through persist_validation",
            "post_fix_entries": s["post_fix"],
            "unlinked": s["unlinked"],
            "unreadable_trails": s["unreadable"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the door was made reachable (run_proof's required sink, "
                                 "`cairn test --seal`) and a caller went around it anyway — "
                                 "so reachability was not what was missing",
            "suggests": "read the `caller` on each unlinked entry and ask what it needed "
                        "that the sink does not offer. The 2026-08-05 fix answered a bypass "
                        "with a fourth lock and the corpus routed around it within two days; "
                        "the finding to look for here is an UNSERVED NEED, not a missing "
                        "refusal"}


# THE HORIZON. Same unit and same honest placeholder as the sibling probe at
# cairn/tools/base/probes/does_optional_mean_never_carried.py: the unit is PULSES because the
# shim counts pulses, the wall-clock beat that would drive them is a filed edge rather than a
# built one, so nothing pulses this shim today and the loudness rides the read-side door
# (`BaseShim.overdue()`) alone. 1000 is "clearly a long standing" against any beat rate we
# would plausibly pick. It is honest as a placeholder and dishonest as a measurement, and it
# must be re-tuned when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="the door was sealed with three physics layers and the corpus wrote around it "
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

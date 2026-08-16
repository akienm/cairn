"""PROBE — does the one-record collapse HOLD once real voyages start sealing against it?

Berth for the WATCHME that ticket ``a-validation-is-one-current-record-not-a-trail`` carries.
Berthed here, beside the tester, because that is WHAT IT WATCHES: the door it asks about is
``cairn/devices/tester/validation_store.persist_validation``, and the hand that would break the
invariant is a caller of ``TesterDevice.run_proof`` or ``quorum.seal``. The ticket it was
compiled from lives in CairnCommons and this probe deliberately does not follow it there.

THE EFFICACY QUESTION, AND WHY A TOOTH CANNOT ASK IT.

The proofs settle that ``persist_validation`` writes exactly one record — in a fixture, on
demand, today. What they cannot settle is whether the corpus AGREES to live that way. The
store has been here before and lost: the door was sealed on 2026-08-05 with three physics
layers and its proofs went green, and within two days two voyages wrote six trails around it,
because no reachable route could land a seal and a builder who needed one reached past the
physics. Every layer held; the corpus routed around them. That is a fact about live traffic
over time, and the only honest instrument for it is the records themselves.

WHAT MAKES THE INVARIANT WORTH WATCHING RATHER THAN ASSUMING: the collapse took something
away. Anyone who wanted the superseded records back — to compare two runs, to read a flap —
now has to go to git for them, and the failure mode is not an argument but a hand that quietly
writes a second record instead. That hand leaves a mark this probe can see.

THE INSTRUMENT IS STRICTLY HARDER TO FAKE THAN THE ONE IT REPLACED. The retired hash chain
could be satisfied by anyone who imported ``_link_for`` and computed a link (MEASURED
2026-08-16 — the forger who bothered produced a trail that verified and stood green). A
one-element list cannot be satisfied that way at all: producing a two-record file REQUIRES
doing the exact thing being watched for. There is no costume.

THE POST-COLLAPSE CUTOFF IS THE WHOLE MEASUREMENT. The 193 records dropped on 2026-08-16 are
history and live in git; counting anything that predates the collapse would make this probe
fire forever on a question already answered. Counting only what stands after it is what makes
the answer falsifiable.

WHAT THIS PROBE PARTLY WATCHES IS THE VOYAGE THAT ARMED IT, said out loud rather than glossed:
the seals this build lands are among the first post-collapse records it will count. They are
honest evidence — they went through the door — but they are the author's own participation,
and at n=2 out of 20 they cannot carry the answer alone. The floor is what keeps that true.

ONE INSTRUMENT, AND NOW ONE PROBE. ``the_door_is_the_only_path_in_practice`` — armed one
voyage earlier for ticket ``standing-gates-the-newest-link-and-run-proof-names-its-sink`` —
asked whether anybody still NEEDS to go around the door, and counted entries carrying no
``trail_link``. The chain retired with the append-only-ness it protected, so that key is
written by nothing: left as it was, it would have counted a corpus-wide zero forever and fired
on a finding false by construction — a check whose reading is decided by its own condition
being satisfied rather than by the world. Its retirement was bound into this ticket's cast
rather than discovered in flight.

The first fix was to re-instrument it onto THIS survey and keep both files. That was measured
wrong during the build: both probes then computed the same number, cleared on the same
condition, and would have delivered the same finding twice — the REPEATS class ``probescan``
already counts as a defect. So the earlier probe is gone and its question is carried HERE,
by this one observation: a validations file holding more than one record IS a write that did
not come through the door, which is the older probe's question stated in the newer probe's
terms. Retiring it is a write to the tester's own probes, which the charter's ``gated_by``
admits (Law 6) — recorded here rather than left to be inferred from an absent file.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that re-opens a
node whose intention did not work is the OWNER's act (Law 6).

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
_COLLAPSE_LANDED = "2026-08-16"

# The sample size below which the question cannot be answered at all. Two or three post-
# collapse records all landing singly is a plausible run; twenty is a pattern. It is a round
# number honestly chosen and not derived, which is the same debt does_optional_mean_never_carried
# carries at its own floor — re-tune it when the seal rate is a measured number rather than a
# guess.
_ENOUGH = 20

# The node this probe was compiled from. A bare id because it is an IDENTITY; `owning_ticket`
# builds the address that rides in the payload (ruling 2026-08-05, "the file path is the link").
_OWNING_TICKET = "a-validation-is-one-current-record-not-a-trail"


def survey_the_corpus() -> dict:
    """Count, over every validations file in class-space: how many records stand at or after
    the collapse, and how many files hold more than one — the shape the door cannot write.

    THE OFFENDING FILES ARE NAMED, NOT JUST COUNTED, and the `caller` of every record in them
    rides along — because the finding this probe would deliver is useless without the answer
    to "who wrote it". That is the question the last breach could not answer for eight days:
    the records held it correctly and nobody read them, so nobody knew which hand to look at.

    Reads files only. A file this probe cannot parse is skipped rather than counted, and
    skipping is reported: a probe that quietly treats an unreadable file as clean is the
    vacuous green its own subject matter is about.
    """
    post_collapse = 0
    multi: list[dict] = []
    unreadable: list[str] = []
    for path in sorted(_CLASS_SPACE.glob("**/validations/*.json")):
        if "__pycache__" in str(path):
            continue
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                raise ValueError("a validations file is a list of records")
        except Exception as err:  # noqa: BLE001
            unreadable.append(f"{os.path.relpath(path, _CLASS_SPACE)}: {err}")
            continue
        current = [r for r in records
                   if isinstance(r, dict) and str(r.get("date", "")) >= _COLLAPSE_LANDED]
        if not current:
            continue
        post_collapse += len(current)
        if len(records) > 1:
            multi.append({
                "trail": os.path.relpath(path, _CLASS_SPACE),
                "records": len(records),
                "callers": [r.get("caller") if isinstance(r, dict) else None for r in records],
                "dates": [r.get("date") if isinstance(r, dict) else None for r in records],
            })
    return {"post_collapse": post_collapse, "multi": multi,
            "multi_count": len(multi), "unreadable": unreadable}


def _trigger(now, context: dict) -> bool:
    """TRUE when enough has landed since the collapse to judge AND at least one file holds
    more than one record. Both clauses carry weight: firing on a thin corpus pokes the owner
    about noise, and firing on zero offenders pokes about a mechanism that is working."""
    s = context.get("corpus") or survey_the_corpus()
    return s["post_collapse"] >= _ENOUGH and s["multi_count"] > 0


def _enough(context: dict) -> bool:
    """CLEARED once enough has landed since the collapse to judge AND every file holds exactly
    one record. At that moment the question is answered — the corpus is living the invariant —
    and a standing watch on a settled question is the re-derivation Law 1 refuses.

    THE FLOOR SITS ON THIS CLAUSE TOO, and that is not symmetry for its own sake. Without it
    this clears at n=0: an empty post-collapse corpus has no multi-record file in it, so the
    watch would retire on its very first pulse, before a single seal had landed — the exact
    asymmetry that made ``does_optional_mean_never_carried`` clear at n=1 against a corpus of
    one ticket, which was itself. A watch that can clear before it can fire is not a watch.
    """
    s = context.get("corpus") or survey_the_corpus()
    return s["post_collapse"] >= _ENOUGH and s["multi_count"] == 0


def _carry(context: dict) -> dict:
    """The datum that rides back: the counts, the offending addresses WITH every caller that
    wrote into each, and a pointer to the ticket the finding is against (Law 6 — the ticket is
    the commons', not ours)."""
    s = context.get("corpus") or survey_the_corpus()
    return {"finding": f"{s['multi_count']} validations file"
                       f"{'' if s['multi_count'] == 1 else 's'} hold more than one record "
                       f"after the collapse — a shape persist_validation cannot write",
            "post_collapse_records": s["post_collapse"],
            "multi_record_files": s["multi"],
            "unreadable_files": s["unreadable"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "clause (3): a reader was found that needed a record other "
                                 "than the current one, and somebody kept the old one by hand "
                                 "rather than reaching for git — one counterexample kills the "
                                 "premise the collapse rests on",
            "suggests": "read every `caller` in each named file and ask what it needed that "
                        "the current record does not carry. If the answer is 'compare two "
                        "runs', that is ticket the-proof-record-persists-so-runs-can-be-"
                        "compared arriving as a real need, and the fix is to build ITS "
                        "substrate — not to re-grow a trail here"}


# THE HORIZON. Same unit and same honest placeholder as the sibling probes: the unit is PULSES
# because the shim counts pulses, the wall-clock beat that would drive them is a filed edge
# rather than a built one, so nothing pulses this shim today and the loudness rides the
# read-side door (`BaseShim.overdue()`) alone. 1000 is "clearly a long standing" against any
# beat rate we would plausibly pick. It is honest as a placeholder and dishonest as a
# measurement, and it must be re-tuned when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="the collapse traded append-only-ness for one current record, and the trade only "
        "holds if nobody needs the superseded ones badly enough to keep them by hand — a "
        "question about live traffic that no fixture can answer, and the same store already "
        "lost this exact bet once, two days after its physics went green",
    trigger=_trigger,
    to="tester",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

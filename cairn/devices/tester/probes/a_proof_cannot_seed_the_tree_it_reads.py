"""PROBE — does the instance seal HOLD once the whole corpus is running through it?

Berth for the WATCHME that ticket ``a-proof-cannot-seed-the-tree-it-reads`` carries. Berthed
here, beside the tester, because that is WHAT IT WATCHES: the seal is built in
``cairn/devices/tester/isolation.py`` and applied in ``TesterDevice.run_proof``, and the hand
that would lose it is a caller of that method. The ticket it was compiled from lives in
CairnCommons and this probe deliberately does not follow it there.

THE EFFICACY QUESTION, AND WHY A TOOTH CANNOT ASK IT.

``proofs/test_instance_seal.py`` settles that the seal holds — in a fixture, on demand, today,
against a proof written to leak on purpose. What it cannot settle is whether the CORPUS keeps
running through it. That is a fact about live traffic over time, and this system has already
watched exactly this shape fail once: the validation store's door was sealed with three physics
layers, its proofs went green, and within two days six voyages wrote around it — every layer
held and the corpus routed past them. A seal is only worth what the traffic actually carries.

THE TWO WAYS IT LOSES, and the second is the one with precedent:

  (1) a run comes back with a verdict that is not SEALED. INDETERMINATE and OPEN are honest
      answers, not lies — but a corpus living on them is a corpus whose proofs are once again
      free to seed the tree they read, and the reason will be sitting right there in the
      detail string.
  (2) a run comes back carrying NO ``instance_seal`` AT ALL. That is a proof executed by some
      path that never met the seal, and it is invisible to (1) by construction — the absence
      of a key looks like nothing, which is precisely how a routed-around physics stays quiet.

WHAT RIDES BACK IS MORE THAN THE VERDICT. Each record now carries ``wrote_to_instance``: the
files that proof would have left in instance-space. That roster is the thing the parent
logging ticket could not previously obtain at any price — the census of which proofs write
into ``~/.cairn/logs/``, and therefore which trail records on the host were a device doing its
job and which were exhaust. On 2026-08-18 the answer to that question was 2,080 records
spanning seventeen minutes, and it took a hand-run measurement to learn it. It rides in the
carry unconditionally, because the finding is useless without it.

THE ARMING CUTOFF IS THE WHOLE MEASUREMENT. Every validation dated before the seal landed has
no ``instance_seal`` key and never could have; counting those would make clause (2) fire
forever on a question that is not being asked. Only records at or after the cutoff are the
population, which is what keeps the answer falsifiable.

WHAT THIS PROBE PARTLY WATCHES IS THE VOYAGE THAT ARMED IT, said out loud rather than glossed:
the first records it counts are this build's own corpus run. They are honest evidence — they
went through the real path — but they are the author's own participation, and the floor is
what keeps that from being mistaken for an answer.

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

# The moment the seal landed and run_proof began recording `instance_seal`. ISO-8601 compares
# correctly as a string against the record's `date`, which is
# `datetime.isoformat(timespec="seconds")` in local time — same clock, same shape.
#
# A TIMESTAMP AND NOT A DATE, because the first draft used "2026-08-18" and immediately
# reported five UNWATCHED records: five proofs sealed and recorded that morning, hours before
# the seal existed. They were not a finding, they were the cutoff being a day wide. Clause (2)
# reads an ABSENCE, and an absence-reader is only as honest as the moment it starts counting
# from — a day-granular cutoff on the very day a mechanism ships manufactures its own
# offenders, and they look exactly like real ones.
_SEAL_LANDED = "2026-08-18T13:45:00"

# The sample size below which the question cannot be answered. A handful of sealed runs is a
# plausible run of luck; forty is most of a corpus pass, which is the unit of traffic that
# actually exercises the seal. Honestly chosen and not derived — the same debt the sibling
# probes carry at their own floors, and re-tunable once the seal rate is a measured number.
_ENOUGH = 40

# The node this probe was compiled from. A bare id because it is an IDENTITY; `owning_ticket`
# builds the address that rides in the payload (ruling 2026-08-05, "the file path is the link").
_OWNING_TICKET = "a-proof-cannot-seed-the-tree-it-reads"


def survey_the_corpus() -> dict:
    """Count, over every validations record dated at or after the seal landed: how many ran
    sealed, how many came back some other verdict, how many carry no seal at all — and what
    the sealed ones would have written into instance-space.

    THE OFFENDERS ARE NAMED, NOT JUST COUNTED, and each carries the ``caller`` that produced
    it, because "who ran this" is the question a finding here is worthless without. That is
    the question the validation store's own breach could not answer for eight days.

    Reads files only. A file this probe cannot parse is skipped rather than counted, and
    skipping is REPORTED: a probe that quietly treats an unreadable file as clean is the
    vacuous green its own subject matter is about.
    """
    population = 0
    unsealed: list[dict] = []
    unwatched: list[dict] = []
    writers: list[dict] = []
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

        rel = os.path.relpath(path, _CLASS_SPACE)
        for rec in records:
            if not isinstance(rec, dict) or str(rec.get("date", "")) < _SEAL_LANDED:
                continue
            population += 1
            where = {"trail": rel, "claim": rec.get("claim"),
                     "caller": rec.get("caller"), "date": rec.get("date")}
            evidence = rec.get("evidence") if isinstance(rec.get("evidence"), dict) else {}
            seal = evidence.get("instance_seal")

            if not isinstance(seal, dict):
                # Clause (2): ran after the seal landed, and met no seal on the way. The
                # absence IS the finding — it cannot be seen by looking at verdicts.
                unwatched.append(where)
                continue
            if seal.get("verdict") != "sealed":
                unsealed.append({**where, "verdict": seal.get("verdict"),
                                 "detail": seal.get("detail")})
                continue

            wrote = seal.get("wrote_to_instance")
            if isinstance(wrote, dict) and wrote.get("count"):
                writers.append({**where, "count": wrote["count"],
                                "paths": wrote.get("paths", []),
                                "elided": wrote.get("elided", 0)})

    breached = [u for u in unsealed if u.get("verdict") == "breached"]
    return {"population": population,
            "unsealed": unsealed, "unsealed_count": len(unsealed),
            "breached_count": len(breached),
            "unwatched": unwatched, "unwatched_count": len(unwatched),
            "writers": sorted(writers, key=lambda w: -w["count"]),
            "writer_count": len(writers),
            "unreadable": unreadable}


def _trigger(now, context: dict) -> bool:
    """TRUE when enough has landed to judge AND the corpus is not living sealed — either a run
    came back some other verdict, or a run came back having never met the seal.

    A WRITER IS NOT A TRIGGER, deliberately. Proofs writing into instance-space is the ordinary
    world this seal was built for, not a defect; the seal working means those writes land in a
    swap and are counted. Firing on them would poke the owner about a mechanism doing its job,
    which is the shape of an alarm nobody keeps reading. The roster rides the carry instead.
    """
    s = context.get("corpus") or survey_the_corpus()
    return s["population"] >= _ENOUGH and (s["unsealed_count"] or s["unwatched_count"])


def _enough(context: dict) -> bool:
    """CLEARED once enough has landed to judge AND every one of them ran sealed. At that moment
    the question is answered — the corpus is living the invariant — and a standing watch on a
    settled question is the re-derivation Law 1 refuses.

    THE FLOOR SITS ON THIS CLAUSE TOO. Without it this clears at n=0: an empty population has
    no unsealed record in it, so the watch would retire on its first pulse, before a single
    proof had run — the asymmetry that made ``does_optional_mean_never_carried`` clear at n=1
    against a corpus of one ticket, which was itself. A watch that can clear before it can fire
    is not a watch.
    """
    s = context.get("corpus") or survey_the_corpus()
    return (s["population"] >= _ENOUGH
            and not s["unsealed_count"] and not s["unwatched_count"])


def _carry(context: dict) -> dict:
    """The datum that rides back: what failed, who ran it, and the writer roster — which is
    the answer to "which trail records were a device and which were the tester", and is the
    reason the parent logging ticket can be measured at all."""
    s = context.get("corpus") or survey_the_corpus()
    parts = []
    if s["breached_count"]:
        parts.append(f"{s['breached_count']} BREACHED (a proof's writes reached the live "
                     f"instance root)")
    other = s["unsealed_count"] - s["breached_count"]
    if other:
        parts.append(f"{other} ran unsealed without breaching (indeterminate or open)")
    if s["unwatched_count"]:
        parts.append(f"{s['unwatched_count']} carry no instance_seal at all — run by a path "
                     f"that never met it")
    return {"finding": "; ".join(parts) or "the corpus is not living sealed",
            "population": s["population"],
            "unsealed_records": s["unsealed"],
            "unwatched_records": s["unwatched"],
            "writers_into_instance_space": s["writers"],
            "unreadable_files": s["unreadable"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "a proof run after 2026-08-18 leaves a file in live "
                                 "instance-space, or runs by a path that never met the seal — "
                                 "either kills the claim that the logs tree shows what the "
                                 "SYSTEM did rather than what the tester did",
            "suggests": "read the `detail` on each unsealed record first: INDETERMINATE names "
                        "its own reason (no bwrap, an empty root, a probe that could not "
                        "write) and is usually an environment answer, not a code one. An "
                        "unwatched record is the harder finding — open its `caller` and ask "
                        "what path ran that proof without run_proof, because that path is "
                        "where the physics stopped being physics"}


# THE HORIZON. Same unit and same honest placeholder as the sibling probes: the unit is PULSES
# because the shim counts pulses, the wall-clock beat that would drive them is a filed edge
# rather than a built one, so nothing pulses this shim today and the loudness rides the
# read-side door (`BaseShim.overdue()`) alone. 1000 is "clearly a long standing" against any
# beat rate we would plausibly pick. Honest as a placeholder and dishonest as a measurement.
_HORIZON = 1000

PROBE = Probe(
    why="the seal's proofs settle that it holds in a fixture today; whether the corpus keeps "
        "running through it is a fact about live traffic, and this system has already watched "
        "a sealed door with green proofs get routed around by six voyages in two days",
    trigger=_trigger,
    to="tester",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

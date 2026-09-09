"""PROBE — does the corpus keep its seal MEASUREMENTS once the guard is standing?

Berth for the WATCHME that ticket ``4431cf2bc625`` carries. Berthed here, beside the
tester, because that is WHAT IT WATCHES: the seal verdict is minted in
``cairn/devices/tester/isolation.py``, sealed through ``validation_store.persist_validation``,
and the hand that would lose it is a caller of that door. The ticket it was compiled from
lives in CairnCommons and this probe deliberately does not follow it there.

THE EFFICACY QUESTION, AND WHY THE TOOTH CANNOT ASK IT.
``proofs/test_seal_is_never_silently_dropped.py`` settles that the door refuses
``sealed -> open`` — in a fixture, on demand, today. What it cannot settle is whether the
CORPUS keeps its measurements, and that is the question the ticket was cast against: on
2026-09-08 forty-four validations lost a `sealed` reading to a record saying nobody had
asked, and every proof in the corpus was green while it happened. A guard is worth what the
traffic actually carries, and this system has watched a sealed door with green proofs get
routed around by six voyages in two days.

THE TWO WAYS IT LOSES, and neither is visible from inside a proof:

  (1) THE ESCAPE BECOMES THE ROUTE. ``unsealing_because`` exists so a real reason can be
      stated and ride permanently in the record — an escape route, not a lock. It is
      correctly used at n≈0. A corpus accumulating them is a corpus where the sentence has
      become a formality, which is the shape every gate-with-an-override fails into, and the
      whole point of putting the reason ON THE RECORD is that this becomes countable rather
      than felt.
  (2) MEASUREMENTS DISAPPEAR SOME OTHER WAY. The guard sits on ONE door. A hand-edited
      validations file, a second writer, a component deleted — each drops a `sealed` reading
      without ever meeting ``persist_validation``, and the absence of a key looks like
      nothing. So the population is counted against a FROZEN BASELINE taken the day the
      guard was armed: sealed readings only ever accumulate under honest use, so a count
      BELOW the baseline is a measurement that went away.

WHAT THE BASELINE IS AND IS NOT. It is 122 sealed readings across both roots, counted
2026-09-09 at arming, and it is a FLOOR rather than an expectation: the honest direction of
travel is upward, and asserting the number itself would red the moment a legitimate new seal
landed (the snapshot-instead-of-invariant failure). Deliberately NOT the sealed:open RATIO,
which the ticket's first cut named — a ratio falls when someone adds an honestly-unsealed
proof, which is ordinary and correct, so a ratio watch would poke about the system working.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that re-opens
a node whose intention did not work is the OWNER's act (Law 6).

FILES ONLY — no device, no bus, no network, so it stays cheap enough to sit on a pulse.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from cairn.tools.base.probe import Probe, once, owning_ticket

# Class-space root: this file is cairn/devices/tester/probes/<name>.py.
_CLASS_SPACE = Path(__file__).resolve().parents[4]
# The commons carries validations too — it holds the human-proved quorum records — so a
# census that walked class-space alone would be blind to a third of the population.
_COMMONS = _CLASS_SPACE.parent / "CairnCommons"

# THE FROZEN BASELINE, measured 2026-09-09 across both roots at the moment the guard shipped:
# 208 validations files, 122 carrying `sealed`, 80 carrying `open`, 6 carrying no seal key at
# all (records that predate the seal). A FLOOR, not an expectation — see the header.
_BASELINE_SEALED = 122
_ARMED = "2026-09-09"

# The ticket's `enough`: thirty days of live traffic with the invariant holding. Thirty rather
# than seven because the failure it watches for is a HABIT forming, and a habit needs enough
# voyages to form in — the 2026-09-08 loss happened inside a single afternoon, but the escape
# turning into the route is a slower shape. Honestly chosen and not derived; re-tunable once
# the corpus has a measured re-seal rate.
_ENOUGH_DAYS = 30

# The node this probe was compiled from. THE FULL STEM, not the bare hex id: `owning_ticket`
# resolves by exact name or by the SUFFIX glob `*-<name>.json`, and this corpus files tickets
# id-FIRST, so the id alone renders a visible hole. Measured here at arming rather than
# reasoned about — the first draft carried `4431cf2bc625` and the carry came back
# `{unresolvable:...}` (which is the function doing its job, loudly, exactly as designed).
_OWNING_TICKET = "4431cf2bc625-a-measured-seal-is-never-replaced-by-an-unrequested-one"


def survey_the_corpus() -> dict:
    """Count, over every standing validation in both roots: how many carry each seal verdict,
    and which ones carry a stated ``unsealing_because``.

    THE ESCAPES ARE NAMED, NOT JUST COUNTED, and each carries its reason and its caller,
    because "who unsealed this and what did they say" is the question a finding here is
    worthless without — the reason was put on the record precisely so it could be read.

    Reads files only. A file this probe cannot parse is skipped rather than counted, and
    skipping is REPORTED: a probe that quietly treats an unreadable file as clean is the
    vacuous green its own subject matter is about.
    """
    verdicts: dict[str, int] = {}
    escapes: list[dict] = []
    unreadable: list[str] = []
    population = 0

    for root in (_CLASS_SPACE, _COMMONS):
        if not root.is_dir():
            unreadable.append(f"{root}: root not present on this host")
            continue
        for path in sorted(root.glob("**/validations/*.json")):
            if "__pycache__" in str(path):
                continue
            try:
                records = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(records, list) or not records:
                    raise ValueError("a validations file is a non-empty list of records")
            except Exception as err:  # noqa: BLE001
                unreadable.append(f"{os.path.relpath(path, root)}: {err}")
                continue

            # The STANDING record only. The door replaces rather than appends (2026-08-16),
            # so the file is a one-element list and [-1] is the seal in force; counting any
            # earlier element would count a reading that has already been superseded.
            rec = records[-1]
            if not isinstance(rec, dict):
                unreadable.append(f"{os.path.relpath(path, root)}: standing record is not an object")
                continue
            population += 1
            evidence = rec.get("evidence") if isinstance(rec.get("evidence"), dict) else {}
            seal = evidence.get("seal") if isinstance(evidence.get("seal"), dict) else {}
            verdict = seal.get("verdict")
            verdicts[str(verdict)] = verdicts.get(str(verdict), 0) + 1

            if evidence.get("unsealing_because"):
                escapes.append({"trail": os.path.relpath(path, root),
                                "because": evidence["unsealing_because"],
                                "caller": rec.get("caller"), "date": rec.get("date")})

    return {"population": population,
            "verdicts": verdicts,
            "sealed_count": verdicts.get("sealed", 0),
            "escapes": escapes, "escape_count": len(escapes),
            "unreadable": unreadable}


def _days_since_arming() -> int:
    """Wall-clock days since the guard shipped.

    READ HERE RATHER THAN FROM ``context`` because ``enough`` is handed only the context and
    the shim's pulse carries no clock into it. The comparison is coarse by design — the unit
    the ``enough`` clause is written in is days, and a day-granular reading cannot be wrong
    by enough to matter against a thirty-day horizon.
    """
    return (datetime.now() - datetime.strptime(_ARMED, "%Y-%m-%d")).days


def _trigger(now, context: dict) -> bool:
    """TRUE when the corpus has lost a seal measurement, or has started stating its way out
    of them.

    NO POPULATION FLOOR ON THIS ONE, and that is a real difference from its siblings. Those
    ask "is the corpus living the invariant?", which is unanswerable at n=0; this asks "did
    something that was measured stop being measured?", and the baseline IS the sample — one
    lost reading is a finding on the day it happens, which is the whole complaint about
    2026-09-08 having been caught by a hand diffing one file.
    """
    s = once(context, "corpus", survey_the_corpus)
    return s["sealed_count"] < _BASELINE_SEALED or bool(s["escape_count"])


def _enough(context: dict) -> bool:
    """CLEARED once thirty days of live traffic have passed with the invariant holding: no
    measurement lost, and nobody having had to state their way past the door.

    THE ELAPSED CLAUSE IS WHAT KEEPS THIS FROM CLEARING ON ITS FIRST PULSE. Without it the
    watch retires the instant it is armed — the corpus trivially satisfies both conditions on
    day zero, because the guard has not yet been given any traffic to hold against. That is
    the asymmetry that let ``does_optional_mean_never_carried`` clear at n=1 against a corpus
    of one ticket, which was itself. A watch that can clear before it can fire is not a watch.
    """
    s = once(context, "corpus", survey_the_corpus)
    return (_days_since_arming() >= _ENOUGH_DAYS
            and s["sealed_count"] >= _BASELINE_SEALED
            and not s["escape_count"])


def _carry(context: dict) -> dict:
    """The datum that rides back: what was lost or stated away, who did it, and what they said."""
    s = once(context, "corpus", survey_the_corpus)
    lost = _BASELINE_SEALED - s["sealed_count"]
    parts = []
    if lost > 0:
        parts.append(f"{lost} sealed reading(s) below the {_BASELINE_SEALED} standing at "
                     f"arming — a measurement went away without meeting the door")
    if s["escape_count"]:
        parts.append(f"{s['escape_count']} validation(s) carry a stated `unsealing_because`")
    return {"finding": "; ".join(parts) or "the corpus is keeping its seal measurements",
            "population": s["population"],
            "verdicts": s["verdicts"],
            "baseline_sealed": _BASELINE_SEALED,
            "sealed_now": s["sealed_count"],
            "escapes": s["escapes"],
            "unreadable_files": s["unreadable"],
            "days_since_arming": _days_since_arming(),
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "a validation that carried a seal verdict of sealed, "
                                 "indeterminate or breached comes to carry `open` instead — "
                                 "which is not a weaker reading but the absence of one, and "
                                 "kills the claim that a measurement taken here survives "
                                 "until a newer measurement of the same question replaces it",
            "suggests": "read each escape's `because` first: the field exists so the choice "
                        "is legible, and a corpus of them that all say the same thing is the "
                        "sentence having become a formality rather than a reason — that is a "
                        "spec question for the owner, not a code fix. A sealed count BELOW "
                        "the baseline is the harder finding: nothing came through the door, "
                        "so ask git what touched a validations file"}


# THE HORIZON. Same unit and same honest placeholder as the sibling probes: the unit is PULSES
# because the shim counts pulses, the wall-clock beat that would drive them is a filed edge
# rather than a built one, so nothing pulses this shim today and the loudness rides the
# read-side door (`BaseShim.overdue()`) alone. 1000 is "clearly a long standing" against any
# beat rate we would plausibly pick. Honest as a placeholder and dishonest as a measurement.
_HORIZON = 1000

PROBE = Probe(
    why="the guard's teeth settle that one door refuses a downgrade today; whether the corpus "
        "keeps its seal measurements is a fact about live traffic, and the loss this ticket "
        "was cast against happened while every proof in the corpus was green",
    trigger=_trigger,
    to="tester",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

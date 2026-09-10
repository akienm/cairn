"""PROBE — does a berth that never changed still deposit, after the world moved under it?

Berth for the WATCHME that ticket ``4c022c44de53`` carries (object
``berth_deposits_again``). Berthed here, beside the machine, because that is WHAT IT
WATCHES; the ticket it was compiled from lives in CairnCommons and this probe deliberately
does not follow it there.

THE FAILURE IT WATCHES FOR NEEDS NO BUILD TO HAVE HAPPENED. Until 2026-09-10 both the
write door and the deposit door re-measured provenance by re-running the floor. The floor
reads TODAY's tree, so a berth written honestly last week was refused this week because a
file moved underneath it — the door refusing the label the door itself had stamped.
Measured on the day it was fixed, across every berth in instance-space:

    orient      356 walked, 68 passed, 286 refused for a provenance disagreement, 2 other
    constrain   348 walked, 55 passed, 293 refused for a provenance disagreement, 2 other

The trouble that reported it named one berth.

WHAT THE FIX WAS, AND WHY IT NEEDS A WATCH RATHER THAN ONLY PROOFS. ``validate_orient``
and ``validate_constrain`` took a ``measure_provenance`` switch: the write door measures,
the deposit door reads the label the write door stamped. Proofs pin that at both doors,
against a fixture. What proofs cannot show is the thing that actually broke — a world that
MOVES. The fixture world is built and torn down inside one run, so a berth in it is never
older than the tree it is checked against, which is precisely the condition the defect
needed. Only live berths, aging against a live repo, can answer.

WHY THE SIBLING PROBE'S CAVEAT IS THIS PROBE'S SUBJECT. ``floor_earns_its_label.py``
carries a disagreement table and deliberately fires on nothing, because "re-derivation
reads today's tree" makes a disagreement a fact about the world rather than about the
door. That reasoning was written the same week, at this address, and is exactly right —
and the deposit door was doing the thing that probe refused to do. So this probe does not
fire on a disagreement either. It fires when a disagreement becomes a REFUSAL.

THE CLEAR IS TWO BEATS AND A MOVED WORLD, and both halves are load-bearing. Zero
refusals alone cannot tell a fixed door from a quiet week: it is the shape that let
``a_pickup_is_witnessed.py`` read green off a single August fact forever. So a beat only
counts toward the clear when the corpus contains at least one berth whose stored label
the floor no longer reproduces — a berth the pre-fix door WOULD have refused. That is the
deterministic reading of "a commit that changed the floor's answer for some berthed
request": the change is observed in its effect on the corpus, not chased through git.

THE POPULATION IS POST-BUILD BERTHS ONLY, by filename stamp. Berths predating 2026-08-14
were written under the old schema and refuse for reasons that have nothing to do with this
ticket; Law 7 says a record of truth is not rewritten by a later rule, so counting them
would retro-red an honest corpus and guarantee the watch fires forever.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that
re-opens a node whose intention did not work is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket, once

# Instance-space, resolved per call and never captured at import — a probe that froze the
# path would keep reading a root the system had already left.
_BERTH_ENV = "CAIRN_CHART_PACKETS"
_BERTH_DEFAULT = Path.home() / ".cairn/devices/chart/0/packets"

# The observation trail. Instance-space, under the device that holds the machine — the
# probe's own state is the HOLDER's to own and gate (Law 6's tool clause, one rung up).
_TRAIL_ENV = "CAIRN_ORIENT_DEPOSIT_TRAIL"
_TRAIL_DEFAULT = (Path.home()
                  / ".cairn/devices/codemother/0/machines/orient/probes"
                  / "a_berth_deposits_again.json")

# The measurement door landed 2026-08-14; berths are named ``<stage>-<YYYYmmddTHHMMSS>-
# <digest>``, so the stamp IS the population filter.
_DOOR_LANDED = "20260814T000000"

# How many consecutive clean-and-moved beats retire the watch. Two, because one cannot
# distinguish a fixed door from a corpus nobody wrote to.
_BEATS_TO_CLEAR = 2

_TICKET = owning_ticket("orient-deposit-reads-stored-provenance")

# The horizon, in pulses because the shim counts pulses. Nothing pulses this shim yet
# (the wall-clock backing is a filed edge in the ground loop, not built), so the loudness
# rides the read-side door alone. Honest as a placeholder, dishonest as a measurement.
_HORIZON = 1000


def _classify(err: str) -> str:
    """WHICH KIND OF REFUSAL, and the classes are not decoration — they route differently.

    ``provenance`` is this ticket's defect and clears without a human. ``pointer`` is a ref
    or a constraint source that has MOVED, which is the same world-drift one layer over and
    is owed its own ticket; it escalates rather than clearing. ``other`` is anything this
    probe did not anticipate and is reported verbatim rather than binned."""
    low = err.lower()
    if "declares its own provenance" in low or "not the one the berth carries" in low:
        return "provenance"
    # THE NEEDLES ARE THE DOORS' OWN SENTENCES, checked against them on 2026-09-10 —
    # orient's gate says "refs the floor cannot verify EXIST", constrain's judge says
    # "names a source that does not resolve". A classifier guessing at wordings would
    # have binned 64 pointer refusals as "other", which is what the first draft did.
    for needle in ("refs the floor cannot verify", "does not resolve", "does not exist",
                   "invented", "names a source"):
        if needle in low:
            return "pointer"
    return "other"


def _walk_stage(stage: str, *, measure_drift: bool) -> dict:
    """Walk every post-build berth of one stage through the DEPOSIT door's validation and
    report what happens, split by refusal class.

    Two readings per berth, and the pair is the whole point. ``deposits`` is what the door
    does today. ``floor_moved`` is whether re-running the floor still reproduces the stored
    label — when it does not, this berth is one the pre-fix door would have refused, and it
    is the evidence that the corpus has actually moved rather than merely been quiet.

    THE DRIFT READING IS TAKEN AT ORIENT ONLY, and that is a measurement rather than a
    preference. Timed 2026-09-10 over the live corpus: orient's floor re-runs at 311 berths
    in 2.5s, and constrain's exceeds 20 SECONDS PER BERTH, because ``constrain_floor``
    discovers and RUNS the ref'd components' proof instruments. A beat costing two hours is
    a beat nobody takes, and a watch nobody takes is the hollow-green shape this probe was
    written against. Both stages are still walked through the deposit door — that reading
    is 0.02s per berth at either stage — so a provenance refusal is caught wherever it
    appears. What orient alone supplies is the "and the world moved" half of the clear,
    which is one fact about the repo and not a per-stage one.

    A berth this probe cannot read is skipped rather than counted in either direction: the
    counts are a claim (Law 3), and a claim resting on a parse failure is worse than a
    smaller n."""
    if stage == "orient":
        from cairn.devices.codemother.machines.orient.orient import (
            OrientRefused as Refused, measured_provenance as measure,
            validate_orient as validate)
    else:
        from cairn.devices.codemother.machines.constrain.constrain import (
            ConstrainRefused as Refused, measured_provenance as measure,
            validate_constrain as validate)

    berths = Path(os.environ.get(_BERTH_ENV) or _BERTH_DEFAULT)
    walked = deposits = floor_moved = 0
    refused: dict[str, int] = {}
    examples: list[dict] = []

    for path in sorted(berths.glob("%s-*.json" % stage)) if berths.is_dir() else []:
        stamp = path.name.split("-")[1] if path.name.count("-") >= 2 else ""
        if stamp < _DOOR_LANDED:
            continue
        try:
            packet = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(packet, dict):
            continue
        walked += 1

        if measure_drift:
            stored = dict(packet.get("provenance") or {})
            try:
                if measure(dict(packet)) != stored:
                    floor_moved += 1
            except Exception:
                # A floor refusal on a stale request says nothing about whether the label
                # moved; it is not this probe's finding either way.
                pass

        try:
            validate(dict(packet), measure_provenance=False)
            deposits += 1
        except Refused as err:
            kind = _classify(str(err))
            refused[kind] = refused.get(kind, 0) + 1
            if len(examples) < 10:
                examples.append({"berth": path.name, "class": kind,
                                 "refusal": str(err)[:400]})
        except Exception as err:  # noqa: BLE001 — an unexpected raise IS a finding
            refused["other"] = refused.get("other", 0) + 1
            if len(examples) < 10:
                examples.append({"berth": path.name, "class": "other",
                                 "refusal": "%s: %s" % (type(err).__name__, err)})

    return {"walked": walked, "deposits": deposits, "refused": refused,
            "floor_moved_under": floor_moved if measure_drift else None,
            "drift_measured": measure_drift, "examples": examples}


def survey_the_corpus() -> dict:
    """THE CENSUS — both stages, one report.

    ``provenance_refusals`` is the number this ticket drove to zero and the number a
    regression would drive back up. ``floor_moved_under`` is what makes a zero mean
    something: berths whose stored label the floor no longer reproduces, which the door
    deposits anyway."""
    stages = {"orient": _walk_stage("orient", measure_drift=True),
              "constrain": _walk_stage("constrain", measure_drift=False)}
    prov = sum(st["refused"].get("provenance", 0) for st in stages.values())
    ptr = sum(st["refused"].get("pointer", 0) for st in stages.values())
    other = sum(st["refused"].get("other", 0) for st in stages.values())
    moved = sum(st["floor_moved_under"] or 0 for st in stages.values())
    return {"stages": stages,
            "walked": sum(st["walked"] for st in stages.values()),
            "deposits": sum(st["deposits"] for st in stages.values()),
            "provenance_refusals": prov,
            "pointer_refusals": ptr,
            "other_refusals": other,
            "floor_moved_under": moved,
            "a_beat_that_counts": prov == 0 and moved > 0}


def _trail_path() -> Path:
    return Path(os.environ.get(_TRAIL_ENV) or _TRAIL_DEFAULT)


def read_trail() -> list:
    try:
        data = json.loads(_trail_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def record_beat(survey: dict, *, at: str) -> list:
    """Append one observation to the trail and return it. APPEND-ONLY: a beat is a
    measurement, and rewriting one to make a streak look longer is the failure the
    two-beat rule exists to prevent."""
    trail = read_trail()
    trail.append({"at": at,
                  "walked": survey["walked"],
                  "provenance_refusals": survey["provenance_refusals"],
                  "pointer_refusals": survey["pointer_refusals"],
                  "floor_moved_under": survey["floor_moved_under"],
                  "counts": survey["a_beat_that_counts"]})
    path = _trail_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trail[-200:], indent=2) + "\n", encoding="utf-8")
    return trail


def _consecutive_counting_beats(trail: list | None = None) -> int:
    """How many beats at the END of the trail counted. A single non-counting beat resets
    it to zero, which is what CONSECUTIVE means and what a running total would not say."""
    run = 0
    for beat in reversed(trail if trail is not None else read_trail()):
        if not beat.get("counts"):
            break
        run += 1
    return run


def _trigger(now, context: dict) -> bool:
    """TRUE when a post-build berth is refused at the deposit door for a provenance
    disagreement — the defect restored. Not on a disagreement, which is a fact about the
    world; on a REFUSAL, which is a fact about the door."""
    return once(context, "survey", survey_the_corpus)["provenance_refusals"] > 0


def _enough(context: dict) -> bool:
    """CLEARED after two consecutive beats that each reported zero provenance-refusals
    over a corpus the floor had MOVED under. The second clause is why this cannot read
    green off one quiet observation."""
    survey = once(context, "survey", survey_the_corpus)
    run = _consecutive_counting_beats()
    if survey["a_beat_that_counts"]:
        # The live reading counts as the current beat whether or not it has been recorded
        # yet — an unrecorded beat is still an observation (Law 10).
        run = max(run, 1) if run == 0 else run
    return run >= _BEATS_TO_CLEAR


def _carry(context: dict) -> dict:
    """The datum that rides back — the full census in ONE report, and a POINTER to the
    ticket rather than a copy of it (Law 6 — the ticket is the commons')."""
    survey = once(context, "survey", survey_the_corpus)
    return {"finding": "a berthed chart packet is being refused at its own deposit door "
                       "for a provenance label that door wrote",
            "census": survey,
            "consecutive_counting_beats": _consecutive_counting_beats(),
            "ticket": _TICKET,
            "against_falsifier": "the ticket's falsifier (c) is that a berth deposits "
                                 "again against TODAY's corpus; a provenance refusal here "
                                 "is that clause failing in the live world",
            "escalate": "a 'pointer' refusal is NOT this ticket's defect — it is a ref or "
                        "a constraint source that has moved, the same world-drift one "
                        "layer over, and it is owed its own ticket. It is reported here "
                        "because the census would be lying by omission without it, and it "
                        "goes to Akien rather than clearing on its own.",
            "suggests": "read validate_orient and validate_constrain first: the deposit "
                        "doors pass measure_provenance=False and the write doors pass "
                        "True. A non-zero count here usually means one of those four call "
                        "sites changed, or a new caller reached validate_* directly and "
                        "took the strict default."}


PROBE = Probe(
    why="does a berth that never changed still deposit after the world moved under it? — "
        "both doors used to re-measure provenance against today's tree, so 286 of 356 "
        "orient berths and 293 of 348 constrain berths were refused for a label their own "
        "write door had stamped. Cleared by two consecutive beats of zero "
        "provenance-refusals over a corpus the floor has actually moved under.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "orient", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

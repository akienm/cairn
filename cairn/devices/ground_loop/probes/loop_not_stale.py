"""PROBE — is a device on the bench for the LOOP's age rather than its own defect?

Berth for the WATCHME that ticket ``the-loop-names-its-own-staleness-instead-of-benching-a-
device`` carries. Berthed beside ``cairn/devices/ground_loop`` because that is WHAT IT
WATCHES: the benching decision in ``loop._reconcile`` and the predicate in ``staleness.py``.

THE CLAIM UNDER WATCH. The build now asks, on the probe-load failure path, whether THIS
PROCESS is older than the code it is judging, and declines to bench anyone when it is. Every
acceptance criterion at that voyage's validate berth can pass on the day it lands and still
leave this bet untested, because the bet is about a condition that only arises when a daemon
outlives a code change — which is a claim about the future, and is why it is here.

THE SIGNATURE THIS FIRES ON is the exact shape of the 29-hour outage, stated as a relation
between two readings rather than as an error string: A DEVICE IS HELD OUT BY A LIVE BENCH
TICKET AND ITS PROBE FOLDER IMPORTS CLEANLY RIGHT NOW. That was true of all fifteen benched
devices, and nobody could see it because reading it required running the second measurement
against the first, and the ticket's own text answered the question in the wrong direction.

  - FIRE on the FIRST one. The failure mode is silent by construction — a benched device
    stops being re-scanned, so its trouble stops recurring and its count freezes, which
    reads exactly like an outage that ended. Waiting for n is waiting in the dark.
  - CLEAR IS NEVER A QUIET PERIOD, because a quiet period is precisely what this looked
    like for 29 hours. It needs the store to hold a record of the condition whose last
    occurrence PRECEDES this process's start — that is, the loop has run its entire life
    clean THROUGH the event that creates the staleness. Until a restart has been survived,
    silence is untested rather than evidence (Law 9), and a store with no such record at all
    clears nothing: there is nothing to have survived yet.

WHY THE CLEAR NEEDS NO PROBE STATE. "Absent across an observed restart" sounds like it must
remember something between fires. It does not: the trouble store's occurrence history is
append-only and the loop's own start time is on disk, so `last occurrence < process start` IS
the observed restart, computed from two reads. That matters because ground_loop's falsifier
clause (5) forbids the heartbeat holding runtime state of its own beyond the ruled liveness
record, and a probe that berthed a cursor here would put that clause in question to answer a
question disk already answers.

COST, because this runs on every beat and the beat is already carrying 2531 ms of trigger:
the common case is ONE `trouble.live()` read, MEASURED rather than asserted cheap — see
`_bench_tickets_exist`, which also records why it is that read and not the cheaper listing
it was first written as. The expensive half — a fresh discovery over the device folders —
runs only when a bench ticket actually stands, which in a healthy system is never.

AUTHORITY: none. This probe deposits and pokes. Re-opening the node is the owner's act at the
register (Law 6). A fire means READ THE PROCESS START AGAINST THE TREE FIRST — that one
comparison separates the two causes, and getting it backwards is how this went unread for 29
hours.
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-loop-names-its-own-staleness-instead-of-benching-a-device"

# Same placeholder horizon, same tracked debt, as the probes at cairn/tools/base and
# cairn/machines/build_inspector: the beat rate is not yet a real number.
_HORIZON = 1000


def _bench_tickets_exist() -> bool:
    """The cheap half — one `live()` read. A healthy system stops here, every beat, forever.

    THROUGH THE STORE'S OWN DOOR, and the first draft of this function was neither.
    It reached for `TroubleDevice().root` — which does not exist; the attribute is
    private (`_root`) and the device publishes the path only inside `state()`. Every
    proof stayed green because they all feed `judge()` fixtures and none of them ever
    reached this line, so the defect was found the one way it could be: by CALLING it
    under a real `discover()`. That is the same lesson as the bench itself — armed by
    hand is not the same as wired, and the diagnostic is to call the thing.

    THE SECOND DEFECT WAS THE WORSE ONE. That draft globbed FILENAMES for the bench
    prefix, and a file keeps its name after it is cleared — so the cheap half counted
    dead tickets as benches while `survey_the_bench` below asked `live()`. Two
    definitions of "benched" inside one probe, disagreeing exactly when a bench had
    just been cleared. `survey_the_bench` refuses to re-implement `discover()` for
    this reason and this half was quietly re-implementing `live()`; it now asks the
    same door, so the halves cannot drift apart.

    COST: `live()` parses the trouble records rather than listing names. Measured on
    the live store at build time, n=15 over 27 records — median 2.1 ms, max 2.4 —
    against a beat already carrying 2531 ms of trigger, so 0.08% of what the beat
    already spends. The expensive half (a fresh discovery over every device folder)
    measured 38 ms on the same store, and still runs only when a bench actually
    stands, which in a healthy system is never. Both numbers are readings, not
    estimates; if the store grows enough to make the first one matter, the reading
    is the thing that will say so.
    """
    from cairn.devices.ground_loop.loop import TROUBLE_PREFIX
    from cairn.devices.trouble.trouble import TroubleDevice
    try:
        return any(str(t.get("id", "")).startswith(TROUBLE_PREFIX)
                   for t in TroubleDevice().live())
    except OSError:
        return False


def survey_the_bench() -> dict:
    """The live read: who is benched, and does each one actually import today?

    The second reading is taken through the loop's OWN ``discover``, not a re-implementation
    of it — a probe carrying its own idea of what 'imports cleanly' means would go green
    against itself while the real decision drifted.
    """
    from cairn.devices.ground_loop.discovery import discover
    from cairn.devices.ground_loop.loop import SELF_TROUBLE, TROUBLE_PREFIX
    from cairn.devices.ground_loop import staleness
    from cairn.devices.trouble.trouble import TroubleDevice

    trouble = TroubleDevice()
    live = trouble.live()
    benched = {t["id"][len(TROUBLE_PREFIX):]: t for t in live
               if str(t.get("id", "")).startswith(TROUBLE_PREFIX)}

    verdicts: dict[str, dict] = {}
    if benched:
        # skip=set() ON PURPOSE: the bench is what we are testing, so honouring it would make
        # the instrument agree with the claim it is measuring by construction.
        found = discover(skip=set())
        for device_id in benched:
            entry = found.get(device_id)
            verdicts[device_id] = {
                "on_disk": entry is not None,
                "imports_cleanly": bool(entry) and not entry["failures"],
                "failures": (entry or {}).get("failures", []),
            }

    # The whole history of this condition, live or cleared — the append-only record is what
    # makes "has a restart been survived" answerable without remembering anything.
    seen_at = [t.get("last_seen") for t in trouble.all()
               if str(t.get("id", "")).startswith(TROUBLE_PREFIX)
               or t.get("id") == SELF_TROUBLE]
    seen_at = sorted(s for s in seen_at if s)

    return {
        "benched": sorted(benched),
        "verdicts": verdicts,
        "self_trouble_live": any(t.get("id") == SELF_TROUBLE for t in live),
        "condition_last_seen": seen_at[-1] if seen_at else None,
        "diagnostics": staleness.diagnostics(),
    }


def judge(survey: dict) -> dict:
    """The pure judgement, separable from the read so the proof can feed it fixtures."""
    wrongly = sorted(d for d, v in survey["verdicts"].items() if v["imports_cleanly"])
    diagnostics = survey["diagnostics"]

    last_seen = survey["condition_last_seen"]
    started = diagnostics["process_started"]
    survived_a_restart = False
    if last_seen:
        try:
            from datetime import datetime
            survived_a_restart = datetime.fromisoformat(last_seen).timestamp() < started
        except (ValueError, TypeError):
            survived_a_restart = False

    return {
        "benched_but_importing": wrongly,
        "benched_total": len(survey["benched"]),
        "self_trouble_live": survey["self_trouble_live"],
        "condition_ever_recorded": bool(last_seen),
        "condition_last_seen": last_seen,
        "survived_a_restart": survived_a_restart,
        "process_started": started,
        "drifted_modules": [f["module"] for f in diagnostics["drifted"]],
        "undecidable_modules": diagnostics["undecidable"],
        "tree_newest_file": diagnostics["tree_newest_file"],
        "tree_newer_than_process": diagnostics["tree_newer_than_process"],
    }


def _seen(context: dict) -> dict:
    return context.get("judged") or judge(context.get("survey") or survey_the_bench())


def _trigger(now, context: dict) -> bool:
    """TRUE on the FIRST device held out by a ticket while importing cleanly."""
    if context.get("judged") is None and context.get("survey") is None \
            and not _bench_tickets_exist():
        return False                      # the cheap exit a healthy system takes every beat
    return bool(_seen(context)["benched_but_importing"])


def _enough(context: dict) -> bool:
    """CLEARED when nothing is wrongly benched AND this process has lived its whole life
    since the last time the condition was recorded at all. The two halves share one variable
    and cannot both be satisfied by silence: a store that has never recorded the condition
    fails the second half, which is the point — a watch that has only ever seen quiet has not
    been tested."""
    s = _seen(context)
    return not s["benched_but_importing"] and s["survived_a_restart"]


def _carry(context: dict) -> dict:
    s = _seen(context)
    return {
        "finding": "a device is held out of the heartbeat by a live bench ticket AND its "
                   "probe folder imports cleanly right now — so the ticket is describing "
                   "the loop's own age, not the device's defect, and every watch in that "
                   "folder is dark for as long as it stands",
        "benched_but_importing": s["benched_but_importing"],
        "benched_total": s["benched_total"],
        "read_this_first": "compare the loop's process start against the tree's newest file. "
                           "If the tree is newer, suspect the LOOP and restart it; the fix "
                           "order is restart, verify through the loop's own discover(), THEN "
                           "clear the tickets — a restart alone does not un-bench, because "
                           "the bench IS the live ticket and clearing is the recipient's act.",
        "process_started": s["process_started"],
        "tree_newest_file": s["tree_newest_file"],
        "tree_newer_than_process": s["tree_newer_than_process"],
        "drifted_modules": s["drifted_modules"],
        "undecidable_modules": s["undecidable_modules"],
        "self_trouble_live": s["self_trouble_live"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's first hollow pass, verbatim: 'improve the ERROR "
                             "STRING so it says possible stale loop and call it done. That "
                             "passes any test that greps the message while all fifteen "
                             "devices stay benched and every watch stays dark — the message "
                             "was never the damage, the BENCH was.'",
    }


PROBE = Probe(
    why="for 29 hours fifteen devices were held out of the heartbeat under their own names "
        "for a defect that belonged to the loop, and twenty-two probes went dark behind "
        "them; the bench made it self-sealing, because a benched device stops being "
        "re-scanned and an outage that stops recurring reads exactly like one that ended",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "triage", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the live bench and what the pair would do with it now.
    s = survey_the_bench()
    j = judge(s)
    print(json.dumps({"judged": j,
                      "would_trigger": _trigger(None, {"judged": j}),
                      "enough": _enough({"judged": j})}, indent=2, default=str))

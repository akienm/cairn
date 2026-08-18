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
TICKET AND ITS PROBE FOLDER IMPORTS CLEANLY IN A FRESH INTERPRETER RIGHT NOW. That was true
of all fifteen benched devices, and nobody could see it because reading it required running
the second measurement against the first, and the ticket's own text answered the question in
the wrong direction.

AND THE SECOND READING IS TAKEN IN A CHILD PROCESS, not here — see ``fresh_import_reading``,
which carries the measurement that forced it. Taking it in this process was the first
build's defect and it was this ticket's own disease: the loop is the suspect, so its own
re-import reproduces its own staleness and reads the misattributed bench as a real defect.

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
runs only when a bench ticket actually stands, which in a healthy system is never. Measured
2026-08-18 over the live store with one device benched: 383 ms for the whole expensive half,
of which the fresh-interpreter reading is one child process per benched device.

SECOND TICKET, SAME BERTH (2026-08-18, staleness-is-about-this-process-not-about-disk). The
predicate under this watch was rebuilt: it used to compare a source's mtime to the mtime in
that module's ``.pyc`` header, and BOTH of those are on disk, so any second interpreter
importing the module repaired the evidence without repairing the loop. It went blind, and the
loop benched an innocent device at 03:44Z on a shared ``.pyc`` an ordinary proof run had
refreshed. The new comparison holds the asker in it — what this process HOLDS against a fresh
compile of the file.

That ticket does not get a probe of its own, and the reason is the point: THIS PROBE'S
SIGNATURE ALREADY COVERED THE NEW DEFECT. It fires on a relation between two readings — held
out by a live ticket, imports cleanly right now — and it read TRUE against the live store on
2026-08-18 while the predicate beneath it was answering empty. A second probe would have been
a duplicate with the survey sitting right there. What it gains is the tally: ``diagnostics``
now reports the pass's COVERAGE (modules read, objects comparable, objects unreachable), so a
carry can say "compared 398 objects, none disagreed" rather than an empty list that reads the
same whether everything was checked or nothing was.

AND THE QUIET FACE IS DETECTED, NOT WATCHED, and not repaired. A probe body exec'd fresh off
its path still binds its ``from cairn... import`` dependencies through the boot-time
``sys.modules``, so it can evaluate old code while every surface reports healthy. The
predicate names that now — but only when something ASKS it, and the loop asks only on the
failure path. A healthy-looking quietly-stale loop asks nobody. Watching it per-beat was
priced and declined: the read measured ~200 ms over 77 held modules against a beat already
carrying 2531 ms, so 8% of the beat forever to catch a condition a restart also fixes.
Recorded rather than built (Law 9 — this is a known dark corner, not a covered one); a cheap
freshness witness is owed a ticket.

AUTHORITY: none. This probe deposits and pokes. Re-opening the node is the owner's act at the
register (Law 6). A fire means READ THE PROCESS START AGAINST THE TREE FIRST — that one
comparison separates the two causes, and getting it backwards is how this went unread for 29
hours.
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-loop-names-its-own-staleness-instead-of-benching-a-device"
# The second ticket this berth answers for — see the SECOND TICKET note in the docstring. It
# rides the carry so a reader of a fire can find both voyages, and it is a separate name
# rather than a list because the FIRST one is what the probe was compiled from.
_ALSO_WATCHES = "staleness-is-about-this-process-not-about-disk"

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


_FRESH_READER = (
    # THE SAME DOOR, IN A PROCESS THAT HOLDS NOTHING. It calls the discovery cache's own
    # `probes_for`, never a second idea of what "imports cleanly" means, and it seeds the
    # child's sys.path from the parent's so the ONLY difference between the two readings is
    # what is already held in memory. That is the whole experiment.
    "import json, sys\n"
    "sys.path[:0] = json.loads(sys.argv[1])\n"
    "from pathlib import Path\n"
    "from cairn.devices.ground_loop.discovery import ProbeCache\n"
    "probes, failures = ProbeCache().probes_for(Path(sys.argv[2]))\n"
    "print(json.dumps({'failures': failures, 'probes': len(probes)}))\n"
)


def fresh_import_reading(folder) -> dict:
    """Does a FRESH INTERPRETER reproduce this folder's import failure?

    THE READING THIS PROBE EXISTS TO TAKE, and the first build of it did not take it. The
    expensive half used to call ``discover()`` IN THIS PROCESS — and this process is the
    ground loop, the very thing suspected of being stale. Measured 2026-08-18 in a throwaway
    tree (scratchpad/probe_blindness.py): a process holding a pre-edit module reads the
    probe folder as ONE ImportError while a fresh interpreter over the same disk reads ZERO.
    So the in-process reading agrees with the bench exactly when the bench is wrong, and the
    probe's signature — held out, imports cleanly right now — could only ever read TRUE when
    the probe was run from somewhere OTHER than the loop. It fired in the smoke test for
    that reason and would have stayed silent where it lives.

    That is this ticket's own defect wearing the instrument's clothes: EVIDENCE THAT DOES
    NOT CONTAIN THE ASKER is the disease, and here the evidence contained the asker so
    thoroughly that it caught the asker's illness. The subprocess is the cure, and it is
    also what the ticket's falsifier declared in words on the day it was cast: "re-run the
    named folder's import in a subprocess; a success is a misattribution".

    COST: one interpreter start per benched device, and only when a bench actually stands.
    A healthy system never pays it. A refusal (the child died, or printed something that is
    not the reading) is returned as a refusal and never silently read as clean — a bench
    lifted on a crashed subprocess would be the loudest possible version of this same bug.
    """
    import subprocess
    import sys
    try:
        done = subprocess.run([sys.executable, "-c", _FRESH_READER,
                               json.dumps([p for p in sys.path if p]), str(folder)],
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"refusal": f"{type(exc).__name__}: {exc}", "failures": None, "probes": None}
    if done.returncode != 0:
        return {"refusal": f"exit {done.returncode}: {(done.stderr or '').strip()[-300:]}",
                "failures": None, "probes": None}
    try:
        read = json.loads(done.stdout)
    except ValueError:
        return {"refusal": f"unreadable stdout: {done.stdout[:200]!r}",
                "failures": None, "probes": None}
    return {"refusal": None, "failures": read["failures"], "probes": read["probes"]}


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
            # TWO READINGS OVER ONE FOLDER, and the pair is the diagnosis. In-process is what
            # the LOOP sees; fresh is what the DISK says. They agree on a real defect and
            # disagree on a stale loop, so neither one alone can tell the two apart.
            fresh = (fresh_import_reading(entry["folder"]) if entry
                     else {"refusal": "not on disk", "failures": None, "probes": None})
            verdicts[device_id] = {
                "on_disk": entry is not None,
                "imports_cleanly_in_this_process": bool(entry) and not entry["failures"],
                "imports_cleanly_fresh": fresh["refusal"] is None and not fresh["failures"],
                "fresh_refusal": fresh["refusal"],
                "failures": (entry or {}).get("failures", []),
                "fresh_failures": fresh["failures"],
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
    # THE DECIDING READING IS THE FRESH ONE (see fresh_import_reading): the in-process read
    # is taken by the process under suspicion, so it reproduces a stale loop's own failure
    # and reads a misattributed bench as a real defect.
    wrongly = sorted(d for d, v in survey["verdicts"].items() if v["imports_cleanly_fresh"])
    # The signature of THE LOOP being the culprit rather than the device: the failure is real
    # here and absent on disk. A device that imports cleanly in both was benched for
    # something else entirely (a cleared-but-not-swept ticket, say) and says so by absence.
    stale_signature = sorted(d for d, v in survey["verdicts"].items()
                             if v["imports_cleanly_fresh"]
                             and not v["imports_cleanly_in_this_process"])
    unreadable = sorted(d for d, v in survey["verdicts"].items() if v["fresh_refusal"])
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
        "reproduces_here_but_not_fresh": stale_signature,
        "fresh_reading_refused": unreadable,
        "benched_total": len(survey["benched"]),
        "self_trouble_live": survey["self_trouble_live"],
        "condition_ever_recorded": bool(last_seen),
        "condition_last_seen": last_seen,
        "survived_a_restart": survived_a_restart,
        "process_started": started,
        "drifted_modules": [f["module"] for f in diagnostics["drifted"]],
        "undecidable_modules": diagnostics["undecidable"],
        "coverage": diagnostics.get("coverage"),
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
                   "probe folder imports cleanly in a FRESH interpreter right now — so the "
                   "ticket is describing "
                   "the loop's own age, not the device's defect, and every watch in that "
                   "folder is dark for as long as it stands",
        "benched_but_importing": s["benched_but_importing"],
        "reproduces_here_but_not_fresh": s["reproduces_here_but_not_fresh"],
        "fresh_reading_refused": s["fresh_reading_refused"],
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
        "also_watches": owning_ticket(_ALSO_WATCHES),
        "coverage": s.get("coverage"),
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

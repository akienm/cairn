"""aider_shim_reflection_earns_its_ask — the second ask costs real tokens. Does it BUY anything?

THE TICKET'S WATCHME, COMPILED. The spec
(CairnCommons/tickets/the-apprentice-learns-its-test-failed.json) names this exact path, and
the emission gate resolves ARMED from it, so this module is what stands between the WATCHME
crossing and a refusal. Its fields are that spec's, kept in the spec's own words where they
are the answer:

  trigger  — "every drive recorded to ~/.cairn/devices/aider_shim/0/drives.jsonl — the
             driver's own record write is the event that already fires, and nothing polls.
             The probe reads the row's num_reflections against its asks and its test
             outcome, so a drive that never reflected is a data point too rather than a gap"
  enough   — "when five drives carrying num_reflections >= 1 have been recorded AND their
             applied-and-passing rate has a consistent relationship to the unreflected
             baseline drawn from the same file", with two stop-early falsifiers (below)
  carrier  — per drive: num_reflections, the ask count and each ask's prompt_eval_count,
             whether the second ask carried the test's failure text, the drive's test
             outcome, and the survival disposition of the files it touched
  nexus    — the hypothesize tree, the same one aider_shim_offload_yield and
             aider_shim_edit_survival deposit to — deliberately, so the three watches answer
             their different questions over ONE drives.jsonl population
  consumer — Akien at triage (reflection multiplies asks against a metered host, so "it
             helps" and "it helps enough" are different answers and only he settles the
             second); and CC, who is the party that would otherwise read num_reflections as
             convergence — the exact misreading that bore this ticket

WHY THIS IS NOT EITHER SIBLING'S QUESTION. `aider_shim_offload_yield` asks whether the build
PASSED. `aider_shim_edit_survival` asks WHO EARNED the pass. This one asks what the EXTRA
ASKS bought — a question neither can see, because both read a drive as one event and this
one reads it as a sequence of attempts. Before 2026-08-18 the question could not be asked at
all: `auto_test=False` meant a failing test never reached the model, and `num_reflections: 0`
read identically for "converged on the first try" and "nothing could ever have reached it".

THREE THINGS THE RECORD CANNOT ANSWER CLEANLY, NAMED HERE RATHER THAN PAPERED OVER.

(1) DID THE SECOND ASK CARRY THE FAILURE TEXT? The fence records `ask_chars`, never the
    prompt — deliberately, so the ask log cannot become a place model payloads accumulate.
    So the containment check the spec asks for is not readable from this file, and this
    probe does NOT pretend otherwise. What IS readable is a ONE-SIDED NECESSARY CONDITION:
    the reflected ask re-sends the whole conversation plus the test output, so its
    `ask_chars` must exceed the previous ask's by at least the length of the failure text.
    If that fails, the failure text certainly did not ride, and the falsifier fires. If it
    holds, nothing is proved — the word carried is `consistent`, never `carried`. A
    one-sided instrument that can only falsify is worth more than a two-sided one that can
    also go green for the wrong reason (which is how a whole-record substring scan passes).
    The containment itself IS measured, at the fixture layer, by
    `proofs/test_driver.py::test_the_second_ask_carries_the_tests_own_failure`, through a
    seam that transcribes what it was asked. Live, it is an owed instrument, not a mystery
    (Law 10: "we have not built the measurement yet" is an ordinary state).

(2) IS A REFLECTED ASK A SECOND OPINION, OR A CACHE HIT? `prompt_eval_count` is None on a
    hit — no call was made, so there is no count. A byte-identical hit has already been
    misread as determinism once in this very population, so a reflected ask that never
    reached the host is counted apart and never toward the yield.

(3) DID THE DRIVE END WORSE THAN ITS FIRST ATTEMPT LEFT IT? The spec names this state and
    the edit-survival probe's four-way vocabulary has no word for it. Neither does the
    record: the driver images the files ONCE before the drive and ONCE after, so the
    intermediate state after attempt 1 was never taken and cannot be computed later. What
    this probe reports instead is the RECORD-VISIBLE SHOULDER of that state —
    `left-changed-and-failing`: the drive moved bytes, got its extra turns, and still ends
    red. That is a SUPERSET of the spec's state (a drive that was already failing and did
    not get worse also lands in it), so it OVER-fires rather than under-fires. That is the
    right side to err on for a stop-early falsifier: its consequence is "a human looks",
    never "the watch retires". The per-attempt image that would narrow it is an owed
    ticket, not a thing this probe should mint a second opinion about.

A PROBE CARRIES NO AUTHORITY (Law 6). This reads `drives.jsonl` and the working tree, and
writes nothing anywhere. It deposits and pokes; re-opening a node whose intention did not
work is the owner's act.
"""

from __future__ import annotations

from cairn.tools.base.probe import Probe

TICKET = "the-apprentice-learns-its-test-failed"

#: The spec's stop-early threshold and its retire threshold, named once so a reader cannot
#: find two different fives in this file.
_ENOUGH_REFLECTED = 5


def _identity(rec: dict) -> tuple:
    """A drive's own identity, minted by the driver at drive time.

    ONE DRIVE APPENDED TWICE IS STILL ONE DRIVE — observed at n=1 in this very store, where
    a live-fire caller called `driver.record` on a result `drive_brief` had already recorded
    and four rows carry byte-identical `at`. `enough` is a count, so a duplicated row would
    retire this watch early. Same collapse as the sibling probe's, on purpose: the two read
    one population and must agree about how many drives are in it.
    """
    return (rec.get("ticket"), rec.get("piece_index"), rec.get("at"))


def _failure_text(rec: dict) -> str:
    """The drive's own test failure, as the record holds it — the text a reflection feeds back.

    Read from the PARENT's test run (`DriveResult.test`), which is the record's authority on
    whether the piece passed. aider ran its own copy inside the drive and that output is what
    actually rode the reflection; nothing captures it. The two are the same command in the
    same tree, so the parent's text is the closest available stand-in for the length bound in
    (1) — and being a stand-in is exactly why the verdict word is `consistent` and not
    `carried`.
    """
    test = rec.get("test") or {}
    if test.get("passed") is not False:
        return ""
    return ((test.get("stderr") or "") + (test.get("stdout") or "")).strip()


def _ask_carriage(rec: dict) -> str | None:
    """`no` | `consistent` | None — the one-sided necessary condition of (1).

    `no` is a MEASUREMENT and fires the falsifier: the second ask was not big enough to be
    holding the failure text, so it is not. `consistent` is the absence of that measurement,
    never its opposite. None means the question does not arise — no reflection, no second
    ask, or a passing test with no failure text to carry.
    """
    asks = rec.get("asks") or []
    if int(rec.get("num_reflections") or 0) < 1 or len(asks) < 2:
        return None
    text = _failure_text(rec)
    if not text:
        return None
    first, second = asks[0].get("ask_chars") or 0, asks[1].get("ask_chars") or 0
    return "consistent" if second - first >= len(text) else "no"


def _cached_asks(rec: dict) -> int:
    """Asks the fence allowed that never reached the host — see (2). A hit has no count."""
    return sum(1 for a in (rec.get("asks") or [])
               if a.get("verdict") == "allowed" and a.get("prompt_eval_count") is None)


def _live_reflected_asks(rec: dict) -> int:
    """Asks AFTER THE FIRST that actually reached the host — the second opinions, counted.

    THE POSITION IS THE WHOLE POINT, and it is a scar one tooth deep. The first version of
    this asked whether the drive had more allowed asks than cached ones, which is a
    statement about the drive and not about the reflection: a live first ask and a CACHED
    second one satisfies it, and the extra turn — the only thing this watch is about —
    bought nothing at all. Five such drives would have retired the watch. Slicing from
    index 1 asks the question that was meant: did the RE-ask reach the host?
    """
    return sum(1 for a in (rec.get("asks") or [])[1:]
               if a.get("verdict") == "allowed" and a.get("prompt_eval_count") is not None)


def _outcome(rec: dict) -> str:
    """One word for what the drive left behind, in this watch's own vocabulary.

    `applied-and-passing` is the thing the yield comparison counts. `left-changed-and-failing`
    is the shoulder of the spec's self-cancelling state (3) and fires the falsifier.
    `no-edit` separates "the apprentice is not producing" from "the apprentice is being
    overruled" — the same distinction the sibling probe refuses to collapse.
    """
    if rec.get("error"):
        return "refused"
    edited = rec.get("aider_reported_edited") or []
    moved = [rel for rel, was in (rec.get("before") or {}).items()
             if (rec.get("after") or {}).get(rel) != was]
    passed = (rec.get("test") or {}).get("passed")
    if not edited and not moved:
        return "no-edit"
    if passed is True:
        return "applied-and-passing"
    if passed is False:
        return "left-changed-and-failing"
    return "applied-untested"


def readings(*, drives_path=None) -> list[dict]:
    """One row per drive, oldest first, in this watch's vocabulary. Composed, never re-derived.

    Reads through `driver.drives` — this module owns no second opinion about what a drive
    record is, which is what keeps it from drifting away from the two probes reading the same
    file.
    """
    from cairn.devices.aider_shim import driver  # noqa: PLC0415

    rows, seen = [], set()
    for rec in driver.drives(drives_path if drives_path is not None else driver.DEFAULT_DRIVES):
        ident = _identity(rec)
        if ident in seen:
            continue
        seen.add(ident)
        asks = rec.get("asks") or []
        rows.append({
            "ticket": rec.get("ticket"),
            "piece_index": rec.get("piece_index"),
            "at": rec.get("at"),
            "model": rec.get("model"),
            "num_reflections": int(rec.get("num_reflections") or 0),
            "max_reflections": int(rec.get("max_reflections") or 0),
            "asks": len(asks),
            "allowed_asks": sum(1 for a in asks if a.get("verdict") == "allowed"),
            "cached_asks": _cached_asks(rec),
            "live_reflected_asks": _live_reflected_asks(rec),
            "prompt_eval_counts": [a.get("prompt_eval_count") for a in asks],
            "second_ask_carriage": _ask_carriage(rec),
            "test_passed": (rec.get("test") or {}).get("passed"),
            "outcome": _outcome(rec),
            "error": rec.get("error") or "",
        })
    return rows


def _reflected(rows: list[dict]) -> list[dict]:
    """The drives that actually reflected, and did so with a live second ask.

    A reflection whose extra ask was a cache hit (2) bought no second opinion, so it does not
    count toward `enough`. Five cached reflections would retire this watch having learned
    nothing — the same hollow stop the sibling probes' `enough` refuses.
    """
    return [r for r in rows
            if r["num_reflections"] >= 1 and r["live_reflected_asks"] >= 1]


def falsifications(rows: list[dict]) -> list[dict]:
    """The spec's two stop-early observations, each with the drive that bore it.

    Reported whether or not `enough` is satisfied: a falsifier that only speaks at the end is
    not a stop-EARLY falsifier. Each carries `over_fires` where the instrument is a superset
    of the state it stands for, so the reader can tell an alarm from a proof.
    """
    out = []
    for r in rows:
        if r["num_reflections"] >= 1 and r["outcome"] == "left-changed-and-failing":
            out.append({
                "which": "ended-worse-shoulder", "at": r["at"], "ticket": r["ticket"],
                "piece_index": r["piece_index"],
                "says": "a reflected drive moved bytes, spent its extra turns and still ends "
                        "red — the record-visible shoulder of the self-cancelling state",
                "over_fires": "a drive already failing before the reflection lands here too; "
                              "the per-attempt image that would separate them is not taken",
            })
        if r["second_ask_carriage"] == "no":
            out.append({
                "which": "failure-text-did-not-ride", "at": r["at"], "ticket": r["ticket"],
                "piece_index": r["piece_index"],
                "says": "the second ask was too small to be holding the test's failure text, "
                        "so the mechanism reported firing while feeding the apprentice nothing",
                "over_fires": "",
            })
    return out


def _yield_compare(rows: list[dict]) -> dict:
    """Reflected vs unreflected applied-and-passing rate, over the one population.

    Rates only, never a verdict: whether the difference is worth the tokens is Akien's call
    at triage, and a probe that answered it would be exercising authority it does not have.
    """
    def rate(group):
        counted = [r for r in group if r["outcome"] != "refused"]
        passing = [r for r in counted if r["outcome"] == "applied-and-passing"]
        return {"drives": len(counted), "applied_and_passing": len(passing),
                "rate": (len(passing) / len(counted)) if counted else None}

    reflected = _reflected(rows)
    ident = {(r["ticket"], r["piece_index"], r["at"]) for r in reflected}
    baseline = [r for r in rows if (r["ticket"], r["piece_index"], r["at"]) not in ident]
    return {"reflected": rate(reflected), "unreflected_baseline": rate(baseline)}


def _trigger(now=None, context=None) -> bool:
    """True when a drive has been recorded that this watch has not read yet.

    NOT A POLL. The driver's `record` write is the event that already fires; this asks
    whether that event left something new behind. The count rides `context` because a Probe
    is frozen and holds no state, and the anti-bounce default means a standing population
    pokes once, at the crossing.
    """
    context = context or {}
    return len(readings(drives_path=(context or {}).get("drives_path"))) > int(
        (context or {}).get("seen", 0))


def _carry(context=None) -> dict:
    context = context or {}
    rows = readings(drives_path=context.get("drives_path"))
    reflected = _reflected(rows)
    bad = falsifications(rows)
    return {
        "ticket": TICKET,
        "drives": len(rows),
        "reflected": len(reflected),
        "needed": _ENOUGH_REFLECTED,
        "status": ("enough" if len(reflected) >= _ENOUGH_REFLECTED
                   else f"not enough yet: {len(reflected)} of {_ENOUGH_REFLECTED} reflected "
                        f"drives across {len(rows)} recorded"),
        "yield": _yield_compare(rows),
        "falsifications": bad,
        "stop_early": bool(bad),
        "rows": rows,
        "holes": {
            "second_ask_carriage": "one-sided — `no` is measured, `consistent` is not proof. "
                                   "The fence records ask_chars, never the prompt; the "
                                   "containment is measured at the fixture layer by "
                                   "proofs/test_driver.py::"
                                   "test_the_second_ask_carries_the_tests_own_failure.",
            "ended_worse": "a superset alarm — the driver images the files once before and "
                           "once after the whole drive, so the state after attempt 1 was "
                           "never taken and cannot be computed later.",
        },
        "reads": "`applied-and-passing` is what the extra ask is supposed to buy. "
                 "`left-changed-and-failing` is what it may instead cost. `no-edit` is "
                 "neither — the apprentice produced nothing, which is a different finding "
                 "and a different decision.",
    }


def _enough(context=None) -> bool:
    """Five reflected drives with a live second ask — the spec's number, unlowered.

    The yield comparison the spec also names is CARRIED, not gated on: 'a consistent
    relationship to the unreflected baseline' is a judgement the consumer makes, and a probe
    that graded it would be deciding for him. The falsifiers do not retire the watch either —
    they are stop-EARLY signals, and stopping early is the owner's act (Law 6).
    """
    context = context or {}
    return len(_reflected(readings(drives_path=context.get("drives_path")))) >= _ENOUGH_REFLECTED


#: Honest as a placeholder, dishonest as a measurement — the same tracked debt every sibling
#: probe carries: nothing pulses this shim yet, so loudness rides BaseShim.overdue() alone.
_HORIZON = 1000

PROBE = Probe(
    why="the fix that made a failing test reach the apprentice also made every failing drive "
        "cost a second ask against a metered host, and nothing in the record says whether "
        "that buys anything. Worse, the loop could actively manufacture harm: giving a "
        "copying apprentice more turns to copy is how a drive ends worse than its first "
        "attempt left it. This watch reads reflected drives against the unreflected baseline "
        "in the same file, separates a real second opinion from a cache hit, and fires early "
        "and loudly on either falsifier — so 'it helps' and 'it helps enough' stay two "
        "questions, and Akien settles the second.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "reflection-yield", "ticket": TICKET,
          "consumer": "Akien at triage — reflection multiplies asks against a metered host, "
                      "so offload-more vs pull-back is his call; and CC, who is the party "
                      "that would otherwise read num_reflections as convergence"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

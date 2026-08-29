"""PROBE — an intention has been retired; did the fleet find out, and did anything escape?

Berth for the WATCHME that ticket ``a-superseded-intention-is-never-silent`` carries
(object ``a_superseded_intention_is_never_silent``). It berths beside
``cairn/devices/cairn/machines/harbor_master`` because that is WHAT IT WATCHES: the retirement key is read
in ``clearance.retirement_of``, the refusal is raised in ``clearance._decide``, and the
reverse read that is supposed to have warned the retiring hand is ``clearance.riders_of``.
The ticket itself sits in the commons; the instrument sits at the seam it measures.

WHAT THIS EXISTS TO CATCH, and it is not "does the code work" — the proof answers that, and
it is sealed. This watch answers whether the mechanism was ever LOAD-BEARING. Three ways it
lands built and hollow, and each is a clause of the ticket's own falsifier:

  (a) AN ESCAPE. A boat naming a retired intention made a forward journaled crossing at or
      after that retirement's ``when``. The refusal is supposed to make that impossible, so
      one such record is the whole finding — no sample needed, because a single escape says
      the gate was walked around or never consulted.
  (b) A RETIREMENT NOBODY COULD READ. A charter carrying the key in a shape
      ``retirement_of`` refuses (``RetirementUnreadable``). The dangerous half of this is
      not the refusal — it is that until this probe counts them, a malformed retirement is
      a charter that LOOKS retired to a human reader and is not retired to the gate.
  (c) A CLEAN REPORT OVER A BLIND CORPUS THAT WAS THEN PROVED BLIND. The gate refused a boat
      whose id the retiring hand's scan had NOT listed as riding. That is the ticket's
      named hollow — "no boats riding, clear to supersede" — caught in the act, and the
      ticket's ``enough`` calls it an EARLY STOP rather than a mere finding, because it
      converts the unattributed backlog from a chore into the next build.

WHY THE BLIND COUNT IS NOT A TRIGGER CLAUSE. The counts are non-zero today (40 unattributed,
7 unresolvable, 3 unreadable, measured 2026-08-18) and will be non-zero for a long time. A
probe firing on that would fire on every pulse forever and teach nothing — the counts are
carried in every payload instead, which is where a standing condition belongs. What IS a
trigger is the count being proved WRONG by a refusal, which is clause (c).

WHY THERE IS NO ERA FLOOR CONSTANT HERE, unlike the sibling ``clearance_actually_gates``.
Its floor is a date somebody had to pick, because the gate it watches began demanding at a
moment nothing recorded. This one needs no such number: each retirement carries its own
``when``, so the floor is per-retirement and READ rather than set. A crossing before a
retirement is not an escape, and the record says so itself.

WHAT THIS PROBE CANNOT SEE, stated because a silent watch and a healthy system read alike.
It counts escapes among boats it can ATTRIBUTE. A boat with no ``owning_intention`` that
should have named the retired intention is invisible to clause (a) exactly as it is
invisible to the scan — the blindness is the same blindness, and the payload carries the
counts beside every finding so a consumer can never read a zero as coverage.

FILES ONLY (charters, tickets, class-space histories) plus the gate's own trace queue,
which is a local file. No device, no bus, no network — cheap enough to sit on a pulse.

AUTHORITY: none. This probe deposits and pokes. Ending a riding boat, re-parenting it onto
the successor, or letting it through anyway is the OWNER's act (Law 6), and the ticket says
so at cast: "the refusal is a stop, not a verdict on the work."
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket
from cairn.devices.cairn.machines.harbor_master.clearance import (
    CAIRN_ROOT, COMMONS_ROOT, REFUSED, RetirementUnreadable,
    read_attempts, retirement_of, riders_of,
)

_REPO_ROOT = Path(CAIRN_ROOT)
_COMMONS = Path(COMMONS_ROOT)

_OWNING_TICKET = "a-superseded-intention-is-never-silent"

# The ticket's own ``enough``, transcribed rather than freshly chosen: "three live
# supersessions". Three because a supersession of an intention with zero boats proves
# nothing about the interesting case. A hand-set constant in a gate is a learns-its-gates
# IOU; this one is owed to the ticket that set it, and the ticket is named right here.
_ENOUGH_RETIREMENTS = 3

# How many escapes ride back verbatim. NOT a silent cap: the payload states the window and
# the total beside it, so a consumer can never mistake the tail for the whole.
_VERBATIM = 20

# The refusal class the gate raises for a retired intention. Spelled once, here, and
# compared against what ``clearance`` actually records — a probe carrying its own copy of a
# writer's vocabulary is a probe that silently stops matching and then reports zero, which
# is the wrong answer to be confident about.
_RETIRED_REASON = "IntentionRetired"


def _charters() -> list[Path]:
    """Every authored charter in both roots. ``intention+why.json`` beside code in
    class-space, and the homeless intentions in the commons — the two places CLAUDE.md says
    an intention can berth, walked in that order so the report reads in root order."""
    found: list[Path] = []
    for root in (_REPO_ROOT, _COMMONS):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("intention+why.json")):
            if ".git" in path.parts:
                continue
            found.append(path)
    return found


def survey_the_retirements() -> dict:
    """Every charter carrying the retirement key, with who rides it NOW and what the read
    could not see — the same three blind classes the retiring hand was shown.

    The reading is the gate's own (``retirement_of``, ``riders_of``); only the walk and the
    counting are here. That split is Law 1: a second opinion about what "retired" means is
    a second implementation of a settled question, and the day the two disagree this probe
    reports the comforting one."""
    retired: list[dict] = []
    unreadable: list[dict] = []

    for path in _charters():
        try:
            charter = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue                     # a charter this probe cannot parse is not a finding
        if not isinstance(charter, dict):
            continue
        rel = os.path.relpath(str(path), str(_REPO_ROOT))
        try:
            mark = retirement_of(charter, at=rel)
        except RetirementUnreadable as exc:
            # CLAUSE (b). Loud, and never collapsed into "not retired" (Law 7) — that
            # collapse is the whole reason the reader raises instead of returning None.
            unreadable.append({"charter": rel, "why": str(exc)})
            continue
        if mark is None:
            continue
        riders = riders_of(rel)
        retired.append({
            "charter": rel,
            "superseded_by": mark.superseded_by,
            "when": mark.when,
            "evidence": mark.evidence,
            "riding": list(riders.riding),
            "blind": riders.blind,
            "in_flight": riders.in_flight,
            "attributable": riders.attributable,
        })

    return {"retirements": retired,
            "retirements_seen": len(retired),
            "unreadable_retirements": unreadable,
            "charters_walked": len(_charters())}


def survey_the_escapes(retirements: list[dict]) -> list[dict]:
    """CLAUSE (a): forward journaled crossings made AT OR AFTER a retirement's ``when`` by a
    boat that names the retired intention.

    Each escape rides back verbatim with its component, seq, actor, date and the retirement
    it walked past, so the consumer never re-derives them (the complete-diagnostic rule: the
    first report carries everything needed to resolve the finding)."""
    if not retirements:
        return []
    by_boat: dict[str, list[dict]] = {}
    for mark in retirements:
        for boat in mark["riding"]:
            by_boat.setdefault(boat, []).append(mark)
    if not by_boat:
        return []

    escapes: list[dict] = []
    for hist in sorted(_REPO_ROOT.rglob("history.json")):
        if ".git" in hist.parts:
            continue
        try:
            records = json.loads(hist.read_text(encoding="utf-8"))
        except Exception:                # noqa: BLE001 — same posture as the sibling probe
            continue
        if not isinstance(records, list):
            continue
        component = os.path.relpath(str(hist.parent), str(_REPO_ROOT))
        for rec in records:
            if not isinstance(rec, dict) or rec.get("direction") != "forward":
                continue                 # a retreat is exempt BY DESIGN — the wall is not a gate
            marks = by_boat.get(str(rec.get("ticket") or ""))
            if not marks:
                continue
            at = str(rec.get("at") or "")
            for mark in marks:
                if at and at >= mark["when"]:
                    escapes.append({"component": component, "seq": rec.get("seq"),
                                    "at": at, "actor": rec.get("actor"),
                                    "to": rec.get("to"), "ticket": rec.get("ticket"),
                                    "walked_past": mark["charter"],
                                    "retired_at": mark["when"]})
    return escapes


def survey_the_refusals(retirements: list[dict]) -> dict:
    """CLAUSE (c): retirement refusals the gate actually recorded, split by whether the
    scan had NAMED the boat it refused.

    A refusal on a boat the scan listed is the mechanism working end to end. A refusal on a
    boat the scan did NOT list is the blindness being real — the ticket's early stop, and
    the strongest single observation this watch can make."""
    named, missed, unreadable_lines = [], [], 0
    listed: set[str] = set()
    for mark in retirements:
        listed.update(mark["riding"])
    try:
        queue = read_attempts()
    except Exception as exc:             # noqa: BLE001 — an unreadable queue is a fact, not a crash
        return {"queue": None, "unreadable": str(exc), "refusals": 0,
                "on_a_named_boat": [], "on_a_boat_the_scan_MISSED": []}
    unreadable_lines = queue.get("unreadable_lines", 0)
    for attempt in queue["attempts"]:
        if attempt.get("event") != REFUSED:
            continue
        if attempt.get("reason_type") != _RETIRED_REASON:
            continue
        boat = str(attempt.get("boat_id") or "")
        (named if boat in listed else missed).append(attempt)
    return {"queue": queue["queue"],
            "refusals": len(named) + len(missed),
            "on_a_named_boat": named[-_VERBATIM:],
            "on_a_boat_the_scan_MISSED": missed[-_VERBATIM:],
            "unreadable_lines": unreadable_lines}


def survey() -> dict:
    """The whole reading, once — so trigger, enough and carry cannot disagree about the
    world by each taking their own."""
    marks = survey_the_retirements()
    escapes = survey_the_escapes(marks["retirements"])
    refusals = survey_the_refusals(marks["retirements"])
    return {**marks,
            "escapes": escapes[-_VERBATIM:],
            "escapes_total": len(escapes),
            "refusals": refusals}


def _blindness_was_proved_real(s: dict) -> bool:
    """The early stop: the gate refused a boat the scan had not listed as riding."""
    return bool(s["refusals"].get("on_a_boat_the_scan_MISSED"))


def _trigger(now, context: dict) -> bool:
    s = context.get("survey") or survey()
    return bool(s["escapes_total"]
                or s["unreadable_retirements"]
                or _blindness_was_proved_real(s))


def _enough(context: dict) -> bool:
    """CLEARED when the ticket's horizon is met: three live retirements observed, no escape
    among them, and no unreadable retirement standing.

    EARLY STOP at one, if that one showed the refusal firing on a boat the scan had missed —
    the ticket's own clause, transcribed. That is not the watch giving up: it is the watch
    having learned the most important thing it could learn, which is that the blind count is
    not a courtesy. Acting on it is the owner's call at the register.

    NOT MUTUALLY EXCLUSIVE WITH THE TRIGGER BY ACCIDENT — by construction. Every trigger
    clause except the early stop appears here negated, and the early stop appears in both
    deliberately: it FIRES (so the finding is delivered) and it CLEARS (so the watch stops),
    in that order, because ``enough`` is asked only after a fire."""
    s = context.get("survey") or survey()
    if _blindness_was_proved_real(s):
        return True
    return (s["retirements_seen"] >= _ENOUGH_RETIREMENTS
            and not s["escapes_total"]
            and not s["unreadable_retirements"])


def _carry(context: dict) -> dict:
    s = context.get("survey") or survey()
    which = []
    if s["escapes_total"]:
        which.append("(a) %d forward crossing(s) landed at or after the retirement of an "
                     "intention the boat NAMES — the refusal did not stand in the way, so "
                     "either the crossing did not go through clearance or the key was "
                     "written after the boat had already passed" % s["escapes_total"])
    if s["unreadable_retirements"]:
        which.append("(b) %d charter(s) carry a retirement key the reader REFUSES — a "
                     "charter that looks retired to a human and is not retired to the gate"
                     % len(s["unreadable_retirements"]))
    if _blindness_was_proved_real(s):
        which.append("(c) the gate refused a boat the retiring hand's scan had NOT listed "
                     "as riding — the blind count is not a courtesy, it is the finding, and "
                     "the unattributed backlog is now the next build rather than a chore")
    return {"finding": "an intention can now be retired in a shape the gate reads, and the "
                       "question is whether that ever stood in anything's way — "
                       + (" / ".join(which) or "no condition fired"),
            "conditions_fired": which,
            "survey": s,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket demands three things of a live supersession: "
                                 "(a) the riding boat's next forward crossing REFUSES, "
                                 "naming the supersession and the successor; (b) the "
                                 "deprecation-time scan names that boat; (c) that scan "
                                 "reports how many in-flight tickets it could NOT attribute. "
                                 "Any of the three missing kills it.",
            "suggests": "read survey.retirements — each row carries its riders AND its three "
                        "blind counts, and a clean 'riding: []' means nothing while those are "
                        "non-zero. For (a), each escape names the component, seq and actor "
                        "that made it; a crossing that reached emit without clearance is a "
                        "finding at THAT caller, not in the gate. Ending or re-parenting a "
                        "riding boat is the owner's act (Law 6) — this probe decides none of "
                        "it."}


# THE HORIZON (falsifier clause: armed, correct, and silent is indistinguishable from
# health without one). Same placeholder and same tracked debt as every sibling: the beat
# rate is not yet a real number, so 1000 pulses is "clearly a long standing" and MUST be
# re-tuned when it becomes one. It is longer than this watch expects to wait — a retirement
# is a rare deliberate act, not a rate — and that is the point of stating it.
_HORIZON = 1000

PROBE = Probe(
    why="an intention can be marked retired and the gate refuses boats that ride it — but "
        "a mechanism built and never leaned on is indistinguishable from one that works. "
        "An escape past a retirement, a retirement no reader can parse, or a refusal on a "
        "boat the scan never saw are the three ways it lands built and hollow",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the whole reading, and what the pair would do with it now.
    s = survey()
    print(json.dumps({"survey": s,
                      "would_trigger": _trigger(None, {"survey": s}),
                      "enough": _enough({"survey": s})}, indent=2, default=str))

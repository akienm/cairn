"""PROBE — the owner is READ off the boat now; does the refusal actually bind anything?

Berth for the WATCHME that ticket ``boat-owner-is-read-not-stated`` carries (object
``boat-owner-comes-from-the-boat``). Berthed beside ``cairn/harbor_master`` because that
is WHAT IT WATCHES: harbor_master owns the authority rung, and Law 6 says the back-edge
that re-opens this node is the OWNER's act, never the probe's.

THE FAILURE THIS EXISTS BECAUSE OF. Until 2026-08-10 ``clear()`` took ``boat_owner`` as
an argument and compared it to ``actor`` — both supplied by the same caller in the same
call. A caller that states both sides of an identity check can always make them equal, so
the Law 6 refusal bound an honest caller and nothing else. The read now goes to disk:
``boat_id -> tickets/<id>.json -> owning_intention -> charter -> gated_by``. That is a
build; whether it made the refusal BIND is a claim about an outcome, and this is the
instrument for it.

THE HARD PART, AND WHY THIS PROBE'S ``enough`` CANNOT BE BOUGHT WITH VOLUME. Everything
in this system is presently moved by one hand. A gate that admits exactly that hand and a
gate that admits everyone are INDISTINGUISHABLE while only that hand ever crosses — a
thousand clean crossings by ``CC`` say nothing about whether the read discriminates. So
``enough`` requires a SECOND DISTINCT ACTOR on a cleared crossing, and no quantity of
same-hand crossings can reach it. Falsifier clause (3) — "every boat's owner resolves to
the same string, the check vacuous by a longer route" — is the same observation pointed
the other way, and it is condition (b) below.

WHAT IT RE-DERIVES RATHER THAN TRUSTS. The record carries ``cleared_by`` and ``actor``;
it does NOT carry the owner the gate resolved. So condition (a) re-resolves each crossing's
boat from disk and asks whether the recorded actor is one the boat's own intention admits.
Re-resolving is the point: a record that carried the resolved owner would be the gate
grading its own homework, and drift between what the gate did and what the boat now says
is exactly the thing worth catching.

TWO WAYS A RE-RESOLUTION CAN COME BACK EMPTY, AND THEY ARE NOT THE SAME. A boat whose
owner cannot be resolved TODAY is reported as ``unresolvable`` and is NOT a finding — the
corpus is deliberately not back-filled, so most tickets have no ``owning_intention`` and
saying so about a crossing made before the field existed would be a check that fires on
normal motion. A crossing whose actor resolves and is NOT admitted is condition (a), and
one record is enough.

FILES ONLY, by construction: class-space ``history.json`` files under ``cairn/`` plus the
ticket and charter JSON the read itself opens — no device, no bus, no network — cheap
enough to sit on a pulse. Same discipline as its sibling at
``clearance_actually_gates.py``.

AUTHORITY: none. This probe deposits and pokes; acting on the finding is the owner's call
at the register (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.base.probe import Probe, owning_ticket
from cairn.harbor_master.clearance import OwnerUnresolvable, boat_owner_of

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CLASS_SPACE = _REPO_ROOT / "cairn"

_OWNING_TICKET = "boat-owner-is-read-not-stated"

# THE ERA FLOOR — set at arming time, 2026-08-10, between the last crossing made under the
# STATED owner (16:55:29) and this voyage's own crossings, which are the first made under
# the READ one. The two cleared crossings before it were cleared by a gate that compared a
# caller's string to itself; counting them here would be counting the defect as evidence
# about its fix. They are a RECORD OF TRUTH (Law 7) — never rewritten, never backfilled,
# and never counted against a read that did not exist when they were made. A date is
# provenance here — when the read began — not a dial.
_ERA_FLOOR = "2026-08-10T18:00:00"


def survey_the_crossings() -> dict:
    """Census every CLEARED crossing since the era floor, each re-resolved against the boat
    it names, and classified: ``admitted`` (the actor is one the boat's intention admits),
    ``delegated`` (not admitted, but the crossing spent a grant, which is Law 6's second
    clause working as designed), ``not_admitted`` (condition (a) — a finding), or
    ``unresolvable`` (the boat says nothing about who owns it; reported, never a finding).

    Every offending crossing rides back VERBATIM with its component, seq, actor, boat and
    the address the resolution read from, so the consumer never re-derives them (the
    complete-diagnostic rule: a finding delivers everything needed to resolve it in its
    first report)."""
    admitted: list[dict] = []
    delegated: list[dict] = []
    not_admitted: list[dict] = []
    unresolvable: list[dict] = []

    for hist in sorted(_CLASS_SPACE.rglob("history.json")):
        if ".git" in hist.parts:
            continue
        try:
            records = json.loads(hist.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a corpus this probe cannot read is not a finding
            continue
        if not isinstance(records, list):
            continue
        component = str(hist.resolve().parent.relative_to(_REPO_ROOT))
        for rec in records:
            if not isinstance(rec, dict) or not rec.get("cleared_by"):
                continue                                   # not a cleared crossing
            if str(rec.get("at", "")) < _ERA_FLOOR:
                continue                                   # Law 7: the record stands, uncounted
            boat = rec.get("ticket")
            row = {"component": component, "seq": rec.get("seq"), "at": rec.get("at"),
                   "actor": rec.get("actor"), "cleared_by": rec.get("cleared_by"),
                   "to": rec.get("to"), "boat": boat,
                   "delegated": bool(rec.get("delegated"))}
            try:
                owner = boat_owner_of(str(boat))
            except OwnerUnresolvable as exc:
                unresolvable.append({**row, "why": str(exc)})
                continue
            row = {**row, "owning_intention": owner.intention, "admits": list(owner.hands)}
            if rec.get("actor") in owner.hands:
                admitted.append(row)
            elif row["delegated"]:
                delegated.append(row)
            else:
                not_admitted.append(row)

    counted = admitted + delegated + not_admitted
    actors = sorted({str(r["actor"]) for r in counted})
    owners = sorted({str(r["owning_intention"]) for r in counted})
    return {"era_floor": _ERA_FLOOR,
            "cleared_since_floor": len(counted) + len(unresolvable),
            "resolved_total": len(counted),
            "admitted": admitted,
            "delegated": delegated,
            "not_admitted": not_admitted,
            "unresolvable": unresolvable,
            "distinct_actors": actors,
            "distinct_owning_intentions": owners}


# The sample below which SILENCE cannot be judged. It bounds condition (b) and the
# ``resolved_total`` half of ``enough`` — never the second-actor half, which is a kind of
# evidence and not an amount of it. Transcribed from the sibling watch's floor (the ticket's
# own "the next 20 journaled crossings") so the two watches on this one gate do not develop
# separate opinions about what a sample is. A hand-set constant in a gate is a
# learns-its-gates IOU; this one is owed to the ticket that set it.
_ENOUGH_CROSSINGS = 20


def _the_read_did_not_bind(s: dict) -> bool:
    """Condition (a). A cleared crossing whose actor is not admitted by the boat it names
    and which spent no grant: the read was bypassed, or the boat has moved underneath it.
    NO SAMPLE FLOOR — one record proves it, and waiting for twenty would be waiting to
    confirm what the first already showed."""
    return bool(s["not_admitted"])


def _vacuous_by_a_longer_route(s: dict) -> bool:
    """Condition (b), the ticket's falsifier clause (3). Enough crossings have resolved and
    every one of them landed on the SAME owning intention AND the same single actor — the
    read runs, costs something, and cannot have discriminated, because it has never once
    been asked about a different answer.

    BOTH halves are required, and that is deliberate: one intention moving many boats is
    ordinary and not a finding, and so is one hand moving boats owned by several
    intentions. It is the pair collapsing to a single point that makes the check
    indistinguishable from a constant. The floor is the same number ``enough`` uses, so the
    trigger and the clear cannot drift apart."""
    return (s["resolved_total"] >= _ENOUGH_CROSSINGS
            and len(s["distinct_owning_intentions"]) <= 1
            and len(s["distinct_actors"]) <= 1)


def _trigger(now, context: dict) -> bool:
    """TRUE on either condition. (a) is the sharp one and has no floor; (b) needs the
    sample and carries it."""
    s = context.get("crossings") or survey_the_crossings()
    return _the_read_did_not_bind(s) or _vacuous_by_a_longer_route(s)


def _enough(context: dict) -> bool:
    """CLEARED when the ticket's HORIZON is met: a crossing made by an actor that is NOT
    the box's single hand, cleared with the owner resolved from the boat, and no
    unbound crossing on record.

    THE SECOND ACTOR IS THE WHOLE CONDITION, and it is why this cannot be bought with
    volume. ``len(distinct_actors) >= 2`` is the ticket's "an actor that is NOT the box's
    single hand" made checkable without hard-coding which hand that is — a hand-set
    constant here would be a learned value stranded in a human's head, and it would also go
    stale the moment a second device is named. Until such a crossing exists the refusal has
    never been observed firing on anything real; the ticket says so in its own falsifier
    rather than leaving it to be discovered later, and this watch stays open saying it.

    MUTUALLY EXCLUSIVE WITH THE TRIGGER BY CONSTRUCTION: (b) requires one distinct actor,
    this requires two; (a) requires an unbound crossing, this requires none."""
    s = context.get("crossings") or survey_the_crossings()
    return (len(s["distinct_actors"]) >= 2
            and s["resolved_total"] >= _ENOUGH_CROSSINGS
            and not s["not_admitted"])


def _carry(context: dict) -> dict:
    s = context.get("crossings") or survey_the_crossings()
    which = []
    if _the_read_did_not_bind(s):
        which.append("(a) a cleared crossing's actor is NOT admitted by the boat it names, "
                     "and no grant was spent — the read was bypassed, or the boat moved "
                     "underneath it. One record is enough")
    if _vacuous_by_a_longer_route(s):
        which.append("(b) %d resolved crossings and every one landed on the same owning "
                     "intention by the same single actor — falsifier clause (3): the check "
                     "vacuous by a longer route, indistinguishable from health"
                     % s["resolved_total"])
    return {"finding": "the owner is read off the boat rather than stated by the caller; "
                       "whether that made the Law 6 refusal BIND is the question, and "
                       + (" / ".join(which) or "no condition fired"),
            "conditions_fired": which,
            "census": s,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket's DONE requires the owner to come from the "
                                 "BOAT, and its HORIZON is the first crossing made by an "
                                 "actor that is NOT the box's single hand — until one "
                                 "exists the refusal has not been observed binding "
                                 "anything real",
            "suggests": "for (a), read the crossings verbatim above — each names the "
                        "component, seq, actor, boat and the hands that boat's intention "
                        "admits; the fix is at the caller or in that intention's "
                        "`gated_by`, not in the gate. For (b), the answer is not more "
                        "crossings: it is a SECOND hand, which is ticket "
                        "an-intention-declares-its-gated-hands and the shim work below it."}


# THE HORIZON (falsifier clause: armed, correct, and silent is indistinguishable from
# health without one). Same placeholder, same tracked debt, as its siblings: the beat rate
# is not yet a real number, so 1000 pulses is "clearly a long standing" and MUST be
# re-tuned when it becomes one.
_HORIZON = 1000

PROBE = Probe(
    why="the owner is now READ off the boat instead of stated by the caller — but every "
        "crossing in this system is made by one hand, and a gate that admits exactly that "
        "hand looks identical to a gate that admits everyone. Fires when a cleared "
        "crossing's actor is not admitted by the boat it names, or when the whole corpus "
        "collapses to one owner and one actor",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the census, and what the pair would do with it right now.
    s = survey_the_crossings()
    print(json.dumps({"census": s,
                      "would_trigger": _trigger(None, {"crossings": s}),
                      "enough": _enough({"crossings": s})}, indent=2))

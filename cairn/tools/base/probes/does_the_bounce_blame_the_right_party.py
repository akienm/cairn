"""PROBE — does the bounce blame the right party?

Berth for the WATCHME that ticket ``every-device-has-a-presence`` (0146df77dae1)
carries. Berthed beside ``cairn/tools/base`` because that is WHAT IT WATCHES:
``shim.py``'s bounce mechanism and the trouble records it eventually produces.

THE EFFICACY QUESTION: when a bounce raises a trouble and that trouble gets
cleared, does the fix land at the SENDER (the one whose message was
undeliverable — the right party to change) or at the RECEIVER (the one who
bounced the message — the innocent party)? A receiver-side majority says the
trouble is raised on the wrong party, which is a spec change, not a tuning
(the ticket's proves_red names this as WRONG INTENT).

TWO POPULATIONS MEASURED TOGETHER:

  (a) BOUNCE-RAISED TROUBLES — trouble records in ``CairnCommons/troubles/``
      whose identity contains "bounce" or whose ``why`` mentions "bounce" (the
      naming convention a bounce-raising mechanism would produce). Currently zero:
      ``handle_bounce`` emits a diagnostic but does not raise a trouble yet.

  (b) CLEARS CLASSIFIED BY FIX LOCATION — for each cleared bounce-raised
      trouble, the ``what_changed`` text from ``cleared_by`` is the raw data.
      Classification uses structural markers in the trouble detail (sender/
      receiver device names) when present, and reports unclassified otherwise.

THE ERA FLOOR: the probe reads only troubles created AFTER the probe was
armed (2026-09-03). Without the era floor, the corpus would include bounces
CC causes and clears inside its own build (the lesson of watchme-emits-a-probe).

FILES ONLY, by construction: the probe walks ``CairnCommons/troubles/`` — a
git-JSON store under the second repo — no device, no bus, no network — so it
stays cheap enough to sit on a pulse.

AUTHORITY: none. This probe deposits and pokes; the back-edge is the owner's
act at the floor (Law 6). The consumer is Akien: the premise under test is his.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "every-device-has-a-presence"

_ERA_FLOOR = "2026-09-03T00:00:00+00:00"

_STALE_DAYS = 14

_ENOUGH_CLEARED = 8
_ENOUGH_SENDER = 6


def _trouble_root() -> Path:
    return Path.home() / "dev" / "src" / "CairnCommons" / "troubles"


def _is_bounce_related(trouble: dict) -> bool:
    identity = trouble.get("id", "")
    why = trouble.get("why", "")
    if "bounce" in identity.lower():
        return True
    if "bounce" in why.lower():
        return True
    for occ in trouble.get("occurrences", []):
        if isinstance(occ, dict) and occ.get("bounce"):
            return True
    return False


def _classify_fix(trouble: dict) -> str:
    cleared_by = trouble.get("cleared_by", [])
    if not cleared_by:
        return "uncleared"
    last_clear = cleared_by[-1]
    what_changed = (last_clear.get("what_changed") or "").lower()
    detail = trouble.get("occurrences", [{}])[0] if trouble.get("occurrences") else {}
    sender = (detail.get("sender") or "").lower()
    receiver = (detail.get("receiver") or "").lower()
    if sender and sender in what_changed:
        return "sender"
    if receiver and receiver in what_changed:
        return "receiver"
    if "sender" in what_changed:
        return "sender"
    if "receiver" in what_changed:
        return "receiver"
    return "unclassified"


def _after_era(trouble: dict) -> bool:
    first_seen = trouble.get("first_seen", "")
    if not first_seen:
        return False
    return first_seen > _ERA_FLOOR


def _age_days(trouble: dict) -> float:
    first_seen = trouble.get("first_seen", "")
    if not first_seen:
        return 0.0
    try:
        born = datetime.fromisoformat(first_seen)
        now = datetime.now(timezone.utc)
        return (now - born).total_seconds() / 86400
    except (ValueError, TypeError):
        return 0.0


def survey_bounce_blame(*, root: Path | None = None) -> dict:
    troubles_root = root or _trouble_root()
    if not troubles_root.exists():
        return {"bounce_troubles": [], "hollow": "the troubles root does not exist"}

    bounce_troubles: list[dict] = []
    for p in sorted(troubles_root.glob("*.json")):
        try:
            t = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(t, dict):
            continue
        if not _is_bounce_related(t):
            continue
        if not _after_era(t):
            continue
        standing = t.get("standing", "OPEN")
        classification = _classify_fix(t) if standing == "CLEARED" else "live"
        age = _age_days(t)
        bounce_troubles.append({
            "id": t.get("id", p.stem),
            "standing": standing,
            "classification": classification,
            "age_days": round(age, 1),
            "count": t.get("count", 0),
            "what_changed": (t.get("cleared_by", [{}])[-1].get("what_changed")
                             if standing == "CLEARED" else None),
            "file": str(p),
        })

    total = len(bounce_troubles)
    cleared = [bt for bt in bounce_troubles if bt["standing"] == "CLEARED"]
    live = [bt for bt in bounce_troubles if bt["standing"] != "CLEARED"]
    sender_fixes = [bt for bt in cleared if bt["classification"] == "sender"]
    receiver_fixes = [bt for bt in cleared if bt["classification"] == "receiver"]
    unclassified = [bt for bt in cleared if bt["classification"] == "unclassified"]
    stale = [bt for bt in live if bt["age_days"] > _STALE_DAYS]

    return {
        "bounce_troubles": bounce_troubles,
        "total": total,
        "cleared": len(cleared),
        "sender_fixes": len(sender_fixes),
        "receiver_fixes": len(receiver_fixes),
        "unclassified": len(unclassified),
        "live": len(live),
        "stale": len(stale),
        "stale_ids": [bt["id"] for bt in stale],
        "hollow": None,
    }


def _survey(context: dict) -> dict:
    return context.get("survey") or survey_bounce_blame()


def _trigger(now, context: dict) -> bool:
    """TRUE when bounce-raised troubles show a wrong-blame pattern.

    Two conditions, either fires:
      (a) receiver-side share exceeds half over at least 8 clears
      (b) a bounce-raised trouble stands live past 14 days
    """
    s = _survey(context)
    if s.get("hollow"):
        return True
    if s["stale"]:
        return True
    if s["cleared"] >= _ENOUGH_CLEARED:
        if s["receiver_fixes"] > s["cleared"] / 2:
            return True
    return False


def _enough(context: dict) -> bool:
    """CLEARED when the bounce mechanism is working as intended.

    >= 8 post-era bounce-raised troubles cleared AND >= 6 fixed at the sender.
    """
    s = _survey(context)
    if s.get("hollow"):
        return False
    if s["stale"]:
        return False
    return s["cleared"] >= _ENOUGH_CLEARED and s["sender_fixes"] >= _ENOUGH_SENDER


def _carry(context: dict) -> dict:
    s = _survey(context)
    parts = []
    if s.get("hollow"):
        parts.append(f"the troubles root is HOLLOW — {s['hollow']}")
    if s["stale"]:
        parts.append(f"{s['stale']} bounce-raised trouble(s) standing live > {_STALE_DAYS} "
                     f"days: {s['stale_ids']}")
    if s["cleared"] >= _ENOUGH_CLEARED and s["receiver_fixes"] > s["cleared"] / 2:
        parts.append(f"receiver-side majority: {s['receiver_fixes']}/{s['cleared']} "
                     "clears fixed at the receiver — wrong-blame signal")

    return {
        "finding": ("; ".join(parts) or
                    ("no bounce-raised troubles in the post-era corpus"
                     if s["total"] == 0 else
                     "the bounce mechanism blames the right party — "
                     f"{s['sender_fixes']}/{s['cleared']} fixes landed at the sender")),
        "counts": {
            "total": s["total"],
            "cleared": s["cleared"],
            "sender_fixes": s["sender_fixes"],
            "receiver_fixes": s["receiver_fixes"],
            "unclassified": s["unclassified"],
            "live": s["live"],
            "stale": s["stale"],
        },
        "era_floor": _ERA_FLOOR,
        "thresholds": {
            "enough_cleared": _ENOUGH_CLEARED,
            "enough_sender": _ENOUGH_SENDER,
            "stale_days": _STALE_DAYS,
        },
        "details": s["bounce_troubles"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "the ticket's proves_red clause: 'ALSO WRONG INTENT if the bounce lane "
            "fills with troubles whose fixes all land at the receiver (the WATCHME's "
            "kill)' — sender_fixes and receiver_fixes are the two counts the carrier "
            "requires as measured values"),
        "suggests": (
            "repair the probe — the troubles root does not exist"
            if s.get("hollow") else
            "read the named trouble(s): each stale bounce trouble is a defect "
            "standing unresolved past the 14-day mark"
            if s["stale"] else
            "the bounce mechanism has not yet raised enough troubles to measure — "
            "the probe is waiting for the corpus to grow"
            if s["total"] < _ENOUGH_CLEARED else
            "the bounce mechanism blames the right party — no action needed"
            if s["sender_fixes"] >= _ENOUGH_SENDER else
            "read the what_changed on each cleared bounce trouble — a receiver-side "
            "majority says the trouble is raised on the wrong party"
        ),
    }


_HORIZON = 1000

PROBE = Probe(
    why="does the bounce blame the right party? — a receiver-side majority "
        "of cleared bounce troubles says the spec is wrong, not the sender",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps(_carry({}), indent=2, default=str))

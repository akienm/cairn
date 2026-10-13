"""PROBE — does a message sent to CC reach the shim's deliver(), and does a CC session read it?

Berth for the WATCHME that ticket ``the-cc-device`` (078476729bca) carries (object
``message-delivery``). Berthed beside ``cairn/devices/cc`` because that is WHAT IT WATCHES:
the shim's deliver() path is the one way bus messages reach CC.

THIS PROBE READS THE SHIM'S MAIL LEDGER, ``~/.cairn/devices/cc/0/mail_ledger.jsonl``. The
shim appends a 'delivered' line when deliver() persists an envelope and a 'consumed' line,
naming the CC session, when consume_mail() removes one. The mail folder itself cannot count
deliveries — consume_mail deletes what it reads — so the ledger is the record.

Trigger: any 'delivered' line. Enough: three reads across two separate CC sessions (the
ticket's own enough — the channel is not a one-off). Holds: False exactly when a delivered
message has gone unread for more than a day; an empty ledger holds.

AUTHORITY: none. This probe deposits and pokes; the back-edge that re-opens the node is the
owner's act (Law 6).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.base.probe import Probe, watch_carry

_TICKET_ID = "078476729bca"

LEDGER = address.instance_path("cc", 0) / "mail_ledger.jsonl"


def read_ledger(path: Path | None = None) -> list[dict]:
    """Every ledger line, oldest first. A missing file is []; a torn line is skipped."""
    p = Path(path) if path is not None else LEDGER
    try:
        text = p.read_text()
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _events(kind: str) -> list[dict]:
    return [r for r in read_ledger() if r.get("event") == kind]


def _sessions() -> list[str]:
    return sorted({r.get("session") for r in _events("consumed") if r.get("session")})


def _trigger(now, context: dict) -> bool:
    return bool(_events("delivered"))


def _carry(context: dict) -> dict:
    delivered, stale = _events("delivered"), _unread_a_day()
    return {
        "delivered": len(delivered),
        "consumed": len(_events("consumed")),
        "sessions": _sessions(),
        "delivery_times": [r.get("at") for r in delivered[-3:]],
        "finding": f"delivered and unread for over a day: {', '.join(stale)}" if stale else "",
    }


def _enough(context: dict) -> bool:
    return len(_events("consumed")) >= 3 and len(_sessions()) >= 2


def _unread_a_day() -> list[str]:
    """Ids delivered more than 24 hours ago with no consumed line."""
    read = {r.get("id") for r in _events("consumed")}
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    out = []
    for r in _events("delivered"):
        if r.get("id") in read:
            continue
        try:
            at = datetime.fromisoformat(r.get("at", ""))
        except (TypeError, ValueError):
            continue
        if at < cutoff:
            out.append(r.get("id"))
    return out


def _holds(context: dict) -> bool:
    """Mail delivered and never read is the failure: False when a delivered id has no
    consumed line and was delivered more than 24 hours ago."""
    return not _unread_a_day()


PROBE = Probe(
    why="the CC device's shim must receive bus messages — without delivery, the "
        "cocoon strategy has no way to poke CC of work, and the device is a "
        "rack address nobody can reach",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    verb="watch",
    carry=watch_carry(_TICKET_ID, _carry, holds=_holds),
    enough=_enough,
    horizon=100,
)


if __name__ == "__main__":
    print(json.dumps({
        "would_trigger": _trigger(None, {}),
        "enough": _enough({}),
        "payload": PROBE.payload({}),
    }, indent=2))

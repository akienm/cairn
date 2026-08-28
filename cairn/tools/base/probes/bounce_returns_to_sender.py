"""PROBE — does the bounce blame the right party?

Berth for the WATCHME that ticket ``undeliverable-mail-returns-to-sender`` carries.
Berthed beside ``cairn/tools/base`` because that is WHAT IT WATCHES: ``shim.py``'s
``_bounce_to_sender`` and ``handle_bounce`` are the writer, and the one way this design
fails silently is a bounce that loses the sender's identity — the blame goes nowhere,
and the diagnostic surfaces in the wrong inbox.

THE EFFICACY QUESTION: does the sender attribution hold across bounce paths that were
never tested together? The proof beside the code settles the three paths on the day they
ship (unknown verb, uncallable handler, no receive). Whether the NEXT bounce path
carries the sender correctly is a fact about the next path, and the ticket's own
``enough`` names that explicitly: "3 bounces observed in live operation with correct
sender attribution."

TWO INVARIANTS MEASURED TOGETHER, because they are one grain seen from two angles:

  (a) EVERY BOUNCE NAMES ITS TARGET. A ``bounce_sent`` emission with a missing or empty
      ``to`` field means the blame was lost — the bounce went somewhere, but the record
      cannot say where.

  (b) THE RETURN PATH FIRES. A ``bounced_mail`` emission on the sender's side proves
      the return trip completed — the bounce was not only sent but received and diagnosed.

FILES ONLY, by construction: the probe walks ``~/.cairn/logs/`` — no device, no bus, no
network — so it stays cheap enough to sit on a pulse.

AUTHORITY: none. This probe deposits and pokes; fixing a lost attribution is the owner's
act at the floor (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.address import resolve
from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "undeliverable-mail-returns-to-sender"


def _survey_bounce_trail(*, roots: dict[str, Path] | None = None) -> dict:
    """Walk every device's log directory and count bounce_sent / bounced_mail emissions."""
    logs_root = resolve("instance/logs", roots)
    if not logs_root.exists():
        return {"bounce_sent": [], "bounced_mail": [], "unattributed": [],
                "hollow": "the logs root does not exist"}

    bounce_sent: list[dict] = []
    bounced_mail: list[dict] = []
    unattributed: list[dict] = []

    for device_dir in sorted(logs_root.iterdir()):
        if not device_dir.is_dir():
            continue
        for instance_dir in sorted(device_dir.iterdir()):
            if not instance_dir.is_dir():
                continue
            device_key = f"{device_dir.name}/{instance_dir.name}"
            for jf in sorted(instance_dir.glob("*.json")):
                try:
                    rec = json.loads(jf.read_text(encoding="utf-8").strip())
                except (ValueError, OSError):
                    continue
                gate = rec.get("gate", "")
                if gate == "bounce_sent":
                    values = rec.get("values", {})
                    to = values.get("to", "")
                    entry = {"device": device_key, "file": str(jf),
                             "to": to, "reason": values.get("reason", "")}
                    bounce_sent.append(entry)
                    if not to:
                        unattributed.append(entry)
                elif gate == "bounced_mail":
                    values = rec.get("values", {})
                    bounced_mail.append({
                        "device": device_key, "file": str(jf),
                        "from": values.get("from", ""),
                        "reason": values.get("reason", ""),
                        "original_verb": values.get("original_verb", "")})

    return {"bounce_sent": bounce_sent, "bounced_mail": bounced_mail,
            "unattributed": unattributed, "hollow": None}


def _corpus(context: dict) -> dict:
    return context.get("corpus") or _survey_bounce_trail()


def _trigger(now, context: dict) -> bool:
    """TRUE when any bounce_sent emission has no target — the blame was lost."""
    s = _corpus(context)
    if s.get("hollow"):
        return True
    return bool(s["unattributed"])


def _enough(context: dict) -> bool:
    """CLEARED when 3+ bounce_sent emissions all name their target correctly."""
    s = _corpus(context)
    if s.get("hollow"):
        return False
    if s["unattributed"]:
        return False
    return len(s["bounce_sent"]) >= 3


def _carry(context: dict) -> dict:
    s = _corpus(context)
    parts = []
    if s.get("hollow"):
        parts.append(f"the logs tree is HOLLOW — {s['hollow']}")
    if s["unattributed"]:
        parts.append(f"{len(s['unattributed'])} bounce(s) with no target attribution: "
                     + ", ".join(e["file"] for e in s["unattributed"]))

    attributed = len(s["bounce_sent"]) - len(s["unattributed"])
    return_trips = len(s["bounced_mail"])

    return {
        "finding": "; ".join(parts) or "every bounce names its target — the blame holds",
        "counts": {
            "bounce_sent": len(s["bounce_sent"]),
            "bounced_mail": return_trips,
            "attributed": attributed,
            "unattributed": len(s["unattributed"]),
        },
        "unattributed": s["unattributed"],
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's clause is 'send a bus message to a device with "
                             "no handler for that verb — the message bounces to sender'; "
                             "the bounce_sent emission carries the target, and a missing "
                             "target is a lost blame",
        "suggests": ("repair the probe — the logs tree does not exist" if s.get("hollow") else
                     "read the named file(s): a bounce with no target is a _bounce_to_sender "
                     "call where envelope.get('sender') was empty — the envelope arrived "
                     "without a return address"),
    }


_HORIZON = 1000

PROBE = Probe(
    why="does every bounce name its target correctly? — the sender owns the decision "
        "about returned mail (Law 6), and a bounce that loses the sender's identity "
        "sends the blame nowhere",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps(_carry({}), indent=2, default=str))

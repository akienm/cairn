"""PROBE — does a message sent to CC reach the shim's deliver()?

Berth for the WATCHME that ticket ``the-cc-device`` carries (object
``message-delivery``). Berthed beside ``cairn/devices/cc`` because that is WHAT
IT WATCHES: the shim's deliver() path is the one way bus messages reach CC.

THIS PROBE READS THE DIAGNOSTIC MAILBOX. When deliver() is called on any shim,
BaseShim records a breadcrumb in the diagnostic mailbox via receive_diagnostic().
If the mailbox has entries, messages are reaching the shim. If not, either nobody
has sent one or deliver() is broken — both worth knowing.

The trigger fires when the shim has received at least one diagnostic breadcrumb
since boot. Until then the probe holds — a watch that has not yet seen evidence
is not a finding, it is patience.

AUTHORITY: none. This probe deposits and pokes; the back-edge that re-opens the
node is the owner's act (Law 6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cairn.tools.base.probe import Probe


def _trigger(now, context: dict) -> bool:
    mailbox = context.get("diagnostics_received", 0)
    return mailbox > 0


def _carry(context: dict) -> dict:
    return {"diagnostics_received": context.get("diagnostics_received", 0)}


def _enough(context: dict) -> bool:
    return context.get("diagnostics_received", 0) >= 3


PROBE = Probe(
    why="the CC device's shim must receive bus messages — without delivery, the "
        "cocoon strategy has no way to poke CC of work, and the device is a "
        "rack address nobody can reach",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=100,
)


if __name__ == "__main__":
    import json
    ctx = {"diagnostics_received": 0}
    print(json.dumps({
        "would_trigger": _trigger(None, ctx),
        "enough": _enough(ctx),
    }, indent=2))

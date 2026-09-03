"""PROBE — does a message sent to CodeMother reach the shim's deliver()?

Berthed beside cairn/devices/codemother because that is WHAT IT WATCHES:
the shim's deliver() path is the one way bus messages reach CodeMother.
The trigger fires when the shim has received at least one diagnostic breadcrumb
since boot.
"""

from __future__ import annotations

from cairn.tools.base.probe import Probe


def _trigger(now, context: dict) -> bool:
    return context.get("diagnostics_received", 0) > 0


def _carry(context: dict) -> dict:
    return {"diagnostics_received": context.get("diagnostics_received", 0)}


def _enough(context: dict) -> bool:
    return context.get("diagnostics_received", 0) >= 3


PROBE = Probe(
    why="the CodeMother device's shim must receive bus messages — without delivery, "
        "the device has no way to be invoked by MCP/chat/CLI/skill, and challenge "
        "cannot fire on proposed changes",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=100,
)

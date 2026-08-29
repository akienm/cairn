"""cc/shim.py — Claude Code's presence on the heartbeat.

CC's process is not started by this shim — CC starts itself. The shim gives CC
a rack address so the bus can deliver messages to it and the ground loop can
fire its probes. A shim without a device process behind it is honest, not broken:
the probes still fire (they read disk, not CC), and deliver() holds mail in the
diagnostic mailbox until CC is reachable.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim


class CCShim(BaseShim):

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "cc"

    def _start_device(self):
        return None

"""ground_loop/shim.py — the heartbeat's page.

THE CARRIER RULE (Akien, 2026-07-28): there is ONLY EVER ONE WEB SERVER in the whole
system. The heartbeat gets a device PAGE the way every device does — a declared pane the
base shim class understands (``declared_panes`` on the device), never a server, a route, or
a port of its own (ticket the-ground-loop-pane-shows-its-state).

THE PAGE IS A TEMPLATE OVER THE LIVENESS JSON (ticket efb670ff1dd8, 2026-09-30). The
heartbeat is the resident process (``__main__.py``) and nothing in a client fronts it any
more: this shim loads from disk like every other device's (``GroundLoopShim(bus=bus)``, the
standard loader contract), and the device it starts is ``HeartbeatPage`` — read-only, it
reads the record the heartbeat writes and answers the ``liveness`` verb and pane from it. No
probes, no bus writes, no beat.
"""

from __future__ import annotations

from datetime import datetime, timezone

from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim
from cairn.tools.liveness.liveness import liveness_pane_data


class HeartbeatPage(BaseDevice):
    """The heartbeat's page: the liveness record, read at request time. Read-only."""

    @property
    def device_id(self) -> str:
        return "ground_loop"

    def declared_panes(self) -> list[dict]:
        return [{
            "kind": "liveness",
            "label": "Liveness",
            "handler": lambda: liveness_pane_data(datetime.now(timezone.utc).astimezone()),
        }]

    def declared_verbs(self) -> dict:
        return {"liveness": self._answer_liveness}

    def _answer_liveness(self, envelope) -> dict:
        """The page's one crossing: a ``liveness`` ask answered from the record. The answer
        leaves a breadcrumb in this device's own log trail (emit, never the bus)."""
        data = liveness_pane_data(datetime.now(timezone.utc).astimezone())
        self.emit("liveness_answered", pointer=(envelope or {}).get("id"))
        return data

    def intention(self) -> dict:
        return {
            "what": "The heartbeat — provides a pulse and a list of devices it beats to. "
            "If its code is newer, it restarts itself. That is all.",
            "why": "A single daemon structure everyone else hangs their own handlers on. Keeping "
            "the heartbeat to ONLY a pulse means a probe is the same unit no matter what fires "
            "it, and no device's logic rots inside the beat.",
        }

    def state(self) -> dict:
        return {}

    def settings(self) -> dict:
        return {
            "does": "list devices",
            "does_not": "judge, bench, raise trouble tickets, execute, resolve, schedule, "
            "route, or write — firing lives in the shim; durable state lives in db_domain",
            "cadence": "none here — the wall-clock backing is __main__.py "
            "(python3 -m cairn.devices.cairn.machines.ground_loop)",
        }


class GroundLoopShim(BaseShim):
    """The heartbeat's shim: loads from disk like any device's and starts its page."""

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "ground_loop"

    def _start_device(self):
        return HeartbeatPage()

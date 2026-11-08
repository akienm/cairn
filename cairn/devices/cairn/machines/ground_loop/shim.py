"""ground_loop/shim.py — the heartbeat's page.

THE CARRIER RULE (Akien, 2026-07-28): there is ONLY EVER ONE WEB SERVER in the whole
system. The heartbeat gets a device PAGE the way every device does — a declared pane the
base shim class understands (``declared_panes`` on the device), never a server, a route, or
a port of its own (ticket the-ground-loop-pane-shows-its-state).

THE PAGE IS A TEMPLATE OVER THE BEAT RECORD (ticket efb670ff1dd8, 2026-09-30; the record
and the lock became the loop's own in ticket 6208d0a27d6e). The
heartbeat is the resident process (``__main__.py``) and nothing in a client fronts it any
more: this shim loads from disk like every other device's (``GroundLoopShim(bus=bus)``, the
standard loader contract), and the device it starts is ``HeartbeatPage`` — read-only, it
reads the record the heartbeat writes, asks whether its lock is held, and answers the
``beat`` verb and pane from those two. No
probes, no bus writes, no beat.
"""

from __future__ import annotations

from datetime import datetime, timezone

from cairn.devices.cairn.machines.ground_loop import guard
from cairn.devices.cairn.machines.ground_loop.heartbeat import default_home, read_record
from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim


def beat_pane_data(home=None, now=None) -> dict:
    """The Heartbeat pane's DATA: is the loop up (its lock held), and its record whole, as the
    read face returns it — rendered, never derived."""
    home = home if home is not None else default_home()
    now = now if now is not None else datetime.now(timezone.utc).astimezone()
    return {
        "reports": "the resident singleton's lock and beat record (instance 0), read from disk "
        "at request time — whatever process serves this page",
        "up": guard.held(home),
        **read_record(home, now),
    }


class HeartbeatPage(BaseDevice):
    """The heartbeat's page: its lock and its record, read at request time. Read-only."""

    @property
    def device_id(self) -> str:
        return "ground_loop"

    def declared_panes(self) -> list[dict]:
        return [{
            "kind": "beat",
            "label": "Heartbeat",
            "handler": beat_pane_data,
        }]

    def declared_verbs(self) -> dict:
        return {"beat": self._answer_beat}

    def _answer_beat(self, envelope) -> dict:
        """The page's one crossing: a ``beat`` ask answered from the lock and the record. The
        answer leaves a breadcrumb in this device's own log trail (emit, never the bus)."""
        data = beat_pane_data()
        self.emit("beat_answered", pointer=(envelope or {}).get("id"))
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

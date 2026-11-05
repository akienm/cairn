"""Proofs for the-console-pane: info and debug are floor panes projected from bus channels.

Ticket: the-console-pane
Akien ruling 2026-08-31: console retired, info and debug are their own panes.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

import uuid

from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim
from cairn.tools.bus_client import bus_client
from cairn.tools.base import testing_mark

# Ticket ad7caca4d54c: this proof rides the LIVE bus through its published client tool
# (RULE 1), every name marked testing-<ticket>- and every body carrying the testing mark,
# so each run owns fresh addresses and never counts another run's traffic.
_TICKET = "ad7caca4d54c"


def _name(label):
    return f"testing-{_TICKET}-{label}-{uuid.uuid4().hex[:8]}"


def _body(text):
    return {"text": text, testing_mark.FIELD: testing_mark.mark(_TICKET)}


class _Recording:
    """Forwards to the live bus and records which of its members the panes reached for."""

    def __init__(self, bus):
        self._bus = bus
        self.called = []

    def __getattr__(self, name):
        self.called.append(name)
        return getattr(self._bus, name)


class _Device(BaseDevice):
    def intention(self):
        return {"what": "console pane test device", "why": "prove the info+debug floor panes"}
    def state(self):
        return {"resting": "test"}
    def settings(self):
        return {}


class _Shim(BaseShim):
    def __init__(self, bus=None, device_id=None):
        super().__init__(bus=bus)
        self._dev = _Device()
        self._id = device_id or _name("console")

    @property
    def device_id(self):
        return self._id

    def device(self):
        return self._dev


class TestConsolePanes:

    def test_info_pane_in_floor_without_bus(self):
        shim = _Shim(bus=None)
        page = shim.active_page()
        kinds = [p["kind"] for p in page["panes"]]
        assert "info" in kinds, "info pane must be in the floor"
        info = [p for p in page["panes"] if p["kind"] == "info"][0]
        assert info["data"] is None, "without bus the info pane has no data"
        assert "absent" in info, "without bus the info pane explains why it is absent"

    def test_debug_pane_in_floor_without_bus(self):
        shim = _Shim(bus=None)
        page = shim.active_page()
        kinds = [p["kind"] for p in page["panes"]]
        assert "debug" in kinds, "debug pane must be in the floor"
        debug = [p for p in page["panes"] if p["kind"] == "debug"][0]
        assert debug["data"] is None, "without bus the debug pane has no data"
        assert "absent" in debug, "without bus the debug pane explains why it is absent"

    def test_info_pane_shows_info_messages(self):
        bus = bus_client.reach()
        shim = _Shim(bus=bus)
        bus.post(sender=_name("system"), to=shim.device_id, channel="info",
                 why="startup", body=_body("device started"))
        bus.post(sender=_name("system"), to=shim.device_id, channel="info",
                 why="health", body=_body("health check passed"))
        page = shim.active_page()
        info = [p for p in page["panes"] if p["kind"] == "info"][0]
        assert info["data"] is not None, "with bus the info pane has data"
        entries = info["data"]["entries"]
        assert len(entries) == 2, f"expected 2 entries, got {len(entries)}"
        assert entries[0]["body"]["text"] == "device started"
        assert entries[1]["body"]["text"] == "health check passed"

    def test_debug_pane_shows_debug_messages(self):
        bus = bus_client.reach()
        shim = _Shim(bus=bus)
        bus.post(sender=_name("system"), to=shim.device_id, channel="debug",
                 why="trace", body=_body("entering probe loop"))
        page = shim.active_page()
        debug = [p for p in page["panes"] if p["kind"] == "debug"][0]
        assert debug["data"] is not None, "with bus the debug pane has data"
        entries = debug["data"]["entries"]
        assert len(entries) == 1, f"expected 1 entry, got {len(entries)}"
        assert entries[0]["body"]["text"] == "entering probe loop"

    def test_info_and_debug_do_not_cross(self):
        bus = bus_client.reach()
        shim = _Shim(bus=bus)
        bus.post(sender=_name("system"), to=shim.device_id, channel="info",
                 why="info msg", body=_body("info only"))
        bus.post(sender=_name("system"), to=shim.device_id, channel="debug",
                 why="debug msg", body=_body("debug only"))
        page = shim.active_page()
        info = [p for p in page["panes"] if p["kind"] == "info"][0]
        debug = [p for p in page["panes"] if p["kind"] == "debug"][0]
        info_bodies = [e["body"]["text"] for e in info["data"]["entries"]]
        debug_bodies = [e["body"]["text"] for e in debug["data"]["entries"]]
        assert "debug only" not in info_bodies, "debug message must not appear in info pane"
        assert "info only" not in debug_bodies, "info message must not appear in debug pane"

    def test_panes_only_read_the_bus(self):
        rec = _Recording(bus_client.reach())
        _Shim(bus=rec).active_page()
        assert rec.called, "the info+debug panes reached the bus for nothing"
        assert set(rec.called) <= {"read", "count"}, f"rendering reached past read/count: {rec.called}"

    def test_panes_are_not_in_declared_panes(self):
        dev = _Device()
        declared_kinds = {p.get("kind") for p in dev.declared_panes()}
        assert "info" not in declared_kinds, "info is a floor pane (shim), not declared (device)"
        assert "debug" not in declared_kinds, "debug is a floor pane (shim), not declared (device)"

    def test_empty_channels_render_empty_entries(self):
        bus = bus_client.reach()
        shim = _Shim(bus=bus)
        page = shim.active_page()
        info = [p for p in page["panes"] if p["kind"] == "info"][0]
        debug = [p for p in page["panes"] if p["kind"] == "debug"][0]
        assert info["data"] == {"entries": []}, "empty info channel → empty entries, not absent"
        assert debug["data"] == {"entries": []}, "empty debug channel → empty entries, not absent"

    def test_record_channels_not_in_diagnostic_panes(self):
        bus = bus_client.reach()
        shim = _Shim(bus=bus)
        bus.post(sender=_name("alice"), to=shim.device_id, channel="personal",
                 why="chat", body=_body("hello"))
        bus.post(sender=_name("system"), to=shim.device_id, channel="announce",
                 why="announce", body=_body("fleet news"))
        bus.post(sender=_name("system"), to=shim.device_id, channel="info",
                 why="info msg", body=_body("info line"))
        page = shim.active_page()
        info = [p for p in page["panes"] if p["kind"] == "info"][0]
        debug = [p for p in page["panes"] if p["kind"] == "debug"][0]
        info_bodies = [e["body"].get("text") for e in info["data"]["entries"]]
        debug_bodies = [e["body"].get("text") for e in debug["data"]["entries"]]
        assert "hello" not in info_bodies, "personal message must not appear in info"
        assert "fleet news" not in info_bodies, "announce message must not appear in info"
        assert "hello" not in debug_bodies, "personal message must not appear in debug"
        assert "fleet news" not in debug_bodies, "announce message must not appear in debug"


PROVES = {"ad7caca4d54c": {"2": "test_info_pane_shows_info_messages"}}

ROSTER_MIN = 9


def test_roster_minimum():
    tests = [name for name in dir() if name.startswith("test_") and callable(eval(name))]
    for cls_name, cls_obj in list(globals().items()):
        if isinstance(cls_obj, type):
            tests.extend(m for m in dir(cls_obj) if m.startswith("test_"))
    assert len(tests) >= ROSTER_MIN, (
        f"need >= {ROSTER_MIN} teeth, have {len(tests)}: {sorted(tests)}"
    )

if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

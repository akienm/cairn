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

from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim
from cairn.devices.cairn.machines.bus.bus import BusDevice, CHANNELS
from cairn.devices.db_domain import store

import uuid

_NONCE = uuid.uuid4().hex[:8]


def _fresh_table():
    return f"_console_pane_test_{_NONCE}_{uuid.uuid4().hex[:6]}"


def _drop_table(table):
    try:
        conn = store._conn()
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{table}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (table,))
        conn.commit()
    except Exception:
        pass


class _Device(BaseDevice):
    def intention(self):
        return {"what": "console pane test device", "why": "prove the info+debug floor panes"}
    def state(self):
        return {"resting": "test"}
    def settings(self):
        return {}


class _Shim(BaseShim):
    def __init__(self, bus=None):
        super().__init__(bus=bus)
        self._dev = _Device()

    @property
    def device_id(self):
        return "test_console_device"

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
        table = _fresh_table()
        bus = BusDevice(table=table)
        try:
            shim = _Shim(bus=bus)
            bus.post(sender="system", to="test_console_device", channel="info",
                     why="startup", body={"text": "device started"})
            bus.post(sender="system", to="test_console_device", channel="info",
                     why="health", body={"text": "health check passed"})
            page = shim.active_page()
            info = [p for p in page["panes"] if p["kind"] == "info"][0]
            assert info["data"] is not None, "with bus the info pane has data"
            entries = info["data"]["entries"]
            assert len(entries) == 2, f"expected 2 entries, got {len(entries)}"
            assert entries[0]["body"] == {"text": "device started"}
            assert entries[1]["body"] == {"text": "health check passed"}
        finally:
            _drop_table(table)

    def test_debug_pane_shows_debug_messages(self):
        table = _fresh_table()
        bus = BusDevice(table=table)
        try:
            shim = _Shim(bus=bus)
            bus.post(sender="system", to="test_console_device", channel="debug",
                     why="trace", body={"text": "entering probe loop"})
            page = shim.active_page()
            debug = [p for p in page["panes"] if p["kind"] == "debug"][0]
            assert debug["data"] is not None, "with bus the debug pane has data"
            entries = debug["data"]["entries"]
            assert len(entries) == 1, f"expected 1 entry, got {len(entries)}"
            assert entries[0]["body"] == {"text": "entering probe loop"}
        finally:
            _drop_table(table)

    def test_info_and_debug_do_not_cross(self):
        table = _fresh_table()
        bus = BusDevice(table=table)
        try:
            shim = _Shim(bus=bus)
            bus.post(sender="system", to="test_console_device", channel="info",
                     why="info msg", body={"text": "info only"})
            bus.post(sender="system", to="test_console_device", channel="debug",
                     why="debug msg", body={"text": "debug only"})
            page = shim.active_page()
            info = [p for p in page["panes"] if p["kind"] == "info"][0]
            debug = [p for p in page["panes"] if p["kind"] == "debug"][0]
            info_bodies = [e["body"]["text"] for e in info["data"]["entries"]]
            debug_bodies = [e["body"]["text"] for e in debug["data"]["entries"]]
            assert "debug only" not in info_bodies, "debug message must not appear in info pane"
            assert "info only" not in debug_bodies, "info message must not appear in debug pane"
        finally:
            _drop_table(table)

    def test_panes_do_not_alter_channels(self):
        channels_before = dict(CHANNELS)
        table = _fresh_table()
        bus = BusDevice(table=table)
        try:
            shim = _Shim(bus=bus)
            shim.active_page()
            assert CHANNELS == channels_before, "rendering info+debug panes must not alter CHANNELS"
        finally:
            _drop_table(table)

    def test_panes_are_not_in_declared_panes(self):
        dev = _Device()
        declared_kinds = {p.get("kind") for p in dev.declared_panes()}
        assert "info" not in declared_kinds, "info is a floor pane (shim), not declared (device)"
        assert "debug" not in declared_kinds, "debug is a floor pane (shim), not declared (device)"

    def test_empty_channels_render_empty_entries(self):
        table = _fresh_table()
        bus = BusDevice(table=table)
        try:
            shim = _Shim(bus=bus)
            page = shim.active_page()
            info = [p for p in page["panes"] if p["kind"] == "info"][0]
            debug = [p for p in page["panes"] if p["kind"] == "debug"][0]
            assert info["data"] == {"entries": []}, "empty info channel → empty entries, not absent"
            assert debug["data"] == {"entries": []}, "empty debug channel → empty entries, not absent"
        finally:
            _drop_table(table)

    def test_record_channels_not_in_diagnostic_panes(self):
        table = _fresh_table()
        bus = BusDevice(table=table)
        try:
            shim = _Shim(bus=bus)
            bus.post(sender="alice", to="test_console_device", channel="personal",
                     why="chat", body={"text": "hello"})
            bus.post(sender="system", to="test_console_device", channel="announce",
                     why="announce", body={"text": "fleet news"})
            bus.post(sender="system", to="test_console_device", channel="info",
                     why="info msg", body={"text": "info line"})
            page = shim.active_page()
            info = [p for p in page["panes"] if p["kind"] == "info"][0]
            debug = [p for p in page["panes"] if p["kind"] == "debug"][0]
            info_bodies = [e["body"].get("text") for e in info["data"]["entries"]]
            debug_bodies = [e["body"].get("text") for e in debug["data"]["entries"]]
            assert "hello" not in info_bodies, "personal message must not appear in info"
            assert "fleet news" not in info_bodies, "announce message must not appear in info"
            assert "hello" not in debug_bodies, "personal message must not appear in debug"
            assert "fleet news" not in debug_bodies, "announce message must not appear in debug"
        finally:
            _drop_table(table)


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
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    teeth = sum(1 for name in dir() if name.startswith("test_") and callable(eval(name)))
    for cls_name, cls_obj in list(globals().items()):
        if isinstance(cls_obj, type):
            teeth += sum(1 for m in dir(cls_obj) if m.startswith("test_"))
    color = "\033[32m" if result.returncode == 0 else "\033[31m"
    print(f"\n{color}{teeth} teeth {'green' if result.returncode == 0 else 'RED'}\033[0m")
    sys.exit(result.returncode)

"""Proofs for chat-is-floor-not-declared: chat is a floor pane projected from the personal channel.

Ticket: chat-is-floor-not-declared
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
    return f"_chat_pane_test_{_NONCE}_{uuid.uuid4().hex[:6]}"


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
        return {"what": "chat pane test device", "why": "prove the chat floor pane"}
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
        return "test_chat_device"

    def device(self):
        return self._dev


class TestChatPaneIsFloor:

    def test_chat_pane_in_floor_without_bus(self):
        shim = _Shim(bus=None)
        page = shim.active_page()
        kinds = [p["kind"] for p in page["panes"]]
        assert "personal_feed" in kinds, "chat pane must be in the floor"
        chat = [p for p in page["panes"] if p["kind"] == "personal_feed"][0]
        assert chat["data"] is None, "without bus the chat pane has no data"
        assert "absent" in chat, "without bus the chat pane explains why it is absent"

    def test_chat_pane_shows_personal_messages(self):
        table = _fresh_table()
        bus = BusDevice(table=table)
        try:
            shim = _Shim(bus=bus)
            bus.post(sender="alice", to="test_chat_device", channel="personal",
                     why="test message", body={"text": "hello"})
            bus.post(sender="bob", to="test_chat_device", channel="personal",
                     why="another test", body={"text": "world"})
            page = shim.active_page()
            chat = [p for p in page["panes"] if p["kind"] == "personal_feed"][0]
            assert chat["data"] is not None, "with bus the chat pane has data"
            turns = chat["data"]["turns"]
            assert len(turns) == 2, f"expected 2 turns, got {len(turns)}"
            assert turns[0]["sender"] == "alice"
            assert turns[1]["sender"] == "bob"
            assert turns[0]["body"] == {"text": "hello"}
        finally:
            _drop_table(table)

    def test_chat_pane_does_not_alter_channels(self):
        channels_before = dict(CHANNELS)
        table = _fresh_table()
        bus = BusDevice(table=table)
        try:
            shim = _Shim(bus=bus)
            shim.active_page()
            assert CHANNELS == channels_before, "rendering the chat pane must not alter CHANNELS"
        finally:
            _drop_table(table)

    def test_chat_pane_is_not_in_declared_panes(self):
        dev = _Device()
        assert not any(
            p.get("kind") == "personal_feed" for p in dev.declared_panes()
        ), "chat is a floor pane (shim), not a declared pane (device)"

    def test_empty_personal_channel_renders_empty_turns(self):
        table = _fresh_table()
        bus = BusDevice(table=table)
        try:
            shim = _Shim(bus=bus)
            page = shim.active_page()
            chat = [p for p in page["panes"] if p["kind"] == "personal_feed"][0]
            assert chat["data"] == {"turns": []}, "empty personal channel → empty turns, not absent"
        finally:
            _drop_table(table)


ROSTER_MIN = 5


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

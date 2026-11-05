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
        return {"what": "chat pane test device", "why": "prove the chat floor pane"}
    def state(self):
        return {"resting": "test"}
    def settings(self):
        return {}


class _Shim(BaseShim):
    def __init__(self, bus=None, device_id=None):
        super().__init__(bus=bus)
        self._dev = _Device()
        self._id = device_id or _name("chat")

    @property
    def device_id(self):
        return self._id

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
        bus = bus_client.reach()
        shim = _Shim(bus=bus)
        alice, bob = _name("alice"), _name("bob")
        bus.post(sender=alice, to=shim.device_id, channel="personal",
                 why="test message", body=_body("hello"))
        bus.post(sender=bob, to=shim.device_id, channel="personal",
                 why="another test", body=_body("world"))
        page = shim.active_page()
        chat = [p for p in page["panes"] if p["kind"] == "personal_feed"][0]
        assert chat["data"] is not None, "with bus the chat pane has data"
        turns = chat["data"]["turns"]
        assert len(turns) == 2, f"expected 2 turns, got {len(turns)}"
        assert turns[0]["sender"] == alice
        assert turns[1]["sender"] == bob
        assert turns[0]["body"]["text"] == "hello"
        assert turns[0]["body"][testing_mark.FIELD] == testing_mark.mark(_TICKET)

    def test_chat_pane_only_reads_the_bus(self):
        rec = _Recording(bus_client.reach())
        _Shim(bus=rec).active_page()
        assert rec.called, "the chat pane reached the bus for nothing"
        assert set(rec.called) <= {"read", "count"}, f"rendering reached past read/count: {rec.called}"

    def test_chat_pane_is_not_in_declared_panes(self):
        dev = _Device()
        assert not any(
            p.get("kind") == "personal_feed" for p in dev.declared_panes()
        ), "chat is a floor pane (shim), not a declared pane (device)"

    def test_empty_personal_channel_renders_empty_turns(self):
        bus = bus_client.reach()
        shim = _Shim(bus=bus)
        page = shim.active_page()
        chat = [p for p in page["panes"] if p["kind"] == "personal_feed"][0]
        assert chat["data"] == {"turns": []}, "empty personal channel → empty turns, not absent"


PROVES = {"ad7caca4d54c": {"2": "test_chat_pane_shows_personal_messages"}}

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
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

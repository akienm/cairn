"""Proofs for Bus.list() and Bus.toggle() — the management verbs.

Ticket: the-bus-answers-list-and-toggle
"""

import pytest
from cairn.devices.cairn.machines.bus.bus import BusDevice, CHANNELS


def _fresh_bus():
    """An ephemeral bus on a test table — same pattern as test_bus.py."""
    import uuid
    tag = uuid.uuid4().hex[:8]
    return BusDevice(table=f"test_lt_{tag}", device_id="bus")


def _noop_hook(envelope):
    pass


class _Recorder:
    def __init__(self):
        self.received = []

    def __call__(self, envelope):
        self.received.append(envelope)


def test_list_empty_bus():
    bus = _fresh_bus()
    assert bus.list() == {}, "unwired bus lists nothing"


def test_list_shows_wired_device():
    bus = _fresh_bus()
    bus.wire_delivery("dev_a", _noop_hook)
    roster = bus.list()
    assert "dev_a" in roster
    assert roster["dev_a"]["wired"] is True
    assert all(roster["dev_a"]["channels"][ch] is True for ch in CHANNELS)


def test_unwire_removes_from_list():
    bus = _fresh_bus()
    bus.wire_delivery("dev_a", _noop_hook)
    bus.unwire_delivery("dev_a")
    assert bus.list() == {}


def test_toggle_suppresses_delivery():
    bus = _fresh_bus()
    rec = _Recorder()
    bus.wire_delivery("dev_a", rec)

    bus.post(sender="s", to="dev_a", channel="personal", why="before toggle")
    assert len(rec.received) == 1, "delivery fires before toggle"

    bus.toggle("dev_a", "personal", False)

    bus.post(sender="s", to="dev_a", channel="personal", why="after toggle off")
    assert len(rec.received) == 1, "delivery suppressed after toggle off"


def test_toggle_restores_delivery():
    bus = _fresh_bus()
    rec = _Recorder()
    bus.wire_delivery("dev_a", rec)
    bus.toggle("dev_a", "personal", False)
    bus.toggle("dev_a", "personal", True)

    bus.post(sender="s", to="dev_a", channel="personal", why="after toggle on")
    assert len(rec.received) == 1, "delivery restored after toggle on"


def test_toggle_reflects_in_list():
    bus = _fresh_bus()
    bus.wire_delivery("dev_a", _noop_hook)
    bus.toggle("dev_a", "info", False)

    roster = bus.list()
    assert roster["dev_a"]["channels"]["info"] is False
    assert roster["dev_a"]["channels"]["personal"] is True


def test_toggle_on_unwired_device_raises():
    bus = _fresh_bus()
    with pytest.raises(ValueError, match="not wired"):
        bus.toggle("ghost", "personal", True)


def test_toggle_unknown_channel_raises():
    bus = _fresh_bus()
    bus.wire_delivery("dev_a", _noop_hook)
    from cairn.devices.cairn.machines.bus.bus import ChannelError
    with pytest.raises(ChannelError):
        bus.toggle("dev_a", "nonexistent", True)


ROSTER_MIN = 8


def test_roster_minimum():
    """The roster floor — a hollow proof cannot reach this count."""
    import inspect
    tests = [name for name, obj in globals().items()
             if name.startswith("test_") and callable(obj)
             and name != "test_roster_minimum"]
    assert len(tests) >= ROSTER_MIN, (
        f"need >= {ROSTER_MIN} teeth, have {len(tests)}: {sorted(tests)}"
    )


if __name__ == "__main__":
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd="/home/akien/dev/src/cairn",
        env={**__import__("os").environ, "PYTHONPATH": "/home/akien/dev/src/cairn"})
    teeth = sum(1 for name in dir() if name.startswith("test_") and callable(eval(name)))
    color = "\033[32m" if result.returncode == 0 else "\033[31m"
    print(f"\n{color}{teeth} teeth {'green' if result.returncode == 0 else 'RED'}\033[0m")
    sys.exit(result.returncode)

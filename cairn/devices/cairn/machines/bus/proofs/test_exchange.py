"""PROOF — the parameterized exchange: sync is post() + correlated read, not a second door.

ONE door: async is fire-and-forget post(), sync is post() + a correlated reply via
reply_to. The timeout fails LOUD (TimeoutError, not empty return — CP1).

What a hollow build cannot pass (Law 8):

  - A request() that ignores reply_to and returns any response from the target fails
    ``test_sync_returns_correlated_reply`` — the reply must match the request's envelope id.
  - A request() that returns None/empty instead of raising on timeout fails
    ``test_timeout_raises_not_returns_empty`` — CP1: loud, not silent.
  - A request() that bypasses post() (a second door) fails
    ``test_request_uses_post_not_a_second_door`` — the envelope must appear in the transit
    table via the same post() path.

Requires Postgres (db_domain's durable transit). Self-cleaning.

    python3 cairn/devices/cairn/machines/bus/proofs/test_exchange.py   # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.shim import BaseShim, ONLINE  # noqa: E402
from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.shim import BusShim  # noqa: E402
from cairn.devices.db_domain import store  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLES: list[str] = []
NOW = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)


class EchoDevice(BaseDevice):
    """A device that echoes back via a reply — the simplest sync responder."""

    def __init__(self, bus: BusDevice | None = None) -> None:
        super().__init__()
        self._bus = bus

    def intention(self) -> dict:
        return {"what": "proof echo device"}

    def state(self) -> dict:
        return {"at": "running"}

    def settings(self) -> dict:
        return {}

    def declared_verbs(self) -> dict:
        return {"echo": self._handle_echo}

    def _handle_echo(self, envelope: dict) -> dict:
        if self._bus is not None:
            self._bus.post(
                sender=envelope["addressee"],
                to=envelope["sender"],
                channel="personal",
                why="echo reply",
                body={"echoed": envelope["body"]},
                reply_to=envelope["id"],
            )
        return {"ack": envelope["id"]}


class EchoShim(BaseShim):
    def __init__(self, device_id: str, device: EchoDevice, bus=None) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self._device = device
        self._presence = ONLINE

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        return self._device


class SilentDevice(BaseDevice):
    """A device that accepts mail but never replies — for timeout tests."""

    def __init__(self) -> None:
        super().__init__()

    def intention(self) -> dict:
        return {"what": "proof silent device"}

    def state(self) -> dict:
        return {"at": "running"}

    def settings(self) -> dict:
        return {}

    def receive(self, envelope: dict):
        return {"ack": envelope["id"]}


class SilentShim(BaseShim):
    def __init__(self, device_id: str, device: SilentDevice, bus=None) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self._device = device
        self._presence = ONLINE

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        return self._device


def _fresh_bus():
    bus = BusDevice(table=f"_bus_exch_{_NONCE}_{len(_TABLES)}")
    _TABLES.append(bus.table)
    return bus


def _rig(bus, *shims):
    loop = GroundLoopDevice(bus=bus)
    bus_shim = BusShim(bus, loop)
    loop.subscribe(bus_shim)
    for shim in shims:
        loop.subscribe(shim)
    return loop


# --- teeth ------------------------------------------------------------------

def test_sync_returns_correlated_reply():
    """The reply is correlated by reply_to — the envelope's own id, not any reply."""
    bus = _fresh_bus()
    echo_dev = EchoDevice(bus=bus)
    echo_shim = EchoShim("echo_a", echo_dev, bus=bus)
    # A "caller" shim to provide the sender address
    caller_dev = SilentDevice()
    caller_shim = SilentShim("caller_a", caller_dev, bus=bus)
    loop = _rig(bus, echo_shim, caller_shim)
    loop.beat(NOW)  # wire delivery for both
    reply = bus.request(
        sender="caller_a", to="echo_a", channel="personal",
        verb="echo", why="sync proof", body={"question": "are you there"},
    )
    assert reply["reply_to"] is not None, "reply must carry reply_to"
    assert reply["body"] == {"echoed": {"question": "are you there"}}
    assert reply["sender"] == "echo_a"
    assert reply["addressee"] == "caller_a"


def test_timeout_raises_not_returns_empty():
    """CP1: a reply that never comes is a TimeoutError, not empty."""
    bus = _fresh_bus()
    silent_dev = SilentDevice()
    silent_shim = SilentShim("silent_a", silent_dev, bus=bus)
    caller_dev = SilentDevice()
    caller_shim = SilentShim("caller_b", caller_dev, bus=bus)
    loop = _rig(bus, silent_shim, caller_shim)
    loop.beat(NOW)
    try:
        bus.request(
            sender="caller_b", to="silent_a", channel="personal",
            why="timeout proof", body={"question": "hello?"},
            timeout=0.2,
        )
        assert False, "request() should have raised TimeoutError"
    except TimeoutError as exc:
        assert "no reply" in str(exc).lower(), str(exc)


def test_request_uses_post_not_a_second_door():
    """The request envelope lands in the transit table via post() — one door."""
    bus = _fresh_bus()
    echo_dev = EchoDevice(bus=bus)
    echo_shim = EchoShim("echo_b", echo_dev, bus=bus)
    caller_dev = SilentDevice()
    caller_shim = SilentShim("caller_c", caller_dev, bus=bus)
    loop = _rig(bus, echo_shim, caller_shim)
    loop.beat(NOW)
    reply = bus.request(
        sender="caller_c", to="echo_b", channel="personal",
        verb="echo", why="door proof", body={"n": 1},
    )
    all_to_echo = bus.read(to="echo_b", channel="personal")
    request_envelopes = [e for e in all_to_echo if e.get("body") == {"n": 1}]
    assert len(request_envelopes) == 1, \
        f"request envelope should be in transit table, found {len(request_envelopes)}"


def test_async_post_still_fire_and_forget():
    """Async post() remains fire-and-forget — returns the envelope, not a reply."""
    bus = _fresh_bus()
    echo_dev = EchoDevice(bus=bus)
    echo_shim = EchoShim("echo_c", echo_dev, bus=bus)
    loop = _rig(bus, echo_shim)
    loop.beat(NOW)
    envelope = bus.post(
        sender="caller_d", to="echo_c", channel="personal",
        why="async proof", body={"n": 2},
    )
    assert envelope["sender"] == "caller_d"
    assert envelope["addressee"] == "echo_c"
    assert "echoed" not in envelope.get("body", {}), \
        "post() must return the SENT envelope, not the reply"


def test_reply_to_correlation_is_exact():
    """Multiple requests: each reply correlates to its own request, not to the other."""
    bus = _fresh_bus()
    echo_dev = EchoDevice(bus=bus)
    echo_shim = EchoShim("echo_d", echo_dev, bus=bus)
    caller_dev = SilentDevice()
    caller_shim = SilentShim("caller_e", caller_dev, bus=bus)
    loop = _rig(bus, echo_shim, caller_shim)
    loop.beat(NOW)
    reply1 = bus.request(
        sender="caller_e", to="echo_d", channel="personal",
        verb="echo", why="correlation proof 1", body={"seq": 1},
    )
    reply2 = bus.request(
        sender="caller_e", to="echo_d", channel="personal",
        verb="echo", why="correlation proof 2", body={"seq": 2},
    )
    assert reply1["body"] == {"echoed": {"seq": 1}}, reply1["body"]
    assert reply2["body"] == {"echoed": {"seq": 2}}, reply2["body"]
    assert reply1["reply_to"] != reply2["reply_to"], \
        "each reply must correlate to its own request"


if __name__ == "__main__":
    failures = 0
    try:
        for name, fn in sorted(globals().items()):
            if not name.startswith("test_") or not callable(fn):
                continue
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    finally:
        try:
            conn = store.connect()
            with conn.cursor() as cur:
                for base in _TABLES:
                    for table in (f"{base}_delivery", base):
                        cur.execute(f'DROP TABLE IF EXISTS "{table}"')
                        cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s',
                                    (table,))
            conn.close()
        except Exception as exc:  # noqa: BLE001
            print(f"  (cleanup refused: {type(exc).__name__}: {exc})")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — one door, correlated replies, loud timeout")

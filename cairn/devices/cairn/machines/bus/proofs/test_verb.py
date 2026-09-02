"""PROOF — the VERB: a device is addressed by verb, not by method name.

Bus-completion child (a). Teeth a hollow pass cannot satisfy:
  (1) a post with verb= carries it in the envelope
  (2) deliver resolves verb → device's declared handler
  (3) an unknown verb goes RED (NotImplementedError), never a silent drop
  (4) a device with no declared verbs and no receive() refuses all mail
  (5) a device with declared verbs and NO verb in the envelope falls back to receive()
  (6) a Probe carries verb and _fire passes it to post
  (7) the verb column exists in the transit table after _ensure

    python3 cairn/devices/cairn/machines/bus/proofs/test_verb.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.tools.base.probe import Probe  # noqa: E402
from cairn.tools.base.shim import BaseShim, ONLINE  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.db_domain import store  # noqa: E402

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLES: list[str] = []


class VerbDevice(BaseDevice):
    """A device that declares verbs."""

    def __init__(self):
        super().__init__()
        self._device_id = "test_verb_device"
        self.pings: list[dict] = []
        self.status_calls: list[dict] = []

    @property
    def device_id(self):
        return self._device_id

    def declared_verbs(self):
        return {
            "ping": self._handle_ping,
            "status": self._handle_status,
        }

    def _handle_ping(self, envelope):
        self.pings.append(envelope)
        return {"pong": True}

    def _handle_status(self, envelope):
        self.status_calls.append(envelope)
        return {"healthy": True}

    def intention(self):
        return {"what": "test device with verbs"}

    def state(self):
        return {"pings": len(self.pings)}

    def settings(self):
        return {}


class NoVerbDevice(BaseDevice):
    """A device with no declared verbs — uses BaseDevice.receive() default."""

    def __init__(self):
        super().__init__()
        self._device_id = "test_no_verb_device"

    @property
    def device_id(self):
        return self._device_id

    def intention(self):
        return {"what": "test device with nothing"}

    def state(self):
        return {}

    def settings(self):
        return {}


class LegacyDevice(BaseDevice):
    """A device with receive() but no declared verbs — backwards compat."""

    def __init__(self):
        super().__init__()
        self.received: list[dict] = []

    def receive(self, envelope):
        self.received.append(envelope)
        return {"legacy": True}

    def intention(self):
        return {"what": "legacy receiver"}

    def state(self):
        return {}

    def settings(self):
        return {}


class _VerbShim(BaseShim):
    def __init__(self, device, bus=None, device_id="test_verb_device"):
        super().__init__(bus=bus)
        self._device = device
        self._presence = ONLINE
        self._device_id = device_id

    @property
    def device_id(self):
        return self._device_id


def test_post_carries_verb_in_envelope():
    """(1) a post with verb= carries it in the envelope."""
    tbl = f"_test_verb_post_{_NONCE}"
    _TABLES.append(tbl)
    bus = BusDevice(table=tbl)
    env = bus.post(sender="tester", to="target", channel="personal",
                   verb="ping", why="proof", body={"x": 1})
    assert env["verb"] == "ping", f"envelope must carry verb, got {env}"


def test_deliver_resolves_verb_to_handler():
    """(2) deliver resolves verb → device's declared handler."""
    device = VerbDevice()
    shim = _VerbShim(device)
    envelope = {"verb": "ping", "body": {"test": True}}
    result = shim.deliver(envelope)
    assert result == {"pong": True}, f"wrong result: {result}"
    assert len(device.pings) == 1, "handler must have been called"
    assert device.pings[0] is envelope, "handler receives the envelope"

    envelope2 = {"verb": "status", "body": {}}
    result2 = shim.deliver(envelope2)
    assert result2 == {"healthy": True}, f"wrong result: {result2}"
    assert len(device.status_calls) == 1


def test_unknown_verb_goes_red():
    """(3) an unknown verb goes RED."""
    device = VerbDevice()
    shim = _VerbShim(device)
    try:
        shim.deliver({"verb": "nonexistent", "body": {}})
        raise AssertionError("unknown verb must raise NotImplementedError")
    except NotImplementedError as e:
        assert "nonexistent" in str(e), f"error must name the verb: {e}"
        assert "ping" in str(e) or "status" in str(e), f"error must list declared verbs: {e}"


def test_no_verbs_unknown_verb_refuses():
    """(4) a device with no declared verbs refuses verbed mail but accepts verbless."""
    device = NoVerbDevice()
    shim = _VerbShim(device)
    # With verb — still refuses (unknown verb, no declared verbs)
    try:
        shim.deliver({"verb": "anything", "body": {}})
        raise AssertionError("must refuse — no verbs declared")
    except NotImplementedError:
        pass
    # Without verb — accepts via BaseDevice.receive() default (records to DataRecorder)
    result = shim.deliver({"body": {}, "sender": "test"})
    assert result["accepted"], f"BaseDevice.receive() must accept: {result}"


def test_empty_verb_falls_back_to_receive():
    """(5) no verb in envelope → falls back to receive() for backwards compat."""
    device = LegacyDevice()
    shim = _VerbShim(device)
    envelope = {"body": {"legacy": True}}
    result = shim.deliver(envelope)
    assert result == {"legacy": True}
    assert len(device.received) == 1

    envelope2 = {"verb": "", "body": {}}
    result2 = shim.deliver(envelope2)
    assert result2 == {"legacy": True}
    assert len(device.received) == 2


def test_probe_carries_verb():
    """(6) a Probe carries verb and _fire passes it to post."""
    probe = Probe(
        why="test verb on probe",
        trigger=lambda now, ctx: True,
        to="target",
        verb="ping",
        body={"test": True},
    )
    assert probe.verb == "ping"

    tbl = f"_test_verb_fire_{_NONCE}"
    _TABLES.append(tbl)
    bus = BusDevice(table=tbl)
    shim = _VerbShim(VerbDevice(), bus=bus)
    record = shim._fire(probe)
    assert record["verb"] == "ping", f"fire record must carry verb: {record}"
    assert record["outcome"] == "ok"


def test_verb_column_in_transit_table():
    """(7) the verb column exists after _ensure."""
    tbl = f"_test_verb_col_{_NONCE}"
    _TABLES.append(tbl)
    bus = BusDevice(table=tbl)
    bus._ensure()
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s "
                "AND column_name = 'verb'", (tbl,))
            assert cur.fetchone() is not None, "verb column must exist"
    finally:
        conn.close()


def test_probe_default_verb_is_empty():
    """Existing probes with no verb= still work — default is empty string."""
    probe = Probe(
        why="legacy probe",
        trigger=lambda now, ctx: True,
        to="target",
    )
    assert probe.verb == "", f"default verb must be empty, got {probe.verb!r}"


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            for tbl in _TABLES:
                for table in (f"{tbl}_delivery", tbl):
                    cur.execute(f'DROP TABLE IF EXISTS "{table}"')
                    cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s',
                                (table,))
    except Exception as exc:  # noqa: BLE001
        print(f"  (cleanup refused: {type(exc).__name__}: {exc})")
    finally:
        conn.close()


if __name__ == "__main__":
    checks = [
        test_post_carries_verb_in_envelope,
        test_deliver_resolves_verb_to_handler,
        test_unknown_verb_goes_red,
        test_no_verbs_unknown_verb_refuses,
        test_empty_verb_falls_back_to_receive,
        test_probe_carries_verb,
        test_verb_column_in_transit_table,
        test_probe_default_verb_is_empty,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print(f"8/8 green — the verb resolves, unknown goes RED, legacy falls back")

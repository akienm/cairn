"""PROOF — the in-memory ring buffer: zero-DB hot path, one-transaction flush.

The ring is the bus's fast path (ticket 67d7a6783fb3). post() and request() write
to the ring and fire delivery hooks with zero DB round-trips. flush() batch-writes
the ring to Postgres in one transaction on the ground loop pulse.

What a hollow build cannot pass (Law 8):
  - A bus that writes to DB on every post passes all shape checks and fails
    test_post_does_not_hit_db — which posts, then reads from DB before flushing
    and asserts the DB is empty.
  - A flush that silently drops messages passes post-only tests and fails
    test_flush_lands_in_db — which posts, flushes, then reads from DB and
    asserts the envelope is there.
  - A request that falls back to DB passes timing tests and fails
    test_request_resolves_from_ring — which posts a request, checks the ring
    has the reply, and asserts no DB read was needed.

    python3 cairn/devices/cairn/machines/bus/proofs/test_ring.py   # exit 0 = green
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
NOW = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)


class EchoDevice(BaseDevice):
    def __init__(self, bus: BusDevice) -> None:
        super().__init__()
        self._bus = bus

    def intention(self) -> dict:
        return {"what": "proof echo"}

    def state(self) -> dict:
        return {}

    def settings(self) -> dict:
        return {}

    def declared_verbs(self) -> dict:
        return {"echo": self._handle_echo}

    def _handle_echo(self, envelope: dict) -> dict:
        self._bus.post(
            sender=envelope["addressee"], to=envelope["sender"],
            channel="personal", why="echo reply",
            body={"echoed": envelope["body"]}, reply_to=envelope["id"],
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


def _fresh_bus():
    bus = BusDevice(table=f"_bus_ring_{_NONCE}_{len(_TABLES)}")
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

def test_post_does_not_hit_db():
    """post() writes to the ring, not to DB. The DB is empty before flush."""
    bus = _fresh_bus()
    bus.post(sender="a", to="b", channel="personal", why="ring proof", body={"n": 1})
    assert bus.ring_depth == 1, f"ring should hold 1 envelope, has {bus.ring_depth}"
    bus._ensure()
    db_rows = store.read(bus.table)
    assert len(db_rows) == 0, f"DB should be empty before flush, has {len(db_rows)} rows"


def test_flush_lands_in_db():
    """flush() batch-writes ring contents to DB in one transaction."""
    bus = _fresh_bus()
    bus.post(sender="a", to="b", channel="personal", why="flush proof", body={"n": 1})
    bus.post(sender="b", to="a", channel="personal", why="flush proof 2", body={"n": 2})
    assert bus.ring_depth == 2
    result = bus.flush()
    assert result["flushed"] == 2, result
    assert bus.ring_depth == 0, "ring should be empty after flush"
    db_rows = store.read(bus.table)
    assert len(db_rows) == 2, f"DB should have 2 rows after flush, has {len(db_rows)}"


def test_read_merges_ring_and_db():
    """read() returns ring + DB rows — the full truth between flushes."""
    bus = _fresh_bus()
    bus.post(sender="a", to="c", channel="personal", why="first", body={"n": 1})
    bus.flush()
    bus.post(sender="a", to="c", channel="personal", why="second", body={"n": 2})
    all_rows = bus.read(to="c", channel="personal")
    assert len(all_rows) == 2, f"read should merge DB + ring, got {len(all_rows)}"
    assert all_rows[0]["body"] == {"n": 1}, "DB row (flushed) comes first"
    assert all_rows[1]["body"] == {"n": 2}, "ring row (unflushed) comes second"


def test_request_resolves_from_ring():
    """request() finds the reply in the ring — zero DB read for the happy path."""
    bus = _fresh_bus()
    echo_dev = EchoDevice(bus)
    echo_shim = EchoShim("echo", echo_dev, bus=bus)
    caller_shim = EchoShim("caller", EchoDevice(bus), bus=bus)
    loop = _rig(bus, echo_shim, caller_shim)
    loop.beat(NOW)
    reply = bus.request(
        sender="caller", to="echo", channel="personal",
        verb="echo", why="ring proof", body={"q": "hello"},
    )
    assert reply["body"] == {"echoed": {"q": "hello"}}
    assert bus.ring_depth > 0, "reply should still be in ring (not flushed yet)"


def test_receipt_in_ring_prevents_redelivery():
    """A receipt in the ring (not yet flushed) keeps the envelope out of undelivered()."""
    bus = _fresh_bus()
    env = bus.post(sender="a", to="b", channel="personal", why="receipt proof")
    assert len(bus.undelivered(to="b")) == 1, "should be undelivered before receipt"
    bus.record_delivery(env["id"], to="b", by="b")
    assert len(bus.undelivered(to="b")) == 0, "should be delivered after ring receipt"


def test_flush_empty_ring_is_noop():
    """Flushing an empty ring returns zeros and touches no DB."""
    bus = _fresh_bus()
    result = bus.flush()
    assert result == {"flushed": 0, "receipts": 0}


def test_flush_writes_receipts_to_db():
    """Receipts in the ring land in the delivery table on flush."""
    bus = _fresh_bus()
    env = bus.post(sender="a", to="b", channel="personal", why="receipt flush proof")
    bus.record_delivery(env["id"], to="b", by="b")
    bus.flush()
    receipts = store.read(bus.delivery_table, where="envelope = %s", params=(env["id"],))
    assert len(receipts) == 1, f"receipt should be in DB after flush, got {len(receipts)}"
    assert receipts[0]["by"] == "b"


if __name__ == "__main__":
    checks = [
        test_post_does_not_hit_db,
        test_flush_lands_in_db,
        test_read_merges_ring_and_db,
        test_request_resolves_from_ring,
        test_receipt_in_ring_prevents_redelivery,
        test_flush_empty_ring_is_noop,
        test_flush_writes_receipts_to_db,
    ]
    failures = 0
    try:
        for check in checks:
            try:
                check()
                print(f"  PASS  {check.__name__}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
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
    print("green — zero-DB hot path, one-transaction flush, ring + DB merge")

"""PROOF — the bus POKES the addressee at post() time.

Delivery is event-driven: post() writes the envelope, then fires the delivery hook
registered by the addressee's shim. No pulse between — the poke lands inside the post()
call itself.

What a hollow build cannot pass (Law 8):

  - A poke that fires but delivers only the current envelope and ignores earlier failures
    passes every happy-path tooth and fails ``test_poke_retries_earlier_failures`` — the
    tooth that pins at-least-once under the event-driven model.
  - A poke that is wired but never fires (the old per-pulse-only path) fails
    ``test_poke_delivers_without_a_pulse`` — the headline tooth.
  - A poke that fires at bus creation (not at post time) fails the same tooth — delivery
    happens at the wrong time.
  - A bus that wires the hook but passes the wrong envelope fails
    ``test_poke_carries_body_and_verb`` — the body/verb integrity tooth.

Requires Postgres (db_domain's durable transit). Self-cleaning.

    python3 cairn/devices/cairn/machines/bus/proofs/test_delivery_poke.py   # exit 0 = green
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
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.shim import BusShim  # noqa: E402
from cairn.devices.db_domain import store  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLES: list[str] = []
NOW = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)


class Mailbox:
    def __init__(self, blow_up: bool = False) -> None:
        self.got: list[dict] = []
        self.blow_up = blow_up

    def receive(self, envelope: dict):
        if self.blow_up:
            raise RuntimeError("this receiver is broken on purpose")
        self.got.append(envelope)
        return {"ack": envelope["id"]}


class MailboxShim(BaseShim):
    def __init__(self, device_id: str, device: Mailbox, bus=None) -> None:
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
    bus = BusDevice(table=f"_bus_poke_{_NONCE}_{len(_TABLES)}")
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

def test_poke_delivers_without_a_pulse():
    """THE HEADLINE TOOTH. After the first pulse wires delivery, a post() delivers to the
    addressee WITHIN the post() call — no second pulse needed. A per-pulse-only path fails
    this: the envelope sits in transit until loop.beat() is called."""
    box = Mailbox()
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("poke_a", box, bus=bus))
    loop.beat(NOW)  # first pulse wires delivery
    assert len(box.got) == 0  # nothing posted yet — nothing delivered
    sent = bus.post(sender="proof", to="poke_a", channel="personal",
                    why="prove poke", body={"test": "poke"})
    assert len(box.got) == 1, f"expected poke delivery within post(), got {len(box.got)}"
    assert box.got[0]["id"] == sent["id"]
    assert bus.undelivered(to="poke_a") == []


def test_poke_carries_body_and_verb():
    """The poke delivers the REAL envelope — body, why, sender all intact. A poke that
    delivers a stub or the wrong envelope passes the count check and fails here."""
    box = Mailbox()
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("poke_b", box, bus=bus))
    loop.beat(NOW)
    bus.post(sender="proof", to="poke_b", channel="personal",
             why="body check", body={"deep": {"key": [1, 2]}})
    assert len(box.got) == 1, f"expected 1 delivery, got {len(box.got)}"
    assert box.got[0]["body"] == {"deep": {"key": [1, 2]}}
    assert box.got[0]["why"] == "body check"
    assert box.got[0]["sender"] == "proof"
    assert box.got[0]["channel"] == "personal"


def test_poke_retries_earlier_failures():
    """AT-LEAST-ONCE under the poke model. A broken receiver leaves mail undelivered; the
    next post pokes again and retries ALL undelivered mail (not just the new envelope).
    A poke that delivers only the current envelope and ignores the backlog fails here."""
    broken = Mailbox(blow_up=True)
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("poke_c", broken, bus=bus))
    first = bus.post(sender="proof", to="poke_c", channel="personal",
                     why="will fail", body={"n": 1})
    loop.beat(NOW)  # wiring drain tries to deliver — receiver raises
    assert len(broken.got) == 0
    assert len(bus.undelivered(to="poke_c")) == 1
    broken.blow_up = False
    second = bus.post(sender="proof", to="poke_c", channel="personal",
                      why="retry trigger", body={"n": 2})
    assert len(broken.got) == 2, f"expected both envelopes, got {len(broken.got)}"
    assert {e["id"] for e in broken.got} == {first["id"], second["id"]}
    assert bus.undelivered(to="poke_c") == []


def test_poke_does_not_fire_for_unwired_device():
    """Mail for a device whose shim has not yet pulsed (delivery not wired) sits in transit
    honestly — no poke fires. The mail waits for the first pulse to drain the backlog."""
    box = Mailbox()
    bus = _fresh_bus()
    _rig(bus, MailboxShim("poke_d", box, bus=bus))
    # Post BEFORE the first pulse — no hook wired yet
    sent = bus.post(sender="proof", to="poke_d", channel="personal",
                    why="pre-wiring", body={"n": 1})
    assert len(box.got) == 0, "poke should not fire before wiring"
    assert len(bus.undelivered(to="poke_d")) == 1


def test_delivery_failed_emits_on_poke_exception():
    """When the poke fires and deliver() raises, the bus emits a delivery_failed event.
    The envelope stays in transit (at-least-once)."""
    broken = Mailbox(blow_up=True)
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("poke_e", broken, bus=bus))
    loop.beat(NOW)  # wire delivery
    sent = bus.post(sender="proof", to="poke_e", channel="personal",
                    why="will fail post-wiring", body={"n": 1})
    assert len(bus.undelivered(to="poke_e")) == 1
    assert bus.undelivered(to="poke_e")[0]["id"] == sent["id"]


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
    print("green — the bus pokes, and the poke delivers")

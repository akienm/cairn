"""PROOF — mail ARRIVES. The half of the bus that had zero callers until 2026-08-11.

``post`` and ``read`` were proved the day the bus shipped. Nothing proved that anything ever
took a message OUT of transit and handed it to a device, because nothing did:
``BaseShim.deliver`` stood with zero callers, and from the sender's side a bus that never
delivers is indistinguishable from one that does — the post succeeds, the row lands, the read
shows the message sitting right there. Three envelopes were in transit when this was found.

WHAT A HOLLOW DELIVERY LAYER WOULD PASS AND THIS MUST NOT (Law 8):

  - One that marked mail delivered and dropped it passes "the inbox drains" and fails
    ``test_the_device_actually_receives_the_body``, which reads what the RECEIVER got.
  - One that wrote the receipt before handing the envelope over passes every happy path and
    fails ``test_a_receiver_that_raises_leaves_the_mail_in_the_inbox`` — the tooth that pins
    at-least-once as the side we fail on, because losing a record of truth is worse than
    delivering it twice.
  - One whose "undelivered" was a flag someone sets passes until a writer forgets; the
    anti-join here derives it, and ``test_a_delivered_envelope_never_comes_back`` re-drains.
  - One that returned ``None`` for a shim with nobody home passes "no exception, so it
    arrived" — the hole that was actually in ``BaseShim.deliver`` — and fails
    ``test_a_shim_with_no_device_refuses_instead_of_swallowing``.
  - One that reported the same stuck envelope every beat passes "it is loud" and fails
    ``test_a_stuck_envelope_is_reported_once_not_once_per_beat``, which is the difference
    between a finding and a firehose.

Requires Postgres (db_domain's durable transit). Self-cleaning: the ephemeral transit and
receipt tables are dropped on the way out.

    python3 cairn/devices/bus/proofs/test_delivery.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.shim import BaseShim, ONLINE  # noqa: E402
from cairn.devices.bus.bus import BusDevice  # noqa: E402
from cairn.devices.bus.shim import BusShim  # noqa: E402
from cairn.devices.db_domain import store  # noqa: E402
from cairn.devices.ground_loop.discovered import DiscoveredShim  # noqa: E402
from cairn.devices.ground_loop.loop import GroundLoopDevice  # noqa: E402

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLES: list[str] = []      # every ephemeral transit table this run made, for the drop
NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


class Mailbox:
    """A device that receives — the smallest honest receiver."""

    def __init__(self, blow_up: bool = False) -> None:
        self.got: list[dict] = []
        self.blow_up = blow_up

    def receive(self, envelope: dict):
        if self.blow_up:
            raise RuntimeError("this receiver is broken on purpose")
        self.got.append(envelope)
        return {"ack": envelope["id"]}


class MailboxShim(BaseShim):
    def __init__(self, device_id: str, device: Mailbox) -> None:
        super().__init__()
        self._device_id = device_id
        self._device = device
        self._presence = ONLINE

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        return self._device


def _rig(*shims):
    """A heartbeat with a postman and whatever receivers a tooth needs. The loop is built with
    no ``liveness_home`` and no discoverer: this proof is about delivery, so the beat is the
    anonymous in-process one and the roster is exactly what is handed in.

    A FRESH TRANSIT TABLE PER TOOTH. Several teeth deliberately leave mail stuck in the inbox
    (that is what they are proving), so a shared table would let one tooth's leftovers become
    another's phantom backlog — and the tooth would go red for a reason that has nothing to do
    with what it measures."""
    bus = BusDevice(table=f"_bus_traffic_{_NONCE}_{len(_TABLES)}")
    _TABLES.append(bus.table)
    loop = GroundLoopDevice()
    postman = BusShim(bus, loop)
    loop.subscribe(postman)
    for shim in shims:
        loop.subscribe(shim)
    return bus, loop, postman


def _post(bus, to, why="a tooth needs mail", body=None):
    return bus.post(sender="proof", to=to, channel="personal", why=why, body=body or {"n": 1})


# --- teeth ------------------------------------------------------------------

def test_the_device_actually_receives_the_body():
    """Not 'the inbox drained' — what the RECEIVER holds. A layer that marks mail delivered
    and drops it passes every count-based check and dies here."""
    box = Mailbox()
    bus, loop, _ = _rig(MailboxShim("box_a", box))
    sent = _post(bus, "box_a", why="prove arrival", body={"question": "are you there"})
    loop.beat(NOW)
    assert len(box.got) == 1, box.got
    assert box.got[0]["id"] == sent["id"]
    assert box.got[0]["body"] == {"question": "are you there"}
    assert box.got[0]["why"] == "prove arrival"      # the why rides all the way to the device


def test_a_delivered_envelope_never_comes_back():
    """The receipt is what makes 'undelivered' derivable. Re-beat twice: still one delivery."""
    box = Mailbox()
    bus, loop, _ = _rig(MailboxShim("box_a", box))
    _post(bus, "box_a")
    loop.beat(NOW)
    loop.beat(NOW)
    loop.beat(NOW)
    assert len(box.got) == 1, [e["id"] for e in box.got]
    assert bus.undelivered(to="box_a") == []


def test_a_receiver_that_raises_leaves_the_mail_in_the_inbox():
    """AT-LEAST-ONCE IS THE SIDE WE FAIL ON. The receipt is written after the device takes the
    envelope, so a receiver that blows up leaves the mail exactly where it was. A layer that
    receipts first passes every happy path and loses this message forever."""
    broken = Mailbox(blow_up=True)
    bus, loop, postman = _rig(MailboxShim("box_bad", broken))
    sent = _post(bus, "box_bad")
    record = loop.beat(NOW)
    found = [p for p in record["pulses"] if p["device"] == "bus"][0]["postman"]
    assert found["delivered"] == [], found
    assert found["findings"][0]["outcome"] == "refused"
    assert "broken on purpose" in found["findings"][0]["error"]
    still = bus.undelivered(to="box_bad")
    assert [e["id"] for e in still] == [sent["id"]], still
    # And it is delivered the moment the receiver is fixed — the mail waited, it did not die.
    broken.blow_up = False
    loop.beat(NOW)
    assert [e["id"] for e in broken.got] == [sent["id"]]
    assert bus.undelivered(to="box_bad") == []


def test_a_shim_with_no_device_refuses_instead_of_swallowing():
    """THE HOLE THAT WAS ACTUALLY THERE. ``BaseShim.deliver`` returned None for a shim holding
    no device, and a discovered shim is always-on with no device by construction — so the
    postman would have receipted mail nobody received. The refusal is what makes the postman
    able to tell 'nobody home' from 'delivered'."""
    bus, loop, _ = _rig(DiscoveredShim("disk_only", "/nowhere"))
    sent = _post(bus, "disk_only")
    record = loop.beat(NOW)
    found = [p for p in record["pulses"] if p["device"] == "bus"][0]["postman"]
    assert found["delivered"] == [], found
    assert found["findings"][0]["outcome"] == "no_receiver", found["findings"]
    assert [e["id"] for e in bus.undelivered(to="disk_only")] == [sent["id"]]


def test_mail_for_a_device_not_on_the_roster_waits():
    """You can only deliver to what is being beaten. Unaddressable mail is a reported finding
    and stays in transit — never a silent drop, never an error that stops the round."""
    box = Mailbox()
    bus, loop, _ = _rig(MailboxShim("box_a", box))
    ghost = _post(bus, "nobody_by_that_name")
    real = _post(bus, "box_a")
    record = loop.beat(NOW)
    found = [p for p in record["pulses"] if p["device"] == "bus"][0]["postman"]
    assert found["delivered"] == [real["id"]], found
    assert found["findings"][0]["outcome"] == "no_shim"
    assert [e["id"] for e in bus.undelivered()] == [ghost["id"]]
    assert len(box.got) == 1        # the round continued past the undeliverable one


def test_a_stuck_envelope_is_reported_once_not_once_per_beat():
    """The difference between a finding and a firehose. Stuck mail is re-tried every beat (it
    must be — the receiver may come up), but it is REPORTED at the crossing only."""
    bus, loop, _ = _rig(DiscoveredShim("disk_only", "/nowhere"))
    _post(bus, "disk_only")
    first = loop.beat(NOW)
    later = [loop.beat(NOW) for _ in range(5)]
    def findings(rec):
        return [p for p in rec["pulses"] if p["device"] == "bus"][0]["postman"]["findings"]
    assert len(findings(first)) == 1
    assert all(findings(r) == [] for r in later), [findings(r) for r in later]
    # Still retried, though — the envelope is in every round's 'waiting' count.
    waiting = [p for p in later[-1]["pulses"] if p["device"] == "bus"][0]["postman"]["waiting"]
    assert waiting == 1


def test_a_dead_store_does_not_stop_the_heartbeat():
    """CP2 at the substrate: a box whose Postgres is down still beats. The drain reports a
    refusal; the beat completes and every other shim is pulsed."""
    box = Mailbox()
    bus, loop, postman = _rig(MailboxShim("box_a", box))

    def dead(*a, **k):
        raise ConnectionError("could not connect to server: Connection refused")

    bus.undelivered = dead      # type: ignore[method-assign]
    record = loop.beat(NOW)
    assert record["pulsed"] == ["bus", "box_a"], record["pulsed"]
    found = [p for p in record["pulses"] if p["device"] == "bus"][0]["postman"]
    assert found["outcome"] == "refused"
    assert "Connection refused" in found["error"]


def test_the_postman_is_not_a_destination():
    """A message addressed to the bus itself must not be handed to the postman's own deliver —
    that would be the substrate delivering to the substrate, and the shim it would wake is the
    one already doing the delivering."""
    bus, loop, _ = _rig()
    _post(bus, "bus")
    record = loop.beat(NOW)
    found = [p for p in record["pulses"] if p["device"] == "bus"][0]["postman"]
    assert found["delivered"] == []
    assert found["findings"][0]["outcome"] == "no_shim"


def test_the_drain_is_one_query_however_many_devices():
    """The shape that shrinks. A per-device sweep would be a query per device per second — a
    poll wearing a heartbeat's clothes — and it would grow with every device added. Counted at
    the bus's own read face, with five receivers on the roster."""
    boxes = {f"box_{i}": Mailbox() for i in range(5)}
    bus, loop, _ = _rig(*[MailboxShim(name, box) for name, box in boxes.items()])
    for name in boxes:
        _post(bus, name)
    calls = {"n": 0}
    real = bus.undelivered

    def counting(**kw):
        calls["n"] += 1
        return real(**kw)

    bus.undelivered = counting  # type: ignore[method-assign]
    loop.beat(NOW)
    assert calls["n"] == 1, f"{calls['n']} queries for 5 devices — that is a per-device sweep"
    assert all(len(b.got) == 1 for b in boxes.values()), {k: len(v.got) for k, v in boxes.items()}


def test_a_receipt_appends_and_never_rewrites_the_envelope():
    """Law 7 at a record of truth: delivery is a separate EVENT, so the envelope on a record
    channel comes back out of transit bit-identical to the one that went in."""
    box = Mailbox()
    bus, loop, _ = _rig(MailboxShim("box_a", box))
    sent = _post(bus, "box_a", body={"deep": {"nested": [1, 2, 3]}})
    before = bus.read(to="box_a")[0]
    loop.beat(NOW)
    after = bus.read(to="box_a")[0]
    assert after == before, (before, after)
    receipts = store.read(bus.delivery_table, where="envelope = %s", params=(sent["id"],))
    assert len(receipts) == 1 and receipts[0]["by"] == "bus"


if __name__ == "__main__":
    failures = 0
    try:
        for name, fn in sorted(globals().items()):
            if not name.startswith("test_") or not callable(fn):
                continue
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as exc:  # noqa: BLE001 — the proof reports, it does not raise
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
        except Exception as exc:  # noqa: BLE001 — cleanup is best-effort, and says so out loud
            print(f"  (cleanup refused: {type(exc).__name__}: {exc})")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — mail arrives, the receipt is the proof, and nothing is lost on the way")

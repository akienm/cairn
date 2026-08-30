"""PROOF — mail ARRIVES. The half of the bus that had zero callers until 2026-08-11.

``post`` and ``read`` were proved the day the bus shipped. Nothing proved that anything ever
took a message OUT of transit and handed it to a device, because nothing did:
``BaseShim.deliver`` stood with zero callers, and from the sender's side a bus that never
delivers is indistinguishable from one that does — the post succeeds, the row lands, the read
shows the message sitting right there. Three envelopes were in transit when this was found.

REWRITTEN 2026-08-29 for event-driven delivery: ``post()`` pokes the addressee's shim at post
time (``_receive_poke``), and the first pulse wires delivery and drains any backlog
(``_wire_delivery``). The per-pulse ``_check_mail`` poll is gone — delivery is event-driven.
What a hollow build STILL cannot pass (Law 8):

  - One that marked mail delivered and dropped it passes "the inbox drains" and fails
    ``test_the_device_actually_receives_the_body``, which reads what the RECEIVER got.
  - One that wrote the receipt before handing the envelope over passes every happy path and
    fails ``test_a_receiver_that_raises_leaves_the_mail_in_the_inbox`` — the tooth that pins
    at-least-once as the side we fail on, because losing a record of truth is worse than
    delivering it twice.
  - One whose "undelivered" was a flag someone sets passes until a writer forgets; the
    anti-join here derives it, and ``test_a_delivered_envelope_never_comes_back`` re-beats.
  - One that returned ``None`` for a shim with nobody home passes "no exception, so it
    arrived" — and fails ``test_a_discovered_shim_cannot_receive`` (a DiscoveredShim cannot
    wake a device; mail waits honestly).

Requires Postgres (db_domain's durable transit). Self-cleaning: the ephemeral transit and
receipt tables are dropped on the way out.

    python3 cairn/devices/cairn/machines/bus/proofs/test_delivery.py     # exit 0 = green
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
from cairn.devices.cairn.machines.ground_loop.discovered import DiscoveredShim  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402

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
    """A fresh bus with its own ephemeral tables, tracked for cleanup."""
    bus = BusDevice(table=f"_bus_traffic_{_NONCE}_{len(_TABLES)}")
    _TABLES.append(bus.table)
    return bus


def _rig(bus, *shims):
    """A heartbeat with receivers. The first pulse wires event-driven delivery; subsequent
    posts poke the shim directly. The loop is built with no liveness_home and no discoverer:
    this proof is about delivery, so the beat is the anonymous in-process one and the
    roster is exactly what is handed in.

    Bus is passed in so shims can be constructed with it before the rig is built."""
    loop = GroundLoopDevice(bus=bus)
    bus_shim = BusShim(bus, loop)
    loop.subscribe(bus_shim)
    for shim in shims:
        loop.subscribe(shim)
    return loop


def _post(bus, to, why="a tooth needs mail", body=None):
    return bus.post(sender="proof", to=to, channel="personal", why=why, body=body or {"n": 1})


def _mail_result(record, device_id):
    """Extract the mail result from a specific device's pulse record."""
    for p in record["pulses"]:
        if p["device"] == device_id:
            return p.get("mail")
    return None


# --- teeth ------------------------------------------------------------------

def test_the_device_actually_receives_the_body():
    """Not 'the inbox drained' — what the RECEIVER holds. A layer that marks mail delivered
    and drops it passes every count-based check and dies here."""
    box = Mailbox()
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("box_a", box, bus=bus))
    sent = _post(bus, "box_a", why="prove arrival", body={"question": "are you there"})
    loop.beat(NOW)
    assert len(box.got) == 1, box.got
    assert box.got[0]["id"] == sent["id"]
    assert box.got[0]["body"] == {"question": "are you there"}
    assert box.got[0]["why"] == "prove arrival"      # the why rides all the way to the device


def test_a_delivered_envelope_never_comes_back():
    """The receipt is what makes 'undelivered' derivable. Re-beat twice: still one delivery."""
    box = Mailbox()
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("box_a", box, bus=bus))
    _post(bus, "box_a")
    loop.beat(NOW)
    loop.beat(NOW)
    loop.beat(NOW)
    assert len(box.got) == 1, [e["id"] for e in box.got]
    assert bus.undelivered(to="box_a") == []


def test_a_receiver_that_raises_leaves_the_mail_in_the_inbox():
    """AT-LEAST-ONCE IS THE SIDE WE FAIL ON. The receipt is written after the device takes the
    envelope, so a receiver that blows up leaves the mail exactly where it was. A layer that
    receipts first passes every happy path and loses this message forever.

    Delivery is event-driven: the bus pokes at post() time and the shim drains its backlog at
    wiring time (first pulse). After the first-pulse drain fails, mail waits until the NEXT POST
    triggers a poke — which retries ALL undelivered mail, including earlier failures."""
    broken = Mailbox(blow_up=True)
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("box_bad", broken, bus=bus))
    sent = _post(bus, "box_bad")
    loop.beat(NOW)
    mail = _mail_result(loop._last_beat, "box_bad") or {}
    assert mail.get("delivered") == [], mail
    assert mail.get("refused", []) != []
    still = bus.undelivered(to="box_bad")
    assert [e["id"] for e in still] == [sent["id"]], still
    # The receiver is fixed. The next POST pokes the shim, which retries all undelivered mail.
    broken.blow_up = False
    retry = _post(bus, "box_bad", why="retry trigger")
    assert len(broken.got) == 2, [e["id"] for e in broken.got]
    assert {e["id"] for e in broken.got} == {sent["id"], retry["id"]}
    assert bus.undelivered(to="box_bad") == []


def test_a_discovered_shim_cannot_receive():
    """A DiscoveredShim exists for probes only — it cannot wake a device. Mail addressed to
    a discovered-only device stays in transit honestly (NotImplementedError, not a silent drop)."""
    bus = _fresh_bus()
    loop = _rig(bus, DiscoveredShim("disk_only", "/nowhere", bus=bus))
    sent = _post(bus, "disk_only")
    loop.beat(NOW)
    mail = _mail_result(loop._last_beat, "disk_only") or {}
    assert mail.get("outcome") == "no_receiver", mail
    assert [e["id"] for e in bus.undelivered(to="disk_only")] == [sent["id"]]


def test_mail_for_a_device_not_on_the_roster_sits():
    """Mail for a device with no shim at all sits in transit — no shim means no delivery
    hook wired, so no poke fires. The real device's mail is still delivered."""
    box = Mailbox()
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("box_a", box, bus=bus))
    ghost = _post(bus, "nobody_by_that_name")
    real = _post(bus, "box_a")
    loop.beat(NOW)
    assert len(box.got) == 1
    assert box.got[0]["id"] == real["id"]
    assert [e["id"] for e in bus.undelivered()] == [ghost["id"]]


def test_a_dead_store_does_not_stop_the_heartbeat():
    """CP2 at the substrate: a box whose Postgres is down still beats. The shim's mail check
    reports nothing; the beat completes and every other shim is pulsed."""
    box = Mailbox()
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("box_a", box, bus=bus))

    def dead(**kw):
        raise ConnectionError("could not connect to server: Connection refused")

    bus.undelivered = dead      # type: ignore[method-assign]
    record = loop.beat(NOW)
    assert "box_a" in record["pulsed"], record["pulsed"]
    mail = _mail_result(record, "box_a")
    assert mail is None


def test_a_receipt_appends_and_never_rewrites_the_envelope():
    """Law 7 at a record of truth: delivery is a separate EVENT, so the envelope on a record
    channel comes back out of transit bit-identical to the one that went in. The receipt's
    ``by`` is the receiving device (self-serve), not the postman."""
    box = Mailbox()
    bus = _fresh_bus()
    loop = _rig(bus, MailboxShim("box_a", box, bus=bus))
    sent = _post(bus, "box_a", body={"deep": {"nested": [1, 2, 3]}})
    before = bus.read(to="box_a")[0]
    loop.beat(NOW)
    after = bus.read(to="box_a")[0]
    assert after == before, (before, after)
    receipts = store.read(bus.delivery_table, where="envelope = %s", params=(sent["id"],))
    assert len(receipts) == 1 and receipts[0]["by"] == "box_a"


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
    print("green — mail arrives, each shim self-serves, and nothing is lost on the way")

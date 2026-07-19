"""Proof for the bus — the sole path for inter-device communication, made durable.

The bus is the second substrate (the heartbeat is the first). This proof exercises it as a
real device composing db_domain: a message posted is an owned transit row, read back whole;
the channel classification is physics (Law 7); every envelope carries its why + causality
(Law 5).

Teeth a hollow bus could not pass:
  - A MESSAGE ROUND-TRIPS WITH ITS WHY + CAUSALITY (Law 5). post → read returns the envelope
    with sender, why, reply_to intact and in causal order. A hollow bus that dropped the
    message, or lost its why/reply_to, trips this.
  - AN UNKNOWN CHANNEL IS REFUSED LOUDLY (CP1); a message with NO WHY is refused (CP3).
  - RECORD vs DIAGNOSTIC IS PHYSICS (Law 7). A record channel (announce/personal) REFUSES to
    collapse into a digest; a diagnostic channel (info/debug) collapses to a count + tail — yet
    read STILL returns the full truth (the substrate never collapses, only the view does).
  - TRANSIT IS OWNER-GATED (Law 6). The traffic table is owned by 'bus'; a non-bus write is
    refused by db_domain's gate — the bus is the sole writer, on behalf of attributed senders.
  - IT IS A DEVICE (Law 2 / Form v0 #2).

Requires Postgres (db_domain's durable transit). Self-cleaning: the ephemeral traffic table
is dropped on the way out.

    python3 cairn/bus/proofs/test_bus.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CoreValuesMixin
from cairn.bus.bus import BusDevice, ChannelError
from cairn.db_domain import store
from cairn.db_domain.store import OwnershipError

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TABLE = f"_bus_traffic_{_NONCE}"     # the ephemeral transit table this proof owns


def _fresh_bus() -> BusDevice:
    return BusDevice(table=_TABLE)


def test_a_message_round_trips_with_why_and_causality():
    bus = _fresh_bus()
    first = bus.post(sender="alice", to="bob", channel="personal",
                     why="ask bob to wake", body={"ping": 1})
    reply = bus.post(sender="bob", to="alice", channel="personal",
                     why="answer alice", body={"pong": 1}, reply_to=first["id"])

    # Bob's feed carries alice's message, whole — why + body intact (Law 5).
    bobs = bus.read(to="bob", channel="personal")
    assert len(bobs) == 1 and bobs[0]["sender"] == "alice"
    assert bobs[0]["why"] == "ask bob to wake" and bobs[0]["body"] == {"ping": 1}

    # Causality survives: the reply points at the message it answers.
    alices = bus.read(to="alice", channel="personal")
    assert len(alices) == 1 and alices[0]["reply_to"] == first["id"], "reply_to must link cause→effect"
    assert bus.state()["posted"] == 2


def test_an_unknown_channel_and_a_whyless_message_are_refused():
    bus = _fresh_bus()
    try:
        bus.post(sender="a", to="b", channel="gossip", why="w")
        raise AssertionError("an unknown channel must be refused (CP1)")
    except ChannelError:
        pass
    try:
        bus.post(sender="a", to="b", channel="info", why="")
        raise AssertionError("a message with no why must be refused (CP3)")
    except ValueError:
        pass


def test_record_channel_refuses_to_collapse_diagnostic_may():
    bus = _fresh_bus()
    # A record of truth: five announces. read returns all five; digest REFUSES (Law 7).
    for i in range(5):
        bus.post(sender="sys", to="all", channel="announce", why="fact", body={"n": i})
    assert len(bus.read(to="all", channel="announce")) == 5
    try:
        bus.digest(to="all", channel="announce")
        raise AssertionError("a record channel must refuse to collapse into a digest (Law 7)")
    except ChannelError:
        pass

    # A diagnostic channel: five debug lines. The VIEW collapses to count + tail...
    for i in range(5):
        bus.post(sender="sys", to="sys", channel="debug", why="trace", body={"n": i})
    d = bus.digest(to="sys", channel="debug", keep=2)
    assert d["count"] == 5 and d["collapsed"] == 3 and len(d["tail"]) == 2
    # ...yet the SUBSTRATE is untouched: read still returns the full five (Law 7).
    assert len(bus.read(to="sys", channel="debug")) == 5, "the substrate never collapses, only the view"


def test_transit_is_owner_gated():
    bus = _fresh_bus()
    bus.post(sender="a", to="b", channel="info", why="ensure the table exists")
    # The transit table is the bus's; a non-bus writer is refused by db_domain's gate (Law 6).
    assert store.owner_of(_TABLE) == "bus"
    try:
        store.write(_TABLE, "impostor", {"id": "x", "sender": "x", "addressee": "y",
                                         "channel": "info", "kind": "diagnostic", "why": "w",
                                         "body": {}, "reply_to": None, "date": "now"})
        raise AssertionError("only the bus may write transit — a non-owner write must be refused (Law 6)")
    except OwnershipError:
        pass


def test_it_is_a_device():
    bus = _fresh_bus()
    assert isinstance(bus, CoreValuesMixin), "a device must compose the core values (Law 2)"
    assert [v.id for v in bus.CORE_VALUES] == ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]
    assert list(bus.introspect()) == ["intention", "state", "settings", "other"], "Form v0 #2 order"


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_a_message_round_trips_with_why_and_causality,
        test_an_unknown_channel_and_a_whyless_message_are_refused,
        test_record_channel_refuses_to_collapse_diagnostic_may,
        test_transit_is_owner_gated,
        test_it_is_a_device,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — bus: one substrate for all comms; messages round-trip with why + causality, "
          "records refuse to collapse while diagnostics may, transit is owner-gated through db_domain")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

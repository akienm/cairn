"""Teeth for ticket 976b5a8512c8 — the bus retires a ruled set of requests and their replies
through its own door, and nothing else.

Akien, 2026-10-18: *"THERE SHOULD BE NO ROWS FOR TROUBLE TICKETS"* and *"those wrong and bad
things all deleted once it's fixed."* Ticket ee04bb869795 moved every trouble reader off the bus;
the rows it left — measured 2026-10-19, 5,274 requests to trouble on live/clears/clear, the 5,274
replies naming them and 10,548 receipts — had no door to leave by. The bus owns ``bus_traffic``
(db_domain owner ``bus``), so only the bus deletes from it (Law 6), and it says what it deleted
(Law 7).

Every tooth runs over a bus of its own, ``BusDevice.scratch()``. The fixture, posted as the live
rows were: three ``live`` requests to trouble and one ``clears`` request, each with its reply
(``reply_to`` set) and a receipt for request and reply alike, one ``clear`` request that the
retire does not name, one menu row from trouble to trouble on ``announce`` (verb ''), and two rows
between other devices; all of it flushed, and then one more ``live`` request with its reply left in
the ring. Retiring ``addressee='trouble', verbs=['live', 'clears']`` must take exactly the five
requests, five replies and eight flushed receipts.

  1. THE MATCHED ROWS GO. No request, reply or receipt of the retired set reads back.
  2. EVERYTHING ELSE STANDS. The ``clear`` request, its reply, the menu row and both
     other-device rows read back whole; the table total falls by exactly the eight flushed
     envelopes retired.
  3. THE COUNT IS SAID TWICE. The return value and the emitted ``retired`` record both carry
     requests 5, replies 5, receipts 8 and the why.
  4. A BLANK IS REFUSED. An empty verb list, a blank why or a blank addressee raises
     ValueError and deletes nothing.
  5. THE RING IS RETIRED TOO. The request and reply still in the ring when retire runs are
     gone, and a later flush does not land them.

The subject is bound at call time, so ``cairn test --hollow`` reverting bus.py reads as red teeth
rather than an import that never ran.

    bin/cairn test cairn/devices/cairn/machines/bus/proofs/test_a_ruled_retire_deletes_requests_and_replies.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "976b5a8512c8": {
        "1": "the_matched_rows_go",
        "2": "everything_else_stands",
        "3": "the_count_is_said_twice",
        "4": "a_blank_is_refused",
        "5": "the_ring_is_retired_too",
    },
}

T = "retire-proof-trouble"
WHY = "the ruled-retire proof's fixture"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:400]}")
    if not ok:
        FAILURES.append(name)


def _bus_class():
    import importlib
    return importlib.import_module("cairn.devices.cairn.machines.bus.bus").BusDevice


class _Recorder:
    def __init__(self):
        self.records = []

    def receive_diagnostic(self, record):
        self.records.append(record)


def _ask(bus, sender, verb, *, receipt=True):
    """One request to T and its reply, as the trouble lane posted them; both ids."""
    req = bus.post(sender=sender, to=T, channel="personal", verb=verb, why=WHY, body={})
    rep = bus.post(sender=T, to=sender, channel="personal", why=WHY,
                   body={"rows": [verb]}, reply_to=req["id"])
    if receipt:
        bus.record_delivery(req["id"], to=T, by=T)
        bus.record_delivery(rep["id"], to=sender, by=sender)
    return req["id"], rep["id"]


def _fill(bus):
    """The flushed fixture plus a ring-held pair; the id sets the teeth compare."""
    retired, kept = [], []
    for sender in ("pane", "socket", "cli"):
        retired += _ask(bus, sender, "live")
    retired += _ask(bus, "counting", "clears")
    kept += _ask(bus, "cli", "clear")
    kept.append(bus.post(sender=T, to=T, channel="announce", why="menu published at wiring",
                         body={"verbs": ["live"]})["id"])
    kept.append(bus.post(sender="alpha", to="beta", channel="personal", verb="live", why=WHY)["id"])
    kept.append(bus.post(sender="beta", to="alpha", channel="personal", why=WHY,
                         reply_to=kept[-1])["id"])
    bus.flush()
    ring = list(_ask(bus, "pane", "live", receipt=False))
    return retired, kept, ring


def _table_ids(bus):
    from cairn.devices.db_domain.tools.client import store
    return {r["id"] for r in store.query("SELECT id FROM {t}", tables={"t": bus.table})}


def _receipt_envelopes(bus):
    from cairn.devices.db_domain.tools.client import store
    return {r["envelope"] for r in store.query("SELECT envelope FROM {d}",
                                               tables={"d": bus.delivery_table})}


def _all_ids(bus):
    return {r["id"] for r in bus.read()}


def main() -> int:
    BusDevice = _bus_class()
    with BusDevice.scratch(prefix="bus_traffic_retire_proof") as bus:
        rec = _Recorder()
        bus.set_diagnostic_receiver(rec)
        retired, kept, ring = _fill(bus)
        before = _table_ids(bus)

        # 4 first: a refused retire must touch nothing the later teeth read.
        name = PROVES["976b5a8512c8"]["4"]
        refused = []
        for kw in ({"addressee": T, "verbs": [], "why": "proof"},
                   {"addressee": T, "verbs": ["live"], "why": "  "},
                   {"addressee": "", "verbs": ["live"], "why": "proof"}):
            try:
                getattr(bus, "retire")(**kw)
            except ValueError:
                refused.append(True)
            except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
                refused.append(f"{type(exc).__name__}: {exc}")
            else:
                refused.append(False)
        check(name, refused == [True, True, True] and _table_ids(bus) == before,
              f"refusals {refused}; table unchanged={_table_ids(bus) == before}")

        try:
            got = bus.retire(addressee=T, verbs=["live", "clears"],
                             why="the ruled-retire proof")
        except Exception as exc:  # noqa: BLE001
            got = {"error": f"{type(exc).__name__}: {exc}"}
        after = _table_ids(bus)
        receipts = _receipt_envelopes(bus)
        seen = _all_ids(bus)

        name = PROVES["976b5a8512c8"]["1"]
        gone = set(retired) | set(ring)
        check(name, not (gone & seen) and not (gone & receipts),
              f"still read back: {len(gone & seen)}; receipts standing: {len(gone & receipts)}; "
              f"retire returned {got}")

        name = PROVES["976b5a8512c8"]["2"]
        check(name, set(kept) <= seen and set(kept) <= after and len(before) - len(after) == 8,
              f"kept standing {len(set(kept) & seen)}/{len(kept)}; table fell by "
              f"{len(before) - len(after)} (want 8 flushed retired envelopes)")

        name = PROVES["976b5a8512c8"]["3"]
        want = {"requests": 5, "replies": 5, "receipts": 8}
        emitted = [r for r in rec.records if r.get("gate") == "retired"]
        vals = emitted[-1]["values"] if emitted else {}
        ok3 = (isinstance(got, dict) and all(got.get(k) == v for k, v in want.items())
               and got.get("why") == "the ruled-retire proof"
               and len(emitted) == 1 and all(vals.get(k) == v for k, v in want.items())
               and vals.get("why") == "the ruled-retire proof")
        check(name, ok3, f"returned {got}; emitted {vals}")

        name = PROVES["976b5a8512c8"]["5"]
        bus.flush()
        landed = set(ring) & _table_ids(bus)
        check(name, not landed and not (set(ring) & _all_ids(bus)),
              f"ring-held ids landed after flush: {len(landed)}")

    print(f"{5 - len(FAILURES)} passed, {len(FAILURES)} failed out of 5")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

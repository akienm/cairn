"""PROOF for ticket b30069239480: mail the bus has not delivered for 600 seconds raises a trouble.

Akien 2026-10-18 (his component outline, the bus entry): *"the bus unable to wake a shim for
600 seconds sends trouble ticket. that was supposed to be the whole package."* Measured the
same day on the live bus: two personal envelopes stood undelivered 122h and 135h (replies to
constrain and to sail, askers that had stopped waiting) and no trouble named either.

The teeth, each on its own scratch bus:

  * mail that stands 600s raises at the flush — a reply to a shimless asker (it stands by
    design, 7cb1989e7825) dated 700s back raises exactly one ``mail-<to>-stood-600s`` when
    ``op_flush`` runs, its detail naming the envelope;
  * it is raised once — a second flush raises nothing new for the same envelope;
  * younger mail is not raised — an envelope dated now raises nothing;
  * the flush still flushes — ``op_flush`` keeps its ``flushed`` / ``receipts`` keys, and no
    stood envelope is receipted or re-delivered by the report (bus clause 5: a trouble is a
    report, never a delivery on a tick).

Every bus rides ``BusDevice.scratch``; every name is ``testing-b300-...`` so a leak explains
itself; the bus's diagnostics go to a list, never the live trouble lane.

    python3 cairn/devices/cairn/machines/bus/proofs/test_mail_that_stands_600s_raises.py
"""
from __future__ import annotations

import contextlib
import sys
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.server import BusProcess  # noqa: E402

PROVES = {"b30069239480": {
    "all": "mail_that_stands_600s_raises_at_the_flush",
    "exactly one trouble per stuck envelope": "it_is_raised_once",
    "none for an envelope younger than 600s": "younger_mail_is_not_raised",
    "all bus proofs stay green": "the_flush_still_flushes",
}}

_SCRATCH = contextlib.ExitStack()
PASS = 0
FAIL = 0
_ASKER = "testing-b300-asker"


class _Inbox:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)

    def raised(self) -> list[dict]:
        return [r for r in self.records if r.get("gate") == "raise_trouble"]


def _rig():
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_b300"))
    inbox = _Inbox()
    bus.set_diagnostic_receiver(inbox)
    return bus, BusProcess(bus), inbox


def _reply(bus, *, age_s: int) -> dict:
    """A reply to a shimless asker — mail that stands by design — dated ``age_s`` back."""
    env = bus.post(sender="testing-b300-answerer", to=_ASKER, channel="personal",
                   why="testing-b300 a reply nobody took", reply_to="testing-b300-request-id")
    env["date"] = (datetime.now() - timedelta(seconds=age_s)).isoformat(timespec="seconds")
    return env


def _stood(inbox) -> list[dict]:
    return [r for r in inbox.raised()
            if (r.get("values") or {}).get("identity") == f"mail-{_ASKER}-stood-600s"
            or r.get("pointer") == f"mail-{_ASKER}-stood-600s"]


def _names(record: dict, envelope_id: str) -> bool:
    return envelope_id in repr(record)


def mail_that_stands_600s_raises_at_the_flush():
    bus, proc, inbox = _rig()
    env = _reply(bus, age_s=700)
    proc.answer({"op": "flush"}, in_process=True)
    stood = _stood(inbox)
    assert len(stood) == 1, (
        f"expected one mail-{_ASKER}-stood-600s after the flush, got {len(stood)}: "
        f"{inbox.raised()}")
    assert _names(stood[0], env["id"]), f"the trouble does not name the envelope: {stood[0]}"


def it_is_raised_once():
    bus, proc, inbox = _rig()
    _reply(bus, age_s=700)
    proc.answer({"op": "flush"}, in_process=True)
    proc.answer({"op": "flush"}, in_process=True)
    stood = _stood(inbox)
    assert len(stood) == 1, f"two flushes raised {len(stood)} troubles for one envelope"


def younger_mail_is_not_raised():
    bus, proc, inbox = _rig()
    old = _reply(bus, age_s=700)
    young = _reply(bus, age_s=5)
    proc.answer({"op": "flush"}, in_process=True)
    stood = _stood(inbox)
    assert stood and _names(stood[0], old["id"]), f"the aged envelope was not raised: {stood}"
    assert not any(_names(r, young["id"]) for r in stood), (
        f"an envelope 5s old was raised: {stood}")


def the_flush_still_flushes():
    bus, proc, inbox = _rig()
    env = _reply(bus, age_s=700)
    reply = proc.answer({"op": "flush"}, in_process=True)
    body = reply.get("json") or {}
    assert reply.get("ok") and "flushed" in body and "receipts" in body, (
        f"op_flush lost its flush keys: {reply}")
    assert env["id"] in {e["id"] for e in bus.undelivered(to=_ASKER, limit=1000)}, (
        "the report receipted or delivered the stood envelope")


TEETH = [mail_that_stands_600s_raises_at_the_flush,
         it_is_raised_once,
         younger_mail_is_not_raised,
         the_flush_still_flushes]


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {fn.__name__}")


if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn)
    finally:
        _SCRATCH.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

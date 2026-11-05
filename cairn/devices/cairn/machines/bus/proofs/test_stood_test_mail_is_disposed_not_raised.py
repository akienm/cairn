#!/usr/bin/env python3
"""Proof that testing-marked mail that stands 600s is disposed of, never raised (ticket 6357c2eeff7c).

Measured 2026-11-05: 4 mail-testing-d0c8c4b4283e-caller-*-stood-600s troubles stood live, raised
by the bus's report_stood for replies d0c8c4b4283e's proof read but never took; cleared by cc,
they were raised again at 14:39 UTC when the bus restarted and forgot _stood_reported. Both kinds
of testing reply carry the mark (shim.deliver stamps a perform mark onto the verb reply;
_return_if_marked posts {testing: mark, is_return: True}). Akien's ruling on ticket 71d1bbfa98b0:
debris born of a test is flagged and disposed of. Sibling of b3386f431ae3 (the bounce half).

Teeth, one per falsifier clause (PROVES below), on the bus's own in-process scratch rig (the rig
of test_mail_that_stands_600s_raises.py), every name ``testing-6357c2eeff7c-<label>-<uuid8>``,
the bus's diagnostics to a list, never the live lane:
  (1) a marked reply dated 700s back raises no stood trouble at the flush, leaves transit
      receipted by 'bus-test-mail-disposed', and the bus emits test_mail_disposed once for it;
  (2) the control: an unmarked one still raises exactly one mail-<to>-stood-600s.

    PYTHONPATH=. python3 cairn/devices/cairn/machines/bus/proofs/test_stood_test_mail_is_disposed_not_raised.py
"""
from __future__ import annotations

import contextlib
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"6357c2eeff7c": {
    "1": "test_marked_stood_mail_is_disposed_not_raised",
    "2": "test_unmarked_stood_mail_still_raises",
}}

_TICKET = "6357c2eeff7c"
_SCRATCH = contextlib.ExitStack()
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _name(label: str) -> str:
    return f"testing-{_TICKET}-{label}-{uuid.uuid4().hex[:8]}"


class _Inbox:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)

    def gate(self, gate: str) -> list[dict]:
        return [r for r in self.records if r.get("gate") == gate]


def _stood_reply(marked: bool):
    """A scratch bus and its bus process; one reply to a shimless asker, dated 700s back, then
    the flush."""
    from cairn.devices.cairn.machines.bus.bus import BusDevice
    from cairn.devices.cairn.machines.bus.server import BusProcess
    from cairn.tools.base import testing_mark

    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_6357"))
    inbox = _Inbox()
    bus.set_diagnostic_receiver(inbox)
    proc = BusProcess(bus)
    asker = _name("asker")
    body = {testing_mark.FIELD: testing_mark.mark(_TICKET)} if marked else {}
    env = bus.post(sender=_name("answerer"), to=asker, channel="personal",
                   why=f"testing-{_TICKET} a reply nobody took",
                   reply_to=f"testing-{_TICKET}-request", body=body)
    env["date"] = (datetime.now() - timedelta(seconds=700)).isoformat(timespec="seconds")
    proc.answer({"op": "flush"}, in_process=True)
    stood = [r for r in inbox.gate("raise_trouble")
             if r.get("pointer") == f"mail-{asker}-stood-600s"]
    return bus, inbox, env, asker, stood


def test_marked_stood_mail_is_disposed_not_raised() -> None:
    bus, inbox, env, asker, stood = _stood_reply(marked=True)
    lacks = []
    if stood:
        lacks.append(f"raised {[r.get('pointer') for r in stood]}")
    if env["id"] in {e["id"] for e in bus.undelivered(to=asker, limit=1000)}:
        lacks.append("the envelope still sits in transit")
    by = [(r.get("values") or {}).get("by") for r in inbox.gate("delivered")
          if r.get("pointer") == env["id"]]
    if by != ["bus-test-mail-disposed"]:
        lacks.append(f"the envelope was receipted by {by!r}, want ['bus-test-mail-disposed']")
    disposed = [r for r in inbox.gate("test_mail_disposed")
                if (r.get("values") or {}).get("envelope") == env["id"]]
    if len(disposed) != 1:
        lacks.append(f"{len(disposed)} test_mail_disposed emissions for the envelope, want 1")
    check("test_marked_stood_mail_is_disposed_not_raised", not lacks, "; ".join(lacks))


def test_unmarked_stood_mail_still_raises() -> None:
    _bus, _inbox, _env, _asker, stood = _stood_reply(marked=False)
    check("test_unmarked_stood_mail_still_raises", len(stood) == 1,
          f"{len(stood)} mail-<asker>-stood-600s raised; want 1")


def main() -> int:
    try:
        for tooth in (test_marked_stood_mail_is_disposed_not_raised,
                      test_unmarked_stood_mail_still_raises):
            try:
                tooth()
            except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    finally:
        _SCRATCH.close()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

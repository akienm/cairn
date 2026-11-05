#!/usr/bin/env python3
"""Proof that testing-marked mail nobody can take never raises a live trouble (ticket b3386f431ae3).

Measured 2026-11-05: ~/.cairn/devices/trouble/0/last_known.json carried 13
mail-testing-*-has-no-receiver identities and ~/.cairn/logs/bus/0 held 16 raise_trouble logs for
testing names. ad7caca4d54c's proofs post testing-marked mail between shimless testing names on
the live bus; the postman bounces it, the bounce cannot land either, and
_raise_undeliverable_bounce raises it as if it were a real red. The bounce body is built from
scratch, so the mark never reached the place that decides. Akien's ruling on ticket 71d1bbfa98b0:
debris born of a test is flagged and disposed of, and what a flagged input bears inherits the flag.

Teeth, one per falsifier clause (PROVES below), on the bus's own in-process scratch rig (the rig
of test_mail_without_a_receiver.py; the bus's proofs may use the bus's scratch), every name
``testing-b3386f431ae3-<label>-<uuid8>``, the bus's diagnostics to a list, never the live lane:
  (1) the bounce of a testing-marked envelope carries the same mark;
  (2) a marked bounce that cannot land raises nothing, leaves transit receipted by
      'bus-test-bounce-disposed', and the bus emits test_bounce_disposed;
  (3) the control: an unmarked bounce that cannot land still raises exactly one
      mail-<to>-has-no-receiver trouble (7cb1989e7825 stands for unmarked mail).

    PYTHONPATH=. python3 cairn/devices/cairn/machines/bus/proofs/test_a_test_bounce_is_disposed_not_raised.py
"""
from __future__ import annotations

import contextlib
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"b3386f431ae3": {
    "1": "test_a_bounce_carries_the_mark",
    "2": "test_a_marked_bounce_is_disposed_not_raised",
    "3": "test_an_unmarked_bounce_still_raises",
}}

_TICKET = "b3386f431ae3"
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


def _post_to_nobody(marked: bool):
    """A scratch bus and its bus process; one post from a shimless sender to a shimless name."""
    from cairn.devices.cairn.machines.bus.bus import BusDevice
    from cairn.devices.cairn.machines.bus.server import BusProcess
    from cairn.tools.base import testing_mark

    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_b338"))
    inbox = _Inbox()
    bus.set_diagnostic_receiver(inbox)
    BusProcess(bus)
    ghost, nobody = _name("ghost"), _name("nobody")
    body = {testing_mark.FIELD: testing_mark.mark(_TICKET)} if marked else {}
    env = bus.post(sender=ghost, to=nobody, channel="personal",
                   why=f"testing-{_TICKET} nobody at either end", body=body)
    bounces = [e for e in bus.read(to=ghost, channel="personal")
               if (e.get("body") or {}).get("is_bounce")]
    return bus, inbox, env, ghost, nobody, bounces


def test_a_bounce_carries_the_mark() -> None:
    from cairn.tools.base import testing_mark
    _bus, _inbox, _env, _ghost, _nobody, bounces = _post_to_nobody(marked=True)
    want = {"kind": "return", "test": _TICKET}
    lacks = []
    if len(bounces) != 1:
        lacks.append(f"{len(bounces)} bounces, want 1")
    elif testing_mark.mark_of(bounces[0].get("body")) != want:
        lacks.append(f"the bounce carries mark {testing_mark.mark_of(bounces[0].get('body'))!r}, "
                     f"want {want!r}")
    check("test_a_bounce_carries_the_mark", not lacks, "; ".join(lacks))


def test_a_marked_bounce_is_disposed_not_raised() -> None:
    bus, inbox, _env, ghost, nobody, bounces = _post_to_nobody(marked=True)
    lacks = []
    raised = [r for r in inbox.gate("raise_trouble")
              if r.get("pointer") == f"mail-{nobody}-has-no-receiver"]
    if raised:
        lacks.append(f"raised {[r.get('pointer') for r in raised]}")
    if len(bounces) != 1:
        lacks.append(f"{len(bounces)} bounces, want 1")
    else:
        bid = bounces[0]["id"]
        if bid in {e["id"] for e in bus.undelivered(to=ghost, limit=1000)}:
            lacks.append("the bounce still sits in transit")
        by = [(r.get("values") or {}).get("by") for r in inbox.gate("delivered")
              if r.get("pointer") == bid]
        if by != ["bus-test-bounce-disposed"]:
            lacks.append(f"the bounce was receipted by {by!r}, want ['bus-test-bounce-disposed']")
        disposed = [r for r in inbox.gate("test_bounce_disposed")
                    if (r.get("values") or {}).get("bounce_envelope") == bid]
        if len(disposed) != 1:
            lacks.append(f"{len(disposed)} test_bounce_disposed emissions for the bounce, want 1")
    check("test_a_marked_bounce_is_disposed_not_raised", not lacks, "; ".join(lacks))


def test_an_unmarked_bounce_still_raises() -> None:
    _bus, inbox, _env, _ghost, nobody, bounces = _post_to_nobody(marked=False)
    raised = [r for r in inbox.gate("raise_trouble")
              if r.get("pointer") == f"mail-{nobody}-has-no-receiver"]
    check("test_an_unmarked_bounce_still_raises", len(bounces) == 1 and len(raised) == 1,
          f"{len(bounces)} bounces, {len(raised)} raised; want 1 and 1")


def main() -> int:
    try:
        for tooth in (test_a_bounce_carries_the_mark,
                      test_a_marked_bounce_is_disposed_not_raised,
                      test_an_unmarked_bounce_still_raises):
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

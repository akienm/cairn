#!/usr/bin/env python3
"""Proof that the testing mark's perform kind reaches the device and marks its reply (ticket d0c8c4b4283e).

Measured 2026-11-05: a device's verb proofs could not move to the live bus marked as testing,
because the only built kind was ``return`` and BaseShim._return_if_marked sends a return-marked
request back unacted on, so the verb under test never runs. Akien 2026-10-05 (testing_mark.py):
"device gets the "perform this test" kind later". This is that kind: the shim passes it through
to the device's verb, and stamps the same mark onto the verb's reply, so a reply caused by a test
rides the test's mark and no device has to learn about testing.

Teeth, one per falsifier clause (PROVES below), all on the live bus through bus_client.reach,
every name ``testing-d0c8c4b4283e-<label>-<uuid8>``:
  (1) testing_mark.mark(t, 'perform') builds and an unbuilt kind still raises;
  (2) a perform-marked request handed to a testing-named shim reaches its verb, and the one
      reply it posts on the live bus carries the verb's result and the same mark;
  (3) a return-marked request to the same kind of shim comes back is_return and the handler
      is never called (the control: the new kind did not widen the old one).

    PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_perform_mark_reaches_the_device.py
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"d0c8c4b4283e": {
    "1": "test_the_perform_kind_builds",
    "2": "test_a_performed_request_is_answered_marked",
    "3": "test_a_returned_request_never_wakes_the_handler",
}}

_TICKET = "d0c8c4b4283e"
FAILURES: list[str] = []
CALLS: list[dict] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _name(label: str) -> str:
    return f"testing-{_TICKET}-{label}-{uuid.uuid4().hex[:8]}"


def _perform() -> str:
    from cairn.tools.base import testing_mark
    return getattr(testing_mark, "PERFORM", "perform")


class _TestingBus:
    """The live bus with one decline: a testing shim never asks the bus to hold it."""

    def __init__(self, bus):
        self._bus = bus

    def wire_delivery(self, *args, **kwargs):
        return None

    def __getattr__(self, name):
        return getattr(self._bus, name)


class _EchoDevice:
    def declared_verbs(self):
        return {"echo": self._echo}

    def _echo(self, envelope: dict) -> dict:
        CALLS.append(envelope)
        return {"echo": (envelope.get("body") or {}).get("text")}


def _rig():
    """A fresh caller name, a fresh testing-named shim fronting the echo device, and the bus."""
    from cairn.tools.base.shim import BaseShim
    from cairn.tools.bus_client import bus_client

    device_name = _name("device")

    class _Shim(BaseShim):
        @property
        def device_id(self) -> str:
            return device_name

        def _start_device(self):
            return _EchoDevice()

    bus = _TestingBus(bus_client.reach())
    return _name("caller"), device_name, _Shim(bus=bus), bus


def _ask(mark: dict, nonce: str):
    """Hand the shim one marked envelope and read what it posted back on the live bus.

    The envelope goes to ``shim.deliver`` directly, never through ``bus.post``: measured
    2026-11-05, the live bus's postman (server.py no_receiver) bounces mail for a name no
    on-disk shim answers to before an in-proof shim can drain it — and the bounce, landing on
    a shimless testing caller, raised a live trouble. What the shim posts back carries
    ``reply_to``, and a correlated reply is the asker's to take (ticket 7cb1989e7825): it sits
    readable for the caller and is neither bounced nor raised."""
    caller, device, shim, bus = _rig()
    shim.deliver({"id": f"testing-{_TICKET}-{uuid.uuid4().hex}", "sender": caller,
                  "addressee": device, "channel": "personal", "verb": "echo",
                  "body": {"text": nonce, "testing": mark}})
    return bus.read(to=caller, channel="personal")


def test_the_perform_kind_builds() -> None:
    from cairn.tools.base import testing_mark
    lacks = []
    try:
        got = testing_mark.mark("t", _perform())
        if got != {"kind": "perform", "test": "t"}:
            lacks.append(f"mark('t', 'perform') built {got!r}")
    except ValueError as exc:
        lacks.append(f"mark('t', 'perform') refused: {exc}")
    try:
        testing_mark.mark("t", "bogus")
        lacks.append("an unbuilt kind 'bogus' was built")
    except ValueError:
        pass
    check("test_the_perform_kind_builds", not lacks, "; ".join(lacks))


def test_a_performed_request_is_answered_marked() -> None:
    from cairn.tools.base import testing_mark
    nonce = f"perform-{uuid.uuid4().hex[:8]}"
    want = {"kind": "perform", "test": _TICKET}
    replies = _ask(want, nonce)
    lacks = []
    if len(replies) != 1:
        lacks.append(f"{len(replies)} replies, want 1")
    else:
        body = replies[0].get("body") or {}
        if body.get("echo") != nonce:
            lacks.append(f"the verb did not answer: body {body!r}")
        if testing_mark.mark_of(body) != want:
            lacks.append(f"the reply carries mark {testing_mark.mark_of(body)!r}, want {want!r}")
    check("test_a_performed_request_is_answered_marked", not lacks, "; ".join(lacks))


def test_a_returned_request_never_wakes_the_handler() -> None:
    from cairn.tools.base import testing_mark
    before = len(CALLS)
    replies = _ask(testing_mark.mark(_TICKET), f"return-{uuid.uuid4().hex[:8]}")
    lacks = []
    if len(replies) != 1 or not (replies[0].get("body") or {}).get("is_return"):
        lacks.append(f"want one is_return reply, got {[r.get('body') for r in replies]!r}")
    if len(CALLS) != before:
        lacks.append("the handler ran for a return-marked request")
    check("test_a_returned_request_never_wakes_the_handler", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    for tooth in (test_the_perform_kind_builds,
                  test_a_performed_request_is_answered_marked,
                  test_a_returned_request_never_wakes_the_handler):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

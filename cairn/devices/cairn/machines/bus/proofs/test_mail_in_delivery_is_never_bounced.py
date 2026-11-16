"""PROOF for ticket 5bcba6e06917: mail a wired shim is still taking is never bounced.

Measured 2026-11-16 by akienasus_cc_0: two scratch buses bounced the first ``inspect`` ask to
codemother with "codemother's shim could not take the envelope — it cannot wake a device to
receive it", 0.24 s and 0.59 s after the bus started. Codemother was hooked and wired both
before and after (tester runs test-a1aa076d088d and test-cca0686b07c2, sealed/bus-bounces.jsonl).
The cause: ``serve`` runs ``return_the_backlog`` on its own thread while the socket already takes
clients. The first ask reaches codemother's hook, and she takes it under her shim's lock, with
the receipt written only when she answers. The backlog pass reads the same envelope as
undelivered and calls ``no_receiver``. ``hold_name`` finds her already wired, the envelope is
still pending, and the bus bounces mail that is being delivered. Now ``no_receiver`` waits on the
addressee's lock before it judges, so a delivery under way finishes first.

  1. the backlog pass, run while a wired shim's device is still taking an envelope, returns
     nothing to the sender, and the envelope is taken once and receipted;
  2. backlog mail to a name no shim answers still comes back to its sender in the same pass.

Every bus rides ``BusDevice.scratch``; every name is ``testing-5bcb-...``; the bus's diagnostics
go to a list, never the live trouble lane.

    python3 cairn/devices/cairn/machines/bus/proofs/test_mail_in_delivery_is_never_bounced.py
"""
from __future__ import annotations

import contextlib
import sys
import threading
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.tools.base.shim import BaseShim  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.server import BusProcess  # noqa: E402

PROVES = {"5bcba6e06917": {
    "1": "test_the_backlog_pass_never_bounces_mail_being_taken",
    "2": "test_backlog_mail_nobody_answers_still_returns"}}

PROOF_TIMEOUT_S = 120

_SLOW = "testing-5bcb-slow"
_ASKER = "testing-5bcb-asker"


class _Slow(BaseDevice):
    """Takes an envelope only when the proof lets it go, as codemother takes an inspect ask."""

    def __init__(self) -> None:
        super().__init__()
        self.took: list[str] = []
        self.entered = threading.Event()
        self.release = threading.Event()

    def intention(self) -> dict:
        return {"what": "testing-5bcb slow taker"}

    def state(self) -> dict:
        return {"took": len(self.took)}

    def settings(self) -> dict:
        return {}

    def receive(self, envelope: dict):
        self.entered.set()
        assert self.release.wait(30), "testing-5bcb: the proof never let the take finish"
        self.took.append(envelope["id"])
        return {"took": envelope["id"]}


class _Shim(BaseShim):
    def __init__(self, device_id: str, bus) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self.dev = _Slow()

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        return self.dev


class _Inbox:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)


def _bounces(bus, to: str) -> list[dict]:
    return [e for e in bus.read(to=to, channel="personal")
            if (e.get("body") or {}).get("is_bounce")]


def test_the_backlog_pass_never_bounces_mail_being_taken():
    with contextlib.ExitStack() as stack:
        bus = stack.enter_context(BusDevice.scratch("bus_5bcb"))
        bus.set_diagnostic_receiver(_Inbox())
        proc = BusProcess(bus)
        shim = _Shim(_SLOW, bus)
        proc.roster.hold(shim)
        proc.hold_name(_SLOW)
        posted: dict = {}
        poster = threading.Thread(target=lambda: posted.update(bus.post(
            sender=_ASKER, to=_SLOW, channel="personal",
            why="testing-5bcb the first ask, still being taken")), daemon=True)
        poster.start()
        assert shim.dev.entered.wait(10), "the wired shim never began to take the envelope"
        backlog = threading.Thread(target=proc.return_the_backlog, daemon=True)
        backlog.start()
        backlog.join(1.0)   # on the unfixed bus the pass bounces inside this second
        shim.dev.release.set()
        poster.join(10)
        backlog.join(10)
        assert not poster.is_alive() and not backlog.is_alive(), "a thread never finished"
        assert _bounces(bus, _ASKER) == [], (
            f"the bus returned mail its shim was still taking: {_bounces(bus, _ASKER)}")
        assert shim.dev.took == [posted["id"]], shim.dev.took
        assert posted["id"] not in {e["id"] for e in bus.undelivered(limit=1000)}, "not receipted"


def test_backlog_mail_nobody_answers_still_returns():
    with contextlib.ExitStack() as stack:
        bus = stack.enter_context(BusDevice.scratch("bus_5bcb"))
        bus.set_diagnostic_receiver(_Inbox())
        lost = bus.post(sender=_ASKER, to="testing-5bcb-nobody", channel="personal",
                        why="testing-5bcb backlog to nobody")
        proc = BusProcess(bus)
        proc.return_the_backlog()
        got = _bounces(bus, _ASKER)
        assert len(got) == 1 and got[0]["reply_to"] == lost["id"], got
        assert lost["id"] not in {e["id"] for e in bus.undelivered(limit=1000)}


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

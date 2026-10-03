"""PROOF for ticket 7cb1989e7825: mail arrives, and what cannot arrive marks itself.

Measured 2026-10-03 before the build: ``get status`` for ``bus`` raised TypeError (BusShim
required a heartbeat the roster never hands it), and four envelopes stood undelivered for
want of a receiver, the oldest from 2026-09-30, because ``BusDevice.post`` with no delivery
hook only appended the envelope to ``_pending``. Nothing woke the addressee and nothing told
the sender.

The bus's half of the fix, one tooth per falsifier clause (amended 2026-08-11):

  * the bus answers get status — the roster builds the bus's own shim and the root verb
    answers exit 0, like every other roster name;
  * a sleeping addressee is woken by its mail — a post to a held-but-unwired shim is
    delivered and receipted inside the same post call, with no flush and no pulse;
  * a device nobody mails is never held — waking is caused by mail and nothing else;
  * a reply to a shimless requester is neither woken nor bounced — correlated mail is the
    asker's to take (ticket 6b1e13704e17);
  * a bounce answering a waiting request is the asker's to take — ``Bus.request`` reads
    it by correlation, so the bus neither raises over it nor leaves it standing;
  * unreachable addressed mail returns to its sender — mail to a name no shim answers, and
    mail a shim cannot wake a device for, leaves transit and one bounce reaches the sender;
  * an undeliverable bounce is raised, not re-bounced — the bus raises the addressee's mail
    trouble itself and receipts the bounce;
  * the standing backlog takes the path at start — envelopes undelivered when the bus
    process starts are woken or returned in one pass.

Every bus rides ``BusDevice.scratch``; every name is ``testing-7cb1-...`` so a leak explains
itself; the bus's diagnostics go to a list, never the live trouble lane.

    python3 cairn/devices/cairn/machines/bus/proofs/test_mail_without_a_receiver.py
"""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.tools.base.shim import BaseShim, ONLINE  # noqa: E402
from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.devices.cairn.machines.bus.server import BusProcess  # noqa: E402

PROVES = {"7cb1989e7825": {
    "every device answers a health query": "the_bus_answers_get_status",
    "a message for a sleeping component wakes it":
        "a_sleeping_addressee_is_woken_by_its_mail",
    "a device nobody mails stays GREEN": "a_device_nobody_mails_is_never_held",
    "a reply is the asker's to take": "a_reply_to_a_shimless_requester_is_neither_woken_nor_bounced",
    "a bounce answering a waiting request is the asker's to take":
        "a_bounce_answering_a_waiting_request_is_the_askers_to_take",
    "a genuinely unreachable ADDRESSED device reds":
        "unreachable_addressed_mail_returns_to_its_sender",
    "a bounce that cannot land is raised, never re-bounced":
        "an_undeliverable_bounce_is_raised_not_re_bounced",
    "no envelope sits in transit for want of a receiver":
        "the_standing_backlog_takes_the_path_at_start",
}}

_SCRATCH = contextlib.ExitStack()
PASS = 0
FAIL = 0


class _Took(BaseDevice):
    """Takes whatever it is handed and remembers it."""

    def __init__(self) -> None:
        super().__init__()
        self.took: list[str] = []

    def intention(self) -> dict:
        return {"what": "testing-7cb1 taker"}

    def state(self) -> dict:
        return {"took": len(self.took)}

    def settings(self) -> dict:
        return {}

    def receive(self, envelope: dict):
        self.took.append(envelope["id"])
        return {"took": envelope["id"]}


class _Sleeper(BaseShim):
    """A shim whose device is asleep until mail wakes it; counts the wakes."""

    def __init__(self, device_id: str, bus) -> None:
        super().__init__(bus=bus)
        self._device_id = device_id
        self.wakes = 0
        self.dev = _Took()

    @property
    def device_id(self) -> str:
        return self._device_id

    def _start_device(self):
        self.wakes += 1
        return self.dev


class _CannotWake(_Sleeper):
    """The base contract's refusal: a shim that cannot start a device."""

    def _start_device(self):
        raise NotImplementedError(f"testing-7cb1: {self._device_id} cannot wake a device")


class _Inbox:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)

    def raised(self) -> list[dict]:
        return [r for r in self.records if r.get("gate") == "raise_trouble"]


def _rig(*shims):
    """A scratch bus, its bus process, and the shims held on the roster UNWIRED — asleep."""
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_7cb1"))
    inbox = _Inbox()
    bus.set_diagnostic_receiver(inbox)
    proc = BusProcess(bus)
    held = []
    for cls, name in shims:
        shim = cls(name, bus)
        shim.set_diagnostic_receiver(_Inbox())
        proc.roster.hold(shim)
        held.append(shim)
    return bus, proc, inbox, held


def _pending(bus, to):
    return {e["id"] for e in bus.undelivered(to=to, limit=1000)}


def _bounces_to(bus, sender):
    return [e for e in bus.read(to=sender, channel="personal")
            if (e.get("body") or {}).get("is_bounce")]


def the_bus_answers_get_status():
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_7cb1"))
    bus.set_diagnostic_receiver(_Inbox())
    proc = BusProcess(bus)
    reply = proc.answer({"op": "verbs", "device": "bus", "verbs": ["get", "status"]},
                        in_process=True)
    assert reply.get("ok") and reply.get("exit") == 0, f"bus get status answered {reply}"


def a_sleeping_addressee_is_woken_by_its_mail():
    bus, proc, _inbox, (sleeper,) = _rig((_Sleeper, "testing-7cb1-sleeper"))
    env = bus.post(sender="testing-7cb1-sender", to="testing-7cb1-sleeper", channel="personal",
                   why="testing-7cb1 wake")
    assert env["id"] in sleeper.dev.took, (
        f"the post returned and the sleeping addressee had not taken it (wakes={sleeper.wakes})")
    assert env["id"] not in _pending(bus, "testing-7cb1-sleeper"), "taken but not receipted"


def a_device_nobody_mails_is_never_held():
    bus, proc, inbox, (a, b) = _rig((_Sleeper, "testing-7cb1-mailed"),
                                    (_Sleeper, "testing-7cb1-unmailed"))
    bus.post(sender="testing-7cb1-sender", to="testing-7cb1-mailed", channel="personal",
             why="testing-7cb1 only one is mailed")
    assert a.wakes == 1, f"the mailed device woke {a.wakes} times"
    assert b.wakes == 0 and "testing-7cb1-unmailed" not in proc._wired, (
        "a device nobody mailed was woken or wired")
    assert not inbox.raised(), f"a trouble was raised with nothing unreachable: {inbox.raised()}"


def a_reply_to_a_shimless_requester_is_neither_woken_nor_bounced():
    bus, proc, inbox, _ = _rig()
    env = bus.post(sender="testing-7cb1-answerer", to="testing-7cb1-asker", channel="personal",
                   why="testing-7cb1 a reply", reply_to="testing-7cb1-request-id")
    assert env["id"] in _pending(bus, "testing-7cb1-asker"), (
        "a correlated reply was receipted before its asker took it")
    assert not _bounces_to(bus, "testing-7cb1-answerer"), "a reply was bounced"
    assert not inbox.raised(), f"a reply raised a trouble: {inbox.raised()}"


def a_bounce_answering_a_waiting_request_is_the_askers_to_take():
    bus, proc, inbox, (sleeper,) = _rig((_Sleeper, "testing-7cb1-sleeper"))
    reply = bus.request(sender="testing-7cb1-asker", to="testing-7cb1-sleeper",
                        why="testing-7cb1 an undeclared verb", verb="testing_7cb1_no_verb",
                        timeout=2)
    assert (reply.get("body") or {}).get("is_bounce"), f"the request was answered {reply}"
    assert reply["id"] not in _pending(bus, "testing-7cb1-asker"), "the asker's bounce sits"
    assert not inbox.raised(), (
        f"the bus raised over a bounce its asker took by correlation: {inbox.raised()}")


def unreachable_addressed_mail_returns_to_its_sender():
    bus, proc, _inbox, (sender, _cw) = _rig((_Sleeper, "testing-7cb1-writer"),
                                             (_CannotWake, "testing-7cb1-cannot-wake"))
    for to in ("testing-7cb1-nobody", "testing-7cb1-cannot-wake"):
        env = bus.post(sender="testing-7cb1-writer", to=to, channel="personal",
                       why=f"testing-7cb1 to {to}", verb="")
        assert env["id"] not in _pending(bus, to), f"mail to {to} still sits in transit"
        bounces = [b for b in _bounces_to(bus, "testing-7cb1-writer")
                   if b.get("reply_to") == env["id"]]
        assert len(bounces) == 1, f"{len(bounces)} bounces for mail to {to}"
        body = bounces[0]["body"]
        assert body.get("original_addressee") == to, body
        assert body.get("trouble") == f"mail-{to}-has-no-receiver", body
        assert bounces[0]["id"] not in _pending(bus, "testing-7cb1-writer"), (
            "the sender's shim did not take its returned letter")


def an_undeliverable_bounce_is_raised_not_re_bounced():
    bus, proc, inbox, _ = _rig()
    env = bus.post(sender="testing-7cb1-ghost", to="testing-7cb1-nobody", channel="personal",
                   why="testing-7cb1 nobody at either end")
    bounces = _bounces_to(bus, "testing-7cb1-ghost")
    assert len(bounces) == 1, f"{len(bounces)} bounces to a shimless sender"
    assert not _bounces_to(bus, "bus"), "the bounce was bounced back to the bus"
    assert env["id"] not in _pending(bus, "testing-7cb1-nobody"), "the original still sits"
    assert bounces[0]["id"] not in _pending(bus, "testing-7cb1-ghost"), "the bounce still sits"
    raised = [r for r in inbox.raised() if r["pointer"] == "mail-testing-7cb1-nobody-has-no-receiver"]
    assert len(raised) == 1, f"the bus raised {inbox.raised()}"
    detail = raised[0]["values"]["detail"]
    assert detail.get("sender") == "testing-7cb1-ghost" and detail.get("bounce") is True, detail


def the_standing_backlog_takes_the_path_at_start():
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_7cb1"))
    bus.set_diagnostic_receiver(_Inbox())
    # Posted before any bus process exists: nothing is wired and no callback is installed,
    # which is exactly the backlog a restarted bus finds in the store.
    asleep = bus.post(sender="testing-7cb1-ghost", to="testing-7cb1-sleeper", channel="personal",
                      why="testing-7cb1 backlog to a sleeper")
    lost = bus.post(sender="testing-7cb1-ghost", to="testing-7cb1-nobody", channel="personal",
                    why="testing-7cb1 backlog to nobody")
    assert {asleep["id"], lost["id"]} <= _pending(bus, None), "the backlog was not standing"
    proc = BusProcess(bus)
    sleeper = _Sleeper("testing-7cb1-sleeper", bus)
    proc.roster.hold(sleeper)
    proc.return_the_backlog()
    assert asleep["id"] in sleeper.dev.took, "the sleeper's backlog was not delivered"
    left = _pending(bus, None)
    assert asleep["id"] not in left and lost["id"] not in left, (
        f"backlog still standing after start: {sorted(left)}")


TEETH = [the_bus_answers_get_status,
         a_sleeping_addressee_is_woken_by_its_mail,
         a_device_nobody_mails_is_never_held,
         a_reply_to_a_shimless_requester_is_neither_woken_nor_bounced,
         a_bounce_answering_a_waiting_request_is_the_askers_to_take,
         unreachable_addressed_mail_returns_to_its_sender,
         an_undeliverable_bounce_is_raised_not_re_bounced,
         the_standing_backlog_takes_the_path_at_start]


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

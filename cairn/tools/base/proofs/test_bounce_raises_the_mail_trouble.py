"""PROOF for ticket 7cb1989e7825: the sender of returned mail raises the mail trouble, and the
addressee's shim clears it when it next genuinely takes mail.

Measured 2026-10-03 before the build: ``BaseShim.handle_bounce`` only emitted
``bounced_mail`` and ``clear_trouble`` had no caller in the shim, so a returned letter marked
nothing and the derived to-do list (Akien 2026-08-11: *"the trouble ticket comes from the
device that received the return to sender"*) could neither grow nor shrink.

The base shim's half of the fix:

  1. a returned letter raises the addressee's mail trouble — on the SENDER, under an identity
     naming the addressee's defect (so many senders fold into one trouble), and a shim that
     bounces names that identity on the bounce it posts;
  2. taking mail clears the trouble; a bounce is not a take — the clear is a measured green,
     emitted once per process per identity, and a returned letter never clears anything;
  3. a recurrence after the clear is a fresh trouble — the raise after a clear carries the
     IDENTICAL identity and is not suppressed. The trouble device's own proven fold turns a
     raise on a CLEARED identity into a fresh ticket (prior_attempts+1); that fold is trusted,
     not driven, here (RULE 1: this proof measures only cairn/tools/base).

Diagnostics go to a list receiver; the bus is a spy. Every name is ``testing-7cb1-...``.

    python3 cairn/tools/base/proofs/test_bounce_raises_the_mail_trouble.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.shim import BaseShim  # noqa: E402

PROVES = {"7cb1989e7825": {
    "a raised trouble names the addressee's defect, raised by the sender":
        "a_returned_letter_raises_the_addressees_mail_trouble",
    "a raised trouble clears on a measured green":
        "taking_mail_clears_the_trouble_a_bounce_is_not_a_take",
    "a recurrence writes a FRESH ticket rather than bumping a count":
        "a_recurrence_after_the_clear_is_a_fresh_trouble",
}}

PASS = 0
FAIL = 0
_ME = "testing-7cb1-me"


class _Inbox:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)

    def lane(self, gate: str) -> list[dict]:
        return [r for r in self.records if r.get("gate") == gate]


class _SpyBus:
    """Holds a mailbox for the shim under test and records every post and receipt."""

    def __init__(self) -> None:
        self.posted: list[dict] = []
        self.waiting: list[dict] = []
        self.receipted: list[str] = []

    def post(self, **envelope) -> dict:
        envelope = {"id": f"testing-7cb1-post-{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope

    def undelivered(self, to=None, limit=50) -> list[dict]:
        return [e for e in self.waiting if e["id"] not in self.receipted][:limit]

    def record_delivery(self, envelope_id, *, to, by) -> None:
        self.receipted.append(envelope_id)

    def wire_delivery(self, device_id, deliver) -> None:
        pass

    def read(self, **kw) -> list[dict]:
        return []


class _Device:
    def __init__(self) -> None:
        self.took: list[str] = []

    def declared_verbs(self):
        return {"ping": lambda envelope: None}

    def receive(self, envelope):
        self.took.append(envelope["id"])


class _Shim(BaseShim):
    def __init__(self, bus) -> None:
        super().__init__(bus=bus)
        self.inbox = _Inbox()
        self.set_diagnostic_receiver(self.inbox)

    @property
    def device_id(self) -> str:
        return _ME

    def _start_device(self):
        return _Device()


def _bounce(n: int, addressee: str, trouble: str | None) -> dict:
    body = {"is_bounce": True, "reason": f"testing-7cb1 {addressee} cannot take it",
            "original_verb": "", "original_addressee": addressee}
    if trouble is not None:
        body["trouble"] = trouble
    return {"id": f"testing-7cb1-bounce-{n}", "sender": "bus", "addressee": _ME,
            "channel": "personal", "body": body, "reply_to": f"testing-7cb1-orig-{n}"}


def _letter(n: int, verb: str = "") -> dict:
    return {"id": f"testing-7cb1-letter-{n}", "sender": "testing-7cb1-friend",
            "addressee": _ME, "channel": "personal", "verb": verb, "body": {}}


def _take(shim, bus, envelope) -> None:
    bus.waiting.append(envelope)
    shim._check_mail()
    assert envelope["id"] in bus.receipted, f"{envelope['id']} was not taken"


def a_returned_letter_raises_the_addressees_mail_trouble():
    bus = _SpyBus()
    shim = _Shim(bus)
    shim.deliver(_bounce(1, "testing-7cb1-absent", "mail-testing-7cb1-absent-has-no-receiver"))
    raised = shim.inbox.lane("raise_trouble")
    assert [r["pointer"] for r in raised] == ["mail-testing-7cb1-absent-has-no-receiver"], raised
    detail = raised[0]["values"]["detail"]
    assert detail.get("sender") == _ME and detail.get("receiver") == "testing-7cb1-absent" \
        and detail.get("bounce") is True, detail
    # a bounce carrying no identity still names its addressee
    shim.deliver(_bounce(2, "testing-7cb1-older", None))
    assert shim.inbox.lane("raise_trouble")[-1]["pointer"] == "mail-testing-7cb1-older-bounced"
    # and a shim that bounces names the identity on what it posts
    shim.deliver(_letter(3, verb="no_such_verb"))
    shim.deliver({"id": "testing-7cb1-letter-4", "sender": "testing-7cb1-friend",
                  "addressee": _ME, "verb": "", "body": {}})  # receive() takes this one
    posted = [e["body"].get("trouble") for e in bus.posted if (e.get("body") or {}).get("is_bounce")]
    assert posted == [f"mail-{_ME}-has-no-verb-no_such_verb"], posted


def taking_mail_clears_the_trouble_a_bounce_is_not_a_take():
    bus = _SpyBus()
    shim = _Shim(bus)
    _take(shim, bus, _bounce(1, "testing-7cb1-absent", "mail-testing-7cb1-absent-has-no-receiver"))
    assert not shim.inbox.lane("clear_trouble"), "a returned letter cleared a trouble"
    _take(shim, bus, _letter(2))
    _take(shim, bus, _letter(3))
    clears = [r["pointer"] for r in shim.inbox.lane("clear_trouble")]
    assert clears == [f"mail-{_ME}-has-no-receiver"], f"clears after two takes: {clears}"
    _take(shim, bus, _letter(4, verb="ping"))
    clears = [r["pointer"] for r in shim.inbox.lane("clear_trouble")]
    assert clears[-1] == f"mail-{_ME}-has-no-verb-ping", clears
    by = shim.inbox.lane("clear_trouble")[0]["values"]
    assert by.get("by") == "cc" and "testing-7cb1-letter-2" in by.get("what_changed", ""), by


def a_recurrence_after_the_clear_is_a_fresh_trouble():
    bus = _SpyBus()
    shim = _Shim(bus)
    identity = "mail-testing-7cb1-flaky-has-no-receiver"
    shim.deliver(_bounce(1, "testing-7cb1-flaky", identity))
    shim.clear_trouble(identity, by="cc", what_changed="testing-7cb1 the receiver was built")
    shim.deliver(_bounce(2, "testing-7cb1-flaky", identity))
    raised = [r["pointer"] for r in shim.inbox.lane("raise_trouble")]
    assert raised == [identity, identity], (
        f"the raise after a clear was suppressed or renamed: {raised}")


TEETH = [a_returned_letter_raises_the_addressees_mail_trouble,
         taking_mail_clears_the_trouble_a_bounce_is_not_a_take,
         a_recurrence_after_the_clear_is_a_fresh_trouble]


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
    for fn in TEETH:
        _tooth(fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

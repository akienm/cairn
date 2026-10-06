"""A marked envelope goes back to its sender (ticket 3bf728e5328d, child of 71d1bbfa98b0).

Akien, 2026-10-05 (/home/akien/.cairn/foreground-decisions.md 8e): "if a test sends a message to
codemother ... code mother should return it to the tester ... "Yep, got here" is implicit in the
return." Where the return happens: "the shim. device gets the "perform this test" kind later".
So the receiving SHIM returns a return-kind envelope to its sender, generically, before any device
code runs. That includes shims that override deliver() (cc_0 persists everything, codemother
persists verbless mail, the tester takes replies), which is why the return sits in BaseShim and
reaches every subclass's deliver().

Teeth a hollow shim could not pass, each against a spy bus:
  1. A RETURN-MARKED ENVELOPE IS POSTED BACK TO ITS SENDER, UNACTED ON: exactly one post, to the
     sender, reply_to the envelope's id, the mark carried in the body with is_return True; the
     device is never started and its verb handler never runs.
  2. A SUBCLASS THAT OVERRIDES deliver() STILL RETURNS IT: the override body never runs.
  3. EVERYTHING ELSE IS UNCHANGED: an unmarked envelope reaches its verb handler with no return,
     and a well-formed mark of a kind the shim does not return ("perform") passes through to the
     device as well.
  4. A RETURN IS NEVER RETURNED AGAIN: an is_return envelope goes to handle_return (posts nothing,
     wakes no device, emits test_returned), and the mail drain does not count it as a take, so it
     clears no mail trouble.

Run: python3 cairn/tools/base/proofs/test_a_marked_envelope_goes_back_to_its_sender.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "3bf728e5328d": {
        "1": "test_a_return_marked_envelope_is_posted_back_to_its_sender_unacted_on",
        "2": "test_a_subclass_that_overrides_deliver_still_returns_it",
        "3": "test_everything_else_is_unchanged",
        "4": "test_a_return_is_never_returned_again",
    },
}

_TEST = "test-3bf728e5328d-fixture"


class _SpyBus:
    def __init__(self) -> None:
        self.posted: list[dict] = []

    def post(self, **envelope) -> dict:
        envelope = {"id": f"posted{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope

    def wire_delivery(self, device_id: str, deliver) -> None:
        pass

    def read(self, **kw) -> list[dict]:
        return []


def _shim_class(*, override: bool = False):
    from cairn.tools.base.shim import BaseShim

    calls = {"started": 0, "handled": 0, "override": 0}

    class _Device:
        def declared_verbs(self):
            def ping(envelope):
                calls["handled"] += 1
                return {"pong": True}
            return {"ping": ping}

    class _Shim(BaseShim):
        def __init__(self, bus):
            super().__init__(bus=bus)
            self.emitted: list[str] = []
            self.set_diagnostic_receiver(None)

        @property
        def device_id(self):
            return "marked_mail_fixture_3bf7"

        def _start_device(self):
            calls["started"] += 1
            return _Device()

        def emit(self, event, **kw):
            self.emitted.append(event)

    if override:
        class _Persisting(_Shim):
            def deliver(self, envelope):
                calls["override"] += 1
                return {"persisted": True}
        return _Persisting, calls
    return _Shim, calls


def _marked(kind: str = "return") -> dict:
    from cairn.tools.base import testing_mark as tm
    mark = tm.mark(_TEST) if kind == tm.RETURN else {"kind": kind, "test": _TEST}
    return {"id": "env-3bf7", "sender": "tester", "addressee": "marked_mail_fixture_3bf7",
            "verb": "ping", "body": {tm.FIELD: mark, "payload": 1}}


def test_a_return_marked_envelope_is_posted_back_to_its_sender_unacted_on():
    from cairn.tools.base import testing_mark as tm
    cls, calls = _shim_class()
    bus = _SpyBus()
    result = cls(bus).deliver(_marked())
    assert isinstance(result, dict) and result.get("returned") is True, \
        f"a return-marked envelope was not returned: {result}"
    assert len(bus.posted) == 1, f"expected exactly one post (the return), got {bus.posted}"
    back = bus.posted[0]
    assert back.get("to") == "tester", f"the return did not go to the sender: {back}"
    assert back.get("reply_to") == "env-3bf7", f"the return does not answer its envelope: {back}"
    body = back.get("body") or {}
    assert body.get("is_return") is True, f"the return is not flagged is_return: {body}"
    assert tm.mark_of(body) == tm.mark(_TEST), f"the return lost its mark: {body}"
    assert calls["started"] == 0, "the device was started for a return-marked envelope"
    assert calls["handled"] == 0, "the verb handler ran on a return-marked envelope"


def test_a_subclass_that_overrides_deliver_still_returns_it():
    cls, calls = _shim_class(override=True)
    bus = _SpyBus()
    result = cls(bus).deliver(_marked())
    assert isinstance(result, dict) and result.get("returned") is True, \
        f"an overriding shim did not return the marked envelope: {result}"
    assert calls["override"] == 0, "the subclass's deliver() ran on a return-marked envelope"
    assert [e.get("to") for e in bus.posted] == ["tester"], bus.posted


def test_everything_else_is_unchanged():
    cls, calls = _shim_class()
    bus = _SpyBus()
    plain = _marked()
    plain["body"] = {"payload": 1}
    result = cls(bus).deliver(plain)
    assert result == {"pong": True}, f"an unmarked envelope did not reach its handler: {result}"
    assert calls["handled"] == 1
    assert not any((e.get("body") or {}).get("is_return") for e in bus.posted), bus.posted

    cls, calls = _shim_class()
    bus = _SpyBus()
    result = cls(bus).deliver(_marked(kind="perform"))
    assert result == {"pong": True}, f"a perform-kind mark did not pass to the device: {result}"
    assert calls["handled"] == 1
    assert not any((e.get("body") or {}).get("is_return") for e in bus.posted), bus.posted


def test_a_return_is_never_returned_again():
    from cairn.tools.base import testing_mark as tm
    cls, calls = _shim_class()
    bus = _SpyBus()
    shim = cls(bus)
    back = _marked()
    back["body"] = {tm.FIELD: tm.mark(_TEST), "is_return": True}
    back["reply_to"] = "env-original"
    result = shim.deliver(back)
    assert bus.posted == [], f"a return was posted again: {bus.posted}"
    assert calls["started"] == 0 and calls["handled"] == 0, "a return woke the device"
    assert "test_returned" in shim.emitted, f"handle_return emitted no test_returned: {shim.emitted}"
    assert isinstance(result, dict) and result.get("returned") is True, result

    cleared: list = []
    shim.clear_trouble = lambda identity, **kw: cleared.append(identity)
    shim._clear_mail_troubles(back, result)
    shim._clear_mail_troubles(_marked(), {"returned": True, "to": "tester"})
    assert cleared == [], f"a returned envelope cleared a mail trouble: {cleared}"


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)

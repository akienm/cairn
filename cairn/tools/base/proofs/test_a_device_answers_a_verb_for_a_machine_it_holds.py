"""A device answers a verb addressed to a machine it holds (ticket 15d850266972).

Outline 3.3.4.3 and 9.6 (Akien 2026-11-10): a ticket crosses a gate by asking
devices/codemother/0/machines/<gate>/queueme <fileref>. Measured 2026-11-10: BaseDevice's
declared_verbs() was a flat table of show and get, so no device could answer a verb addressed
to one of its machines.

Teeth a hollow base could not pass (a fixture device holding machine 'gate_x' with verb
'queueme', a fixture shim, a spy bus — no live device, no store):
  1. machines/gate_x/queueme is declared; delivery calls the machine's handler with the
     envelope and posts its answer with reply_to equal to the request id.
  2. machines/no_such/queueme bounces, its reason naming the declared verbs.
  3. machines/gate_x/no_such bounces the same way, and the handler is not called.
  4. The announce menu posted at wiring lists machines/gate_x/queueme.
  5. A '/' in a machine name or verb raises ValueError naming it; a device declaring no
     machines answers exactly show and get.

Run: bin/cairn test cairn/tools/base/proofs/test_a_device_answers_a_verb_for_a_machine_it_holds.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "15d850266972": {
        "1": "test_a_held_machines_verb_is_delivered_and_answered",
        "2": "test_an_unknown_machine_bounces_naming_the_declared_verbs",
        "3": "test_an_unknown_verb_on_a_known_machine_bounces_and_calls_nothing",
        "4": "test_the_announce_menu_lists_the_machine_verb",
        "5": "test_a_slash_is_refused_and_a_machineless_device_answers_show_and_get",
    },
}

_DEVICE = "holding_device_15d8"
_PATH_VERB = "machines/gate_x/queueme"


class _SpyBus:
    """Records every post."""

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

    def undelivered(self, *, to: str, limit: int) -> list[dict]:
        return []

    def record_delivery(self, envelope_id: str, *, to: str, by: str) -> None:
        pass

    def bounces(self) -> list[dict]:
        return [e for e in self.posted if (e.get("body") or {}).get("is_bounce")]


def _fixture(machines: dict | None = None):
    """Build the device and shim at call time, so a reverted base reds the tooth."""
    from cairn.tools.base.device import BaseDevice
    from cairn.tools.base.shim import BaseShim

    calls: list[dict] = []

    def _queueme(envelope):
        calls.append(envelope)
        return {"accepted": True, "queued": (envelope.get("body") or {}).get("fileref")}

    class _Gate:
        def declared_verbs(self):
            return {"queueme": _queueme}

    held = {"gate_x": _Gate()} if machines is None else machines

    class _Holding(BaseDevice):
        @property
        def device_id(self) -> str:
            return _DEVICE

        def intention(self) -> dict:
            return {"what": "fixture holder", "why": "proof"}

        def state(self) -> dict:
            return {"awake": True}

        def settings(self) -> dict:
            return {}

        def declared_machines(self) -> dict:
            return held

    device = _Holding()

    class _Shim(BaseShim):
        def __init__(self, bus):
            super().__init__(bus=bus)
            self.set_diagnostic_receiver(None)

        @property
        def device_id(self):
            return _DEVICE

        def _start_device(self):
            return device

        def raise_trouble(self, *a, **kw):
            return None

    return device, _Shim, calls


def _envelope(eid: str, verb: str) -> dict:
    return {"id": eid, "addressee": _DEVICE, "verb": verb, "sender": "alice",
            "body": {"fileref": "CairnCommons/tickets/x.json"}}


def test_a_held_machines_verb_is_delivered_and_answered():
    device, Shim, calls = _fixture()
    assert _PATH_VERB in device.declared_verbs(), (
        f"{_PATH_VERB} not declared: {sorted(device.declared_verbs())}")
    bus = _SpyBus()
    env = _envelope("env-15d8-1", _PATH_VERB)
    Shim(bus).deliver(env)
    assert len(calls) == 1 and calls[0]["id"] == "env-15d8-1", f"handler calls: {calls}"
    replies = [e for e in bus.posted if e.get("reply_to") == "env-15d8-1"
               and not (e.get("body") or {}).get("is_bounce")]
    assert len(replies) == 1, f"expected one answer with reply_to, posted: {bus.posted}"
    body = replies[0].get("body") or {}
    assert body.get("accepted") is True and body.get("queued") == "CairnCommons/tickets/x.json", (
        f"the answer is not the handler's: {body}")
    assert replies[0].get("to") == "alice", f"answer went to {replies[0].get('to')!r}"
    print("ok test_a_held_machines_verb_is_delivered_and_answered")


def _bounce_reason(bus, eid: str) -> str:
    bounces = [b for b in bus.bounces() if b.get("reply_to") == eid]
    assert len(bounces) == 1, f"expected one bounce for {eid}, posted: {bus.posted}"
    return str((bounces[0].get("body") or {}).get("reason", ""))


def test_an_unknown_machine_bounces_naming_the_declared_verbs():
    _, Shim, calls = _fixture()
    bus = _SpyBus()
    Shim(bus).deliver(_envelope("env-15d8-2", "machines/no_such/queueme"))
    reason = _bounce_reason(bus, "env-15d8-2")
    assert _PATH_VERB in reason, f"the bounce does not name the declared verbs: {reason!r}"
    assert not calls, f"a handler was called for an unknown machine: {calls}"
    print("ok test_an_unknown_machine_bounces_naming_the_declared_verbs")


def test_an_unknown_verb_on_a_known_machine_bounces_and_calls_nothing():
    _, Shim, calls = _fixture()
    bus = _SpyBus()
    Shim(bus).deliver(_envelope("env-15d8-3", "machines/gate_x/no_such"))
    reason = _bounce_reason(bus, "env-15d8-3")
    assert _PATH_VERB in reason, f"the bounce does not name the declared verbs: {reason!r}"
    assert not calls, f"the machine's handler was called for an unknown verb: {calls}"
    print("ok test_an_unknown_verb_on_a_known_machine_bounces_and_calls_nothing")


def test_the_announce_menu_lists_the_machine_verb():
    _, Shim, _ = _fixture()
    bus = _SpyBus()
    Shim(bus)._announce_menu()
    menus = [e for e in bus.posted if e.get("channel") == "announce"]
    assert len(menus) == 1, f"expected one menu, posted: {bus.posted}"
    verbs = (menus[0].get("body") or {}).get("verbs") or []
    assert _PATH_VERB in verbs and "show" in verbs and "get" in verbs, f"menu: {verbs}"
    print("ok test_the_announce_menu_lists_the_machine_verb")


def test_a_slash_is_refused_and_a_machineless_device_answers_show_and_get():
    class _Bad:
        def __init__(self, verb):
            self._verb = verb

        def declared_verbs(self):
            return {self._verb: lambda env: {}}

    for machines, named in (({"a/b": _Bad("queueme")}, "a/b"),
                            ({"gate_y": _Bad("x/y")}, "x/y")):
        device, _, _ = _fixture(machines)
        try:
            device.declared_verbs()
        except ValueError as exc:
            assert named in str(exc), f"ValueError does not name {named!r}: {exc}"
        else:
            raise AssertionError(f"declared_verbs() accepted a '/' in {named!r}")
    device, _, _ = _fixture({})
    assert sorted(device.declared_verbs()) == ["get", "show"], (
        f"a machineless device answers {sorted(device.declared_verbs())}")
    print("ok test_a_slash_is_refused_and_a_machineless_device_answers_show_and_get")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

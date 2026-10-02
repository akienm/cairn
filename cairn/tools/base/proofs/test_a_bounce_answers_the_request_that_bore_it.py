"""A bounce answers the request that bore it (ticket 60cc220da787).

Measured 2026-10-02 at ticket 67b78ae59c1d's hollow: a bus request to a verb its target does
not declare raised TimeoutError after the WHOLE timeout, though the target's shim bounced the
envelope within milliseconds. Bus.request returns only a message whose reply_to is the
request's id — the correlation every verb reply already carries — and the bounce carried none,
so the asker sat out 30 to 180 seconds and was then told the target "did not reply" when it had.

Teeth a hollow shim could not pass:
  1. THE BOUNCE CARRIES THE BOUNCED ENVELOPE'S ID AS reply_to — read off the envelope the shim
     posts, against a spy bus.
  2. A LIVE REQUEST FOR AN UNDECLARED VERB IS ANSWERED BY THE BOUNCE, quickly: under 10
     seconds, is_bounce True, and a reason naming the verb. The tester is reached only through
     its bus interface (RULE 1).

Run: python3 cairn/tools/base/proofs/test_a_bounce_answers_the_request_that_bore_it.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "60cc220da787": {
        "1": "test_the_bounce_carries_the_bounced_envelopes_id_as_reply_to",
        "2": "test_a_live_request_for_an_undeclared_verb_is_answered_by_the_bounce",
    },
}

_VERB = "no_such_verb_60cc220da787"


class _SpyBus:
    """Records the kwargs of every post — the shim's contract is 'it bounces via post'."""

    def __init__(self) -> None:
        self.posted: list[dict] = []

    def post(self, **envelope) -> dict:
        envelope = {"id": f"bounce{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope

    def wire_delivery(self, device_id: str, deliver) -> None:
        pass

    def read(self, **kw) -> list[dict]:
        return []


def test_the_bounce_carries_the_bounced_envelopes_id_as_reply_to():
    from cairn.tools.base.shim import BaseShim

    class _OneVerb:
        def declared_verbs(self):
            return {"ping": lambda envelope: "pong"}

    class _Shim(BaseShim):
        def __init__(self, bus):
            super().__init__(bus=bus)
            self.set_diagnostic_receiver(None)

        @property
        def device_id(self):
            return "one_verb_device_60cc"

        def _start_device(self):
            return _OneVerb()

    bus = _SpyBus()
    result = _Shim(bus).deliver({"id": "env-60cc", "sender": "alice",
                                 "addressee": "one_verb_device_60cc", "verb": _VERB, "body": {}})
    assert result.get("bounced") is True, f"the undeclared verb did not bounce: {result}"
    bounces = [e for e in bus.posted if (e.get("body") or {}).get("is_bounce")]
    assert len(bounces) == 1, f"expected exactly one bounce posted, got {bus.posted}"
    assert bounces[0].get("reply_to") == "env-60cc", (
        f"the bounce must answer the envelope that bore it: reply_to={bounces[0].get('reply_to')!r}")
    print("ok test_the_bounce_carries_the_bounced_envelopes_id_as_reply_to")


def test_a_live_request_for_an_undeclared_verb_is_answered_by_the_bounce():
    from cairn.tools.bus_client.bus_client import reach
    started = time.monotonic()
    try:
        reply = reach("tester").request(
            sender="a_bounce_answers_60cc", to="tester", verb=_VERB,
            why="proof 60cc220da787: an undeclared verb is answered by its bounce",
            body={}, timeout=30)
    except TimeoutError as exc:
        raise AssertionError(f"the bounce never answered the request: {exc}") from exc
    took = time.monotonic() - started
    body = (reply or {}).get("body") or {}
    assert took < 10, f"the bounce answered, but only after {took:.1f}s"
    assert body.get("is_bounce") is True, f"the answer is not a bounce: {reply}"
    assert _VERB in str(body.get("reason", "")), f"the bounce reason does not name the verb: {body}"
    print("ok test_a_live_request_for_an_undeclared_verb_is_answered_by_the_bounce")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

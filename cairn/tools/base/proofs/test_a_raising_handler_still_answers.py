"""A verb handler that raises still answers its asker (ticket 41f57726a609).

Measured 2026-10-14 at ticket e194f4b4cb3e: the base shim's verb dispatch called
handler(envelope) bare, so a handler that raised posted nothing. The delivery batch caught the
raise into ``refused`` — loud in the record — but the asker, correlating by reply_to, heard
nothing and sat out its whole timeout before being told the target "did not reply".

Teeth a hollow shim could not pass (a fixture shim whose verb handler raises ValueError('boom'),
against a spy bus — no live device, no store):
  1. THE ASKER IS ANSWERED: one is_bounce envelope is posted with reply_to equal to the request
     id, its reason naming ValueError and boom.
  2. THE ERROR IS NOT SWALLOWED: the delivery batch still records the raise in ``refused`` —
     with a sender and without one (a bounce that cannot be delivered must not turn one bad
     envelope into the whole batch's no_receiver).
  3. A TROUBLE IS NAMED for it through _bounce_to_sender's trouble argument:
     mail-<device>-verb-<verb>-raised.
  4. A BOUNCE POSTS NOTHING FURTHER: an envelope that is itself a bounce reaching the raising
     verb posts no bounce of its own.
  5. THE EXISTING BOUNCE PROOF STAYS GREEN: test_a_bounce_answers_the_request_that_bore_it.py
     run whole, exit 0.

Run: python3 cairn/tools/base/proofs/test_a_raising_handler_still_answers.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "41f57726a609": {
        "1": "test_a_raising_handler_answers_its_asker_with_a_correlated_bounce",
        "2": "test_the_batch_still_records_the_raise_in_refused",
        "3": "test_the_bounce_names_a_trouble_for_the_device_and_verb",
        "4": "test_a_bounce_reaching_the_raising_verb_posts_nothing",
        "5": "test_the_existing_bounce_proof_stays_green",
    },
}

_DEVICE = "raising_device_41f5"
_VERB = "boom"


class _SpyBus:
    """Records every post; serves a fixed mailbox to the batch."""

    def __init__(self, mail: list[dict] | None = None) -> None:
        self.posted: list[dict] = []
        self.mail = list(mail or [])
        self.receipted: list[str] = []

    def post(self, **envelope) -> dict:
        envelope = {"id": f"posted{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope

    def wire_delivery(self, device_id: str, deliver) -> None:
        pass

    def read(self, **kw) -> list[dict]:
        return []

    def undelivered(self, *, to: str, limit: int) -> list[dict]:
        return list(self.mail)

    def record_delivery(self, envelope_id: str, *, to: str, by: str) -> None:
        self.receipted.append(envelope_id)

    def bounces(self) -> list[dict]:
        return [e for e in self.posted if (e.get("body") or {}).get("is_bounce")]


def _shim(bus):
    from cairn.tools.base.shim import BaseShim

    def _raise(envelope):
        raise ValueError("boom")

    class _Raising:
        def declared_verbs(self):
            return {_VERB: _raise}

    class _Shim(BaseShim):
        def __init__(self, bus):
            super().__init__(bus=bus)
            self.set_diagnostic_receiver(None)

        @property
        def device_id(self):
            return _DEVICE

        def _start_device(self):
            return _Raising()

        def raise_trouble(self, *a, **kw):   # the sender's half is out of bounds here
            return None

    return _Shim(bus)


def _envelope(eid: str, *, sender: str | None = "alice", body: dict | None = None) -> dict:
    env = {"id": eid, "addressee": _DEVICE, "verb": _VERB, "body": body or {}}
    if sender:
        env["sender"] = sender
    return env


def _deliver_raising(bus, envelope) -> BaseException | None:
    try:
        _shim(bus).deliver(envelope)
    except Exception as exc:  # noqa: BLE001 — the re-raise is part of the contract
        return exc
    return None


def test_a_raising_handler_answers_its_asker_with_a_correlated_bounce():
    bus = _SpyBus()
    raised = _deliver_raising(bus, _envelope("env-41f5-1"))
    bounces = bus.bounces()
    assert len(bounces) == 1, f"expected one bounce answering the asker, posted: {bus.posted}"
    b = bounces[0]
    assert b.get("reply_to") == "env-41f5-1", f"the bounce is not correlated: {b}"
    assert b.get("to") == "alice", f"the bounce went to {b.get('to')!r}, not the asker"
    reason = str((b.get("body") or {}).get("reason", ""))
    assert "ValueError" in reason and "boom" in reason, f"reason does not name the error: {reason!r}"
    assert isinstance(raised, ValueError), f"the original error was not re-raised: {raised!r}"
    print("ok test_a_raising_handler_answers_its_asker_with_a_correlated_bounce")


def test_the_batch_still_records_the_raise_in_refused():
    for sender in ("alice", None):
        bus = _SpyBus(mail=[_envelope("env-41f5-2", sender=sender)])
        result = _shim(bus)._check_mail() or {}
        assert result.get("outcome") != "no_receiver", (
            f"sender={sender!r}: one raising envelope became the whole batch's no_receiver: {result}")
        refused = result.get("refused") or []
        assert any(r.get("envelope") == "env-41f5-2" and "ValueError" in r.get("error", "")
                   for r in refused), f"sender={sender!r}: the raise is not in refused: {result}"
        assert "env-41f5-2" not in bus.receipted, f"a raised envelope was receipted: {bus.receipted}"
    print("ok test_the_batch_still_records_the_raise_in_refused")


def test_the_bounce_names_a_trouble_for_the_device_and_verb():
    bus = _SpyBus()
    _deliver_raising(bus, _envelope("env-41f5-3"))
    bounces = bus.bounces()
    assert bounces, f"no bounce posted, so no trouble named: {bus.posted}"
    trouble = (bounces[0].get("body") or {}).get("trouble")
    assert trouble == f"mail-{_DEVICE}-verb-{_VERB}-raised", f"trouble named {trouble!r}"
    print("ok test_the_bounce_names_a_trouble_for_the_device_and_verb")


def test_a_bounce_reaching_the_raising_verb_posts_nothing():
    bus = _SpyBus()
    _deliver_raising(bus, _envelope("env-41f5-4", body={"is_bounce": True, "reason": "x"}))
    assert not bus.bounces(), f"a bounce bore a bounce: {bus.bounces()}"
    print("ok test_a_bounce_reaching_the_raising_verb_posts_nothing")


def test_the_existing_bounce_proof_stays_green():
    proof = _REPO_ROOT / "cairn/tools/base/proofs/test_a_bounce_answers_the_request_that_bore_it.py"
    r = subprocess.run([sys.executable, str(proof)], cwd=_REPO_ROOT,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"the bounce proof reds: rc={r.returncode}\n{r.stdout[-800:]}{r.stderr[-800:]}"
    print("ok test_the_existing_bounce_proof_stays_green")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

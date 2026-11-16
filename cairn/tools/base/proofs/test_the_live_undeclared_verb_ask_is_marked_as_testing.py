"""Proof for ticket bdfea1523c8e: the live undeclared-verb ask in 60cc220da787's proof is marked.

Measured 2026-11-16: the live trouble lane held mail-tester-has-no-verb-no-such-verb-60cc220da787,
7 occurrences raised by TesterShim between 2026-11-12 23:59 and 2026-11-13 12:09, each with
sender a_bounce_answers_60cc. Each came from tooth 2 of
test_a_bounce_answers_the_request_that_bore_it.py, which asks the live tester for a verb it does
not declare with an unmarked body. The tester's shim bounces it, as the tooth wants, and since
the body carries no testing mark, _bounce_to_sender also raises a live trouble. A body with a
testing mark makes the shim dispose of the trouble and stamp the mark on the bounce instead
(b3386f431ae3). The mark is a perform mark: a return mark would be returned unacted on, and the
tooth would never see its bounce.

  1. the tooth's live request carries a well-formed perform testing mark, and the bounce that
     answers it carries the same mark back (the shim took the disposal branch, not the raise);
  2. the tooth itself still passes: the bounce answers in under 10 s, naming the verb.

The world: the live tester through its published bus client (RULE 1), wrapped so each request
the tooth makes and the reply it gets are recorded.

    python3 cairn/tools/base/proofs/test_the_live_undeclared_verb_ask_is_marked_as_testing.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"bdfea1523c8e": {
    "1": "test_the_live_ask_and_its_bounce_carry_the_mark",
    "2": "test_the_bounce_tooth_still_passes"}}

PROOF_TIMEOUT_S = 120

_BOUNCE = Path(__file__).with_name("test_a_bounce_answers_the_request_that_bore_it.py")


def _bounce_module():
    spec = importlib.util.spec_from_file_location("base_bounce_answers_under_proof_bdfe", _BOUNCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Recording:
    """The live bus, every request recorded as (body asked, reply got)."""

    def __init__(self, bus):
        self._bus, self.asks = bus, []

    def request(self, *args, **kwargs):
        reply = self._bus.request(*args, **kwargs)
        self.asks.append((kwargs.get("body"), reply))
        return reply

    def __getattr__(self, name):
        return getattr(self._bus, name)


def _run_tooth():
    from cairn.tools.bus_client import bus_client
    real = bus_client.reach
    box: dict = {}

    def reach(*a, **k):
        box["bus"] = _Recording(real(*a, **k))
        return box["bus"]

    bus_client.reach = reach
    try:
        _bounce_module().test_a_live_request_for_an_undeclared_verb_is_answered_by_the_bounce()
    finally:
        bus_client.reach = real
    return box["bus"]


def test_the_live_ask_and_its_bounce_carry_the_mark():
    from cairn.tools.base import testing_mark
    rec = _run_tooth()
    assert len(rec.asks) == 1, rec.asks
    body, reply = rec.asks[0]
    mark = testing_mark.mark_of(body or {})
    assert mark is not None, f"the live ask went unmarked: {body}"
    assert mark["kind"] == testing_mark.PERFORM, f"a {mark['kind']} mark never reaches the verb: {mark}"
    back = testing_mark.mark_of((reply or {}).get("body") or {})
    assert back == mark, f"the bounce did not carry the ask's mark back, so a trouble was raised: {reply}"


def test_the_bounce_tooth_still_passes():
    rec = _run_tooth()
    assert len(rec.asks) == 1, rec.asks


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

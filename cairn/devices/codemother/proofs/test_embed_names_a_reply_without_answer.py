"""Proof for ticket 09bd383fd6a6: chart learn names an embed reply that carries no answer.

MEASURED 2026-11-12 on akiendell: ``chart learn`` raised a bare ``KeyError: 'answer'``.
deposit.embed and deposit.embed_metered index ``reply["body"]["answer"]["vector"]`` with no
guard. A body with no ``answer`` key is what the bus returns when no handler took the ask
(``is_bounce`` with a ``reason``). inference_domain's own refusal carries ``answer: None`` with
``outcome``, ``refused`` and ``detail`` (cairn/devices/inference_domain/device.py,
_handle_resolve), which crashes with a TypeError on the same line instead.

  1. test_a_reply_without_answer_is_named: for each reply shape (a bus bounce, the domain's
     refusal, an ``error`` body), embed and embed_metered raise deposit.EmbedRefused. The
     message names the reply's own error field, and the error is never a KeyError or a
     TypeError;
  2. test_a_reply_with_a_vector_is_unchanged: a reply carrying answer.vector returns the vector
     from embed, and the vector, tokens and hit from embed_metered, exactly as given.

The bus is a stub whose request() returns a scripted reply. Only codemother/deposit.py is
measured.

    bin/cairn test cairn/devices/codemother/proofs/test_embed_names_a_reply_without_answer.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"09bd383fd6a6": {
    "1": "test_a_reply_without_answer_is_named",
    "2": "test_a_reply_with_a_vector_is_unchanged",
}}


class _Bus:
    def __init__(self, body):
        self.body = body
        self.asked = []

    def request(self, **kw):
        self.asked.append(kw)
        return {"body": self.body}


# (reply body, the text its error field carries, which the refusal must name)
_GONE = [
    ({"is_bounce": True, "reason": "testing-09bd383fd6a6 no handler for resolve"},
     "testing-09bd383fd6a6 no handler for resolve"),
    ({"outcome": "refused", "refused": "HostUnreachable",
      "detail": "testing-09bd383fd6a6 host 10.0.0.9 did not answer", "answer": None, "hit": False},
     "testing-09bd383fd6a6 host 10.0.0.9 did not answer"),
    ({"error": "testing-09bd383fd6a6 resolve raised"}, "testing-09bd383fd6a6 resolve raised"),
]


def test_a_reply_without_answer_is_named():
    from cairn.devices.codemother import deposit
    # bound at call time; absent, nothing matches it, so the bare error below is what reds
    refused = getattr(deposit, "EmbedRefused", None) or type("_NoRefusal", (Exception,), {})
    for body, said in _GONE:
        for face in (deposit.embed, deposit.embed_metered):
            try:
                face(_Bus(body))("some text")
            except (KeyError, TypeError) as exc:
                raise AssertionError(f"{face.__name__} over {body} raised a bare "
                                     f"{type(exc).__name__}: {exc!r}") from exc
            except refused as exc:
                assert said in str(exc), f"{face.__name__}'s refusal does not name {said!r}: {exc}"
            else:
                raise AssertionError(f"{face.__name__} over {body} returned instead of refusing")


def test_a_reply_with_a_vector_is_unchanged():
    from cairn.devices.codemother import deposit
    vec = [0.25, -1.5, 3.0]
    body = {"answer": {"vector": vec}, "hit": True,
            "provenance": {"counters": {"prompt_eval_count": 7}}}
    bus = _Bus(body)
    assert deposit.embed(bus)("some text") == vec, "embed changed the vector"
    got = deposit.embed_metered(bus)("some text")
    assert got == {"vector": vec, "tokens": 7, "hit": True}, f"embed_metered returned {got}"
    assert len(bus.asked) == 2 and all(a["to"] == "inference_domain" and a["verb"] == "resolve"
                                       for a in bus.asked), bus.asked


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

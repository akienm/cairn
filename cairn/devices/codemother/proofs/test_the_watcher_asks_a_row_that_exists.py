"""The watcher's escalation reaches an answer, and a refusal it gets is loud (ticket 9f448a03ba40, gap B of the
2026-10-05 re-plan; Akien 8h, ~/.cairn/foreground-decisions.md).

codemother/watch.py _escalate_to_hex asks inference_domain's `infer` verb with domain
'codemother' and model 'qwen'. inference_domain has no domain row named 'codemother', so every
escalation is refused — measured 2026-10-05: 689 of 689 `outcome: refused` replies in
~/.cairn/devices/codemother/0/mail say "no domain row named 'codemother' in the domains stack".
The refusal comes back as a VALUE, never a raise, and _escalate_to_hex wraps it as a node whose
content is the reply's `answer` (None on a refusal; a dict {"text", "body"} on success), so the
watcher records a finding of nothing and activate() records no escalation_error: the failure is
silent at the one surface that would show it (Law 7).

  1. THE LIVE DOMAIN ANSWERS THE WATCHER: _escalate_to_hex over the live bus comes back with no
     error and a node whose content is non-empty text — the request names a row and a model the
     live inference_domain serves. (The prompt is fixed, so after the first run the domain's
     cache answers; the area names itself as a proof's, so the answer is a testing artifact.)
  2. A REFUSAL IS AN ERROR, NOT A NODE: a reply with outcome 'refused' yields no nodes and an
     error naming the refusal's detail.
  3. THE ANSWER IS ITS TEXT: a reply whose answer is {"text": T, ...} yields one node whose
     content is T, the string, never the dict.
  4. ACTIVATE RECORDS A RETURNED ERROR: when the escalation comes back with an error, the
     activation record carries escalation_error — not only when the escalation raises.

    python3 cairn/devices/codemother/proofs/test_the_watcher_asks_a_row_that_exists.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cairn.devices.codemother import watch  # noqa: E402

PROVES = {"9f448a03ba40": {
    "1": "test_the_live_domain_answers_the_watcher",
    "2": "test_a_refusal_is_an_error_not_a_node",
    "3": "test_the_answer_is_its_text",
    "4": "test_activate_records_a_returned_error",
}}


class _FakeBus:
    def __init__(self, body: dict):
        self.body, self.sent = body, []

    def request(self, **kw):
        self.sent.append(kw)
        return {"body": self.body}


def test_the_live_domain_answers_the_watcher():
    got = watch._escalate_to_hex("cairn-proof-watcher-row (a proof's area; testing)",
                                 "testing: the watcher asks a row that exists", None)
    assert not got.get("error"), f"escalation errored: {got.get('error')}"
    content = (got.get("nodes") or [{}])[0].get("content")
    assert isinstance(content, str) and content.strip(), f"node content is {content!r}"


def test_a_refusal_is_an_error_not_a_node():
    bus = _FakeBus({"outcome": "refused", "refused": "domain",
                    "detail": "no domain row named 'x'", "answer": None})
    with patch.object(watch, "_bus", lambda: bus):
        got = watch._escalate_to_hex("a", "r", None)
    assert got.get("nodes") == [] and "no domain row named 'x'" in str(got.get("error")), got


def test_the_answer_is_its_text():
    bus = _FakeBus({"answer": {"text": "watch the seam", "body": {"response": "watch the seam"}}})
    with patch.object(watch, "_bus", lambda: bus):
        got = watch._escalate_to_hex("a", "r", None)
    assert got.get("nodes") and got["nodes"][0]["content"] == "watch the seam", got


def test_activate_records_a_returned_error():
    logged = []
    with patch.object(watch, "_embed", lambda text: [0.0]), \
         patch("cairn.tools.tree.tree.counsel", lambda **kw: []), \
         patch.object(watch, "_escalate_to_hex", lambda *a: {"nodes": [], "error": "refused: x"}), \
         patch.object(watch, "_log_activation", logged.append):
        watch.activate("a", "r")
    assert logged and logged[0].get("escalation_error") == "refused: x", logged


def main() -> int:
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except Exception as exc:  # noqa: BLE001
                fails += 1
                print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not fails else 'RED'} — {4 - fails}/4")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

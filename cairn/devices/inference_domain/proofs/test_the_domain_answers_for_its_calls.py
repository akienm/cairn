"""Proof for ticket ``b905340f8162`` — the inference domain answers who asks for its calls.

A consumer that honours RULE 1 (the librarian first, ticket 95f8c561e742) cannot import
``domain.read_ticket``; it asks over the bus. These four teeth measure the ``calls`` verb over
a scratch ``inference_calls`` table seeded with three rows at known ``created`` times, so the
live cache is never read and the order and the since-bound are checkable to the row:

  1. ``calls`` is a declared verb, and the charter's ``public_interface`` names it.
  2. ``{'limit': 2}`` returns the two NEWEST rows, newest first.
  3. ``{'since': <the oldest row's created>}`` returns only the two later rows — a row created
     AT the bound is already seen, so it is dropped.
  4. the reply survives ``json.dumps`` — it has to cross the bus.

Hollow: before the build there is no ``calls`` verb and no ``since`` keyword, so 1-4 red.

    python3 cairn/devices/inference_domain/proofs/test_the_domain_answers_for_its_calls.py
"""

from __future__ import annotations

import contextlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "b905340f8162": {
        "1": "test_calls_is_a_declared_verb_and_the_charter_names_it",
        "2": "test_a_limit_returns_the_newest_rows_newest_first",
        "3": "test_since_returns_only_the_rows_after_it",
        "4": "test_the_reply_is_json_safe",
    },
}

_SCRATCH = contextlib.ExitStack()
_HELD: list[str] = []
_T0 = datetime(2026, 10, 13, 12, 0, 0, tzinfo=timezone.utc)
_CREATED = [_T0, _T0 + timedelta(minutes=1), _T0 + timedelta(minutes=2)]


def _table() -> str:
    """The proof's one table: three rows, one minute apart, minted on first use."""
    if not _HELD:
        from cairn.devices.inference_domain import domain
        from cairn.devices.db_domain.tools.client import store
        table = _SCRATCH.enter_context(domain.scratch_cache("calls_verb"))
        for i, created in enumerate(_CREATED):
            store.write(table, domain.CACHE_OWNER,
                        {"canonical": json.dumps({"kind": "generate", "prompt": f"row {i}"}),
                         "verdict": "miss", "answer": {"text": f"answer {i}"},
                         "provenance": {"model": "fixture"}, "cost": i, "created": created})
        _HELD.append(table)
    return _HELD[0]


def _ask(body: dict) -> dict:
    from cairn.devices.inference_domain.device import InferenceDomainDevice
    return InferenceDomainDevice()._handle_calls({"body": body}, table=_table())


def _prompts(reply: dict) -> list[str]:
    return [row["request"]["prompt"] for row in reply["calls"]]


def test_calls_is_a_declared_verb_and_the_charter_names_it():
    from cairn.devices.inference_domain.device import InferenceDomainDevice
    assert "calls" in InferenceDomainDevice().declared_verbs(), "the 'calls' verb is not declared"
    charter = json.loads((_REPO_ROOT / "cairn/devices/inference_domain/intention+why.json").read_text())
    assert any("calls" in entry for entry in charter.get("public_interface") or []), \
        f"public_interface does not name the calls verb: {charter.get('public_interface')}"


def test_a_limit_returns_the_newest_rows_newest_first():
    reply = _ask({"limit": 2})
    assert _prompts(reply) == ["row 2", "row 1"], f"want the two newest, newest first: {_prompts(reply)}"


def test_since_returns_only_the_rows_after_it():
    reply = _ask({"since": _CREATED[0].isoformat()})
    assert _prompts(reply) == ["row 2", "row 1"], f"want only the rows after since: {_prompts(reply)}"
    assert _prompts(_ask({"since": _CREATED[2].isoformat()})) == [], "a since at the newest row returns nothing"


def test_the_reply_is_json_safe():
    reply = _ask({})
    text = json.dumps(reply)
    assert len(json.loads(text)["calls"]) == 3, "all three rows cross the bus whole"


_TEETH = [test_calls_is_a_declared_verb_and_the_charter_names_it,
          test_a_limit_returns_the_newest_rows_newest_first,
          test_since_returns_only_the_rows_after_it,
          test_the_reply_is_json_safe]


def _main() -> int:
    failed = 0
    try:
        for tooth in _TEETH:
            try:
                tooth()
                print(f"  PASS  {tooth.__name__}")
            except Exception as e:   # noqa: BLE001 — every red is named, then counted
                failed += 1
                print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {e}")
    finally:
        _SCRATCH.close()
    print("green — the calls verb answers limit and since" if not failed else f"red — {failed} tooth/teeth failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

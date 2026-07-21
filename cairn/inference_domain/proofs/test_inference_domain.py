"""Proof for inference_domain — the compile-once path to the inference host.

Proven UNDER the tester (dogfood), on a real db_domain store. Teeth a hollow inference_domain
could not pass:

  - COMPILE-ONCE (Telos 1). A canonically-identical repeat is served from the store WITHOUT
    touching the host — the resolver is called once, then never again. A hollow cache that
    re-resolves every time trips this (the resolver call-count betrays it).
  - CANONICAL EQUIVALENCE. A request with the SAME content in a different key order hits the
    same entry — canonicalize collapses ordering, so equivalent questions are one question.
  - VERIFY BEFORE ANSWER (T1.3). A stored answer past its horizon is NOT served — it forces a
    re-resolve. A hollow cache that replays blindly (ignores the horizon) trips this.
  - THE ANSWER IS SERVED UNCHANGED (Law 7). A hit returns byte-for-byte what the miss stored;
    a cache that mangles the record it serves is worse than none.
  - THE OWNER GATES THE CACHE (Law 6). Only inference_domain may write the cache table; a
    non-owner write is refused by db_domain's gate.
  - THE METER IS COMPLETE (Law 3). Every call lands a row; yield_report separates tokens SPENT
    (misses) from tokens AVOIDED (hits), so the saving is measured, not asserted.

Requires the db_domain provisioning (an OS-named LOGIN CREATEDB role); uses an ephemeral table
dropped on the way out, so the real `inference_calls` store is never touched by fixtures.

    python3 cairn/inference_domain/proofs/test_inference_domain.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.db_domain import store
from cairn.db_domain.store import OwnershipError
from cairn.inference_domain import domain

# Ephemeral table + a per-run tag on every canonical, so cleanup is exact and re-runs never collide.
_NONCE = f"{os.getpid()}_{datetime.now(timezone.utc).strftime('%H%M%S%f')}"
_TABLE = f"_probe_infer_{_NONCE}"


class _CountingResolver:
    """Stands in for the host client (the injected seam). Counts calls so a silent re-resolve
    cannot hide, and can be told to return an already-expired horizon."""

    def __init__(self, *, horizon: str = "", cost: float = 100.0):
        self.calls = 0
        self._horizon = horizon
        self._cost = cost

    def __call__(self, request: dict) -> dict:
        self.calls += 1
        return {
            "answer": {"text": f"answer to {request.get('q')!r}", "served_on_call": self.calls},
            "cost": self._cost,
            "horizon": self._horizon,
            "provenance": {"host": "fake-host", "call": self.calls},
        }


def test_compile_once_a_repeat_does_not_touch_the_host():
    r = _CountingResolver()
    first = domain.resolve({"q": "sky", "n": 1}, resolver=r, table=_TABLE)
    assert first["hit"] is False and r.calls == 1, "the first ask is a miss that touches the host once"

    second = domain.resolve({"q": "sky", "n": 1}, resolver=r, table=_TABLE)
    assert second["hit"] is True, "a canonically-identical repeat must be served from the store"
    assert r.calls == 1, "a HIT must NOT touch the host — the resolver stays at one call (Telos 1)"
    # Law 7: what is served is exactly what was stored.
    assert second["answer"] == first["answer"], "a hit must serve the stored answer UNCHANGED"


def test_key_order_is_the_same_question():
    r = _CountingResolver()
    domain.resolve({"q": "reorder", "a": 1, "b": 2}, resolver=r, table=_TABLE)
    assert r.calls == 1
    # same content, different key order -> same canonical form -> a hit, no new host call.
    hit = domain.resolve({"b": 2, "q": "reorder", "a": 1}, resolver=r, table=_TABLE)
    assert hit["hit"] is True and r.calls == 1, "key-ordering must not make a new question"


def test_verify_before_answer_a_stale_entry_re_resolves():
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    r = _CountingResolver(horizon=past)
    domain.resolve({"q": "stale"}, resolver=r, table=_TABLE)
    assert r.calls == 1, "first ask is a miss"
    # The stored answer is already past its horizon -> it must NOT be served; the host is touched again.
    again = domain.resolve({"q": "stale"}, resolver=r, table=_TABLE)
    assert again["hit"] is False, "an expired answer must not be served (verify before answer, T1.3)"
    assert r.calls == 2, "a stale entry forces a re-resolve"


def test_the_owner_gates_the_cache():
    domain.ensure_cache(table=_TABLE)
    try:
        store.write(_TABLE, "impostor", {"canonical": "x", "verdict": "miss"})
        raise AssertionError("a non-owner write to the cache must be REFUSED (Law 6)")
    except OwnershipError:
        pass


def test_the_meter_measures_spent_against_avoided():
    tag = {"q": f"meter_{_NONCE}"}
    r = _CountingResolver(cost=100.0)
    domain.resolve(tag, resolver=r, table=_TABLE)       # miss  -> spends 100
    domain.resolve(tag, resolver=r, table=_TABLE)       # hit   -> avoids 100
    domain.resolve(tag, resolver=r, table=_TABLE)       # hit   -> avoids 100

    report = domain.yield_report(table=_TABLE)
    assert report["misses"] >= 1 and report["hits"] >= 2, f"every call must land a row: {report}"
    assert report["spent"] >= 100.0, f"a miss must be metered as spend: {report}"
    assert report["avoided"] >= 200.0, f"hits must be metered as avoided spend: {report}"


def _cleanup():
    """Drop this run's ephemeral cache table and its registry row — leave no fixtures."""
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TABLE,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_compile_once_a_repeat_does_not_touch_the_host,
        test_key_order_is_the_same_question,
        test_verify_before_answer_a_stale_entry_re_resolves,
        test_the_owner_gates_the_cache,
        test_the_meter_measures_spent_against_avoided,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — inference_domain: compile-once, verified-before-served, owner-gated, fully metered")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

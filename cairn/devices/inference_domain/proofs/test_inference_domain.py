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

    python3 cairn/devices/inference_domain/proofs/test_inference_domain.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.db_domain import store
from cairn.devices.db_domain.store import OwnershipError
from cairn.devices.inference_domain import domain

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


def _stacks_with_prompts(text: str) -> dict:
    """A fixture domains stack riding the REAL other three (the seam only reads domains
    rows), with a non-default vertical whose generate dressing is ``text``."""
    from cairn.devices.inference_domain import route
    stacks = dict(route.load_stacks())
    stacks["domains"] = {"domains": [
        {"name": "general", "default": True, "why": "fixture default",
         "prompts": {"generate": ""}, "escalation": {}, "prefers": []},
        {"name": "research", "default": False, "why": "fixture vertical",
         "prompts": {"generate": text}, "escalation": {}, "prefers": []},
    ]}
    return stacks


def test_a_bare_call_and_the_explicit_default_are_one_question():
    """The default rides silently (ticket falsifier tell 3): a bare request and one naming
    the default domain share a canonical — same question, one cache line — and the bare
    canonical is byte-for-byte the pre-domains form (no new key rides it)."""
    r = _CountingResolver()
    bare = domain.resolve({"q": "default-rides", "kind": "generate", "prompt": "p"},
                          resolver=r, table=_TABLE)
    named = domain.resolve({"q": "default-rides", "kind": "generate", "prompt": "p",
                            "domain": "general"}, resolver=r, table=_TABLE)
    assert named["hit"] is True and r.calls == 1, \
        "naming the default must be the same question as not naming it"
    assert bare["canonical"] == named["canonical"]
    assert "domain" not in bare["canonical"] and "system" not in bare["canonical"], \
        "a bare general call's canonical must carry no domain artifacts — byte-for-byte the old question"


def test_two_domains_are_never_one_question():
    """The cache-collision defect (hypothesize falsifier): a dressed vertical's request
    canonicalizes apart from the bare one, so one vertical's answer is never served to
    the other."""
    r = _CountingResolver()
    stacks = _stacks_with_prompts("Ground your answer in the material provided.")
    tag = {"q": "collide", "kind": "generate", "prompt": "p"}
    bare = domain.resolve(dict(tag), resolver=r, table=_TABLE, stacks=stacks)
    dressed = domain.resolve({**tag, "domain": "research"}, resolver=r, table=_TABLE,
                             stacks=stacks)
    assert bare["canonical"] != dressed["canonical"], \
        "two requests differing only in (dressing-bearing) domain must never share a canonical"
    assert dressed["hit"] is False and r.calls == 2, "the dressed ask is its own miss"


def test_the_provenance_carries_the_domain_marker_on_both_paths():
    """The watch reads this marker: a miss row and a hit row both land it, and the bare
    path lands the default's name — every row answers 'which vertical rode?'."""
    r = _CountingResolver()
    stacks = _stacks_with_prompts("dressing")
    tag = {"q": "marker", "kind": "generate", "prompt": "p", "domain": "research"}
    miss = domain.resolve(dict(tag), resolver=r, table=_TABLE, stacks=stacks)
    hit = domain.resolve(dict(tag), resolver=r, table=_TABLE, stacks=stacks)
    assert miss["provenance"]["domain"] == "research" and hit["hit"] is True
    assert hit["provenance"]["domain"] == "research", "the marker rides the hit path too"
    bare = domain.resolve({"q": "marker-bare", "kind": "generate", "prompt": "p"},
                          resolver=r, table=_TABLE, stacks=stacks)
    assert bare["provenance"]["domain"] == "general", \
        "a bare call's row must still say which vertical rode (the default's name)"


def test_editing_a_rows_prompt_is_a_new_question():
    """A prompt edit must never serve the pre-edit cached answer (hypothesize falsifier):
    the dressing is in the canonical, so new dressing = new question = fresh miss."""
    r = _CountingResolver()
    tag = {"q": "edit", "kind": "generate", "prompt": "p", "domain": "research"}
    domain.resolve(dict(tag), resolver=r, table=_TABLE,
                   stacks=_stacks_with_prompts("first dressing"))
    again = domain.resolve(dict(tag), resolver=r, table=_TABLE,
                           stacks=_stacks_with_prompts("second dressing"))
    assert again["hit"] is False and r.calls == 2, \
        "an edited row's dressing must re-ask the host, never serve the stale answer"


def test_an_unknown_domain_is_refused_before_any_spend():
    """A vertical is an authored row, never an ad-hoc string — and the refusal costs no
    host call and lands no row."""
    from cairn.devices.inference_domain.route import RouteRefused
    r = _CountingResolver()
    try:
        domain.resolve({"q": "unknown", "kind": "generate", "prompt": "p",
                        "domain": "no-such-vertical"}, resolver=r, table=_TABLE)
        raise AssertionError("an unknown domain must refuse loudly")
    except RouteRefused as e:
        assert "no-such-vertical" in str(e)
    assert r.calls == 0, "the refusal must land before the host is touched"


def test_a_malformed_domains_stack_is_refused():
    """Exactly one default, every row complete — the loader refuses, never defaults."""
    from cairn.devices.inference_domain import route
    stacks = dict(route.load_stacks())
    stacks["domains"] = {"domains": [
        {"name": "a", "default": True, "why": "w", "prompts": {}, "escalation": {}},
        {"name": "b", "default": True, "why": "w", "prompts": {}, "escalation": {}},
    ]}
    try:
        route.domain_rows(stacks)
        raise AssertionError("two default rows must refuse")
    except route.RouteRefused as e:
        assert "default" in str(e)
    stacks["domains"] = {"domains": [{"name": "only", "default": True, "why": "w"}]}
    try:
        route.domain_rows(stacks)
        raise AssertionError("an incomplete row must refuse")
    except route.RouteRefused as e:
        assert "lacks" in str(e)


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
        test_a_bare_call_and_the_explicit_default_are_one_question,
        test_two_domains_are_never_one_question,
        test_the_provenance_carries_the_domain_marker_on_both_paths,
        test_editing_a_rows_prompt_is_a_new_question,
        test_an_unknown_domain_is_refused_before_any_spend,
        test_a_malformed_domains_stack_is_refused,
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

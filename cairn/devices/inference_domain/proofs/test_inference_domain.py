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
  - A REFUSED ASK LEAVES A ROW (Law 3). A resolver that RAISES still lands a row naming the
    exception's type; the refusal propagates unchanged, spends nothing, and is never served as
    a hit. A hollow build writes only on success and the refusal rate stays unreadable.
  - THE STANDING READERS ARE UNMOVED. The third verdict is fed to each of the three probes'
    own judgements as a REAL row, not reasoned about — the one that fires on (no text, no cost)
    included.
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

import psycopg2.errors

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
    from cairn.devices.inference_domain.machines.route import route
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
    from cairn.devices.inference_domain.machines.route.route import RouteRefused
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
    from cairn.devices.inference_domain.machines.route import route
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


class _RefusingResolver(_CountingResolver):
    """The host seam RAISING instead of returning — the shape every refusal has at this door.

    Subclasses the counting resolver on purpose: `calls` still counts, so a tooth can tell
    "the ask reached the seam and the seam refused" apart from "the ask never got there."
    """

    def __init__(self, error: Exception, **kw):
        super().__init__(**kw)
        self._error = error

    def __call__(self, request: dict) -> dict:
        self.calls += 1
        raise self._error


def test_a_refused_ask_leaves_a_row():
    """A resolver that RAISES must still land a row — the refusal is a measurement (Law 3).

    Five teeth in one, because they only mean anything together:
      (a) the exception PROPAGATES unchanged — recording is not handling (constrain's bound).
      (b) a row landed, naming the exception's TYPE. RED ON HEAD, for the reason "no row was
          written" — never for "the call did not raise".
      (c) that row is NEVER served as a hit — a refusal is not an answer.
      (d) SPENT and AVOIDED are unmoved — a refusal costs nothing and avoids nothing.
      (e) an ordinary ask after the refusal is unchanged — the door still works.
    """
    tag = {"q": f"refused_{_NONCE}"}
    boom = RuntimeError("the host refused this ask")
    r = _RefusingResolver(boom)

    before = domain.yield_report(table=_TABLE)

    # (a) the exception propagates — the SAME object, not a wrapper.
    try:
        domain.resolve(tag, resolver=r, table=_TABLE)
        raise AssertionError("a raising resolver must PROPAGATE — recording is not handling")
    except AssertionError:
        raise
    except RuntimeError as e:
        assert e is boom, f"the refusal must propagate unchanged, got {e!r}"
    assert r.calls == 1, "the ask must have reached the seam"

    # (b) THE TOOTH THE TICKET EXISTS FOR. Red on HEAD: no row is written today.
    rows = store.read(_TABLE, where="canonical LIKE %s", params=(f"%refused_{_NONCE}%",))
    assert len(rows) == 1, (
        f"a refused ask must leave exactly one row; found {len(rows)}. "
        "On unmodified HEAD this is red because NO ROW WAS WRITTEN — resolve() writes only "
        "after the resolver returns, so every refusal is invisible to the meter."
    )
    row = rows[0]
    prov = row["provenance"] or {}
    assert prov.get("refused") == "RuntimeError", (
        f"the row must name the exception TYPE so refusals can be counted by kind: {prov}"
    )
    assert "the host refused this ask" in (prov.get("detail") or ""), (
        f"the row must carry the refusal's own words: {prov}"
    )
    assert prov.get("domain"), "the refused row must still say which vertical rode (the watch reads this)"
    assert row["answer"] is None, "a refusal has no answer; a row claiming one would be a lie (Law 7)"
    assert float(row["cost"] or 0) == 0.0, "a refusal spends nothing"

    # (c) the refusal must NEVER be served as a hit — the host is touched again.
    again = _RefusingResolver(RuntimeError("second refusal"))
    try:
        domain.resolve(tag, resolver=again, table=_TABLE)
        raise AssertionError("the second ask must reach the seam, not be served from the refused row")
    except AssertionError:
        raise
    except RuntimeError:
        pass
    assert again.calls == 1, "a refused row must not satisfy a later ask (it is not an answer)"

    # (d) the meter is untouched by refusals — constrain's hard bound.
    after = domain.yield_report(table=_TABLE)
    assert after["spent"] == before["spent"], f"a refusal must not move SPENT: {before} -> {after}"
    assert after["avoided"] == before["avoided"], f"a refusal must not move AVOIDED: {before} -> {after}"
    assert after["hits"] == before["hits"] and after["misses"] == before["misses"], (
        f"a refusal is neither a hit nor a miss: {before} -> {after}"
    )
    assert after["refused"] == before["refused"] + 2, (
        f"both refused asks must be counted as refused: {before} -> {after}"
    )
    assert after["calls"] == after["hits"] + after["misses"] + after["refused"], (
        f"calls == hits + misses + refused must be a checkable identity: {after}"
    )

    # (e) an ordinary ask still works, and is a plain miss.
    good = _CountingResolver()
    ok = domain.resolve({"q": f"after_refusal_{_NONCE}"}, resolver=good, table=_TABLE)
    assert ok["hit"] is False and good.calls == 1, "the door must still answer after a refusal"


def test_the_standing_readers_are_unmoved_by_a_refused_row():
    """The third verdict arrives beside FOUR standing readers. MEASURE them — do not reason.

    The chart's survey read all four and concluded none would fire on a refused row. That is a
    chain of true premises with a behavioural link in the middle, which is exactly the shape
    that has put a false sentence into an append-only history before. So: make one REAL refused
    row through the real writer, hand it to each reader's own judgement, and read the answer.

      - a_non_final_answer_is_refused_by_name — fires on (no text) AND (zero cost), which is
        precisely a refused row's shape. It must not fire, and the reason must be HONEST: the
        row falls outside its `/api/chat` jurisdiction because the resolver raised before it
        returned a provenance, so there is no path to record. Not a contrivance — 1150 hit rows
        already lack one.
      - does_a_domain_ride_the_request — demands provenance.domain on every post-era row. The
        refused row carries it, so this reader stays clean BECAUSE the row was built right.
      - does_the_route_leave_loopback — selects verdict='miss'; a third value is invisible to it.
      - yield_report — SPENT/AVOIDED unmoved (asserted in the tooth above).
    """
    from cairn.devices.inference_domain.probes import (
        a_non_final_answer_is_refused_by_name as nonfinal,
        does_a_domain_ride_the_request as domained,
        does_the_route_leave_loopback as loopback,
    )

    tag = {"kind": "generate", "q": f"readers_{_NONCE}"}
    r = _RefusingResolver(RuntimeError("refused for the readers"))
    try:
        domain.resolve(tag, resolver=r, table=_TABLE)
    except RuntimeError:
        pass

    rows = store.read(_TABLE, where="canonical LIKE %s", params=(f"%readers_{_NONCE}%",))
    assert len(rows) == 1 and rows[0]["verdict"] == "refused", f"fixture must be a real refused row: {rows}"

    nf = nonfinal.judge_rows(rows)
    assert nf["got_through"] == [], (
        f"a refused row must not read as a non-final answer that got through: {nf}"
    )
    assert nf["post_era_chat_rows"] == 0, (
        "and the REASON must be jurisdiction, not luck: a refused row carries no provenance.path, "
        f"so it is not a chat row at all: {nf}"
    )

    dm = domained.judge_rows(rows)
    assert dm["post_era_rows"] == 1, f"the refused row IS post-era for this reader: {dm}"
    assert dm["undomained"] == [], f"a refused row must still say which vertical rode: {dm}"

    lb = loopback.judge_rows(rows)
    assert lb["post_era_generate_misses"] == 0, (
        f"verdict='refused' is not a miss — the loopback reader must not see it: {lb}"
    )
    assert lb["loopback_offenders"] == [], f"and nothing may be reported against it: {lb}"


def test_the_watch_reads_a_row_the_real_writer_made():
    """THE WATCH'S FIXTURES, VALIDATED THROUGH THE PRODUCER'S OWN GATE.

    test_watch_refused_probe.py judges hand-built rows. A fixture that agrees only with its
    READER is the coin-toss-green failure: it proves the judge is self-consistent and nothing
    about the writer. So make one refused row and one answered row with the REAL writer, over
    the real store, and hand THOSE to the same judge. If the writer's shape and the watch's
    expectation ever drift apart, this is where it shows.
    """
    from cairn.devices.inference_domain.probes import a_refused_ask_leaves_a_row as watch

    ok = _CountingResolver()
    domain.resolve({"q": f"watchfix_ok_{_NONCE}"}, resolver=ok, table=_TABLE)
    bad = _RefusingResolver(RuntimeError("refused for the watch"))
    try:
        domain.resolve({"q": f"watchfix_bad_{_NONCE}"}, resolver=bad, table=_TABLE)
    except RuntimeError:
        pass

    rows = store.read(_TABLE, where="canonical LIKE %s", params=(f"%watchfix_%{_NONCE}%",))
    assert len(rows) == 2, f"expected one answered and one refused row from the real writer: {rows}"

    s = watch.judge_rows(rows)
    assert s["post_era_rows"] == 2, (
        f"rows the real writer just made must be in the watch's jurisdiction — if this is 0 the "
        f"probe's _ERA is ahead of the writer: {s}"
    )
    assert s["refused"] == 1 and s["answered"] == 1, s
    assert s["refused_by_type"] == {"RuntimeError": 1}, (
        f"the watch must read the exception type the writer actually recorded: {s}"
    )
    assert s["offenders"] == [], f"a row the real writer made must not offend its own watch: {s}"
    assert s["hollow_answers"] == [], f"and the answered row beside it must read healthy: {s}"


class _BodyCarryingResolver:
    """A resolver whose response body carries a key the PARSE never extracts — the tooth
    that proves the raw body is present, not just the extracted fields."""

    def __init__(self):
        self.calls = 0

    def __call__(self, request: dict) -> dict:
        self.calls += 1
        return {
            "answer": {
                "text": "the parsed text",
                "body": {
                    "response": "the parsed text",
                    "model": "fixture-model",
                    "done": True,
                    "prompt_eval_count": 10,
                    "eval_count": 5,
                    "context": [1, 2, 3],
                    "load_duration": 42000000,
                    "total_duration": 99000000,
                    "_unparsed_key": "THIS KEY IS NEVER EXTRACTED BY THE PARSE",
                },
            },
            "cost": 15.0,
            "provenance": {"host": "fixture-host"},
        }


def test_the_ticket_comes_back_whole():
    """THE INFERENCE TICKET IS RETRIEVABLE AND COMPLETE — the four clauses of the falsifier.

    (a) A caller names a call and gets its ticket back carrying the full request AND body.
    (b) The answer carries a key the parse never extracted (proving body, not just text).
    (c) A pre-build row lacking the body reads back UNKNOWABLE, not empty.
    (d) The reader round-trips canonical to the request dict, EQUALITY not containment.
    """
    # First, seed a PRE-BUILD row (no body on the answer) to test clause (c).
    plain = _CountingResolver()
    domain.resolve({"q": f"prebuild_{_NONCE}"}, resolver=plain, table=_TABLE)

    # Now seed a row whose answer carries the raw body.
    r = _BodyCarryingResolver()
    request_dict = {"q": f"whole_{_NONCE}", "kind": "generate", "prompt": "p"}
    domain.resolve(request_dict, resolver=r, table=_TABLE)
    assert r.calls == 1

    canonical = domain.canonicalize(request_dict)
    tickets = domain.read_ticket(canonical=canonical, table=_TABLE)
    assert len(tickets) >= 1, f"the reader must find the row by canonical: {tickets}"
    ticket = tickets[0]

    # (a) The ticket carries the full request AND the full response body.
    assert ticket["request"] is not None, "the request must be decoded from canonical"
    answer = ticket["answer"]
    assert isinstance(answer, dict), f"answer must be a dict, got {type(answer)}"
    assert "body" in answer, f"the answer must carry the raw body: {sorted(answer)}"
    assert "text" in answer, "the parsed text must still be present (additive)"

    # (b) The body carries a key the parse never extracted.
    body = answer["body"]
    assert "_unparsed_key" in body, (
        f"the body must carry keys the parse never extracted — this is what proves the BODY "
        f"is present, not just the text: {sorted(body)}"
    )
    assert body["_unparsed_key"] == "THIS KEY IS NEVER EXTRACTED BY THE PARSE"

    # (c) The pre-build row reads UNKNOWABLE, not empty.
    pre_canonical = domain.canonicalize({"q": f"prebuild_{_NONCE}"})
    pre_tickets = domain.read_ticket(canonical=pre_canonical, table=_TABLE)
    assert len(pre_tickets) >= 1
    assert pre_tickets[0]["body_status"] == "unknowable", (
        f"a pre-build row lacking the body must read UNKNOWABLE, never empty: "
        f"{pre_tickets[0].get('body_status')}"
    )

    # The new row IS whole.
    assert ticket["body_status"] == "whole", (
        f"a row with the body must read WHOLE: {ticket.get('body_status')}"
    )

    # (d) The reader round-trips canonical → request dict, EQUALITY not containment.
    # The canonical strips "domain" (by canonicalize's own rule), so compare against the
    # canonicalized form of the input — the same transform the writer applied.
    roundtripped = ticket["request"]
    expected = {k: v for k, v in request_dict.items() if k != "domain"}
    assert roundtripped == expected, (
        f"the reader must round-trip canonical → request dict by EQUALITY, not containment.\n"
        f"  got:      {roundtripped}\n"
        f"  expected: {expected}"
    )

    # Recency: read_ticket with limit returns newest first.
    all_tickets = domain.read_ticket(limit=5, table=_TABLE)
    assert len(all_tickets) >= 2, "the reader must see both rows"
    assert all_tickets[0]["created"] >= all_tickets[1]["created"], \
        "read_ticket must return rows newest first"

    # A refused row is also UNKNOWABLE (answer is None).
    bad = _RefusingResolver(RuntimeError("for wholeness"))
    try:
        domain.resolve({"q": f"refused_whole_{_NONCE}"}, resolver=bad, table=_TABLE)
    except RuntimeError:
        pass
    refused_canonical = domain.canonicalize({"q": f"refused_whole_{_NONCE}"})
    refused_tickets = domain.read_ticket(canonical=refused_canonical, table=_TABLE)
    assert len(refused_tickets) >= 1
    assert refused_tickets[0]["body_status"] == "unknowable", \
        "a refused row (answer=None) must read UNKNOWABLE"


def test_an_out_of_vocabulary_verdict_is_refused_at_the_database():
    domain.ensure_cache(table=_TABLE)
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            for good in domain.VERDICT_VOCABULARY:
                cur.execute(
                    f'INSERT INTO "{_TABLE}" (canonical, verdict, cost) '
                    f"VALUES (%s, %s, 0)",
                    (f"vocab_check_{good}_{_NONCE}", good),
                )
            conn.commit()
            try:
                cur.execute(
                    f'INSERT INTO "{_TABLE}" (canonical, verdict, cost) '
                    f"VALUES (%s, %s, 0)",
                    (f"vocab_check_invalid_{_NONCE}", "invalid"),
                )
                conn.commit()
                raise AssertionError(
                    "an out-of-vocabulary verdict must be refused by the CHECK constraint"
                )
            except psycopg2.errors.CheckViolation:
                conn.rollback()
    finally:
        conn.close()


def test_the_verdict_constraint_exists_on_the_table():
    domain.ensure_cache(table=_TABLE)
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT constraint_name FROM information_schema.table_constraints "
                "WHERE table_name = %s AND constraint_type = 'CHECK' "
                "AND constraint_name = 'verdict_vocabulary'",
                (_TABLE,),
            )
            row = cur.fetchone()
            assert row is not None, (
                f"CHECK constraint 'verdict_vocabulary' must exist on {_TABLE} "
                f"after ensure_cache()"
            )
    finally:
        conn.close()


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
        test_a_refused_ask_leaves_a_row,
        test_the_standing_readers_are_unmoved_by_a_refused_row,
        test_the_watch_reads_a_row_the_real_writer_made,
        test_the_ticket_comes_back_whole,
        test_an_out_of_vocabulary_verdict_is_refused_at_the_database,
        test_the_verdict_constraint_exists_on_the_table,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — inference_domain: compile-once, verified-before-served, owner-gated, fully metered, ticket comes back whole, verdict vocabulary held")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

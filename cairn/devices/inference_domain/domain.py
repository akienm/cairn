"""inference_domain — the ONE path to the inference host, and the compile-once gate.

THE MOVE, A THIRD TIME. `db_domain` is the only module that holds a connection to 5432;
the tester is the only owner of the network seal; `inference_domain` is the only module
that will hold the inference host client. Same physics (Law 6 + Law 4): a resource with
exactly one owner, reached only through the owner's gate — not because a supervisor forbids
the others, but because there is no other door. "Gates, not supervisors" (MAP.md).

WHAT AN INFERENCE TICKET IS. An inference request is a TICKET — a workflow node — and the
states below ARE its workflow (state IS the pipeline instance; state-machine-physics):

    RECEIVED -> CANONICALIZE -> lookup -> (hit)  VERIFY -------------------> ANSWER
                                       \\-(miss)  METER -> RESOLVE -> RECORD -> ANSWER

`resolve()` runs that workflow inside the owner. Each state is one thing the owner does,
no more — the device is not a bag of features, it is where this one workflow lives.

WHY THE CACHE IS THE POINT (Telos 1 — demonstrate inference compilation). An answered
question becomes structure (Law 1): the second time a canonically-identical request arrives,
the host is not touched — a stored answer is VERIFIED (its horizon still holds) and served.
The meter makes that saving a measured fact, not a hope (Law 3): every call lands a row, so
`yield_report()` reports tokens SPENT (on misses) against tokens AVOIDED (by hits). The
domain being the sole pipe is exactly what makes metering free and complete — there is no
uninstrumented path to the host.

WHICH ASKS EARN A ROW — the line, and where it is actually drawn (ticket
a-refused-ask-leaves-a-row). Until 2026-08-18 the row was written only AFTER the resolver
returned, so every refusal was invisible: the refusal rate of this system's only inference
door could not be read at all, and "the host is answering" and "the host is refusing every
ask" produced the same silence in the meter.

The obvious predicate was to sort the host's error classes by whether a byte had been sent —
BadRequest and RouteRefused fire before the dial, the four Host* classes after it. THAT
PREDICATE IS NOT AVAILABLE HERE, and the reason is the design rather than an oversight: the
resolver is INJECTED (the seam below), so this module does not know its host and must not
import that host's exception names to classify them. It also could not be made to work by
type: RouteRefused is pre-dispatch and a RuntimeError, exactly like the four post-dispatch
ones, so no type test separates them.

So the line is drawn where this door can actually see it, and it is the `try:` block rather
than a list: EVERY RAISE THAT ESCAPES `resolver(request)` EARNS A ROW. That is honest about
what the domain knows — it handed an ask to the seam and got no answer back; whether the
seam got as far as dialling is the seam's knowledge, not this one's — and it survives host.py
growing a seventh error class, which an enumerated tuple would not. What happens BEFORE the
call (dressing, canonicalization, connecting) writes nothing, which is why the unknown-domain
refusal stays row-less exactly as its proof has always pinned it.

RECORDING IS NOT HANDLING. The refusal propagates unchanged — same object, same type, same
message. A refused row carries `answer` NULL, `cost` 0, and a provenance naming the exception
type and its words; it never moves SPENT or AVOIDED, and it is never served as a hit (the
read path selects `verdict = 'miss'`, so a refusal cannot become an answer).

APPEND-ONLY, ON PURPOSE (Law 7). The cache is a log, never mutated: a miss appends the
answer it resolved; a hit appends the reuse it served. A stale answer is not overwritten,
it is simply out-voted by verification (a later valid miss wins; an expired one is skipped).
This is why the store's INSERT-only primitives are enough — a record of truth is not edited.

OPEN EDGES, filed not faked:
  - CANONICALIZE is first-cut STRUCTURAL only (sorted-key JSON): it collapses key-ordering
    and structural-whitespace differences, NOT semantic equivalence (paraphrases, equivalent
    prompts). Semantic canonicalization is T1.3's hard core — a filed edge, wants a /challenge
    pass and Akien's read before a shape is committed. The shallow form is honest structure;
    it does not pretend to solve the hard problem.
  - THE HOST CLIENT is injected (the `resolver` seam) and not yet wired to a real host — the
    real client will live HERE and nowhere else (credentials are instance-space; the endpoint
    is a later wiring, exactly as db_domain filed its live FORWARD path). The sole-path TOOTH
    (a tester import-scan that reds any OTHER module opening the host) is the tester's later
    tooth; today it is sole by construction.
  - VERIFY checks the HORIZON (time expiry) only. The stored FALSIFIER is carried for T1.4
    active invalidation (a falsifier firing upstream) — evaluating it is a later edge; a
    horizon is the mechanical check available now.
  - The BaseDevice introspection FACE and bus-fronting (callers poke the domain over the bus
    rather than importing it) are the runtime face — deferred until a prober/runtime pulls
    them, exactly as db_domain deferred its face.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from cairn.devices.db_domain import store

# inference_domain owns its cache. One append-only table is both the compiled answers
# (verdict='miss' rows carry the resolved answer) and the meter (every call is a row).
CACHE = "inference_calls"
CACHE_OWNER = "inference_domain"
_CACHE_COLUMNS = {
    "canonical": "text NOT NULL",
    # 'miss' (the host was touched) | 'hit' (a prior answer served) | 'refused' (the ask
    # reached the seam and the seam RAISED). Three values, and no CHECK constraint holds them
    # to it — the vocabulary is prose in three places and enforced in none. Ticket owed.
    "verdict": "text NOT NULL",
    "answer": "jsonb",           # structured, so it survives round-trip as structure (Law 7)
    "falsifier": "text",         # carried for T1.4 active invalidation (a filed edge)
    "horizon": "text",           # ISO-8601 expiry; '' = no expiry (first cut)
    "provenance": "jsonb",       # a miss: where it came from; a hit: which stored answer it served
    "cost": "numeric",           # a miss: tokens SPENT; a hit: tokens AVOIDED
    "created": "timestamptz NOT NULL DEFAULT now()",
}


def canonicalize(request: dict) -> str:
    """Reduce a request to its canonical form (state 2). FIRST CUT: structural only.

    Sorted-key JSON collapses key-ordering and structural-whitespace differences, so
    `{"a":1,"b":2}` and `{"b":2,"a":1}` are the SAME question. It does NOT collapse semantic
    equivalence — that is the hard core (T1.3), a filed edge. This is honest structure, not a
    claim to have solved paraphrase-equivalence.

    The ``domain`` NAME is excluded — it says how the request got dressed and walked, never
    what is being asked; the dressing CONTENT the domain applied (the ``system`` text) is in
    the dict and IS part of the question (ticket the-domain-carries-the-inference-side). So a
    bare call and an explicit default-domain call are one question (one cache line), a
    pre-domains row's canonical still matches its old question, and editing a row's prompt
    text changes the canonical — a new dressing is a new question, never a stale answer.
    """
    view = {k: v for k, v in request.items() if k != "domain"}
    return json.dumps(view, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _domain_dressed(request: dict, *, stacks: dict | None = None) -> tuple[dict, str]:
    """The domain seam (RECEIVED, before CANONICALIZE): resolve which vertical rides and
    dress the request with its content — on the way IN only, so a stored answer is never
    transformed on the way out (Law 7).

    A bare request rides the default row (the domains stack marks exactly one); an unknown
    name refuses loudly — a vertical is an authored row, never an ad-hoc string. Dressing
    applies to ``generate`` only (dressing an embed would move the vector, not inform the
    model), and a caller's own ``system`` outranks the row's — the reasoning stays in the
    calling device; the row only supplies what the caller left unsaid.
    """
    from cairn.devices.inference_domain import route as route_mod   # lazy: keeps import-light
    table = route_mod.domain_rows(stacks)
    name = request.get("domain") or table["default"]
    row = table["rows"].get(name)
    if row is None:
        raise route_mod.RouteRefused(
            f"no domain row named {name!r} in the domains stack — a vertical is an authored "
            f"row, never an ad-hoc string; rows: {sorted(table['rows'])}")
    dressed = dict(request)
    dressed["domain"] = name
    if dressed.get("kind", "generate") == "generate":
        content = (row.get("prompts") or {}).get("generate") or ""
        if content:
            dressed.setdefault("system", content)
    return dressed, name


def ensure_cache(*, table: str = CACHE, conn=None) -> None:
    """The cache table, owned by inference_domain — created through the one door (db_domain)."""
    store.create_owned_table(table, CACHE_OWNER, _CACHE_COLUMNS, conn=conn)


def _valid(row: dict, now: datetime) -> bool:
    """Does a stored answer still hold? (state VERIFY.) Horizon check — the mechanical one.

    An empty/absent horizon means no expiry (first cut). A stored answer past its horizon is
    NOT served — verification, not blind replay: a cache hit verifies before it answers (T1.3).
    """
    horizon = (row.get("horizon") or "").strip()
    if not horizon:
        return True
    try:
        deadline = datetime.fromisoformat(horizon)
    except ValueError:
        # An unparseable horizon is treated as no-expiry rather than silently discarding the
        # entry; getting horizon shapes wrong is a filed edge, not a reason to lose the answer.
        return True
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return now <= deadline


def _latest_valid_answer(canonical: str, now: datetime, *, table: str, conn) -> dict | None:
    """The most recent still-valid stored answer for `canonical`, or None (a genuine miss).

    Reads the append-only log; a stale (expired) answer is skipped, so a later re-resolve
    out-votes it without anything being mutated or deleted.
    """
    rows = store.read(
        table, where="canonical = %s AND verdict = 'miss'", params=(canonical,), conn=conn
    )
    valid = [r for r in rows if _valid(r, now)]
    if not valid:
        return None
    return max(valid, key=lambda r: r["created"])


def resolve(request: dict, *, resolver, now: datetime | None = None, table: str = CACHE,
            conn=None, stacks: dict | None = None) -> dict:
    """Run the inference-ticket workflow and return the answer.

    `resolver(request) -> {"answer": <jsonb-able>, "cost": <number>, "falsifier"?, "horizon"?,
    "provenance"?}` is the ONE seam that touches the host — injected today, wired to the real
    client later (and only here). On a verified hit the resolver is NEVER called: that untouched
    host call is inference compilation happening (Telos 1).

    Returns `{"answer", "hit": bool, "canonical"}`.
    """
    request, domain_name = _domain_dressed(request, stacks=stacks)
    canonical = canonicalize(request)
    own = conn or store.connect()
    try:
        ensure_cache(table=table, conn=own)
        moment = now or datetime.now(timezone.utc)

        prior = _latest_valid_answer(canonical, moment, table=table, conn=own)
        if prior is not None:
            # HIT — verified (horizon holds). Serve the stored answer UNCHANGED (Law 7: a cache
            # that mutated the answer would be worse than none). Append the reuse as a metered row
            # whose `cost` is the spend AVOIDED.
            store.write(
                table,
                CACHE_OWNER,
                {
                    "canonical": canonical,
                    "verdict": "hit",
                    "answer": prior["answer"],
                    "falsifier": prior.get("falsifier") or "",
                    "horizon": prior.get("horizon") or "",
                    "provenance": {"served_from": str(prior["created"]), "domain": domain_name},
                    "cost": prior["cost"],
                },
                conn=own,
            )
            # `cost` and `provenance` ride back ADDITIVELY (2026-07-29, ticket
            # a-node-holds-one-claim): the host reports real counters
            # (prompt_eval_count) and this door has always RECORDED them in the row
            # while returning only the answer — so a caller wanting to know what a
            # call actually cost in tokens had no way to ask, and the embed ceiling
            # stayed folklore ("about 7400 chars") measured by an operator's eye.
            # On a hit the provenance is the served_from marker, and the cost is the
            # spend AVOIDED — both the stored values, unchanged (Law 7: a cache that
            # mutated what it serves would be worse than none).
            return {"answer": prior["answer"], "hit": True, "canonical": canonical,
                    "cost": prior["cost"],
                    "provenance": {"served_from": str(prior["created"]), "domain": domain_name}}

        # MISS — the one place the host is touched. Meter (this row) + resolve + record, as one
        # append: the answer, its falsifier/horizon (so it can later be invalidated, T1.4), its
        # provenance, and the real `cost` spent.
        try:
            result = resolver(request)
        except Exception as refusal:
            # A REFUSED ASK LEAVES A ROW (Law 3 — an unrecorded refusal is an unmeasured one).
            # The row records what THIS door knows: which vertical rode, what was raised, and
            # what it said. No `path`/`host` — the resolver raised before it returned a
            # provenance, so there is none to record, and inventing one would be manufacturing
            # a measurement.
            try:
                store.write(
                    table,
                    CACHE_OWNER,
                    {
                        "canonical": canonical,
                        "verdict": "refused",
                        "answer": None,
                        "falsifier": "",
                        "horizon": "",
                        "provenance": {
                            "domain": domain_name,
                            "refused": type(refusal).__name__,
                            "detail": str(refusal)[:2000],
                        },
                        "cost": 0,
                    },
                    conn=own,
                )
            except Exception as unrecorded:      # pragma: no cover — the store being down
                # The refusal is the caller's answer and must reach them UNCHANGED (a
                # bookkeeping failure may not impersonate a host failure). Loud where it can
                # be, on stderr, and then out of the way.
                print(f"inference_domain: a refusal went UNRECORDED ({unrecorded!r}); "
                      f"the refusal itself follows", file=sys.stderr)
            raise
        provenance = dict(result.get("provenance") or {})
        provenance["domain"] = domain_name    # which vertical rode — the watch reads this
        store.write(
            table,
            CACHE_OWNER,
            {
                "canonical": canonical,
                "verdict": "miss",
                "answer": result["answer"],
                "falsifier": result.get("falsifier") or "",
                "horizon": result.get("horizon") or "",
                "provenance": provenance,
                "cost": result.get("cost", 0),
            },
            conn=own,
        )
        return {"answer": result["answer"], "hit": False, "canonical": canonical,
                "cost": result.get("cost", 0),
                "provenance": provenance}
    finally:
        if conn is None:
            own.close()


def yield_report(*, table: str = CACHE, conn=None) -> dict:
    """The meter read back (how_it_learns): tokens SPENT vs AVOIDED — is compilation paying off?

    Spent = the cost of misses (real host calls). Avoided = the cost hits did not have to pay.
    Avoided climbing against spent IS the evidence the cache earns its keep (Telos 1, Law 3).
    """
    rows = store.read(table, conn=conn)
    hits = [r for r in rows if r["verdict"] == "hit"]
    misses = [r for r in rows if r["verdict"] == "miss"]
    spent = float(sum((r["cost"] or 0) for r in misses))
    avoided = float(sum((r["cost"] or 0) for r in hits))
    return {
        "calls": len(rows),
        "hits": len(hits),
        "misses": len(misses),
        "spent": spent,
        "avoided": avoided,
    }

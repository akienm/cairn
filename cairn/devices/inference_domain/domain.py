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

import hashlib
import inspect
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from cairn.devices.db_domain import store
from cairn.tools.base import address
from cairn.tools.base.diagnostic import DiagnosticBase

# inference_domain owns its cache. One append-only table is both the compiled answers
# (verdict='miss' rows carry the resolved answer) and the meter (every call is a row).
CACHE = "inference_calls"
CACHE_OWNER = "inference_domain"
_CACHE_COLUMNS = {
    "canonical": "text NOT NULL",
    # 'miss' (the host was touched) | 'hit' (a prior answer served) | 'refused' (the ask
    # reached the seam and the seam RAISED). Three values, held by CHECK constraint
    # verdict_vocabulary (ticket 6890cf7e4053).
    "verdict": "text NOT NULL",
    "answer": "jsonb",           # structured, so it survives round-trip as structure (Law 7)
    "falsifier": "text",         # carried for T1.4 active invalidation (a filed edge)
    "horizon": "text",           # ISO-8601 expiry; '' = no expiry (first cut)
    "provenance": "jsonb",       # a miss: where it came from; a hit: which stored answer it served
    "cost": "numeric",           # a miss: tokens SPENT; a hit: tokens AVOIDED
    "created": "timestamptz NOT NULL DEFAULT now()",
}


# ── the trail: this door's crossings, written down ───────────────────────────
#
# WHY THERE IS A CLASS IN A MODULE OF PLAIN FUNCTIONS. ``emit`` is a method on
# ``DiagnosticBase``, and this module has no object for it to hang on. The five lines below
# ARE that object. They are not a new mechanism: a class defined in this file carries
# ``cairn.devices.inference_domain.domain`` in its ``__module__``, so ``DiagnosticBase``
# derives the component — ``inference_domain`` — from the address the class already had, and
# the records land in ``~/.cairn/logs/inference_domain/0/`` as one JSON file per emission, with nobody
# wiring anything. Nothing here is hand-spelled; the one authored string is the source name.
# ``charter.projector`` does the same thing for the same reason (2026-08-18), and copying its
# shape is cheaper than a floor abstraction bought for a second user.
#
# WHY THE CROSSINGS ARE THE THREE BRANCHES OF ``resolve`` AND NOTHING ELSE. Akien's brief
# draws the grain: "every single everyting is supposed to log major boundry crossings and
# state changes. that doesn't mean every function call, or every heartbeat from the ground
# loop... but starting an inference call sure should." A miss IS starting an inference call.
# A refusal is that same crossing, failed. A hit is the crossing NOT taken, and it earns a
# record for one reason that is not symmetry: without it the trail cannot be read against the
# meter, because a trail carrying only misses looks identical whether the hits went
# unrecorded or never happened. One record per call, at the outcome — never one per routed
# rung, which would make an ordinary cheapest-first walk read as three failures.
#
# THE RECORDS CARRY WHAT THE BRANCH ALREADY HOLDS. Every value below is read out of a dict
# this function is already holding when it emits — the stored row on a hit, the resolver's
# provenance on a miss. Nothing re-derives, nothing re-dials, and the compile-once claim
# (falsifier 1) is untouched: adding the trail does not touch the host one extra time.
class _Trail(DiagnosticBase):
    @property
    def diagnostic_source(self) -> str:
        return "inference_domain.domain.resolve"


_trail = _Trail()

# What a miss record carries about the far end — read out of the same `provenance` dict the
# row is written from, so the two records cannot disagree about the endpoint.
#
# NO COST AND NO COUNTERS, and that bound was MEASURED into place rather than reasoned. The
# first draft put the spend on both lines; the hit line came back from the receiver DEGRADED,
# because `cost` off a stored row is a postgres `Decimal` and the trail is a JSONL file. The
# receiver did the right thing (the crossing survived, the payload was named unwritable), and
# the failure asked a better question than the bug: why is spend on the trail at all? It is
# already on the row, keyed by the same canonical the line points at. So the split is one
# question each — the trail answers "which vertical, which host, over which path, with which
# model", the meter answers "what did it cost" — and a number living in two records that can
# drift apart is exactly what this ticket's own agreement criterion exists to forbid.
_ENDPOINT_KEYS = ("domain", "host", "path", "model", "provider", "route_walked")


def set_diagnostic_receiver(receiver) -> None:
    """Divert this door's stream (an Inspector, a temp-tree ``BreadcrumbLog``), or, with
    ``None``, silence it and HOLD the records in memory. Not the ordinary path: unwired, the
    records go to this device's own trail."""
    _trail.set_diagnostic_receiver(receiver)


def set_diagnostic_roots(roots) -> None:
    """Point the trail at a different WORLD — the seam a proof reaches for. It keeps the
    default receiver (the mechanism under test) and moves the tree it writes into; wiring a
    substitute receiver would quietly prove the substitute instead."""
    _trail.set_diagnostic_roots(roots)


def held_diagnostics() -> list[dict]:
    """Records emitted with nowhere to send them — held, never dropped (Law 7). Non-empty is
    itself a finding: either this door was deliberately silenced, or the component name
    stopped deriving and the trail has no address."""
    return _trail.held_diagnostics()


def diagnostic_trail():
    """Where this door's crossings land. Resolves and touches nothing."""
    return _trail.diagnostic_trail()


def diagnostic_records() -> list[dict]:
    """What this door's crossings ARE — read from wherever ``diagnostic_trail`` points, so a
    caller under ``set_diagnostic_roots`` reads the world it moved the device into."""
    return _trail.diagnostic_records()


# ── the task ticket: one artifact per call, the call made inspectable ────────
#
# TICKET ea4a6151300f. The meter (a row) says what a call COST and the trail (a line) says
# which far end it crossed to; neither says WHO asked, what they asked FOR versus what the
# route actually SELECTED, or how the call ENDED. So every ``resolve`` now writes ONE FILE —
# the task ticket — into this device's own instance-space, and hands its path back on the
# result. The receiver can open it or ignore it; either way the call is inspectable after
# the fact, which is what a ticket is for.
#
# WHY A FILE AND NOT MORE COLUMNS (Akien 2026-08-31, superseding the first cut): the
# inference call is a TASK the domain performs, and a task produces an ARTIFACT. The row
# stays the index and the meter; the ticket is the whole record, in the one root that is
# nobody's shared truth (instance-space, never git). It is not a parallel store — nothing
# is read back from it to answer a call, and the cache is still the one place a hit comes
# from.
#
# THE CALLER IS MEASURED, NOT DECLARED (Akien: "call chain or message envelope"). Over the
# bus the shim knows the sender and passes it in; a direct caller (tree.py's embed, the
# inference seam a subprocess uses) declared nothing, so the identity is read off the call
# stack — the nearest frame that is not this module, named by its class-space address. A
# call that leaves NO trace of who asked records ``unknown`` rather than a blank, because
# a blank is a field somebody forgot and ``unknown`` is a measurement that found nothing.
TICKETS = "tickets"
_TICKET_FIELDS = ("id", "caller", "request", "canonical", "verdict", "outcome",
                  "specified", "selected", "response", "cost", "timings", "trouble")
_HERE = Path(__file__).resolve()
_REPO = address.ROOTS["repo"]


def tickets_dir(roots: dict | None = None) -> Path:
    """Where this device's task tickets land: ``<instance>/devices/inference_domain/0/tickets``.

    Follows the trail's roots (``set_diagnostic_roots``) so a proof that moved the device
    into a temp world finds its tickets there too, never in the live tree."""
    table = roots if roots is not None else getattr(_trail, "_diagnostic_roots", None)
    return address.instance_path("inference_domain", 0, table) / TICKETS


def _frame_identity(frames) -> str | None:
    """The nearest caller outside this module, as a class-space address — or None."""
    for frame in frames:
        filename = getattr(frame, "filename", None) or (frame[1] if isinstance(frame, tuple) else None)
        if not filename or filename.startswith("<"):
            continue                    # <stdin>, <string>, <frozen …>: nowhere to point at
        path = Path(filename)
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if not resolved.is_file():
            continue
        if resolved == _HERE:
            continue
        try:
            rel = resolved.relative_to(_REPO)
        except ValueError:
            # Outside class-space: a shell, a REPL, a script with no address to name.
            continue
        func = getattr(frame, "function", None) or (frame[3] if isinstance(frame, tuple) else "")
        return f"{rel.as_posix()}:{func}" if func else rel.as_posix()
    return None


def caller_identity(explicit: str | None = None, *, frames=None) -> dict:
    """Who asked — ``{"identity", "how"}``. ``how`` says which measurement produced it:
    ``declared`` (the caller or the shim named it), ``call_chain`` (read off the stack),
    or ``none`` (nothing named it — identity ``unknown``)."""
    if explicit:
        return {"identity": str(explicit), "how": "declared"}
    if frames is None:
        frames = inspect.stack()[1:]
    found = _frame_identity(frames)
    if found:
        return {"identity": found, "how": "call_chain"}
    return {"identity": "unknown", "how": "none"}


def _specified(request: dict, domain_name: str) -> dict:
    """What the CALLER asked for — read off the request before the route touched it."""
    return {"model": request.get("model"),
            "provider": request.get("provider"),
            "domain": request.get("domain") or domain_name,
            "kind": request.get("kind", "generate")}


def _selected(provenance: dict) -> dict:
    """What the route actually USED — read off the resolver's own provenance, so the two
    blocks can disagree and the disagreement is the finding (a route that escalated)."""
    return {k: provenance.get(k) for k in ("model", "provider", "host", "path", "route_walked")
            if k in provenance}


_counter = 0


def _ticket_path(ticket: dict, *, roots: dict | None = None) -> Path:
    """Allocate the ticket's address before anything is written, so a trouble raised on
    the way down can NAME the ticket it belongs to (the chart's fourth criterion)."""
    global _counter
    _counter += 1
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    name = f"{stamp}-{ticket['canonical_digest'][:12]}-{os.getpid()}-{_counter}.json"
    return tickets_dir(roots) / name


def _write_task_ticket(ticket: dict, *, roots: dict | None = None,
                       path: Path | None = None) -> Path:
    """One JSON file per call. Loud on failure (Law 7) — but a ticket that cannot be
    written may not eat the answer, so the caller wraps this in its own try."""
    path = path or _ticket_path(ticket, roots=roots)
    path.parent.mkdir(parents=True, exist_ok=True)
    ticket = dict(ticket, id=path.stem)
    path.write_text(json.dumps(ticket, indent=2, sort_keys=True, default=str) + "\n",
                    encoding="utf-8")
    return path


def read_task_tickets(*, roots: dict | None = None, limit: int | None = None) -> list[dict]:
    """The tickets read back, newest first. A reader's face for the probe and the operator."""
    folder = tickets_dir(roots)
    if not folder.is_dir():
        return []
    names = sorted((p for p in folder.glob("*.json")), reverse=True)
    if limit is not None:
        names = names[:limit]
    out = []
    for p in names:
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            out.append({"id": p.stem, "unreadable": f"{type(exc).__name__}: {exc}"})
    return out


def ticket_lacks(ticket: dict) -> list[str]:
    """What a task ticket is MISSING to be complete — ``[]`` is complete. The probe and the
    proof judge with this one predicate so they cannot disagree about the word."""
    lacks = [f for f in _TICKET_FIELDS if f not in ticket]
    caller = ticket.get("caller") or {}
    if not caller.get("identity"):
        lacks.append("caller.identity")
    outcome = ticket.get("outcome") or {}
    if outcome.get("kind") not in ("answered", "refused"):
        lacks.append("outcome.kind")
    if outcome.get("kind") == "refused":
        if not outcome.get("refused"):
            lacks.append("outcome.refused")
        if not ticket.get("trouble"):
            lacks.append("trouble")
    timings = ticket.get("timings") or {}
    for k in ("started", "finished", "elapsed_ms"):
        if k not in timings:
            lacks.append(f"timings.{k}")
    return lacks


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


def canonical_digest(text: str) -> str:
    """SHA-256 hex digest of canonical text — the thin pointer that replaces the full text
    in the trail, joinable back to the store's ``canonical`` column by hashing that column."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    from cairn.devices.inference_domain.machines.route import route as route_mod   # lazy: keeps import-light
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


VERDICT_VOCABULARY = ("hit", "miss", "refused")

def ensure_cache(*, table: str = CACHE, conn=None) -> None:
    """The cache table, owned by inference_domain — created through the one door (db_domain)."""
    store.create_owned_table(table, CACHE_OWNER, _CACHE_COLUMNS, conn=conn)
    store.add_owned_constraint(
        table, CACHE_OWNER, "verdict_vocabulary",
        "verdict IN ('hit', 'miss', 'refused')",
        conn=conn,
    )


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
            conn=None, stacks: dict | None = None, sink=None, caller: str | None = None) -> dict:
    """Run the inference-ticket workflow and return the answer.

    `resolver(request) -> {"answer": <jsonb-able>, "cost": <number>, "falsifier"?, "horizon"?,
    "provenance"?}` is the ONE seam that touches the host — injected today, wired to the real
    client later (and only here). On a verified hit the resolver is NEVER called: that untouched
    host call is inference compilation happening (Telos 1).

    Returns `{"answer", "hit": bool, "canonical", "cost", "provenance", "ticket"}` — ``ticket``
    is the path of the task ticket this call wrote (ticket ea4a6151300f), so the receiver can
    inspect what happened rather than only consume the answer. ``caller`` is the asker's
    identity when the caller (or the shim, from the envelope's sender) declares it; undeclared,
    it is read off the call stack, and a call nothing can name records ``unknown``.
    """
    sink = sink or _trail
    started = datetime.now(timezone.utc)
    tick = time.perf_counter()
    who = caller_identity(caller, frames=inspect.stack()[1:])
    request, domain_name = _domain_dressed(request, stacks=stacks)
    canonical = canonicalize(request)
    ticket = {
        "caller": who,
        "request": request,
        "canonical": canonical,
        "canonical_digest": canonical_digest(canonical),
        "specified": _specified(request, domain_name),
        "cache": {"table": table},
    }

    def _close(verdict: str, *, outcome: dict, selected: dict, response, cost, trouble,
               path: Path | None = None) -> Path | None:
        """Finish and write the ticket. In its own try: a ticket that cannot be written is
        said loudly on stderr and the ANSWER (or the refusal) still reaches the caller."""
        finished = datetime.now(timezone.utc)
        ticket.update({
            "verdict": verdict,
            "outcome": outcome,
            "selected": selected,
            "response": response,
            "cost": cost,
            "trouble": trouble,
            "timings": {"started": started.isoformat(), "finished": finished.isoformat(),
                        "elapsed_ms": round((time.perf_counter() - tick) * 1000, 3)},
        })
        try:
            return _write_task_ticket(ticket, path=path)
        except Exception as unwritten:      # pragma: no cover — instance-space unwritable
            print(f"inference_domain: a task ticket went UNWRITTEN ({unwritten!r}); "
                  f"the answer itself follows", file=sys.stderr)
            return None
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
            #
            # THE TRAIL: the crossing that did NOT happen. The gate is the verdict word the
            # row already uses, so the trail and the meter speak one vocabulary and can be
            # counted against each other without a translation table in between.
            sink.emit(
                "hit",
                pointer=canonical_digest(canonical),
                values={"domain": domain_name, "served_from": str(prior["created"])},
                now=moment,
            )
            served = {"served_from": str(prior["created"]), "domain": domain_name}
            path = _close("hit", outcome={"kind": "answered", "served_from": str(prior["created"])},
                          selected=_selected(dict(prior.get("provenance") or {})),
                          response=prior["answer"], cost=prior["cost"], trouble=None)
            return {"answer": prior["answer"], "hit": True, "canonical": canonical,
                    "cost": prior["cost"], "provenance": served,
                    "ticket": str(path) if path else None}

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
            # THE TRAIL: the crossing attempted and failed. In its OWN try, and after the
            # row rather than inside its try, for two separate reasons. (1) The refusal is
            # the caller's answer: nothing here may replace it, so a trail failure is caught
            # and spoken rather than raised — the same contract the row above already holds
            # to. (2) Sharing the row's try would make a store outage silently cost the trail
            # line too, and the trail's whole value is being the record that survives when
            # the store is the thing that broke.
            try:
                sink.emit(
                    "refused",
                    pointer=canonical_digest(canonical),
                    values={"domain": domain_name, "refused": type(refusal).__name__,
                            "detail": str(refusal)[:2000]},
                    now=moment,
                )
            except Exception as untrailed:      # pragma: no cover — the trail being unwritable
                print(f"inference_domain: a refusal left no trail record ({untrailed!r}); "
                      f"the refusal itself follows", file=sys.stderr)
            # THE TROUBLE LANE (ticket ea4a6151300f): a failed call is a fault, and a fault
            # that cannot escalate anywhere else goes to trouble. ``raise_trouble`` is the
            # inherited tool on DiagnosticBase — one emission file in this device's own log
            # home, folded into a counted ticket at the trouble device's drain — so no
            # import of the trouble device and no second path: the SAME defect (the same
            # canonical refused again) increments, it does not shout twice. Its own try,
            # for the same reason the trail's is: the refusal is the caller's answer.
            trouble = None
            ticket_path = _ticket_path(ticket)     # named first, so the trouble can point at it
            try:
                raiser = sink if hasattr(sink, "raise_trouble") else _trail
                record = raiser.raise_trouble(
                    f"inference-refused-{canonical_digest(canonical)[:16]}",
                    why=f"the inference host refused an ask at domain {domain_name!r}: "
                        f"{type(refusal).__name__}: {str(refusal)[:200]}",
                    detail={"refused": type(refusal).__name__, "detail": str(refusal)[:2000],
                            "domain": domain_name, "caller": who,
                            "canonical_digest": canonical_digest(canonical),
                            "ticket": str(ticket_path)},
                    now=moment)
                trouble = {"identity": record.get("pointer"), "poke": record.get("poke"),
                           "home": record.get("home")}
            except Exception as unraised:      # pragma: no cover — the lane unreachable
                print(f"inference_domain: a refusal raised no trouble ({unraised!r}); "
                      f"the refusal itself follows", file=sys.stderr)
                trouble = {"identity": None, "poke": f"unraised: {unraised!r}"}
            path = _close("refused",
                          outcome={"kind": "refused", "refused": type(refusal).__name__,
                                   "detail": str(refusal)[:2000]},
                          selected={}, response=None, cost=0, trouble=trouble,
                          path=ticket_path)
            if path is not None:
                refusal.task_ticket = str(path)
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
        # THE TRAIL: the crossing that actually happened — "starting an inference call sure
        # should" log (Akien, 2026-08-18). The endpoint keys are the ones the resolver's own
        # provenance carries (`host`, `path`, `model` from ollama_resolver; `provider` and
        # `route_walked` added by the routed resolver when rungs were skipped), lifted by a
        # roster rather than a chain of `.get`s so a key the resolver did not report is
        # ABSENT from the record instead of present-and-null. An absent key says the resolver
        # did not report it; a null one says it reported nothing, and they are different
        # facts about the host.
        sink.emit(
            "miss",
            pointer=canonical_digest(canonical),
            values={k: provenance[k] for k in _ENDPOINT_KEYS if k in provenance},
            now=moment,
        )
        path = _close("miss", outcome={"kind": "answered"}, selected=_selected(provenance),
                      response=result["answer"], cost=result.get("cost", 0), trouble=None)
        return {"answer": result["answer"], "hit": False, "canonical": canonical,
                "cost": result.get("cost", 0),
                "provenance": provenance,
                "ticket": str(path) if path else None}
    finally:
        if conn is None:
            own.close()


def read_ticket(*, canonical: str | None = None, limit: int | None = None,
                table: str = CACHE, conn=None) -> list[dict]:
    """The reader face: inference_calls rows themselves, not an aggregate (yield_report) but
    the individual tickets — request and answer.

    By canonical (exact match), or by recency (most recent first). Each returned row carries:
      - ``request``: the decoded request dict (canonical round-tripped through json.loads)
      - ``body_status``: ``"whole"`` if the answer carries the host's raw body,
        ``"unknowable"`` if the row predates the build that carries it (pre-build rows are
        never "empty" — absent-not-empty, which is where a hollow green would hide)
      - everything else the row already has
    """
    own_conn = conn or store.connect()
    try:
        if canonical is not None:
            rows = store.read(table, where="canonical = %s", params=(canonical,), conn=own_conn)
        else:
            rows = store.read(table, conn=own_conn)
        rows.sort(key=lambda r: r["created"], reverse=True)
        if limit is not None:
            rows = rows[:limit]
        result = []
        for row in rows:
            enriched = dict(row)
            try:
                enriched["request"] = json.loads(row["canonical"])
            except (json.JSONDecodeError, TypeError):
                enriched["request"] = None
            answer = row.get("answer")
            if answer is None:
                enriched["body_status"] = "unknowable"
            elif isinstance(answer, dict) and "body" in answer:
                enriched["body_status"] = "whole"
            else:
                enriched["body_status"] = "unknowable"
            result.append(enriched)
        return result
    finally:
        if conn is None:
            own_conn.close()


def yield_report(*, table: str = CACHE, conn=None) -> dict:
    """The meter read back (how_it_learns): tokens SPENT vs AVOIDED — is compilation paying off?

    Spent = the cost of misses (real host calls). Avoided = the cost hits did not have to pay.
    Avoided climbing against spent IS the evidence the cache earns its keep (Telos 1, Law 3).
    """
    rows = store.read(table, conn=conn)
    hits = [r for r in rows if r["verdict"] == "hit"]
    misses = [r for r in rows if r["verdict"] == "miss"]
    refused = [r for r in rows if r["verdict"] == "refused"]
    spent = float(sum((r["cost"] or 0) for r in misses))
    avoided = float(sum((r["cost"] or 0) for r in hits))
    return {
        "calls": len(rows),
        "hits": len(hits),
        "misses": len(misses),
        "refused": len(refused),
        "spent": spent,
        "avoided": avoided,
    }

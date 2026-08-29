"""librarian/loop.py — the core resolve-or-generate loop: always the graph first.

Akien's ruling, 2026-07-27, verbatim: "The librarian ALWAYS reaches for the graph trees,
and if the graph tree can't, the LLM is used to backfill it until it can." And the
load-bearing clause: "escalate on graph failure to a node depositing call THAT VALIDATES
BY RESUBMITTING THE SAME REQUEST." The host is never in the answer path — it supplies
NODES on a miss and the graph folds them in. RE-SCOPED 2026-08-09 (ticket
the-tenure-loop, under Akien's "persistance!" ruling): the resubmit still drives the
loop's progress check, but a same-crossing mint no longer counts as the proof — the
validation COMPLETES at a LATER crossing, because same-crossing corroboration is the
measured defect (a memory validating itself at birth). Law 1 as a runtime mechanism.

THE LIVELOCK, FIXED AS PHYSICS (filed 2026-07-27, held-librarian's ruling section; fixed
here AS the loop goes live, not after). The trap: escalation asks the host for nodes;
nodes deposit; the request resubmits; the graph still fails; escalation fires again with
the SAME request — which canonicalizes to the same cache key, HITS, and returns the very
nodes that just failed, while yield_report books every spin as tokens AVOIDED. The fix is
two-layered:
  1. THE KEY CARRIES THE GRAPH STATE. The backfill prompt embeds ``tree_state``'s digest
     (and the nearest already-known nodes), so 'same request, changed graph' canonicalizes
     to a DIFFERENT key — a genuine miss, a real host call, fresh nodes for the new
     situation. 'Same request, same graph' still hits — honestly, it IS the same question.
  2. THE PROGRESS GATE. A backfill round that grows the tree by nothing (every node a
     duplicate or refused at the door) terminates the loop LOUDLY as ``no_progress`` —
     the model cannot extend the graph for this question, and spinning would relabel
     that fact as savings.

RESOLUTION IS A MEASUREMENT WITH ITS THRESHOLD VISIBLE: the graph "can" answer when the
walk's best cosine clears ``RESOLUTION_FLOOR``. The floor is a GUESS seeded by the first
live walk (n=1: the right node scored 0.7473, the adjacent one 0.6278 — 0.65 splits
them), labeled as such and returned in every verdict so no caller mistakes it for settled
(Law 3). It tunes against real use.

Import-pure like trees.py: both seams arrive as the one injected ``resolve`` callable
(inference_domain's shape — kind "embed" and kind "generate" through the same door);
live wiring in ``live.py``, never here. The proof pins the allowlist.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from cairn.devices.librarian.trees import (
    NODES, DepositRefused, LibrarianDevice, corroborate, tree_state,
)

# The floor a walk must clear to count as resolved — a labeled guess, not a settled law
# (seeded by the first live walk, n=1; see the module note). Returned in every verdict.
RESOLUTION_FLOOR = 0.65

# Rounds of backfill before the loop reports exhaustion. Small on purpose: each round is
# a real host call, and a question three rounds cannot ground is a finding, not a retry.
MAX_BACKFILLS = 3

# THE TENURE DIALS — hand-set at birth, declared per learns-its-gates (ticket
# the-tenure-loop, dials_declared): the WATCHME accumulates the evidence their learning
# needs; a future cast moves them from hand-set to learned.
#
# Distinct cross-question corroborations before standing turns 'earned'. Two, because one
# could be a phrasing coincidence between two questions; two independent questions walking
# to the same node is the smallest count that is a pattern rather than an echo.
PROMOTION_THRESHOLD = 2
# Days an UNCORROBORATED hypothesis keeps counting as resolution evidence. Fourteen,
# because the measured defect (2026-08-09: 48 of 70 nodes were same-turn slug-shards) was
# hours old, not weeks — a fortnight gives a genuine fact every chance to be corroborated
# by real use before it fades, while a shard nobody ever walks back to goes quiet.
DECAY_HORIZON = timedelta(days=14)


class BackfillRefused(RuntimeError):
    """A backfill draft the loop cannot honestly use — refused loudly, raw carried whole."""


def backfill_prompt(question: str, state: dict, known: list[dict]) -> str:
    """The node-depositing ask. Deterministic per (question, graph-state, nearest-known) —
    which IS the livelock fix's first layer: the graph state rides in the prompt, so the
    cache key moves when the tree does. The already-known list steers the model away from
    re-supplying residents (fighting no_progress from the other side)."""
    known_lines = "\n".join(f"- {n['content']}" for n in known) or "- (the tree is empty)"
    return (
        "A knowledge graph could not resolve the REQUEST below. Supply 2 to 5 NEW nodes — "
        "short, self-contained declarative statements of fact — that would let the graph "
        "resolve it. Do not restate ALREADY-KNOWN nodes. Output ONLY one strict JSON "
        'object: {"nodes": ["statement", ...]}.\n\n'
        f"REQUEST: {question}\n"
        f"GRAPH-STATE: {state['digest']} ({state['nodes']} nodes)\n"
        f"ALREADY-KNOWN (nearest):\n{known_lines}"
    )


def parse_backfill(raw: str) -> list[str]:
    """The draft's nodes, or a loud refusal carrying the raw draft WHOLE (first-pass
    diagnostic). One tolerated presentation quirk, as everywhere: a markdown fence is
    wrapping, not content."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    try:
        draft = json.loads(text)
    except ValueError:
        draft = None
    nodes = draft.get("nodes") if isinstance(draft, dict) else None
    if not (isinstance(nodes, list) and nodes and all(isinstance(n, str) and n.strip() for n in nodes)):
        raise BackfillRefused(
            "backfill: the draft is not one JSON object with a non-empty 'nodes' list of "
            f"non-empty strings — the model failed the contract. Raw draft, carried whole: {raw!r}"
        )
    return [n.strip() for n in nodes]


def _question_digest(question: str) -> str:
    return hashlib.sha256(question.encode("utf-8")).hexdigest()[:12]


def _label_evidence(walk: list[dict], deposited: list[str], now: datetime) -> None:
    """Mark each walked node ``evidence: True|False`` — may it count toward RESOLVED?

    Four refusals, three of them tenure behaviours (tickets the-tenure-loop and
    revision-with-receipts):
      - REFUTATION: a node someone has retired as WRONG never counts again. This is tested
        FIRST, above the earned pass-through, and the order is the whole correctness of the
        clause: a node that had EARNED tenure before it was refuted would otherwise
        short-circuit to ``evidence: True`` and the retirement would be silently
        ineffective for exactly the nodes that matter most.
      - CROSSING HONESTY: a node this crossing itself minted is excluded — a deposit
        cannot count toward resolving the utterance that spawned it (the 2026-08-09
        measured defect: four same-turn mints cited as a RESOLVED walk).
      - LAZY DECAY: an uncorroborated hypothesis older than DECAY_HORIZON has faded —
        nobody independently walked to it in its window. Earned nodes and nodes carrying
        any attestation count whole, whatever their age. Arithmetic at read; no clock
        process anywhere.
    The node STAYS in the walk, labeled with ``evidence_why`` — the reader sees what was
    near and why it did not count (Law 3: the measurement visible, not silently
    subtracted). All of it is arithmetic over fields the row already carries: no new
    query, no generate, no clock process.
    """
    excluded = set(deposited)
    for node in walk:
        if node.get("standing") == "refuted":
            node["evidence"] = False
            node["evidence_why"] = "refuted — retired as wrong; see provenance.attestations"
            continue
        if node["node_id"] in excluded:
            node["evidence"] = False
            node["evidence_why"] = "minted by this crossing — cannot resolve its own utterance"
            continue
        if node.get("standing") == "earned":
            node["evidence"] = True
            node["evidence_why"] = "earned tenure"
            continue
        prov = node.get("provenance") or {}
        birth_q = prov.get("question")
        # Only a CROSS-question attestation exempts from decay — a same-question echo
        # (the node's own birth re-arriving as a duplicate) is not independent reach,
        # or the home-field shard would immortalize itself by re-minting.
        if any(a.get("question") != birth_q for a in (prov.get("attestations") or [])):
            node["evidence"] = True
            node["evidence_why"] = "attested from a different question — independent reach"
            continue
        created = node.get("created")
        if created is None:
            node["evidence"] = True   # no birth record — age cannot be held against it
            node["evidence_why"] = "no birth record — age cannot be held against it"
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        node["evidence"] = (now - created) <= DECAY_HORIZON
        node["evidence_why"] = ("within the decay horizon" if node["evidence"]
                                else "uncorroborated hypothesis past the decay horizon")


def _evidence_best(walk: list[dict]) -> float | None:
    """The best cosine among nodes allowed to count — the number the floor test reads."""
    counted = [n["similarity"] for n in walk if n.get("evidence")]
    return max(counted) if counted else None


def _tenure_on_resolution(question: str, walk: list[dict], floor: float, *,
                          tree: str, table: str, conn=None) -> dict:
    """The earning half, fired ON the resolution event — never a clock (the event that
    already fires carries the write).

    Every EVIDENCING node (counted, at or above the floor) is offered to
    ``trees.corroborate`` — which appends a cross-question attestation, refuses the
    birth-question echo as a touch, and writes standing='earned' at
    PROMOTION_THRESHOLD, all through db_domain's owner-gated update face.

    Returns ``{"corroborated": [node_ids], "promoted": [node_ids]}`` for the verdict.
    """
    corroborated, promoted = [], []
    for node in walk:
        if not node.get("evidence") or node["similarity"] < floor:
            continue
        r = corroborate(node["node_id"], question, promote_at=PROMOTION_THRESHOLD,
                        tree=tree, table=table, conn=conn)
        if r["corroborated"]:
            corroborated.append(node["node_id"])
        if r["promoted"]:
            promoted.append(node["node_id"])
    return {"corroborated": corroborated, "promoted": promoted}


def resolve_query(question: str, *, resolve, tree: str = "commons", k: int = 5,
                  floor: float = RESOLUTION_FLOOR, max_backfills: int = MAX_BACKFILLS,
                  table: str = NODES, conn=None, dev: LibrarianDevice | None = None,
                  session_id: str | None = None) -> dict:
    """One crossing of the core loop. Returns a VERDICT, never a guess::

        {"verdict": "RESOLVED" | "UNRESOLVED",
         "reason":  None | "learned" | "no_progress" | "exhausted",
         "nodes":   the walk (each node labeled "evidence": True|False),
         "best":    top cosine AMONG EVIDENCE or None, "floor": floor,   # Law 3
         "backfills": rounds run, "deposited": fresh node_ids,
         "refused_at_door": findings for backfill nodes the deposit door turned back,
         "tenure": {"corroborated": [...], "promoted": [...]} on RESOLVED}

    The answer comes from STRUCTURE — and since 2026-08-09 (ticket the-tenure-loop),
    from structure THIS CROSSING DID NOT MINT: the floor test reads only evidence-labeled
    nodes, so a first touch that only backfilled returns the honest ``"learned"`` (fresh
    nodes landed for the future; resolution belongs to a LATER crossing). ``"no_progress"``
    and ``"exhausted"`` keep their meanings when nothing landed at all. On RESOLVED, the
    evidencing nodes are corroborated (and promoted at threshold) in the same event.
    """
    if not callable(resolve):
        raise BackfillRefused(
            "resolve_query: no resolve seam injected — both verbs (embed, generate) come "
            "through inference_domain.resolve or not at all (sole path)."
        )
    if not isinstance(question, str) or not question.strip():
        raise BackfillRefused(f"resolve_query: question must be a non-empty string, got {question!r}")

    dev = dev or LibrarianDevice()
    embed = lambda text: resolve({"kind": "embed", "prompt": text})["answer"]["vector"]

    now = datetime.now(timezone.utc)
    backfills, deposited, refused = 0, [], []
    qv = embed(question)
    walk = dev.nearest(qv, k=k, tree=tree, table=table, conn=conn)
    _label_evidence(walk, deposited, now)
    best = _evidence_best(walk)

    while best is None or best < floor:
        if backfills >= max_backfills:
            reason = "learned" if deposited else "exhausted"
            return _verdict(dev, question, "UNRESOLVED", reason, walk, best, floor,
                            backfills, deposited, refused, tree)
        state = tree_state(tree, table=table, conn=conn)
        drafted = resolve({"kind": "generate",
                           "prompt": backfill_prompt(question, state, walk)})
        nodes = parse_backfill(drafted["answer"]["text"])
        backfills += 1

        fresh = 0
        for content in nodes:
            provenance = {"source": "llm-backfill", "question": question,
                          "graph_state": state["digest"]}
            if session_id:
                provenance["origin_session"] = session_id
            try:
                r = dev.deposit(content, embed(content), provenance,
                                tree=tree, table=table, conn=conn)
            except DepositRefused as e:
                # The door's judgment outranks the backfill's enthusiasm — the refusal is
                # carried in the verdict, complete, and the loop moves on (Law 7).
                refused.append({"content": content, "refusal": str(e)})
                continue
            if not r["duplicate"]:
                fresh += 1
                deposited.append(r["node_id"])
        if fresh == 0:
            # THE PROGRESS GATE — the livelock's second layer. Nothing landed, so the same
            # graph would fail the same way; spinning would book the trap as savings. If
            # EARLIER rounds landed nodes, the crossing still learned — say so.
            reason = "learned" if deposited else "no_progress"
            return _verdict(dev, question, "UNRESOLVED", reason, walk, best, floor,
                            backfills, deposited, refused, tree)

        # THE RESUBMIT, re-scoped 2026-08-09 (ticket the-tenure-loop): the 2026-07-27
        # clause "validates by resubmitting the same request" still drives this walk, but
        # a same-crossing mint no longer counts as the proof — the evidence label excludes
        # this crossing's own deposits, so validation COMPLETES at a LATER crossing, when
        # a different question (or this one, re-asked against standing structure) walks
        # here honestly. Same-crossing corroboration is the measured defect, not the proof.
        walk = dev.nearest(qv, k=k, tree=tree, table=table, conn=conn)
        _label_evidence(walk, deposited, now)
        best = _evidence_best(walk)

    tenure = _tenure_on_resolution(question, walk, floor, tree=tree, table=table, conn=conn)
    return _verdict(dev, question, "RESOLVED", None, walk, best, floor,
                    backfills, deposited, refused, tree, tenure=tenure)


def _promotion_callbacks(walk: list[dict], tenure: dict | None) -> list[dict]:
    """Callbacks for promoted nodes whose depositing session should be notified.

    Rides the resolution event — no clock, no poll. Only nodes with an
    ``origin_session`` in their provenance produce a callback; nodes deposited
    before session tracking was added, or deposited without a session context,
    are silently skipped."""
    if not tenure or not tenure.get("promoted"):
        return []
    promoted_ids = set(tenure["promoted"])
    callbacks = []
    for node in walk:
        if node["node_id"] not in promoted_ids:
            continue
        origin = (node.get("provenance") or {}).get("origin_session")
        if origin:
            callbacks.append({
                "node_id": node["node_id"],
                "origin_session": origin,
                "content": node["content"],
                "event": "promoted",
            })
    return callbacks


def _receipts(walk: list[dict], tenure: dict | None) -> list[dict]:
    """The citation back: for each node this crossing ACTED ON, the question it was born
    from — so a turn can name the earlier question it revises (Akien's "cite back to
    changes", ticket revision-with-receipts).

    Three ways a node earns a receipt, strongest first: it was ``refuted`` (someone
    retired it and this walk still surfaced it), it was ``promoted`` to earned tenure by
    this crossing, or it was ``corroborated``. A node in more than one of those is
    reported once, under the strongest.

    Arithmetic over the walk already in hand: no new query, no generate, no clock. A node
    whose birth question is unrecorded comes back ``"question": None`` rather than a
    manufactured one — 19 of the 78 live rows carry no ``provenance.question`` (library
    folds and seeds), and inventing a plausible question for them would be minted
    attribution wearing a bibliography. The absence is reported; it is never filled.
    """
    by_id = {n["node_id"]: n for n in walk}
    why: dict[str, str] = {}
    for nid in (tenure or {}).get("corroborated", []):
        why[nid] = "corroborated"
    for nid in (tenure or {}).get("promoted", []):
        why[nid] = "promoted"
    for node in walk:
        if node.get("standing") == "refuted":
            why[node["node_id"]] = "refuted"

    out = []
    for nid, reason in why.items():
        prov = (by_id.get(nid, {}).get("provenance") or {})
        q = prov.get("question")
        out.append({"node_id": nid, "why": reason,
                    "question": q if isinstance(q, str) and q.strip() else None,
                    "source": prov.get("source")})
    return out


def _verdict(dev, question, verdict, reason, walk, best, floor,
             backfills, deposited, refused, tree, tenure=None) -> dict:
    # GATE CONTACT: one crossing of the core loop, RESOLVED and UNRESOLVED alike — an
    # unresolved question is the loop working, not an anomaly. Thin: the pointer is the
    # question's digest; the values are what a reader wants without the full verdict.
    dev.emit("resolve", pointer=_question_digest(question),
             values={"verdict": verdict, "reason": reason, "tree": tree,
                     "best": best, "floor": floor, "backfills": backfills,
                     "fresh_nodes": len(deposited),
                     "promoted": len(tenure["promoted"]) if tenure else 0})
    out = {"verdict": verdict, "reason": reason, "nodes": walk, "best": best,
           "floor": floor, "backfills": backfills, "deposited": deposited,
           "refused_at_door": refused, "question": question,
           "receipts": _receipts(walk, tenure)}
    if tenure is not None:
        out["tenure"] = tenure
    callbacks = _promotion_callbacks(walk, tenure)
    if callbacks:
        out["callbacks"] = callbacks
    return out

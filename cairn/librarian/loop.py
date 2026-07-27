"""librarian/loop.py — the core resolve-or-generate loop: always the graph first.

Akien's ruling, 2026-07-27, verbatim: "The librarian ALWAYS reaches for the graph trees,
and if the graph tree can't, the LLM is used to backfill it until it can." And the
load-bearing clause: "escalate on graph failure to a node depositing call THAT VALIDATES
BY RESUBMITTING THE SAME REQUEST." The host is never in the answer path — it supplies
NODES on a miss, the graph folds them in, and the proof the backfill worked is that the
ORIGINAL request now resolves through structure. Law 1 as a runtime mechanism.

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

from cairn.librarian.trees import (
    NODES, DepositRefused, LibrarianDevice, tree_state,
)

# The floor a walk must clear to count as resolved — a labeled guess, not a settled law
# (seeded by the first live walk, n=1; see the module note). Returned in every verdict.
RESOLUTION_FLOOR = 0.65

# Rounds of backfill before the loop reports exhaustion. Small on purpose: each round is
# a real host call, and a question three rounds cannot ground is a finding, not a retry.
MAX_BACKFILLS = 3


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


def resolve_query(question: str, *, resolve, tree: str = "commons", k: int = 5,
                  floor: float = RESOLUTION_FLOOR, max_backfills: int = MAX_BACKFILLS,
                  table: str = NODES, conn=None, dev: LibrarianDevice | None = None) -> dict:
    """One crossing of the core loop. Returns a VERDICT, never a guess::

        {"verdict": "RESOLVED" | "UNRESOLVED",
         "reason":  None | "no_progress" | "exhausted",
         "nodes":   the walk that answered (or the best failing walk),
         "best":    top cosine or None, "floor": floor,       # threshold visible (Law 3)
         "backfills": rounds run, "deposited": fresh node_ids,
         "refused_at_door": findings for backfill nodes the deposit door turned back}

    The answer comes from STRUCTURE: on RESOLVED, ``nodes`` is the graph's walk — the
    generate answer is never returned, only folded in. An UNRESOLVED verdict is an honest
    measured outcome (the model could not extend the graph, or the rounds ran out), loud
    in its breadcrumb and complete in its findings — not an exception, not a retry-forever.
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

    qv = embed(question)
    walk = dev.nearest(qv, k=k, tree=tree, table=table, conn=conn)
    best = walk[0]["similarity"] if walk else None
    backfills, deposited, refused = 0, [], []

    while best is None or best < floor:
        if backfills >= max_backfills:
            return _verdict(dev, question, "UNRESOLVED", "exhausted", walk, best, floor,
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
            # graph would fail the same way; spinning would book the trap as savings.
            return _verdict(dev, question, "UNRESOLVED", "no_progress", walk, best, floor,
                            backfills, deposited, refused, tree)

        # VALIDATES BY RESUBMITTING THE SAME REQUEST — the load-bearing clause: the proof
        # the backfill worked is that the ORIGINAL request now resolves through the graph.
        walk = dev.nearest(qv, k=k, tree=tree, table=table, conn=conn)
        best = walk[0]["similarity"] if walk else None

    return _verdict(dev, question, "RESOLVED", None, walk, best, floor,
                    backfills, deposited, refused, tree)


def _verdict(dev, question, verdict, reason, walk, best, floor,
             backfills, deposited, refused, tree) -> dict:
    # GATE CONTACT: one crossing of the core loop, RESOLVED and UNRESOLVED alike — an
    # unresolved question is the loop working, not an anomaly. Thin: the pointer is the
    # question's digest; the values are what a reader wants without the full verdict.
    dev.emit("resolve", pointer=_question_digest(question),
             values={"verdict": verdict, "reason": reason, "tree": tree,
                     "best": best, "floor": floor, "backfills": backfills,
                     "fresh_nodes": len(deposited)})
    return {"verdict": verdict, "reason": reason, "nodes": walk, "best": best,
            "floor": floor, "backfills": backfills, "deposited": deposited,
            "refused_at_door": refused, "question": question}

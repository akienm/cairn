"""librarian/trees.py — the graph-tree store: the librarian's spine, db_domain's first tenant.

Akien's founding facts (settled 2026-07-22, notes/held-librarian.json): "the embedding IS
the path through the graph trees" — edges are DERIVED from vector proximity, never stored
(O(n) vectors, and the paths fall out); the librarian OWNS the graph (Law 6), so every
write passes db_domain's owner-gate under the name ``librarian``. The face this feeds
(named the current goal 2026-07-27): a chatbot, learning always, summarizing when asked —
a query resolves by traversing structure, and the resolver is spent only on the novel.

THE CONTRACT
  - A node is content + vector + PROVENANCE + standing. The deposit door refuses a node
    nobody can trace: fabricated attribution at the extractor was a draft problem; here it
    would be a permanent resident. Provenance names at least its ``source``.
  - Every node is born ``standing = "hypothesis"`` (Law 3): a node the LLM provided — or
    anyone else — has not yet earned tenure. The tenure loop is a filed edge; until it
    exists nodes honestly stay hypotheses, and the charter says so.
  - Edges are NEVER stored. ``nearest`` walks a tree by cosine proximity to a query
    vector; ``neighbors`` derives a node's edges the same way. No edge table can exist —
    the proof pins that nothing named like one is ever registered.
  - Dimensions are physics, not luck: the first deposit into a tree sets its dimension;
    a mismatched deposit or query is REFUSED loudly (a 4-dim query against 768-dim nodes
    is a wrong question, and answering it would be a silent wrong answer).
  - A duplicate deposit (same tree, same content) writes NOTHING and says so — the
    cheapest deposit is the one never made (Law 1, the cache's shape). Its dropped
    provenance is a filed edge: corroboration becomes evidence when the tenure loop lands.

This module is import-pure toward the network: vectors arrive as DATA (the embed call is
the caller's, through inference_domain — live wiring in ``live.py``, never here), and the
database is reached only through db_domain (the sole path; Law 4). The proof pins both
by AST allowlist.
"""

from __future__ import annotations

import hashlib
import math

from cairn.base.device import BaseDevice
from cairn.db_domain import store

# The librarian's one table (a `tree` column partitions the forest). The filed edge about
# "other owners' trees" landed 2026-07-28 (ticket chart-tree), and simpler than a grant:
# every function takes an ``owner`` (default: the librarian), so a second tenant — chart's
# nexi first — reaches ITS OWN table through the same tools and db_domain's same gate
# (Law 6 held per-tenant; the ratified unification: one tool set, many owners).
NODES = "librarian_nodes"
OWNER = "librarian"

# The floor under content: a node distilled from near-nothing is invention wearing a
# vector (the extractor's _MIN_SOURCE_CHARS lesson, one layer down).
_MIN_CONTENT_CHARS = 8

_COLUMNS = {
    "node_id": "text PRIMARY KEY",
    "tree": "text NOT NULL",
    "content": "text NOT NULL",
    "vector": "jsonb NOT NULL",
    "provenance": "jsonb NOT NULL",
    "standing": "text NOT NULL",
    "created": "timestamptz NOT NULL DEFAULT now()",
}


class DepositRefused(RuntimeError):
    """A deposit the door cannot honestly accept — refused loudly, nothing landed (Law 7)."""


class WalkRefused(RuntimeError):
    """A walk that would answer a different question than the one asked — refused, not guessed."""


def node_id_for(tree: str, content: str) -> str:
    """Deterministic identity: the same content in the same tree IS the same node."""
    return hashlib.sha256(f"{tree}\n{content}".encode("utf-8")).hexdigest()[:16]


def _norm(s: str) -> str:
    return " ".join(s.split())


def _check_vector(vector, *, who: str) -> list[float]:
    """A vector is a non-empty list of finite numbers with direction (nonzero magnitude).

    A zero vector has no direction, so proximity to it is undefined — cosine would divide
    by zero or, patched, silently rank everything equal. Refused, both doors."""
    if not isinstance(vector, (list, tuple)) or not vector:
        raise (DepositRefused if who == "deposit" else WalkRefused)(
            f"{who}: vector must be a non-empty list of numbers, got "
            f"{type(vector).__name__}{'' if vector else ' (empty)'}"
        )
    try:
        v = [float(x) for x in vector]
    except (TypeError, ValueError):
        raise (DepositRefused if who == "deposit" else WalkRefused)(
            f"{who}: vector carries a non-numeric entry — refusing to coerce"
        ) from None
    if not all(math.isfinite(x) for x in v):
        raise (DepositRefused if who == "deposit" else WalkRefused)(
            f"{who}: vector carries a non-finite entry (nan/inf) — that is not a direction"
        )
    if not any(x != 0.0 for x in v):
        raise (DepositRefused if who == "deposit" else WalkRefused)(
            f"{who}: zero vector — no direction, so proximity is undefined; refusing to "
            "rank everything as equally near"
        )
    return v


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity — the derived edge's weight. Callers guarantee nonzero vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def ensure_trees(*, table: str = NODES, owner: str = OWNER, conn=None) -> None:
    """The table, owner-gated into existence. Idempotent; ownership is recorded at birth."""
    store.create_owned_table(table, owner, _COLUMNS, conn=conn)


def _tree_rows(tree: str, *, table: str, conn) -> list[dict]:
    return store.read(table, where="tree = %s", params=(tree,), conn=conn)


def deposit(content: str, vector, provenance: dict, *,
            tree: str = "commons", table: str = NODES, owner: str = OWNER,
            conn=None) -> dict:
    """The deposit door: one node in, judged before it lands.

    Returns ``{"node_id", "duplicate": bool, "dim"}``. A duplicate (same tree + content)
    writes nothing — the standing node's id comes back with ``duplicate: True``.
    Refusals (all BEFORE any write, all first-pass complete):
      - content under the floor (a node from near-nothing is invention),
      - a vector without direction (empty / non-numeric / non-finite / zero),
      - provenance that is not a dict naming a non-empty ``source`` (an untraceable node
        is fabricated attribution taking up permanent residence),
      - a dimension that disagrees with the tree's (the first deposit set it).
    """
    if not isinstance(content, str) or len(_norm(content)) < _MIN_CONTENT_CHARS:
        raise DepositRefused(
            f"deposit: content is "
            f"{len(_norm(content)) if isinstance(content, str) else 'not a string'} "
            f"normalized chars — floor is {_MIN_CONTENT_CHARS}. A node distilled from "
            "near-nothing is invention; nothing landed."
        )
    v = _check_vector(vector, who="deposit")
    if not isinstance(provenance, dict) or not str(provenance.get("source", "")).strip():
        raise DepositRefused(
            f"deposit: provenance must be a dict naming a non-empty 'source', got "
            f"{provenance!r}. A node nobody can trace is fabricated attribution as a "
            "permanent resident; nothing landed."
        )

    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        nid = node_id_for(tree, content)
        existing = store.read(table, where="node_id = %s", params=(nid,), conn=own)
        if existing:
            # Nothing written: the cheapest deposit is the one never made (Law 1). The
            # incoming provenance is dropped for now — filed edge (b): corroboration
            # becomes a provenance APPEND when the tenure loop lands.
            return {"node_id": nid, "duplicate": True, "dim": len(existing[0]["vector"])}

        siblings = _tree_rows(tree, table=table, conn=own)
        if siblings:
            tree_dim = len(siblings[0]["vector"])
            if len(v) != tree_dim:
                raise DepositRefused(
                    f"deposit: vector dim {len(v)} vs tree {tree!r} dim {tree_dim} — a "
                    "mixed-dimension tree cannot be walked; refusing (the first deposit "
                    "set the tree's dimension)."
                )
        store.write(table, owner, {
            "node_id": nid,
            "tree": tree,
            "content": content,
            "vector": v,
            "provenance": provenance,
            "standing": "hypothesis",   # born one, stays one until tenure is a measurement
        }, conn=own)
        return {"node_id": nid, "duplicate": False, "dim": len(v)}
    finally:
        if conn is None:
            own.close()


def tree_state(tree: str, *, table: str = NODES, owner: str = OWNER, conn=None) -> dict:
    """The tree's fingerprint: ``{"digest", "nodes"}`` — same members, same digest.

    This is what makes 'same request, changed graph' DISTINGUISHABLE: the core loop folds
    this digest into the backfill key, so a resubmit against a changed tree is a genuine
    cache MISS while a resubmit against an unchanged tree is honestly the same question
    (the livelock fix, filed 2026-07-27 in held-librarian's ruling section, as physics).
    An empty tree fingerprints as ``"empty"`` — a nameable state, not an error.
    """
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        ids = sorted(r["node_id"] for r in _tree_rows(tree, table=table, conn=own))
        digest = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()[:16] if ids else "empty"
        return {"digest": digest, "nodes": len(ids)}
    finally:
        if conn is None:
            own.close()


def nearest(vector, *, k: int = 5, tree: str = "commons",
            table: str = NODES, owner: str = OWNER, conn=None) -> list[dict]:
    """The walk: the k nodes of ``tree`` nearest the query vector, by cosine.

    THE derived edge — nothing is looked up, proximity is computed (the embedding is the
    path). An empty tree returns an honest ``[]``. A dimension mismatch is refused.
    """
    if not isinstance(k, int) or k < 1:
        raise WalkRefused(f"nearest: k must be a positive int, got {k!r}")
    v = _check_vector(vector, who="nearest")
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        rows = _tree_rows(tree, table=table, conn=own)
        if not rows:
            return []
        tree_dim = len(rows[0]["vector"])
        if len(v) != tree_dim:
            raise WalkRefused(
                f"nearest: query dim {len(v)} vs tree {tree!r} dim {tree_dim} — "
                "answering across dimensions would be a silent wrong answer; refused."
            )
        ranked = sorted(
            ({"node_id": r["node_id"], "content": r["content"],
              "similarity": cosine(v, [float(x) for x in r["vector"]]),
              "provenance": r["provenance"], "standing": r["standing"]}
             for r in rows),
            key=lambda n: n["similarity"], reverse=True)
        return ranked[:k]
    finally:
        if conn is None:
            own.close()


def neighbors(node_id: str, *, k: int = 5, tree: str = "commons",
              table: str = NODES, owner: str = OWNER, conn=None) -> list[dict]:
    """A node's derived edges: its k nearest siblings, itself excluded.

    Asking for the neighbors of a node that is not there is refused loudly — a ghost has
    no neighborhood, and an empty answer would read as 'isolated', a different fact.
    """
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        home = store.read(table, where="node_id = %s AND tree = %s",
                          params=(node_id, tree), conn=own)
        if not home:
            raise WalkRefused(
                f"neighbors: node {node_id!r} is not in tree {tree!r} — a ghost has no "
                "neighborhood (an empty [] would claim 'isolated', which is a different fact)."
            )
        ranked = nearest([float(x) for x in home[0]["vector"]], k=k + 1, tree=tree,
                         table=table, conn=own)
        return [n for n in ranked if n["node_id"] != node_id][:k]
    finally:
        if conn is None:
            own.close()


# ── the device ───────────────────────────────────────────────────────────────


class LibrarianDevice(BaseDevice):
    """The librarian (carries CP1-CP6; reports the Form v0 #2 surface).

    v0 surface = the graph-tree spine: ``deposit`` (a write-crossing — breadcrumbed,
    DEPOSITED and DUPLICATE alike) and the walks ``nearest`` / ``neighbors`` (reads —
    silent, per the extractor's reads-silent rule). The core resolve-or-generate loop,
    the summarizer, and the chat face land on this same device as later stones.
    """

    def __init__(self) -> None:
        super().__init__()
        self._deposits = 0
        self._verdicts = {"DEPOSITED": 0, "DUPLICATE": 0}
        self._last_node: str | None = None
        self._chat = None        # the conversational face — attached by the shim at wake

    @property
    def device_id(self) -> str:
        return "librarian"

    def deposit(self, content: str, vector, provenance: dict, *,
                tree: str = "commons", table: str = NODES, conn=None) -> dict:
        """One deposit crossing — judged at the door, breadcrumbed after it lands."""
        result = deposit(content, vector, provenance, tree=tree, table=table, conn=conn)
        verdict = "DUPLICATE" if result["duplicate"] else "DEPOSITED"
        self._deposits += 1
        self._verdicts[verdict] += 1
        self._last_node = result["node_id"]
        # GATE CONTACT: a node crossed the deposit door (or was turned back as already
        # standing — that verdict breadcrumbs too; a write avoided is the cache's shape
        # and worth a trace). Thin: pointer is the node, values the verdict and where.
        self.emit("deposit", pointer=result["node_id"],
                  values={"verdict": verdict, "tree": tree, "dim": result["dim"]})
        return result

    def nearest(self, vector, *, k: int = 5, tree: str = "commons",
                table: str = NODES, conn=None) -> list[dict]:
        return nearest(vector, k=k, tree=tree, table=table, conn=conn)

    def neighbors(self, node_id: str, *, k: int = 5, tree: str = "commons",
                  table: str = NODES, conn=None) -> list[dict]:
        return neighbors(node_id, k=k, tree=tree, table=table, conn=conn)

    # --- the chat window: a surface the base shim class understands ---------

    def attach_chat(self, session) -> None:
        """Wire the conversational face (a ChatSession). Live composition happens in
        the SHIM at wake time — this device stays import-pure toward the host. The
        chat window is a declared PANE (below): the librarian owns a page the ONE web
        server displays through the standard shim machinery — never a server, a
        route, or a port of its own."""
        self._chat = session

    def declared_panes(self) -> list[dict]:
        """The chat window, offered as a pane. Unattached (nobody woke the face) it
        is honestly ABSENT-with-reason on the page, not a missing surface."""
        return [{"kind": "chat", "label": "Chat",
                 "handler": None if self._chat is None else self._chat.page}]

    def receive(self, envelope: dict) -> dict:
        """Incoming mail (web_server → shim → here: the designed path, in-process
        v0). Channel ``chat`` carries one utterance to the face. Anything this
        device cannot honestly process refuses loudly — mail never vanishes
        (Law 7)."""
        channel = envelope.get("channel")
        if channel != "chat":
            raise ValueError(
                f"librarian: no handler for channel {channel!r} — this device "
                "receives 'chat' (one utterance per envelope)")
        if self._chat is None:
            raise RuntimeError(
                "librarian: a chat envelope arrived but no face is attached — the "
                "shim wires the ChatSession at wake; an unwired face refuses, it "
                "does not pretend")
        return self._chat.turn(str((envelope.get("body") or {}).get("utterance", "")))

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The librarian: owner of the graph trees (db_domain's first tenant). "
            "v0 is the spine — a provenance-gated deposit door and proximity walks whose "
            "edges are derived from the vectors, never stored. The face it feeds: a "
            "chatbot, learning always, summarizing when asked.",
            "why": "A query answered from structure costs a walk; only the novel costs "
            "inference (Law 1 as runtime). The embedding IS the path — so the store "
            "holds O(n) vectors and the paths fall out. Every node is traceable at "
            "birth: an untraceable node would be fabricated attribution in permanent "
            "residence.",
        }

    def state(self) -> dict:
        return {
            "deposits": self._deposits,
            "verdicts": dict(self._verdicts),
            "last_node_id": self._last_node,
        }

    def settings(self) -> dict:
        return {
            "table": NODES,
            "owner": OWNER,
            "min_content_chars": _MIN_CONTENT_CHARS,
            "standing_at_birth": "hypothesis (Law 3; the tenure loop is a filed edge)",
            "edges": "derived from cosine proximity at walk time — no edge table exists",
            "seam": "vectors arrive as data; the embed call is the caller's, through "
                    "inference_domain (live wiring in live.py, never here)",
        }

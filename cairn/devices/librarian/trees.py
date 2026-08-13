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
    anyone else — has not yet earned tenure. Tenure is a MEASUREMENT, and the three
    standings are the whole vocabulary: ``hypothesis`` at birth, ``earned`` when distinct
    crossings corroborate it (``corroborate``, 2026-08-09, ticket the-tenure-loop), and
    ``refuted`` when a stated correction retires it (``refute``, 2026-08-10, ticket
    revision-with-receipts). A retired node is invalidated, never deleted.
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
from datetime import datetime, timezone

from cairn.tools.base.device import BaseDevice
from cairn.devices.db_domain import store

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


class RefutationRefused(RuntimeError):
    """A retirement the door cannot honestly accept — every lack named in ONE pass, nothing landed.

    One pass rather than one-per-run is the point: a caller that fixes a lack and is
    refused for the next one learns the door's shape by attrition, and a human typing a
    correction gets told the whole truth once (Law 7 at a diagnostic surface)."""


# Who may retire an EARNED node. The borrow is cairn/machines/ruling's supersession rule —
# "an unconfirmed reading cannot retire a confirmed act; that would be my guess outvoting
# his signature" — cited in the charter's `entry`, never imported (charter falsifier 7).
# Read as an ALLOWLIST, not a denylist: an unrecognized source is refused against earned
# knowledge, because red is the default and an unknown hand is not a known-safe one (CP6).
_REFUTER_AUTHORITIES = frozenset({"correction"})


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
    grows the table by nothing — the standing node's id comes back with
    ``duplicate: True`` and ``provenance_appended: True``: since 2026-08-09 (ticket
    the-tenure-loop) the incoming provenance lands as an attestation on the standing
    row's ``provenance.attestations`` instead of being dropped.
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
            # Edge (b)'s recorded switch, flipped 2026-08-09 (ticket the-tenure-loop):
            # a duplicate still writes no NEW ROW — Law 1 stops redundant STRUCTURE —
            # but its provenance now lands as an ATTESTATION on the standing row.
            # Redundant arrival is evidence of independent reach, and the tenure loop
            # counts it; dropping it was the filed debt.
            prior = existing[0]["provenance"] or {}
            attests = list(prior.get("attestations") or [])
            attests.append({**provenance, "at": datetime.now(timezone.utc).isoformat()})
            merged = {**prior, "attestations": attests}
            store.update(table, owner, {"provenance": merged},
                         where="node_id = %s", params=(nid,), conn=own)
            return {"node_id": nid, "duplicate": True, "dim": len(existing[0]["vector"]),
                    "provenance_appended": True}

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


def corroborate(node_id: str, question: str, *, promote_at: int,
                tree: str = "commons", table: str = NODES, owner: str = OWNER,
                conn=None) -> dict:
    """The earning write, fired by the librarian's resolution event (ticket
    the-tenure-loop) — never by a clock.

    Appends a corroboration attestation for ``question`` onto the standing node's
    provenance, UNLESS it is the node's birth question (a node cannot tenure on echoes
    of its own birth — that touch does not corroborate) or already attested (distinct
    questions are the count, not raw arrivals). Once distinct cross-question
    corroborations — resolution corroborations and duplicate-deposit attestations
    alike — reach ``promote_at``, standing turns ``'earned'`` in the same write. Both
    mutations ride db_domain's owner-gated update face; the promotion check runs even
    when nothing new appends, so a node that reached threshold between resolutions is
    not stranded at hypothesis.

    Returns ``{"corroborated": bool, "promoted": bool, "distinct": int}``.
    """
    own = conn or store.connect()
    try:
        rows = store.read(table, where="node_id = %s AND tree = %s",
                          params=(node_id, tree), conn=own)
        if not rows:
            raise DepositRefused(
                f"corroborate: no standing node {node_id!r} in tree {tree!r} — nothing to attest")
        row = rows[0]
        prov = dict(row["provenance"] or {})
        birth_q = prov.get("question")
        attests = list(prov.get("attestations") or [])
        distinct = {a.get("question") for a in attests
                    if a.get("question") and a.get("question") != birth_q}
        changes: dict = {}
        corroborated = False
        if question != birth_q and question not in distinct:
            attests.append({"source": "corroboration", "question": question,
                            "at": datetime.now(timezone.utc).isoformat()})
            distinct.add(question)
            changes["provenance"] = {**prov, "attestations": attests}
            corroborated = True
        promoted = False
        if len(distinct) >= promote_at and row["standing"] != "earned":
            changes["standing"] = "earned"
            promoted = True
        if changes:
            store.update(table, owner, changes, where="node_id = %s AND tree = %s",
                         params=(node_id, tree), conn=own)
        return {"corroborated": corroborated, "promoted": promoted, "distinct": len(distinct)}
    finally:
        if conn is None:
            own.close()


def _may_retire_earned(refuter: dict) -> bool:
    """Is this refuter allowed to outvote corroborated knowledge?

    Yes if it has EARNED tenure itself, or if its provenance names it an authority — today
    that means a stated correction, which is an INPUT from outside and therefore not the
    system's own guess. Law 9 forces this second arm: "no past artifact outranks him now",
    and a node in this tree is a past artifact. A gate keyed on standing ALONE would make
    Akien's correction unable to retire an earned node, since every node is born a
    hypothesis (the deposit door's contract) — the gate would then be protecting the
    corpus from its own author.
    """
    if refuter.get("standing") == "earned":
        return True
    source = str((refuter.get("provenance") or {}).get("source", "")).strip()
    return source in _REFUTER_AUTHORITIES


def refute(node_id: str, refuter_id: str, evidence: str, *,
           tree: str = "commons", table: str = NODES, owner: str = OWNER,
           minted_this_crossing=(), conn=None) -> dict:
    """The retirement door: a standing node marked WRONG, in one owner-gated act.

    The third write face beside ``deposit`` and ``corroborate``, and the fifth tenure
    behaviour (ticket revision-with-receipts). Invalidate, never delete: the row keeps its
    content, its vector and its birth provenance byte-for-byte, and gains
    ``standing = "refuted"`` plus one appended attestation
    ``{source: "refutation", refuter, evidence, at}``. What was believed and then found
    wrong is a record of truth, and a record of truth is permanent (Law 7) — a deleted node
    would leave every later reader unable to tell "never known" from "known and retired".

    Refutation is an INPUT, never a discovery. Nothing here looks for contradictions:
    cosine finds nodes that are ALIKE, and a statement and its negation are alike.

    Refusals — ALL named in one pass, ALL before any write:
      - evidence that is empty (a retirement nobody can read back is an unexplained hole),
      - a node id, either one, that does not stand in this tree,
      - self-refutation (a node arguing itself down is not evidence, it is a loop),
      - a doubled retirement (the second one would overwrite the first's receipt),
      - a refuter that is itself refuted (retired knowledge does not get to retire more),
      - THE STANDING GATE: a refuter that may not outvote an EARNED node — see
        ``_may_retire_earned``. This is the borrow's whole point, and the only thing
        between a hallucinated backfill and corroborated knowledge.
      - crossing honesty, unchanged from the tenure loop: a node minted DURING this
        crossing may not act as the refuter in it (pass the crossing's own mints as
        ``minted_this_crossing``). A loop that mints its own refuter has manufactured a
        revision the same way manufactured resolution was closed.

    Returns ``{"refuted", "node_id", "refuter", "was", "attestations"}`` — ``was`` is the
    standing being retired, so a caller can tell a hypothesis's retirement from an earned
    node's without a second read.
    """
    lacks: list[str] = []
    ev = evidence.strip() if isinstance(evidence, str) else ""
    if not ev:
        lacks.append(
            f"evidence is {'empty' if isinstance(evidence, str) else f'{type(evidence).__name__}, not a string'} "
            "— a retirement nobody can read back is an unexplained hole in the record"
        )

    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        seen: dict[str, dict] = {}
        for wanted in (node_id, refuter_id):
            if wanted in seen:
                continue
            found = store.read(table, where="node_id = %s AND tree = %s",
                               params=(wanted, tree), conn=own)
            if found:
                seen[wanted] = found[0]
        target = seen.get(node_id)
        refuter = seen.get(refuter_id)

        if target is None:
            lacks.append(f"no standing node {node_id!r} in tree {tree!r} — nothing to retire")
        if refuter is None:
            lacks.append(
                f"no standing node {refuter_id!r} in tree {tree!r} — the refuter must itself "
                "be in the record, or the retirement cites nothing"
            )
        if node_id == refuter_id:
            lacks.append(
                f"{node_id!r} would refute itself — a node arguing itself down is not "
                "evidence, and the receipt would cite the thing it retired"
            )
        if refuter_id in set(minted_this_crossing):
            lacks.append(
                f"crossing honesty: {refuter_id!r} was minted during this crossing, so it "
                "may not retire anything in it — that is a manufactured revision"
            )
        if target is not None and target["standing"] == "refuted":
            lacks.append(
                f"{node_id!r} is already refuted — a second retirement would overwrite the "
                "first one's receipt, and the first refuter is who the record owes"
            )
        if refuter is not None and refuter["standing"] == "refuted":
            lacks.append(
                f"the refuter {refuter_id!r} is itself refuted — retired knowledge does not "
                "get to retire more"
            )
        if (target is not None and refuter is not None
                and target["standing"] == "earned" and not _may_retire_earned(refuter)):
            lacks.append(
                f"the standing gate: {node_id!r} is EARNED (corroborated across distinct "
                f"crossings) and the refuter {refuter_id!r} is standing "
                f"{refuter['standing']!r} from source "
                f"{str((refuter['provenance'] or {}).get('source', ''))!r} — a guess does not "
                f"outvote a signature. Authorities: {sorted(_REFUTER_AUTHORITIES)}"
            )

        if lacks:
            raise RefutationRefused(
                "refute: " + "; ".join(lacks) + ". Nothing landed."
            )

        # ONE act, one owner moment (Law 6): the standing change and the receipt land
        # together, exactly as corroborate's promotion does. Two writes would invent a
        # window in which a node is retired with no reason attached to it.
        prov = dict(target["provenance"] or {})
        attests = list(prov.get("attestations") or [])
        attests.append({"source": "refutation", "refuter": refuter_id, "evidence": ev,
                        "at": datetime.now(timezone.utc).isoformat()})
        store.update(table, owner,
                     {"standing": "refuted", "provenance": {**prov, "attestations": attests}},
                     where="node_id = %s AND tree = %s", params=(node_id, tree), conn=own)
        return {"refuted": True, "node_id": node_id, "refuter": refuter_id,
                "was": target["standing"], "attestations": len(attests)}
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
              "provenance": r["provenance"], "standing": r["standing"],
              # created rides the walk so a READER can weigh age (the librarian's lazy
              # decay does, in its own path); the RANKING here stays raw cosine only.
              "created": r["created"]}
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

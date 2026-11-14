"""librarian/trees.py — the graph-tree store: the librarian's spine, db_domain's first tenant.

The memory schema (outline 4.3.1.5.1.6, Akien Q#108 2026-11-14; ticket 06db586bedfd). Every
reference is ONE 64-bit address: a 16-bit table tag over a 48-bit row (``cairn.tools.node_address``).
A row id is a direct fetch, never a search (Q#104: "row ids are fastest").

  - **cairn_mem_nodes**: what is remembered, tree-free — the one long list. row, gen, state
    (VOID | NOTCACHED | DATA), kind, payload (inline when small), blob (a blob address, when
    large), meta (flexible json: provenance, standing; confidence when scored), out_list and
    in_list (list addresses), seq (the sync's cursor). A slot is reserved from the home box's
    librarian before the write (4.3.1.5.1.1); a write past this box's end lays the rows between
    as NOTCACHED; a NOTCACHED read is fed from the master (4.3.1.5.1.4).
  - **cairn_mem_lists**: row, gen, state, owner, items bigint[] (addresses of anything), weights
    real[] (optional, parallel), next (the next chunk's address when a list outgrows a chunk).
  - **cairn_mem_links**: row, gen, state, a, b, weight, traversals — one row per link, its address
    held in a's out_list and b's in_list (bidirectional, one home for the weight).
  - **cairn_mem_blobs**: row, gen, state, kind, bytes. The storage layer is blob rows and nothing
    file-based (Q#111: locators vs content is the storing part's call, not this one's).
  - **cairn_mem_embeddings**: renderings as coordinates, keyed by node address.
  - **cairn_mem_tags**: the leaf tables' tags, handed out by the home librarian from 0x0100 (the
    core four live in node_address/tags.json). A leaf's address is its table's tag over its row.
  - **per-tree leaf tables**: how a node is found. leaf_id + row + node_id (the node's address)
    + embedding_id (or key, for a keyed leaf). The node's in_list holds the leaf's address back.

gen: a reference is (address, gen); reading a reused row through an older Ref raises Gone, never
the new tenant's data. void walks in_list and out_list, unhooks itself from every link's other
end and every leaf that held it, clears its data and bumps gen — no search.

THE CONTRACT
  - A node is content + PROVENANCE + standing — no tree, no vector (those belong to
    embeddings and leaves). The deposit door refuses a node nobody can trace.
  - Every node is born ``standing = "hypothesis"`` (Law 3). Tenure is a MEASUREMENT.
  - confidence is absent until something scores it; an absent one reads "unscored".
  - Similarity lives inside a tree (Q#110): ``nearest`` walks a leaf table's embeddings.
  - Dimensions are physics: the first embedding deposited sets the tree's dimension.
  - A duplicate deposit (same content, ANY tree) writes no new node row — the same claim
    IS the same node however many trees index it (§4.3, constraint 4). Deposit asks
    "is this content already held?" through ONE seam, ``already_held``, which answers from a
    keyed content index (content hash -> node address), never a node search (Q#109, answered
    2026-11-14: "we're going to save things we find aren't already there").

This module is import-pure toward the network: vectors arrive as DATA, the database is
reached only through db_domain (the sole path; Law 4). The proof pins both by AST allowlist.
"""

from __future__ import annotations

import hashlib
import math
import os
import platform
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from cairn.devices.db_domain.tools.client import store
from cairn.tools.node_address import node_address as A

NODES_TABLE = "cairn_mem_nodes"
LISTS_TABLE = "cairn_mem_lists"
LINKS_TABLE = "cairn_mem_links"
BLOBS_TABLE = "cairn_mem_blobs"
TAGS_TABLE = "cairn_mem_tags"
EMBEDDINGS_TABLE = "cairn_mem_embeddings"
# The keyed index tree the dedup seam answers from (content hash -> node address).
CONTENT_INDEX = "cairn_mem_content_index"
# A row's three states (outline 4.3.1.5.1.3). Anything else is a bug, refused by the write
# door and by the table's CHECK.
VOID, NOTCACHED, DATA = "void", "notcached", "data"
STATES = (VOID, NOTCACHED, DATA)
NODES = "librarian_nodes"
# The floor a walk must clear to count as resolved — a labeled guess, not a settled law
# (seeded by the first live walk, n=1; see the module note). Returned in every verdict.
RESOLUTION_FLOOR = 0.65
OWNER = "librarian"
# The keyed tree the librarian plants its cross-domain question corpus in (outline 4.3.1.8,
# ticket 2248911aaf05). A device holding questions as the librarian's delegate (4.3.1.4) finds
# each by its id here, through find, and never imports the librarian's corpus module (RULE 1,
# outline 4.4.2).
CROSS_DOMAIN_QUESTIONS = "librarian_cross_domain_questions"

_MIN_CONTENT_CHARS = 8
# A payload past this many characters lands as a blob row the node points at (Q#108: "payload
# inline when small, blob when large"). A labeled guess, not a measured bound.
INLINE_MAX = 4096
# The items one list row holds before the list chains to a next chunk. A labeled guess.
LIST_CHUNK = 256
# Leaf tables' tags start here; below it are the core tables (node_address/tags.json).
LEAF_TAG_FLOOR = 0x0100

_SEQ = "bigint NOT NULL UNIQUE"

_NODE_COLUMNS = {
    "row": "bigint PRIMARY KEY",
    "gen": "integer NOT NULL DEFAULT 0",
    "state": "text NOT NULL",
    "kind": "text",
    "payload": "text",
    "blob": "bigint",
    "meta": "jsonb",
    "out_list": "bigint",
    "in_list": "bigint",
    "seq": _SEQ,
    "created": "timestamptz NOT NULL DEFAULT now()",
}

_LIST_COLUMNS = {
    "row": "bigint PRIMARY KEY",
    "gen": "integer NOT NULL DEFAULT 0",
    "state": "text NOT NULL",
    "owner": "bigint",
    "items": "bigint[]",
    "weights": "real[]",
    "next": "bigint",
    "seq": _SEQ,
}

_LINK_COLUMNS = {
    "row": "bigint PRIMARY KEY",
    "gen": "integer NOT NULL DEFAULT 0",
    "state": "text NOT NULL",
    "a": "bigint",
    "b": "bigint",
    "weight": "real",
    "traversals": "integer NOT NULL DEFAULT 0",
    "seq": _SEQ,
    "created": "timestamptz NOT NULL DEFAULT now()",
}

_BLOB_COLUMNS = {
    "row": "bigint PRIMARY KEY",
    "gen": "integer NOT NULL DEFAULT 0",
    "state": "text NOT NULL",
    "kind": "text",
    "bytes": "bytea",
    "seq": _SEQ,
}

_TAG_COLUMNS = {
    "name": "text PRIMARY KEY",
    "tag": "integer NOT NULL UNIQUE",
    "created": "timestamptz NOT NULL DEFAULT now()",
}

_STATE_CHECK = "state IN ('void', 'notcached', 'data')"

# The physics of each table's rows: a state off the three is refused; a data row holds its
# data, and a row that is not data holds none (a VOID row is cleared).
_CHECKS = {
    "nodes": {
        "state": _STATE_CHECK,
        "data": "(state = 'data') = ((payload IS NOT NULL OR blob IS NOT NULL) "
                "AND meta IS NOT NULL AND kind IS NOT NULL)",
        "cleared": "state = 'data' OR (payload IS NULL AND blob IS NULL AND meta IS NULL "
                   "AND out_list IS NULL AND in_list IS NULL)",
    },
    "lists": {
        "state": _STATE_CHECK,
        "data": "(state = 'data') = (items IS NOT NULL)",
        "weights": "weights IS NULL OR cardinality(weights) = cardinality(items)",
    },
    "links": {
        "state": _STATE_CHECK,
        "data": "(state = 'data') = (a IS NOT NULL AND b IS NOT NULL AND weight IS NOT NULL)",
    },
    "blobs": {
        "state": _STATE_CHECK,
        "data": "(state = 'data') = (kind IS NOT NULL AND bytes IS NOT NULL)",
    },
}

_CONTENT_INDEX_COLUMNS = {
    "key": "text PRIMARY KEY",
    "node": "bigint NOT NULL",
}

_EMBEDDING_COLUMNS = {
    "embedding_id": "text PRIMARY KEY",
    "node_id": "bigint NOT NULL",
    "vector": "jsonb NOT NULL",
    "render_method": "text NOT NULL",
}

_LEAF_COLUMNS = {
    "leaf_id": "text PRIMARY KEY",
    "row": "bigint UNIQUE",
    "node_id": "text NOT NULL",
    "embedding_id": "text NOT NULL",
}

# The keyed leaf (ticket e62f40f35f59, outline 4.3.1.6, Akien 2026-11-05): "Not every node gets
# one ... A node without an embedding is found by its key (eg an exact request)." Its shape is
# declared when the table is made, and recognised afterwards from the table's own columns.
_KEYED_LEAF_COLUMNS = {
    "leaf_id": "text PRIMARY KEY",
    "row": "bigint UNIQUE",
    "key": "text NOT NULL",
    "node_id": "text NOT NULL",
    "meta": "jsonb NOT NULL DEFAULT '{}'",
    "created": "timestamptz NOT NULL DEFAULT now()",
}

THREADS_TABLE = "cairn_threads"

_THREAD_COLUMNS = {
    "thread_id": "text PRIMARY KEY",
    "summary": "text NOT NULL",
    "lifecycle_state": "text NOT NULL DEFAULT 'awake'",
    "node_ids": "jsonb NOT NULL DEFAULT '[]'",
    "importance": "real NOT NULL DEFAULT 0.0",
    "recurrence": "real NOT NULL DEFAULT 0.0",
    "last_touched": "timestamptz NOT NULL DEFAULT now()",
    "created": "timestamptz NOT NULL DEFAULT now()",
}

MAX_THREADS = 7
CO_OCCURRENCE_THRESHOLD = 3
WARM_BOOST = 0.1
SLEEP_AFTER = 20

CALVE_THRESHOLD = 5000


class DepositRefused(RuntimeError):
    """A deposit the door cannot honestly accept — refused loudly, nothing landed (Law 7)."""


class WalkRefused(RuntimeError):
    """A walk that would answer a different question than the one asked — refused, not guessed."""


class ReserveRefused(RuntimeError):
    """A slot this box may not hand itself: only the home box's librarian reserves a row
    (outline 4.3.1.5.1.1), so a remote box with no way to ask the home is refused, never
    left to mint a row another box may also be handed."""


class Gone(LookupError):
    """A reference taken at an older gen of a row that has since been voided (and perhaps
    reused): loud, never the new tenant's data (outline 4.3.1.5.1.6)."""


class RefutationRefused(RuntimeError):
    """A retirement the door cannot honestly accept — every lack named in ONE pass, nothing landed.

    One pass rather than one-per-run is the point: a caller that fixes a lack and is
    refused for the next one learns the door's shape by attrition, and a human typing a
    correction gets told the whole truth once (Law 7 at a diagnostic surface)."""


# Who may retire an EARNED node. The borrow is the old ruling intake's supersession rule
# (ruling.py, deleted by ticket 640a7a48e1c5, outline Q#43; the idea stands here) —
# "an unconfirmed reading cannot retire a confirmed act; that would be my guess outvoting
# his signature" — cited in the charter's `entry`, never imported (charter falsifier 7).
# Read as an ALLOWLIST, not a denylist: an unrecognized source is refused against earned
# knowledge, because red is the default and an unknown hand is not a known-safe one (CP6).
_REFUTER_AUTHORITIES = frozenset({"correction"})


def embedding_id_for(node_id, render_method: str) -> str:
    """Deterministic embedding identity: same node + same rendering = same embedding."""
    return hashlib.sha256(f"{node_id}\n{render_method}".encode("utf-8")).hexdigest()[:16]


def leaf_id_for(node_id, embedding_id: str) -> str:
    """Deterministic leaf identity within a leaf table."""
    return hashlib.sha256(f"{node_id}\n{embedding_id}".encode("utf-8")).hexdigest()[:16]


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


# ── addresses, rows, seq (outline 4.3.1.5.1.6, ticket 06db586bedfd) ──────────────────────────


def _tag(kind: str) -> int:
    return A.tag_for(kind)


def _addr(kind: str, row: int) -> int:
    return A.pack(_tag(kind), row)


def _table(kind: str) -> str:
    return {"nodes": NODES_TABLE, "lists": LISTS_TABLE, "links": LINKS_TABLE,
            "blobs": BLOBS_TABLE}[kind]


# The SQL face of a nodes address: tag 1 over the row, as a positive bigint (tag < 0x8000).
_NODE_BASE = A.pack(A.tag_for("nodes"), 1) - 1
_BLOB_BASE = A.pack(A.tag_for("blobs"), 1) - 1


def _node_row(node, *, who: str = "node") -> int:
    """A node reference as its row: a Ref, a nodes address, a bare row, or either as digits.
    Anything else (a hash id, another table's address) is refused, never guessed."""
    if isinstance(node, A.Ref):
        node = node.address
    if isinstance(node, str) and node.strip().lstrip("-").isdigit():
        node = int(node.strip())
    if isinstance(node, bool) or not isinstance(node, int):
        raise WalkRefused(f"{who}: {node!r} is no node address — a node is named by its row "
                          "(outline 4.3.1.5.1.2), never by a hash")
    if 1 <= node <= A.MAX_ROW:
        return node
    try:
        tag, row = A.unpack(node)
    except A.AddressRefused as e:
        raise WalkRefused(f"{who}: {e}") from None
    if tag != _tag("nodes"):
        raise WalkRefused(f"{who}: address {node} is tag {tag} ({_tag_name(tag)}), not a node")
    return row


def _as_addr(node) -> int:
    """``_node_row`` for an entry that judges a missing node itself: a reference that names no
    node reads as 0, which no address is, so the entry's own refusal fires."""
    try:
        return _addr("nodes", _node_row(node))
    except WalkRefused:
        return 0


def _tag_name(tag: int) -> str:
    try:
        return A.name_for(tag)
    except A.AddressRefused:
        return "a leaf table" if tag >= LEAF_TAG_FLOOR else "no table"


def _arr(xs) -> str | None:
    """A postgres array literal (the store json-dumps a Python list, which no array takes)."""
    if xs is None:
        return None
    return "{" + ",".join(str(x) for x in xs) + "}"


def _next_seq(table: str, *, conn) -> int:
    got = store.query("SELECT COALESCE(max(seq), 0) + 1 AS s FROM {t}", tables={"t": table}, conn=conn)
    return int(got[0]["s"])


def _is_seq_race(e: Exception) -> bool:
    return "duplicate key" in str(e) and "seq" in str(e)


def _write(table: str, owner: str, data: dict, *, conn) -> None:
    """A row in, its seq the table's next (the sync's cursor, 4.3.1.5.1.6). seq is UNIQUE, so a
    concurrent writer taking the same number is retried, never doubled."""
    for _ in range(50):
        try:
            store.write(table, owner, {**data, "seq": _next_seq(table, conn=conn)}, conn=conn)
            return
        except Exception as e:  # noqa: BLE001
            if not _is_seq_race(e):
                raise
    raise DepositRefused(f"{table}: 50 tries lost the race for a seq; nothing landed")


def _update(table: str, owner: str, changes: dict, *, where: str, params: tuple, conn) -> int:
    """``_write``'s mutation face: every change moves seq."""
    for _ in range(50):
        try:
            return store.update(table, owner, {**changes, "seq": _next_seq(table, conn=conn)},
                                where=where, params=params, conn=conn)
        except Exception as e:  # noqa: BLE001
            if not _is_seq_race(e):
                raise
    raise DepositRefused(f"{table}: 50 tries lost the race for a seq; nothing changed")


_ENSURED: set[tuple] = set()


def ensure_nodes(*, conn=None) -> None:
    """The shared tables — nodes, lists, links, blobs, tags, the content index, the embeddings —
    and their CHECKs, owner-gated into existence. Asked once per process per set of names."""
    names = (NODES_TABLE, LISTS_TABLE, LINKS_TABLE, BLOBS_TABLE, TAGS_TABLE, CONTENT_INDEX,
             EMBEDDINGS_TABLE)
    if names in _ENSURED:
        return
    for kind, cols in (("nodes", _NODE_COLUMNS), ("lists", _LIST_COLUMNS),
                       ("links", _LINK_COLUMNS), ("blobs", _BLOB_COLUMNS)):
        table = _table(kind)
        store.create_owned_table(table, OWNER, cols, conn=conn)
        for name, expr in _CHECKS[kind].items():
            store.add_owned_constraint(table, OWNER, f"{table}_{name}", expr, conn=conn)
    store.create_owned_table(TAGS_TABLE, OWNER, _TAG_COLUMNS, conn=conn)
    store.create_owned_table(CONTENT_INDEX, OWNER, _CONTENT_INDEX_COLUMNS, conn=conn)
    store.create_owned_table(EMBEDDINGS_TABLE, OWNER, _EMBEDDING_COLUMNS, conn=conn)
    store.add_owned_index(EMBEDDINGS_TABLE, OWNER, f"{EMBEDDINGS_TABLE}_node", ["node_id"], conn=conn)
    _ENSURED.add(names)


def _is_home() -> bool:
    """This box is the home: CAIRN_HOME_HOST unset, or naming this box (the bus's own test)."""
    host = os.environ.get("CAIRN_HOME_HOST", "").strip()
    return not host or host.split(".")[0].lower() == platform.node().split(".")[0].lower()


def _local_max(table: str, *, conn) -> int:
    got = store.query("SELECT max(row) AS m FROM {t}", tables={"t": table}, conn=conn)
    return int(got[0]["m"] or 0)


def _hold_open(table: str, row: int, *, conn) -> None:
    """Rows this box lacks, up to and including ``row``, laid as NOTCACHED (4.3.1.5.1.1/4)."""
    top = _local_max(table, conn=conn)
    if row <= top:
        if not store.read(table, where="row = %s", params=(row,), conn=conn):
            _write(table, OWNER, {"row": row, "gen": 0, "state": NOTCACHED}, conn=conn)
        return
    for r in range(top + 1, row + 1):
        _write(table, OWNER, {"row": r, "gen": 0, "state": NOTCACHED}, conn=conn)


def _reserve_row(kind: str, *, reserver, conn) -> int:
    """A slot in ``kind``'s table, held NOTCACHED until its write completes (4.3.1.5.1.1).

    On the home box the librarian hands out the lowest VOID row, else the next past the end.
    Any other box asks the home through ``reserver(kind)`` (the device wires it to the home
    librarian's bus verb) and holds that row open locally; with no reserver it is refused."""
    table = _table(kind)
    if not _is_home() or reserver is not None:
        if reserver is None:
            raise ReserveRefused(
                f"reserve: this box is not the home ({os.environ.get('CAIRN_HOME_HOST')!r} is) "
                f"and no home-reserver was given — a {kind} slot only the home hands out; "
                "nothing landed")
        row = int(reserver(kind))
        _hold_open(table, row, conn=conn)
        return row
    for _ in range(50):
        free = store.query("SELECT min(row) AS m FROM {t} WHERE state = %s",
                           tables={"t": table}, params=(VOID,), conn=conn)[0]["m"]
        if free is not None:
            if _update(table, OWNER, {"state": NOTCACHED}, where="row = %s AND state = %s",
                       params=(free, VOID), conn=conn):
                return int(free)
            continue
        nxt = _local_max(table, conn=conn) + 1
        try:
            _write(table, OWNER, {"row": nxt, "gen": 0, "state": NOTCACHED}, conn=conn)
            return nxt
        except Exception as e:  # noqa: BLE001 — a concurrent reserve took nxt; ask again
            if "duplicate key" not in str(e):
                raise
    raise ReserveRefused(f"reserve: 50 tries lost the race for a {kind} slot; nothing landed")


def reserve(*, reserver=None, conn=None) -> int:
    """A node slot (its row), from the home box — see ``_reserve_row``."""
    own = conn or store.connect()
    try:
        ensure_nodes(conn=own)
        return _reserve_row("nodes", reserver=reserver, conn=own)
    finally:
        if conn is None:
            own.close()


# ── the dedup seam (Q#109, answered 2026-11-14) ──────────────────────────────────────────────
# FORK POINT: "is this content already held?" is asked HERE and nowhere else. Today the answer
# comes from a keyed content index (content hash -> node address), a tree lookup, never a search
# of the nodes. Whatever replaces the index replaces these three functions and nothing else.


def content_key(content: str) -> str:
    """The key the content index files a node under: the full sha256 of its content. A key in a
    tree, never the node's id."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def already_held(content: str, *, conn) -> int | None:
    """The node address holding ``content``, or None."""
    held = store.read(CONTENT_INDEX, where="key = %s", params=(content_key(content),), conn=conn)
    return int(held[0]["node"]) if held else None


def _hold_content(content: str, node: int, *, conn) -> int | None:
    """File ``content`` under ``node``. None when filed; the address already filed when a
    concurrent deposit won the race."""
    try:
        store.write(CONTENT_INDEX, OWNER, {"key": content_key(content), "node": node}, conn=conn)
        return None
    except Exception as e:  # noqa: BLE001
        if "duplicate key" not in str(e):
            raise
    held = store.read(CONTENT_INDEX, where="key = %s", params=(content_key(content),), conn=conn)
    return int(held[0]["node"])


def _unhold_content(node: int, *, conn) -> None:
    store.delete(CONTENT_INDEX, OWNER, where="node = %s", params=(node,), conn=conn)


# ── lists (outline 4.3.1.5.1.6) ──────────────────────────────────────────────────────────────


def _list_chunks(head, *, conn) -> list[dict]:
    chunks, seen, nxt = [], set(), head
    while nxt and nxt not in seen:
        seen.add(nxt)
        got = store.read(LISTS_TABLE, where="row = %s AND state = %s",
                         params=(A.row_of(nxt), DATA), conn=conn)
        if not got:
            break
        chunks.append(got[0])
        nxt = got[0]["next"]
    return chunks


def list_items(head, *, conn=None) -> list[int]:
    """Every address a list holds, chunk after chunk through ``next``, in order. [] for None."""
    if not head:
        return []
    own = conn or store.connect()
    try:
        return [int(x) for c in _list_chunks(head, conn=own) for x in (c["items"] or [])]
    finally:
        if conn is None:
            own.close()


def _new_list(owner: int, items: list[int], *, reserver, conn) -> int:
    row = _reserve_row("lists", reserver=reserver, conn=conn)
    _update(LISTS_TABLE, OWNER, {"state": DATA, "owner": owner, "items": _arr(items),
                                 "weights": None, "next": None},
            where="row = %s", params=(row,), conn=conn)
    return _addr("lists", row)


def _list_append(node_row: int, column: str, item: int, *, reserver=None, conn) -> None:
    """Append ``item`` to the node's out_list or in_list, laying the list or a next chunk as
    needed."""
    node = store.read(NODES_TABLE, where="row = %s", params=(node_row,), conn=conn)[0]
    owner = _addr("nodes", node_row)
    if not node[column]:
        head = _new_list(owner, [item], reserver=reserver, conn=conn)
        _update(NODES_TABLE, OWNER, {column: head}, where="row = %s", params=(node_row,), conn=conn)
        return
    tail = _list_chunks(node[column], conn=conn)[-1]
    items = list(tail["items"] or [])
    if len(items) < LIST_CHUNK:
        _update(LISTS_TABLE, OWNER, {"items": _arr(items + [item])},
                where="row = %s", params=(tail["row"],), conn=conn)
        return
    nxt = _new_list(owner, [item], reserver=reserver, conn=conn)
    _update(LISTS_TABLE, OWNER, {"next": nxt}, where="row = %s", params=(tail["row"],), conn=conn)


def _list_swap(head, old: int, new: int | None, *, conn) -> None:
    """Replace ``old`` with ``new`` wherever the list holds it; ``new=None`` removes it."""
    for c in _list_chunks(head, conn=conn):
        items = [int(x) for x in (c["items"] or [])]
        if old in items:
            kept = [new if x == old else x for x in items]
            kept = [x for x in kept if x is not None]
            _update(LISTS_TABLE, OWNER, {"items": _arr(kept)}, where="row = %s",
                    params=(c["row"],), conn=conn)


def _void_rows(table: str, rows, *, clear: dict, conn) -> None:
    for row in rows:
        got = store.read(table, where="row = %s", params=(row,), conn=conn)
        if got and got[0]["state"] != VOID:
            _update(table, OWNER, {**clear, "state": VOID, "gen": got[0]["gen"] + 1},
                    where="row = %s", params=(row,), conn=conn)


def _void_list(head, *, conn) -> None:
    rows = [c["row"] for c in _list_chunks(head, conn=conn)]
    _void_rows(LISTS_TABLE, rows, clear={"owner": None, "items": None, "weights": None,
                                         "next": None}, conn=conn)


# ── blobs (Q#111: the storage layer is blob rows) ────────────────────────────────────────────


def _write_blob(data: bytes, kind: str, *, reserver, conn) -> int:
    row = _reserve_row("blobs", reserver=reserver, conn=conn)
    _update(BLOBS_TABLE, OWNER, {"state": DATA, "kind": kind, "bytes": data},
            where="row = %s", params=(row,), conn=conn)
    return _addr("blobs", row)


def _blob_text(blob, *, conn) -> str | None:
    got = store.read(BLOBS_TABLE, where="row = %s AND state = %s",
                     params=(A.row_of(blob), DATA), conn=conn)
    return bytes(got[0]["bytes"]).decode("utf-8") if got else None


# ── the leaf tag registry (home-held, from 0x0100) ───────────────────────────────────────────


def leaf_tag(table: str, *, reserver=None, conn=None) -> int:
    """The tag ``table``'s leaf addresses carry. The home librarian hands the next one out from
    LEAF_TAG_FLOOR the first time a leaf table asks; a remote box asks the home through
    ``reserver("tag", table)`` and records the answer, and with no reserver is refused."""
    own = conn or store.connect()
    try:
        ensure_nodes(conn=own)
        for _ in range(50):
            held = store.read(TAGS_TABLE, where="name = %s", params=(table,), conn=own)
            if held:
                return int(held[0]["tag"])
            if not _is_home() or reserver is not None:
                if reserver is None:
                    raise ReserveRefused(
                        f"leaf_tag: this box is not the home "
                        f"({os.environ.get('CAIRN_HOME_HOST')!r} is) and no home-reserver was "
                        f"given — a tag for {table!r} only the home hands out; nothing landed")
                tag = int(reserver("tag", table))
            else:
                top = store.query("SELECT max(tag) AS m FROM {t}", tables={"t": TAGS_TABLE},
                                  conn=own)[0]["m"]
                tag = max(int(top or 0) + 1, LEAF_TAG_FLOOR)
            if not LEAF_TAG_FLOOR <= tag <= A.MAX_TAG:
                raise ReserveRefused(f"leaf_tag: tag {tag:#x} is outside "
                                     f"{LEAF_TAG_FLOOR:#x}..{A.MAX_TAG:#x}; nothing landed")
            try:
                store.write(TAGS_TABLE, OWNER, {"name": table, "tag": tag}, conn=own)
                return tag
            except Exception as e:  # noqa: BLE001 — a concurrent ask took the name or the tag
                if "duplicate key" not in str(e):
                    raise
        raise ReserveRefused(f"leaf_tag: 50 tries lost the race for {table!r}'s tag")
    finally:
        if conn is None:
            own.close()


def _table_for_tag(tag: int, *, conn) -> str | None:
    got = store.read(TAGS_TABLE, where="tag = %s", params=(tag,), conn=conn)
    return got[0]["name"] if got else None


def _write_leaf(table: str, owner: str, data: dict, node_row: int, *, reserver, conn) -> None:
    """A leaf in, at its own row, and its address appended to the node's in_list."""
    for _ in range(50):
        top = store.query("SELECT max(row) AS m FROM {t}", tables={"t": table}, conn=conn)[0]["m"]
        row = int(top or 0) + 1
        try:
            store.write(table, owner, {**data, "row": row}, conn=conn)
            break
        except Exception as e:  # noqa: BLE001 — a concurrent leaf took the row
            if "duplicate key" not in str(e) or "row" not in str(e):
                raise
    else:
        raise DepositRefused(f"{table}: 50 tries lost the race for a leaf row; nothing landed")
    tag = leaf_tag(table, reserver=reserver, conn=conn)
    _list_append(node_row, "in_list", A.pack(tag, row), reserver=reserver, conn=conn)


# ── the node door ────────────────────────────────────────────────────────────────────────────


def _judge_state(state, content, provenance, standing, *, who: str) -> None:
    if state not in STATES:
        raise DepositRefused(f"{who}: state {state!r} is not one of {STATES} — a node row off its "
                             "three states is a bug (outline 4.3.1.5.1.3); nothing landed")
    if state == DATA:
        if content is None or provenance is None or not standing:
            raise DepositRefused(f"{who}: a {DATA!r} row needs content, provenance and standing; "
                                 "nothing landed")
    elif content is not None or provenance is not None:
        raise DepositRefused(f"{who}: a {state!r} row holds no data; nothing landed")


def _view(raw: dict, *, conn) -> dict:
    """A node row as its readers take it: the row's columns, plus node_id (its address),
    content (inline or through its blob), provenance and standing (from meta)."""
    meta = raw.get("meta")
    content = raw.get("payload")
    if content is None and raw.get("blob"):
        content = _blob_text(raw["blob"], conn=conn)
    return {**raw, "node_id": _addr("nodes", raw["row"]), "content": content,
            "provenance": (meta or {}).get("provenance") if meta is not None else None,
            "standing": (meta or {}).get("standing") if meta is not None else None}


def _get(node, *, conn) -> dict | None:
    """The DATA node a reference names, as a view, or None. No hold-open, no fetch."""
    try:
        row = _node_row(node)
    except WalkRefused:
        return None
    got = store.read(NODES_TABLE, where="row = %s AND state = %s", params=(row, DATA), conn=conn)
    return _view(got[0], conn=conn) if got else None


def _put_meta(node, changes: dict, *, conn) -> None:
    """Merge ``changes`` into a DATA node's meta (provenance, standing, ...); seq moves."""
    row = _node_row(node)
    got = store.read(NODES_TABLE, where="row = %s AND state = %s", params=(row, DATA), conn=conn)
    if not got:
        raise DepositRefused(f"no data node at row {row} to change")
    _update(NODES_TABLE, OWNER, {"meta": {**(got[0]["meta"] or {}), **changes}},
            where="row = %s", params=(row,), conn=conn)


def write_node(row, content, provenance, *, standing: str = "hypothesis", state: str = DATA,
               kind: str = "text", reserver=None, conn=None) -> int:
    """Lay the node at ``row`` (a row or a nodes address) in its state, holding open as NOTCACHED
    any rows between this box's end and it. A payload past INLINE_MAX lands as a blob row the
    node points at. The node's lists are kept. Returns the node's address."""
    _judge_state(state, content, provenance, standing if state == DATA else None, who="write_node")
    own = conn or store.connect()
    try:
        ensure_nodes(conn=own)
        try:
            row = _node_row(row, who="write_node")
        except WalkRefused as e:
            raise DepositRefused(f"{e}; nothing landed") from None
        _hold_open(NODES_TABLE, row, conn=own)
        prior = store.read(NODES_TABLE, where="row = %s", params=(row,), conn=own)[0]
        if prior.get("blob"):
            _void_rows(BLOBS_TABLE, [A.row_of(prior["blob"])], clear={"kind": None, "bytes": None},
                       conn=own)
        if state == DATA:
            payload, blob = content, None
            if len(content) > INLINE_MAX:
                payload = None
                blob = _write_blob(content.encode("utf-8"), "text", reserver=reserver, conn=own)
            data = {"state": DATA, "kind": kind, "payload": payload, "blob": blob,
                    "meta": {"provenance": provenance, "standing": standing},
                    "created": datetime.now(timezone.utc)}
        else:
            data = {"state": state, "kind": None, "payload": None, "blob": None, "meta": None,
                    "out_list": None, "in_list": None}
        _update(NODES_TABLE, OWNER, data, where="row = %s", params=(row,), conn=own)
        return _addr("nodes", row)
    finally:
        if conn is None:
            own.close()


def read_node(node, *, fetch=None, conn=None) -> dict:
    """The node as this box holds it, by Ref, address or row. A row it lacks is held open as
    NOTCACHED; a NOTCACHED row is fed from the master through ``fetch(row) -> {content,
    provenance, standing} | None`` when one is given, and the answer populates the local copy
    (outline 4.3.1.5.1.4). A Ref whose gen the row has moved past raises Gone."""
    own = conn or store.connect()
    try:
        ensure_nodes(conn=own)
        row = _node_row(node, who="read_node")
        _hold_open(NODES_TABLE, row, conn=own)
        got = store.read(NODES_TABLE, where="row = %s", params=(row,), conn=own)[0]
        if isinstance(node, A.Ref) and node.gen != got["gen"]:
            raise Gone(f"row {row} is at gen {got['gen']}; the reference was taken at gen "
                       f"{node.gen} — that node was voided, and the row is not it")
        if got["state"] == NOTCACHED and fetch is not None:
            fed = fetch(row)
            if fed:
                write_node(row, fed["content"], fed["provenance"],
                           standing=fed.get("standing") or "hypothesis", conn=own)
                got = store.read(NODES_TABLE, where="row = %s", params=(row,), conn=own)[0]
        return _view(got, conn=own)
    finally:
        if conn is None:
            own.close()


def confidence(node, *, conn=None):
    """The node's confidence, 0..1, or "unscored" when nothing has scored it (Q#108: in meta;
    measured results high, internet reads lower by source; a WHY when adjudicating conflicts)."""
    own = conn or store.connect()
    try:
        got = _get(node, conn=own)
        score = ((got or {}).get("meta") or {}).get("confidence")
        return "unscored" if score is None else float(score)
    finally:
        if conn is None:
            own.close()


def _unhook(item: int, me: int, *, conn) -> None:
    """Drop one entry of a voided node's lists: a link is voided and taken off its other end's
    list; a leaf is deleted from its table."""
    tag, row = A.unpack(item)
    if tag == _tag("links"):
        got = store.read(LINKS_TABLE, where="row = %s AND state = %s", params=(row, DATA), conn=conn)
        if got:
            lnk = got[0]
            for end, column in ((lnk["a"], "out_list"), (lnk["b"], "in_list")):
                if end != me:
                    other = store.read(NODES_TABLE, where="row = %s", params=(A.row_of(end),),
                                       conn=conn)
                    if other and other[0][column]:
                        _list_swap(other[0][column], item, None, conn=conn)
            _void_rows(LINKS_TABLE, [row], clear={"a": None, "b": None, "weight": None}, conn=conn)
    elif tag >= LEAF_TAG_FLOOR:
        table = _table_for_tag(tag, conn=conn)
        if table and store.owner_of(table, conn=conn):
            store.delete(table, store.owner_of(table, conn=conn), where="row = %s",
                         params=(row,), conn=conn)


def void(node, *, conn=None) -> int:
    """VOID the node: every link it is an end of is voided and taken off the other end's list,
    every leaf that held it is dropped, its embeddings, lists, blob and content-index entry go,
    its data is cleared and its gen bumped, the row free for reuse. Walks its own lists — no
    search. Returns the rows changed (0 for a row already void or not held)."""
    own = conn or store.connect()
    try:
        ensure_nodes(conn=own)
        row = _node_row(node, who="void")
        got = store.read(NODES_TABLE, where="row = %s", params=(row,), conn=own)
        if not got or got[0]["state"] == VOID:
            return 0
        raw, me = got[0], _addr("nodes", row)
        for column in ("in_list", "out_list"):
            for item in list_items(raw[column], conn=own):
                _unhook(item, me, conn=own)
            _void_list(raw[column], conn=own)
        if raw["blob"]:
            _void_rows(BLOBS_TABLE, [A.row_of(raw["blob"])], clear={"kind": None, "bytes": None},
                       conn=own)
        store.delete(EMBEDDINGS_TABLE, OWNER, where="node_id = %s", params=(me,), conn=own)
        _unhold_content(me, conn=own)
        return _update(NODES_TABLE, OWNER,
                       {"state": VOID, "kind": None, "payload": None, "blob": None, "meta": None,
                        "out_list": None, "in_list": None, "gen": raw["gen"] + 1},
                       where="row = %s AND state <> %s", params=(row, VOID), conn=own)
    finally:
        if conn is None:
            own.close()


def ensure_trees(*, table: str = NODES, owner: str = OWNER, keyed: bool = False,
                 conn=None) -> None:
    """The shared tables + the caller's leaf table, owner-gated into existence.

    ``keyed=True`` makes the leaf a keyed one (no embedding; found by its key)."""
    ensure_nodes(conn=conn)
    store.create_owned_table(table, owner, _KEYED_LEAF_COLUMNS if keyed else _LEAF_COLUMNS,
                             conn=conn)


# The tables this process found keyed (ticket fe263b21cece): a leaf's shape is fixed when
# ensure_trees makes it, so the catalog is asked once per table, not on every find. Only a True
# is remembered, so the memory can never refuse a table wrongly; scratch_leaf forgets its table
# as it drops.
_KEYED: set[str] = set()


def _is_keyed(table: str, *, conn) -> bool:
    """A keyed leaf is recognised by its columns: a key, and no embedding_id."""
    if table in _KEYED:
        return True
    cols = {r["column_name"] for r in store.query(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
        tables={}, params=(table,), conn=conn)}
    keyed = "key" in cols and "embedding_id" not in cols
    if keyed:
        _KEYED.add(table)
    return keyed


@contextmanager
def scratch_leaf(prefix: str, *, owner: str = OWNER, suffix: str = "", keyed: bool = False):
    """A leaf table that cannot outlive this process (ticket 201a37bf1613): minted through
    ``store.scratch()`` with the leaf columns, the shared tables ensured beside it, yielded
    by name, dropped at exit — swept by pid if the process never gets there. Children a
    calve mints under it ride as companions (see ``calve``). For proofs and one-shot
    drains; a standing leaf is ``ensure_trees``."""
    columns = _KEYED_LEAF_COLUMNS if keyed else _LEAF_COLUMNS
    with store.scratch(owner, prefix, columns, suffix=suffix) as table:
        try:
            ensure_trees(table=table, owner=owner, keyed=keyed)
            yield table
        finally:
            _KEYED.discard(table)


def forget_leaf(table: str, *, conn=None) -> int:
    """Take a leaf's nodes out of the corpus — each VOIDED for reuse (a row is never deleted:
    its number is its address), which drops its embeddings and every leaf that held it —
    before a scratch leaf drops. Returns the node count forgotten."""
    own = conn or store.connect()
    try:
        if store.owner_of(table, conn=own) is None:
            return 0
        rows = sorted({_node_row(r["node_id"]) for r in store.read(table, conn=own)})
        for row in rows:
            void(row, conn=own)
        return len(rows)
    finally:
        if conn is None:
            own.close()


def ensure_threads(*, conn=None) -> None:
    """The threads table, owner-gated into existence."""
    store.create_owned_table(THREADS_TABLE, OWNER, _THREAD_COLUMNS, conn=conn)


# A leaf's node_id is the node's address as digits; the join takes its row back off the tag.
_LEAF_JOIN = (f"JOIN {{node}} n ON n.state = 'data' AND n.row = "
              f"(CASE WHEN l.node_id ~ '^-?[0-9]+$' THEN l.node_id::bigint END) - {_NODE_BASE} "
              f"LEFT JOIN {{blob}} b ON b.row = n.blob - {_BLOB_BASE} ")
_NODE_FIELDS = (f"(n.row + {_NODE_BASE}) AS node_id, n.row, "
                "COALESCE(n.payload, convert_from(b.bytes, 'UTF8')) AS content, "
                "n.meta->'provenance' AS provenance, n.meta->>'standing' AS standing, n.created")


def _leaf_rows(*, table: str, conn,
               time_window: tuple[datetime, datetime] | None = None) -> list[dict]:
    """All rows in a leaf table, joined through embedding->node.

    When time_window is (start, end), restricts to nodes created in that window.
    A keyed leaf has no embedding to join through, so it is refused, never read as empty.
    """
    if _is_keyed(table, conn=conn):
        raise WalkRefused(
            f"{table!r} is a keyed leaf table — its nodes carry no embedding, so there is no "
            "proximity to walk; find it by its key (find)."
        )
    sql = (
        "SELECT l.leaf_id, l.row AS leaf_row, " + _NODE_FIELDS + ", e.vector, "
        "e.embedding_id, e.render_method "
        "FROM {leaf} l "
        "JOIN {embed} e ON l.embedding_id = e.embedding_id " + _LEAF_JOIN
    )
    params: tuple = ()
    if time_window is not None:
        sql += " WHERE n.created >= %s AND n.created <= %s"
        params = (time_window[0], time_window[1])
    return store.query(sql,
        tables={"leaf": table, "embed": EMBEDDINGS_TABLE, "node": NODES_TABLE,
                "blob": BLOBS_TABLE},
        params=params, conn=conn,
    )


def _judge_content(content, *, who: str) -> None:
    if not isinstance(content, str) or len(_norm(content)) < _MIN_CONTENT_CHARS:
        raise DepositRefused(
            f"{who}: content is "
            f"{len(_norm(content)) if isinstance(content, str) else 'not a string'} "
            f"normalized chars — floor is {_MIN_CONTENT_CHARS}. A node distilled from "
            "near-nothing is invention; nothing landed."
        )


def _judge_provenance(provenance, *, who: str) -> None:
    if not isinstance(provenance, dict) or not str(provenance.get("source", "")).strip():
        raise DepositRefused(
            f"{who}: provenance must be a dict naming a non-empty 'source', got "
            f"{provenance!r}. A node nobody can trace is fabricated attribution as a "
            "permanent resident; nothing landed."
        )


def _write_node(content: str, provenance: dict, *, reserver, conn) -> tuple[int, bool]:
    """The node write both deposit doors share. Content already held (ANY tree) is the node the
    dedup seam names; its provenance is appended as an attestation. New content reserves a row,
    is filed with the seam, and is born a hypothesis there. Returns (address, duplicate)."""
    held = already_held(content, conn=conn)
    if held is None:
        row = reserve(reserver=reserver, conn=conn)
        addr = _addr("nodes", row)
        held = _hold_content(content, addr, conn=conn)
        if held is None:
            write_node(row, content, provenance, reserver=reserver, conn=conn)
            return addr, False
        void(row, conn=conn)  # a concurrent deposit filed the same content first
    prior = _get(held, conn=conn)
    if prior is None:
        raise DepositRefused(f"deposit: the content index names {held}, which holds no data — "
                             "the index and the nodes disagree; nothing landed")
    prov = dict(prior["provenance"] or {})
    attests = list(prov.get("attestations") or [])
    attests.append({**provenance, "at": datetime.now(timezone.utc).isoformat()})
    _put_meta(held, {"provenance": {**prov, "attestations": attests}}, conn=conn)
    return prior["node_id"], True


def deposit(content: str, vector, provenance: dict, *,
            tree: str = "commons", table: str = NODES, owner: str = OWNER,
            render_method: str = "embed:default", reserver=None,
            conn=None) -> dict:
    """The deposit door: one node in, judged before it lands.

    node -> its row in the nodes list, embedding -> the embeddings, leaf -> the caller's leaf
    table, the leaf's address -> the node's in_list. The returned node_id is the node's address
    (outline 4.3.1.5.1.6). A duplicate node (same content, ANY tree) appends provenance as an
    attestation; a new leaf is still written for this tree. Off the home box ``reserver``
    asks the home for each slot (see ``_reserve_row``).
    """
    _judge_content(content, who="deposit")
    v = _check_vector(vector, who="deposit")
    _judge_provenance(provenance, who="deposit")

    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        if _is_keyed(table, conn=own):
            raise DepositRefused(
                f"deposit: {table!r} is a keyed leaf table — it holds no embedding, so a "
                "vectored deposit cannot land there; use deposit_keyed. Nothing landed."
            )
        siblings = _leaf_rows(table=table, conn=own)
        if siblings and len(v) != len(siblings[0]["vector"]):
            raise DepositRefused(
                f"deposit: vector dim {len(v)} vs tree {tree!r} dim {len(siblings[0]['vector'])} "
                "— a mixed-dimension tree cannot be walked; refusing (the first deposit set the "
                "tree's dimension)."
            )
        nid, node_is_dup = _write_node(content, provenance, reserver=reserver, conn=own)
        eid = embedding_id_for(nid, render_method)
        lid = leaf_id_for(nid, eid)
        if not store.read(EMBEDDINGS_TABLE, where="embedding_id = %s", params=(eid,), conn=own):
            store.write(EMBEDDINGS_TABLE, OWNER, {
                "embedding_id": eid,
                "node_id": nid,
                "vector": v,
                "render_method": render_method,
            }, conn=own)
        leaf_is_dup = bool(store.read(table, where="leaf_id = %s", params=(lid,), conn=own))
        if not leaf_is_dup:
            _write_leaf(table, owner, {"leaf_id": lid, "node_id": str(nid), "embedding_id": eid},
                        A.row_of(nid), reserver=reserver, conn=own)
        return {"node_id": nid, "duplicate": node_is_dup and leaf_is_dup,
                "dim": len(v), "provenance_appended": node_is_dup}
    finally:
        if conn is None:
            own.close()


def deposit_keyed(content: str, key: str, provenance: dict, *, table: str,
                  owner: str = OWNER, meta: dict | None = None, reserver=None,
                  conn=None) -> dict:
    """The keyed deposit door (ticket e62f40f35f59, outline 4.3.1.6): one node in, with no
    embedding, under ``key`` in a keyed leaf table. Judged as ``deposit`` judges (content
    floor, provenance), plus a non-blank key; the node write is deposit's own. The same
    content under the same key is one leaf (its provenance attested); under a second key, a
    second leaf over the one node. ``meta`` rides the leaf (eg a stored answer's verdict)."""
    _judge_content(content, who="deposit_keyed")
    _judge_provenance(provenance, who="deposit_keyed")
    if not isinstance(key, str) or not key.strip():
        raise DepositRefused(
            f"deposit_keyed: key must be a non-blank string, got {key!r} — a node filed under "
            "nothing can never be found by its key; nothing landed."
        )
    if meta is not None and not isinstance(meta, dict):
        raise DepositRefused(f"deposit_keyed: meta must be a dict or None, got {type(meta).__name__}")
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, keyed=True, conn=own)
        if not _is_keyed(table, conn=own):
            raise DepositRefused(
                f"deposit_keyed: {table!r} is a vectored leaf table — its leaves need an "
                "embedding; use deposit with a vector. Nothing landed."
            )
        nid, node_is_dup = _write_node(content, provenance, reserver=reserver, conn=own)
        lid = leaf_id_for(nid, key)
        leaf_is_dup = bool(store.read(table, where="leaf_id = %s", params=(lid,), conn=own))
        if not leaf_is_dup:
            _write_leaf(table, owner, {"leaf_id": lid, "key": key, "node_id": str(nid),
                                       "meta": meta or {}},
                        A.row_of(nid), reserver=reserver, conn=own)
        return {"node_id": nid, "duplicate": node_is_dup and leaf_is_dup,
                "provenance_appended": node_is_dup}
    finally:
        if conn is None:
            own.close()


def find(key: str, *, table: str, conn=None) -> list[dict]:
    """The nodes under ``key`` in a keyed leaf table, newest leaf first: node_id, key,
    content, provenance, standing, meta, created. [] for an unknown key or an absent table;
    a vectored table is refused (it is walked by proximity, not found by key)."""
    own = conn or store.connect()
    try:
        if store.owner_of(table, conn=own) is None:
            return []
        if not _is_keyed(table, conn=own):
            raise WalkRefused(
                f"find: {table!r} is a vectored leaf table — it is walked by proximity "
                "(nearest), not found by key."
            )
        ensure_nodes(conn=own)
        return store.query(
            f"SELECT (n.row + {_NODE_BASE}) AS node_id, l.key, "
            "COALESCE(n.payload, convert_from(b.bytes, 'UTF8')) AS content, "
            "n.meta->'provenance' AS provenance, n.meta->>'standing' AS standing, l.meta, "
            "l.created FROM {leaf} l " + _LEAF_JOIN +
            "WHERE l.key = %s ORDER BY l.created DESC",
            tables={"leaf": table, "node": NODES_TABLE, "blob": BLOBS_TABLE},
            params=(key,), conn=own)
    finally:
        if conn is None:
            own.close()


def corroborate(node_id: str, question: str, *, promote_at: int,
                tree: str = "commons", table: str = NODES, owner: str = OWNER,
                conn=None) -> dict:
    """The earning write on the SHARED node (cairn_mem_nodes), fired by the
    librarian's resolution event — never by a clock.

    The tree/table params kept for API compatibility but the attestation
    lands on the shared node.
    """
    own = conn or store.connect()
    try:
        node_id = _as_addr(node_id)
        row = _get(node_id, conn=own)
        if row is None:
            raise DepositRefused(
                f"corroborate: no standing node {node_id!r} — nothing to attest")
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
            _put_meta(node_id, changes, conn=own)
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
    """The retirement door on the SHARED node (cairn_mem_nodes).

    tree/table params kept for API compatibility; reads/writes go to the node's meta.
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
        node_id = _as_addr(node_id)
        refuter_id = _as_addr(refuter_id)
        ensure_trees(table=table, owner=owner, conn=own)
        seen: dict[str, dict] = {}
        for wanted in (node_id, refuter_id):
            if wanted in seen:
                continue
            found = _get(wanted, conn=own)
            if found:
                seen[wanted] = found
        target = seen.get(node_id)
        refuter = seen.get(refuter_id)

        if target is None:
            lacks.append(f"no standing node {node_id!r} — nothing to retire")
        if refuter is None:
            lacks.append(
                f"no standing node {refuter_id!r} — the refuter must itself "
                "be in the record, or the retirement cites nothing"
            )
        if node_id == refuter_id:
            lacks.append(
                f"{node_id!r} would refute itself — a node arguing itself down is not "
                "evidence, and the receipt would cite the thing it retired"
            )
        if refuter_id in {_as_addr(m) for m in minted_this_crossing}:
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

        prov = dict(target["provenance"] or {})
        attests = list(prov.get("attestations") or [])
        attests.append({"source": "refutation", "refuter": refuter_id, "evidence": ev,
                        "at": datetime.now(timezone.utc).isoformat()})
        _put_meta(node_id, {"standing": "refuted",
                            "provenance": {**prov, "attestations": attests}}, conn=own)
        return {"refuted": True, "node_id": node_id, "refuter": refuter_id,
                "was": target["standing"], "attestations": len(attests)}
    finally:
        if conn is None:
            own.close()


CONTRADICTION_K = 5
CONTRADICTION_THRESHOLD = 0.7

_CONTRADICTION_PROMPT = (
    "You are a factual consistency checker. Given two statements, determine if "
    "Statement B directly contradicts Statement A — meaning they cannot both be true.\n\n"
    "Statement A: {existing}\n"
    "Statement B: {incoming}\n\n"
    "Answer ONLY 'YES' if Statement B directly contradicts Statement A, or 'NO' if they "
    "are compatible, related but not contradictory, or addressing different aspects.\n"
    "Answer:"
)


def contradiction_scan(node_id: str, vector, *, resolve,
                       tree: str = "commons", table: str = NODES,
                       owner: str = OWNER, conn=None) -> list[dict]:
    """Deposit-time contradiction detection — cosine filter, inference judge.

    Walk the k nearest neighbors of the just-deposited node. For each that is not
    already refuted and is above the cosine threshold, ask inference whether the new
    statement contradicts the existing one. On YES, call refute() on the existing node.

    Returns a list of {refuted_node_id, evidence} for each confirmed contradiction.
    The 'contradicts' provenance field on the depositing node is set here.
    """
    own = conn or store.connect()
    try:
        node_id = _as_addr(node_id)
        ensure_trees(table=table, owner=owner, conn=own)
        walk = nearest(vector, k=CONTRADICTION_K, tree=tree, table=table, conn=own)
        candidates = [n for n in walk
                      if n["node_id"] != node_id
                      and n.get("standing") != "refuted"
                      and n["similarity"] >= CONTRADICTION_THRESHOLD]
        if not candidates:
            return []

        depositor = _get(node_id, conn=own)
        if not depositor:
            return []
        incoming_content = depositor["content"]

        refuted = []
        for candidate in candidates:
            prompt = _CONTRADICTION_PROMPT.format(
                existing=candidate["content"],
                incoming=incoming_content
            )
            try:
                result = resolve({"kind": "generate", "prompt": prompt})
                answer = result.get("answer", {}).get("text", "").strip().upper()
            except Exception:
                continue
            if not answer.startswith("YES"):
                continue
            try:
                refute(candidate["node_id"], node_id,
                       f"Contradicted by deposit {node_id}: "
                       f"{incoming_content[:200]}",
                       tree=tree, table=table, owner=owner, conn=own)
                refuted.append({"refuted_node_id": candidate["node_id"],
                                "evidence": "inference-confirmed contradiction"})
            except RefutationRefused:
                continue

        if refuted:
            dep_row = _get(node_id, conn=own)
            if dep_row:
                prov = dict(dep_row["provenance"] or {})
                prov["contradicts"] = [r["refuted_node_id"] for r in refuted]
                _put_meta(node_id, {"provenance": prov}, conn=own)

        return refuted
    finally:
        if conn is None:
            own.close()


CONSOLIDATION_K = 10
CONSOLIDATION_THRESHOLD = 0.5
CONSOLIDATION_MIN_SOURCES = 2

_CONSOLIDATION_PROMPT = (
    "You are a knowledge synthesizer. Given multiple related statements, produce ONE "
    "higher-level statement that subsumes them — a concise summary that captures the "
    "essential insight across all of them.\n\n"
    "Statements:\n{statements}\n\n"
    "Produce exactly ONE synthesized statement (no numbering, no preamble):\n"
)


class ConsolidationRefused(Exception):
    pass


def consolidate(node_id: str, vector, *, resolve,
                tree: str = "commons", table: str = NODES,
                owner: str = OWNER, conn=None) -> dict | None:
    """Promotion-event consolidation: synthesize a cluster into a higher-level node.

    Walks the promoted node's neighbors, filters to attestation-bearing nodes that
    are not refuted, calls inference to synthesize a higher-level statement, deposits
    it as a new node with provenance.source='consolidated', and links to each source.

    The recursive gate: a source node with provenance.source='consolidated' is only
    included if it has earned standing — ungated recursion is the rot path.

    Returns the deposit result dict on success, None if the cluster is too small.
    """
    own = conn or store.connect()
    try:
        node_id = _as_addr(node_id)
        ensure_trees(table=table, owner=owner, conn=own)

        walk = nearest(vector, k=CONSOLIDATION_K, tree=tree, table=table, conn=own)
        sources = []
        for n in walk:
            if n["node_id"] == node_id:
                continue
            if n.get("standing") == "refuted":
                continue
            if n["similarity"] < CONSOLIDATION_THRESHOLD:
                continue
            prov = n.get("provenance") or {}
            if not prov.get("attestations"):
                continue
            # Recursive gate: consolidated sources must be earned
            if str(prov.get("source", "")) == "consolidated":
                if n.get("standing") != "earned":
                    continue
            sources.append(n)

        # Include the promoted node itself
        promoted_row = _get(node_id, conn=own)
        if promoted_row:
            sources.insert(0, {
                "node_id": node_id,
                "content": promoted_row["content"],
                "provenance": promoted_row["provenance"],
                "standing": promoted_row["standing"],
            })

        if len(sources) < CONSOLIDATION_MIN_SOURCES:
            return None

        statements = "\n".join(
            f"- {s['content']}" for s in sources
        )
        prompt = _CONSOLIDATION_PROMPT.format(statements=statements)
        result = resolve({"kind": "generate", "prompt": prompt})
        synthesis = result.get("answer", {}).get("text", "").strip()
        if not synthesis:
            return None

        source_node_ids = [s["node_id"] for s in sources]
        provenance = {
            "source": "consolidated",
            "source_nodes": source_node_ids,
            "trigger": "promotion",
        }

        embed_result = resolve({"kind": "embed", "prompt": synthesis})
        synth_vector = embed_result["answer"]["vector"]

        dep_result = deposit(synthesis, synth_vector, provenance,
                             tree=tree, table=table, owner=owner, conn=own)

        if not dep_result["duplicate"]:
            for sid in source_node_ids:
                try:
                    link(dep_result["node_id"], sid, 1.0, conn=own)
                except Exception:
                    pass

        return dep_result
    finally:
        if conn is None:
            own.close()


# ── warm-set threads ────────────────────────────────────────────────────────


_TEMPORAL_KEYWORDS = {
    "yesterday": timedelta(hours=24),
    "last week": timedelta(days=7),
    "recently": timedelta(days=3),
}


def parse_temporal(question: str, *,
                   now: datetime | None = None) -> tuple[datetime, datetime] | None:
    """Extract a time window from temporal language in the question.

    Returns (start, end) or None if no temporal signal is found.
    """
    ref = now or datetime.now(timezone.utc)
    q = question.lower()
    for keyword, delta in _TEMPORAL_KEYWORDS.items():
        if keyword in q:
            return (ref - delta, ref)
    # ISO date: look for YYYY-MM-DD pattern
    for i in range(len(q) - 9):
        candidate = q[i:i + 10]
        if (len(candidate) == 10 and candidate[4] == "-" and candidate[7] == "-"
                and candidate[:4].isdigit() and candidate[5:7].isdigit()
                and candidate[8:10].isdigit()):
            try:
                day = datetime.fromisoformat(candidate).replace(tzinfo=timezone.utc)
                return (day, day + timedelta(days=1))
            except ValueError:
                continue
    return None


def _thread_id() -> str:
    return hashlib.sha256(
        datetime.now(timezone.utc).isoformat().encode()
    ).hexdigest()[:12]


def get_threads(*, conn=None) -> list[dict]:
    """All threads, sorted by last_touched descending."""
    own = conn or store.connect()
    try:
        ensure_threads(conn=own)
        rows = store.read(THREADS_TABLE, conn=own)
        return sorted(rows, key=lambda t: t.get("last_touched", ""), reverse=True)
    finally:
        if conn is None:
            own.close()


def awake_thread_node_ids(*, conn=None) -> set[str]:
    """The union of node_ids from all awake threads."""
    threads = get_threads(conn=conn)
    result: set[str] = set()
    for t in threads:
        if t.get("lifecycle_state") == "awake":
            for nid in (t.get("node_ids") or []):
                result.add(nid)
    return result


def _retire_lowest(*, conn) -> bool:
    """Retire the lowest-importance sleeping thread. Returns True if one was retired."""
    threads = get_threads(conn=conn)
    sleeping = [t for t in threads if t.get("lifecycle_state") == "sleeping"]
    if not sleeping:
        return False
    lowest = min(sleeping, key=lambda t: t.get("importance", 0.0))
    store.delete(THREADS_TABLE, OWNER,
                 where="thread_id = %s", params=(lowest["thread_id"],), conn=conn)
    return True


def detect_threads(node_id: str, *, resolve, conn=None) -> dict | None:
    """Detect co-occurring clusters and crystallize into a thread.

    Scans the promoted node's links for traversals > CO_OCCURRENCE_THRESHOLD.
    If a cluster is found, calls inference for a summary and creates a thread.
    Enforces MAX_THREADS bound by retiring the lowest-importance sleeping thread.
    """
    own = conn or store.connect()
    try:
        node_id = _as_addr(node_id)
        ensure_threads(conn=own)
        _ensure_links(own)
        links = linked(node_id, conn=own)
        cluster = [node_id]
        total_traversals = 0
        for lnk in links:
            if lnk.get("traversals", 0) >= CO_OCCURRENCE_THRESHOLD:
                other = lnk["target_id"] if lnk["source_id"] == node_id else lnk["source_id"]
                cluster.append(other)
                total_traversals += lnk["traversals"]

        if len(cluster) < 2:
            return None

        existing = get_threads(conn=own)
        existing_node_sets = [set(t.get("node_ids", [])) for t in existing]
        cluster_set = set(cluster)
        for ens in existing_node_sets:
            if cluster_set & ens:
                return None

        if len(existing) >= MAX_THREADS:
            if not _retire_lowest(conn=own):
                return None

        contents = []
        for nid in cluster:
            got = _get(nid, conn=own)
            if got:
                contents.append(got["content"])
        if not contents:
            return None

        prompt = ("Summarize this cluster of related topics in one sentence:\n"
                  + "\n".join(f"- {c}" for c in contents))
        result = resolve({"kind": "generate", "prompt": prompt})
        summary = result.get("answer", {}).get("text", "").strip()
        if not summary:
            summary = contents[0][:100]

        tid = _thread_id()
        importance = total_traversals / max(len(cluster) - 1, 1)
        store.write(THREADS_TABLE, OWNER, {
            "thread_id": tid,
            "summary": summary,
            "lifecycle_state": "awake",
            "node_ids": cluster,
            "importance": importance,
            "recurrence": 0.0,
        }, conn=own)
        return {"thread_id": tid, "summary": summary, "node_ids": cluster}
    finally:
        if conn is None:
            own.close()


def wake_threads(node_ids: list[str], *, conn=None) -> list[str]:
    """Wake any sleeping threads whose nodes overlap with the given node_ids."""
    own = conn or store.connect()
    try:
        ensure_threads(conn=own)
        touched = set(node_ids)
        threads = get_threads(conn=own)
        woken = []
        for t in threads:
            if t.get("lifecycle_state") != "sleeping":
                continue
            thread_nodes = set(t.get("node_ids", []))
            if thread_nodes & touched:
                store.update(THREADS_TABLE, OWNER, {
                    "lifecycle_state": "awake",
                    "last_touched": datetime.now(timezone.utc),
                }, where="thread_id = %s", params=(t["thread_id"],), conn=own)
                woken.append(t["thread_id"])
        return woken
    finally:
        if conn is None:
            own.close()


def attend_thread(node_ids: list[str], *, conn=None) -> list[str]:
    """Attend awake threads whose nodes were involved in a resolution."""
    own = conn or store.connect()
    try:
        ensure_threads(conn=own)
        touched = set(node_ids)
        threads = get_threads(conn=own)
        attended = []
        for t in threads:
            if t.get("lifecycle_state") != "awake":
                continue
            thread_nodes = set(t.get("node_ids", []))
            if thread_nodes & touched:
                store.update(THREADS_TABLE, OWNER, {
                    "recurrence": t.get("recurrence", 0.0) + 1.0,
                    "last_touched": datetime.now(timezone.utc),
                }, where="thread_id = %s", params=(t["thread_id"],), conn=own)
                attended.append(t["thread_id"])
        return attended
    finally:
        if conn is None:
            own.close()


def sleep_check(*, conn=None, _resolution_counter: dict | None = None) -> list[str]:
    """Put awake threads to sleep after SLEEP_AFTER untouched resolutions.

    The _resolution_counter is a mutable dict mapping thread_id -> count of
    resolutions since last touch. Callers maintain it across resolution calls.
    """
    if _resolution_counter is None:
        return []
    own = conn or store.connect()
    try:
        ensure_threads(conn=own)
        threads = get_threads(conn=own)
        slept = []
        for t in threads:
            if t.get("lifecycle_state") != "awake":
                continue
            tid = t["thread_id"]
            count = _resolution_counter.get(tid, 0)
            if count >= SLEEP_AFTER:
                store.update(THREADS_TABLE, OWNER, {
                    "lifecycle_state": "sleeping",
                }, where="thread_id = %s", params=(tid,), conn=own)
                slept.append(tid)
                _resolution_counter.pop(tid, None)
        return slept
    finally:
        if conn is None:
            own.close()


def tree_state(tree: str, *, table: str = NODES, owner: str = OWNER, conn=None) -> dict:
    """The tree's fingerprint: ``{"digest", "nodes"}`` — same members, same digest.

    Reads the leaf table to enumerate what nodes this tree contains.
    """
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        ids = sorted(str(r["node_id"]) for r in _leaf_rows(table=table, conn=own))
        digest = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()[:16] if ids else "empty"
        return {"digest": digest, "nodes": len(ids)}
    finally:
        if conn is None:
            own.close()


# ── attractor ────────────────────────────────────────────────────────────────


def attractor(*, table: str = NODES, owner: str = OWNER, conn=None) -> list[float] | None:
    """The tree's attractor: centroid of all embedding vectors in this leaf table.

    None for an empty tree (no leaves = no direction). The attractor IS the
    tree's identity in vector space — routing (ρ) compares queries to it, and
    calving triggers when the attractor stops representing its members.
    """
    own = conn or store.connect()
    try:
        try:
            rows = _leaf_rows(table=table, conn=own)
        except Exception:
            return None
        if not rows:
            return None
        dim = len(rows[0]["vector"])
        centroid = [0.0] * dim
        for r in rows:
            v = r["vector"]
            for i in range(dim):
                centroid[i] += float(v[i])
        n = len(rows)
        return [c / n for c in centroid]
    finally:
        if conn is None:
            own.close()


# ── calving and the shear ───────────────────────────────────────────────────
# Links join node addresses, which a calve never moves, so the shear on links is a
# verification. A leaf's address is its table's tag over its row, so a rehomed leaf gets a
# new address in its child and calve swaps it in the node's in_list (outline 4.3.1.5.1.6.6).


def _kmeans2(vectors: list[list[float]], max_iter: int = 20) -> tuple[list[int], list[list[float]]]:
    """2-means clustering. Returns (assignments, [centroid_0, centroid_1])."""
    n = len(vectors)
    if n < 2:
        return [0] * n, [list(vectors[0])] if vectors else []
    dim = len(vectors[0])
    centroid = [sum(v[d] for v in vectors) / n for d in range(dim)]
    s0 = max(range(n), key=lambda i: 1.0 - cosine(vectors[i], centroid))
    s1 = max(range(n), key=lambda i: 1.0 - cosine(vectors[i], vectors[s0]))
    if s0 == s1:
        return [0] * n, [centroid]
    centroids = [list(vectors[s0]), list(vectors[s1])]
    assignments = [0] * n
    for _ in range(max_iter):
        changed = False
        for i, v in enumerate(vectors):
            a = 0 if cosine(v, centroids[0]) >= cosine(v, centroids[1]) else 1
            if a != assignments[i]:
                assignments[i] = a
                changed = True
        if not changed:
            break
        for c in range(2):
            members = [vectors[i] for i, a in enumerate(assignments) if a == c]
            if members:
                centroids[c] = [sum(m[d] for m in members) / len(members) for d in range(dim)]
    return assignments, centroids


def _verify_links_after_calve(node_ids: set, conn) -> int:
    """Verify every link of a calved node still resolves at both ends (the shear)."""
    verified, seen = 0, set()
    for nid in node_ids:
        for lnk in linked(nid, conn=conn):
            if lnk["link"] in seen:
                continue
            seen.add(lnk["link"])
            for end in (lnk["source_id"], lnk["target_id"]):
                if _get(end, conn=conn) is None:
                    raise RuntimeError(
                        f"calve shear: link {lnk['link']!r} references node {end!r} "
                        "which holds no data — orphaned link")
            verified += 1
    return verified


def calve(*, table: str = NODES, owner: str = OWNER,
          threshold: int = CALVE_THRESHOLD, conn=None) -> dict | None:
    """Split a leaf table into two child tables by 2-means clustering.

    Returns None if the table has fewer than ``threshold`` leaves (no split needed).
    On split: creates ``{table}_0`` and ``{table}_1``, moves every leaf into the
    nearer child, and empties the parent. The parent table stays (its name may be
    held by callers); the children are the new walk targets.

    Link integrity: links join node addresses, which a calve never moves; the shear verifies
    it after every split. Each leaf takes a new row (so a new address) in its child, and the
    node's in_list entry is swapped from the old leaf address to the new one.
    """
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        rows = _leaf_rows(table=table, conn=own)
        if len(rows) < threshold:
            return None

        vectors = [[float(x) for x in r["vector"]] for r in rows]
        assignments, centroids = _kmeans2(vectors)

        if len(centroids) < 2 or all(a == 0 for a in assignments):
            return None

        child_a = f"{table}_0"
        child_b = f"{table}_1"
        store.create_owned_table(child_a, owner, _LEAF_COLUMNS, conn=own)
        store.create_owned_table(child_b, owner, _LEAF_COLUMNS, conn=own)
        # children of a scratch leaf (a proof's) are scratch: they drop with the parent
        # (ticket 201a37bf1613 — the same companion rule the bus's _delivery rides)
        if store.is_scratch(table, conn=own):
            store.register_scratch_companion(table, child_a, conn=own)
            store.register_scratch_companion(table, child_b, conn=own)

        node_ids = set()
        sizes = [0, 0]
        parent_tag = leaf_tag(table, conn=own)
        child_tags = [leaf_tag(child_a, conn=own), leaf_tag(child_b, conn=own)]
        for i, r in enumerate(rows):
            target = child_a if assignments[i] == 0 else child_b
            store.write(target, owner, {
                "leaf_id": r["leaf_id"],
                "row": _local_max(target, conn=own) + 1,
                "node_id": str(r["node_id"]),
                "embedding_id": r["embedding_id"],
            }, conn=own)
            moved = store.read(target, where="leaf_id = %s", params=(r["leaf_id"],), conn=own)[0]
            node = store.read(NODES_TABLE, where="row = %s", params=(r["row"],), conn=own)[0]
            if r["leaf_row"] is not None:
                _list_swap(node["in_list"], A.pack(parent_tag, r["leaf_row"]),
                           A.pack(child_tags[assignments[i]], moved["row"]), conn=own)
            node_ids.add(r["node_id"])
            sizes[assignments[i]] += 1

        store.delete(table, owner, conn=own)

        links_verified = _verify_links_after_calve(node_ids, own)

        return {
            "children": [child_a, child_b],
            "sizes": sizes,
            "attractors": centroids,
            "links_verified": links_verified,
        }
    finally:
        if conn is None:
            own.close()


# ── bidirectional links (outline 4.3.1.5.1.6: one row, held by both ends) ────────────────────


def _ensure_links(conn) -> None:
    ensure_nodes(conn=conn)


def _find_link(a: int, b: int, *, conn) -> dict | None:
    """The live link between two nodes, either way round, found through a's own lists."""
    node = store.read(NODES_TABLE, where="row = %s AND state = %s",
                      params=(A.row_of(a), DATA), conn=conn)
    if not node:
        return None
    rows = [A.row_of(x) for col in ("out_list", "in_list")
            for x in list_items(node[0][col], conn=conn) if A.tag_of(x) == _tag("links")]
    if not rows:
        return None
    got = store.query("SELECT * FROM {t} WHERE state = %s AND row = ANY(%s) "
                      "AND ((a = %s AND b = %s) OR (a = %s AND b = %s))",
                      tables={"t": LINKS_TABLE}, params=(DATA, rows, a, b, b, a), conn=conn)
    return got[0] if got else None


def link(source_id, target_id, weight: float, *, reserver=None, conn=None) -> dict:
    """Create or update the one bidirectional link between two nodes: its address goes in the
    source's out_list and the target's in_list; asked either way round, it is the same link."""
    own = conn or store.connect()
    try:
        a, b = _as_addr(source_id), _as_addr(target_id)
        for end, name in ((a, source_id), (b, target_id)):
            if not end or _get(end, conn=own) is None:
                raise DepositRefused(f"link: no data node {name!r} to link; nothing landed")
        _ensure_links(own)
        existing = _find_link(a, b, conn=own)
        if existing:
            _update(LINKS_TABLE, OWNER, {"weight": weight}, where="row = %s",
                    params=(existing["row"],), conn=own)
            laddr = _addr("links", existing["row"])
            return {"link": laddr, "link_id": laddr, "updated": True}
        row = _reserve_row("links", reserver=reserver, conn=own)
        _update(LINKS_TABLE, OWNER, {"state": DATA, "a": a, "b": b, "weight": weight,
                                     "traversals": 0}, where="row = %s", params=(row,), conn=own)
        laddr = _addr("links", row)
        _list_append(A.row_of(a), "out_list", laddr, reserver=reserver, conn=own)
        _list_append(A.row_of(b), "in_list", laddr, reserver=reserver, conn=own)
        return {"link": laddr, "link_id": laddr, "updated": False}
    finally:
        if conn is None:
            own.close()


def link_neighbors(node_id, *, k: int = 5, table: str = NODES,
                   owner: str = OWNER, conn=None) -> list[dict]:
    """Create links between a node and its k nearest neighbors in the tree."""
    own = conn or store.connect()
    try:
        node_id = _as_addr(node_id)
        _ensure_links(own)
        emb = store.read(EMBEDDINGS_TABLE, where="node_id = %s",
                         params=(node_id,), conn=own)
        if not emb:
            return []
        vector = [float(x) for x in emb[0]["vector"]]
        nears = nearest(vector, k=k + 1, table=table, conn=own)
        results = []
        for n in nears:
            if n["node_id"] != node_id:
                results.append(link(node_id, n["node_id"], n["similarity"], conn=own))
        return results[:k]
    finally:
        if conn is None:
            own.close()


def traverse_link(source_id, target_id, *, conn=None) -> dict | None:
    """Record a link traversal — increment the use count. Either way round is the same link."""
    own = conn or store.connect()
    try:
        a, b = _as_addr(source_id), _as_addr(target_id)
        _ensure_links(own)
        existing = _find_link(a, b, conn=own) if a and b else None
        if not existing:
            return None
        new_count = existing["traversals"] + 1
        _update(LINKS_TABLE, OWNER, {"traversals": new_count}, where="row = %s",
                params=(existing["row"],), conn=own)
        laddr = _addr("links", existing["row"])
        return {"link": laddr, "link_id": laddr, "traversals": new_count}
    finally:
        if conn is None:
            own.close()


def linked(node_id, *, conn=None) -> list[dict]:
    """All live links of a node, both directions, ordered by weight: link, source_id,
    target_id, weight, traversals, created, and the other end's content and standing."""
    own = conn or store.connect()
    try:
        me = _as_addr(node_id)
        _ensure_links(own)
        node = store.read(NODES_TABLE, where="row = %s AND state = %s",
                          params=(A.row_of(me), DATA), conn=own) if me else []
        if not node:
            return []
        rows = [A.row_of(x) for col in ("out_list", "in_list")
                for x in list_items(node[0][col], conn=own) if A.tag_of(x) == _tag("links")]
        if not rows:
            return []
        got = store.query(
            "SELECT l.row, l.a AS source_id, l.b AS target_id, l.weight, l.traversals, "
            "l.created FROM {links} l WHERE l.state = %s AND l.row = ANY(%s) "
            "ORDER BY l.weight DESC",
            tables={"links": LINKS_TABLE}, params=(DATA, rows), conn=own)
        out = []
        for lnk in got:
            other = _get(lnk["target_id"] if lnk["source_id"] == me else lnk["source_id"],
                         conn=own)
            laddr = _addr("links", lnk["row"])
            out.append({"link": laddr, "link_id": laddr, "source_id": lnk["source_id"],
                        "target_id": lnk["target_id"], "weight": lnk["weight"],
                        "traversals": lnk["traversals"], "created": lnk["created"],
                        "content": (other or {}).get("content"),
                        "standing": (other or {}).get("standing")})
        return out
    finally:
        if conn is None:
            own.close()


# ── multi-tree routing ρ(q) ─────────────────────────────────────────────────


def route(vector, *, tables: list[str], k: int = 3, conn=None) -> list[dict]:
    """Multi-tree routing: rank trees by attractor proximity to the query vector.

    Each tree's attractor (centroid) is compared to the query; the top k trees
    are returned. An empty tree (no attractor) is skipped.
    """
    v = _check_vector(vector, who="route")
    own = conn or store.connect()
    try:
        scored = []
        for t in tables:
            a = attractor(table=t, owner=OWNER, conn=own)
            if a is not None:
                scored.append({
                    "table": t,
                    "similarity": cosine(v, a),
                })
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:k]
    finally:
        if conn is None:
            own.close()


# ── walks ────────────────────────────────────────────────────────────────────


def nearest(vector, *, k: int = 5, tree: str = "commons",
            table: str = NODES, owner: str = OWNER,
            warm_node_ids: set[str] | None = None,
            time_window: tuple[datetime, datetime] | None = None,
            conn=None) -> list[dict]:
    """The walk: the k nodes nearest the query vector, by cosine.

    Reads the leaf table (three-table join) to get content + vector + provenance.
    When warm_node_ids is provided, those nodes get an additive WARM_BOOST to similarity.
    When time_window is provided, only nodes created in that window are considered.
    """
    if not isinstance(k, int) or k < 1:
        raise WalkRefused(f"nearest: k must be a positive int, got {k!r}")
    v = _check_vector(vector, who="nearest")
    own = conn or store.connect()
    try:
        ensure_trees(table=table, owner=owner, conn=own)
        rows = _leaf_rows(table=table, conn=own, time_window=time_window)
        if not rows:
            return []
        tree_dim = len(rows[0]["vector"])
        if len(v) != tree_dim:
            raise WalkRefused(
                f"nearest: query dim {len(v)} vs tree {tree!r} dim {tree_dim} — "
                "answering across dimensions would be a silent wrong answer; refused."
            )
        warm = warm_node_ids or set()
        ranked = sorted(
            ({"node_id": r["node_id"], "content": r["content"],
              "similarity": cosine(v, [float(x) for x in r["vector"]])
                           + (WARM_BOOST if r["node_id"] in warm else 0.0),
              "provenance": r["provenance"], "standing": r["standing"],
              "created": r["created"]}
             for r in rows),
            key=lambda n: n["similarity"], reverse=True)
        return ranked[:k]
    finally:
        if conn is None:
            own.close()


def neighbors(node_id: str, *, k: int = 5, tree: str = "commons",
              table: str = NODES, owner: str = OWNER, conn=None) -> list[dict]:
    """A node's derived edges: its k nearest siblings in this tree, itself excluded."""
    own = conn or store.connect()
    try:
        node_id = _as_addr(node_id)
        ensure_trees(table=table, owner=owner, conn=own)
        if _is_keyed(table, conn=own):
            raise WalkRefused(
                f"neighbors: {table!r} is a keyed leaf table — its nodes carry no embedding, "
                "so they have no neighborhood; find them by their key (find)."
            )
        emb = store.read(EMBEDDINGS_TABLE, where="node_id = %s",
                         params=(node_id,), conn=own)
        if not emb:
            raise WalkRefused(
                f"neighbors: node {node_id!r} has no embedding — a ghost has no "
                "neighborhood (an empty [] would claim 'isolated', which is a different fact)."
            )
        ranked = nearest([float(x) for x in emb[0]["vector"]], k=k + 1, tree=tree,
                         table=table, conn=own)
        return [n for n in ranked if n["node_id"] != node_id][:k]
    finally:
        if conn is None:
            own.close()

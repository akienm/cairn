"""The librarian asks for the inference calls and keeps their answers (ticket 95f8c561e742).

Every resolved generate call the inference domain stored is an answer somebody paid for, and
until this module nothing carried it into the shared node set: the answer sat in
``inference_calls`` and no walk could reach it. ``ingest`` closes that gap from the
librarian's side. It ASKS for the calls (the inference domain's ``calls`` bus verb, ticket
b905340f8162) and deposits each resolved answer through the deposit door, so the domain never
learns who reads its calls or why (RULE 1 — the asker asks).

The bus and the embedder arrive as callables, so this module imports neither the bus nor the
inference domain; the device's ``ingest`` verb is what wires them. Nothing here runs on a
clock: an ``ingest`` ask is the event (D-c).

Idempotent on ``call_id``. The calls table has no id column, so a call's id is derived from
the two fields that make the row: its canonical request and its created time. A call already
carried — as a node's own provenance, or as an attestation on a node its answer duplicated —
is skipped, so a second ingest writes nothing at all. The high-water ``since`` is read back
from those same nodes, never from a file of its own.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from cairn.devices.db_domain.tools.client import store
from cairn.devices.librarian.tools.trees.trees import NODES_TABLE, DepositRefused, deposit

SOURCE = "inference_calls"
TABLE = "librarian_inference_calls"
TREE = "inference_calls"
LIMIT = 1000


def call_id(row: dict) -> str:
    """A call's id: the calls table carries none, so it is derived from canonical + created."""
    return hashlib.sha256(f"{row['canonical']}|{row['created']}".encode()).hexdigest()[:16]


def answer_text(row: dict) -> str | None:
    """The answer a resolved call carries, or None: only a 'miss' the host answered with a
    non-empty response is resolved. A 'hit' re-serves an answer carried at its miss, a
    'refused' row has none, and an embed row carries a vector, not text."""
    if row.get("verdict") != "miss":
        return None
    answer = row.get("answer")
    body = answer.get("body") if isinstance(answer, dict) else None
    text = body.get("response") if isinstance(body, dict) else None
    return text if isinstance(text, str) and text.strip() else None


def _when(stamp) -> datetime:
    at = stamp if isinstance(stamp, datetime) else datetime.fromisoformat(str(stamp))
    return at if at.tzinfo else at.replace(tzinfo=timezone.utc)


def _carried(conn) -> dict[str, str]:
    """{call_id: call_created} for every call already in the node set, own or attested."""
    rows = store.read(
        NODES_TABLE,
        where="provenance->>'source' = %s OR provenance->'attestations' @> %s::jsonb",
        params=(SOURCE, json.dumps([{"source": SOURCE}])), conn=conn)
    carried: dict[str, str] = {}
    for r in rows:
        prov = r["provenance"] or {}
        for p in [prov, *(prov.get("attestations") or [])]:
            if isinstance(p, dict) and p.get("source") == SOURCE and p.get("call_id"):
                carried[p["call_id"]] = p.get("call_created") or ""
    return carried


def ingest(ask, embed, *, table: str = TABLE, conn=None) -> dict:
    """Ask for the calls since the newest one carried; deposit each resolved answer once.

    ``ask(body) -> {'calls': [...]}`` is the inference domain's ``calls`` verb;
    ``embed(text) -> list[float]`` is one embed through the inference door. Returns
    ``{'asked', 'deposited', 'skipped': {'unresolved', 'already', 'refused'}}``."""
    own = conn or store.connect()
    try:
        carried = _carried(own)
        stamps = [s for s in carried.values() if s]
        body = {"limit": LIMIT}
        if stamps:
            body["since"] = max(stamps, key=_when)
        calls = ask(body)["calls"]
        result = {"asked": len(calls), "deposited": 0,
                  "skipped": {"unresolved": 0, "already": 0, "refused": 0}}
        for row in calls:
            text = answer_text(row)
            if text is None:
                result["skipped"]["unresolved"] += 1
                continue
            cid = call_id(row)
            if cid in carried:
                result["skipped"]["already"] += 1
                continue
            try:
                deposit(text, embed(text),
                        {"source": SOURCE, "call_id": cid, "call_created": str(row["created"])},
                        tree=TREE, table=table, conn=own)
            except DepositRefused:
                result["skipped"]["refused"] += 1
                continue
            carried[cid] = str(row["created"])
            result["deposited"] += 1
        return result
    finally:
        if conn is None:
            own.close()

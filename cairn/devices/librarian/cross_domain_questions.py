"""librarian/cross_domain_questions.py — the cross-domain question corpus, and its planting.

The librarian owns the cross-domain questions (outline 4.3.1.11; ticket 2248911aaf05). Akien,
2026-11-05 (open-6f41eecaf09d): "if a device owns a question, it's also kind of a delegate,
because all knowledge belongs ultimately to the librarian" and "right, these are
cross-domain-questions. a special kind."

The corpus is the git JSON beside this file, ``cross_domain_questions.json``. Every question is
marked ``origin``: ``verbatim`` means Akien's own words, character for character, and carries
who said it, when and where. ``proposed`` means somebody else's wording, never passed off as his.

- ``load(path=None)`` validates the corpus and returns it. A corpus that is wrong raises
  ``CorpusRefused`` naming EVERY lack in one pass.
- ``plant(table=..., conn=None)`` plants it as a keyed question tree: one keyed leaf per
  question, found by its id. No embedding: a question is found by its key, and its ANSWERS are
  what get embedded (4.3.1.11.2). Each consecutive pair of each known sequence is linked, the
  earlier question as source_id. Idempotent.

    python3 -m cairn.devices.librarian.cross_domain_questions plant
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "cross_domain_questions.json"
TABLE = "librarian_cross_domain_questions"
ORIGINS = ("verbatim", "proposed")


class CorpusRefused(ValueError):
    """The corpus is malformed; the message names every lack found, in one pass."""


def _lacks(doc) -> list[str]:
    if not isinstance(doc, dict):
        return [f"the corpus is a {type(doc).__name__}, not an object"]
    lacks: list[str] = []
    qs = doc.get("questions")
    if not isinstance(qs, list) or not qs:
        lacks.append("no questions list")
        qs = []
    seen: set[str] = set()
    for i, q in enumerate(qs):
        if not isinstance(q, dict):
            lacks.append(f"question {i} is not an object")
            continue
        qid = q.get("id")
        where = f"question {qid or i}"
        if not isinstance(qid, str) or not qid.strip():
            lacks.append(f"{where} has no id")
        elif qid in seen:
            lacks.append(f"duplicate id {qid}")
        else:
            seen.add(qid)
        if not isinstance(q.get("question"), str) or not q["question"].strip():
            lacks.append(f"{where} has no question text")
        origin = q.get("origin")
        if origin not in ORIGINS:
            lacks.append(f"{where} has origin {origin!r}, not one of {ORIGINS}")
        if origin == "verbatim":
            for field in ("said_by", "date", "source"):
                if not isinstance(q.get(field), str) or not q[field].strip():
                    lacks.append(f"{where} is verbatim without {field}")
    seqs = doc.get("sequences", [])
    if not isinstance(seqs, list):
        lacks.append("sequences is not a list")
        seqs = []
    for s in seqs:
        name = s.get("name") if isinstance(s, dict) else None
        order = s.get("order") if isinstance(s, dict) else None
        if not isinstance(order, list):
            lacks.append(f"sequence {name!r} has no order")
            continue
        for qid in order:
            if qid not in seen:
                lacks.append(f"sequence {name!r} names {qid!r}, which resolves to no question")
    return lacks


def load(path: Path | str | None = None) -> dict:
    """The validated corpus. Raises CorpusRefused naming every lack at once."""
    p = Path(path) if path is not None else CORPUS
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CorpusRefused(f"{p}: unreadable ({type(exc).__name__}: {exc})") from exc
    lacks = _lacks(doc)
    if lacks:
        raise CorpusRefused(f"{p}: " + "; ".join(lacks))
    return doc


def plant(*, table: str = TABLE, path: Path | str | None = None, conn=None) -> dict:
    """Plant the corpus as a keyed tree in ``table`` and link its sequences followed-by.
    Returns ``{planted, links}``: the questions deposited and the links written. Idempotent:
    a second plant lands no new leaf and no new link."""
    from cairn.devices.db_domain.tools.client import store
    from cairn.devices.librarian.tools.trees import trees

    doc = load(path)
    own = conn or store.connect()
    try:
        trees.ensure_trees(table=table, owner="librarian", keyed=True, conn=own)
        node: dict[str, str] = {}
        for q in doc["questions"]:
            prov = {"source": f"cross_domain_questions.json#{q['id']}", "origin": q["origin"],
                    "said_by": q.get("said_by", "")}
            r = trees.deposit_keyed(q["question"], q["id"], prov, table=table,
                                    meta={"function": q.get("function", ""), "origin": q["origin"]},
                                    conn=own)
            node[q["id"]] = r["node_id"]
        links = 0
        for s in doc.get("sequences", []):
            for a, b in zip(s["order"], s["order"][1:]):
                trees.link(node[a], node[b], 1.0, conn=own)
                links += 1
        return {"planted": len(node), "links": links}
    finally:
        if conn is None:
            own.close()


def main(argv: list[str]) -> int:
    if argv[:1] == ["plant"]:
        print(json.dumps(plant()))
        return 0
    doc = load()
    print(json.dumps({"questions": len(doc["questions"]), "sequences": len(doc.get("sequences", []))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

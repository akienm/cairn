"""The migration — every question Akien answered before the question door existed, copied into
the corpus through ``question.migrate`` (ticket d23356c26e7d).

Akien, 2026-09-15: *"once all this stuff is stable, everything we can push through it, we do."*
His answer to the population question (open-de25b82c3ced, 2026-09-29): *"yes B"* — the rulings,
the ticket decision lines citing him, AND the chat-log answers that never got a record.

THREE SOURCES, each read deterministically, each a translation that names its original:

- RULINGS — ``decisions/*.json`` carrying ``the_ruling_verbatim``. Bound to the one ticket the
  ruling names (the first named, in text order, when it names several — the rest ride
  ``tickets_named``), else to the ruling's own id. The answer is his words: a string verbatim, a
  list joined by newlines. ``decisions/`` is read, never written (9adc6fddf185).
- DECISION LINES — a ticket's ``decisions[]`` line whose ``by`` names Akien. One that already
  cites an ``open-*`` record in the corpus is linked to it, not copied twice; one reading
  *"CC's call, per Akien"* is CC answering under his standing delegation, not his answer, and is
  counted out; one with his words quoted (``"..."``, ``'...'``, ``“...”``) is copied, answer =
  the quoted phrases verbatim. Either way the line gains ``question: open-…`` beside ``by``.
  A line naming him with no words to carry is counted out as ``no_words``.
- CHAT — a Claude Code transcript turn where CC's final text ended in a question and the next
  turn is his typed string. Question = the last sentence of CC's text ending in '?', answer =
  his string verbatim, bound to the one ticket CC's text named, else ``chat:<session>``. Counted
  out, never copied into git: a reply carrying a secret-shaped token (``secret_shaped``), a pair
  about the CC0AC weather project that shares the transcript folder (``other_project`` — its
  house details stay out of committed files, and a pasted mail or post is someone else's
  words), and a "reply" that is a command echo or system tag (``not_typed``).

The migration is idempotent: ``question.migrate`` refuses nothing it already holds (ticket +
source), so a second run writes 0 records.

    python3 -m cairn.tools.question.migrate [--census] [--transcripts DIR]

``--census`` writes nothing, prints per source what stands outside the corpus, and exits 1 while
anything does — the verdict's instrument.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from cairn.tools.artifact import artifact as door
from cairn.tools.base.ticket_file import read_ticket, rewrite_ticket
from cairn.tools.question import question as Q

TICKET_ID = re.compile(r"\b[0-9a-f]{12}\b")
QUESTION_ID = re.compile(r"\bopen-[0-9a-f]{12}\b")
DATE = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")
DELEGATED = re.compile(r"CC's call, per Akien", re.I)
QUOTED = re.compile(r'"([^"\n]{3,}?)"|“([^”]{3,}?)”|(?<![A-Za-z])\'([^\'\n]{3,}?)\'(?![A-Za-z])')
SECRET = re.compile(r"(?i)\b(pass(word|wd)?|token|secret|api[_-]?key)\s*[:=]\s*\S+"
                    r"|\b(sk|ghp|gho|xox[bp])[-_][A-Za-z0-9_-]{16,}|\b[A-Za-z0-9+/_-]{40,}\b")
# The CC0AC weather project shares this transcript folder and is not Cairn: its house details
# stay out of committed files, and a pasted mail or Reddit post is someone else's words.
OTHER_PROJECT = re.compile(r"(?i)cc0ac|weather|acurite|dayenu|reddit|akienpi|kiosk|play store|gmail|\bmail\b")
SENTENCE = re.compile(r"(?<=[.!?])\s+")
DEFAULT_TRANSCRIPTS = Path.home() / ".claude" / "projects" / "-home-akien-dev-src-cairn"


def _commons() -> Path:
    return door.roots()["CairnCommons"]


def _ticket_ids(commons: Path) -> set[str]:
    return {p.name[:12] for p in (commons / "tickets").glob("*.json") if TICKET_ID.fullmatch(p.name[:12])}


def _plans(commons: Path) -> list[Path]:
    return sorted(p for p in (commons / "tickets").glob("*.json")
                  if TICKET_ID.fullmatch(p.name[:12]) and not p.name.endswith(".state.json"))


def _named(text: str, ids: set[str]) -> list[str]:
    out: list[str] = []
    for m in TICKET_ID.findall(text):
        if m in ids and m not in out:
            out.append(m)
    return out


# ── rulings ───────────────────────────────────────────────────────────────────────────────

def rulings(commons: Path) -> list[dict]:
    """One migrate() argument set per ruling carrying the_ruling_verbatim."""
    ids, out = _ticket_ids(commons), []
    for p in sorted((commons / "decisions").glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict) or not d.get("the_ruling_verbatim"):
            continue
        words = d["the_ruling_verbatim"]
        answer = words if isinstance(words, str) else "\n".join(str(w) for w in words)
        named = _named(p.read_text(encoding="utf-8"), ids)
        rid = str(d.get("id") or p.stem)
        asked = d.get("question")
        if not (isinstance(asked, str) and asked.strip().endswith("?")):
            topic = d.get("title") or re.sub(r"^\d{4}-\d\d-\d\d-", "", rid).replace("-", " ")
            asked = f"What is the ruling on: {topic}?"
        extra = {"migrated_from": "ruling"}
        if len(named) > 1:
            extra["tickets_named"] = named
        if d.get("confirmation_verbatim"):
            extra["confirmation"] = d["confirmation_verbatim"]
        date = str(d.get("date"))
        out.append(dict(ticket=named[0] if named else rid, question=asked, answer_words=answer,
                        date=date, answered_at=date, source=f"decisions/{p.name}",
                        raised_by=str(d.get("recorded_by") or "CC"),
                        answered_by=str(d.get("ruled_by") or "Akien"), extra=extra))
    return out


# ── decision lines ────────────────────────────────────────────────────────────────────────

def decision_lines(commons: Path, corpus: set[str]) -> list[dict]:
    """Every decisions[] line whose ``by`` names Akien, classified. Each item: {plan, index,
    kind: linked|delegated|no_words|copy|done, args (copy only), qid (linked/done)}."""
    out = []
    for plan in _plans(commons):
        try:
            doc = json.loads(plan.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for i, line in enumerate(doc.get("decisions") or []):
            if not isinstance(line, dict) or "akien" not in str(line.get("by", "")).lower():
                continue
            by, text = str(line.get("by", "")), str(line.get("text", ""))
            item = {"plan": plan, "index": i, "ticket": plan.name[:12]}
            have = line.get("question")
            cited = [q for q in QUESTION_ID.findall(by + " " + text) if q in corpus]
            if isinstance(have, str) and have in corpus:
                item.update(kind="done", qid=have)
            elif cited:
                item.update(kind="linked", qid=cited[0])
            elif DELEGATED.search(by):
                item.update(kind="delegated")
            else:
                said = [next(g for g in m.groups() if g) for m in QUOTED.finditer(by)] or \
                       [next(g for g in m.groups() if g) for m in QUOTED.finditer(text)]
                if not said:
                    item.update(kind="no_words")
                else:
                    n = line.get("n", i + 1)
                    when = (DATE.findall(by) or DATE.findall(text) or [str(doc.get("date") or "")])[0]
                    item.update(kind="copy", args=dict(
                        ticket=item["ticket"],
                        question=f"{text.strip().rstrip('.')} — is that the decision?",
                        answer_words="\n".join(said), date=when, answered_at=when,
                        source=f"tickets/{plan.name}#D{n}", raised_by="CC",
                        extra={"migrated_from": "ticket decision line", "by": by}))
            out.append(item)
    return out


def _set_line_question(item: dict, qid: str) -> None:
    doc = read_ticket(item["plan"])
    line = doc["decisions"][item["index"]]
    if line.get("question") == qid:
        return
    line["question"] = qid
    rewrite_ticket(item["plan"], doc, verb="cast",
                   why=f"decision line {item['index'] + 1} names the corpus record {qid} (d23356c26e7d)")


# ── chat ──────────────────────────────────────────────────────────────────────────────────

def _assistant_text(entry: dict) -> str:
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    return "".join(c.get("text", "") for c in content or [] if isinstance(c, dict) and c.get("type") == "text")


def chat_pairs(transcripts: Path, ids: set[str]) -> tuple[list[dict], dict]:
    """(migrate() argument sets, {reason: count} for the pairs counted out)."""
    out, counted_out = [], {"secret_shaped": 0, "other_project": 0, "not_typed": 0}
    for log in sorted(transcripts.glob("*.jsonl")) if transcripts.is_dir() else []:
        last = ""
        for raw in log.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                e = json.loads(raw)
            except ValueError:
                continue
            if e.get("type") == "assistant":
                t = _assistant_text(e)
                if t.strip():
                    last = t
                continue
            if e.get("type") != "user":
                continue
            said = (e.get("message") or {}).get("content")
            if not isinstance(said, str):
                continue  # a tool result rides a user turn; it is not his reply
            asked, last = last.strip(), ""
            if not asked.endswith("?") or not said.strip():
                continue
            if said.lstrip().startswith("<"):
                counted_out["not_typed"] += 1  # a command's echo or a system tag, not his reply
                continue
            if SECRET.search(said):
                counted_out["secret_shaped"] += 1
                continue
            if OTHER_PROJECT.search(asked + "\n" + said):
                counted_out["other_project"] += 1
                continue
            sentences = [s.strip() for ln in asked.splitlines() for s in SENTENCE.split(ln)]
            question = next(s for s in reversed(sentences) if s.endswith("?"))
            named = _named(asked, ids)
            when = str(e.get("timestamp") or "")
            out.append(dict(ticket=named[0] if len(named) == 1 else f"chat:{log.stem}",
                            question=question, answer_words=said, date=when[:10], answered_at=when,
                            source=f"chat:{log.stem}#{e.get('uuid')}", raised_by="CC (chat)",
                            extra={"migrated_from": "chat"}))
    return out, counted_out


# ── the run ───────────────────────────────────────────────────────────────────────────────

def _corpus(root: Path | str | None) -> list[dict]:
    return Q._all(root)


def run(*, transcripts: Path | None = DEFAULT_TRANSCRIPTS, root: Path | str | None = None,
        write: bool = True) -> dict:
    """Migrate (or, ``write=False``, census) every source. Returns per-source counts:
    ``outside`` is what stands outside the corpus BEFORE this call; ``wrote`` what it wrote."""
    commons = _commons()
    held = _corpus(root)
    by_source = {(q.get("ticket"), q.get("source")) for q in held}
    ids = _ticket_ids(commons)
    report: dict = {}

    rs = rulings(commons)
    todo = [a for a in rs if (a["ticket"], a["source"]) not in by_source]
    report["rulings"] = {"population": len(rs), "outside": len(todo), "wrote": 0}
    if write:
        report["rulings"]["wrote"] = sum(Q.migrate(**a, root=root)["migrated"] for a in todo)

    lines = decision_lines(commons, {q.get("id") for q in held})
    kinds = {k: sum(1 for x in lines if x["kind"] == k)
             for k in ("copy", "linked", "done", "delegated", "no_words")}
    outside = sum(1 for x in lines if x["kind"] in ("copy", "linked"))
    report["decision_lines"] = {"population": len(lines), "outside": outside, **kinds, "wrote": 0}
    if write:
        wrote = 0
        for x in lines:
            if x["kind"] == "copy":
                rec = Q.migrate(**x["args"], root=root)
                wrote += rec["migrated"]
                _set_line_question(x, rec["id"])
            elif x["kind"] == "linked":
                _set_line_question(x, x["qid"])
        report["decision_lines"]["wrote"] = wrote

    pairs, counted_out = chat_pairs(transcripts, ids) if transcripts else ([], {})
    todo = [a for a in pairs if (a["ticket"], a["source"]) not in by_source]
    report["chat"] = {"population": len(pairs), "outside": len(todo), **counted_out, "wrote": 0}
    if write:
        report["chat"]["wrote"] = sum(Q.migrate(**a, root=root)["migrated"] for a in todo)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m cairn.tools.question.migrate")
    ap.add_argument("--census", action="store_true", help="write nothing; print what stands outside")
    ap.add_argument("--transcripts", type=Path, default=DEFAULT_TRANSCRIPTS)
    a = ap.parse_args(argv)
    report = run(transcripts=a.transcripts, write=not a.census)
    print(json.dumps(report, indent=1))
    # a census is an instrument: it exits 1 while anything stands outside the corpus
    return 1 if a.census and any(v["outside"] for v in report.values()) else 0


if __name__ == "__main__":
    sys.exit(main())

"""The question door — a decision Akien has to make is a QUESTION bound to the ticket that
needs it, standing in his inbox until answered; the answer IS the decision.

Akien, 2026-09-14 (ideas/2026-09-14-why-are-we-still-doing-rulings-we): *"what was the ruling
should now be part of the ticketing or intention recording process. slash sorted should lead
to questions, and if i can't answer then right then, for whatever reason, they become open
questions in the inbox. and yes, the answer to the question is the decision... ASSUMING THE
ANSWER DOES NOT LEAD TO YET MORE QUESTIONS. If the answer does, we keep going around until you
have all the answers you need."*

THE STORE is the open lane that already existed (ruled 2026-08-01, edges become open
questions): ``CairnCommons/questions/open-<id>.json``, read by the operator inbox and the
frontier projector. This tool is that lane's door — the one writer, riding the artifact door
(verbs ``question`` and ``answer``) so every open and every answer is journaled with its
caller's cgroup class. A record:

    {id, date, ticket, question, why_it_blocks, raised_by, born_of, source,
     resolved, answer, answered_by, answered_at, follow_ups}

THE LOOP is the ``follow_ups``: an answer may bear more questions, each opened ``born_of``
the one it came from and bound to the same ticket, unresolved until answered in turn. The
exit condition is not here — it is the BUILDME crossing gate
(``build_inspector.buildme_has_no_open_questions``): a ticket with an unresolved question
citing it does not cross. "Until you have all the answers you need" as physics.

WHO ANSWERS. Akien answers in chat and CC records it (caller class ``cc``, the words his),
or he runs ``cairn question answer`` from his own shell (caller class ``akien``); both are
accepted and the class rides the record and the journal (his answer to open-690330e1cfa6:
"yes it can come via chat ... those are all fine").

    cairn question open --ticket <id> "<question>" --why "<what it blocks>" [--born-of <qid>]
    cairn question answer <qid> "<his words>" [--follow-up "<question>" ...]
    cairn question list [<ticket>]
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.artifact import artifact as door
from cairn.tools.base.address import ROOTS

QUESTIONS_DIR = Path(os.environ.get("CAIRN_QUESTIONS_DIR", ROOTS["commons"] / "questions"))
PREFIX = "open-"


class Refused(ValueError):
    """The door refuses — every lack named, nothing written."""


def _dir(root: Path | str | None) -> Path:
    return Path(root) if root is not None else QUESTIONS_DIR


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _path(qid: str, root: Path | str | None = None) -> Path:
    qid = qid if qid.startswith(PREFIX) else PREFIX + qid
    return _dir(root) / f"{qid}.json"


def _write(path: Path, record: dict, *, verb: str, why: str) -> None:
    door.write(str(path), json.dumps(record, indent=2, ensure_ascii=False) + "\n",
               verb=verb, why=why)


def read(qid: str, root: Path | str | None = None) -> dict:
    p = _path(qid, root)
    if not p.exists():
        raise Refused(f"no question {qid!r} under {p.parent}")
    return json.loads(p.read_text(encoding="utf-8"))


def open_question(ticket: str, question: str, why_it_blocks: str, *,
                  raised_by: str | None = None, born_of: str | None = None,
                  source: str | None = None, root: Path | str | None = None) -> dict:
    """Open one question against a ticket. Returns the record as written."""
    lacks = []
    if not (isinstance(ticket, str) and ticket.strip()):
        lacks.append("ticket: the id of the ticket or intention this question is bound to")
    if not (isinstance(question, str) and question.strip().endswith("?")):
        lacks.append("question: a question ends with '?' — a statement is not one")
    if not (isinstance(why_it_blocks, str) and why_it_blocks.strip()):
        lacks.append("why_it_blocks: what the build cannot settle without the answer")
    if born_of is not None and not _path(born_of, root).exists():
        lacks.append(f"born_of: {born_of!r} is not a question under {_dir(root)}")
    if lacks:
        raise Refused("question refused — " + "; ".join(lacks))
    qid = PREFIX + uuid.uuid4().hex[:12]
    who = door.caller()
    record = {
        "id": qid, "date": _now()[:10], "ticket": ticket.strip(),
        "question": question.strip(), "why_it_blocks": why_it_blocks.strip(),
        "raised_by": raised_by or f"{who['class']} ({who.get('unit') or who.get('cgroup')})",
        "born_of": born_of if born_of is None else (born_of if born_of.startswith(PREFIX) else PREFIX + born_of),
        "source": source, "resolved": False,
        "answer": None, "answered_by": None, "answered_at": None, "follow_ups": [],
    }
    _write(_path(qid, root), record, verb="question",
           why=f"question for Akien bound to {ticket}" + (f", born of {born_of}" if born_of else ""))
    return record


def answer(qid: str, words: str, *, follow_ups: list[str] | tuple[str, ...] = (),
           follow_up_why: str | None = None, root: Path | str | None = None) -> dict:
    """Record his answer verbatim; open each follow-up born of this one on the same ticket.

    The answer resolves THIS question. The follow-ups are new open questions — the loop
    goes around again, and the ticket stays short of BUILDME until they are answered too.
    """
    if not (isinstance(words, str) and words.strip()):
        raise Refused("answer refused — the answer is his words, verbatim, and they are empty")
    record = read(qid, root)
    if record.get("resolved"):
        raise Refused(f"answer refused — {record['id']} is already answered "
                      f"({record.get('answered_at')}); a second answer is a new question")
    who = door.caller()
    born = []
    for q in follow_ups:
        child = open_question(record["ticket"], q,
                              follow_up_why or f"born of the answer to {record['id']}",
                              born_of=record["id"], source=record.get("source"), root=root)
        born.append(child["id"])
    record.update({
        "resolved": True, "answer": words.strip(),
        "answered_by": f"Akien, recorded by caller class {who['class']}",
        "answered_at": _now(), "follow_ups": born,
    })
    _write(_path(record["id"], root), record, verb="answer",
           why=f"Akien answered {record['id']}" +
               (f"; {len(born)} follow-up(s) born" if born else "; no follow-ups"))
    return record


def _all(root: Path | str | None = None) -> list[dict]:
    d = _dir(root)
    out = []
    for p in sorted(d.glob(f"{PREFIX}*.json")) if d.exists() else []:
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            # Law 7: an unreadable question counts as UNRESOLVED — it cannot be read as answered.
            out.append({"id": p.stem, "ticket": None, "question": "UNREADABLE — counts as unresolved",
                        "resolved": False, "unreadable": True})
    return out


def open_for(ticket: str, root: Path | str | None = None) -> list[dict]:
    """Every unresolved question citing the ticket — what the BUILDME gate reads."""
    return [q for q in _all(root) if not q.get("resolved") and q.get("ticket") == ticket]


def list_open(root: Path | str | None = None) -> list[dict]:
    return [q for q in _all(root) if not q.get("resolved")]


def render(records: list[dict]) -> str:
    """One line per question for a human: the id, the ticket, and the question itself —
    the inbox renders the same shape (the operator reads the question, not its id)."""
    lines = []
    for q in records:
        head = f"{q.get('id', '?')}  [{q.get('ticket') or '-'}]"
        lines.append(f"{head}  {q.get('question', '')}")
        if q.get("born_of"):
            lines.append(f"{' ' * len(head)}  born of {q['born_of']}")
        if q.get("resolved"):
            lines.append(f"{' ' * len(head)}  answered {q.get('answered_at')}: {q.get('answer')}")
    return "\n".join(lines)

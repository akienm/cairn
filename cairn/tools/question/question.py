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
     resolved, answer, answered_by, answered_at, spawned}

THE LINK HAS TWO STORED ENDS (ticket bc7b64626405, Akien 2026-09-14: *"if a question is
about a ticket, it should have a bidirectional link"*). ``open_question`` writes the question
AND, in the same act, appends the id to the ticket file's ``questions`` list through the
door's ``cast`` verb — ``_ticket_file`` finds the ticket by id prefix under the commons
``tickets/`` root (the ``transitions._find_ticket`` shape, over ``door.roots()`` so a proof's
scratch world holds). No ticket file — a question bound to an intent berth path before
/sorted has cast, or a fixture with no tickets — writes the question side only, and
``rebind`` moves it onto the id once the cast exists. Only ``open-*`` strings in a ticket's
``questions`` are links; the 129 tickets carrying ``{q, a}`` prose pairs there are not.
The build inspector's ``question_links_agree`` sieve reds the two ends disagreeing.

THE LOOP is the ``spawned``: an answer may bear more questions, each opened ``born_of`` the
one it came from and bound to the same ticket, unresolved until answered in turn. The field
is REQUIRED — ``[]`` is the recorded claim "this answer spawned nothing", and an answer that
does not say is refused (his words: *"we should explicitly say 'and the answer spawned x, y
and z new questions' in some jsonic way that's not prose"* — a default ``[]`` made "nothing"
and "nobody thought about it" read the same). A pre-build record (before 2026-09-14)
carries the field as ``follow_ups`` (pre-2026-09-14); readers accept either. The exit condition is not here — it is the
BUILDME crossing gate (``build_inspector.buildme_has_no_open_questions``): a ticket with an
unresolved question citing it does not cross. "Until you have all the answers you need" as
physics.

WHO ANSWERS. Akien answers in chat and CC records it (caller class ``cc``, the words his),
or he runs ``cairn question answer`` from his own shell (caller class ``akien``); both are
accepted and the class rides the record and the journal (his answer to open-690330e1cfa6:
"yes it can come via chat ... those are all fine").

    cairn question open --ticket <id> "<question>" --why "<what it blocks>" [--born-of <qid>]
    cairn question answer <qid> "<his words>" --spawned none | --spawned "<question>" ...
    cairn question answer <qid> "<the finding>" --measured <record> --spawned none
    cairn question rebind <ticket-id>        questions bound to the ticket's intent berth → the id
    cairn question list [<ticket>]           open questions; for one ticket, its whole tree
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


def _ticket_file(ticket: str) -> Path | None:
    """The ticket file an id names, or None. ``<commons>/tickets/<id>-*.json`` by id prefix —
    the ``transitions._find_ticket`` shape — over the door's roots, so the scratch world a
    proof hands the door is the world this reads. A berth path, a bare word, or an id with no
    file resolve to None: that is a real answer (the question side alone is written)."""
    if not isinstance(ticket, str) or not ticket or "/" in ticket:
        return None
    commons = door.roots().get("CairnCommons")
    if commons is None:
        return None
    tdir = commons / "tickets"
    exact = tdir / f"{ticket}.json"
    if exact.exists():
        return exact
    hits = sorted(tdir.glob(f"{ticket}-*.json")) if tdir.exists() else []
    return hits[0] if len(hits) == 1 else None


def _link_to_ticket(ticket: str, qid: str, *, why: str) -> Path | None:
    """The ticket-side end of the link: the ticket's ``questions`` gains ``qid`` through the
    door's ``cast`` verb. A list appends (idempotent); a ``"none, because ..."`` string or
    None becomes ``[qid]``; ``{q, a}`` prose entries already in a list are left alone.
    Returns the ticket path written, or None when no ticket file exists."""
    tk = _ticket_file(ticket)
    if tk is None:
        return None
    doc = json.loads(tk.read_text(encoding="utf-8"))
    have = doc.get("questions")
    if isinstance(have, list):
        if qid in have:
            return tk
        have = list(have) + [qid]
    else:
        have = [qid]
    doc["questions"] = have
    door.write(str(tk), json.dumps(doc, indent=2, ensure_ascii=False) + "\n", verb="cast", why=why)
    return tk


def links_of(doc: dict) -> list[str]:
    """The question ids a ticket document links — only ``open-*`` strings count."""
    have = doc.get("questions")
    if not isinstance(have, list):
        return []
    return [x for x in have if isinstance(x, str) and x.startswith(PREFIX)]


def spawned_of(record: dict) -> list[str]:
    """The ids an answer spawned; pre-2026-09-14 records say ``follow_ups``."""
    have = record.get("spawned")
    if have is None:
        have = record.get("follow_ups")  # pre-2026-09-14 records
    return [x for x in (have or []) if isinstance(x, str)]


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
        "answer": None, "answered_by": None, "answered_at": None, "spawned": None,
    }
    why = f"question for Akien bound to {ticket}" + (f", born of {born_of}" if born_of else "")
    _write(_path(qid, root), record, verb="question", why=why)
    # the other end, in the same act — a question about a ticket is named by the ticket
    _link_to_ticket(record["ticket"], qid, why=f"{qid} opened: {why}")
    return record


def answer(qid: str, words: str, *, spawned: list[str] | tuple[str, ...] | None = None,
           spawned_why: str | None = None, measured: str | None = None,
           root: Path | str | None = None) -> dict:
    """Record his answer verbatim, and what it spawned; open each spawned question born of
    this one on the same ticket.

    ``measured`` is the OTHER answerer: a record on disk that settles the question. Law 9
    (ruling 2026-08-15): *"anything settled by measurment trumps approvals by even me"* —
    so a measurement closes a question without his gate, and the record says so:
    ``answered_by`` reads ``measurement: <record>``, never "Akien", and ``words`` are the
    finding in the recorder's words, not his. The record must exist when the answer is
    written — a citation of nothing is a claim, not a measurement (Law 3).

    ``spawned`` is REQUIRED: ``[]`` records that the answer bore nothing; a list of questions
    opens each and records their ids. None is refused — an answer that does not say what it
    spawned is not a recorded claim, and the sieve cannot inspect a silence. The answer
    resolves THIS question; the spawned ones are new open questions — the loop goes around
    again, and the ticket stays short of BUILDME until they are answered too.
    """
    lacks = []
    if not (isinstance(words, str) and words.strip()):
        lacks.append("the answer is his words, verbatim, and they are empty")
    if spawned is None or not isinstance(spawned, (list, tuple)):
        lacks.append("spawned: [] (this answer bore no new question) or the questions it bore "
                     "— an answer says what it spawned, or it is not recorded")
    elif any(not (isinstance(q, str) and q.strip().endswith("?")) for q in spawned):
        lacks.append("spawned: each entry is a question and ends with '?'")
    if measured is not None and not (isinstance(measured, str) and measured.strip()
                                     and Path(measured).expanduser().is_file()):
        lacks.append(f"measured: {measured!r} is not a record on disk — a measurement "
                     "answers by citing what it read")
    if lacks:
        raise Refused("answer refused — " + "; ".join(lacks))
    record = read(qid, root)
    if record.get("resolved"):
        raise Refused(f"answer refused — {record['id']} is already answered "
                      f"({record.get('answered_at')}); a second answer is a new question")
    who = door.caller()
    born = []
    for q in spawned:
        child = open_question(record["ticket"], q,
                              spawned_why or f"born of the answer to {record['id']}",
                              born_of=record["id"], source=record.get("source"), root=root)
        born.append(child["id"])
    record.pop("follow_ups", None)  # pre-2026-09-14 records
    by = f"measurement: {measured}" if measured else "Akien"
    record.update({
        "resolved": True, "answer": words.strip(),
        "answered_by": f"{by}, recorded by caller class {who['class']}",
        "answered_at": _now(), "spawned": born,
    })
    if measured:
        record["measured"] = measured
    _write(_path(record["id"], root), record, verb="answer",
           why=f"{'a measurement' if measured else 'Akien'} answered {record['id']}" +
               (f"; spawned {len(born)} question(s)" if born else "; spawned none"))
    return record


def rebind(ticket: str, root: Path | str | None = None) -> list[dict]:
    """Move every question bound to the ticket's intent berth path onto the ticket id, and
    write the ticket-side end for each. Fired at /sorted step 5, once the ticket file exists
    (charter edge (a): a question raised at /intent has no id yet — the berth path is the
    only name it can carry, and the cast is the moment the real name appears). Returns the
    records rebound; [] when the ticket carries no berth or nothing is bound to it."""
    tk = _ticket_file(ticket)
    if tk is None:
        raise Refused(f"rebind refused — no ticket file for {ticket!r} under {door.roots().get('CairnCommons')}/tickets")
    doc = json.loads(tk.read_text(encoding="utf-8"))
    berth = doc.get("intent_berth")
    if not isinstance(berth, str) or "/" not in berth:
        return []
    out = []
    for q in _all(root):
        if q.get("ticket") != berth or q.get("unreadable"):
            continue
        q["ticket"] = ticket
        _write(_path(q["id"], root), q, verb="question",
               why=f"{q['id']} rebound from intent berth to ticket {ticket} at /sorted")
        _link_to_ticket(ticket, q["id"], why=f"{q['id']} rebound to {ticket} at /sorted")
        out.append(q)
    return out


def _berth_of(ticket: str) -> str | None:
    tk = _ticket_file(ticket)
    if tk is None:
        return None
    try:
        berth = json.loads(tk.read_text(encoding="utf-8")).get("intent_berth")
    except (OSError, ValueError):
        return None
    return berth if isinstance(berth, str) and "/" in berth else None


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
    """Every unresolved question citing the ticket — what the BUILDME gate reads. A question
    still bound to the ticket's intent berth path (opened at /intent, not yet rebound) counts:
    the lane holds either way, and rebind only changes the name on the record."""
    names = {ticket}
    berth = _berth_of(ticket)
    if berth:
        names.add(berth)
    return [q for q in _all(root) if not q.get("resolved") and q.get("ticket") in names]


def for_ticket(ticket: str, root: Path | str | None = None) -> list[dict]:
    """Every question citing the ticket (or its intent berth), answered or not."""
    names = {ticket}
    berth = _berth_of(ticket)
    if berth:
        names.add(berth)
    return [q for q in _all(root) if q.get("ticket") in names]


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


def render_tree(records: list[dict], roots_ids: list[str] | None = None, indent: int = 0) -> str:
    """The questions as a tree: question → spawned → spawned. Each line carries the id,
    open|answered, and the question; an answered one shows its answer and what it spawned
    (``spawned: none`` when the recorded claim is []). ``roots_ids`` limits the top level to
    the ids a ticket links, in that order; otherwise every record with no parent is a root."""
    by_id = {q.get("id"): q for q in records}
    if roots_ids is None:
        roots_ids = [q["id"] for q in records if not q.get("born_of") or q["born_of"] not in by_id]
    out = []
    seen: set = set()

    def walk(qid: str, depth: int) -> None:
        pad = "  " * (indent + depth)
        q = by_id.get(qid)
        if q is None:
            out.append(f"{pad}{qid}  MISSING — the link names a record that does not exist")
            return
        if qid in seen:
            return
        seen.add(qid)
        state = "answered" if q.get("resolved") else "OPEN"
        out.append(f"{pad}{qid}  [{state}]  {q.get('question', '')}")
        if q.get("resolved"):
            out.append(f"{pad}  answer: {q.get('answer')}")
            kids = spawned_of(q)
            if kids:
                out.append(f"{pad}  spawned:")
                for k in kids:
                    walk(k, depth + 2)
            elif "spawned" in q:
                out.append(f"{pad}  spawned: none")
            else:  # a pre-2026-09-14 record: follow_ups defaulted, nobody claimed "none"
                out.append(f"{pad}  spawned: unrecorded (answered before the claim was required)")

    for r in roots_ids:
        walk(r, 0)
    return "\n".join(out)

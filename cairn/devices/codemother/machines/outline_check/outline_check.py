"""The outline check — CodeMother's read of one ticket beside the component outline (ticket
6541ccd1594c; outline 10.3.5.1).

Akien, 2026-10-26: *"the reason we did all this was so you'll know if somebody files a ticket
without one of us investing the cognition to go look."* So the cheapest reader reads the
outline as it stands and the ticket, once, and names the outline lines the ticket touches and
the ones it contradicts. Everything after that read is deterministic: the numbers are resolved
against the parsed file (the line's text is always the FILE's, never the reader's), each
contradiction and each open [Q#n] in a touched section becomes one question bound to the
ticket through the question door (never twice), and every run leaves one record under
``<commons>/outline_checks/`` through the artifact door.

The outline is read on every run, never cached (D2): Akien edits it in place, and its line
numbers move after every round of edits — only the [Q#n] ids are stable.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from cairn.machines.rehearsal.rehearsal import MODEL, commons, ticket_file
from cairn.tools.artifact import artifact as door
from cairn.tools.question import question as Q

HERE = Path(__file__).resolve().parent
PROMPT_PATH = HERE / "prompt.md"
SCHEMA_PATH = HERE / "schema.json"
OUTLINE_NAME = "CairnComponentOutline.txt"
CLAUDE = os.environ.get("CAIRN_REHEARSAL_CLAUDE", "claude")
SOURCE = "outline_check"
READS = 2       # D6: a read that fails the schema is read once more, then the run is ran:false

ENTRY = re.compile(r"^\s*(\d+(?:\.\d+)*)\s+(\S.*)$")
TAGGED = re.compile(r"\[Q#(\d+):\s*(.*?)\]")
BARE = re.compile(r"\[Q#(\d+)\]")


# ---------------------------------------------------------------------------
# the outline, parsed (D3, D4)

def parse(text: str) -> list[dict]:
    """Every numbered entry as ``{'number', 'text'}``. A line starting with a dotted number
    starts an entry; each following unnumbered, non-blank line is joined onto it with one
    space. Lines before the first entry are not entries."""
    entries: list[dict] = []
    for line in text.splitlines():
        m = ENTRY.match(line)
        if m:
            entries.append({"number": m.group(1), "text": m.group(2).strip()})
        elif line.strip() and entries:
            entries[-1]["text"] += " " + line.strip()
    return entries


def open_questions(entries: list[dict]) -> list[dict]:
    """Every [Q#n] the outline carries, ``{'n', 'number', 'text'}``. A tagged ``[Q#n: text]``
    carries its own text; a bare ``[Q#n]`` asks the entry's own text, the marker removed. A
    marker without digits is not a question id."""
    out = []
    for e in entries:
        for m in TAGGED.finditer(e["text"]):
            out.append({"n": int(m.group(1)), "number": e["number"], "text": m.group(2).strip()})
        for m in BARE.finditer(e["text"]):
            out.append({"n": int(m.group(1)), "number": e["number"],
                        "text": BARE.sub("", e["text"]).strip()})
    return out


def section(number: str) -> str:
    """D8: the section of a number is its first two dot components."""
    return ".".join(number.split(".")[:2])


# ---------------------------------------------------------------------------
# the reader (D5, D6) — injectable, so a proof never reaches this one

def claude_reader(prompt_text: str, schema_doc: dict) -> tuple[dict | None, dict]:
    """One read through the claude CLI, the rehearsal's cheapest model, the prompt on stdin,
    CLAUDECODE unset so it runs outside this session. Returns ``(structured_output or None,
    meta)``; the machine validates the doc, this only fetches it."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    # Stripping CLAUDECODE takes the child out of the session, so it says whose hand it is
    # (ticket a135bdb13646): CAIRN_USER set is a machine, unset is Akien.
    env["CAIRN_USER"] = "outline_check"
    cmd = [CLAUDE, "-p", "--model", MODEL, "--output-format", "json", "--tools", "",
           "--json-schema", json.dumps(schema_doc)]
    try:
        r = subprocess.run(cmd, input=prompt_text, capture_output=True, text=True,
                           timeout=300, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, {"error": f"{type(exc).__name__}: {exc}", "model": MODEL}
    meta: dict = {"model": MODEL, "rc": r.returncode}
    try:
        env_doc = json.loads(r.stdout)
    except json.JSONDecodeError:
        meta["error"] = "envelope is not JSON: " + (r.stdout or r.stderr)[-300:]
        return None, meta
    meta.update({
        "cost_usd": env_doc.get("total_cost_usd"),
        "duration_ms": env_doc.get("duration_ms"),
        "is_error": env_doc.get("is_error"),
        "session_id": env_doc.get("session_id"),
    })
    if env_doc.get("is_error"):
        meta["error"] = str(env_doc.get("result"))[-300:]
        return None, meta
    doc = env_doc.get("structured_output")
    if doc is None and isinstance(env_doc.get("result"), str):
        try:
            doc = json.loads(env_doc["result"])
        except json.JSONDecodeError:
            meta["error"] = "no structured_output and result is not JSON"
    return doc, meta


def validate(doc) -> list[str]:
    """What the read lacks against schema.json, by hand. Empty is a valid read."""
    if not isinstance(doc, dict):
        return [f"the read is not an object: {type(doc).__name__}"]
    lacks = []
    if set(doc) != {"touches", "conflicts"}:
        lacks.append(f"keys are exactly touches and conflicts, not {sorted(doc)}")
    t = doc.get("touches")
    if not (isinstance(t, list) and all(isinstance(x, str) for x in t)):
        lacks.append("touches is a list of outline numbers as strings")
    c = doc.get("conflicts")
    if not isinstance(c, list):
        lacks.append("conflicts is a list")
    else:
        for i, x in enumerate(c):
            if not (isinstance(x, dict) and set(x) == {"number", "ticket_says", "why"}
                    and all(isinstance(v, str) for v in x.values())):
                lacks.append(f"conflicts[{i}] is exactly {{number, ticket_says, why}}, each a string")
    return lacks


def render(outline_text: str, ticket_text: str) -> str:
    return (PROMPT_PATH.read_text(encoding="utf-8").strip() + "\n\n=== OUTLINE ===\n"
            + outline_text + "\n=== TICKET ===\n" + ticket_text)


# ---------------------------------------------------------------------------
# the check (D7-D11)

def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def records_dir(root: Path | str | None = None) -> Path:
    return commons(root) / "outline_checks"


def _record_path(ticket: str, root, stamp: str) -> Path:
    path = records_dir(root) / f"{ticket}-{stamp}.json"
    n = 1
    while path.exists():   # two runs inside one second are two records, never one overwritten
        n += 1
        path = records_dir(root) / f"{ticket}-{stamp}-{n}.json"
    return path


def _conflict_q(ticket: str, c: dict) -> str:
    return (f'Ticket {ticket} says {c["ticket_says"]!r}, but outline {c["number"]} reads '
            f'"{c["text"]}" ({c["why"]}). Which stands, the ticket or the outline?')


def _open_q(ticket: str, o: dict) -> str:
    return (f'Ticket {ticket} touches outline section {o["section"]}, where Q#{o["n"]} stands '
            f'open: "{o["text"]}" What is the answer?')


def check(ticket: str, *, reader: Callable = claude_reader, root: Path | str | None = None) -> dict:
    """Read ``ticket`` beside the outline, open what stands, write the record. Returns
    ``{'path', 'record', 'qids'}`` — ``qids`` is each conflict's then each open question's
    question id, in record order (the record keeps D11's fields only)."""
    base = commons(root)
    outline_path = base / OUTLINE_NAME
    tk = ticket_file(ticket, root)
    if tk is None:
        raise door.Refused(f"no ticket {ticket!r} under {base / 'tickets'}")
    outline_bytes, ticket_bytes = outline_path.read_bytes(), tk.read_bytes()
    outline_text = outline_bytes.decode("utf-8")
    schema_doc = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    prompt_text = render(outline_text, ticket_bytes.decode("utf-8"))

    metas, lacks, doc = [], [], None
    for _ in range(READS):
        got, meta = reader(prompt_text, schema_doc)
        metas.append(meta)
        lacks = validate(got)
        if not lacks:
            doc = got
            break

    record = {"ticket": ticket, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "ran": doc is not None, "model": MODEL, "meta": metas,
              "outline_path": str(outline_path), "outline_sha256": _sha(outline_bytes),
              "ticket_sha256": _sha(ticket_bytes), "touches": [], "conflicts": [],
              "open_questions": [], "unresolved": [], "questions_opened": [],
              "questions_already_open": []}
    qids: list[str] = []
    if doc is None:
        record["lacks"] = lacks
    else:
        entries = parse(outline_text)
        text_of = {e["number"]: e["text"] for e in entries}
        unresolved: list[str] = []

        def resolves(n: str) -> bool:
            if n in text_of:
                return True
            if n not in unresolved:
                unresolved.append(n)
            return False

        for n in doc["touches"]:
            if resolves(n) and n not in [t["number"] for t in record["touches"]]:
                record["touches"].append({"number": n, "text": text_of[n]})
        for c in doc["conflicts"]:
            if resolves(c["number"]):
                record["conflicts"].append({"number": c["number"], "text": text_of[c["number"]],
                                            "ticket_says": c["ticket_says"], "why": c["why"]})
        sections = []
        for t in record["touches"]:
            if section(t["number"]) not in sections:
                sections.append(section(t["number"]))
        seen = set()
        for oq in open_questions(entries):
            for s in sections:
                if oq["n"] not in seen and (oq["number"] == s or oq["number"].startswith(s + ".")):
                    seen.add(oq["n"])
                    record["open_questions"].append({"n": oq["n"], "number": oq["number"],
                                                     "section": s, "text": oq["text"]})
        record["unresolved"] = unresolved
        qids = _open_what_stands(ticket, record, base / "questions")

    path = _record_path(ticket, root, datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"))
    door.write(path, json.dumps(record, indent=2, ensure_ascii=False) + "\n",
               verb="outline_check", why=f"outline check of {ticket}")
    return {"path": str(path), "record": record, "qids": qids}


def _open_what_stands(ticket: str, record: dict, qroot: Path) -> list[str]:
    """D9, D10: one question per conflict and per open Q#n, unless one this check opened
    before is still open on the ticket. Returns the question id standing for each, in order."""
    standing = [q for q in Q.open_for(ticket, root=qroot) if q.get("source") == SOURCE]

    qids: list[str] = []

    def already(marker: str) -> str | None:
        return next((q["id"] for q in standing if marker in q.get("question", "")), None)

    for c in record["conflicts"]:
        qid = already(f'"{c["text"]}"')
        if qid:
            record["questions_already_open"].append(qid)
            qids.append(qid)
            continue
        q = Q.open_question(ticket, _conflict_q(ticket, c),
                            "the ticket and the component outline disagree; building it would "
                            "build one of them wrong", source=SOURCE, root=qroot)
        record["questions_opened"].append(q["id"])
        qids.append(q["id"])
    for o in record["open_questions"]:
        qid = already(f'where Q#{o["n"]} stands open')
        if qid:
            record["questions_already_open"].append(qid)
            qids.append(qid)
            continue
        q = Q.open_question(ticket, _open_q(ticket, o),
                            f'the ticket works inside outline section {o["section"]}, and the '
                            f'answer to Q#{o["n"]} may change it', source=SOURCE, root=qroot)
        record["questions_opened"].append(q["id"])
        qids.append(q["id"])
    return qids


# ---------------------------------------------------------------------------
# standing (D14) — reads records, never runs a check

def _order(path: Path) -> tuple[str, int]:
    rest = path.stem.split("-", 1)[1]
    stamp, _, n = rest.partition("-")
    return stamp, int(n or 1)


def standing(ticket: str, root: Path | str | None = None) -> dict:
    ran = []
    for p in sorted(records_dir(root).glob(f"{ticket}-*.json"), key=_order):
        try:
            if json.loads(p.read_text(encoding="utf-8")).get("ran") is True:
                ran.append(p)
        except (OSError, json.JSONDecodeError):
            continue   # an unreadable record is not a run that read
    if ran:
        return {"ok": True, "lack": None, "record": str(ran[-1])}
    return {"ok": False, "lack": f"no outline check has run over {ticket}: cairn outlinecheck {ticket}",
            "record": None}


# ---------------------------------------------------------------------------
# the CLI (D12)

def run(argv: list[str], *, reader: Callable = claude_reader, root: Path | str | None = None) -> int:
    """``cairn outlinecheck <ticket>``: 0 nothing stands, 1 a question was opened or is still
    open, 2 the read failed."""
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        print("usage: cairn outlinecheck <ticket>\n\n" + __doc__.strip().splitlines()[0])
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    out = check(argv[0], reader=reader, root=root)
    rec = out["record"]
    print(out["path"])
    if not rec["ran"]:
        print("the read failed the schema twice: " + "; ".join(rec["lacks"]))
        return 2
    qids = iter(out["qids"])
    for c in rec["conflicts"]:
        print(f'conflict {c["number"]}: {next(qids)}')
    for o in rec["open_questions"]:
        print(f'Q#{o["n"]} open in {o["section"]}: {next(qids)}')
    return 1 if rec["questions_opened"] or rec["questions_already_open"] else 0

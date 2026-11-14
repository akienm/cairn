"""The outline check — CodeMother's read of one ticket beside the component outline (ticket
6541ccd1594c; outline 10.3.5.1).

Akien, 2026-10-26: *"the reason we did all this was so you'll know if somebody files a ticket
without one of us investing the cognition to go look."* So the cheapest reader reads the
outline as it stands and the ticket, once, and names the outline lines the ticket touches and
the ones it contradicts. Everything after that read is deterministic: the numbers are resolved
against the parsed file (the line's text is always the FILE's, never the reader's), each
contradiction and each open [Q#n] on a touched line, or above one, becomes one question bound to the
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
OUTLINE_HOME = "press_office"  # moved from the commons root, Akien 2026-11-09
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


# ---------------------------------------------------------------------------
# freshness (ticket a3ac9282bdfa; idea 2026-11-13-an-outline-check-only-stands-for-the)
#
# A ran:true record stands only for the documents it read. It is FRESH iff
#   (1) the outline's bytes hash to its outline_sha256, AND
#   (2) the ticket's PLAN fields (tickets/_charter+why.json#plan_fields) equal those of the git revision of the
#       ticket whose bytes hash to its ticket_sha256 (or the ticket's bytes hash to it outright).
# Otherwise it is stale and the check is re-run. A ticket revision that cannot be found reads stale: it cannot
# be shown that the plan is unchanged. The ticket's STATE (its cursor) moves at every crossing and is not a plan
# field, so it never makes a record stale. The outline is still read (hashed) on every call, so this does not
# cache the outline (D2); it reuses a RECORD only while the hash still matches. The rule was measured on live
# tickets by the integrator's scratch script /tmp/akienasus_ocfresh.py (Dell, 2026-11-13). The build_inspector
# sieve spells the same predicate again (RULE 1: it reads records and cannot import this machine): ticket
# cbf1d333984f. Change one, change the other.

def _plan_fields(base: Path) -> list[str] | None:
    """The ticket charter's plan_fields: the ONE list, never a hand-kept copy. None when unreadable."""
    try:
        got = json.loads((base / "tickets" / "_charter+why.json").read_text(encoding="utf-8")).get("plan_fields")
    except (OSError, ValueError):
        return None
    return [f for f in got if isinstance(f, str)] if isinstance(got, list) and got else None


def _revision_with_hash(base: Path, rel: str, want: str | None) -> bytes | None:
    """The bytes of the git revision of ``rel`` (under the commons repo ``base``) that hash to ``want``."""
    if not want:
        return None
    try:
        revs = subprocess.run(["git", "-C", str(base), "log", "--format=%H", "--", rel],
                              capture_output=True, text=True, timeout=60).stdout.split()
        for rev in revs:
            blob = subprocess.run(["git", "-C", str(base), "show", f"{rev}:{rel}"],
                                  capture_output=True, timeout=60).stdout
            if _sha(blob) == want:
                return blob
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def _sections_sha(entries: list[dict], numbers: list[str]) -> str | None:
    """sha256 of the outline SECTIONS ``numbers`` name (ticket de75c632ea30): for each number, that entry and every
    entry beneath it (numbers starting ``n.``), each as ``number text`` joined by newlines. An entry's text carries
    its [Q#n] tag inline, so a Q added, removed or reworded on or beneath a touched line changes the hash. None when
    a number no longer resolves (the outline was renumbered or the line removed)."""
    parts = []
    for n in numbers:
        if not any(e["number"] == n for e in entries):
            return None
        parts.append("\n".join(f'{e["number"]} {e["text"]}' for e in entries
                              if e["number"] == n or e["number"].startswith(n + ".")))
    return _sha("\n".join(parts).encode("utf-8"))


_OUTLINE_BY_SHA: dict[tuple[str, str], dict[str, str]] = {}


def _outline_revision(want_sha: str | None) -> bytes | None:
    """The bytes of the git revision of the outline whose sha256 is ``want_sha`` (the version a record read), or None.

    One ``git cat-file --batch`` over every revision that touched the file builds a sha256 -> revision map, cached per
    (repo, head) so a census over hundreds of records pays for the history once. A record taken from an outline that
    was never committed (the outline is edited in place) is not in git: None, and the record reads stale."""
    if not want_sha:
        return None
    repo = door.roots()["cairn"]
    rel = f"{OUTLINE_HOME}/{OUTLINE_NAME}"
    try:
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=60).stdout.strip()
        key = (str(repo), head)
        if key not in _OUTLINE_BY_SHA:
            revs = subprocess.run(["git", "-C", str(repo), "log", "--format=%H", "--", rel], capture_output=True,
                                  text=True, timeout=120).stdout.split()
            table: dict[str, str] = {}
            if revs:
                feed = "".join(f"{r}:{rel}\n" for r in revs).encode()
                out = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch"], input=feed,
                                     capture_output=True, timeout=300).stdout
                pos = 0
                for r in revs:
                    nl_at = out.index(b"\n", pos)
                    header = out[pos:nl_at].split()
                    if len(header) < 3 or header[1] != b"blob":      # "<rev>:<path> missing"
                        pos = nl_at + 1
                        continue
                    size = int(header[2])
                    table.setdefault(_sha(out[nl_at + 1:nl_at + 1 + size]), r)
                    pos = nl_at + 1 + size + 1
            _OUTLINE_BY_SHA[key] = table
        rev = _OUTLINE_BY_SHA[key].get(want_sha)
        if rev is None:
            return None
        return subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{rel}"], capture_output=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _sections_unchanged(record: dict, outline_bytes: bytes) -> tuple[bool, str]:
    """The outline's bytes differ from the record's outline_sha256; does that matter to THIS ticket? Only if a section
    it touched changed. A record with no touched number keeps the whole-outline rule: it is stale on any outline
    change. A record with no section hash (taken before de75c632ea30) derives it from the outline version it read. Accepted gap (de75c632ea30 D3): a NEW line elsewhere that
    the ticket would have touched is not noticed until a re-run (--force, a plan change or a touched-section change)."""
    want = record.get("touched_sha256")
    numbers = [t["number"] for t in record.get("touches", []) if isinstance(t, dict) and t.get("number")]
    if not numbers:
        return False, "the outline changed since the check ran"
    if not want:
        # a record taken before the section hash existed: derive it from the outline version it read, found in git by
        # its outline_sha256 (the same way the ticket's plan is compared); not in git means it cannot be shown unchanged
        old = _outline_revision(record.get("outline_sha256"))
        if old is None:
            return False, "the outline changed since the check ran, and the version it read is not in git"
        want = _sections_sha(parse(old.decode("utf-8")), numbers)
        if want is None:
            return False, "a section the ticket touches did not resolve in the outline it read"
    have = _sections_sha(parse(outline_bytes.decode("utf-8")), numbers)
    if have is None:
        return False, "a section the ticket touches no longer resolves in the outline"
    if have != want:
        return False, "a section the ticket touches changed in the outline"
    return True, "the sections the ticket touches are unchanged"


def fresh(ticket: str, record: dict, root: Path | str | None = None) -> tuple[bool, str]:
    """``(True, why)`` iff ``record`` still stands for the outline sections and ticket plan it read."""
    if record.get("ran") is not True:
        return False, "not a ran:true record"
    outline_bytes = outline_file().read_bytes()
    if _sha(outline_bytes) != record.get("outline_sha256"):
        unchanged, why = _sections_unchanged(record, outline_bytes)
        if not unchanged:
            return False, why
    base = commons(root)
    tk = ticket_file(ticket, root)
    if tk is None:
        return False, f"no ticket {ticket!r} on file"
    now = tk.read_bytes()
    if _sha(now) == record.get("ticket_sha256"):
        return True, "the outline and the ticket are unchanged"
    try:
        rel = tk.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return False, "the ticket is outside the commons, so its revisions cannot be read"
    then = _revision_with_hash(base, rel, record.get("ticket_sha256"))
    if then is None:
        return False, "the ticket version the check read is not in git, so the plan cannot be shown unchanged"
    plan = _plan_fields(base)
    if plan is None:
        return False, "the ticket charter's plan_fields cannot be read"
    try:
        a, b = json.loads(then), json.loads(now)
    except ValueError:
        return False, "the ticket cannot be parsed"
    moved = [f for f in plan if a.get(f) != b.get(f)]
    if moved:
        return False, f"the ticket plan changed since the check ran ({', '.join(moved)})"
    return True, "the outline and the ticket plan are unchanged"


def fresh_standing(ticket: str, root: Path | str | None = None) -> dict | None:
    """The newest ran:true record, as ``{"path", "record"}``, only if it is still fresh; else None."""
    newest = None
    for p in sorted(records_dir(root).glob(f"{ticket}-*.json"), key=_order):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue   # an unreadable record is not a run that read
        if doc.get("ran") is True:
            newest = (p, doc)
    if newest is None or not fresh(ticket, newest[1], root)[0]:
        return None
    return {"path": str(newest[0]), "record": newest[1]}


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


def outline_file() -> Path:
    """The outline: ``<cairn>/press_office/CairnComponentOutline.txt`` in the world the door
    is pointed at (Akien moved it out of the commons root, 2026-11-09)."""
    return door.roots()["cairn"] / OUTLINE_HOME / OUTLINE_NAME


def check(ticket: str, *, reader: Callable = claude_reader, root: Path | str | None = None,
          force: bool = False) -> dict:
    """Read ``ticket`` beside the outline, open what stands, write the record. Returns
    ``{'path', 'record', 'qids'}`` — ``qids`` is each conflict's then each open question's
    question id, in record order (the record keeps D11's fields only).

    A FRESH standing record is REUSED, not re-run (ticket a3ac9282bdfa): the reader is not called, no record
    is written, and ``qids`` are the ids the record itself names (``questions_opened`` then
    ``questions_already_open``; the record keeps no order, so a reuse's ids are not matched to conflicts
    by position). _open_what_stands is NOT called on a reuse: it knows only questions still open, so it would
    open a new one for a conflict that was answered since, which is the very re-run this avoids. ``force``
    re-runs regardless; a stale record is re-run (see ``fresh``)."""
    if not force:
        got = fresh_standing(ticket, root)
        if got is not None:
            rec = got["record"]
            return {"path": got["path"], "record": rec, "reused": True,
                    "qids": list(rec.get("questions_opened", [])) + list(rec.get("questions_already_open", []))}
    base = commons(root)
    outline_path = outline_file()
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
        # D8 (ticket 0d3b8a51c9df): an open [Q#n] bears on the ticket when the ticket touches
        # the question's own line or a line beneath it. A touched sibling or a touched heading
        # above it does not: widening to two components made 9.4 (all of CodeMother) one
        # section, and 99 of 139 opens measured over 295 records came from that widening.
        touched = [t["number"] for t in record["touches"]]
        for oq in open_questions(entries):
            q = oq["number"]
            hit = next((t for t in touched if t == q or t.startswith(q + ".")), None)
            if hit is not None:
                record["open_questions"].append({"n": oq["n"], "number": q,
                                                 "section": hit, "text": oq["text"]})
        record["unresolved"] = unresolved
        if record["touches"]:
            # what the ticket's touched sections were when read (ticket de75c632ea30): the freshness rule's
            # section-scoped half. Absent when the ticket touched nothing: that record keeps the whole-outline rule.
            record["touched_sha256"] = _sections_sha(entries, [t["number"] for t in record["touches"]])
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
    force = "--force" in argv
    args = [a for a in argv if a != "--force"]
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: cairn outlinecheck <ticket> [--force]\n\n" + __doc__.strip().splitlines()[0]
              + "\n\nA fresh standing check is reused; --force re-runs it.")
        return 0 if args and args[0] in ("-h", "--help") else 2
    out = check(args[0], reader=reader, root=root, force=force)
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

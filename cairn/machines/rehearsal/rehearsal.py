"""The rehearsal machine — the cheapest reader rehearses a ticket before BUILDME.

Ticket cf80bdb57205 (2026-09-15). Akien: *"We run an agent with the ticket, ask for it's
proof tree, simplify or get questions answered, then try again until it passes that gate.
All on the cheapest model. and after the prebuild."* The machine measures a cast ticket's
BUILDABILITY before anyone spends a builder on it: render the ticket plus its standing chart
berths as text, hand it to the cheapest reader three times cold, and diff the three typed
build trees BY CODE into deterministic gaps (D6). A gap is disposed at the CLI as a decision
line on the ticket (``decide``) or as a question in his inbox; a pass with zero gaps writes a
CLEAN record carrying the ticket's sha256, and the BUILDME entry lane
``the_ticket_rehearses_clean`` (``build_inspector.buildme_rides_the_rehearsal``) reads it.

What is physics here and what is not:
  - the reader is INJECTABLE (``reader(prompt_text, schema) -> (tree | None, meta)``) so a
    proof stubs it with recorded trees — no proof tooth calls the live reader (D15); the
    live transport is ``claude_reader`` below, the claude CLI as a subprocess (D7);
  - the schema is checked BY HAND (``validate``) — no jsonschema package on the box — and a
    read that fails it is re-read (D5), never patched;
  - every record and every ticket edit goes through the artifact door (D9): records under
    ``<commons>/rehearsals/`` with verb ``rehearse``, the ticket's ``rehearsal`` pointer and
    ``decisions`` through verb ``cast``;
  - the hash protocol (D8, amended at build): the ticket's ``rehearsal`` pointer is written
    FIRST, then the resulting bytes are hashed, then the record is written carrying that
    hash — so the lane compares the record's hash against the exact live bytes, and any
    later edit of the ticket un-rehearses it. The hash of the bytes the reader actually saw
    rides beside it as ``ticket_sha256_at_read``.
  - the loop cap is 5 (D11): a sixth invocation with the ticket still unclean opens ONE
    question naming the standing gaps and reads nothing.
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

from cairn.tools.artifact import artifact as door
from cairn.tools.system_word import fold

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCHEMA_PATH = HERE / "schema.json"
PROMPT_PATH = HERE / "prompt.md"
STATES = ("builds_as_written", "builds_under_assumption", "cannot_proceed")
READS = 3               # D1: three cold reads
RETRIES_PER_READ = 2    # D5: a read that fails the schema is re-read; this many times, then the pass is refused
PASS_CAP = 5            # D11
MODEL = "claude-haiku-4-5-20251001"   # D7: the cheapest reader
CLAUDE = os.environ.get("CAIRN_REHEARSAL_CLAUDE", "claude")
GAP_KINDS = ("assumes", "assumption_differs", "cannot_proceed", "step_absent", "unlisted")
# D6 as amended (open-d71a52522428, Akien: "i am trying to move us AWAY from free text"): a step
# is named by the ticket decision it builds — D<n> — or, when no decision covers it, by
# "unlisted: <text>". A decision id folds exactly, so three reads converge or they do not; an
# unlisted step is itself a gap, because the ticket is a list of decisions and a step no
# decision names is a decision the ticket still owes.
STEP_RE = re.compile(r"^(?:D(?P<n>[1-9][0-9]*)|unlisted: \S.*)$")
UNLISTED = "unlisted: "

Reader = Callable[[str, dict], tuple[dict | None, dict]]


class Refused(Exception):
    """A rehearsal that cannot proceed — named lack, nothing written."""


class ReaderFailed(Refused):
    """The reader never returned a tree the schema accepts, ``RETRIES_PER_READ`` re-reads in.
    An instrument failure, not a gap in the ticket: NO record is written, because a record
    would count toward the pass cap against a ticket the reader never actually read."""


# ---------------------------------------------------------------------------
# where things are

def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def commons(root: Path | str | None = None) -> Path:
    """The commons the door is pointed at — a scratch world in a proof, the live one in the
    field. ``root`` overrides for a caller that has one in hand."""
    if root is not None:
        return Path(root)
    return door.roots()["CairnCommons"]


def records_dir(root: Path | str | None = None) -> Path:
    return commons(root) / "rehearsals"


def ticket_file(ticket: str, root: Path | str | None = None) -> Path | None:
    """The ticket file an id names under the commons the door sees, or None. Rides the one
    locator (``grammar.ticket_path``) so this and the gate cannot disagree about the file."""
    from cairn.tools.chain.grammar import ticket_path
    if not isinstance(ticket, str) or not ticket.strip() or "/" in ticket:
        return None
    hit = ticket_path(ticket.strip(), root=str(REPO), tickets_dir=str(commons(root) / "tickets"))
    return Path(hit) if hit else None


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


# ---------------------------------------------------------------------------
# the schema, by hand

def decision_ids_of(doc: dict) -> set[int]:
    """The ``n`` of every decision the ticket carries — the vocabulary a step may name."""
    have = doc.get("decisions") if isinstance(doc, dict) else None
    return {d["n"] for d in (have or []) if isinstance(d, dict) and isinstance(d.get("n"), int)}


def validate(tree: object, decision_ids: set[int] | None = None) -> list[str]:
    """Every way ``tree`` fails schema.json, named; empty means it passes. Written by hand
    because the box has no jsonschema package and the shape is small; the schema file stays
    the contract the reader is handed and this is its mirror — a tooth in the proof holds
    the two together over the schema's own examples. ``decision_ids`` is the ticket's own
    vocabulary: a step naming ``D<n>`` the ticket does not carry is a lack the schema's
    pattern cannot see, so the machine checks it here and the read is re-read (D5)."""
    lacks: list[str] = []
    if not isinstance(tree, dict):
        return [f"tree is {type(tree).__name__}, not an object"]
    for k in tree:
        if k not in ("ticket", "ticket_sha256", "read", "nodes"):
            lacks.append(f"unknown top-level key {k!r}")
    nodes = tree.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return lacks + ["nodes: a non-empty list is required"]
    for i, n in enumerate(nodes):
        at = f"nodes[{i}]"
        if not isinstance(n, dict):
            lacks.append(f"{at}: not an object")
            continue
        for k in n:
            if k not in ("step", "state", "assumption", "would_settle", "confidence"):
                lacks.append(f"{at}: unknown key {k!r}")
        for k in ("step", "state", "assumption", "would_settle", "confidence"):
            if k not in n:
                lacks.append(f"{at}: missing {k!r}")
        step = n.get("step")
        if "step" in n and not (isinstance(step, str) and step.strip()):
            lacks.append(f"{at}.step: a non-empty string is required")
        elif "step" in n:
            m = STEP_RE.match(step)
            if not m:
                lacks.append(f"{at}.step: {step!r} is neither D<n> (a decision the ticket carries) "
                             f"nor 'unlisted: <text>'")
            elif m.group("n") and decision_ids is not None and int(m.group("n")) not in decision_ids:
                lacks.append(f"{at}.step: {step!r} names a decision the ticket does not carry "
                             f"(it has {sorted(decision_ids)})")
        if "state" in n and n.get("state") not in STATES:
            lacks.append(f"{at}.state: {n.get('state')!r} is not one of {STATES}")
        for k in ("assumption", "would_settle"):
            if k in n and not isinstance(n.get(k), str):
                lacks.append(f"{at}.{k}: a string is required")
        c = n.get("confidence")
        if "confidence" in n and not (isinstance(c, (int, float)) and not isinstance(c, bool)
                                      and 0 <= c <= 1):
            lacks.append(f"{at}.confidence: a number in [0, 1] is required")
    return lacks


# ---------------------------------------------------------------------------
# the render: what the reader sees, and nothing else (D4)

def render(ticket: str, *, root: Path | str | None = None, berths_root=None,
           repo: Path | str | None = None) -> tuple[str, str, Path]:
    """The text the reader is handed: the ticket file verbatim, the standing chart berths
    for the ticket (per stage, the latest claiming packet — through the one chain locator),
    and the charters of the components orient ref'd. Returns ``(text, sha256 of the ticket
    bytes as read, ticket path)``. No repository, no code: D4 is the whole point, and the
    prompt says so to the reader."""
    from cairn.tools.chain.chain import chain_for_ticket
    tk = ticket_file(ticket, root)
    if tk is None:
        raise Refused(f"no ticket file for {ticket!r} under {commons(root) / 'tickets'}")
    blob = tk.read_bytes()
    repo = Path(repo) if repo is not None else REPO
    parts = [prompt(), "\n\n# THE TICKET\n\n```json\n" + blob.decode("utf-8").rstrip() + "\n```\n"]
    try:
        chain = chain_for_ticket(ticket, berths_root=berths_root)
    except Exception as exc:  # the chart is a courtesy to the reader, not a gate here — the lane a_berthed_chart_chain_claims_the_ticket judges it
        chain = {}
        parts.append(f"\n# THE CHART\n\n(no chart could be read: {exc})\n")
    refs: list[str] = []
    for stage, path in chain.items():
        if not path:
            continue
        try:
            doc = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if stage == "orient" and isinstance(doc.get("refs"), list):
            refs = [r for r in doc["refs"] if isinstance(r, str)]
        parts.append(f"\n# CHART — {stage}\n\n```json\n" + json.dumps(doc, indent=1, ensure_ascii=False) + "\n```\n")
    for ref in refs:
        ch = repo / ref / "intention+why.json"
        if ch.is_file():
            parts.append(f"\n# CHARTER — {ref}\n\n```json\n" + ch.read_text(encoding="utf-8").rstrip() + "\n```\n")
    return "".join(parts), _sha(blob), tk


# ---------------------------------------------------------------------------
# the reader (D7) — injectable, so a proof never reaches this one (D15)

def claude_reader(prompt_text: str, schema_doc: dict) -> tuple[dict | None, dict]:
    """One cold read through the claude CLI: ``claude -p --model <cheapest> --output-format
    json --tools "" --json-schema <schema>``, the prompt on stdin, CLAUDECODE unset so it
    runs outside this session. Returns ``(structured_output or None, meta)`` where meta
    carries cost, duration and the raw result tail — the machine validates the tree, this
    only fetches it."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
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
    tree = env_doc.get("structured_output")
    if tree is None and isinstance(env_doc.get("result"), str):
        try:
            tree = json.loads(env_doc["result"])
        except json.JSONDecodeError:
            meta["error"] = "no structured_output and result is not JSON"
    return tree, meta


def read_tree(text: str, reader: Reader, n: int, *, ticket: str, sha: str,
              decision_ids: set[int] | None = None) -> tuple[dict, list[dict]]:
    """Read ``n`` of three: call the reader, check the shape, re-read on a schema failure
    (D5) up to ``RETRIES_PER_READ`` times. Identity fields are stamped from truth AFTER the
    shape passes — the reader's own ``ticket``/``read`` are never trusted. Returns the tree
    and the meta of every attempt."""
    schema_doc = schema()
    attempts: list[dict] = []
    for attempt in range(1, RETRIES_PER_READ + 2):
        tree, meta = reader(text, schema_doc)
        lacks = validate(tree, decision_ids) if tree is not None else [meta.get("error") or "reader returned nothing"]
        attempts.append({"attempt": attempt, "read": n, "schema_lacks": lacks, **meta})
        if not lacks:
            return {"ticket": ticket, "ticket_sha256": sha, "read": n, "nodes": tree["nodes"]}, attempts
    raise ReaderFailed(
        f"read {n}: no tree passed the schema in {RETRIES_PER_READ + 1} attempts — last lacks: "
        + "; ".join(attempts[-1]["schema_lacks"][:5]))


# ---------------------------------------------------------------------------
# the diff (D6) — deterministic, by code

def gaps(reads: list[dict]) -> list[dict]:
    """D6, verbatim: *"any node not builds_as_written in any read; any step present in one
    read and absent in another after case-folding through cairn.tools.system_word; any two
    reads whose assumption text differs on the same step."* Steps fold (a word the reader
    could type); assumption text is free text and never folds. One gap per (kind, step),
    reads merged, sorted by (kind, step) so two runs over the same trees write the same
    list. Amended (open-d71a52522428): a step named ``unlisted: <text>`` in any read is a
    gap of kind ``unlisted`` — the ticket owes the decision that would name it."""
    by_kind_step: dict[tuple[str, str], dict] = {}

    def gap(kind: str, step: str, read_n: int, **more) -> None:
        key = (kind, fold(step))
        g = by_kind_step.setdefault(key, {"kind": kind, "step": step, "reads": []})
        if read_n not in g["reads"]:
            g["reads"].append(read_n)
        for k, v in more.items():
            if v in (None, ""):
                continue
            g.setdefault(k, [])
            if v not in g[k]:
                g[k].append(v)

    steps_by_read: list[dict[str, dict]] = []
    for r in reads:
        seen: dict[str, dict] = {}
        for node in r.get("nodes", []):
            seen.setdefault(fold(node["step"]), node)
            if node["step"].startswith(UNLISTED):
                gap("unlisted", node["step"], r["read"],
                    would_settle=node.get("would_settle", "").strip())
            if node["state"] == "builds_under_assumption":
                gap("assumes", node["step"], r["read"],
                    assumption=node.get("assumption", "").strip(),
                    would_settle=node.get("would_settle", "").strip())
            elif node["state"] == "cannot_proceed":
                gap("cannot_proceed", node["step"], r["read"],
                    assumption=node.get("assumption", "").strip(),
                    would_settle=node.get("would_settle", "").strip())
        steps_by_read.append(seen)
    every = set().union(*steps_by_read) if steps_by_read else set()
    for folded in sorted(every):
        present = [i for i, s in enumerate(steps_by_read) if folded in s]
        absent = [reads[i]["read"] for i, s in enumerate(steps_by_read) if folded not in s]
        name = steps_by_read[present[0]][folded]["step"]
        for r_n in absent:
            gap("step_absent", name, r_n, present_in=[reads[i]["read"] for i in present])
        texts = {steps_by_read[i][folded].get("assumption", "").strip() for i in present}
        texts.discard("")
        if len(texts) > 1:
            for i in present:
                gap("assumption_differs", name, reads[i]["read"],
                    assumption=steps_by_read[i][folded].get("assumption", "").strip())
    out = sorted(by_kind_step.values(), key=lambda g: (g["kind"], fold(g["step"])))
    for g in out:
        g["reads"].sort()
    return out


# ---------------------------------------------------------------------------
# records

def records_for(ticket: str, root: Path | str | None = None) -> list[tuple[Path, dict]]:
    """Every readable rehearsal record for the ticket, oldest first.

    Order rides the record's own ``at`` and ``pass`` — a filename can carry a
    ``-2`` de-collision suffix that sorts BEFORE ``.json``, so names lie.
    """
    d = records_dir(root)
    out = []
    for p in d.glob(f"{ticket}-*.json") if d.is_dir() else []:
        try:
            out.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    out.sort(key=lambda pd: (str(pd[1].get("at", "")), int(pd[1].get("pass") or 0), pd[0].name))
    return out


def passes_since_clean(ticket: str, root: Path | str | None = None) -> int:
    n = 0
    for _, doc in records_for(ticket, root):
        n = 0 if doc.get("clean") else n + 1
    return n


def _write_ticket(tk: Path, doc: dict, *, why: str) -> bytes:
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    door.write(str(tk), text, verb="cast", why=why)
    return tk.read_bytes()


def rehearse(ticket: str, *, reader: Reader = claude_reader, root: Path | str | None = None,
             berths_root=None, repo: Path | str | None = None, by: str | None = None) -> dict:
    """One pass: render, three cold reads, the diff, one record — clean or not. On the sixth
    pass over an unclean ticket (D11) no read happens: ONE question is opened on the ticket
    naming the standing gaps, and the return names it. Returns the record as written (plus
    ``path``), or ``{"question": <id>, ...}``."""
    tk = ticket_file(ticket, root)
    if tk is None:
        raise Refused(f"no ticket file for {ticket!r} under {commons(root) / 'tickets'}")
    passes = passes_since_clean(ticket, root)
    if passes >= PASS_CAP:
        return _open_the_question(ticket, root)
    text, sha_at_read, tk = render(ticket, root=root, berths_root=berths_root, repo=repo)
    ids = decision_ids_of(json.loads(tk.read_text(encoding="utf-8")))
    reads, meta = [], []
    for n in range(1, READS + 1):
        tree, attempts = read_tree(text, reader, n, ticket=ticket, sha=sha_at_read, decision_ids=ids)
        reads.append(tree)
        meta.extend(attempts)
    found = gaps(reads)
    clean = not found
    stamp = _stamp()
    rec_path = records_dir(root) / f"{ticket}-{stamp}.json"
    n = 1
    while rec_path.exists():   # two passes inside one second are two records, never one overwritten
        n += 1
        rec_path = records_dir(root) / f"{ticket}-{stamp}-{n}.json"
    rec_rel = rec_path.relative_to(commons(root)).as_posix()
    if clean:
        # D8 as amended: the pointer lands first, the record hashes what the lane will see.
        doc = json.loads(tk.read_text(encoding="utf-8"))
        doc["rehearsal"] = rec_rel
        live = _write_ticket(tk, doc, why=f"rehearsal clean on pass {passes + 1}: {rec_rel}")
        sha_live = _sha(live)
    else:
        sha_live = sha_at_read
    record = {
        "ticket": ticket,
        "record": rec_rel,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pass": passes + 1,
        "clean": clean,
        "ticket_sha256": sha_live,
        "ticket_sha256_at_read": sha_at_read,
        "reads": reads,
        "gaps": found,
        "meta": {
            "model": MODEL,
            "attempts": meta,
            "cost_usd": round(sum((m.get("cost_usd") or 0) for m in meta), 6),
            "duration_ms": sum((m.get("duration_ms") or 0) for m in meta),
            "rendered_chars": len(text),
            "by": by,
        },
        "divergence": None,
    }
    door.write(str(rec_path), json.dumps(record, indent=2, ensure_ascii=False) + "\n",
               verb="rehearse",
               why=f"pass {passes + 1} over {ticket}: {'clean' if clean else str(len(found)) + ' gap(s)'}")
    return dict(record, path=str(rec_path))


def _open_the_question(ticket: str, root: Path | str | None) -> dict:
    """The sixth pass (D11): one question on the ticket naming the standing gaps; no read."""
    from cairn.tools.question import question as Q
    qroot = commons(root) / "questions"
    latest = records_for(ticket, root)[-1][1]
    standing = latest.get("gaps") or []
    already = [q for q in Q.open_for(ticket, root=qroot) if q.get("source") == "rehearsal"]
    if already:
        # ONE question (D11): the standing one is the answer owed, not a second copy of it
        return {"ticket": ticket, "question": already[0]["id"], "gaps": standing,
                "passes": PASS_CAP, "clean": False, "already_open": True}
    lines = "; ".join(f"{g['kind']} at '{g['step']}'" + (f" ({g['would_settle'][0]})" if g.get("would_settle") else "")
                      for g in standing[:8])
    q = (f"five rehearsal passes over {ticket} did not converge — the standing gaps are: {lines}"
         f"{' …' if len(standing) > 8 else ''}; which of these does the ticket settle, and how?")
    rec = Q.open_question(
        ticket, q,
        f"the cheapest reader cannot build this ticket as written after {PASS_CAP} passes; "
        f"the BUILDME lane the_ticket_rehearses_clean holds until a clean record exists",
        source="rehearsal", root=qroot)
    return {"ticket": ticket, "question": rec["id"], "gaps": standing, "passes": PASS_CAP, "clean": False}


def decide(ticket: str, step: str, line: str, *, by: str, root: Path | str | None = None) -> dict:
    """A gap disposed as a decision line on the ticket (D3: a ticket is a list of one-line
    decisions): appends ``{n, text, by, step, source: "rehearsal"}`` to ``decisions`` through
    the door's ``cast`` verb. The next pass reads the edited ticket, so the pointer (if any)
    goes stale by construction — the lane demands a fresh clean record."""
    tk = ticket_file(ticket, root)
    if tk is None:
        raise Refused(f"no ticket file for {ticket!r}")
    if not (isinstance(line, str) and line.strip()):
        raise Refused("a decision is one line of text — an empty one decides nothing")
    if not (isinstance(by, str) and by.strip()):
        raise Refused("--by: who made this decision (D3 — each decision carries who made it)")
    doc = json.loads(tk.read_text(encoding="utf-8"))
    have = doc.get("decisions")
    have = list(have) if isinstance(have, list) else []
    n = 1 + max((d.get("n", 0) for d in have if isinstance(d, dict)), default=0)
    entry = {"n": n, "text": line.strip(), "by": by.strip(), "step": step.strip(), "source": "rehearsal"}
    have.append(entry)
    doc["decisions"] = have
    _write_ticket(tk, doc, why=f"rehearsal gap at '{step.strip()}' decided by {by.strip()}: D{n}")
    return entry


# ---------------------------------------------------------------------------
# the lane's question: is the ticket rehearsed clean, over these exact bytes?

def standing(ticket: str, root: Path | str | None = None) -> dict:
    """What the BUILDME lane reads: ``{ok, lack, record, ticket_sha256, live_sha256}``.
    ``ok`` iff the ticket's ``rehearsal`` pointer names a readable record that is clean and
    whose ``ticket_sha256`` equals the sha256 of the live ticket bytes. Everything else is a
    named lack — no pointer, an unreadable record, an unclean one, a stale hash."""
    tk = ticket_file(ticket, root)
    if tk is None:
        return {"ok": False, "lack": "no ticket file", "record": None}
    try:
        blob = tk.read_bytes()
        doc = json.loads(blob)
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "lack": f"ticket unreadable: {exc}", "record": None}
    ptr = doc.get("rehearsal") if isinstance(doc, dict) else None
    if not isinstance(ptr, str) or not ptr.strip():
        return {"ok": False, "lack": "the ticket carries no rehearsal pointer — `cairn rehearse <id>`",
                "record": None, "live_sha256": _sha(blob)}
    rec_path = commons(root) / ptr
    try:
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "lack": f"rehearsal record {ptr} unreadable: {exc}", "record": ptr,
                "live_sha256": _sha(blob)}
    if not rec.get("clean"):
        return {"ok": False, "lack": f"rehearsal record {ptr} is not clean ({len(rec.get('gaps') or [])} gap(s))",
                "record": ptr, "live_sha256": _sha(blob)}
    if rec.get("ticket_sha256") != _sha(blob):
        return {"ok": False, "lack": "the ticket was edited after its rehearsal — rehearse again",
                "record": ptr, "ticket_sha256": rec.get("ticket_sha256"), "live_sha256": _sha(blob)}
    return {"ok": True, "lack": None, "record": ptr, "ticket_sha256": rec["ticket_sha256"],
            "live_sha256": _sha(blob)}


# ---------------------------------------------------------------------------
# after PROVED (D14): the built proof against the converged tree

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "is", "it", "its", "for", "on", "with",
         "test", "that", "not", "by", "as", "at", "be", "from", "this", "no", "one", "into"}


def _tokens(s: str) -> set[str]:
    return {t for t in _TOKEN.findall(fold(s).replace("_", " ")) if t not in _STOP and len(t) > 1}


def decision_ids_and_text(tk: Path | None) -> list[dict]:
    if tk is None:
        return []
    doc = json.loads(tk.read_text(encoding="utf-8"))
    return [d for d in (doc.get("decisions") or []) if isinstance(d, dict) and isinstance(d.get("n"), int)]


def step_text(step: str, decisions: dict[int, str]) -> str:
    """A step's words for the divergence tokens: the decision's text for ``D<n>``, the text
    after the prefix for an unlisted step — the id itself carries no tokens a tooth shares."""
    m = STEP_RE.match(step or "")
    if m and m.group("n"):
        return decisions.get(int(m.group("n")), step)
    return step[len(UNLISTED):] if step.startswith(UNLISTED) else step


def teeth_of(proof: Path | str) -> list[str]:
    """``def test_*`` names in a proof file, in order."""
    text = Path(proof).read_text(encoding="utf-8")
    return re.findall(r"^\s*def (test_\w+)\s*\(", text, flags=re.M)


def divergence(steps: list[str], teeth: list[str], *, overlap: int = 2) -> dict:
    """The diff both ways between the converged tree's steps and the built proof's teeth:
    a step is covered when some tooth shares ``overlap`` significant tokens with it; a tooth
    is expected when some step does. ``{"steps_unproved": [...], "teeth_unforeseen": [...],
    "matched": [[step, tooth], ...]}`` — empty lists both ways is the rehearsal predicting
    the build."""
    st = {s: _tokens(s) for s in steps}
    tt = {t: _tokens(t) for t in teeth}
    matched = [[s, t] for s in steps for t in teeth if len(st[s] & tt[t]) >= overlap]
    covered = {s for s, _ in matched}
    foreseen = {t for _, t in matched}
    return {"steps_unproved": [s for s in steps if s not in covered],
            "teeth_unforeseen": [t for t in teeth if t not in foreseen],
            "matched": matched}


def record_divergence(ticket: str, proofs: list[Path | str], *, root: Path | str | None = None) -> dict:
    """Write the divergence list onto the ticket's clean record (D14) through the door.
    The converged tree is the clean record's first read — three agreeing reads have the same
    folded steps by construction of a clean record."""
    st = standing(ticket, root)
    if not st.get("record"):
        raise Refused(f"{ticket} has no rehearsal record to write a divergence onto: {st['lack']}")
    rec_path = commons(root) / st["record"]
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    if not rec.get("clean"):
        raise Refused(f"{st['record']} is not a clean record — divergence is measured against a converged tree")
    tk = ticket_file(ticket, root)
    decisions = {d["n"]: d.get("text", "") for d in decision_ids_and_text(tk)}
    steps = [step_text(n["step"], decisions) for n in rec["reads"][0]["nodes"]]
    teeth = [t for p in proofs for t in teeth_of(p)]
    d = divergence(steps, teeth)
    d["proofs"] = [str(p) for p in proofs]
    d["at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rec["divergence"] = d
    door.write(str(rec_path), json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
               verb="rehearse",
               why=f"divergence after PROVED over {ticket}: {len(d['steps_unproved'])} step(s) unproved, "
                   f"{len(d['teeth_unforeseen'])} tooth/teeth unforeseen")
    return d

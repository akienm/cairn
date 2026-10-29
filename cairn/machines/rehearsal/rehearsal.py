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

import ast
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from cairn.tools.artifact import artifact as door
from cairn.tools.base import ticket_log
from cairn.tools.base.diagnostic import DiagnosticBase
from cairn.tools.system_word import fold

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCHEMA_PATH = HERE / "schema.json"
PROMPT_PATH = HERE / "prompt.md"
VOYAGE_CRAFT_PATH = HERE / "voyage_craft.md"
STATES = ("builds_as_written", "builds_under_assumption", "cannot_proceed")
LOOK_KINDS = ("path", "module")   # 7a31059daa23 D2: what a reader may name for the machine to look at
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
HANDED_BACK = """

# YOUR PREVIOUS READING WAS HANDED BACK

It did not pass the shape, for these reasons. Read the ticket again and return the whole
tree — every decision the ticket carries, exactly once, in the form above.

{lacks}
"""

# Ticket c3f8efa612ce: a read whose ONLY lacks are missing decision ids is patched, not re-read
# whole — measured, a whole re-read told 'missing D<n>' drops the same tail again. The reader is
# handed its own nodes back and asked for exactly the missing ones (warm only to its own read).
HANDED_BACK_MISSING = """

# YOUR PREVIOUS READING LEFT DECISIONS OUT

Your reading below covered every other decision and passed the shape, but:

{lacks}

Return a tree whose nodes cover ONLY these decisions, one node each, in the form above —
nothing else:

{missing}

Your earlier nodes, for reference (do not return them again):

{earlier}
"""

_MISSING_LACK = re.compile(r"^nodes: every decision gets one node; missing \[(.*)\]$")

Reader = Callable[[str, dict], tuple[dict | None, dict]]


class Refused(Exception):
    """A rehearsal that cannot proceed — named lack, nothing written."""


class ReaderFailed(DiagnosticBase, Refused):
    """The reader never returned a tree the schema accepts, ``RETRIES_PER_READ`` re-reads in.
    An instrument failure, not a gap in the ticket — and still a RUN (ticket ba4166fe51c4,
    Akien 2026-09-29: *"shouldn't a rehsersal pass be counted like a testing pass?"*):
    ``rehearse`` catches it and writes a record with ``ran: false`` carrying this text, and
    that record counts toward the pass cap. ``attempts`` carries every failed attempt."""

    def __init__(self, message: str, attempts: list[dict] | None = None):
        super().__init__(message)
        self.attempts = list(attempts or [])


# ---------------------------------------------------------------------------
# where things are

def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def voyage_craft() -> str:
    """The standing voyage-craft note (ticket 996668eceef1): the steps every code-seam voyage
    takes the same way, handed to the reader on every render so they are settled once. Read at
    call time from ``VOYAGE_CRAFT_PATH``; absent, the render refuses rather than hand a reader less."""
    if not VOYAGE_CRAFT_PATH.is_file():
        raise Refused(f"no voyage-craft note at {VOYAGE_CRAFT_PATH}")
    return VOYAGE_CRAFT_PATH.read_text(encoding="utf-8")


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


def design_sha(blob: bytes) -> str:
    """The sha256 of a ticket's DESIGN: its JSON with ``workflow_and_state`` (the cursor) and
    ``rehearsal`` (the pointer to this very record) removed, serialized with sorted keys. A
    clean record stands over this, so the cursor moving through the workflow leaves it
    standing and any edit to what the builder reads still makes it stale (ticket 9fb045a476dc)."""
    doc = json.loads(blob)
    doc.pop("workflow_and_state", None)
    doc.pop("rehearsal", None)
    return _sha(json.dumps(doc, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


# ---------------------------------------------------------------------------
# the schema, by hand

def decision_ids_of(doc: dict) -> set[int]:
    """The ``n`` of every live decision the ticket carries — the vocabulary a step may name.
    A retired decision (ticket 4968b5d18645) is not in it: the reader is no longer handed it,
    so a read naming it is a lack and a read omitting it is not. A scoped decision (ticket
    eb05adbe0a0f) is not in it either: it is handed as context, never as a step."""
    have = doc.get("decisions") if isinstance(doc, dict) else None
    return {d["n"] for d in (have or []) if isinstance(d, dict) and isinstance(d.get("n"), int)
            and not d.get("retired") and not d.get("context")}


def validate(tree: object, decision_ids: set[int] | None = None) -> list[str]:
    """Every way ``tree`` fails schema.json, named; empty means it passes. Written by hand
    because the box has no jsonschema package and the shape is small; the schema file stays
    the contract the reader is handed and this is its mirror — a tooth in the proof holds
    the two together over the schema's own examples. ``decision_ids`` is the ticket's own
    vocabulary: a step naming ``D<n>`` the ticket does not carry is a lack the schema's
    pattern cannot see, and so is a carried decision with no node or with two — every
    decision gets exactly one — so the machine checks both here and the read is re-read (D5)."""
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
            if k not in ("step", "state", "assumption", "would_settle", "confidence", "looks_at"):
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
        if "looks_at" in n:                          # 7a31059daa23 D2
            looks = n["looks_at"]
            if not isinstance(looks, list):
                lacks.append(f"{at}.looks_at: a list is required")
            else:
                for j, item in enumerate(looks):
                    if not (isinstance(item, dict) and set(item) == {"kind", "name"}):
                        lacks.append(f"{at}.looks_at[{j}]: an object with exactly kind and name is required")
                        continue
                    if item["kind"] not in LOOK_KINDS:
                        lacks.append(f"{at}.looks_at[{j}].kind: {item['kind']!r} is not one of {LOOK_KINDS}")
                    if not (isinstance(item["name"], str) and item["name"]):
                        lacks.append(f"{at}.looks_at[{j}].name: a non-empty string is required")
    # every decision the ticket carries, exactly once (D17): three readers that each judge
    # which decisions are steps never converge on the same set — measured on this machine's
    # own ticket, 6 of 17 ids step_absent — so the set is not judged, it is required. A
    # missing or doubled id is a lack like any other and the read is re-read (D5).
    if decision_ids is not None:
        seen: list[int] = []
        for n in nodes:
            m = STEP_RE.match(n.get("step") or "") if isinstance(n, dict) else None
            if m and m.group("n"):
                seen.append(int(m.group("n")))
        missing = sorted(decision_ids - set(seen))
        doubled = sorted({i for i in seen if seen.count(i) > 1})
        if missing:
            lacks.append(f"nodes: every decision gets one node; missing {['D%d' % i for i in missing]}")
        if doubled:
            lacks.append(f"nodes: every decision gets one node; doubled {['D%d' % i for i in doubled]}")
    return lacks


# ---------------------------------------------------------------------------
# the render: what the reader sees, and nothing else (D4)

_DECISION_STEP = re.compile(r"[Dd]([1-9][0-9]*)")


def reader_view(blob: bytes) -> str:
    """The ticket as the reader is handed it (ticket eb1c943e09b9). Only the PASTED COPY's
    ``decisions`` change; the file, and the sha256 every record keeps, are its bytes as read.

    (a) every decision's text begins with its own ``D<n>`` — a read that cannot see an id in
        the text refuses 'missing D<n>' (measured 2026-09-29 on cd8096f9eeca, 2026-10-02 on
        d8e8a2dc1176); a text already labeled is left as it is;
    (b) a decision ``decide()`` appended (source 'rehearsal', step 'D<m>' naming a decision in
        the list) is also shown INSIDE D<m>'s line as ``[settled by D<n>: <its text>]``, so the
        reader judging D<m> sees the answer where the question is, instead of re-flagging a
        settled step whose answer stands lines away. It stays in the list, labeled. A step
        that is not 'D<m>', or names no decision, is left alone.

    (c) a decision ``retire()`` stamped is left out of the pasted copy entirely, and so is any
        '[settled by]' annotation whose settler or target it was (ticket 4968b5d18645) — the
        file keeps its text and its stamp; the reader is handed only the live lines.

    (d) a decision ``scope()`` stamped with ``context`` moves out of ``decisions`` into a
        top-level ``context`` list, in order, its text still labeled ``D<n>`` (ticket
        eb05adbe0a0f) — read for what it says, never a step. The key is set only when the list
        is non-empty, so a ticket with nothing scoped reads as it did before.

    decide() is unchanged (D3): the file keeps who said what and when; this is a view. A ticket
    that does not parse, or carries no decisions list, is pasted verbatim."""
    raw = blob.decode("utf-8").rstrip()
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    have = doc.get("decisions") if isinstance(doc, dict) else None
    if not isinstance(have, list):
        return raw
    doc["decisions"] = have = [d for d in have if not (isinstance(d, dict) and d.get("retired"))]
    entries = [d for d in have if isinstance(d, dict) and isinstance(d.get("n"), int)]
    original = {d["n"]: str(d.get("text", "")) for d in entries}
    view = {}
    for n, text in original.items():
        view[n] = text if re.match(rf"D{n}\b", text) else f"D{n} {text}"
    for d in sorted(entries, key=lambda d: d["n"]):
        m = _DECISION_STEP.fullmatch(str(d.get("step") or "").strip())
        if d.get("source") != "rehearsal" or not m:
            continue
        target = int(m.group(1))
        if target in view and target != d["n"]:
            view[target] += f" [settled by D{d['n']}: {original[d['n']]}]"
    for d in entries:
        d["text"] = view[d["n"]]
    scoped = [d for d in have if isinstance(d, dict) and d.get("context")]
    if scoped:
        doc["decisions"] = [d for d in have if not (isinstance(d, dict) and d.get("context"))]
        doc["context"] = scoped
    return json.dumps(doc, indent=2, ensure_ascii=False)


# THE RECORDS A DOOR WRITES (D8): a commit that changes only these is a crossing or a seal — a
# record of the cursor or of a proof's state, not work. The same idea as the tester's hollow
# (cairn/devices/tester/hollow.py _RECORD_NAMES/_RECORD_DIRS), held separately under RULE 1.
_RECORD_NAMES = frozenset({"history.json", "state.json", ".artifact-journal.jsonl"})
_RECORD_DIRS = frozenset({"validations"})


def _is_record(path: str) -> bool:
    p = Path(path)
    return p.name in _RECORD_NAMES or bool(_RECORD_DIRS & set(p.parts))


NOT_DONE = "This voyage is NOT complete: its remaining steps are still to be built."


def landed(ticket: str, cursor: str, repo: Path) -> str:
    """The ALREADY LANDED section (ticket 80518446bfc8): the ticket's cursor and every commit
    whose message names the ticket id, oldest first. Measured 2026-10-07 on 41202d4c8d3b: a
    reader told every ticket is unbuilt raised work already landed at 9154af40 and fc17a873
    as a gap. The reader still gets text, never the repository (D4). A commit whose every
    changed file is a record is left out (D8): measured 2026-10-08 (F22(b)), 0d83860a — a
    PROVEME crossing the kick-back undid — listed as landed hid the crossing-command gap."""
    try:
        out = subprocess.run(["git", "-C", str(repo), "log", "--reverse", "--name-only",
                              "--format=%x1e%h %s", f"--grep={ticket}"],
                             capture_output=True, text=True, check=True).stdout
    # NEVER str(exc): a CalledProcessError carries the command line, and the repo path in
    # the reader's text is repository content the reader must not see (D7).
    except subprocess.CalledProcessError as exc:
        return f"\n# ALREADY LANDED\n\n{NOT_DONE}\n\n(landed commits could not be read: git log exited {exc.returncode})\n"
    except OSError as exc:
        return ("\n# ALREADY LANDED\n\n" + NOT_DONE + "\n\n(landed commits could not be read: "
                + (exc.strerror or type(exc).__name__) + ")\n")
    lines = []
    for chunk in out.split("\x1e"):
        rows = [l for l in chunk.splitlines() if l.strip()]
        if not rows:
            continue
        paths = rows[1:]
        if paths and all(_is_record(p) for p in paths):
            continue
        lines.append(rows[0])
    return ("\n# ALREADY LANDED\n\n" + NOT_DONE + "\n\ncursor: " + cursor + "\n\n"
            + ("\n".join(lines) if lines else "(nothing landed for this ticket)") + "\n")


def render(ticket: str, *, root: Path | str | None = None, berths_root=None,
           repo: Path | str | None = None) -> tuple[str, str, Path]:
    """The text the reader is handed: the ticket as ``reader_view`` shows it after the standing voyage-craft note, the standing chart berths
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
    parts = [prompt(), "\n\n# VOYAGE CRAFT\n\n" + voyage_craft(), "\n\n# THE TICKET\n\n```json\n" + reader_view(blob) + "\n```\n"]
    try:
        cursor = json.loads(blob).get("workflow_and_state") or "(no cursor)"
    except (json.JSONDecodeError, AttributeError):
        cursor = "(no cursor)"
    parts.append(landed(ticket, str(cursor), repo))
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
    # Stripping CLAUDECODE takes the child out of the session, so it says whose hand it is
    # (ticket a135bdb13646): CAIRN_USER set is a machine, unset is Akien.
    env["CAIRN_USER"] = "rehearsal"
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


def _only_missing(lacks: list[str]) -> list[int] | None:
    """The missing decision ids when EVERY lack is a missing-id lack, else None."""
    ids: list[int] = []
    for lack in lacks:
        m = _MISSING_LACK.match(lack)
        if not m:
            return None
        ids.extend(int(x) for x in re.findall(r"D(\d+)", m.group(1)))
    return ids or None


def read_tree(text: str, reader: Reader, n: int, *, ticket: str, sha: str,
              decision_ids: set[int] | None = None) -> tuple[dict, list[dict]]:
    """Read ``n`` of three: call the reader, check the shape, re-read on a schema failure
    (D5) up to ``RETRIES_PER_READ`` times. Identity fields are stamped from truth AFTER the
    shape passes — the reader's own ``ticket``/``read`` are never trusted. Returns the tree
    and the meta of every attempt."""
    schema_doc = schema()
    attempts: list[dict] = []
    handed_back = text
    earlier: list | None = None     # the nodes a patch attempt merges into (c3f8efa612ce)
    patch_ids: set[int] | None = None
    for attempt in range(1, RETRIES_PER_READ + 2):
        tree, meta = reader(handed_back, schema_doc)
        kind = "patch" if earlier is not None else "whole"
        if tree is not None and earlier is not None:
            # the patch reply is validated against the missing set alone, then merged and the
            # merged tree validated against the full set
            lacks = validate(tree, patch_ids)
            if not lacks:
                tree = {**tree, "nodes": [*earlier, *tree["nodes"]]}
                lacks = validate(tree, decision_ids)
            elif not validate(tree, decision_ids):
                lacks = []      # the reader answered the patch with a whole tree that passes: take it
        else:
            lacks = validate(tree, decision_ids) if tree is not None else [meta.get("error") or "reader returned nothing"]
        attempts.append({"attempt": attempt, "read": n, "kind": kind, "schema_lacks": lacks, **meta})
        if not lacks:
            return {"ticket": ticket, "ticket_sha256": sha, "read": n, "nodes": tree["nodes"]}, attempts
        missing = _only_missing(lacks)
        if missing and tree is not None:
            # D1: patch only when every lack is a missing id — a doubled id or a shape lack
            # cannot say which node the reader meant, so it re-reads whole
            earlier, patch_ids = list(tree["nodes"]), set(missing)
            handed_back = text + HANDED_BACK_MISSING.format(
                lacks="\n".join(f"- {l}" for l in lacks),
                missing="\n".join(f"- D{i}" for i in sorted(missing)),
                earlier=json.dumps(earlier, indent=1, ensure_ascii=False))
            continue
        earlier = patch_ids = None
        # A re-read is told what it lacked. MEASURED 2026-09-15 on this machine's own ticket
        # (36 decisions): read 3 returned D1..D17 and nothing after, three times running, at
        # $0.27 a time — the same text to the same reader is the same mistake, and a re-read
        # that learns nothing is a coin toss on temperature. The re-read stays cold with
        # respect to the OTHER two reads (D1); it is warm only to its own refusal.
        handed_back = text + HANDED_BACK.format(lacks="\n".join(f"- {l}" for l in lacks))
    raise ReaderFailed(
        f"read {n}: no tree passed the schema in {RETRIES_PER_READ + 1} attempts — last lacks: "
        + "; ".join(attempts[-1]["schema_lacks"][:5]), attempts)


# ---------------------------------------------------------------------------
# the diff (D6) — deterministic, by code

_DECISION_ID = re.compile(r"\bD(\d+)\b")


def cites_a_decision(step: str, assumption: str, decision_ids) -> bool:
    """A reader's assumption is settled when it names ANOTHER decision the ticket carries
    (Akien, open-ba8f0eaca8cd: "yes ... with that condition" — the id must resolve in the
    same ticket). The step's own number never counts; an id the ticket does not carry never
    counts."""
    if not decision_ids or not assumption:
        return False
    own = re.fullmatch(r"D(\d+)", (step or "").strip())
    own_n = int(own.group(1)) if own else None
    return any(int(m) in decision_ids and int(m) != own_n for m in _DECISION_ID.findall(assumption))


_MODULE_NAME = re.compile(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*")


def look(item: dict, roots) -> bool:
    """Ticket 7a31059daa23 D3: whether one thing a reader named is THERE. A path is found
    when it exists (absolute after expanduser, else under any root); a module is found when
    its source file exists under any root (``a/b.py``, ``a/b/__init__.py`` or
    ``a/b/__main__.py``). Only stats files: a look never imports and never runs anything,
    so naming a module cannot execute it."""
    name = item.get("name")
    if not (isinstance(name, str) and name):
        return False
    if item.get("kind") == "path":
        expanded = os.path.expanduser(name)
        if os.path.isabs(expanded):
            return Path(expanded).exists()
        # FIXME 2: a ticket spells a path from its root ("CairnCommons/tickets/…"), so a name
        # whose first segment IS a root's own name is read under that root — only a declared
        # root's name, never a sibling of it.
        parts = Path(name).parts
        return any((Path(root) / name).exists()
                   or (parts[:1] == (Path(root).name,) and (Path(root).parent / name).exists())
                   for root in roots)
    if item.get("kind") == "module":
        if not _MODULE_NAME.fullmatch(name):
            return False
        rel = Path(*name.split("."))
        return any((Path(root) / rel).with_suffix(".py").is_file()
                   or (Path(root) / rel / "__init__.py").is_file()
                   or (Path(root) / rel / "__main__.py").is_file() for root in roots)
    return False


def world_looker(roots) -> Callable[[dict], dict | None]:
    """Ticket 7a31059daa23 D4: the looker ``gaps`` settles by. For a builds_under_assumption
    node naming a non-empty ``looks_at`` it returns what was looked at and whether every
    thing was found; for any other node, None — so cannot_proceed never settles by the
    world, and a node naming nothing is untouched."""
    roots = [Path(r) for r in roots]

    def looker(node: dict) -> dict | None:
        looks = node.get("looks_at")
        if node.get("state") != "builds_under_assumption" or not isinstance(looks, list) or not looks:
            return None
        looked = [{"kind": i.get("kind"), "name": i.get("name"), "found": look(i, roots)}
                  for i in looks if isinstance(i, dict)]
        return {"looked_at": looked, "settled": bool(looked) and all(x["found"] for x in looked)}
    return looker


def gaps(reads: list[dict], decision_ids: set[int] | None = None,
         looker: Callable[[dict], dict | None] | None = None) -> list[dict]:
    """D6, verbatim: *"any node not builds_as_written in any read; any step present in one
    read and absent in another after case-folding through cairn.tools.system_word; any two
    reads whose assumption text differs on the same step."* Steps fold (a word the reader
    could type); assumption text is free text and never folds. One gap per (kind, step),
    reads merged, sorted by (kind, step) so two runs over the same trees write the same
    list. Amended (open-d71a52522428): a step named ``unlisted: <text>`` in any read is a
    gap of kind ``unlisted`` — the ticket owes the decision that would name it. Amended
    (open-ba8f0eaca8cd): with ``decision_ids`` a builds_under_assumption node whose assumption
    names another carried decision id (cites_a_decision) is settled — it raises no ``assumes``
    gap and its text joins no ``assumption_differs`` comparison; without ids nothing settles.
    Amended (7a31059daa23 D5): with a ``looker`` a node the world settles (every thing in its
    ``looks_at`` found) is settled the same way, and an unsettled one's ``assumes`` gap carries
    ``measured_absent`` naming each thing not found; without a looker nothing changes."""
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

    def world(node) -> dict | None:
        return looker(node) if looker is not None else None

    def settled(node) -> bool:
        if node["state"] != "builds_under_assumption":
            return False
        if cites_a_decision(node["step"], node.get("assumption", "").strip(), decision_ids):
            return True
        r = world(node)
        return r is not None and r["settled"]

    steps_by_read: list[dict[str, dict]] = []
    for r in reads:
        seen: dict[str, dict] = {}
        for node in r.get("nodes", []):
            seen.setdefault(fold(node["step"]), node)
            if node["step"].startswith(UNLISTED):
                gap("unlisted", node["step"], r["read"],
                    would_settle=node.get("would_settle", "").strip())
            if node["state"] == "builds_under_assumption" and not settled(node):
                gap("assumes", node["step"], r["read"],
                    assumption=node.get("assumption", "").strip(),
                    would_settle=node.get("would_settle", "").strip())
                for x in (world(node) or {}).get("looked_at", []):
                    if not x["found"]:
                        gap("assumes", node["step"], r["read"], measured_absent=x["name"])
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
        live = [i for i in present if not settled(steps_by_read[i][folded])]
        texts = {steps_by_read[i][folded].get("assumption", "").strip() for i in live}
        texts.discard("")
        if len(texts) > 1:
            for i in live:
                gap("assumption_differs", name, reads[i]["read"],
                    assumption=steps_by_read[i][folded].get("assumption", "").strip())
    out = sorted(by_kind_step.values(), key=lambda g: (g["kind"], fold(g["step"])))
    for g in out:
        g["reads"].sort()
    return out


def settled_by_world(reads: list[dict], looker: Callable[[dict], dict | None]) -> list[dict]:
    """Ticket 7a31059daa23 D13: every node the world settled, read then node order, with
    what was looked at — the record says why a step raised no gap, so a look too shallow to
    serve the goal is readable on the record that trusted it."""
    out = []
    for r in reads:
        for node in r.get("nodes", []):
            w = looker(node)
            if w is not None and w["settled"]:
                out.append({"step": node["step"], "read": r["read"], "looked_at": w["looked_at"]})
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


def _last_answer_at(ticket: str, root: Path | str | None) -> datetime | None:
    """When Akien last answered a question THIS machine opened on the ticket (D11's), or None."""
    from cairn.tools.question import question as Q
    stamps = []
    for q in Q.for_ticket(ticket, root=commons(root) / "questions"):
        if q.get("source") == "rehearsal" and q.get("resolved") and q.get("answered_at"):
            try:
                stamps.append(datetime.fromisoformat(str(q["answered_at"])))
            except ValueError:
                continue
    return max(stamps) if stamps else None


def _last_decide_at(ticket: str, root: Path | str | None) -> datetime | None:
    """When a gap was last disposed as a decision line on the ticket (``decide``), or None.
    Decisions written before 2026-09-23 carry no ``at`` and reset nothing."""
    tk = ticket_file(ticket, root)
    stamps = []
    for d in decision_ids_and_text(tk):
        if d.get("source") == "rehearsal" and d.get("at"):
            try:
                stamps.append(datetime.fromisoformat(str(d["at"])))
            except ValueError:
                continue
    return max(stamps) if stamps else None


def passes_since_clean(ticket: str, root: Path | str | None = None) -> int:
    """Unclean passes in a row — since the last clean record, since Akien ANSWERED the
    question the cap opened, or since a gap was last disposed with ``--decide``, whichever is
    latest. Each is new input the next passes run on, so the loop starts over at zero; without
    the answer reset the cap re-fires forever after the answer (measured 2026-09-17 on
    a705346aa75c), and without the decide reset the CLI's own ``dispose each: ... --decide``
    then ``rehearse again`` is unreachable at pass 5 (open-8b95d8bb20c5, Akien 2026-09-23:
    *"Reset it fully."*)."""
    resets = [t for t in (_last_answer_at(ticket, root), _last_decide_at(ticket, root)) if t]
    reset = max(resets) if resets else None
    n = 0
    for _, doc in records_for(ticket, root):
        if doc.get("clean"):
            n = 0
            continue
        try:
            before_answer = reset is not None and datetime.fromisoformat(str(doc.get("at"))) <= reset
        except ValueError:
            before_answer = False
        n = 0 if before_answer else n + 1
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
    failed: ReaderFailed | None = None
    for n in range(1, READS + 1):
        try:
            tree, attempts = read_tree(text, reader, n, ticket=ticket, sha=sha_at_read, decision_ids=ids)
        except ReaderFailed as exc:
            # A RUN THAT FAILS TO RUN IS STILL A RUN (ticket ba4166fe51c4 D2): it leaves a
            # ran:false record and counts toward the cap; it never moves the pointer.
            failed = exc
            meta.extend(exc.attempts)
            break
        reads.append(tree)
        meta.extend(attempts)
    if failed is not None:
        return _record_the_failed_run(ticket, root, failed, reads=reads, meta=meta, text=text,
                                      sha_at_read=sha_at_read, passes=passes, by=by)
    repo_path = Path(repo) if repo is not None else REPO
    looker = world_looker([repo_path, commons(root)])      # 7a31059daa23 D13
    found = gaps(reads, ids, looker)
    sbw = settled_by_world(reads, looker)
    clean = not found
    try:
        reaches = log_reaches(found, ticket_log.read_log(tk))
    except (OSError, ValueError) as exc:   # an unreadable log is said on the record, never skipped
        reaches = [{"unreadable_log": f"{type(exc).__name__}: {exc}"}]
    stamp = _stamp()
    rec_path = _record_path(ticket, root, stamp)
    rec_rel = rec_path.relative_to(commons(root)).as_posix()
    if clean:
        # D8 as amended: the pointer lands first, the record hashes what the lane will see.
        # The pointer is trail, so it is a line on the ticket's log (fad76bb5d1f5); the plan's
        # bytes are not touched.
        ticket_log.append_log(tk, "rehearsal", {"record": rec_rel}, actor=by or "rehearsal",
                              why=f"rehearsal clean on pass {passes + 1}: {rec_rel}")
        live = tk.read_bytes()
        sha_live = _sha(live)
        design = design_sha(live)
    else:
        sha_live = sha_at_read
        blob = tk.read_bytes()
        design = design_sha(blob) if _sha(blob) == sha_at_read else None
    record = {
        "ticket": ticket,
        "record": rec_rel,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pass": passes + 1,
        "ran": True,
        "clean": clean,
        "ticket_sha256": sha_live,
        "ticket_sha256_at_read": sha_at_read,
        "design_sha256": design,
        "reads": reads,
        "gaps": found,
        **({"settled_by_world": sbw} if sbw else {}),
        # gaps a ticket-log line already speaks to (fad76bb5d1f5 D1: heuristic token overlap)
        "log_reaches": reaches,
        "log_reach_count": sum(1 for r in reaches if "gap_step" in r),
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


def _record_path(ticket: str, root: Path | str | None, stamp: str) -> Path:
    rec_path = records_dir(root) / f"{ticket}-{stamp}.json"
    n = 1
    while rec_path.exists():   # two passes inside one second are two records, never one overwritten
        n += 1
        rec_path = records_dir(root) / f"{ticket}-{stamp}-{n}.json"
    return rec_path


def _record_the_failed_run(ticket: str, root: Path | str | None, failed: ReaderFailed, *,
                           reads: list[dict], meta: list[dict], text: str, sha_at_read: str,
                           passes: int, by: str | None) -> dict:
    """The ran:false record (ticket ba4166fe51c4 D2): same door, same naming, same verb as a
    pass that ran. ``clean`` is false and ``gaps`` empty — the reader failed, the ticket was
    not judged — and the ticket's rehearsal pointer is never written (D4)."""
    rec_path = _record_path(ticket, root, _stamp())
    record = {
        "ticket": ticket,
        "record": rec_path.relative_to(commons(root)).as_posix(),
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pass": passes + 1,
        "ran": False,
        "clean": False,
        "why": str(failed),
        "ticket_sha256_at_read": sha_at_read,
        "reads": reads,
        "gaps": [],
        "meta": {
            "model": MODEL,
            "attempts": meta,
            "cost_usd": round(sum((m.get("cost_usd") or 0) for m in meta), 6),
            "duration_ms": sum((m.get("duration_ms") or 0) for m in meta),
            "rendered_chars": len(text),
            "by": by,
        },
    }
    door.write(str(rec_path), json.dumps(record, indent=2, ensure_ascii=False) + "\n",
               verb="rehearse", why=f"pass {passes + 1} over {ticket}: did not run — {failed}")
    return dict(record, path=str(rec_path))


def drive_a_failed_run(scratch: Path | str) -> dict:
    """The runner's failure path, driven on purpose (ticket ba4166fe51c4 D20): one pass with a
    reader that returns nothing, over a scratch commons built under ``scratch`` with one
    testing ticket. Its trail is ``<scratch>/CairnCommons/rehearsals/*.json``. This is the
    verb build_inspector's ``a_run_that_fails_to_run_leaves_a_trail`` drives (RULE 1: the
    sieve calls this public verb, never the code)."""
    scratch = Path(scratch)
    root = scratch / "CairnCommons"
    for d in ("tickets", "rehearsals", "questions"):
        (root / d).mkdir(parents=True, exist_ok=True)
    (scratch / "cairn").mkdir(parents=True, exist_ok=True)
    (root / "tickets" / "_charter+why.json").write_text(json.dumps({
        "plan_fields": ["id", "title", "intention", "workflow_and_state", "decisions", "questions"],
        "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}}) + "\n")
    tid = "d71fe0000001"
    (root / "tickets" / f"{tid}-testing-a-driven-failed-run.json").write_text(json.dumps({
        "id": tid, "title": "testing: a driven failed run", "intention": "testing fixture",
        "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PR",
        "decisions": [{"n": 1, "text": "D1 testing: build the widget", "by": "drive", "source": "cast"}],
        "questions": []}, indent=2) + "\n")

    def nothing(text, schema_doc):
        return None, {"model": "drive", "cost_usd": 0.0, "duration_ms": 0,
                      "error": "testing: the driven reader returns nothing"}

    door.set_diagnostic_roots({"cairn": scratch / "cairn", "CairnCommons": root})
    try:
        return rehearse(tid, reader=nothing, root=root, berths_root=scratch / "no-berths",
                        repo=scratch / "no-repo", by="drive")
    finally:
        door.set_diagnostic_roots(None)


def _open_the_question(ticket: str, root: Path | str | None) -> dict:
    """The sixth pass (D11): one question on the ticket naming the standing gaps; no read.
    The gaps come from the latest record that RAN (ticket ba4166fe51c4 D16): a ran:false
    record names none, and reading it would hide the last real ones."""
    from cairn.tools.question import question as Q
    qroot = commons(root) / "questions"
    ran = [doc for _, doc in records_for(ticket, root) if doc.get("ran") is not False]
    standing = (ran[-1].get("gaps") or []) if ran else []
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


def names_as_replaced(step: str, line: str) -> int | None:
    """The 996668eceef1 shape (ticket c70eeeef73ac): a step shaped ``D<n>`` whose line names
    that same D<n> as replaced or superseded — a line meant to stand IN PLACE of D<n>, which
    ``decide`` would land BESIDE it. Returns n, or None. Any other line at a D<n> step is a
    gap disposed at its own label and lands (the peer's ruling 2026-10-11 on clause 2)."""
    m = re.fullmatch(r"D(\d+)", (step or "").strip())
    if not m:
        return None
    n = m.group(1)
    if (re.search(rf"\b(replac(?:es|ed|ing)|supersed(?:es|ed|ing))\s+D{n}\b", line, re.I)
            or re.search(rf"\bD{n}\b(?:'s)?\s+(?:is\s+|are\s+)?(?:replaced|superseded)\b", line, re.I)):
        return int(n)
    return None


def decide(ticket: str, step: str, line: str, *, by: str, root: Path | str | None = None,
           supersedes: list[int] | None = None) -> dict:
    """A gap disposed as a decision line on the ticket (D3: a ticket is a list of one-line
    decisions): appends ``{n, text, by, step, source: "rehearsal"}`` to ``decisions`` through
    the door's ``cast`` verb. The next pass reads the edited ticket, so the pointer (if any)
    goes stale by construction — the lane demands a fresh clean record.

    ``supersedes=[n, ...]`` (ticket c70eeeef73ac) retires each named line INTO the new one in
    the same act — retire()'s rules and refusals, the plan written once. Without it, a line at
    a ``D<n>`` step that names D<n> as replaced is refused naming --supersedes."""
    tk = ticket_file(ticket, root)
    if tk is None:
        raise Refused(f"no ticket file for {ticket!r}")
    if not (isinstance(line, str) and line.strip()):
        raise Refused("a decision is one line of text — an empty one decides nothing")
    if not (isinstance(by, str) and by.strip()):
        raise Refused("--by: who made this decision (D3 — each decision carries who made it)")
    if not supersedes:
        shaped = names_as_replaced(step, line)
        if shaped is not None:
            raise Refused(f"the line at step D{shaped} names D{shaped} as replaced — decide would land it "
                          f"BESIDE D{shaped}, not in its place; say --supersedes D{shaped} to retire D{shaped} "
                          f"into the new line in one act (c70eeeef73ac); nothing written")
    doc = json.loads(tk.read_text(encoding="utf-8"))
    have = doc.get("decisions")
    have = list(have) if isinstance(have, list) else []
    n = 1 + max([d.get("n", 0) for d in have if isinstance(d, dict)] + _retired_on_log(tk), default=0)
    entry = {"n": n, "text": line.strip(), "by": by.strip(), "step": step.strip(), "source": "rehearsal",
             "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    why = f"rehearsal gap at '{step.strip()}' decided by {by.strip()}: D{n}"
    if supersedes:
        want = sorted(set(supersedes))
        because = f"superseded by D{n}"
        lacks = _retire_lacks(doc, tk, want, by, because, into=None)
        if lacks:
            raise Refused(f"decide refused over {ticket} — {len(lacks)} lack(s): " + "; ".join(lacks))
        at = entry["at"]
        why = f"{why}, superseding {', '.join('D%d' % k for k in want)}"
        by_n = {d["n"]: d for d in have if isinstance(d, dict) and isinstance(d.get("n"), int)}
        for k in want:
            by_n[k]["retired"] = {"by": by.strip(), "at": at, "because": because, "into": n}
            # a retired line is trail (fad76bb5d1f5): it moves whole to the log, then leaves the plan
            ticket_log.append_log(tk, "decision_retired", {"decision": by_n[k]}, actor=by.strip(),
                                  why=f"retired D{k} by {by.strip()} into D{n}: {because}")
        have = [d for d in have if not (isinstance(d, dict) and d.get("n") in want)]
    have.append(entry)
    doc["decisions"] = have
    _write_ticket(tk, doc, why=why)
    return entry


def _retire_lacks(doc: dict, tk: Path, want: list[int], by: str, because: str,
                  into: int | None) -> list[str]:
    """Every reason the lines ``want`` cannot be retired, named once (retire()'s rules,
    shared with ``decide(supersedes=)``): an id absent or already retired; a line another
    author wrote; a live line still citing a retired id; an ``into`` absent, retired, or
    itself being retired; no ``because``."""
    have = [d for d in (doc.get("decisions") or []) if isinstance(d, dict) and isinstance(d.get("n"), int)]
    by_n = {d["n"]: d for d in have}
    on_log = set(_retired_on_log(tk))
    lacks: list[str] = []
    if not (isinstance(by, str) and by.strip()):
        lacks.append("--by: who is retiring these lines")
    if not (isinstance(because, str) and because.strip()):
        lacks.append("--because: why these lines are superseded — an empty reason retires nothing")
    if not want:
        lacks.append("no decision named to retire")
    for n in want:
        d = by_n.get(n)
        if d is None:
            lacks.append(f"D{n} is already retired" if n in on_log else f"D{n} is not on the ticket")
        elif d.get("retired"):
            lacks.append(f"D{n} is already retired")
        elif isinstance(by, str) and fold(str(d.get("by") or "")) != fold(by.strip()):
            lacks.append(f"D{n} was written by {d.get('by')!r}, not {by.strip()!r} — not yours to retire")
    for d in have:
        if d["n"] in want or d.get("retired"):
            continue
        text = str(d.get("text", "")).split(" [settled by", 1)[0]
        cited = [n for n in want if re.search(rf"\bD{n}\b", text)]
        if cited:
            lacks.append(f"D{d['n']} still cites {', '.join('D%d' % n for n in cited)} — retire or re-decide it too")
    if into is not None:
        t = by_n.get(into)
        if t is None:
            lacks.append(f"--into D{into} is retired" if into in on_log else f"--into D{into} is not on the ticket")
        elif t.get("retired"):
            lacks.append(f"--into D{into} is retired")
        elif into in want:
            lacks.append(f"--into D{into} is one of the lines being retired")
    return lacks


def retire(ticket: str, ns: list[int], *, by: str, because: str, into: int | None = None,
           root: Path | str | None = None) -> list[dict]:
    """Superseded decision lines retired through the door (ticket 4968b5d18645): each named
    entry gains ``retired = {by, at, because, into}`` and keeps its text, so the file still
    says who said what, while ``reader_view`` and ``decision_ids_of`` stop handing it on.
    Every lack is named in ONE refusal and nothing is written: an id absent or already
    retired; a line another author wrote (his lines are not CC's to fold); a live line still
    citing a retired id; an ``into`` absent, retired, or itself being retired; no ``because``."""
    tk = ticket_file(ticket, root)
    if tk is None:
        raise Refused(f"no ticket file for {ticket!r}")
    doc = json.loads(tk.read_text(encoding="utf-8"))
    have = [d for d in (doc.get("decisions") or []) if isinstance(d, dict) and isinstance(d.get("n"), int)]
    by_n = {d["n"]: d for d in have}
    want = sorted(set(ns))
    lacks = _retire_lacks(doc, tk, want, by, because, into)
    if lacks:
        raise Refused(f"retire refused over {ticket} — {len(lacks)} lack(s): " + "; ".join(lacks))
    at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stamped = []
    why = (f"retired {', '.join('D%d' % n for n in want)} by {by.strip()}"
           f"{f' into D{into}' if into is not None else ''}: {because.strip()}")
    for n in want:
        by_n[n]["retired"] = {"by": by.strip(), "at": at, "because": because.strip(), "into": into}
        stamped.append(by_n[n])
    # a retired line is trail (fad76bb5d1f5): it moves whole to the log, then leaves the plan
    for d in stamped:
        ticket_log.append_log(tk, "decision_retired", {"decision": d}, actor=by.strip(), why=why)
    doc["decisions"] = [d for d in doc["decisions"]
                        if not (isinstance(d, dict) and d.get("n") in want)]
    _write_ticket(tk, doc, why=why)
    return stamped


def _retired_on_log(tk: Path) -> list[int]:
    """The ``n`` of every decision the ticket's log holds as retired — names the plan no
    longer carries and a new line must never reuse."""
    return [x["decision"]["n"] for x in ticket_log.read_log(tk, "decision_retired")
            if isinstance(x.get("decision"), dict) and isinstance(x["decision"].get("n"), int)]


def scope(ticket: str, ns: list[int], *, by: str, because: str,
          root: Path | str | None = None) -> list[dict]:
    """Decision lines scoped as context through the door (ticket eb05adbe0a0f): each named
    entry gains ``context = {by, at, because}`` and keeps its text, and ``reader_view`` hands it
    in a top-level ``context`` list while ``decision_ids_of`` leaves it out — a line that
    describes the voyage or the session is read for what it says, never judged as a step.
    Every lack is named in ONE refusal and nothing is written, as retire(): an id absent,
    already scoped or retired; a line another author wrote; no ``because``. No citation check:
    a scoped line stays visible to the reader."""
    tk = ticket_file(ticket, root)
    if tk is None:
        raise Refused(f"no ticket file for {ticket!r}")
    doc = json.loads(tk.read_text(encoding="utf-8"))
    have = [d for d in (doc.get("decisions") or []) if isinstance(d, dict) and isinstance(d.get("n"), int)]
    by_n = {d["n"]: d for d in have}
    want = sorted(set(ns))
    lacks: list[str] = []
    if not (isinstance(by, str) and by.strip()):
        lacks.append("--by: who is scoping these lines")
    if not (isinstance(because, str) and because.strip()):
        lacks.append("--because: why these lines are context — an empty reason scopes nothing")
    if not want:
        lacks.append("no decision named to scope")
    for n in want:
        d = by_n.get(n)
        if d is None:
            lacks.append(f"D{n} is not on the ticket")
        elif d.get("context"):
            lacks.append(f"D{n} is already scoped")
        elif d.get("retired"):
            lacks.append(f"D{n} is retired")
        elif isinstance(by, str) and fold(str(d.get("by") or "")) != fold(by.strip()):
            lacks.append(f"D{n} was written by {d.get('by')!r}, not {by.strip()!r} — not yours to scope")
    if lacks:
        raise Refused(f"scope refused over {ticket} — {len(lacks)} lack(s): " + "; ".join(lacks))
    at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stamped = []
    for n in want:
        by_n[n]["context"] = {"by": by.strip(), "at": at, "because": because.strip()}
        stamped.append(by_n[n])
    _write_ticket(tk, doc, why=f"scoped {', '.join('D%d' % n for n in want)} as context by {by.strip()}")
    return stamped


# ---------------------------------------------------------------------------
# the lane's question: is the ticket rehearsed clean, over these exact bytes?

def standing(ticket: str, root: Path | str | None = None) -> dict:
    """What the BUILDME lane reads: ``{ok, lack, record, ticket_sha256, live_sha256}``.
    ``ok`` iff the ticket's ``rehearsal`` pointer names a readable record that is clean and
    whose ``design_sha256`` equals ``design_sha`` of the live ticket — the DESIGN, so the cursor
    moving does not stale it (ticket 9fb045a476dc). A record written before that carries no
    ``design_sha256`` and stands on the whole bytes (``ticket_sha256``) as it did. Everything
    else is a named lack — no pointer, an unreadable record, an unclean one, a stale design."""
    tk = ticket_file(ticket, root)
    if tk is None:
        return {"ok": False, "lack": "no ticket file", "record": None}
    try:
        blob = tk.read_bytes()
        doc = json.loads(blob)
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "lack": f"ticket unreadable: {exc}", "record": None}
    try:
        lines = ticket_log.read_log(tk, "rehearsal")
    except (OSError, ValueError) as exc:
        return {"ok": False, "lack": f"ticket log unreadable: {exc}", "record": None, "live_sha256": _sha(blob)}
    # the last 'rehearsal' line on the log (fad76bb5d1f5); a v1 plan not yet split by
    # 29569fca68a3 still carries its pointer on the plan, and stands on it (D3)
    ptr = lines[-1].get("record") if lines else (doc.get("rehearsal") if isinstance(doc, dict) else None)
    if not isinstance(ptr, str) or not ptr.strip():
        return {"ok": False, "lack": "the ticket carries no rehearsal pointer (no 'rehearsal' line on its log) "
                                     "— `cairn rehearse <id>`",
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
    if rec.get("design_sha256"):
        stale = rec["design_sha256"] != design_sha(blob)
    else:   # a record written before ticket 9fb045a476dc stands on the whole bytes, as it did
        stale = rec.get("ticket_sha256") != _sha(blob)
    if stale:
        return {"ok": False, "lack": "the ticket was edited after its rehearsal — rehearse again",
                "record": ptr, "ticket_sha256": rec.get("ticket_sha256"), "live_sha256": _sha(blob)}
    return {"ok": True, "lack": None, "record": ptr, "ticket_sha256": rec.get("ticket_sha256"),
            "live_sha256": _sha(blob), "design_sha256": rec.get("design_sha256")}


# ---------------------------------------------------------------------------
# after PROVED (D14): the built proof against the converged tree

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "is", "it", "its", "for", "on", "with",
         "test", "that", "not", "by", "as", "at", "be", "from", "this", "no", "one", "into"}


def _tokens(s: str) -> set[str]:
    return {t for t in _TOKEN.findall(fold(s).replace("_", " ")) if t not in _STOP and len(t) > 1}


REACH = 4   # D1: shared significant tokens for a log line to speak to a gap — heuristic


def log_reaches(found: list[dict], log: list[dict], *, overlap: int = REACH) -> list[dict]:
    """The gaps a ticket-log line already speaks to (fad76bb5d1f5): words the plan did not
    carry and the log does. A gap's words are its step plus its assumption and would_settle
    texts; a line's are its whole JSON. One reach per gap — the line sharing the most tokens,
    ties to the lowest index — when that is at least ``overlap``:
    ``{gap_step, gap_kind, log_index, kind, overlap}``, ``kind`` the line's."""
    lines = [_tokens(json.dumps(x, ensure_ascii=False)) for x in log]
    out = []
    for g in found:
        words = _tokens(" ".join([g.get("step", ""), *g.get("assumption", []), *g.get("would_settle", [])]))
        best = max(range(len(lines)), key=lambda i: (len(words & lines[i]), -i), default=None)
        if best is not None and len(words & lines[best]) >= overlap:
            out.append({"gap_step": g.get("step"), "gap_kind": g.get("kind"), "log_index": best,
                        "kind": log[best].get("kind"), "overlap": len(words & lines[best])})
    return out


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


def teeth_bodies(proof: Path | str) -> dict[str, str]:
    """Each top-level ``def test_*`` in a proof file, in order, with its source. A ``def test_``
    inside a fixture string is not a tooth (8 phantoms measured 2026-10-18). A file that does
    not parse gives its names by line and empty bodies."""
    text = Path(proof).read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {t: "" for t in re.findall(r"^\s*def (test_\w+)\s*\(", text, flags=re.M)}
    return {n.name: ast.get_source_segment(text, n) or "" for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")}


def teeth_of(proof: Path | str) -> list[str]:
    """``def test_*`` names in a proof file, in order — the top-level ones."""
    return list(teeth_bodies(proof))


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _identifiers(s: str) -> set[str]:
    """The snake_case code names a text carries — a tooth's other names and dunders aside."""
    return {w for w in _IDENT.findall(s) if "_" in w.strip("_") and len(w) >= 5
            and not w.startswith("test_") and not (w.startswith("__") and w.endswith("__"))}


def _common(sets: list[set[str]]) -> set[str]:
    """Names more than half of three or more texts carry: they say which component, not which
    step (0539e85f8b2d's 'counting_block', measured 2026-10-18)."""
    if len(sets) < 3:
        return set()
    n: dict[str, int] = {}
    for d in sets:
        for w in d:
            n[w] = n.get(w, 0) + 1
    return {w for w, c in n.items() if c > len(sets) / 2}


def divergence(steps: list[str], teeth: list[str], *, overlap: int = 2,
               bodies: dict[str, str] | None = None) -> dict:
    """The diff both ways between the converged tree's steps and the built proof's teeth:
    a step is covered when some tooth shares ``overlap`` significant tokens with it, or —
    given the teeth's ``bodies`` — when the tooth's body uses a code identifier the step
    names that most steps and most teeth do not (870d26e0da47); a tooth is expected when
    some step does. ``{"steps_unproved": [...], "teeth_unforeseen": [...],
    "matched": [[step, tooth], ...]}`` — empty lists both ways is the rehearsal predicting
    the build."""
    st = {s: _tokens(s) for s in steps}
    tt = {t: _tokens(t) for t in teeth}
    si = {s: _identifiers(s) for s in steps}
    bi = {t: _identifiers((bodies or {}).get(t, "")) for t in teeth}
    drop = _common(list(si.values())) | _common(list(bi.values()))
    matched = [[s, t] for s in steps for t in teeth
               if len(st[s] & tt[t]) >= overlap or si[s] & bi[t] - drop]
    covered = {s for s, _ in matched}
    foreseen = {t for _, t in matched}
    return {"steps_unproved": [s for s in steps if s not in covered],
            "teeth_unforeseen": [t for t in teeth if t not in foreseen],
            "matched": matched}


def proof_divergence(steps: list[str], proofs: list[Path | str]) -> dict:
    """``divergence`` of the steps against every proof's teeth, read with their bodies."""
    bodies: dict[str, str] = {}
    for p in proofs:
        bodies.update(teeth_bodies(p))
    return divergence(steps, list(bodies), bodies=bodies)


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
    d = proof_divergence(steps, proofs)
    d["proofs"] = [str(p) for p in proofs]
    d["at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rec["divergence"] = d
    door.write(str(rec_path), json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
               verb="rehearse",
               why=f"divergence after PROVED over {ticket}: {len(d['steps_unproved'])} step(s) unproved, "
                   f"{len(d['teeth_unforeseen'])} tooth/teeth unforeseen")
    return d

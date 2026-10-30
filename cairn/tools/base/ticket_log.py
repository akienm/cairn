"""ticket_log — a ticket's trail, appended to its log through one door (ticket 76da3a283277).

A ticket is two files (Akien 2026-10-10, "Flat plan + .log.jsonl"): the PLAN
``tickets/<id>-<slug>.json`` — "always the 'current what to do' all questions answered, all
intentions clear", rewritten in place — and the LOG ``tickets/<id>-<slug>.log.jsonl`` beside
it — "the questions and the answering of them", one JSON object per line, only ever grown.

The plan's field set and the log's kinds are declared ONCE, in the store charter beside the
plans (``_charter+why.json``: ``plan_fields``, ``log_kinds``); this module reads them there and
keeps no second copy. Every line is ``{kind, at, actor, **body}`` and lands through the
artifact door, whose ``.jsonl`` rule (9df0f230a087) refuses any write that is not a pure
append — so "append-only" is the door's physics, not this module's promise.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_RESERVED = ("kind", "at", "actor")

# The two v1 trail fields with their own log kinds; every other non-plan key is a 'field'.
_PHASE_WRITES = "phase_writes"
_REHEARSAL = "rehearsal"

# The plan's one statement of intent, and the v1 keys that carried it, in precedence order.
_INTENTION = "intention"
_INTENTION_V1 = ("intent", "what")


_LIVE_CHARTER = Path(__file__).resolve().parents[4] / "CairnCommons" / "tickets" / "_charter+why.json"


def _charter(plan: Path) -> dict:
    """The store charter beside ``plan``; the live one when none sits there (a proof's scratch
    tickets dir carries plans without a charter, and the declared sets are the live ones)."""
    here = plan.parent / "_charter+why.json"
    return json.loads((here if here.is_file() else _LIVE_CHARTER).read_text(encoding="utf-8"))


def plan_fields(plan: str | Path) -> tuple[str, ...]:
    """The plan's declared top-level keys, read from the store charter beside ``plan``."""
    return tuple(_charter(Path(plan))["plan_fields"])


def state_fields(plan: str | Path) -> tuple[str, ...]:
    """The state file's declared keys (ticket 284798998ab0), read as ``plan_fields`` is."""
    return tuple(_charter(Path(plan)).get("state_fields") or ())


def log_fields(plan: str | Path) -> tuple[str, ...]:
    """The census's log-bound fields (ticket 284798998ab0): a cast carrying one writes it as a
    kind 'field' line rather than onto the plan."""
    return tuple(_charter(Path(plan)).get("log_fields") or ())


def log_kinds(plan: str | Path) -> dict:
    return dict(_charter(Path(plan))["log_kinds"])


def _plan(ticket: str | Path) -> Path:
    """A plan path as given, or a ticket id/slug resolved by the transitions resolver."""
    p = Path(ticket)
    if p.suffix == ".json" and p.is_file():
        return p
    from cairn.tools.base.ticket_file import find_ticket as _find_ticket  # at call time
    found = _find_ticket(str(ticket))
    if found is None:
        raise ValueError(f"ticket {ticket!r} resolves to no plan file")
    return found


def log_path(plan: str | Path) -> Path:
    """``<dir>/<id>-<slug>.log.jsonl`` beside ``<dir>/<id>-<slug>.json``."""
    p = Path(plan)
    if not p.name.endswith(".json"):
        raise ValueError(f"{p} is not a plan file (*.json)")
    return p.with_name(p.name[:-5] + ".log.jsonl")


def _line(plan: Path, kind: str, body: dict, actor: str, at: str) -> dict:
    if kind not in log_kinds(plan):
        raise ValueError(f"log kind {kind!r} is not declared in {plan.parent / '_charter+why.json'} "
                         f"log_kinds {sorted(log_kinds(plan))}; nothing written")
    clash = [k for k in _RESERVED if k in body]
    if clash:
        raise ValueError(f"log body keys {clash} are reserved for the line envelope; nothing written")
    return {"kind": kind, "at": at, "actor": actor, **body}


def _append_lines(plan: Path, lines: list[dict], why: str) -> dict:
    from cairn.tools.artifact import artifact as door
    log = log_path(plan)
    old = log.read_bytes() if log.exists() else b""
    tail = "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in lines)
    return door.write(log, old + tail.encode("utf-8"), verb="append", why=why, count=len(lines))


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def append_log(ticket: str | Path, kind: str, body: dict, *, actor: str, why: str) -> dict:
    """Append one ``{kind, at, actor, **body}`` line to the ticket's log, through the door.

    Refuses (ValueError, nothing written) a kind the charter does not declare and a body key
    that would overwrite the envelope. Returns the line written."""
    plan = _plan(ticket)
    line = _line(plan, kind, dict(body), actor, _now())
    _append_lines(plan, [line], why)
    return line


def read_log(ticket: str | Path, kind: str | None = None) -> list[dict]:
    """Every line of the ticket's log in order ([] when it has none), optionally one kind."""
    log = log_path(_plan(ticket))
    if not log.exists():
        return []
    out = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [x for x in out if kind is None or x.get("kind") == kind]


def field_value(ticket: str | Path, field: str, default=None):
    """The last logged value of a log-bound ``field`` (a kind 'field' line), else ``default``:
    how a reader reads ``from_idea`` or ``measurements_since_cast`` once the split has moved
    it off the plan (ticket 284798998ab0)."""
    hits = [x for x in read_log(ticket, "field") if x.get("field") == field]
    return hits[-1]["value"] if hits else default


def split(ticket: str | Path, *, actor: str, why: str) -> dict:
    """Move every v1 trail item off a plan into its log, losslessly; idempotent.

    - each top-level key in state_fields -> the state file beside the plan, merged over the
      one standing there (ticket 284798998ab0; counted as kind 'state');
    - each other top-level key outside plan_fields -> kind 'field' {field, value};
    - each entry of a non-empty ``phase_writes`` list -> kind 'phase_write' {record};
    - a string ``rehearsal`` pointer -> kind 'rehearsal' {record};
    - each decision carrying 'retired' -> kind 'decision_retired' {decision} (whole);
    - a plan then left with no 'intention' takes a v1 string 'intent', else 'what', as it,
      with one kind 'renamed' {from, to[, was]} line (the v1 key's 'field' line stays too;
      a blank 'intention' it replaces rides as ``was``).

    An empty or non-list ``phase_writes`` and a non-string ``rehearsal`` go as 'field' lines,
    so ``reconstruct`` returns them exactly. The log lines land first, then the plan is
    rewritten without what moved; a plan already v2-clean appends and writes nothing.
    Returns ``{'moved': {kind: count}}``."""
    from cairn.tools.artifact import artifact as door
    plan = _plan(ticket)
    doc = json.loads(plan.read_text(encoding="utf-8"))
    keep = set(plan_fields(plan))
    to_state = set(state_fields(plan))
    at = _now()
    lines: list[dict] = []
    new = {}
    state = {}
    for key, value in doc.items():
        if key in to_state:
            state[key] = value
        elif key == _PHASE_WRITES and isinstance(value, list) and value:
            lines += [_line(plan, "phase_write", {"record": r}, actor, at) for r in value]
        elif key == _REHEARSAL and isinstance(value, str):
            lines.append(_line(plan, "rehearsal", {"record": value}, actor, at))
        elif key not in keep:
            lines.append(_line(plan, "field", {"field": key, "value": value}, actor, at))
        elif key == "decisions" and isinstance(value, list):
            live = []
            for d in value:
                if isinstance(d, dict) and "retired" in d:
                    lines.append(_line(plan, "decision_retired", {"decision": d}, actor, at))
                else:
                    live.append(d)
            new[key] = live
        else:
            new[key] = value
    stood = {"was": new[_INTENTION]} if _INTENTION in new else {}
    named = _name_intention(new, [*read_log(plan, "field"), *lines])
    if named:
        body = {"from": named, "to": _INTENTION, **stood}
        lines.append(_line(plan, "renamed", body, actor, at))
    moved: dict[str, int] = {}
    for x in lines:
        moved[x["kind"]] = moved.get(x["kind"], 0) + 1
    if state:
        moved["state"] = len(state)
    if not lines and not state:
        return {"moved": moved}
    if lines:
        _append_lines(plan, lines, why)
    if state:
        from cairn.tools.base.ticket_file import state_path, write_state  # at call time
        sp = state_path(plan)
        standing = json.loads(sp.read_text(encoding="utf-8")) if sp.is_file() else {}
        write_state(plan, {**standing, **state}, why=why, verb="cast")
    raw = plan.read_bytes()
    door.write_json(plan, new, verb="cast", why=why, ensure_ascii=not _has_non_ascii(raw),
                    newline=raw.endswith(b"\n"))
    return {"moved": moved}


def _blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _name_intention(new: dict, field_lines: list[dict]) -> str | None:
    """A plan left with no 'intention' (absent, or blank: it states nothing) takes a v1 string
    'intent', else a string 'what', as its one statement of intent (29569fca68a3, CC's call
    per Akien 2026-10-09: one key, renamed once, at the split). The v1 key's own 'field' line
    stays in the log; a non-string value is trail and is never promoted. Returns the key
    renamed, or None. Mutates ``new``."""
    if not _blank(new.get(_INTENTION)):
        return None
    values = {x["field"]: x["value"] for x in field_lines if x.get("kind") == "field"}
    for key in _INTENTION_V1:
        if isinstance(values.get(key), str) and values[key].strip():
            new[_INTENTION] = values[key]
            return key
    return None


def _has_non_ascii(raw: bytes) -> bool:
    return any(b > 127 for b in raw)


def reconstruct(plan_doc: dict, log: list[dict], state: dict | None = None) -> dict:
    """The v1 doc a split started from: the plan, then its ``state`` file's keys, plus every
    trail line put back.

    a 'renamed' line's ``to`` key leaves the plan, or takes back the blank ``was`` it replaced
    (its v1 key returns by its 'field' line);
    'field' values return to their keys; 'phase_write' records rebuild ``phase_writes`` in
    log order; the last 'rehearsal' record is the pointer; retired decisions rejoin the live
    ones in ``n`` order (the corpus measured 2026-10-10: every decisions list carrying a
    retired line is sorted by integer n)."""
    doc = {**plan_doc, **(state or {})}
    for x in log:
        if x.get("kind") == "renamed":
            if "was" in x:
                doc[x["to"]] = x["was"]
            else:
                doc.pop(x["to"], None)
    pw = [x["record"] for x in log if x.get("kind") == "phase_write"]
    if pw:
        doc[_PHASE_WRITES] = pw
    reh = [x["record"] for x in log if x.get("kind") == "rehearsal"]
    if reh:
        doc[_REHEARSAL] = reh[-1]
    for x in log:
        if x.get("kind") == "field":
            doc[x["field"]] = x["value"]
    retired = [x["decision"] for x in log if x.get("kind") == "decision_retired"]
    if retired:
        doc["decisions"] = sorted([*doc.get("decisions", []), *retired], key=lambda d: d.get("n"))
    return doc

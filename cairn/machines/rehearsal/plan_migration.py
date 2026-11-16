"""THE MECHANICAL STEP OF OUTLINE 9.3.5.1.2.1 (ticket aa3e9a70db47, Q#100).

Every ticket still in flight takes the outcomes shape: the plan is constraints, then
outcomes ``{n, claim, writes_to, reads, after}``, then resources. This module moves the plan
and judges nothing; the judgement happens at build-open (sibling 4d8a2c6e91f7), where each
outcome still awaiting its claim either gets one or moves to constraints.

- **clauses first.** A falsifier carrying a numbered ``clauses`` list becomes outcomes 1..k,
  each ``{n, claim, writes_to: [], reads: [], after: []}`` with its n kept. The ``falsifier``
  key goes. A prose falsifier (a string, or a dict with no clauses list) stays as written,
  and the report names it.
- **trail out.** A decision is trail when its text, once the leading ``D<n>:`` label is
  dropped and the text case-folded, opens with one of D2's markers: fold, MEASURED, SETTLES,
  re-point or superseded. Each trail line moves whole to the ticket's log (kind
  ``decision_retired``) and leaves the plan. "repoint" without the hyphen is a build step
  ("D10: repoint the sibling proof", measured 2026-11-16) and is not trail.
- **by out.** Each remaining decision's ``by`` is logged (kind ``field``, value
  ``{n, by}``) and removed (outline 9.3.5.1.1, Q#96). Any other key that is not part of an
  outcome (step, source, at, date, amended, ...) is logged the same way, under field
  ``decision_keys``, so nothing is lost.
- **decisions become outcomes.** The i-th remaining decision in list order becomes outcome
  k+i ``{n, text, writes_to, reads, after: []}``, its leading ``D<n>:`` dropped and no claim.
  ``writes_to`` and ``reads`` are copied only when the line carried them: an absent list is
  not invented as ``[]``, and the report's ``shape_lacks`` names it.

``migrate(root)`` returns ``{ticket_id: report}`` for every open ticket under
``<root>/tickets``, where each report is ``{changed, awaiting, too_big, prose_falsifier,
trail_moved, by_moved, shape_lacks}``. A terminal ticket is never opened for write: its cursor
(its state's workflow_and_state, else its plan's) stands at one of its class's terminals, the
last state of each workflow version plus the class's dispositions, read from
``<root>/node_classes/<class>.json``, united with the grammar's TERMINAL_STATES (ticket
8c1329759813). A class with no definition there
refuses the run. A run over an already
migrated store writes nothing. Every plan write goes through the rehearsal's own door
(``rehearsal._write_ticket``) and every log line through ``ticket_log.append_log``, with the
log written before the plan so a crash never leaves a moved line nowhere.

    python3 -m cairn.machines.rehearsal.plan_migration <commons root> [--dry-run]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from cairn.tools.base import ticket_log
from cairn.tools.base import plan as plan_view

ACTOR = "plan_migration"
TOO_BIG = 7  # the outline's ~7 (9.3.5.1.2.1); the charter's max_items is the cast door's bound

_LABEL = re.compile(r"^\s*D\d+\s*:\s*")
_LOOSE_LABEL = re.compile(r"^\s*D\d+\s*[:.]?\s*")
_TRAIL = re.compile(r"^(fold|measured|settles|re-point|superseded)", re.IGNORECASE)
_OUTCOME_KEYS = ("n", "text", "writes_to", "reads")
_KEPT_BY_LOG = ("by",)


def is_trail(text: str) -> bool:
    """D2: the text, its ``D<n>`` label dropped and case-folded, opens with a trail marker."""
    return bool(_TRAIL.match(_LOOSE_LABEL.sub("", str(text or ""), count=1).casefold()))


def _workflow(plan: Path, doc: dict) -> str:
    st = plan.with_name(plan.name[:-5] + ".state.json")
    wf = None
    if st.is_file():
        try:
            wf = json.loads(st.read_text(encoding="utf-8")).get("workflow_and_state")
        except json.JSONDecodeError:
            wf = None
    if wf is None:
        wf = doc.get("workflow_and_state")
    return str(wf or "")


def _terminals(classes: Path, node_class: str, cache: dict) -> frozenset[str]:
    """The class's terminal set: the last state of each workflow version plus its declared
    dispositions, read from its definition under the commons, united with the grammar's own
    TERMINAL_STATES (KILLED and ABSORBED are terminal there and declared by no class, measured
    2026-11-16) (ticket 8c1329759813). A class with no definition refuses the run: an unknown
    class is never guessed open or closed."""
    if node_class not in cache:
        from cairn.tools.base.transitions import load_class_def
        from cairn.tools.base.workflow_grammar import TERMINAL_STATES
        cd = load_class_def(node_class, root=classes)
        ends = {v["path"][-1] for v in (cd.get("workflow_versions") or {}).values() if v.get("path")}
        cache[node_class] = frozenset(ends | set(cd.get("dispositions") or []) | TERMINAL_STATES)
    return cache[node_class]


def _terminal(plan: Path, doc: dict, classes: Path, cache: dict) -> bool:
    """The ticket's cursor stands at one of its class's terminals: its voyage is over, so its
    plan is a record, not work to migrate (PROVED, SUPERSEDED, RETIRED, DROPPED, ...)."""
    from cairn.tools.base.workflow_grammar import parse_workflow
    wf = parse_workflow(_workflow(plan, doc))
    return wf.here in _terminals(classes, wf.node_class, cache)


def _plans(root: Path) -> list[Path]:
    tickets = Path(root) / "tickets"
    return sorted(p for p in tickets.glob("*.json")
                  if not p.name.startswith("_") and not p.name.endswith(".state.json"))


def _numbered_clauses(doc: dict) -> list[dict] | None:
    f = doc.get("falsifier")
    if isinstance(f, dict) and isinstance(f.get("clauses"), list):
        return [c for c in f["clauses"] if isinstance(c, dict)]
    return None


def shaped(doc: dict) -> tuple[dict, list[tuple[str, dict]]]:
    """The migrated plan and the log lines it owes, ``[(kind, body)]``. Pure: writes nothing.
    A plan with no ``decisions`` key and no numbered clauses comes back unchanged with no lines."""
    clauses = _numbered_clauses(doc)
    if "decisions" not in doc and clauses is None:
        return doc, []
    out = dict(doc)
    lines: list[tuple[str, dict]] = []
    outcomes = [{"n": c.get("n"), "claim": c.get("claim"), "writes_to": [], "reads": [], "after": []}
                for c in (clauses or [])]
    k = len(outcomes)
    live = []
    for d in doc.get("decisions") or []:
        if not (isinstance(d, dict) and isinstance(d.get("n"), int)) or is_trail(
                d.get("text", "") if isinstance(d, dict) else ""):
            lines.append(("decision_retired", {"decision": d, "migrated_as_trail": True}))
            continue
        live.append(d)
    for i, d in enumerate(live, start=1):
        if "by" in d:
            lines.append(("field", {"field": "by", "value": {"n": d["n"], "by": d["by"]}}))
        rest = {key: v for key, v in d.items() if key not in _OUTCOME_KEYS + _KEPT_BY_LOG}
        if rest:
            lines.append(("field", {"field": "decision_keys", "value": {"n": d["n"], **rest}}))
        o = {"n": k + i, "text": _LABEL.sub("", str(d.get("text", "")), count=1)}
        for key in ("writes_to", "reads"):
            if key in d:
                o[key] = d[key]
        o["after"] = []
        outcomes.append(o)
    out.pop("decisions", None)
    if clauses is not None:
        out.pop("falsifier", None)
    out["outcomes"] = outcomes
    return out, lines


def report(doc: dict, charter: Path, *, changed: bool, trail: int = 0, by: int = 0) -> dict:
    """D5: what a judge at build-open needs; it judges nothing and moves nothing."""
    from cairn.tools.base import transitions
    outs = doc.get("outcomes") if isinstance(doc.get("outcomes"), list) else []
    f = doc.get("falsifier")
    return {"changed": changed,
            "awaiting": plan_view.awaiting(doc),
            "too_big": len(outs) > TOO_BIG,
            "prose_falsifier": f is not None and _numbered_clauses(doc) is None,
            "trail_moved": trail, "by_moved": by,
            "shape_lacks": transitions._shape_lacks(doc, charter) if charter.is_file() else
            [f"no store charter at {charter}"]}


def migrate(root: Path | str, *, dry_run: bool = False) -> dict:
    """D1: walk ``<root>/tickets``; migrate every open plan; return ``{ticket_id: report}``."""
    from cairn.machines.rehearsal import rehearsal as R
    root = Path(root)
    charter = root / "tickets" / "_charter+why.json"
    classes = root / "node_classes"
    cache: dict = {}
    out: dict = {}
    for plan in _plans(root):
        try:
            doc = json.loads(plan.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(doc, dict) or _terminal(plan, doc, classes, cache):
            continue
        tid = str(doc.get("id") or plan.name.split("-", 1)[0])
        new, lines = shaped(doc)
        changed = new is not doc
        trail = sum(1 for kind, _ in lines if kind == "decision_retired")
        by = sum(1 for kind, b in lines if kind == "field" and b["field"] == "by")
        if changed and not dry_run:
            why = (f"aa3e9a70db47: {tid}'s plan migrates to outcomes ({trail} trail line(s) and "
                   f"{by} by-line(s) to its log)")
            for kind, body in lines:
                ticket_log.append_log(plan, kind, body, actor=ACTOR, why=why)
            R._write_ticket(plan, new, why=why)
        out[tid] = report(new, charter, changed=changed, trail=trail, by=by)
    return out


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    dry = "--dry-run" in argv
    args = [a for a in argv if a != "--dry-run"]
    if len(args) != 1:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    got = migrate(args[0], dry_run=dry)
    print(json.dumps(got, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""AT BUILD-OPEN, A PLAN NOT YET IN OUTCOMES IS JUDGED INTO THEM — /sail step 0a.
Ticket 4d8a2c6e91f7 (parent 5c1e0a7d93b2, Q#100, outline 9.3.5.1.2.1).

A plan is constraints, then outcomes, then resources. A ticket opened for build may still carry
the older shape (``decisions`` beside ``falsifier.clauses``), or outcomes the migration moved
with no claim yet (``plan.awaiting``). Neither can be charted as outcomes until each line is
JUDGED: it is an outcome (it gets a claim), or a constraint (a how — Akien's own stays word for
word). That judgement is the builder's, made once, here; this module only applies it, checks
it, and writes it through the doors.

The judgement packet::

    {"<n>": {"claim": "<the outcome's claim>"} | {"constraint": true},
     ...,
     "conflicts": [{"n": <n>, "disposition": "log" | "named", "why": "<why>"}]}

- ``{"claim": ...}``: line n becomes (or stays) outcome n with that claim. Numbers are KEPT, never
  renumbered, so old clause n stays outcome n.
- ``{"constraint": true}``: line n leaves the outcomes, and its text joins ``constraints``
  VERBATIM (the step text as written; no paraphrase is accepted, so none can drift in).
- a conflict marked ``log`` moves line n whole to the ticket's log (kind ``decision_retired``,
  ``retired={by, at, because, into: "log"}``) and needs no judgement; one marked ``named``
  stays in the plan and is reported.

Every line to judge (every decision; every outcome awaiting its claim) must be judged or
logged. The result loses ``decisions`` and ``falsifier`` (an outcomes plan carries neither);
the falsifier moves whole to the log (kind ``field``), so no word of it is lost. The result is
written only when the cast door's own shape check (``transitions._shape_lacks``, read against
the store charter beside the plan) admits it; otherwise NOTHING is written and every lack is
named in one pass.

Reads go through the one plan view (``cairn.tools.base.plan``); this module keeps no second
reading of either shape.

    PYTHONPATH=$HOME/dev/src/cairn python3 -m skills.sail.judge_plan <ticket> <packet.json>
        [--tickets-dir D]

exit 0 written (or nothing to judge), 2 refused (lacks printed, nothing written).
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.tools.base import plan as _plan  # noqa: E402

DISPOSITIONS = ("log", "named")


def needs_judging(doc: dict) -> bool:
    """True when the plan still carries decisions, or an outcome awaiting its claim."""
    d = doc.get("decisions") if isinstance(doc, dict) else None
    return bool(_plan.awaiting(doc)) or (not _plan.has_outcomes(doc) and isinstance(d, list)
                                         and any(isinstance(x, dict) for x in d))


def judge(doc: dict, packet: dict, charter: Path) -> dict:
    """Apply ``packet`` to ``doc`` (a pure read). Returns {doc, constraints_added, logged,
    named, lacks}; ``doc`` is the converted plan, meaningful only when ``lacks`` is []."""
    lacks: list[str] = []
    if not isinstance(packet, dict):
        return {"doc": None, "constraints_added": [], "logged": [], "named": [],
                "lacks": [f"the packet is not an object: {repr(packet)[:80]}"]}
    outcomes_plan = _plan.has_outcomes(doc)
    field = "outcomes" if outcomes_plan else "decisions"
    raw = doc.get(field) if isinstance(doc.get(field), list) else []
    lines = [x for x in raw if isinstance(x, dict)]
    steps = _plan.steps(doc)  # one per dict line, in order
    ns = [st["n"] for st in steps]
    to_judge = list(_plan.awaiting(doc)) if outcomes_plan else list(ns)

    # conflicts
    logged, named = {}, []
    conflicts = packet.get("conflicts", [])
    if not isinstance(conflicts, list):
        lacks.append(f"conflicts is not a list: {repr(conflicts)[:80]}")
        conflicts = []
    for i, c in enumerate(conflicts):
        if not isinstance(c, dict):
            lacks.append(f"conflicts[{i}] is not an object: {repr(c)[:80]}")
            continue
        n, disp, why = c.get("n"), c.get("disposition"), c.get("why")
        if n not in ns:
            lacks.append(f"conflicts[{i}] names n={n!r}, no line of this plan")
        if disp not in DISPOSITIONS:
            lacks.append(f"conflicts[{i}].disposition is {disp!r}, not one of {list(DISPOSITIONS)}")
        if not (isinstance(why, str) and why.strip()):
            lacks.append(f"conflicts[{i}] carries no why")
        if n in ns and disp == "log":
            logged[n] = c
        elif n in ns and disp == "named":
            named.append(c)

    # judgements
    judged: dict = {}
    for k, v in packet.items():
        if k == "conflicts":
            continue
        n = int(k) if isinstance(k, str) and k.isdigit() else None
        if n not in ns:
            lacks.append(f"a judgement for {k!r}, no line of this plan")
            continue
        claim_ok = isinstance(v, dict) and set(v) == {"claim"} and isinstance(v["claim"], str) \
            and v["claim"].strip()
        constraint_ok = isinstance(v, dict) and set(v) == {"constraint"} and v["constraint"] is True
        if not (claim_ok or constraint_ok):
            lacks.append(f"the judgement for {n} is not {{claim: <text>}} or {{constraint: true}}: "
                         f"{repr(v)[:80]}")
            continue
        if n in logged:
            lacks.append(f"line {n} is both judged and logged as a conflict")
            continue
        judged[n] = v
    for n in to_judge:
        if n not in judged and n not in logged:
            lacks.append(f"line {n} is unjudged: give it a claim or mark it a constraint")

    # the converted plan
    outcomes, added = [], []
    for line, st in zip(lines, steps):
        n = st["n"]
        if n in logged:
            continue
        j = judged.get(n)
        if j and "constraint" in j:
            text = st["text"]
            if not (isinstance(text, str) and text.strip()):
                lacks.append(f"line {n} has no text to carry as a constraint")
            else:
                added.append(text)
            continue
        o = dict(line)
        if j:
            o["claim"] = j["claim"]
        o.setdefault("after", [])
        outcomes.append(o)
    new = {k: v for k, v in doc.items() if k not in ("decisions", "falsifier")}
    new["outcomes"] = outcomes
    standing = doc.get("constraints")
    if added or standing is not None:
        new["constraints"] = (list(standing) if isinstance(standing, list) else []) + added
    if not lacks:
        from cairn.tools.base.transitions import _shape_lacks
        lacks.extend(f"the cast door's shape check refuses the result: {lk}"
                     for lk in _shape_lacks(new, charter))
    return {"doc": new, "constraints_added": added,
            "logged": [dict(next(x for x, s in zip(lines, steps) if s["n"] == n)) for n in logged],
            "named": named, "lacks": lacks, "_logged_by": logged}


def apply(plan_path: str | Path, packet: dict, *, actor: str = "cc") -> dict:
    """Judge the plan at ``plan_path`` by ``packet`` and, only when nothing lacks, write it:
    each logged line and the dropped falsifier to the log, then the plan through
    ``rewrite_ticket``. Returns {written, lacks, named, logged, constraints_added}."""
    from cairn.tools.base.ticket_file import read_ticket, rewrite_ticket
    from cairn.tools.base.ticket_log import append_log
    p = Path(plan_path)
    doc = read_ticket(p)
    if not needs_judging(doc):
        return {"written": False, "lacks": [], "named": [], "logged": [], "constraints_added": [],
                "nothing_to_judge": True}
    r = judge(doc, packet, p.parent / "_charter+why.json")
    out = {k: r[k] for k in ("lacks", "named", "logged", "constraints_added")}
    if r["lacks"]:
        return {"written": False, **out}
    why = "the plan is judged into outcomes at build-open (ticket 4d8a2c6e91f7)"
    today = date.today().isoformat()
    for line in r["logged"]:
        c = r["_logged_by"][line.get("n")]
        append_log(p, "decision_retired",
                   {"decision": {**line, "retired": {"by": actor, "at": today,
                                                     "because": c["why"], "into": "log"}}},
                   actor=actor, why=why)
    if doc.get("falsifier") is not None:
        append_log(p, "field", {"field": "falsifier", "value": doc["falsifier"]},
                   actor=actor, why=why)
    rewrite_ticket(p, r["doc"], why=why, verb="cast")
    return {"written": True, **out}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2 or argv[0].startswith("-"):
        print(__doc__.split("\n\n")[-2], file=sys.stderr)
        return 2
    ticket, packet_path, tdir = argv[0], argv[1], None
    rest = argv[2:]
    if rest[:1] == ["--tickets-dir"] and len(rest) == 2:
        tdir = rest[1]
    elif rest:
        print(f"refused: unknown argument {rest[0]}", file=sys.stderr)
        return 2
    from cairn.tools.chain.grammar import ticket_path
    tp = ticket_path(ticket, tickets_dir=tdir)
    if tp is None:
        print(f"refused: no ticket {ticket} on file", file=sys.stderr)
        return 2
    try:
        packet = json.loads(Path(packet_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"refused: cannot read the packet {packet_path}: {exc}", file=sys.stderr)
        return 2
    r = apply(tp, packet)
    if r.get("nothing_to_judge"):
        print("nothing to judge: the plan is outcomes, every one claimed")
        return 0
    if not r["written"]:
        print("refused, nothing written:", file=sys.stderr)
        for lk in r["lacks"]:
            print(f"  - {lk}", file=sys.stderr)
        return 2
    print(json.dumps({k: r[k] for k in ("named", "logged", "constraints_added")},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Proof for ticket 5c1e0a7d93b2 — the cast door reads a plan of outcomes (Q#100, outline
9.3.5.1.2.1): constraints, then outcomes {n, claim, writes_to, reads, after, via?}, then resources.

1. an_outcomes_plan_casts: a doc carrying outcomes (claims, numbered 1..k), constraints and
   resources, with no falsifier and no decisions, casts; the plan file carries the outcomes as
   written, and no decisions line is seeded beside them from the berth's builder_check;
2. a_plan_the_door_cannot_read_is_refused: an outcome with no claim, a plan of 8 outcomes, and
   outcomes beside decisions (and beside a falsifier) are each refused naming the lack — the
   eight naming 'too big: split into children' — and nothing lands;
3. both_shapes_read_the_same: plan.clauses and plan.steps read an outcomes plan and the
   decisions+falsifier plan of the same content to the same {n, claim} and
   {n, text, writes_to, reads} lists, and the base charter's public_interface names the module;
4. the_lane_holds_a_claimless_outcome: the BUILDME entry lane every_outcome_has_its_claim
   refuses a ticket whose plan has an outcome with no claim, naming its n, and passes once the
   claim is given;
5. a_retired_outcome_rejoins_its_outcomes: split moves a retired outcome to the log, and the
   read (reconstruct over the log) puts it back into outcomes in n order, never into decisions.

Every tooth runs in a SCRATCH commons through ``artifact.set_diagnostic_roots``, restored in
``finally``; the store charter is copied from the commons beside this checkout (else the home
one). Tooth 4 stubs the inspector's four judges (``transitions._judge``) so only the lane under
proof speaks, and points ``ticket_file._TICKETS`` at the scratch store, both restored.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_the_cast_door_reads_a_plan_of_outcomes.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "5c1e0a7d93b2": {
        "1": "an_outcomes_plan_casts",
        "2": "a_plan_the_door_cannot_read_is_refused",
        "3": "both_shapes_read_the_same",
        "4": "the_lane_holds_a_claimless_outcome",
        "5": "a_retired_outcome_rejoins_its_outcomes",
    },
}

FAILURES: list[str] = []
WORKFLOW = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
READ = "cairn/tools/base/transitions.py"
OUTCOMES = [
    {"n": 1, "claim": "testing: the door reads outcomes", "writes_to": ["cairn/tools/base/plan.py"],
     "reads": [READ]},
    {"n": 2, "claim": "testing: the lane holds a claimless one", "writes_to": [READ],
     "reads": [], "after": [1], "via": "the BUILDME entry gate"},
]
CONSTRAINTS = ["testing: one plan view, every reader composes it"]
RESOURCES = ["testing: a scratch commons"]
BOUNDS = {"in": ["cairn/tools/base/plan.py", READ], "out": ["every other component"]}
MEASURED = [{"when": "2026-11-14", "saw": "testing: no reader reads outcomes", "how": "a grep"}]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:700]}")
    if not ok:
        FAILURES.append(name)


def _copy(x):
    return json.loads(json.dumps(x))


def _doc(tmp: Path, tid: str, **over) -> dict:
    """A complete OUTCOMES cast whose sorted berth agrees with it (and carries a builder_check,
    so a seeded decision would show). A key given as None is dropped."""
    sorted_berth = tmp / f"sorted-{tid}.json"
    sorted_berth.write_text(json.dumps({"skill": "sorted", "answers": {
        "workflow": WORKFLOW, "node_class": "code-seam",
        "builder_check": "testing: what does outcome 1 write?"}}), encoding="utf-8")
    intent_berth = tmp / "intent.json"
    intent_berth.write_text(json.dumps({"skill": "intent"}), encoding="utf-8")
    doc = {
        "id": tid, "title": f"testing outcomes plan fixture {tid}", "date": "2026-11-14",
        "owner": "codemother", "owning_intention": "cairn/tools/base/intention+why.json",
        "intention": "testing: a plan of outcomes casts", "why": "proof", "traces_to": "Law 4",
        "how": "cast_ticket", "constraints": list(CONSTRAINTS), "outcomes": _copy(OUTCOMES),
        "resources": list(RESOURCES), "bounds": _copy(BOUNDS), "measured": _copy(MEASURED),
        "node_class": "code-seam", "workflow_and_state": WORKFLOW,
        "watchme": "none, because cairn/tools/base/transitions.py",
        "sorted_berth": str(sorted_berth), "intent_berth": str(intent_berth),
    }
    doc.update(over)
    return {k: v for k, v in doc.items() if v is not None}


def _cast(tickets: Path, doc: dict):
    """(the path written or None, the lacks if refused else None, the files the id holds)."""
    from cairn.tools.base.transitions import CastRefused, cast_ticket
    try:
        p, lacks = cast_ticket(doc, actor="proof-actor", tickets_dir=tickets), None
    except CastRefused as exc:
        p, lacks = None, list(exc.lacks)
    return p, lacks, sorted(x.name for x in tickets.glob(f"{doc['id']}-*"))


def tooth_1(tmp: Path, tickets: Path) -> None:
    name = PROVES["5c1e0a7d93b2"]["1"]
    try:
        p, lacks, _ = _cast(tickets, _doc(tmp, "5c1e000a0001"))
        if p is None:
            check(name, False, f"refused: {lacks}")
            return
        got = json.loads(p.read_text(encoding="utf-8"))
        kept = (got.get("outcomes") == OUTCOMES and got.get("constraints") == CONSTRAINTS
                and got.get("resources") == RESOURCES)
        bare = "decisions" not in got and "falsifier" not in got
        check(name, kept and bare, f"outcomes kept={kept}; no decisions/falsifier={bare}; "
              f"keys={sorted(got)}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(tmp: Path, tickets: Path) -> None:
    name = PROVES["5c1e0a7d93b2"]["2"]
    claimless = _copy(OUTCOMES)
    del claimless[1]["claim"]
    eight = [{"n": i, "claim": f"testing: outcome {i}", "writes_to": [], "reads": []}
             for i in range(1, 9)]
    cases = [
        ("an outcome with no claim", {"outcomes": claimless}, "outcomes[1] has no claim"),
        ("eight outcomes", {"outcomes": eight}, "too big: split into children"),
        ("outcomes beside decisions",
         {"decisions": [{"n": 1, "text": "D1: x", "writes_to": [], "reads": []}]},
         "outcomes beside decisions"),
        ("outcomes beside a falsifier",
         {"falsifier": {"clauses": [{"n": 1, "claim": "a"}]}}, "outcomes beside falsifier"),
        ("a prose constraint", {"constraints": "testing: one view"}, "constraints is not a list"),
        ("a blank resource", {"resources": ["  "]}, "resources is not a list"),
    ]
    try:
        bad = []
        for i, (label, over, needle) in enumerate(cases):
            p, lacks, landed = _cast(tickets, _doc(tmp, f"5c1e000b{i:04x}", **over))
            if lacks is None or not any(needle in x for x in lacks) or landed:
                bad.append(f"{label}: lacks={lacks} landed={landed}")
        check(name, not bad, "; ".join(bad) or "four unreadable plans refused by name, none landed")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3() -> None:
    name = PROVES["5c1e0a7d93b2"]["3"]
    try:
        from cairn.tools.base import plan
        new = {"outcomes": _copy(OUTCOMES)}
        old = {"falsifier": {"clauses": [{"n": o["n"], "claim": o["claim"]} for o in OUTCOMES]},
               "decisions": [{"n": o["n"], "text": o["claim"], "writes_to": o["writes_to"],
                              "reads": o["reads"], "by": "cc"} for o in OUTCOMES]}
        want_c = [{"n": o["n"], "claim": o["claim"]} for o in OUTCOMES]
        want_s = [{"n": o["n"], "text": o["claim"], "writes_to": o["writes_to"],
                   "reads": o["reads"]} for o in OUTCOMES]
        same = (plan.clauses(new) == plan.clauses(old) == want_c
                and plan.steps(new) == plan.steps(old) == want_s)
        quiet = plan.awaiting(new) == [] and plan.awaiting(old) == []
        charter = json.loads((REPO / "cairn/tools/base/intention+why.json").read_text(encoding="utf-8"))
        named = "cairn.tools.base.plan" in (charter.get("public_interface") or [])
        check(name, same and quiet and named,
              f"same={same} (clauses new={plan.clauses(new)} old={plan.clauses(old)}; "
              f"steps new={plan.steps(new)} old={plan.steps(old)}); awaiting none={quiet}; "
              f"public_interface names it={named}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_4(tickets: Path) -> None:
    name = PROVES["5c1e0a7d93b2"]["4"]
    from cairn.tools.base import ticket_file, transitions
    tid = "5c1e000d0001"
    plan_file = tickets / f"{tid}-testing-a-migrated-plan.json"
    waiting = _copy(OUTCOMES)
    del waiting[1]["claim"]
    saved = ticket_file._TICKETS, transitions._judge
    ticket_file._TICKETS = tickets
    transitions._judge = lambda judge: (lambda *a, **k: [])
    try:
        def lane():
            rec = transitions.inspect_entry(tid)
            hit = [e for e in rec if e["identity"] == "every_outcome_has_its_claim"]
            return hit[0] if hit else None, [e["identity"] for e in rec]
        plan_file.write_text(json.dumps({"id": tid, "outcomes": waiting}), encoding="utf-8")
        held, names = lane()
        found = ((held or {}).get("values") or {}).get("findings") or [{}]
        refused = (held is not None and not transitions.gate.passed(held)
                   and found[0].get("actual") == [2])
        plan_file.write_text(json.dumps({"id": tid, "outcomes": _copy(OUTCOMES)}), encoding="utf-8")
        given, _ = lane()
        passes = given is not None and transitions.gate.passed(given)
        beside = (names.index("every_outcome_has_its_claim")
                  == names.index("the_ticket_has_every_answer_it_needs") + 1) if held else False
        check(name, refused and passes and beside,
              f"claimless refused={refused} ({held}); claim given passes={passes}; "
              f"beside the answers lane={beside}; lanes={names}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")
    finally:
        ticket_file._TICKETS, transitions._judge = saved


def tooth_5(tickets: Path) -> None:
    name = PROVES["5c1e0a7d93b2"]["5"]
    try:
        from cairn.tools.base import ticket_log
        retired = {"n": 2, "claim": "testing: retired", "writes_to": [], "reads": [],
                   "retired": "2026-11-14: testing"}
        live = [dict(OUTCOMES[0]), {"n": 3, "claim": "testing: three", "writes_to": [], "reads": []}]
        plan_file = tickets / "5c1e000e0001-testing-a-retired-outcome.json"
        plan_file.write_text(json.dumps({"id": "5c1e000e0001", "title": "testing",
                                         "outcomes": [live[0], retired, live[1]]}, indent=2) + "\n",
                             encoding="utf-8")
        ticket_log.split(plan_file, actor="proof-actor", why="testing: 5c1e tooth 5")
        on_plan = json.loads(plan_file.read_text(encoding="utf-8")).get("outcomes")
        moved = on_plan == live
        logged = [x.get("decision") for x in ticket_log.read_log(plan_file, "decision_retired")]
        back = ticket_log.reconstruct(json.loads(plan_file.read_text(encoding="utf-8")),
                                      ticket_log.read_log(plan_file))
        rejoined = ([o.get("n") for o in back.get("outcomes") or []] == [1, 2, 3]
                    and "decisions" not in back)
        # and a log line handed to the read directly, as any earlier split wrote it
        direct = ticket_log.reconstruct({"outcomes": _copy(live)},
                                        [{"kind": "decision_retired", "decision": retired}])
        direct_ok = ([o.get("n") for o in direct.get("outcomes") or []] == [1, 2, 3]
                     and "decisions" not in direct)
        old = ticket_log.reconstruct({"decisions": [{"n": 1, "text": "D1"}]},
                                     [{"kind": "decision_retired", "decision": {"n": 2, "text": "D2"}}])
        old_ok = [d.get("n") for d in old.get("decisions") or []] == [1, 2]
        check(name, moved and logged == [retired] and rejoined and direct_ok and old_ok,
              f"split left {on_plan}; logged={logged}; read back={back.get('outcomes')}; "
              f"direct={direct.get('outcomes')}; decisions plan still rejoins={old_ok}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-5c1e0a7d93b2-outcomes-")
    commons = tmp / "CairnCommons"
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    # the commons beside this checkout carries the charter this build's door reads; a checkout
    # with none beside it (a hollow's worktree) reads the home one
    beside = REPO.parent / "CairnCommons" / "tickets" / "_charter+why.json"
    charter = beside if beside.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    (tickets / "_charter+why.json").write_bytes(charter.read_bytes())
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
    try:
        tooth_1(tmp, tickets)
        tooth_2(tmp, tickets)
        tooth_3()
        tooth_4(tickets)
        tooth_5(tickets)
    finally:
        A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

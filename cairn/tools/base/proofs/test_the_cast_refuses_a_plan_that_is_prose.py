"""Proof for ticket e4f02a1ceef5 — the cast door refuses a ticket plan that is prose.

Measured 2026-11-05: falsifier is a dict on 248 tickets and a string on 384 (39 of the newest
40); writes_to is set on 17 of 635, bounds on 3, though both are declared in plan_fields. The
door checked only non-blank. Akien 2026-11-05: "should be json."

1. a_prose_falsifier_is_refused: a string falsifier, a dict with no clauses, an empty clauses,
   clauses numbered [1, 3], and a blank claim are each refused naming the falsifier, nothing lands;
2. a_pathless_decision_is_refused: a decision with no writes_to, with reads only, with a blank
   path, and with a reads path that resolves to no file are each refused by name;
3. a_shapeless_bounds_or_measured_is_refused: bounds as a string or without out, measured
   absent, empty, an entry without how, and a when that is no ISO date are each refused;
4. a_shaped_plan_casts: a doc carrying all four shapes lands with them byte-identical, and the
   builder_check seed line lands with writes_to [] and reads [];
5. the_shapes_are_read_from_the_charter: with the copied charter a doc without bounds is
   refused naming bounds; with a scratch charter whose plan_shapes and cast_requires_shaped
   drop 'bounds' the same doc casts.

Every tooth casts into a SCRATCH commons through ``artifact.set_diagnostic_roots``, restored in
``finally``; the store charter is COPIED from the live one (the home commons when the hollow's
worktree has none beside it); ``cast_ticket`` is resolved when a tooth asks, never at import.
Tooth 5 edits only the scratch charter.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_the_cast_refuses_a_plan_that_is_prose.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "e4f02a1ceef5": {
        "1": "a_prose_falsifier_is_refused",
        "2": "a_pathless_decision_is_refused",
        "3": "a_shapeless_bounds_or_measured_is_refused",
        "4": "a_shaped_plan_casts",
        "5": "the_shapes_are_read_from_the_charter",
    },
}

FAILURES: list[str] = []
WORKFLOW = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
FALSIFIER = {"clauses": [{"n": 1, "claim": "a"}, {"n": 2, "claim": "b"}],
             "wrong_intent": "testing: wrong if nothing reads it"}
DECISIONS = [{"n": 1, "text": "D1: build it", "by": "cc", "source": "cast",
              "writes_to": ["cairn/tools/base/transitions.py"],
              "reads": ["cairn/tools/base/transitions.py", "CairnCommons/tickets/_charter+why.json"]}]
BOUNDS = {"in": ["cairn/tools/base/transitions.py"], "out": ["every other component"]}
MEASURED = [{"when": "2026-11-05", "saw": "testing: 39 of 40 prose", "how": "a grep"}]


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:600]}")
    if not ok:
        FAILURES.append(name)


def _doc(tmp: Path, tid: str, builder_check: str = "", **over) -> dict:
    """A complete, SHAPED cast whose sorted berth agrees with it. A key given as None is dropped."""
    sorted_berth = tmp / f"sorted-{tid}.json"
    answers = {"workflow": WORKFLOW, "node_class": "code-seam"}
    if builder_check:
        answers["builder_check"] = builder_check
    sorted_berth.write_text(json.dumps({"skill": "sorted", "answers": answers}), encoding="utf-8")
    intent_berth = tmp / "intent.json"
    intent_berth.write_text(json.dumps({"skill": "intent"}), encoding="utf-8")
    doc = {
        "id": tid, "title": f"testing shaped plan fixture {tid}", "date": "2026-11-05",
        "owner": "codemother", "owning_intention": "cairn/tools/base/intention+why.json",
        "intention": "testing: a cast's plan is JSON", "why": "proof", "traces_to": "Law 4",
        "how": "cast_ticket", "falsifier": json.loads(json.dumps(FALSIFIER)),
        "decisions": json.loads(json.dumps(DECISIONS)), "bounds": dict(BOUNDS),
        "measured": json.loads(json.dumps(MEASURED)),
        "node_class": "code-seam", "workflow_and_state": WORKFLOW,
        "watchme": "none, because cairn/tools/base/transitions.py",
        "sorted_berth": str(sorted_berth), "intent_berth": str(intent_berth),
    }
    doc.update(over)
    return {k: v for k, v in doc.items() if v is not None}


def _refusal(tickets: Path, doc: dict) -> tuple[list[str] | None, list[str]]:
    """(the lacks if refused else None, the files the id holds afterwards)."""
    from cairn.tools.base.transitions import CastRefused, cast_ticket
    try:
        cast_ticket(doc, actor="proof-actor", tickets_dir=tickets)
        lacks = None
    except CastRefused as exc:
        lacks = list(exc.lacks)
    return lacks, sorted(p.name for p in tickets.glob(f"{doc['id']}-*"))


def _cases(tmp: Path, tickets: Path, prefix: str, cases: list[tuple[str, dict, str]]) -> list[str]:
    """Each (label, overrides, needle) must be refused with a lack carrying needle, nothing landed."""
    bad = []
    for i, (label, over, needle) in enumerate(cases):
        tid = f"{prefix}{i:04x}"
        lacks, landed = _refusal(tickets, _doc(tmp, tid, **over))
        if lacks is None or not any(needle in x for x in lacks) or landed:
            bad.append(f"{label}: lacks={lacks} landed={landed}")
    return bad


def tooth_1(tmp: Path, tickets: Path) -> None:
    name = PROVES["e4f02a1ceef5"]["1"]
    try:
        bad = _cases(tmp, tickets, "e4f0000a", [
            ("a string", {"falsifier": "(1) a (2) b"}, "falsifier"),
            ("no clauses", {"falsifier": {"wrong_intent": "x"}}, "falsifier"),
            ("empty clauses", {"falsifier": {"clauses": []}}, "falsifier"),
            ("numbered 1, 3", {"falsifier": {"clauses": [{"n": 1, "claim": "a"}, {"n": 3, "claim": "b"}]}},
             "falsifier.clauses"),
            ("a blank claim", {"falsifier": {"clauses": [{"n": 1, "claim": "  "}]}}, "falsifier.clauses[0]"),
        ])
        check(name, not bad, "; ".join(bad) or "five prose shapes refused by name, none landed")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(tmp: Path, tickets: Path) -> None:
    name = PROVES["e4f02a1ceef5"]["2"]
    line = {"n": 1, "text": "D1: x"}
    try:
        bad = _cases(tmp, tickets, "e4f0000b", [
            ("no paths", {"decisions": [dict(line)]}, "decisions[0] lacks writes_to"),
            ("reads only", {"decisions": [dict(line, reads=["cairn/tools/base/transitions.py"])]},
             "decisions[0] lacks writes_to"),
            ("writes_to only", {"decisions": [dict(line, writes_to=["a.py"])]}, "decisions[0] lacks reads"),
            ("a blank path", {"decisions": [dict(line, writes_to=[" "], reads=[])]}, "decisions[0]"),
            ("a reads to no file", {"decisions": [dict(line, writes_to=[], reads=["no/such/file.py"])]},
             "resolves to no file"),
        ])
        check(name, not bad, "; ".join(bad) or "four pathless lines and a dead reads refused by name")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(tmp: Path, tickets: Path) -> None:
    name = PROVES["e4f02a1ceef5"]["3"]
    m = dict(MEASURED[0])
    try:
        bad = _cases(tmp, tickets, "e4f0000c", [
            ("bounds a string", {"bounds": "in: transitions.py"}, "bounds"),
            ("bounds without out", {"bounds": {"in": ["a.py"]}}, "bounds"),
            ("measured absent", {"measured": None}, "measured"),
            ("measured empty", {"measured": []}, "measured"),
            ("an entry without how", {"measured": [{k: v for k, v in m.items() if k != "how"}]},
             "measured[0] lacks how"),
            ("a when that is no date", {"measured": [dict(m, when="yesterday")]}, "measured[0].when"),
        ])
        check(name, not bad, "; ".join(bad) or "six shapeless bounds/measured refused by name")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_4(tmp: Path, tickets: Path) -> None:
    name = PROVES["e4f02a1ceef5"]["4"]
    try:
        from cairn.tools.base.transitions import cast_ticket
        p = cast_ticket(_doc(tmp, "e4f0000d0001"), actor="proof-actor", tickets_dir=tickets)
        got = json.loads(p.read_text(encoding="utf-8"))
        same = all(json.dumps(got.get(k)) == json.dumps(v) for k, v in
                   (("falsifier", FALSIFIER), ("decisions", DECISIONS), ("bounds", BOUNDS),
                    ("measured", MEASURED)))
        q = cast_ticket(_doc(tmp, "e4f0000d0002", builder_check="testing: what does D1 write?",
                             decisions=None), actor="proof-actor", tickets_dir=tickets)
        seed = json.loads(q.read_text(encoding="utf-8")).get("decisions") or [{}]
        seeded = len(seed) == 1 and seed[0].get("writes_to") == [] and seed[0].get("reads") == []
        check(name, same and seeded, f"shapes kept={same} seed={seed}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_5(tmp: Path, tickets: Path) -> None:
    name = PROVES["e4f02a1ceef5"]["5"]
    charter = tickets / "_charter+why.json"
    before = charter.read_bytes()
    try:
        lacks, landed = _refusal(tickets, _doc(tmp, "e4f0000e0001", bounds=None))
        refused = lacks is not None and any("bounds" in x for x in lacks) and not landed
        c = json.loads(before)
        shapes = c.get("plan_shapes")
        if isinstance(shapes, dict):
            shapes.pop("bounds", None)
        if isinstance(c.get("cast_requires_shaped"), list):
            c["cast_requires_shaped"] = [k for k in c["cast_requires_shaped"] if k != "bounds"]
        charter.write_text(json.dumps(c, indent=2) + "\n", encoding="utf-8")
        lacks2, landed2 = _refusal(tickets, _doc(tmp, "e4f0000e0002", bounds=None))
        check(name, refused and lacks2 is None and bool(landed2),
              f"with bounds shaped: lacks={lacks}; dropped from the charter: lacks={lacks2} landed={landed2}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")
    finally:
        charter.write_bytes(before)


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-e4f02a1ceef5-cast-shapes-")
    commons = tmp / "CairnCommons"
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    # The hollow's worktree has no CairnCommons beside it, so _LIVE_CHARTER (REPO.parent) is absent
    # there; the charter is then read from the home checkout, as hollow.py resolves the commons.
    charter = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    (tickets / "_charter+why.json").write_bytes(charter.read_bytes())
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
    try:
        tooth_1(tmp, tickets)
        tooth_2(tmp, tickets)
        tooth_3(tmp, tickets)
        tooth_4(tmp, tickets)
        tooth_5(tmp, tickets)
    finally:
        A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

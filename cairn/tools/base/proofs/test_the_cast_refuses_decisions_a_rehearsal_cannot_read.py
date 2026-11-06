"""Proof for ticket 6d81b55be139 — the casting door refuses decisions a rehearsal cannot read.

Measured 2026-11-04 on 3dc005de27cf pass 1 (idea ff77d32f9848): cast_ticket accepted plain-string
decisions; the rehearsal's labeled() (cairn/machines/rehearsal/rehearsal.py) reads only dicts
with an int n, so every decision was dropped and the reader said 'the plan has no steps'.

1. a_string_decision_is_refused: decisions ['D1: a string'] raises CastRefused naming
   decisions[0], and no file for the id lands;
2. an_n_less_or_blank_decision_is_refused: [{'text': 'no n'}] and [{'n': 1, 'text': '  '}]
   each raise CastRefused naming decisions[0];
3. a_repeated_n_is_refused: two entries with n 1 raise CastRefused naming D1;
4. well_formed_decisions_still_cast: a {n, text, by, source} line lands byte-identical, and a
   doc with no decisions casts.

Every tooth casts into a SCRATCH commons through ``artifact.set_diagnostic_roots``, restored in
``finally``; ``cast_ticket`` is resolved when a tooth asks, never at import.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_the_cast_refuses_decisions_a_rehearsal_cannot_read.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "6d81b55be139": {
        "1": "a_string_decision_is_refused",
        "2": "an_n_less_or_blank_decision_is_refused",
        "3": "a_repeated_n_is_refused",
        "4": "well_formed_decisions_still_cast",
    },
}

FAILURES: list[str] = []
WORKFLOW = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:400]}")
    if not ok:
        FAILURES.append(name)


def _doc(tmp: Path, tid: str, **over) -> dict:
    """A complete cast whose sorted berth agrees with it (no builder_check, so nothing is seeded)."""
    sorted_berth = tmp / f"sorted-{tid}.json"
    sorted_berth.write_text(json.dumps({"skill": "sorted", "answers": {
        "workflow": WORKFLOW, "node_class": "code-seam"}}), encoding="utf-8")
    intent_berth = tmp / "intent.json"
    intent_berth.write_text(json.dumps({"skill": "intent"}), encoding="utf-8")
    doc = {
        "id": tid, "title": f"testing decisions fixture {tid}", "date": "2026-11-05",
        "owner": "codemother", "owning_intention": "cairn/tools/base/intention+why.json",
        "intention": "testing: a cast's decisions are readable", "why": "proof", "traces_to": "Law 7",
        "how": "cast_ticket", "falsifier": {"clauses": [{"n": 1, "claim": "DONE when the shape is judged"}]},
        "bounds": {"in": ["cairn/tools/base/transitions.py"], "out": []},
        "measured": [{"when": "2026-11-05", "saw": "a fixture", "how": "the e4f02a1ceef5 shapes"}],
        "node_class": "code-seam", "workflow_and_state": WORKFLOW,
        "watchme": "none, because cairn/tools/base/transitions.py",
        "sorted_berth": str(sorted_berth), "intent_berth": str(intent_berth),
    }
    doc.update(over)
    return doc


def _refusal(tickets: Path, doc: dict) -> tuple[list[str] | None, list[str]]:
    """(the lacks if refused else None, the files the id holds afterwards)."""
    from cairn.tools.base.transitions import CastRefused, cast_ticket
    try:
        cast_ticket(doc, actor="proof-actor", tickets_dir=tickets)
        lacks = None
    except CastRefused as exc:
        lacks = list(exc.lacks)
    return lacks, sorted(p.name for p in tickets.glob(f"{doc['id']}-*"))


def _names(lacks: list[str] | None, needle: str) -> bool:
    return lacks is not None and any(needle in x for x in lacks)


def tooth_1(tmp: Path, tickets: Path) -> None:
    name = PROVES["6d81b55be139"]["1"]
    try:
        lacks, landed = _refusal(tickets, _doc(tmp, "6d810000a001", decisions=["D1: a string"]))
        check(name, _names(lacks, "decisions[0]") and not landed, f"lacks={lacks} landed={landed}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(tmp: Path, tickets: Path) -> None:
    name = PROVES["6d81b55be139"]["2"]
    try:
        a, la = _refusal(tickets, _doc(tmp, "6d810000a002", decisions=[{"text": "no n"}]))
        b, lb = _refusal(tickets, _doc(tmp, "6d810000a003", decisions=[{"n": 1, "text": "  "}]))
        check(name, _names(a, "decisions[0]") and _names(b, "decisions[0]") and not la and not lb,
              f"n-less={a} {la} blank={b} {lb}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(tmp: Path, tickets: Path) -> None:
    name = PROVES["6d81b55be139"]["3"]
    try:
        lacks, landed = _refusal(tickets, _doc(tmp, "6d810000a004", decisions=[
            {"n": 1, "text": "D1: a"}, {"n": 1, "text": "D1: b"}]))
        check(name, _names(lacks, "D1") and not landed, f"lacks={lacks} landed={landed}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_4(tmp: Path, tickets: Path) -> None:
    name = PROVES["6d81b55be139"]["4"]
    try:
        from cairn.tools.base.transitions import cast_ticket
        kept = [{"n": 1, "text": "D1: a", "by": "cc", "source": "cast", "writes_to": [], "reads": []}]
        p = cast_ticket(_doc(tmp, "6d810000a005", decisions=[dict(x) for x in kept]),
                        actor="proof-actor", tickets_dir=tickets)
        got = json.loads(p.read_text(encoding="utf-8")).get("decisions")
        q = cast_ticket(_doc(tmp, "6d810000a006"), actor="proof-actor", tickets_dir=tickets)
        check(name, json.dumps(got) == json.dumps(kept) and q.is_file(), json.dumps(got))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-6d81b55be139-cast-decisions-")
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
    finally:
        A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

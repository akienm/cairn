"""Proof for ticket 5defc13bfebe — a bug ticket casts carrying fixes, the proofs whose red it fixes.

Measured 2026-11-12: cast_ticket refused a bug doc with "fixes is not a plan, state or log
field" and cast the same doc without it. The fixit rule reads ``fixes`` at
cairn/devices/tester/reseal.py (rung 4, path y) and at codemother's clearance (the BUILDME
fixit rule), as outline 17.11.7.2 asks ("at BUILDME the ticket names the red it fixes"), but
the store charter never declared it, so only fixtures written straight to disk ever carried it.

1. clause_1_a_well_shaped_fixes_casts_and_reads_back: a bug doc whose fixes is a non-empty list
   of repo-relative paths to existing files casts into a scratch commons (the live charter
   copied in), and read_ticket over the cast plan returns that list unchanged;
2. clause_2_a_malformed_fixes_is_refused_by_name: fixes that is not a list, an empty list, a
   list with a blank entry, or a list naming a path that resolves to no file is refused with a
   lack naming fixes, and nothing lands;
3. clause_3_the_live_charter_declares_and_shapes_fixes: the live store charter lists fixes in
   plan_fields and shapes it in plan_shapes;
4. clause_4_a_doc_without_fixes_still_casts: the same doc with no fixes casts.

``cast_ticket`` and ``read_ticket`` are resolved at tooth time; the scratch commons is reached
through ``artifact.set_diagnostic_roots``, restored in ``finally``.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_bug_ticket_casts_with_the_red_it_fixes.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "5defc13bfebe": {
        "1": "clause_1_a_well_shaped_fixes_casts_and_reads_back",
        "2": "clause_2_a_malformed_fixes_is_refused_by_name",
        "3": "clause_3_the_live_charter_declares_and_shapes_fixes",
        "4": "clause_4_a_doc_without_fixes_still_casts",
    },
}

FAILURES: list[str] = []
# A proof that exists in every checkout: this file itself, repo-relative.
RED = "cairn/tools/base/proofs/test_a_bug_ticket_casts_with_the_red_it_fixes.py"
BUG_WORKFLOW = "bug@v1: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:600]}")
    if not ok:
        FAILURES.append(name)


def _doc(tmp: Path, tid: str, **extra) -> dict:
    sorted_berth = tmp / f"sorted-{tid}.json"
    sorted_berth.write_text(json.dumps({"skill": "sorted", "answers": {
        "workflow": BUG_WORKFLOW, "node_class": "bug"}}), encoding="utf-8")
    intent_berth = tmp / "intent.json"
    intent_berth.write_text(json.dumps({"skill": "intent"}), encoding="utf-8")
    doc = {
        "id": tid, "title": f"testing a bug that names its red {tid}", "date": "2026-11-12",
        "owner": "CC", "owning_intention": "cairn/tools/base/intention+why.json",
        "intention": "a fixture bug", "why": "a fixture why", "traces_to": "Law 8",
        "how": "a fixture how", "falsifier": {"clauses": [{"n": 1, "claim": "the fixture red goes green"}]},
        "bounds": {"in": [RED], "out": ["every other component"]},
        "measured": [{"when": "2026-11-12", "saw": "a fixture red", "how": "a fixture run"}],
        "node_class": "bug", "workflow_and_state": BUG_WORKFLOW,
        "watchme": "none, because its proof " + RED + " is the whole of its correctness",
        "sorted_berth": str(sorted_berth), "intent_berth": str(intent_berth),
    }
    doc.update(extra)
    return doc


def _cast(doc: dict, tickets: Path):
    """(path, None) on a cast, (None, lacks) on a refusal."""
    from cairn.tools.base.transitions import CastRefused, cast_ticket
    try:
        return cast_ticket(doc, actor="proof-actor", tickets_dir=tickets), None
    except CastRefused as exc:
        return None, list(exc.lacks)


def tooth_1(tmp: Path, tickets: Path) -> None:
    name = PROVES["5defc13bfebe"]["1"]
    try:
        from cairn.tools.base.ticket_file import read_ticket
        p, lacks = _cast(_doc(tmp, "5def0000a001", fixes=[RED]), tickets)
        got = read_ticket(p).get("fixes") if p else None
        check(name, p is not None and got == [RED], f"path={p} lacks={lacks} fixes read back={got!r}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(tmp: Path, tickets: Path) -> None:
    name = PROVES["5defc13bfebe"]["2"]
    try:
        bad = {"not a list": RED, "empty": [], "blank entry": [RED, "  "],
               "unresolvable": ["cairn/tools/base/proofs/test_no_such_proof_anywhere.py"]}
        wrong = []
        for i, (label, value) in enumerate(bad.items()):
            tid = f"5def0000b00{i}"
            p, lacks = _cast(_doc(tmp, tid, fixes=value), tickets)
            landed = list(tickets.glob(f"{tid}-*"))
            # The lack must be the SHAPE's, not the today's "not a plan, state or log field".
            named = lacks is not None and any(
                "fixes" in x and "not a plan, state or log field" not in x for x in lacks)
            if p is not None or landed or not named:
                wrong.append(f"{label}: path={p} lacks={lacks} landed={[x.name for x in landed]}")
        check(name, not wrong, "; ".join(wrong) or "all four malformed fixes refused by name")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(live: Path) -> None:
    name = PROVES["5defc13bfebe"]["3"]
    try:
        c = json.loads(live.read_text(encoding="utf-8"))
        in_plan = "fixes" in (c.get("plan_fields") or [])
        shaped = "fixes" in (c.get("plan_shapes") or {})
        check(name, in_plan and shaped, f"{live}: in plan_fields={in_plan} in plan_shapes={shaped}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_4(tmp: Path, tickets: Path) -> None:
    name = PROVES["5defc13bfebe"]["4"]
    try:
        p, lacks = _cast(_doc(tmp, "5def0000c001"), tickets)
        check(name, p is not None, f"path={p} lacks={lacks}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-5defc13bfebe-fixes-")
    commons = tmp / "CairnCommons"
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    # The hollow's worktree has no CairnCommons beside it; the charter is then the home checkout's.
    live = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    (tickets / "_charter+why.json").write_bytes(live.read_bytes())
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
    try:
        tooth_1(tmp, tickets)
        tooth_2(tmp, tickets)
        tooth_3(live)
        tooth_4(tmp, tickets)
    finally:
        A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

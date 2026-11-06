"""Proof for ticket 02a4ddc2d12a — /sorted instructs the shaped ticket plan.

Measured 2026-11-05: skills/sorted/SKILL.md's cast step listed the 15 required fields and let
'the decision lines … ride along as extras'; it named none of the four shapes the cast door
(parent e4f02a1ceef5) now refuses without. This proof keeps the instruction tracking the door:

1. clause_1_skill_md_carries_one_shaped_example: SKILL.md carries exactly one fenced json block
   directly under the marker line ``<!-- the shaped example (ticket 02a4ddc2d12a) -->``;
2. clause_2_the_example_is_admitted_by_the_cast_door: that block, cast into a SCRATCH commons
   holding a copy of the live store charter (only id, title and the two berths swapped for
   fixture ones), is admitted by cast_ticket and lands its four shapes unchanged;
3. clause_3_a_prose_falsifier_in_the_example_is_refused: the same block with its falsifier
   replaced by a string is refused, naming the falsifier.

``cast_ticket`` is resolved at tooth time; the scratch commons is reached through
``artifact.set_diagnostic_roots``, restored in ``finally``.

Run bare:  PYTHONPATH=. python3 skills/sorted/proofs/test_sorted_instructs_the_shaped_plan.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "02a4ddc2d12a": {
        "1": "clause_1_skill_md_carries_one_shaped_example",
        "2": "clause_2_the_example_is_admitted_by_the_cast_door",
        "3": "clause_3_a_prose_falsifier_in_the_example_is_refused",
    },
}

FAILURES: list[str] = []
SKILL = REPO / "skills" / "sorted" / "SKILL.md"
MARKER = "<!-- the shaped example (ticket 02a4ddc2d12a) -->"
_BLOCK = re.compile(re.escape(MARKER) + r"\s*\n```json\n(.*?)\n```", re.S)


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:600]}")
    if not ok:
        FAILURES.append(name)


def _examples() -> list[str]:
    return _BLOCK.findall(SKILL.read_text(encoding="utf-8"))


def _fixture(tmp: Path, tid: str, example: dict) -> dict:
    """The example with only its id, title and berths swapped for fixture ones."""
    doc = json.loads(json.dumps(example))
    sorted_berth = tmp / f"sorted-{tid}.json"
    sorted_berth.write_text(json.dumps({"skill": "sorted", "answers": {
        "workflow": doc.get("workflow_and_state"), "node_class": doc.get("node_class")}}), encoding="utf-8")
    intent_berth = tmp / "intent.json"
    intent_berth.write_text(json.dumps({"skill": "intent"}), encoding="utf-8")
    doc.update(id=tid, title=f"testing shaped example {tid}", sorted_berth=str(sorted_berth),
               intent_berth=str(intent_berth))
    return doc


def tooth_1() -> None:
    name = PROVES["02a4ddc2d12a"]["1"]
    try:
        found = _examples()
        parsed = [json.loads(b) for b in found]
        check(name, len(parsed) == 1 and isinstance(parsed[0], dict), f"{len(found)} marked json block(s)")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(tmp: Path, tickets: Path) -> None:
    name = PROVES["02a4ddc2d12a"]["2"]
    try:
        from cairn.tools.base.transitions import cast_ticket
        example = json.loads(_examples()[0])
        p = cast_ticket(_fixture(tmp, "02a40000b001", example), actor="proof-actor", tickets_dir=tickets)
        got = json.loads(p.read_text(encoding="utf-8"))
        kept = all(json.dumps(got.get(k)) == json.dumps(example.get(k))
                   for k in ("falsifier", "decisions", "bounds", "measured"))
        check(name, kept and all(k in example for k in ("falsifier", "decisions", "bounds", "measured")),
              f"landed {p.name}; shapes kept {kept}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(tmp: Path, tickets: Path) -> None:
    name = PROVES["02a4ddc2d12a"]["3"]
    try:
        from cairn.tools.base.transitions import CastRefused, cast_ticket
        example = json.loads(_examples()[0])
        doc = _fixture(tmp, "02a40000b002", example)
        doc["falsifier"] = "(1) it works (2) it keeps working"
        try:
            cast_ticket(doc, actor="proof-actor", tickets_dir=tickets)
            lacks = None
        except CastRefused as exc:
            lacks = list(exc.lacks)
        landed = list(tickets.glob("02a40000b002-*"))
        check(name, lacks is not None and any("falsifier" in x for x in lacks) and not landed,
              f"lacks={lacks} landed={landed}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-02a4ddc2d12a-shaped-example-")
    commons = tmp / "CairnCommons"
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    # The hollow's worktree has no CairnCommons beside it; the charter is then the home checkout's.
    charter = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    (tickets / "_charter+why.json").write_bytes(charter.read_bytes())
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
    try:
        tooth_1()
        tooth_2(tmp, tickets)
        tooth_3(tmp, tickets)
    finally:
        A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Proof for ticket 0dbc830e58d2 — a cast seeds decisions from builder_check.

Peer F35 (2026-10-08): a cast already answers the builder's questions at /sorted
(builder_check), but the answers rode the ticket only as builder_notes, which the rehearsal
reader ties to no step, so the first pass rediscovered them as gaps (80518446bfc8 pass 1: 40
gaps of one cause). So cast_ticket seeds ONE decision carrying builder_check verbatim when the
doc has none (open-c3c6a660608e, answered: "the build as written: one D1 carrying
builder_check verbatim").

1. a decision-less cast over a sorted berth whose answers.builder_check is 'WHERE? x.py'
   lands with decisions == [one entry: n 1, source 'sorted', step 'cast', by the actor,
   'WHERE? x.py' in its text];
2. a cast already carrying decisions [{n:1, text:'D1: keep'}] lands with them
   byte-identical and no seed;
3. a berth whose builder_check is '' (and one with none) lands with no 'decisions' key.

Every tooth casts into a SCRATCH commons through ``artifact.set_diagnostic_roots``, restored
in ``finally``; ``cast_ticket`` is resolved when a tooth asks, never at import.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_cast_seeds_decisions_from_builder_check.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "0dbc830e58d2": {
        "1": "a_decision_less_cast_gains_the_builder_check_as_d1",
        "2": "a_cast_carrying_decisions_keeps_them_byte_identical",
        "3": "a_blank_or_absent_builder_check_adds_no_decisions_key",
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


def _doc(tmp: Path, tid: str, answers_extra: dict, **over) -> dict:
    """A complete cast whose sorted berth agrees with it, plus whatever builder_check is given."""
    sorted_berth = tmp / f"sorted-{tid}.json"
    sorted_berth.write_text(json.dumps({"skill": "sorted", "answers": {
        "workflow": WORKFLOW, "node_class": "code-seam", **answers_extra}}), encoding="utf-8")
    intent_berth = tmp / "intent.json"
    intent_berth.write_text(json.dumps({"skill": "intent"}), encoding="utf-8")
    doc = {
        "id": tid, "title": f"seed fixture {tid}", "date": "2026-10-12",
        "owner": "codemother", "owning_intention": "skills/sorted/intention+why.json",
        "intention": "a cast seeds its decisions", "why": "proof", "traces_to": "Law 1",
        "how": "cast_ticket", "falsifier": "DONE when the seed lands",
        "node_class": "code-seam", "workflow_and_state": WORKFLOW,
        "watchme": "none, because cairn/tools/base/transitions.py",
        "sorted_berth": str(sorted_berth), "intent_berth": str(intent_berth),
    }
    doc.update(over)
    return doc


def _cast(tickets: Path, doc: dict) -> dict:
    from cairn.tools.base.transitions import cast_ticket
    path = cast_ticket(doc, actor="proof-actor", tickets_dir=tickets)
    return json.loads(path.read_text(encoding="utf-8"))


def tooth_1(tmp: Path, tickets: Path) -> None:
    name = PROVES["0dbc830e58d2"]["1"]
    try:
        got = _cast(tickets, _doc(tmp, "0dbc0000a001", {"builder_check": "WHERE? x.py"}))
        ds = got.get("decisions")
        d = ds[0] if isinstance(ds, list) and len(ds) == 1 and isinstance(ds[0], dict) else {}
        check(name, bool(d) and d.get("n") == 1 and d.get("source") == "sorted"
              and d.get("step") == "cast" and d.get("by") == "proof-actor"
              and "WHERE? x.py" in str(d.get("text")) and bool(d.get("at")),
              json.dumps(ds))
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(tmp: Path, tickets: Path) -> None:
    name = PROVES["0dbc830e58d2"]["2"]
    try:
        kept = [{"n": 1, "text": "D1: keep"}]
        got = _cast(tickets, _doc(tmp, "0dbc0000a002", {"builder_check": "WHERE? x.py"},
                                  decisions=[dict(x) for x in kept]))
        check(name, json.dumps(got.get("decisions")) == json.dumps(kept), json.dumps(got.get("decisions")))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(tmp: Path, tickets: Path) -> None:
    name = PROVES["0dbc830e58d2"]["3"]
    try:
        blank = _cast(tickets, _doc(tmp, "0dbc0000a003", {"builder_check": "  "}))
        empty = _cast(tickets, _doc(tmp, "0dbc0000a004", {"builder_check": ""}))
        absent = _cast(tickets, _doc(tmp, "0dbc0000a005", {}))
        check(name, all("decisions" not in t for t in (blank, empty, absent)),
              json.dumps([t.get("decisions") for t in (blank, empty, absent)]))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("cairn-cast-seed-proof-")
    commons = tmp / "CairnCommons"
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    (tickets / "_charter+why.json").write_bytes(_LIVE_CHARTER.read_bytes())
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
    try:
        tooth_1(tmp, tickets)
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

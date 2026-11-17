"""Proof for ticket cf4482b200a1: the cast door refuses a bug that brings a new proof.

Measured 2026-11-16: 38dc3a0f93b1 was cast as a bug whose bounds.in named a new proof. Its
BUILDME was refused twice (q165, q166) with "no VALIDATION has ever sealed" it. Clearance rule
2 admits a bug only onto a proof whose seal is a measured red (outline 19.14.8 y), and a new
proof's seal reaches main only at the land, after BUILDME. So the ticket could never cross, and
it had to be re-cast as a code-seam. 2dda7060d84e was cast the same way.

1. clause_1_a_bug_bringing_an_unsealed_proof_is_refused: a bug doc whose bounds.in names a
   proof path with no seal is refused, one lack naming that path and code-seam@v2, and nothing
   lands;
2. clause_2_the_same_doc_as_a_code_seam_casts: the same doc, cast as code-seam@v2 with its own
   sorted berth, casts;
3. clause_3_a_bug_whose_proofs_are_sealed_casts: a bug doc whose bounds.in names only a proof
   that has a seal (the sibling proof, sealed in cairn/tools/base/validations) casts.

The scratch commons is reached through ``artifact.set_diagnostic_roots``, restored in ``finally``.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_bug_that_brings_a_new_proof_is_refused_at_cast.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "cf4482b200a1": {
        "1": "clause_1_a_bug_bringing_an_unsealed_proof_is_refused",
        "2": "clause_2_the_same_doc_as_a_code_seam_casts",
        "3": "clause_3_a_bug_whose_proofs_are_sealed_casts",
    },
}

FAILURES: list[str] = []
NEW = "cairn/tools/base/proofs/test_cf44_never_sealed_fixture.py"        # no seal anywhere
SEALED = "cairn/tools/base/proofs/test_a_bug_ticket_casts_with_the_red_it_fixes.py"
CODE = "cairn/tools/base/transitions.py"
WORKFLOWS = {
    "bug": "bug@v1: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED",
    "code-seam": "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED",
}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:600]}")
    if not ok:
        FAILURES.append(name)


def _doc(tmp: Path, tid: str, kind: str, proof: str) -> dict:
    sorted_berth = tmp / f"sorted-{tid}.json"
    sorted_berth.write_text(json.dumps({"skill": "sorted", "answers": {
        "workflow": WORKFLOWS[kind], "node_class": kind}}), encoding="utf-8")
    intent_berth = tmp / "intent.json"
    intent_berth.write_text(json.dumps({"skill": "intent"}), encoding="utf-8")
    return {
        "id": tid, "title": f"testing a {kind} that brings {Path(proof).stem} {tid}",
        "date": "2026-11-16", "owner": "CC",
        "owning_intention": "cairn/tools/base/intention+why" + ".json",
        "intention": "a fixture", "why": "a fixture why", "traces_to": "Law 8",
        "how": "a fixture how", "falsifier": {"clauses": [{"n": 1, "claim": "the fixture holds"}]},
        "bounds": {"in": [CODE, proof], "out": ["every other component"]},
        "measured": [{"when": "2026-11-16", "saw": "a fixture", "how": "a fixture run"}],
        "node_class": kind, "workflow_and_state": WORKFLOWS[kind],
        "watchme": "none, because its proof " + SEALED + " is the whole of its correctness",
        "sorted_berth": str(sorted_berth), "intent_berth": str(intent_berth),
    }


def _cast(doc: dict, tickets: Path):
    """(path, None) on a cast, (None, lacks) on a refusal."""
    from cairn.tools.base.transitions import CastRefused, cast_ticket
    try:
        return cast_ticket(doc, actor="proof-actor", tickets_dir=tickets), None
    except CastRefused as exc:
        return None, list(exc.lacks)


def tooth_1(tmp: Path, tickets: Path) -> None:
    name = PROVES["cf4482b200a1"]["1"]
    try:
        tid = "cf440000a001"
        p, lacks = _cast(_doc(tmp, tid, "bug", NEW), tickets)
        landed = [x.name for x in tickets.glob(f"{tid}-*")]
        named = [x for x in (lacks or []) if NEW in x and "code-seam@v2" in x]
        check(name, p is None and not landed and len(named) == 1,
              f"path={p} landed={landed} lacks={lacks}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(tmp: Path, tickets: Path) -> None:
    name = PROVES["cf4482b200a1"]["2"]
    try:
        p, lacks = _cast(_doc(tmp, "cf440000b001", "code-seam", NEW), tickets)
        check(name, p is not None, f"path={p} lacks={lacks}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(tmp: Path, tickets: Path) -> None:
    name = PROVES["cf4482b200a1"]["3"]
    try:
        from cairn.tools.base.validation import latest_seal
        seal = latest_seal(str(REPO / SEALED))
        p, lacks = _cast(_doc(tmp, "cf440000c001", "bug", SEALED), tickets)
        check(name, seal is not None and p is not None,
              f"sibling sealed={seal is not None} path={p} lacks={lacks}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-cf4482b200a1-bug-new-proof-")
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
        tooth_3(tmp, tickets)
    finally:
        A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

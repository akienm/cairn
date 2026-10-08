"""Proof for ticket 3d9cedf76a7e — a ticket's cursor crosses through one command.

Teeth a hollow build could not pass (Law 8), every one over a SCRATCH world the proof owns:
a scratch commons handed to the artifact door (``artifact.set_diagnostic_roots``, restored in
``finally``) and a scratch repo root whose component directory holds the fixture charter.
The live store, the live journal and every live history are never touched.

1. a back-edge BUILDME -> TICKETME on a fixture ticket moves ``workflow_and_state`` to exactly
   emit's return, appends the crossing (ticket=<id>) to the fixture component's history, and
   the ticket write is the artifact door's journal line, verb cast — driven through main(argv);
2. an illegal target (a forward skip) is refused and the ticket and history are byte-identical;
3. PROVED is refused naming harbor_master's clearance, exit 1, nothing written;
4. an owning_intention whose directory holds no charter is refused naming it, nothing written.

THE SUBJECT IS BOUND AT CALL TIME. ``_cross()`` imports the build when a tooth asks, so a
worktree with cairn/tools/base/cross.py reverted reds every declared tooth by name instead
of failing at import.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_crossing_runs_through_one_command.py
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "3d9cedf76a7e": {
        "1": "test_a_back_edge_moves_the_cursor_and_journals_it",
        "2": "test_an_illegal_target_writes_nothing",
        "3": "test_proved_is_refused_naming_clearance",
        "4": "test_a_charterless_owning_intention_is_refused",
    },
}

FAILURES: list[str] = []
TID = "abc123def456"
AT_BUILDME = "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"
AT_TICKETME = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
AT_PROVEME = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME:waiting] -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _cross():
    from cairn.tools.base import cross
    return cross


class World:
    """A scratch commons + scratch repo root with one fixture component and one ticket."""

    def __init__(self, label: str, workflow: str, *, charter: bool = True) -> None:
        from cairn.tools.scratch.scratch import scratch_dir
        base = scratch_dir(f"cross-proof-{label}-")
        self.commons = base / "CairnCommons"
        self.tickets = self.commons / "tickets"
        self.tickets.mkdir(parents=True)
        self.repo = base / "repo"
        self.component = self.repo / "fixture" / "component"
        self.component.mkdir(parents=True)
        if charter:
            (self.component / "intention+why.json").write_text(
                json.dumps({"intention": "a fixture component for the crossing proof"}) + "\n",
                encoding="utf-8")
        self.ticket = self.tickets / f"{TID}-a-fixture-ticket.json"
        self.ticket.write_text(json.dumps({
            "id": TID, "title": "a fixture ticket",
            "owning_intention": "fixture/component/intention+why.json",
            "workflow_and_state": workflow}, indent=2) + "\n", encoding="utf-8")
        self.history = self.component / "history.json"

    def snapshot(self) -> tuple:
        return (self.ticket.read_bytes(),
                self.history.read_bytes() if self.history.exists() else None)

    def main(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            rc = _cross().main(list(argv), tickets_dir=self.tickets, repo_root=self.repo)
        return rc, out.getvalue()


# --------------------------------------------------------------------------- the teeth


def test_a_back_edge_moves_the_cursor_and_journals_it(A) -> None:
    w = World("t1", AT_BUILDME)
    A.set_diagnostic_roots({"CairnCommons": w.commons, "cairn": REPO})
    try:
        before = len(A.read_journal(w.commons))
        rc, out = w.main(TID, "TICKETME", "--actor", "proof", "--why", "tooth 1 back-edge")
        doc = json.loads(w.ticket.read_text(encoding="utf-8"))
        hist = json.loads(w.history.read_text(encoding="utf-8")) if w.history.exists() else []
        entries = A.read_journal(w.commons)
    finally:
        A.set_diagnostic_roots(None)
    ok = (rc == 0 and doc.get("workflow_and_state") == AT_TICKETME
          and out.strip().splitlines()[-1:] == [AT_TICKETME]
          and len(hist) == 1 and hist[0].get("ticket") == TID
          and hist[0].get("workflow") == AT_TICKETME and hist[0].get("actor") == "proof"
          and len(entries) == before + 1 and entries[-1].get("verb") == "cast"
          and entries[-1].get("path") == f"tickets/{w.ticket.name}")
    check(PROVES["3d9cedf76a7e"]["1"], ok,
          f"rc={rc} cursor={doc.get('workflow_and_state')!r} history={len(hist)} "
          f"journal+{len(entries) - before} out={out.strip()[-160:]!r}")


def test_an_illegal_target_writes_nothing(A) -> None:
    w = World("t2", AT_TICKETME)
    snap = w.snapshot()
    A.set_diagnostic_roots({"CairnCommons": w.commons, "cairn": REPO})
    try:
        before = len(A.read_journal(w.commons))
        rc, out = w.main(TID, "PROVEME", "--actor", "proof", "--why", "tooth 2 forward skip")
        after = len(A.read_journal(w.commons))
    finally:
        A.set_diagnostic_roots(None)
    ok = rc == 1 and w.snapshot() == snap and after == before and "illegal" in out
    check(PROVES["3d9cedf76a7e"]["2"], ok,
          f"rc={rc} unchanged={w.snapshot() == snap} journal+{after - before} out={out.strip()[-160:]!r}")


def test_proved_is_refused_naming_clearance(A) -> None:
    w = World("t3", AT_PROVEME)
    snap = w.snapshot()
    A.set_diagnostic_roots({"CairnCommons": w.commons, "cairn": REPO})
    try:
        rc, out = w.main(TID, "PROVED", "--actor", "proof", "--why", "tooth 3 rest",
                         "--proven-by", "fixture/component/proofs/test_x.py")
    finally:
        A.set_diagnostic_roots(None)
    ok = rc == 1 and w.snapshot() == snap and "PROVED" in out and "clearance" in out
    check(PROVES["3d9cedf76a7e"]["3"], ok,
          f"rc={rc} unchanged={w.snapshot() == snap} out={out.strip()[-160:]!r}")


def test_a_charterless_owning_intention_is_refused(A) -> None:
    w = World("t4", AT_BUILDME, charter=False)
    snap = w.snapshot()
    A.set_diagnostic_roots({"CairnCommons": w.commons, "cairn": REPO})
    try:
        rc, out = w.main(TID, "TICKETME", "--actor", "proof", "--why", "tooth 4 charterless")
    finally:
        A.set_diagnostic_roots(None)
    ok = (rc == 1 and w.snapshot() == snap and not w.history.exists()
          and "fixture/component" in out and "charter" in out)
    check(PROVES["3d9cedf76a7e"]["4"], ok,
          f"rc={rc} unchanged={w.snapshot() == snap} out={out.strip()[-160:]!r}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    live = A.journal_path(A.roots()["CairnCommons"])
    live_before = live.read_bytes() if live.exists() else b""
    for tooth in (test_a_back_edge_moves_the_cursor_and_journals_it,
                  test_an_illegal_target_writes_nothing,
                  test_proved_is_refused_naming_clearance,
                  test_a_charterless_owning_intention_is_refused):
        try:
            tooth(A)
        except Exception as exc:  # noqa: BLE001 — a subject whose build was taken away
            check(tooth.__name__, False, f"aborted: {type(exc).__name__}: {exc}")
    live_after = live.read_bytes() if live.exists() else b""
    check("the live journal never moved", live_before == live_after)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

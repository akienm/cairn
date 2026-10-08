"""Proof for ticket 3d9cedf76a7e — a ticket's cursor crosses through one command.

Teeth a hollow build could not pass (Law 8), every one over a SCRATCH world the proof owns
(D2): ``root = scratch_dir('cross-command-fixture-')``, a commons at root/CairnCommons with
tickets/, a repo at root/cairn holding only comp/intention+why.json, both handed to the
artifact door (``artifact.set_diagnostic_roots``) and restored in ``finally``. The live
store, the live journal and every live history are never touched. The world also carries
root/CairnCommons/node_classes/code-seam.json, a copy of the live class definition handed to
cross() as ``node_class_root`` (D9, the F18 pattern): the hollow's worktree has no CairnCommons
beside it, so transitions' default node-class root points at nothing there (measured
2026-10-08 at fc32dafc: "unknown node-class 'code-seam'" reds teeth 1 and 3).

1. a back-edge PROVEME -> BUILDME on a fixture ticket: the ticket's workflow_and_state equals
   cross()'s return, which carries [BUILDME], and comp/history.json gained one record naming
   the ticket;
2. target 'NOTASTAGE' raises naming the vocabulary, ticket and history bytes identical;
3. target 'PROVED' raises naming clearance, bytes identical;
4. an owning_intention 'nowhere/intention+why.json' raises naming no charter, bytes identical.
Each refusal is asserted by its own text (D9), so none can pass on a node-class lookup refusal.
Each tooth is driven once more through main() over a fresh world for its exit code (0 on
tooth 1, 1 on teeth 2-4); main() reads transitions._TICKETS, transitions._REPO_ROOT and transitions._NODE_CLASSES,
which the proof points at the fresh world and restores in ``finally``.

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
        "1": "test_a_crossing_moves_the_cursor_and_journals_at_the_component",
        "2": "test_an_illegal_target_writes_nothing",
        "3": "test_proved_is_refused_naming_clearance",
        "4": "test_an_owning_intention_with_no_charter_is_refused",
    },
}

FAILURES: list[str] = []
_LIVE_NODE_CLASSES = next((c / "node_classes" for c in (REPO.parent / "CairnCommons",
                                                        Path.home() / "dev" / "src" / "CairnCommons")
                           if (c / "node_classes" / "code-seam.json").is_file()), None)
TID = "abc123def456"
AT_PROVEME = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _cross():
    from cairn.tools.base import cross
    return cross


class World:
    """The D2 fixture: a scratch commons with one ticket, a scratch repo with one charter."""

    def __init__(self, owning_intention: str = "comp/intention+why.json") -> None:
        from cairn.tools.scratch.scratch import scratch_dir
        root = Path(scratch_dir("cross-command-fixture-"))
        self.commons = root / "CairnCommons"
        self.tickets = self.commons / "tickets"
        self.tickets.mkdir(parents=True)
        self.repo = root / "cairn"
        self.comp = self.repo / "comp"
        self.comp.mkdir(parents=True)
        (self.comp / "intention+why.json").write_text("{}", encoding="utf-8")
        assert _LIVE_NODE_CLASSES is not None, \
            "no CairnCommons/node_classes/code-seam.json beside the repo or under $HOME"
        self.node_classes = self.commons / "node_classes"
        self.node_classes.mkdir()
        (self.node_classes / "code-seam.json").write_bytes(
            (_LIVE_NODE_CLASSES / "code-seam.json").read_bytes())
        self.ticket = self.tickets / f"{TID}-a-fixture-ticket.json"
        self.ticket.write_text(json.dumps({
            "id": TID, "owning_intention": owning_intention,
            "workflow_and_state": AT_PROVEME}, indent=2) + "\n", encoding="utf-8")
        self.history = self.comp / "history.json"
        self.state = self.comp / "state.json"

    def snapshot(self) -> tuple:
        return tuple(p.read_bytes() if p.exists() else None
                     for p in (self.ticket, self.history, self.state))

    @contextlib.contextmanager
    def door(self, A):
        A.set_diagnostic_roots({"CairnCommons": self.commons, "cairn": self.repo})
        try:
            yield
        finally:
            A.set_diagnostic_roots(None)

    def cross(self, A, target: str):
        """cross() with this world's store and repo; returns (new, exception)."""
        with self.door(A):
            try:
                return _cross().cross(TID, target, actor="proof", why=f"proof: {target}",
                                      tickets_dir=self.tickets, repo_root=self.repo,
                                      node_class_root=self.node_classes), None
            except ImportError:
                raise
            except Exception as exc:  # noqa: BLE001 — a refusal is the measured outcome
                return None, exc

    def main_rc(self, A, target: str) -> int:
        """main(argv) with transitions' store, repo and node classes pointed here, restored after."""
        from cairn.tools.base import transitions as T
        saved = (T._TICKETS, T._REPO_ROOT, T._NODE_CLASSES)
        out = io.StringIO()
        with self.door(A):
            T._TICKETS, T._REPO_ROOT, T._NODE_CLASSES = self.tickets, self.repo, self.node_classes
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                    return _cross().main([TID, target, "--actor", "proof", "--why", "proof"])
            finally:
                T._TICKETS, T._REPO_ROOT, T._NODE_CLASSES = saved


# --------------------------------------------------------------------------- the teeth


def test_a_crossing_moves_the_cursor_and_journals_at_the_component(A) -> None:
    w = World()
    new, exc = w.cross(A, "BUILDME")
    cursor = json.loads(w.ticket.read_text(encoding="utf-8")).get("workflow_and_state")
    hist = json.loads(w.history.read_text(encoding="utf-8")) if w.history.exists() else []
    rc = World().main_rc(A, "BUILDME")
    ok = (exc is None and isinstance(new, str) and "[BUILDME" in new and cursor == new
          and len(hist) == 1 and hist[0].get("ticket") == TID and rc == 0)
    check(PROVES["3d9cedf76a7e"]["1"], ok,
          f"exc={exc!r} new={new!r} cursor={cursor!r} history={len(hist)} main rc={rc}")


def _refused(A, name: str, target: str, *, owning: str = "comp/intention+why.json",
             says: str = "") -> None:
    w = World(owning)
    snap = w.snapshot()
    new, exc = w.cross(A, target)
    rc = World(owning).main_rc(A, target)
    ok = (exc is not None and new is None and w.snapshot() == snap
          and (not says or says in str(exc)) and rc == 1)
    check(name, ok, f"exc={exc!r} unchanged={w.snapshot() == snap} main rc={rc}")


def test_an_illegal_target_writes_nothing(A) -> None:
    _refused(A, PROVES["3d9cedf76a7e"]["2"], "NOTASTAGE",
             says="not in the code-seam@v2 vocabulary")


def test_proved_is_refused_naming_clearance(A) -> None:
    _refused(A, PROVES["3d9cedf76a7e"]["3"], "PROVED", says="clearance")


def test_an_owning_intention_with_no_charter_is_refused(A) -> None:
    _refused(A, PROVES["3d9cedf76a7e"]["4"], "BUILDME", owning="nowhere/intention+why.json",
             says="names no charter")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    live = A.journal_path(A.roots()["CairnCommons"])
    live_before = live.read_bytes() if live.exists() else b""
    for tooth, name in ((test_a_crossing_moves_the_cursor_and_journals_at_the_component, "1"),
                        (test_an_illegal_target_writes_nothing, "2"),
                        (test_proved_is_refused_naming_clearance, "3"),
                        (test_an_owning_intention_with_no_charter_is_refused, "4")):
        try:
            tooth(A)
        except Exception as exc:  # noqa: BLE001 — a subject whose build was taken away
            check(PROVES["3d9cedf76a7e"][name], False, f"aborted: {type(exc).__name__}: {exc}")
    live_after = live.read_bytes() if live.exists() else b""
    check("the live journal never moved", live_before == live_after)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

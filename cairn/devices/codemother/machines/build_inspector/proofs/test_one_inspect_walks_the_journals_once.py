#!/usr/bin/env python3
"""Proof that one whole-tree inspect() lists the history.json journals of each root once
(ticket 7bdcd8a801df).

Measured 2026-11-22 on akiendelllinux: a whole-tree inspect() took 560.6 s; under cProfile,
proof_covers_the_ticket alone spent 164 of 253 s in crossings._index -> journals(), an
rglob('history.json') over both repos called 2041 times. _index cached its parse but keyed the
cache on a fresh rglob, so the walk was never saved. crossings.pinned_journals() pins the
listing per roots while a scope is open, and inspect() opens it around its body.

  (1) one whole-tree inspect() over the house tree calls Path.rglob('history.json') at most once
      per root, and the proof prints its wall time;
  (2) with no scope open, a history.json created under a scratch root between two journals()
      calls is listed by the second;
  (3) inside an open scope, a listed journal whose bytes change between two crossings_for calls
      is re-parsed: the second call sees the new entry.

    PYTHONPATH=. python3 cairn/devices/codemother/machines/build_inspector/proofs/test_one_inspect_walks_the_journals_once.py
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(_REPO))

from cairn.tools.base import crossings  # noqa: E402

PROVES = {"7bdcd8a801df": {
    "1": "test_clause_1_one_inspect_walks_each_root_once",
    "2": "test_clause_2_with_no_scope_a_new_journal_is_seen",
    "3": "test_clause_3_inside_a_scope_changed_bytes_are_reparsed",
}}

PROOF_TIMEOUT_S = 900

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _journal(path: Path, ticket: str, at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    if path.exists():
        entries = json.loads(path.read_text(encoding="utf-8"))["entries"]
    entries.append({"ticket": ticket, "at": at, "from": "TICKETME", "to": "BUILDME",
                    "direction": "forward"})
    path.write_text(json.dumps({"entries": entries}), encoding="utf-8")


def _scratch_roots(tmp: Path) -> dict:
    repo, commons = tmp / "repo", tmp / "commons"
    repo.mkdir()
    commons.mkdir()
    return {"repo": repo, "commons": commons}


def test_clause_1_one_inspect_walks_each_root_once() -> None:
    from cairn.devices.codemother.machines.build_inspector import inspector
    calls: dict[str, int] = {}
    real = pathlib.Path.rglob

    def counting(self, pattern, *a, **k):
        if pattern == "history.json":
            calls[str(self)] = calls.get(str(self), 0) + 1
        return real(self, pattern, *a, **k)

    pathlib.Path.rglob = counting
    t0 = time.perf_counter()
    try:
        inspector.inspect()
    finally:
        pathlib.Path.rglob = real
    wall = time.perf_counter() - t0
    worst = max(calls.values()) if calls else 0
    check("test_clause_1_one_inspect_walks_each_root_once", bool(calls) and worst <= 1,
          f"rglob('history.json') per root {calls}; whole-tree inspect() wall {wall:.1f} s")


def test_clause_2_with_no_scope_a_new_journal_is_seen() -> None:
    with tempfile.TemporaryDirectory() as td:
        roots = _scratch_roots(Path(td))
        first = crossings.journals(roots)
        _journal(roots["repo"] / "a" / "history.json", "aaaaaaaaaaaa", "2026-11-22T00:00:01")
        second = crossings.journals(roots)
        check("test_clause_2_with_no_scope_a_new_journal_is_seen",
              first == [] and len(second) == 1, f"before {first}, after {second}")


def test_clause_3_inside_a_scope_changed_bytes_are_reparsed() -> None:
    pin = getattr(crossings, "pinned_journals", None)
    if pin is None:
        check("test_clause_3_inside_a_scope_changed_bytes_are_reparsed", False,
              "crossings.pinned_journals does not exist")
        return
    with tempfile.TemporaryDirectory() as td:
        roots = _scratch_roots(Path(td))
        j = roots["repo"] / "a" / "history.json"
        _journal(j, "bbbbbbbbbbbb", "2026-11-22T00:00:01")
        with pin():
            before = len(crossings.crossings_for("bbbbbbbbbbbb", roots))
            time.sleep(0.01)
            _journal(j, "bbbbbbbbbbbb", "2026-11-22T00:00:02")
            after = len(crossings.crossings_for("bbbbbbbbbbbb", roots))
        check("test_clause_3_inside_a_scope_changed_bytes_are_reparsed",
              before == 1 and after == 2, f"crossings before {before}, after {after}")


if __name__ == "__main__":
    test_clause_2_with_no_scope_a_new_journal_is_seen()
    test_clause_3_inside_a_scope_changed_bytes_are_reparsed()
    test_clause_1_one_inspect_walks_each_root_once()
    print(f"{len(FAILURES)} failed" if FAILURES else "all teeth green")
    raise SystemExit(1 if FAILURES else 0)

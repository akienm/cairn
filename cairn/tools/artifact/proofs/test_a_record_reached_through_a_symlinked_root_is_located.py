#!/usr/bin/env python3
"""Proof that the door finds a record reached through a symlinked default root (ticket 47995fff1c32).

MEASURED 2026-11-20 on akiendelllinux: hollow links the standing commons beside its worktree as
a symlink (ticket 19193ff1e41e). ``locate`` resolves the path it is asked about, which follows the
link, but compares it against the DEFAULT root ``_REPO.parent / "CairnCommons"`` unresolved, so
``relative_to`` fails and ``locate`` answers None for every commons record. So the artifact gate
guards nothing in that worktree, and bin/proofs/test_artifact_gate.py reads 12 FAILs there.
(The env seam ``CAIRN_ARTIFACT_ROOTS`` and ``set_diagnostic_roots`` already resolve their roots.)

Teeth, one per falsifier clause, over a scratch layout: ``<tmp>/wt`` stands for the repo, and
``<tmp>/CairnCommons`` is a symlink to ``<tmp>/standing`` (the hollow layout). ``_REPO`` is pointed
at ``<tmp>/wt`` and no env or diagnostic root is set, so the default branch of ``roots()`` answers.
  (1) a ticket path spelled through the symlinked root locates as a CairnCommons record;
  (2) the same ticket spelled at the link's target locates as the same record;
  (3) a path under neither root still locates as None, and a non-record path under the
      symlinked root (notes/) still locates as None.

    bin/cairn test cairn/tools/artifact/proofs/test_a_record_reached_through_a_symlinked_root_is_located.py
"""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {"47995fff1c32": {
    "1": "test_a_ticket_through_the_symlinked_root_is_a_record",
    "2": "test_the_same_ticket_at_the_links_target_is_the_same_record",
    "3": "test_what_is_not_a_record_stays_outside",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _teeth(tmp: Path) -> None:
    # Bound at call time: a reverted subject reds the teeth instead of crashing the import.
    A = importlib.import_module("cairn.tools.artifact.artifact")
    os.environ.pop("CAIRN_ARTIFACT_ROOTS", None)
    A.set_diagnostic_roots(None)
    (tmp / "wt").mkdir()
    (tmp / "standing" / "tickets").mkdir(parents=True)
    (tmp / "standing" / "notes").mkdir()
    (tmp / "CairnCommons").symlink_to(tmp / "standing", target_is_directory=True)
    saved = A._REPO
    A._REPO = tmp / "wt"
    try:
        via_link = A.locate(tmp / "CairnCommons" / "tickets" / "abcdef012345-x.json")
        check(PROVES["47995fff1c32"]["1"],
              via_link is not None and via_link[0] == "CairnCommons"
              and via_link[2].as_posix() == "tickets/abcdef012345-x.json",
              f"locate={via_link}")
        at_target = A.locate(tmp / "standing" / "tickets" / "abcdef012345-x.json")
        check(PROVES["47995fff1c32"]["2"],
              at_target is not None and via_link is not None
              and (at_target[0], at_target[2]) == (via_link[0], via_link[2]),
              f"locate={at_target} beside {via_link}")
        outside = A.locate(tmp / "elsewhere" / "tickets" / "abcdef012345-x.json")
        note = A.locate(tmp / "CairnCommons" / "notes" / "x.md")
        check(PROVES["47995fff1c32"]["3"], outside is None and note is None,
              f"outside={outside} note={note}")
    finally:
        A._REPO = saved


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="testing-locate-link-") as t:
            _teeth(Path(t).resolve())
    except Exception as exc:  # noqa: BLE001 — a subject whose world was taken away
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["47995fff1c32"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

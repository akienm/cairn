"""Proof that the components the outline retires are gone from class-space.

Outline rule 1.3.7: code that is no longer needed is deleted; git history keeps it. A deleted
component cannot hold its own proof, so the retirements berth here, in bin: the surface every
Cairn facility is reached through. Each retirement ticket adds its own PROVES key and teeth.

Ticket 80df7712b8c5 (quarry_index, outline 17.13 / Q#44, Akien 2026-11-06), one tooth per
falsifier clause:

  1. cairn/machines/quarry_index/ is absent from the working tree;
  2. no file in the repo names the module or its folder (dot-records and caches excepted);
  3. the compiler module cannot be loaded: importing it exits nonzero with "No module named"
     (an import, never `-m`, so the red-first run cannot run the compiler).

Reads only the repo, never CairnCommons (the hollow worktree has none beside it).

    python3 bin/proofs/test_retired_components_are_gone.py   # exit 0 = green
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()

PROVES = {
    "80df7712b8c5": {
        "1": "quarry_index_folder_is_absent",
        "2": "nothing_names_quarry_index",
        "3": "quarry_index_compiler_does_not_import",
    },
}

FAILURES: list[str] = []

# names written split, so this file never matches its own search
_QI_MODULE = "cairn.machines." + "quarry_index"
_QI_PATH = "cairn/machines/" + "quarry_index"


def _check(name: str, ok: bool, detail: str = "") -> None:
    # the label is the tooth's PROVES name: the hollow reading reads green teeth by it
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1400]}", flush=True)
        FAILURES.append(name)


def _naming(needles: tuple[str, ...]) -> list[str]:
    """Repo files whose text holds any needle. Skipped: this proof, __pycache__, egg-info, and
    every dot-file and dot-folder (.git, .pytest_cache, .artifact-journal.jsonl): those are
    records and caches that name what passed through, never callers."""
    hits: list[str] = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "cairn.egg-info")]
        for f in files:
            if f.startswith("."):
                continue
            p = Path(root) / f
            if p.resolve() == SELF:
                continue
            try:
                text = p.read_text(errors="ignore")
            except OSError:
                continue
            if any(n in text for n in needles):
                hits.append(str(p.relative_to(REPO)))
    return hits


def _gone(name: str, folder: str, module: str, runnable: str) -> None:
    """The three retirement teeth for one component."""
    p = REPO / folder
    _check(PROVES_NAME[name][0], not p.exists(), f"{folder} still exists")
    hits = _naming((module, folder))
    _check(PROVES_NAME[name][1], not hits, "named by: " + ", ".join(hits[:12]))
    # import, never -m: running the module while it still stands would run it
    r = subprocess.run([sys.executable, "-c", f"import {runnable}"], cwd=REPO,
                       capture_output=True, text=True, timeout=60)
    _check(PROVES_NAME[name][2], r.returncode != 0 and "No module named" in r.stderr,
           f"rc={r.returncode} stderr={r.stderr[-300:]!r}")


PROVES_NAME = {
    "quarry_index": [PROVES["80df7712b8c5"][k] for k in ("1", "2", "3")],
}


def check() -> list[str]:
    FAILURES.clear()
    _gone("quarry_index", _QI_PATH, _QI_MODULE, _QI_MODULE + ".compiler")
    return list(FAILURES)


def main() -> int:
    fails = check()
    print(f"retired components proofs: {'all green' if not fails else f'{len(fails)} red'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Proof for ticket 5dc2364a8adb — the inspector judges only the census root's own repo.

Measured 2026-11-16 on ticket 6ea3a8548493: a test_transitions fixture laid its census root at
/tmp/tmpXXX/<name>, and encapsulation_holds took the directory holding it (/tmp) as the repo.
import_sites AST-parsed 13,947 foreign .py files per gated crossing, ~97 s each.

1. with the census root at <tmp>/outer/<name>, encapsulation_holds hands import_sieve.import_sites
   the census root, never <tmp>/outer, and a breach-shaped .py planted directly under
   <tmp>/outer is not read;
2. with the census root at <tmp>/outer/<name> and <tmp>/outer a git repo with one tracked file
   carrying the debt word, no_iou_stands reports no site from that file;
3. with the live shape <tmp>/cairn/<comp>, both sieves still take <tmp> as the repo, and
   encapsulation_holds still reds a real cross-device import planted under <tmp>/cairn.

Every fixture is a scratch_dir (swept at exit); nothing reads or writes the live repo.

Run bare:  PYTHONPATH=. python3 cairn/machines/build_inspector/proofs/test_a_census_root_outside_a_repo_reads_only_itself.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402  the fixture door; swept at exit


class _Late:
    """Resolve the subject at call time, so `cairn test --hollow` reads red teeth, not UNRAN."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.machines.build_inspector.inspector")

PROVES = {
    "5dc2364a8adb": {
        "1": "a_census_root_outside_a_repo_is_the_only_tree_import_sites_reads",
        "2": "an_iou_in_the_directory_holding_the_census_root_is_not_a_site",
        "3": "the_live_shape_still_takes_the_parent_of_cairn_and_still_reds_a_breach",
    },
}

PASS = 0
FAIL = 0
BREACH = "from cairn.devices.d import internal\n"
IOU_WORD = "I" + "OU"   # spelled apart so this proof is no IOU site itself


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _charter() -> str:
    return json.dumps({"what": "a fixture component", "why": "a fixture component"})


def _lay(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def _census_files() -> dict[str, str]:
    """A census root's contents: device a reaching into device d, and build_inspector's row."""
    return {"devices/d/intention+why.json": _charter(),
            "devices/d/internal.py": "X = 1\n",
            "devices/a/intention+why.json": _charter(),
            "devices/a/a.py": BREACH,
            "machines/build_inspector/intention+why.json": _charter()}


def _git_commit(root: Path) -> None:
    env_cfg = ["-c", "user.email=testing@example.invalid", "-c", "user.name=testing"]
    for cmd in (["init", "-q"], ["add", "-A"], [*env_cfg, "commit", "-q", "-m", "testing"]):
        subprocess.run(["git", "-C", str(root), *cmd], check=True, capture_output=True,
                       env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin"})


def _clear() -> None:
    _inspector._BREACH_CACHE.clear()
    _inspector._CENSUS_DIRS.clear()
    _inspector._IOU_CACHE.clear()


def _encapsulation(census_root: Path, row_dir: str) -> tuple[list[dict], list[str]]:
    """Run encapsulation_holds on one row, recording every tree import_sites is handed."""
    sieve = _inspector.import_sieve
    real = sieve.import_sites
    seen: list[str] = []

    def recording(repo_root, *a, **k):
        seen.append(str(Path(repo_root).resolve()))
        return real(repo_root, *a, **k)

    _clear()
    sieve.import_sites = recording
    try:
        row = {"component": row_dir.rsplit("/", 1)[-1], "dir": row_dir}
        findings = _inspector.encapsulation_holds(row, census_root / row_dir)
    finally:
        sieve.import_sites = real
    return findings, seen


def _iou(census_root: Path, row_dir: str) -> list[dict]:
    _clear()
    row = {"component": row_dir.rsplit("/", 1)[-1], "dir": row_dir}
    return _inspector.no_iou_stands(row, census_root / row_dir)


def a_census_root_outside_a_repo_is_the_only_tree_import_sites_reads():
    tmp = scratch_dir("testing-census-root-outside-")
    outer = tmp / "outer"
    census = outer / "pkg"
    _lay(census, _census_files())
    _lay(outer, {"stray.py": BREACH})          # breach-shaped, directly under <tmp>/outer
    findings, seen = _encapsulation(census, "devices/a")
    want = str(census.resolve())
    assert seen, "import_sites was never called"
    assert set(seen) == {want}, f"import_sites read {sorted(set(seen))}, want only {want}"
    stray = [f for f in findings if "stray.py" in json.dumps(f, default=str)]
    assert not stray, f"a file under <tmp>/outer was read: {stray}"


def an_iou_in_the_directory_holding_the_census_root_is_not_a_site():
    tmp = scratch_dir("testing-census-root-outside-iou-")
    outer = tmp / "outer"
    census = outer / "pkg"
    _lay(census, _census_files())
    _lay(outer, {"notes.txt": f"this rests as an {IOU_WORD} for later\n"})
    _git_commit(outer)
    sites = _iou(census, "machines/build_inspector")
    from_outer = [s for s in sites if "notes.txt" in json.dumps(s, default=str)]
    assert not from_outer, f"no_iou_stands reported a site outside the census root: {from_outer}"


def the_live_shape_still_takes_the_parent_of_cairn_and_still_reds_a_breach():
    tmp = scratch_dir("testing-census-root-live-shape-")
    census = tmp / "cairn"
    _lay(census, _census_files())
    _lay(census, {"machines/build_inspector/stands.txt": f"an {IOU_WORD} rests here\n"})
    _git_commit(tmp)
    findings, seen = _encapsulation(census, "devices/a")
    want = str(tmp.resolve())
    assert set(seen) == {want}, f"import_sites read {sorted(set(seen))}, want only {want}"
    hits = [f for f in findings if "cairn/devices/a/a.py" in json.dumps(f, default=str)]
    assert hits, f"the cross-device import under <tmp>/cairn did not red: {findings}"
    sites = _iou(census, "machines/build_inspector")
    assert any("stands.txt" in json.dumps(s, default=str) for s in sites), \
        f"no_iou_stands did not read the repo at <tmp>: {sites}"


def main() -> int:
    print("the inspector judges only the census root's own repo (ticket 5dc2364a8adb)")
    _tooth("a_census_root_outside_a_repo_is_the_only_tree_import_sites_reads",
           a_census_root_outside_a_repo_is_the_only_tree_import_sites_reads)
    _tooth("an_iou_in_the_directory_holding_the_census_root_is_not_a_site",
           an_iou_in_the_directory_holding_the_census_root_is_not_a_site)
    _tooth("the_live_shape_still_takes_the_parent_of_cairn_and_still_reds_a_breach",
           the_live_shape_still_takes_the_parent_of_cairn_and_still_reds_a_breach)
    print(f"{'GREEN' if not FAIL else 'RED'} — {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

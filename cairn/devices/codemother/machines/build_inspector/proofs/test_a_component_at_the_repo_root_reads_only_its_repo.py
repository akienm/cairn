"""Proof for ticket 46a93ddcc122 — a component at the repo root (bin) is judged against its repo alone.

Measured 2026-11-18 on the PROVED crossing of ticket 8c5fdb750b75 (component bin): the gate passes
root=comp_dir.parent, which for bin is the repo itself, and the repo is named cairn, so _repo_of
took its parent (~/dev/src) and import_sites parsed all 85 worktrees there. The clearance never
answered inside 120 s. The row's own address was also 'cairn/bin' while breaches are keyed 'bin',
so no breach could ever land on bin.

1. with the census root at <tmp>/cairn holding a cairn/ package and a bin/ component,
   encapsulation_holds for row bin hands import_sieve.import_sites only <tmp>/cairn, and a
   breach-shaped .py under a sibling <tmp>/wt-x is not read;
2. a cross-device import planted in <tmp>/cairn/bin/ reds on row bin;
3. the live shape <tmp>/cairn/devices/a (census root <tmp>/cairn with no cairn/ child) still takes
   <tmp> as the repo and still reds a cross-device import on row devices/a.

Every fixture is a scratch_dir (swept at exit); nothing reads or writes the live repo.

Run bare:  PYTHONPATH=. python3 cairn/devices/codemother/machines/build_inspector/proofs/test_a_component_at_the_repo_root_reads_only_its_repo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402  the fixture door; swept at exit


class _Late:
    """Resolve the subject at call time, so `cairn test --hollow` reads red teeth, not UNRAN."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.devices.codemother.machines.build_inspector.inspector")

PROVES = {
    "46a93ddcc122": {
        "1": "a_repo_root_component_reads_only_its_repo",
        "2": "a_breach_under_bin_reds_on_bin",
        "3": "the_live_shape_still_takes_the_parent_of_cairn_and_still_reds_a_breach",
    },
}

PASS = 0
FAIL = 0
BREACH = "from cairn.devices.d import internal\n"


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


def _package(prefix: str) -> dict[str, str]:
    """A cairn package's contents at ``prefix``: device d, and device a reaching into it."""
    return {f"{prefix}devices/d/intention+why.json": _charter(),
            f"{prefix}devices/d/internal.py": "X = 1\n",
            f"{prefix}devices/a/intention+why.json": _charter(),
            f"{prefix}devices/a/a.py": BREACH,
            f"{prefix}machines/build_inspector/intention+why.json": _charter()}


def _repo_root_shape(bin_text: str) -> Path:
    """<tmp>/cairn is a repo root: a cairn/ package, a bin/ component, a stray sibling worktree."""
    tmp = scratch_dir("testing-repo-root-component-")
    repo = tmp / "cairn"
    _lay(repo, {**_package("cairn/"), "bin/intention+why.json": _charter(), "bin/tool.py": bin_text})
    _lay(tmp, {"wt-x/stray.py": BREACH, **_package("wt-x/cairn/")})
    return repo


def _encapsulation(census_root: Path, row_dir: str) -> tuple[list[dict], list[str]]:
    """Run encapsulation_holds on one row, recording every tree import_sites is handed."""
    sieve = _inspector.import_sieve
    real = sieve.import_sites
    seen: list[str] = []

    def recording(repo_root, *a, **k):
        seen.append(str(Path(repo_root).resolve()))
        return real(repo_root, *a, **k)

    _inspector._BREACH_CACHE.clear()
    _inspector._CENSUS_DIRS.clear()
    sieve.import_sites = recording
    try:
        row = {"component": row_dir.rsplit("/", 1)[-1], "dir": row_dir}
        findings = _inspector.encapsulation_holds(row, census_root / row_dir)
    finally:
        sieve.import_sites = real
    return findings, seen


def a_repo_root_component_reads_only_its_repo():
    repo = _repo_root_shape("X = 1\n")
    findings, seen = _encapsulation(repo, "bin")
    want = str(repo.resolve())
    assert seen, "import_sites was never called"
    assert set(seen) == {want}, f"import_sites read {sorted(set(seen))}, want only {want}"
    stray = [f for f in findings if "wt-x" in json.dumps(f, default=str)]
    assert not stray, f"a file under the sibling worktree was read: {stray}"


def a_breach_under_bin_reds_on_bin():
    repo = _repo_root_shape(BREACH)
    findings, _ = _encapsulation(repo, "bin")
    hits = [f for f in findings if "bin/tool.py" in json.dumps(f, default=str)]
    assert hits, f"the cross-device import in bin/tool.py did not red on row bin: {findings}"


def the_live_shape_still_takes_the_parent_of_cairn_and_still_reds_a_breach():
    tmp = scratch_dir("testing-repo-root-live-shape-")
    census = tmp / "cairn"
    _lay(tmp, _package("cairn/"))
    findings, seen = _encapsulation(census, "devices/a")
    want = str(tmp.resolve())
    assert set(seen) == {want}, f"import_sites read {sorted(set(seen))}, want only {want}"
    hits = [f for f in findings if "cairn/devices/a/a.py" in json.dumps(f, default=str)]
    assert hits, f"the cross-device import under <tmp>/cairn did not red: {findings}"


def main() -> int:
    print("a component at the repo root is judged against its repo alone (ticket 46a93ddcc122)")
    for name, fn in (("a_repo_root_component_reads_only_its_repo", a_repo_root_component_reads_only_its_repo),
                     ("a_breach_under_bin_reds_on_bin", a_breach_under_bin_reds_on_bin),
                     ("the_live_shape_still_takes_the_parent_of_cairn_and_still_reds_a_breach",
                      the_live_shape_still_takes_the_parent_of_cairn_and_still_reds_a_breach)):
        _tooth(name, fn)
    print(f"{'GREEN' if not FAIL else 'RED'} — {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

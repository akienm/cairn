"""Proof for ticket 82d203c11015: component_of over many paths walks component_dirs once.

MEASURED 2026-11-12: the home bus wedged at 100% of one core (py-spy, pid 1881010) in
validation_store calling address.component_of once per closure file. Each call re-walks
component_dirs (77 components, 6.5 ms), about 8.5 ms a call; 2.66 s over 300 repo files.

  1. test_components_of_agrees_with_component_of: for every sampled path, components_of
     answers exactly what component_of answers, None included for a path under no component;
  2. test_components_of_walks_component_dirs_once: over 40 paths, component_dirs is called
     exactly once.

The paths are a sample of ``git ls-files cairn``, plus one under the scratch root, which no
component owns. The count replaces ``address.component_dirs`` with a counting wrapper for
the call and restores it after.

    bin/cairn test cairn/tools/base/proofs/test_components_of_walks_once.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"82d203c11015": {
    "1": "test_components_of_agrees_with_component_of",
    "2": "test_components_of_walks_component_dirs_once",
}}


def _sample(n: int) -> list[str]:
    files = subprocess.run(["git", "ls-files", "cairn"], cwd=str(_REPO),
                           capture_output=True, text=True, check=True).stdout.split()
    step = max(1, len(files) // n)
    return [str(_REPO / f) for f in files[::step][:n]]


def _outside() -> str:
    from cairn.tools.scratch.scratch import scratch_dir
    return str(scratch_dir("testing-82d203c11015-outside-") / "nobody-owns-me.py")


def test_components_of_agrees_with_component_of():
    from cairn.tools.base import address
    paths = _sample(40) + [_outside()]
    got = address.components_of(paths)
    want = {p: address.component_of(p) for p in paths}
    wrong = {p: (got.get(p), want[p]) for p in paths if got.get(p) != want[p]}
    assert set(got) == set(paths), f"components_of keys differ from the paths given: {sorted(set(got) ^ set(paths))[:5]}"
    assert not wrong, f"components_of disagrees with component_of (got, want): {list(wrong.items())[:5]}"
    assert want[paths[-1]] is None and got[paths[-1]] is None, "the outside path must have no owner"
    assert sum(v is not None for v in got.values()) >= 30, f"too few owned paths to mean anything: {got}"


def test_components_of_walks_component_dirs_once():
    from cairn.tools.base import address
    calls = []
    real = address.component_dirs

    def counting(*a, **k):
        calls.append(1)
        return real(*a, **k)

    address.component_dirs = counting
    try:
        address.components_of(_sample(40))
    finally:
        address.component_dirs = real
    assert len(calls) == 1, f"components_of over 40 paths walked component_dirs {len(calls)} times"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

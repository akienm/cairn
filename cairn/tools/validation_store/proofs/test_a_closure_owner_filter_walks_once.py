"""Proof for ticket 9f4442c932da: a seal's closure owner filter walks the component tree once.

MEASURED 2026-11-12: the home bus wedged at 100% of one core (py-spy, pid 1881010) in
``_owned_by_the_proofs_component``, which asked ``address.component_of`` once per closure file;
each call re-walks ``component_dirs``. 2.66 s over 300 files on akienasus.

  1. test_the_filter_walks_component_dirs_once: over 40 closure paths, address.component_dirs
     is called exactly once;
  2. test_the_filter_answers_as_before: the answer equals the per-path filter computed here:
     the proof's own file, and each other rel whose component_of is the proof's owner.

The closure is the proof itself plus a fixed-size sample of ``git ls-files cairn``: five of its
own component's files and forty that other components own (an invariant of the sample, not a
floor over the live tree; reshaped 2026-11-13 after a stride sample read 39 on Linux). This proof measures only cairn/tools/validation_store.

    bin/cairn test cairn/tools/validation_store/proofs/test_a_closure_owner_filter_walks_once.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"9f4442c932da": {
    "1": "test_the_filter_walks_component_dirs_once",
    "2": "test_the_filter_answers_as_before",
}}

_PROOF = "cairn/tools/validation_store/proofs/test_a_closure_owner_filter_walks_once.py"


_FOREIGN, _OWN = 40, 5


def _rels() -> set:
    """A closure of a FIXED size: the proof, _OWN of its component's files and _FOREIGN files
    other components own, spread across the tree. Sized by count, never by a stride over the
    live tree: a stride's sample shrank to 39 on akiendelllinux with no build at all (measured
    2026-11-13), and a floor over a snapshot reds on the tree moving, not on the filter."""
    files = subprocess.run(["git", "ls-files", "cairn"], cwd=str(_REPO),
                           capture_output=True, text=True, check=True).stdout.split()
    home = "cairn/tools/validation_store/"
    own = [f for f in files if f.startswith(home) and f.endswith(".py") and f != _PROOF]
    foreign = [f for f in files if not f.startswith(home)]
    assert len(own) >= _OWN and len(foreign) >= _FOREIGN, \
        f"the tree is too small to sample: own={len(own)} foreign={len(foreign)}"
    step = len(foreign) // _FOREIGN
    return set(foreign[::step][:_FOREIGN]) | set(own[:_OWN]) | {_PROOF}


def test_the_filter_walks_component_dirs_once():
    from cairn.tools.base import address
    from cairn.tools.validation_store import validation_store as V
    rels = _rels()
    calls = []
    real = address.component_dirs

    def counting(*a, **k):
        calls.append(1)
        return real(*a, **k)

    address.component_dirs = counting
    try:
        V._owned_by_the_proofs_component(rels, str(_REPO / _PROOF))
    finally:
        address.component_dirs = real
    assert len(rels) == 1 + _OWN + _FOREIGN, f"the fixed closure lost members: {len(rels)}"
    assert len(calls) == 1, f"filtering {len(rels)} closure paths walked component_dirs {len(calls)} times"


def test_the_filter_answers_as_before():
    from cairn.tools.base.address import component_of
    from cairn.tools.validation_store import validation_store as V
    rels = _rels()
    owner = component_of(_REPO / _PROOF)
    want = {_PROOF} | {r for r in rels - {_PROOF} if component_of(_REPO / r) == owner}
    got = V._owned_by_the_proofs_component(rels, str(_REPO / _PROOF))
    assert got == want, f"the filter changed its answer: extra {sorted(got - want)}, missing {sorted(want - got)}"
    assert len(want) > 1 and len(want) < len(rels), f"the sample must hold own and foreign files: {sorted(want)}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

"""Proof that a proof run through the tester imports from its own directory, whatever the caller's cwd.

Measured 2026-11-13 on Windows: ``run_proof`` launches the proof as ``python -c <runner>``, which puts
the CALLER's cwd first on ``sys.path`` (as ``''``). With isolation ``none`` no cwd is passed, so when
the caller stood in the live repo root the live ``cairn`` shadowed the worktree the tester had pinned
on PYTHONPATH, and a proof under revert imported the tree it was meant to be measured against.
Running a script puts the script's directory first; the runner must do the same.

Both teeth run ``run_proof`` for real, with the cwd set to somewhere that is not the proof's directory.

    python <this file>
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

PROVES = {
    "cfb4cb45d85c": {
        "1": "sys_path_zero_is_the_proofs_directory_when_the_caller_stands_in_the_live_root",
        "2": "a_module_beside_the_proof_beats_a_same_named_module_in_the_callers_cwd",
    },
}


def _run(probe: Path, cwd: Path) -> str:
    from cairn.devices.tester.device import TesterDevice
    here = os.getcwd()
    os.chdir(cwd)
    try:
        rec = TesterDevice().run_proof(probe, sink="none", caller="t", isolation="none")
    finally:
        os.chdir(here)
    return rec["evidence"]["stdout_tail"]


def test_sys_path_zero_is_the_proofs_directory_when_the_caller_stands_in_the_live_root():
    from cairn.tools.scratch.scratch import scratch_dir
    d = Path(scratch_dir("cairn-closure-first-"))
    probe = d / "_probe.py"
    probe.write_text("import sys\nprint('SP0=' + sys.path[0])\n", encoding="utf-8")
    out = _run(probe, REPO)
    got = next((l[4:] for l in out.splitlines() if l.startswith("SP0=")), None)
    assert got is not None, out
    assert os.path.normcase(os.path.realpath(got)) == os.path.normcase(os.path.realpath(str(d))), (got, str(d))


def test_a_module_beside_the_proof_beats_a_same_named_module_in_the_callers_cwd():
    from cairn.tools.scratch.scratch import scratch_dir
    proof_dir = Path(scratch_dir("cairn-closure-mine-"))
    decoy = Path(scratch_dir("cairn-closure-decoy-"))
    (proof_dir / "shadowed.py").write_text("WHO = 'beside-the-proof'\n", encoding="utf-8")
    (decoy / "shadowed.py").write_text("WHO = 'callers-cwd'\n", encoding="utf-8")
    probe = proof_dir / "_probe.py"
    probe.write_text("import shadowed\nprint('WHO=' + shadowed.WHO)\n", encoding="utf-8")
    out = _run(probe, decoy)
    assert "WHO=beside-the-proof" in out, out


def main() -> int:
    bad = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except Exception as e:  # noqa: BLE001
                bad += 1
                print(f"  FAIL {name}: {e}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

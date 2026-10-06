"""Proof that proofgate counts a ``$var`` script slot as a proof run only through its loop (66ae6f4a2c0e).

WHAT IT PROVES, and the reason is a measured over-wrap: on 2026-10-06 proofgate judged a ``$var``
in python's script slot by searching the WHOLE command for a proofs/ glob, so
``python3 $S/x.py; bin/cairn test <proof>`` and ``python3 $S/x.py <proof>`` were rewritten into
``cairn test --exec`` though neither runs a proof by python (n=3, the third a PROVEME crossing
that named its proof as an argument). Since 67af8b743a63 a ``cairn test --seal`` nested inside
``--exec`` is refused, so the over-wrap became a loud refusal. 72a37498c601's clause 6 is the rule
(a proof path as an argument is not a proof run); this is its ``$var`` branch.

Teeth, one per falsifier clause (PROVES below), each calling the gate's own ``judge()``:
  (1) A PROOF IN ANOTHER SEGMENT binds nothing: ``python3 $S/x.py; bin/cairn test <proof>`` is None.
  (2) A PROOF AS THE SCRIPT'S ARGUMENT binds nothing: ``python3 $S/x.py <proof>`` is None.
  (3) THE LOOP STILL BINDS: ``for p in <dir>/proofs/test_*.py; do python3 "$p"; done``, in both the
      ``$p`` and ``${p}`` spellings, is rewritten to ``<repo>/bin/cairn test --exec`` + the quoted
      original.

Nothing runs a proof: the commands are strings handed to ``judge()``.

    bin/cairn test bin/proofs/test_a_var_script_slot_runs_a_proof_only_through_its_loop.py
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import shlex
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GATE = _REPO_ROOT / "bin" / "cmd" / "proofgate"

PROVES = {"66ae6f4a2c0e": {
    "1": "test_a_proof_in_another_segment_binds_no_var",
    "2": "test_a_proof_as_the_scripts_argument_binds_no_var",
    "3": "test_the_loop_over_a_proofs_glob_still_binds",
}}

_HELD: list = []


def _gate():
    """The subject is an extensionless command, loaded by location as bin/cmd subjects are.
    Loaded fresh per process, so the hollow taking the build away reads as a red tooth."""
    assert _GATE.is_file(), f"no gate at {_GATE.relative_to(_REPO_ROOT)}"
    if not _HELD:
        spec = importlib.util.spec_from_loader(
            "proofgate", importlib.machinery.SourceFileLoader("proofgate", str(_GATE)))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _HELD.append(mod)
    return _HELD[0]


PROOF = "cairn/devices/tester/proofs/test_a.py"


def _wrapped(command: str) -> str:
    return f"{_REPO_ROOT}/bin/cairn test --exec {shlex.quote(command)}"


def test_a_proof_in_another_segment_binds_no_var():
    for c in (f"PYTHONPATH=. python3 $S/x.py; bin/cairn test {PROOF}",
              f"python3 ${{S}}/x.py && bin/cairn test --seal {PROOF}"):
        got = _gate().judge(c)
        assert got is None, f"{c!r}: a proof named in another segment made the $var a proof run: {got}"


def test_a_proof_as_the_scripts_argument_binds_no_var():
    for c in (f"python3 $S/x.py {PROOF}",
              f"PYTHONPATH=. python3 \"$S/cross.py\" 67af8b743a63 PROVEME cairn/devices/tester why {PROOF}"):
        got = _gate().judge(c)
        assert got is None, f"{c!r}: a proof handed to a $var script as its argument was judged a proof run: {got}"


def test_the_loop_over_a_proofs_glob_still_binds():
    for c in ('for p in cairn/devices/inference_domain/proofs/test_*.py; do python3 "$p"; done',
              'for p in cairn/devices/inference_domain/proofs/test_*.py; do python3 "${p}"; done'):
        got = (_gate().judge(c) or {}).get("command")
        assert got == _wrapped(c), f"{c!r}: the loop over a proofs glob must be rewritten under the seal, got {got!r}"


def test_the_whole_falsifier_holds_end_to_end():
    test_a_proof_in_another_segment_binds_no_var()
    test_a_proof_as_the_scripts_argument_binds_no_var()
    test_the_loop_over_a_proofs_glob_still_binds()


def _main() -> int:
    checks = [
        test_a_proof_in_another_segment_binds_no_var,
        test_a_proof_as_the_scripts_argument_binds_no_var,
        test_the_loop_over_a_proofs_glob_still_binds,
        test_the_whole_falsifier_holds_end_to_end,
    ]
    # EVERY TOOTH PRINTS, red ones too, so a red names which clause fell.
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except AssertionError as e:
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {e}")
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed")
        return 1
    print("green — proofgate: a $var script slot runs a proof only through the loop that binds it")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

"""Proof for tester/scratch — a proof's throwaway directory cannot survive the run.

The defect this seals was MEASURED, not imagined: on 2026-08-03 there were 3581 leaked
entries and 33M sitting in /tmp, from thirty-one temp-directory sites that each forgot
the same cleanup. Teeth a hollow door could not pass:

  - THE DIRECTORY IS GONE AFTER THE PROCESS EXITS. Measured from OUTSIDE, in a real
    subprocess, because that is the only place "after exit" exists. A check inside the
    same process can only observe the registration, never the removal.
  - NON-VACUITY: THE BARE CALL STILL LEAKS. The same subprocess using ``tempfile.mkdtemp``
    directly LEAVES its directory behind. If that ever stops being true, the tooth above
    is measuring the operating system, not this door, and this whole file is theatre.
  - A SWEEP THAT CANNOT SWEEP SAYS SO. An unremovable directory prints to stderr and does
    NOT take down the run. Silence here would reproduce the original defect exactly —
    invisible accumulation — with the added insult of a door that claims to have handled it.
  - NO PROOF REACHES THE SYSTEM TEMP DIRECTORY EXCEPT THROUGH THE DOOR. This is the tooth
    that makes the fix PHYSICS rather than a one-time cleanup (Law 4). Thirty-four sites
    were fixed by hand; the thirty-fifth is what this catches. Without it the leak returns
    the first time someone writes the obvious line, and nobody finds out for two months.

    python3 cairn/tester/proofs/test_scratch.py     # exit 0 = green
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

# Run a snippet in a FRESH interpreter that exits normally, so atexit actually fires.
# Its last stdout line is the path we then interrogate from out here, after it is dead.
_RUNNER = (
    "import sys; sys.path.insert(0, {repo!r})\n"
    "{body}\n"
)


def _in_a_dead_process(body: str) -> tuple[str, str]:
    """Run ``body`` to completion in its own interpreter. Returns (last stdout line, stderr)."""
    r = subprocess.run([sys.executable, "-c", _RUNNER.format(repo=str(REPO), body=body)],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"the fixture process itself failed: {r.returncode}\n{r.stderr}"
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    assert lines, f"the fixture process printed no path\nstderr: {r.stderr}"
    return lines[-1], r.stderr


def test_the_scratch_is_gone_once_the_process_is():
    body = ("from cairn.tester.scratch import scratch_dir\n"
            "d = scratch_dir('scratch-proof-gone-')\n"
            "(d / 'a_file').write_text('x')\n"          # non-empty: rmtree must be recursive
            "assert d.is_dir()\n"
            "print(d)\n")
    path, _ = _in_a_dead_process(body)
    assert not Path(path).exists(), \
        f"the door registered a sweep that never ran — {path} outlived its process"


def test_a_bare_mkdtemp_still_leaks_so_the_tooth_above_measures_something():
    body = ("import tempfile\n"
            "print(tempfile.mkdtemp(prefix='scratch-proof-vacuity-'))\n")
    path, _ = _in_a_dead_process(body)
    leaked = Path(path)
    assert leaked.exists(), (
        "a BARE mkdtemp no longer leaks — either the interpreter or the OS now cleans /tmp, "
        "and test_the_scratch_is_gone_once_the_process_is is therefore measuring nothing")
    leaked.rmdir()                              # this proof does not become the defect it seals


def test_a_sweep_that_cannot_sweep_is_loud_and_not_fatal():
    # Make the directory unremovable from inside: a child the sweep cannot unlink because
    # the parent it must unlink from is not writable. The run must still exit 0.
    body = ("import os\n"
            "from cairn.tester.scratch import scratch_dir\n"
            "d = scratch_dir('scratch-proof-stuck-')\n"
            "(d / 'child').mkdir()\n"
            "print(d)\n"
            "os.chmod(d, 0o500)\n")
    path, stderr = _in_a_dead_process(body)     # returncode 0 is asserted in the helper
    stuck = Path(path)
    assert "could not remove" in stderr, \
        f"a failed sweep said NOTHING — the leak would be invisible again. stderr: {stderr!r}"
    assert path in stderr, f"the complaint does not name the directory it is about: {stderr!r}"
    stuck.chmod(0o700)                          # leave the box as we found it
    (stuck / "child").rmdir()
    stuck.rmdir()


def test_no_proof_in_this_repo_calls_mkdtemp_bare():
    # THIS file is the one legitimate exception and says so out loud: the vacuity tooth
    # above MUST call mkdtemp bare, or it cannot show that bare still leaks. An exemption
    # that is a single named self-reference is not the exemption-roster pattern (a
    # mechanism built ahead of any entry) — it is the scanner declining to indict its own
    # control group.
    me = Path(__file__).resolve()
    offenders = []
    for py in sorted(REPO.rglob("proofs/test_*.py")):
        if "__pycache__" in py.parts or py.resolve() == me:
            continue
        for n, line in enumerate(py.read_text(errors="replace").splitlines(), 1):
            # gettempdir is here because the FIRST version of this tooth grepped only for
            # mkdtemp and missed a real leak of a different spelling — 18 boot-log FILES
            # from launchers/proofs/test_bootstrap.py, one per run. A tooth narrower than
            # its own defect is the hollow kind. Both reach the system temp dir; only the
            # door may. The three sites that named a deliberately-NONEXISTENT path came
            # through the door too, so there is no exemption to maintain and no judgement
            # call about which reach is harmless.
            if not line.lstrip().startswith("#") and ("mkdtemp" in line or "gettempdir" in line):
                offenders.append(f"{py.relative_to(REPO)}:{n}: {line.strip()}")
    assert not offenders, (
        "a proof reaches the system temp directory directly, so what it makes there outlives "
        "the run — exactly how 3581 of them accumulated. Use "
        "cairn.tester.scratch.scratch_dir:\n  " + "\n  ".join(offenders))


def _main() -> int:
    checks = [
        test_the_scratch_is_gone_once_the_process_is,
        test_a_bare_mkdtemp_still_leaks_so_the_tooth_above_measures_something,
        test_a_sweep_that_cannot_sweep_is_loud_and_not_fatal,
        test_no_proof_in_this_repo_calls_mkdtemp_bare,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — scratch: a proof's throwaway directory cannot outlive the run, "
          "and no proof in this repo can opt out of that")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

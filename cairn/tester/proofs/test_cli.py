"""Proof: `cairn test` reports the verdict it was given, seals nothing, and cannot go green over nothing.

The falsifier this proof grips (tickets/superclaude-starts-itself.json): "the verb can report
green without a proof having actually passed" — in three distinct shapes, because a runner has
three separate ways to lie and only one of them is 'says green when it means red':

  1. VERDICT DRIFT — green over a proof that exited non-zero.
  2. THE HOLLOW GREEN — green over ZERO proofs, because a path was typo'd and silently
     matched nothing. This is the dangerous one: it looks exactly like success (Law 8).
  3. SEALING — a dev command anyone types twenty times an hour writing entries into a
     record of truth. `run_proof` deliberately persists nothing and the standing-lesson
     gate is what seals; this verb must keep that split intact (Law 7).

It also asserts the thing that makes the verb worth having at all: a RED prints its evidence
in the FIRST run. A diagnostic that forces you to re-run to find out why has failed at its job,
and re-running to gather what the first report should have carried is re-derivation (Law 1).

Deliberately dependency-light: subprocess + tempfile + pathlib. Runs bare.

    python3 cairn/tester/proofs/test_cli.py     # exit 0 = green
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CAIRN = REPO / "bin" / "cairn"

GREEN_FIXTURE = "print('the fixture ran and is happy')\nraise SystemExit(0)\n"
# The red fixture prints a DISTINCTIVE token on the way down, so the test can prove the
# evidence actually travelled rather than merely that something was printed.
RED_FIXTURE = (
    "import sys\n"
    "print('fixture stdout: SENTINEL_STDOUT_9f3a')\n"
    "print('fixture stderr: SENTINEL_STDERR_9f3a', file=sys.stderr)\n"
    "raise SystemExit(3)\n"
)

_failures: list[str] = []


def _fixture_dir(tmp: Path, **proofs: str) -> Path:
    """Build <tmp>/proofs/test_*.py. The directory name matters: discovery globs
    '**/proofs/test_*.py', so a fixture outside a proofs/ dir would never be found and the
    test would pass for the wrong reason."""
    d = tmp / "proofs"
    d.mkdir(parents=True, exist_ok=True)
    for name, body in proofs.items():
        (d / f"test_{name}.py").write_text(body)
    return d


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(CAIRN), "test", *args], capture_output=True, text=True, timeout=300)


def check(name: str, fn) -> None:
    try:
        fn()
        print(f"  PASS  {name}")
    except AssertionError as exc:
        print(f"  FAIL  {name}: {exc}", file=sys.stderr)
        _failures.append(name)


def test_a_green_proof_reports_green_and_exits_zero() -> None:
    with tempfile.TemporaryDirectory() as t:
        d = _fixture_dir(Path(t), ok=GREEN_FIXTURE)
        r = _run(str(d / "test_ok.py"))
        assert r.returncode == 0, f"green fixture exited {r.returncode}: {r.stdout}{r.stderr}"
        assert "1 green" in r.stdout, f"summary did not count the green — {r.stdout!r}"
        assert "0 red" in r.stdout, f"summary invented a red — {r.stdout!r}"


def test_a_red_proof_reports_red_and_exits_nonzero() -> None:
    """The verdict is READ from the exit code, never granted. An always-green runner is a
    hollow build, so this is the case that kills one."""
    with tempfile.TemporaryDirectory() as t:
        d = _fixture_dir(Path(t), bad=RED_FIXTURE)
        r = _run(str(d / "test_bad.py"))
        assert r.returncode != 0, f"a proof that exited 3 was reported as success: {r.stdout!r}"
        assert "1 red" in r.stdout, f"summary did not count the red — {r.stdout!r}"
        assert "0 green" in r.stdout, f"summary invented a green — {r.stdout!r}"


def test_a_red_carries_its_evidence_in_the_first_run() -> None:
    with tempfile.TemporaryDirectory() as t:
        d = _fixture_dir(Path(t), bad=RED_FIXTURE)
        r = _run(str(d / "test_bad.py"))
        assert "SENTINEL_STDOUT_9f3a" in r.stdout, (
            "the failing proof's stdout did not reach the report — the reader must re-run to see why"
        )
        assert "SENTINEL_STDERR_9f3a" in r.stdout, (
            "the failing proof's stderr did not reach the report — the traceback is the whole point"
        )
        assert "exit 3" in r.stdout, f"the report does not name the exit code it read — {r.stdout!r}"


def test_the_run_seals_nothing() -> None:
    """A VALIDATION is a record of truth; this verb is a diagnostic surface. run_proof returns
    the eight fields and persists none of them — the standing-lesson gate is the write-door.
    If this verb ever starts sealing, that split is gone and so is Law 7's guarantee."""
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        d = _fixture_dir(tmp, ok=GREEN_FIXTURE)
        before = {p for p in tmp.rglob("*")}
        r = _run(str(d / "test_ok.py"))
        assert r.returncode == 0, f"fixture went red unexpectedly: {r.stdout}{r.stderr}"
        after = {p for p in tmp.rglob("*")}
        new = after - before
        assert not new, f"the run wrote files beside the proof it ran: {sorted(str(p) for p in new)}"
        assert not (tmp / "validations").exists(), "the verb minted a VALIDATION — it is not a sealing door"


def test_a_directory_expands_to_the_proofs_beneath_it() -> None:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        _fixture_dir(tmp, one=GREEN_FIXTURE, two=GREEN_FIXTURE)
        r = _run(str(tmp))
        assert r.returncode == 0, f"exited {r.returncode}: {r.stdout}{r.stderr}"
        assert "2 proofs" in r.stdout, f"discovery did not find both fixtures — {r.stdout!r}"


def test_a_typod_path_is_loud_and_never_a_green_over_nothing() -> None:
    """THE HOLLOW GREEN, killed. A runner that matched zero proofs and exited 0 would report
    success in the exact shape of real success — the most expensive possible lie, because
    nobody investigates a green."""
    r = _run("/no/such/path/at/all/test_nope.py")
    assert r.returncode != 0, (
        f"a nonexistent path exited 0 — that is a green over zero proofs: {r.stdout!r}"
    )
    combined = r.stdout + r.stderr
    assert "no such path" in combined, f"the miss was not reported — {combined!r}"


def test_the_verb_is_registered_with_the_dispatcher() -> None:
    """The whole point was that `cairn test` is the ADDRESS. If the dispatcher does not list
    it, the next session guesses again and the four tool calls come back."""
    r = subprocess.run([str(CAIRN)], capture_output=True, text=True, timeout=60)
    listed = r.stdout + r.stderr
    assert "test" in listed.split(), f"`cairn` does not list `test` among its verbs — {listed!r}"


def test_it_runs_from_a_cwd_that_is_not_the_repo() -> None:
    """The cwd accident, retired. Before the bootstrap this verb could only have worked from
    the repo root, because that is the only place `import cairn` resolved."""
    with tempfile.TemporaryDirectory() as t:
        d = _fixture_dir(Path(t), ok=GREEN_FIXTURE)
        r = subprocess.run([str(CAIRN), "test", str(d / "test_ok.py")],
                           capture_output=True, text=True, cwd="/", timeout=300)
        assert r.returncode == 0, f"running from / failed: {r.stdout}{r.stderr}"


def _main() -> int:
    print(f"proof: the `cairn test` verb — repo={REPO}")
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            check(name, fn)
    if _failures:
        print(f"\n{len(_failures)} FAILED: {', '.join(_failures)}", file=sys.stderr)
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

"""Proof for ticket 6437cfd935bb — the outside-readers census proof declares its own time limit.

Measured 2026-11-20 on akiendelllinux: test_a_census_names_every_outside_reader ran 137 s wall, and
a71b39b54 records its reseal at 133 s, past the reseal door's 120 s default budget, so a reseal that
touches artifact.py read it as a timeout. The budget is the proof's own byte (ticket 8383a32d20c5);
300 s is 2.2x the measured wall.

Reached through the tester's public interface only (RULE 1; ticket 4cc2775efeff), as cf32e6f141e0's
proof is: the declaration is read from the source by AST, the reading the tester does, and the run
goes through `cairn test`. A run's budget is not in a green record (only a TIMEOUT carries
timeout_s), so tooth 2 reads it by behaviour: a caller budget below the fixture's sleep, which
only a declared budget can outlast. The tester's rule does not depend on the caller's number, so a
2 s caller measures what a 120 s one would, without a two-minute sleep per run.

  1. the census proof declares a top-level PROOF_TIMEOUT_S = 300;
  2. a fixture carrying that declared value outlasts the caller's budget under `cairn test`;
     undeclared, or declared below its sleep, it does not.

    bin/cairn test cairn/tools/artifact/proofs/test_the_census_proof_declares_a_budget_above_its_wall.py
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROOF_TIMEOUT_S = 300

PROVES = {"6437cfd935bb": {
    "1": "test_the_census_proof_declares_300",
    "2": "test_a_declared_budget_outranks_the_callers",
}}

_SUBJECT = _REPO_ROOT / "cairn" / "tools" / "artifact" / "proofs" / "test_a_census_names_every_outside_reader.py"

# The caller's budget is set below the fixture's sleep, so only a budget the fixture declares lets it finish.
_CALLER_BUDGET_S = 2
_FIXTURE_SLEEP_S = 5


def _declared(path: Path) -> int | None:
    """A top-level PROOF_TIMEOUT_S integer literal, last assignment wins; None when absent."""
    value = None
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PROOF_TIMEOUT_S"
                                                for t in node.targets):
            value = node.value.value if isinstance(node.value, ast.Constant) else node.value
    return value


def _run_fixture(declared: int | None) -> tuple[int, str]:
    """`cairn test --timeout 2` over a fixture that sleeps 5 s; returns (exit, output)."""
    root = scratch_dir("cairn-6437-") / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    fixture = root / "proofs" / "test_fixture.py"
    head = f"PROOF_TIMEOUT_S = {declared}\n" if declared is not None else ""
    fixture.write_text(head + 'PROVES = {"aaaaaaaaaaaa": {"1": "test_fixture_tooth"}}\n'
                       f"import time\ntime.sleep({_FIXTURE_SLEEP_S})\nprint('ok   test_fixture_tooth')\n",
                       encoding="utf-8")
    r = subprocess.run([*bash_script_argv(_REPO_ROOT / "bin" / "cairn"), "test",
                        "--timeout", str(_CALLER_BUDGET_S), str(fixture)],
                       capture_output=True, text=True, timeout=120, cwd=str(_REPO_ROOT))
    return r.returncode, r.stdout + r.stderr


def _green(out: str) -> bool:
    return "1 green" in out and "0 red" in out


def test_the_census_proof_declares_300():
    got = _declared(_SUBJECT)
    assert got == 300, got


def test_a_declared_budget_outranks_the_callers():
    declared = _declared(_SUBJECT)
    assert declared, "the census proof declares no budget"
    rc, out = _run_fixture(declared)
    assert rc == 0 and _green(out), f"declaring {declared} did not outlast a {_CALLER_BUDGET_S} s caller: rc={rc} {out[-600:]}"
    # Controls, so the tooth can red: undeclared, the caller's budget holds; declared below the sleep,
    # the declared value is the budget.
    rc, out = _run_fixture(None)
    assert not _green(out), f"an undeclared fixture outlasted the caller's {_CALLER_BUDGET_S} s: rc={rc} {out[-600:]}"
    rc, out = _run_fixture(_FIXTURE_SLEEP_S - 2)
    assert not _green(out), f"a fixture declaring {_FIXTURE_SLEEP_S - 2} s ran past it: rc={rc} {out[-600:]}"


def main() -> int:
    fails = 0
    for name in PROVES["6437cfd935bb"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

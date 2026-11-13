"""An exec's bound reaches the proof it runs (ticket e6b25d61abc4).

Codemother's verdict runs a chart instrument as ``bin/cairn test --exec '<cmd>' --timeout
<timeout_s>``, so the chart's declared budget bounded only the exec envelope. The command
inside, ``bin/cairn test <proof>``, gave the proof the cli's 120 s default. Measured
2026-11-13: 8e73a9efa04a declared 300 s, and test_call_time_binding (56 s alone) timed out at
120 s under load. That red measured the box's load and a dropped declaration, not the code.

``run_exec`` now exports its bound as CAIRN_TESTER_PROOF_BUDGET, and the cli's default reads it.

  1. ``cairn test --exec 'printenv CAIRN_TESTER_PROOF_BUDGET' --timeout 300`` prints 300;
  2. a fixture proof sleeping 8 s, run under CAIRN_TESTER_PROOF_BUDGET=3 with no --timeout,
     reports the 3 s budget exceeded;
  3. an explicit --timeout beats the env bound, a proof's PROOF_TIMEOUT_S beats it too, and
     with no env var (or an unusable one) the default stays 120.

Every run sets the env var explicitly, or strips it: when this proof is itself run under an
exec, it inherits the outer bound.

    python3 cairn/devices/tester/proofs/test_an_exec_bound_reaches_the_proof_it_runs.py   # exit 0 = green
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROOF_TIMEOUT_S = 300

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"e6b25d61abc4": {
    "1": "test_the_exec_exports_its_bound",
    "2": "test_a_proof_under_the_bound_runs_at_it",
    "3": "test_explicit_limits_still_win_and_the_default_stands",
}}

_CAIRN = _REPO_ROOT / "bin" / "cairn"
_VAR = "CAIRN_TESTER_PROOF_BUDGET"


def _fixture(prefix: str, sleep_s: int, header: str = "") -> Path:
    proofs = scratch_dir(prefix) / "fixture_component" / "proofs"
    proofs.mkdir(parents=True)
    proof = proofs / "test_fixture.py"
    proof.write_text((header + "\n" if header else "")
                     + 'import time\nPROVES = {"aaaaaaaaaaaa": {"1": "test_fixture_tooth"}}\n'
                     + f"time.sleep({sleep_s})\nprint('ok   test_fixture_tooth')\n")
    return proof


def _cairn_test(*argv: str, budget: str | None, timeout: int = 240) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != _VAR}
    if budget is not None:
        env[_VAR] = budget
    return subprocess.run([*bash_script_argv(_CAIRN), "test", *argv], capture_output=True,
                          text=True, timeout=timeout, cwd=str(_REPO_ROOT), env=env)


def test_the_exec_exports_its_bound():
    r = _cairn_test("--exec", f"printenv {_VAR}", "--timeout", "300", budget=None)
    assert r.stdout.strip() == "300", \
        f"the exec's bound did not reach its command: exit {r.returncode}, stdout {r.stdout!r}, " \
        f"stderr {r.stderr[-300:]!r}"


def test_a_proof_under_the_bound_runs_at_it():
    proof = _fixture("cairn-e6b2-2-", 8)
    r = _cairn_test(str(proof), budget="3")
    out = r.stdout + r.stderr
    assert "exceeded the 3s budget" in out, \
        f"a proof under a 3 s bound did not run at it: exit {r.returncode}, {out[-500:]!r}"


def test_explicit_limits_still_win_and_the_default_stands():
    faults = []
    r = _cairn_test(str(_fixture("cairn-e6b2-3a-", 8)), "--timeout", "3", budget="300")
    if "exceeded the 3s budget" not in r.stdout + r.stderr:
        faults.append(f"--timeout 3 under a 300 s bound: {(r.stdout + r.stderr)[-300:]!r}")
    r = _cairn_test(str(_fixture("cairn-e6b2-3b-", 5, "PROOF_TIMEOUT_S = 30")), budget="3")
    if r.returncode != 0 or "TIMEOUT" in r.stdout + r.stderr:
        faults.append(f"PROOF_TIMEOUT_S = 30 under a 3 s bound: exit {r.returncode}, "
                      f"{(r.stdout + r.stderr)[-300:]!r}")
    r = _cairn_test(str(_fixture("cairn-e6b2-3c-", 1)), budget="x")
    if r.returncode != 0:
        faults.append(f"an unusable bound 'x' over a 1 s proof: exit {r.returncode}, "
                      f"{(r.stdout + r.stderr)[-300:]!r}")
    from cairn.devices.tester import cli
    reader = getattr(cli, "default_proof_budget", None)
    if reader is None:
        faults.append("cli has no default_proof_budget: the default cannot be read")
    else:
        for env, want in (({}, 120), ({_VAR: "x"}, 120), ({_VAR: "0"}, 120), ({_VAR: "-5"}, 120),
                          ({_VAR: "300"}, 300)):
            got = reader(env)
            if got != want:
                faults.append(f"default_proof_budget({env}) = {got}, not {want}")
    assert not faults, "\n".join(faults)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

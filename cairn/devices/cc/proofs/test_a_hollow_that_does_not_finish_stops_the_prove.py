"""Proof for ticket ae531c6b49db — a hollow that does not finish stops prove.sh loudly.

Measured 2026-11-21: cdfc928cc5ff's hollow ran under prove.sh's `timeout 1500 bin/cairn test --hollow ...
| tail -4`, was killed at 25 min having printed nothing, and prove.sh exited 0 — the pipe's status is
tail's — so the walk went on to a verdict and close refused later on hollow_evidence_absent. Each tooth
runs prove.sh's hollow step as written (from its `--- hollow` line to the end of the script) in a scratch
house whose bin/cairn is a stub, with a recording `timeout` first on PATH; the steps before it (reflection,
seal, commits, PROVEME) are not run, as the sibling cc proofs run one line of the script alone.

    python3 cairn/devices/cc/proofs/test_a_hollow_that_does_not_finish_stops_the_prove.py
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROVE = HERE.parent / "scripts" / "prove.sh"
_BASH = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"  # ticket f2a3b90c2931

PROVES = {"ae531c6b49db": {
    "1": "test_a_hollow_that_exits_nonzero_stops_the_prove_with_exit_6",
    "2": "test_a_hollow_that_finishes_passes_its_last_lines_and_exits_0",
    "3": "test_the_prove_puts_no_wall_clock_bound_on_the_hollow",
}}

ID = "aaaaaaaaaaaa"
STUB_CAIRN = """#!/bin/bash
echo "$*" >> "$PROOF_CAIRN_LOG"
for i in 1 2 3 4 5 6; do echo "hollow line $i"; done
exit "$PROOF_STUB_EXIT"
"""
STUB_TIMEOUT = """#!/bin/bash
echo "$*" >> "$PROOF_TIMEOUT_LOG"
shift
exec "$@"
"""


def _hollow_step() -> str:
    """prove.sh from its hollow step to the end, as written."""
    text = PROVE.read_text(encoding="utf-8")
    at = text.find('echo "--- hollow"')
    assert at >= 0, "prove.sh has no '--- hollow' step"
    return text[at:]


def _exe(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _run(stub_exit: int) -> tuple[int, str, list[str], list[str]]:
    """(exit status, output, timeout calls, cairn calls) of the hollow step over a stub hollow."""
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        house, shims = tmp / "cairn", tmp / "shims"
        _exe(house / "bin" / "cairn", STUB_CAIRN)
        _exe(shims / "timeout", STUB_TIMEOUT)
        tlog, clog = tmp / "timeout.log", tmp / "cairn.log"
        env = {**os.environ, "PATH": f"{shims}{os.pathsep}{os.environ.get('PATH', '')}",
               "PROOF_STUB_EXIT": str(stub_exit), "PROOF_TIMEOUT_LOG": str(tlog),
               "PROOF_CAIRN_LOG": str(clog)}
        prog = f"set -u\nID={ID}\ncd {house.as_posix()}\n" + _hollow_step()
        r = subprocess.run([_BASH, "-c", prog], env=env, capture_output=True, text=True, timeout=120)
        read = lambda p: p.read_text(encoding="utf-8").splitlines() if p.is_file() else []  # noqa: E731
        return r.returncode, r.stdout + r.stderr, read(tlog), read(clog)


def test_a_hollow_that_exits_nonzero_stops_the_prove_with_exit_6():
    code, out, _, calls = _run(124)
    assert calls, f"the hollow step never ran bin/cairn: {out!r}"
    assert code == 6, f"a hollow exiting 124 left prove.sh at exit {code}, not 6: {out!r}"
    assert "HOLLOW DID NOT FINISH" in out and "124" in out, f"no 'HOLLOW DID NOT FINISH (exit 124)' line: {out!r}"
    print("a hollow exiting 124 stops prove.sh with exit 6 and 'HOLLOW DID NOT FINISH (exit 124)'")


def test_a_hollow_that_finishes_passes_its_last_lines_and_exits_0():
    code, out, _, calls = _run(0)
    assert calls, f"the hollow step never ran bin/cairn: {out!r}"
    assert code == 0, f"a hollow exiting 0 left prove.sh at exit {code}: {out!r}"
    assert "hollow line 6" in out and "hollow line 1" not in out, f"not the hollow's last lines: {out!r}"
    assert "HOLLOW DID NOT FINISH" not in out, f"a finished hollow was called unfinished: {out!r}"
    print("a hollow exiting 0 leaves prove.sh at exit 0, showing the hollow's last lines")


def test_the_prove_puts_no_wall_clock_bound_on_the_hollow():
    _, out, timed, calls = _run(0)
    assert any("--hollow" in c for c in calls), f"the hollow step never ran the hollow verb: {calls} {out!r}"
    bounded = [c for c in timed if "--hollow" in c]
    assert not bounded, f"prove.sh bounds the hollow with timeout: {bounded}"
    print("no timeout invocation carries --hollow; the verb's own per-run bound is the only one")


def main() -> int:
    bad = 0
    for t in (test_a_hollow_that_exits_nonzero_stops_the_prove_with_exit_6,
              test_a_hollow_that_finishes_passes_its_last_lines_and_exits_0,
              test_the_prove_puts_no_wall_clock_bound_on_the_hollow):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            bad += 1
            print(f"  FAIL  {t.__name__}\n        {type(exc).__name__}: {str(exc)[:400]}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

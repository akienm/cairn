"""Proof for ticket 7c76b7c95433 — a raised trouble carries its call stack.

Akien, 2026-09-24 (open-f998fae25b35): "a trouble should have it's diagnostic info too, so the
call stack will be in there. if not, we make it so." Measured at the cast: 0 of 249 raises
carried a stack.

Teeth (each raises through a ModuleRaiser under a SCRATCH instance root; nothing reaches the
live lane):
  1. a_raise_carries_its_stack — the raise record's values.detail.stack is a non-empty list of
     str whose last entry names this file and the line of the raise_trouble call;
  2. the_callers_detail_is_untouched — the dict handed in is unchanged after the call;
  3. a_clear_carries_no_stack — a clear_trouble record's values carry no 'stack'.

    python3 cairn/tools/base/proofs/test_a_raised_trouble_carries_its_call_stack.py
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"7c76b7c95433": {
    "1": "test_a_raise_carries_its_stack",
    "2": "test_the_callers_detail_is_untouched",
    "3": "test_a_clear_carries_no_stack",
}}


def _raiser():
    from cairn.tools.base.diagnostic import ModuleRaiser
    from cairn.tools.scratch.scratch import scratch_dir
    return ModuleRaiser("testing-stack",
                        roots={"instance": scratch_dir("testing-7c76b7c95433-stack-")})


def _gate(r, gate: str) -> list[dict]:
    return [x for x in r.diagnostic_records() if x.get("gate") == gate]


def test_a_raise_carries_its_stack():
    r = _raiser()
    line = inspect.currentframe().f_lineno + 1
    r.raise_trouble("testing-stack", why="w", detail={"k": 1})
    raised = _gate(r, "raise_trouble")
    assert len(raised) == 1, f"expected one raise record, got {len(raised)}"
    stack = raised[0]["values"]["detail"].get("stack")
    assert isinstance(stack, list) and stack and all(isinstance(s, str) for s in stack), (
        f"detail.stack is not a non-empty list of str: {stack!r}")
    last = stack[-1]
    assert Path(__file__).name in last and f"line {line}" in last, (
        f"the innermost frame does not name the raise at line {line}: {last!r}")


def test_the_callers_detail_is_untouched():
    r = _raiser()
    d = {"k": 1}
    r.raise_trouble("testing-stack", why="w", detail=d)
    assert d == {"k": 1}, f"the caller's detail was mutated: {d!r}"


def test_a_clear_carries_no_stack():
    r = _raiser()
    r.raise_trouble("testing-stack", why="w")
    r.clear_trouble("testing-stack", by="cc", what_changed="x")
    cleared = _gate(r, "clear_trouble")
    assert len(cleared) == 1, f"expected one clear record, got {len(cleared)}"
    assert "stack" not in cleared[0]["values"], f"a clear carries a stack: {cleared[0]['values']!r}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

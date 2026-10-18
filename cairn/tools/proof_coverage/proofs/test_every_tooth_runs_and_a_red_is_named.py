"""Teeth for ticket 280e6daa198e — every tooth runs, and a red prints its name.

Charter: cairn/tools/proof_coverage/intention+why.json
Ticket:  CairnCommons/tickets/280e6daa198e-test-inference-domain-stops-at-the-first-raise-and-prints-no-teeth-behind-it.json

Run: python3 cairn/tools/proof_coverage/proofs/test_every_tooth_runs_and_a_red_is_named.py

A runner that stops at the first raise prints nothing for the teeth behind it, and
``teeth_printed`` cannot tell "this tooth failed" from "this tooth never ran" (measured
in test_the_agent_retry_probe_judges.py's docstring: '1 proof(s) printed no teeth at all').
``run_teeth`` is the per-tooth runner, beside the reader of what it prints, so a proof
with a plain list of checks gets the legible shape by calling one function
(open-4122fee9293a, answered: "the gate stays hard").

RESOLVED AT CALL TIME: a hollow reading reverts proof_coverage.py to a world without
``run_teeth``, and a proof that died importing it would print no teeth at all.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

import cairn.tools.proof_coverage.proof_coverage as pc  # noqa: E402

PROVES = {
    "280e6daa198e": {
        "all": "test_a_broken_first_tooth_leaves_the_rest_named",
    },
}


def _broken():
    raise AssertionError("deliberately broken")


def _second():
    pass


def _third():
    pass


_broken.__name__ = "test_broken_first"
_second.__name__ = "test_second"
_third.__name__ = "test_third"


def _run(checks):
    """Run ``checks`` through the tool's runner and return (exit, stdout) — captured, so the
    fixture teeth never print into this proof's own stream and get read as its teeth."""
    run_teeth = getattr(pc, "run_teeth", None)
    assert run_teeth is not None, "proof_coverage carries no run_teeth"
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = run_teeth(checks)
    return code, out.getvalue()


def test_a_broken_first_tooth_leaves_the_rest_named():
    code, out = _run([_broken, _second, _third])
    read = pc.teeth_printed(out)
    assert read["red"] == ["test_broken_first"], "the broken tooth is not read red by name: " + out
    assert read["green"] == ["test_second", "test_third"], \
        "the teeth behind the first red did not print by name: " + out
    assert "AssertionError: deliberately broken" in out, "the FAIL line does not carry the raise"
    assert code != 0, "a run with a red tooth exited 0"


def test_an_all_green_run_returns_zero():
    code, out = _run([_second, _third])
    assert code == 0, out
    assert pc.teeth_printed(out) == {"green": ["test_second", "test_third"], "red": []}, out


def test_a_crash_that_is_not_an_assertion_is_a_red_too():
    def _crash():
        raise KeyError("missing")
    _crash.__name__ = "test_crash"
    code, out = _run([_crash, _second])
    assert pc.teeth_printed(out)["red"] == ["test_crash"], out
    assert "test_second" in pc.teeth_printed(out)["green"], out
    assert code != 0


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))

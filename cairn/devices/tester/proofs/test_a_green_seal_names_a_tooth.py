"""A green seal names at least one tooth — the tester refuses to mint one that does not.

Ticket 77f15efd5a96. Measured 2026-09-15: 31 of 224 green seals in the corpus carried
``teeth_green: []`` — proofs that exit 0 having named nothing (no ``__main__`` block, a
pytest subprocess whose ``-v`` trailer defeats the reader, an aggregate ``7/7 green``).
Each read green to every reader and had proved nothing anyone could name. ``run_proof``
now seals such a run RED with ``zero teeth printed`` in ``evidence.stderr_tail`` — inside
the ratified eight fields, no ninth.

Both teeth run the REAL tester through the REAL door over fixture proofs under a scratch
root (``sink="none"``: the comparison is about the reading, not the store). A canned
string would prove only that a parser works on strings I wrote.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.device import TesterDevice  # noqa: E402
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "77f15efd5a96": {
        "1": ["test_an_exit_zero_run_that_names_no_tooth_seals_red"],
        "2": ["test_an_exit_zero_run_that_names_one_tooth_seals_green_naming_it"],
    },
}


def _fixture(name: str, body: str) -> Path:
    d = scratch_dir("green-seal-names-a-tooth-")
    p = d / name
    p.write_text(body, encoding="utf-8")
    return p


def test_an_exit_zero_run_that_names_no_tooth_seals_red():
    """THE CATCH. ``raise SystemExit(0)`` and nothing on stdout was a green seal until today."""
    proof = _fixture("test_silent_exit_zero.py", "raise SystemExit(0)\n")
    record = TesterDevice().run_proof(proof, sink="none", caller="77f15efd5a96 clause 1",
                                      isolation="none")
    ev = record["evidence"]
    assert record["verdict"] == "red", record
    assert ev["returncode"] == 0, ev          # the exit code is still recorded as it was
    assert ev["teeth_green"] == [] and ev["teeth_red"] == [], ev
    assert "zero teeth printed" in ev["stderr_tail"], ev["stderr_tail"]
    assert set(record) == {"claim", "caller", "date", "method", "verdict", "evidence",
                           "falsifier", "horizon"}, (
        "the detail rides an existing evidence field — the eight are ratified", sorted(record))
    assert "zero teeth printed" not in ev["stdout_tail"], ev  # the subject did not say it


def test_an_exit_zero_run_that_names_one_tooth_seals_green_naming_it():
    """The other side of the same branch: one named tooth is enough, and it is recorded."""
    proof = _fixture("test_one_tooth.py", "print('  ok   test_x')\nraise SystemExit(0)\n")
    record = TesterDevice().run_proof(proof, sink="none", caller="77f15efd5a96 clause 1",
                                      isolation="none")
    ev = record["evidence"]
    assert record["verdict"] == "green", record
    assert ev["teeth_green"] == ["test_x"], ev
    assert "zero teeth printed" not in ev["stderr_tail"], ev


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))

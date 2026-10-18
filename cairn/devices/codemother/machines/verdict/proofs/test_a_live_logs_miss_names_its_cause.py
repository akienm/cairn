"""A RE-RUN THAT CANNOT FIND THE LIVE LOGS SAYS SO — ticket 87ea3fb1058c.

WHAT WAS WRONG. The verdict door re-runs each criterion's instrument inside the tester's
sealed exec, and that exec leaves ~/.cairn/logs empty by design (68cef2ddd8ef). An instrument
that reads live logs fails there and passes when run by hand, and the refusal the builder got
was the bare traceback in the output tail (trouble verdict-door-sandbox-hides-live-logs,
measured by BUILDER 2026-10-13 sailing ea4a6151300f). The cause was in nobody's words.

WHAT THESE TEETH SETTLE. A contradicted pass whose tail cannot find a file under the live logs
tree carries a cause line naming the path and the seal (1). A disagreement for any other reason
carries no such line (2), and neither does a missing file outside that tree (3), so the line is
evidence of the seal and never a stock sentence.

NO FORK. ``observe_instruments`` takes its runner as an argument, so the reasoning is watched
against a substitute; the sealed exec itself is not what is under test.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.codemother.machines.verdict.verdict import (  # noqa: E402
    VerdictRefused, observe_instruments, validate_verdict)
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "87ea3fb1058c": {
        "1": "test_a_live_logs_miss_names_its_cause",
        "2": "test_an_ordinary_disagreement_names_no_seal_cause",
        "3": "test_a_missing_file_outside_the_logs_tree_names_no_seal_cause",
    },
}

_CLAIM = "the live tickets dir holds this run's ticket"
_LOGS_MISS = ("Traceback (most recent call last):\n  File \"<string>\", line 1\n"
              "FileNotFoundError: [Errno 2] No such file or directory: "
              "'/home/someone/.cairn/logs/inference_domain/0/tickets'")


def _world():
    """A filed ticket and a claiming chain of one criterion — the smallest the door reads."""
    tmp = str(scratch_dir("live_logs_miss_"))
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    tickets = os.path.join(tmp, "CairnCommons", "tickets")
    os.makedirs(tickets)
    with open(os.path.join(tickets, "sworn.json"), "w") as fh:
        fh.write("{}")
    packets = os.path.join(tmp, "berths", "0", "packets")
    os.makedirs(packets)
    hyp = os.path.join(packets, "hypothesize-20261018T000000-feedfeedfeed.json")
    with open(hyp, "w") as fh:
        json.dump({"hypotheses": [{"piece": "read the live tickets", "expect": "a ticket is there",
                                   "falsifier": "none is", "instrument": "true"}]}, fh)
    val = os.path.join(packets, "validate-20261018T000001-cafecafecafe.json")
    with open(val, "w") as fh:
        json.dump({"ticket": "sworn", "hypothesize_ref": hyp,
                   "criteria": [{"claim": _CLAIM, "instrument": "true",
                                 "covers": ["read the live tickets"]}]}, fh)
    artifact = {
        "ticket": "sworn", "validate_ref": val,
        "verdicts": [{"claim": _CLAIM, "instrument": "true", "outcome": "pass",
                      "evidence": "exit 0", "discriminating_observation": "emptied it; exit 1"}],
        "dispositions": [{"piece": "read the live tickets", "expect": "a ticket is there",
                          "disposition": "confirmed", "by": "exit 0"}],
    }
    return root, artifact


def _refusal_for(tail: str) -> str:
    root, artifact = _world()

    def runner(command, *, timeout_s=600, cwd=None):
        return {"command": command, "exit": 1, "timed_out": False,
                "timeout_s": timeout_s, "seconds": 0.0, "tail": tail}

    try:
        validate_verdict(artifact, root=root,
                         observations=observe_instruments(artifact, root, runner=runner))
    except VerdictRefused as err:
        assert "reports pass" in str(err), str(err)
        return str(err)
    raise AssertionError("a contradicted pass was not refused")


def test_a_live_logs_miss_names_its_cause():
    err = _refusal_for(_LOGS_MISS)
    assert "live logs tree" in err, "the refusal does not name the seal's empty logs tree: " + err
    assert "/home/someone/.cairn/logs/inference_domain/0/tickets" in err, \
        "the cause line does not carry the path the instrument could not find"


def test_an_ordinary_disagreement_names_no_seal_cause():
    err = _refusal_for("3 hits, not 0")
    assert "3 hits, not 0" in err
    assert "live logs tree" not in err


def test_a_missing_file_outside_the_logs_tree_names_no_seal_cause():
    err = _refusal_for("FileNotFoundError: [Errno 2] No such file or directory: '/tmp/x/notes.txt'")
    assert "live logs tree" not in err


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))

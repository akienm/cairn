"""PROOF for ticket 5cef97f01c79: a door write that journals mid-pass is not named after the run.

Measured 2026-11-18 21:26:44: artifactgate's after-run pass (ticket 7989bb520e14) named a ticket's
state.json during a read-only command. The write was the door's, and the journal matched the disk
seconds later: the pass had read between the door's bytes and its journal append.

  1. a record unjournaled when the pass starts, which the door writes and journals 0.2 s into the
     pass, is not named (the door skips an unchanged write, so the late write carries new bytes)
  2. a record written by hand and never journaled is still named after the settle
  3. the gate declares SETTLE_S == 0.5 and REREADS == 2, the ticket's hypothesis

The gate is loaded in-process and the door pointed at a scratch world (set_diagnostic_roots).

    bin/cairn test --seal bin/proofs/test_a_door_write_journaled_mid_pass_is_not_named.py
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "bin" / "cmd" / "artifactgate"
sys.path.insert(0, str(REPO))

PROVES = {"5cef97f01c79": {
    "1": "test_a_door_write_journaled_mid_pass_is_not_named",
    "2": "test_a_hand_write_never_journaled_is_still_named",
    "3": "test_the_settle_is_the_tickets_hypothesis",
}}

RECORD = "troubles/a-scratch-trouble.json"


def _gate():
    """The gate as a module, bound at call time (the hollow reading takes the build away)."""
    loader = importlib.machinery.SourceFileLoader("artifactgate_under_proof", str(GATE))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def _world(tmp: Path):
    """Two scratch git roots, the door pointed at them; returns (gate, door, record path)."""
    from cairn.tools.artifact import artifact as door
    roots = {}
    for name in ("cairn", "CairnCommons"):
        r = tmp / name
        (r / "troubles").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(r)], check=True)
        roots[name] = r
    door.set_diagnostic_roots(roots)
    return _gate(), door, roots["CairnCommons"] / RECORD


def _body(n: int) -> str:
    return json.dumps({"x": n}, indent=2) + "\n"


def test_a_door_write_journaled_mid_pass_is_not_named(tmp_path):
    gate, door, target = _world(tmp_path)
    try:
        target.write_text(_body(1))       # unjournaled bytes on disk as the pass starts
        late = threading.Timer(0.2, lambda: door.write(target, _body(2), verb="cast", why="proof 5cef97f01c79"))
        late.start()
        try:
            said = gate.after_run("Bash")
        finally:
            late.join()
        assert said is None, f"a door write that journaled 0.2 s into the pass was named:\n{said}"
    finally:
        door.set_diagnostic_roots(None)


def test_a_hand_write_never_journaled_is_still_named(tmp_path):
    gate, door, target = _world(tmp_path)
    try:
        target.write_text(_body(2))
        t0 = time.monotonic()
        said = gate.after_run("Bash")
        took = time.monotonic() - t0
        assert said is not None and str(target) in said, f"an unjournaled hand write was not named: {said!r}"
        assert took < 5, f"the pass took {took:.1f} s; the hook's timeout is 10 s"
    finally:
        door.set_diagnostic_roots(None)


def test_the_settle_is_the_tickets_hypothesis():
    gate = _gate()
    got = (getattr(gate, "SETTLE_S", None), getattr(gate, "REREADS", None))
    assert got == (0.5, 2), f"artifactgate declares (SETTLE_S, REREADS) = {got}, the ticket names (0.5, 2)"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))

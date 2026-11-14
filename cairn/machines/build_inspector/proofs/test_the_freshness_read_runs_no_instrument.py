"""Proof for ticket 6ebec06794ac, clause 5, on the side where the read runs: the PROVED gate's
freshness read (proved_answers_the_chart) runs no instrument and reaches no tree.

Since ticket 0c2c3f53c2be, code outside codemother asks this judge over the bus, and the judge
runs in CodeMother's bus process. A spy in the asking process (the chain tool's
test_the_read_runs_no_instrument_and_reaches_no_tree) sees only its own half, the wire, and can
never see what the judge runs. This proof keeps that measurement where the read happens: the
inspector is imported in a child under a scratch HOME (so its crossing roots bend to the
fixture's journal, test_the_roots_bend_only_under_a_scratch_home), subprocess.run is spied and
the module set recorded AFTER the import, and the judge is called directly.

  5. Over a stale verdict with a BUILDME journaled, proved_answers_the_chart refuses it
     ("predates the build"), runs no subprocess, and imports no tree, db or inference module.

A hollow build could not pass: a freshness read that shells out (git, systemd-run) or loads
the tree reads its call or module back here.

    python3 cairn/machines/build_inspector/proofs/test_the_freshness_read_runs_no_instrument.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"6ebec06794ac": {"5": "test_the_judge_runs_no_instrument_and_reaches_no_tree"}}

_ANSWER = {
    "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                  "evidence": "seen: exit 0 twice",
                  "discriminating_observation": "reverted the fix; the instrument exits 1"}],
    "dispositions": [{"piece": "p1", "expect": "e1", "disposition": "confirmed",
                      "by": "the run observed"}],
}

_CHILD = r"""
import json, subprocess, sys
from pathlib import Path
from cairn.machines.build_inspector import inspector
calls = []
_real = subprocess.run
def spy(argv, *a, **k):
    calls.append(list(argv))
    return _real(argv, *a, **k)
subprocess.run = spy
before = set(sys.modules)
f = inspector.proved_answers_the_chart("widget", berths_root=Path(sys.argv[1]))
reached = sorted(m for m in set(sys.modules) - before if m.startswith((
    "cairn.tools.tree", "cairn.devices.db_domain", "cairn.devices.librarian",
    "cairn.devices.inferenceproxy", "psycopg", "requests", "httpx")))
print(json.dumps({"findings": f, "calls": calls, "reached": reached}, default=str))
"""


def _world(d: Path) -> tuple[Path, Path]:
    """Chart berths claiming 'widget' with one verdict stamped before a journaled BUILDME."""
    packets = d / "berths" / "0" / "packets"
    packets.mkdir(parents=True)
    hyp = packets / "hypothesize-20260901T000000-feed.json"
    hyp.write_text(json.dumps({"hypotheses": [
        {"piece": "p1", "expect": "e1", "falsifier": "f", "instrument": "i"}]}))
    val = packets / "validate-20260901T000001-feed.json"
    val.write_text(json.dumps({"ticket": "widget", "hypothesize_ref": str(hyp),
                               "criteria": [{"claim": "c1", "instrument": "cmd", "covers": ["p1"]}]}))
    (packets / "verdict-20261001T115959-0000feed.json").write_text(
        json.dumps({"ticket": "widget", "validate_ref": str(val), **_ANSWER}))
    journal = d / "crossings"
    journal.mkdir()
    (journal / "history.json").write_text(json.dumps([
        {"ticket": "widget", "at": "2026-10-01T12:00:00", "from": "TICKETME", "to": "BUILDME",
         "direction": "forward", "by": "fixture"}]))
    return d / "berths", journal


def test_the_judge_runs_no_instrument_and_reaches_no_tree():
    from cairn.tools.inspect_wire.inspect_wire import _launch_env
    from cairn.tools.scratch.scratch import home_env, scratch_dir
    world = scratch_dir("freshness-read-6ebec-")
    berths, journal = _world(world)
    env = home_env(world, **_launch_env(None, None, {"repo": journal, "commons": journal}))
    done = subprocess.run([sys.executable, "-c", _CHILD, str(berths)],
                          env={**env, "PYTHONPATH": str(REPO)}, capture_output=True, text=True,
                          timeout=300, cwd=str(REPO))
    assert done.returncode == 0, done.stderr[-1500:]
    got = json.loads(done.stdout.strip().splitlines()[-1])
    assert got["findings"] and "predates the build" in got["findings"][0]["about"], got
    assert got["calls"] == [], f"the freshness read runs nothing when a BUILDME stands: {got['calls']}"
    assert got["reached"] == [], f"the freshness read reached tree/db/inference machinery: {got['reached']}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

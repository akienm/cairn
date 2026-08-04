"""Proof for superclaude's trace wire (deploy pass, approved 2026-08-01).

A launch is a firing: door_pass on a clean floor, send_back with the lack named when
the preflight was bypassed or left residue — launched anyway (prime directive), but
counted. The wire is backgrounded, so the teeth wait for the record; and the teeth
assert INVARIANTS, never snapshots (the preflight's residue on a real box is
legitimately variable — pinning it would red on normal motion).

    python3 launchers/proofs/test_superclaude_wire.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
# Runnable bare, so it cannot lean on an externally-set PYTHONPATH to reach cairn.*.
sys.path.insert(0, str(_REPO))

from cairn.tester.scratch import scratch_dir  # noqa: E402

_LAUNCHER = _REPO / "launchers" / "superclaude"


def _launch(*args: str, troot: str) -> subprocess.CompletedProcess:
    env = {**os.environ,
           "CAIRN_LB_TRACE_ROOT": troot,          # a proof launch is not a real firing
           "PYTHONPATH": str(_REPO),
           "CLAUDE_BIN": "true",                  # exec lands on /bin/true, not claude
           "CAIRN_BOOT_LOG": os.path.join(troot, "bootlog")}
    return subprocess.run(["bash", str(_LAUNCHER), *args],
                          capture_output=True, text=True, env=env, timeout=120)


def _wait_records(troot: str, want: int = 1, timeout: float = 15.0) -> list[dict]:
    path = Path(troot) / "superclaude.jsonl"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            recs = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
            if len(recs) >= want:
                return recs
        time.sleep(0.1)
    return []


def test_a_bypassed_preflight_is_a_named_send_back():
    troot = str(scratch_dir("sc-wire-bypass-"))
    r = _launch("--no-preflight", troot=troot)
    assert r.returncode == 0, f"the launch must reach exec: {r.stderr}"
    recs = _wait_records(troot)
    assert len(recs) == 1, f"one launch, one firing: {recs}"
    assert recs[0]["event"] == "send_back", "a bypassed floor check is a counted refusal"
    assert "no-preflight" in recs[0]["data"]["lacks"][0], "the send_back names the bypass"


def test_a_real_launch_fires_exactly_once_with_an_honest_event():
    troot = str(scratch_dir("sc-wire-launch-"))
    r = _launch(troot=troot)
    assert r.returncode == 0, f"the launch must reach exec: {r.stderr}"
    recs = _wait_records(troot)
    assert len(recs) == 1, f"one launch, one firing: {recs}"
    rec = recs[0]
    assert rec["event"] in ("door_pass", "send_back"), rec
    if rec["event"] == "send_back":                      # residue is real, then: named
        assert rec["data"]["lacks"], "a send_back never fires unnamed"
    assert rec["consumer"] == "training", "the denominator must not expire"


def test_a_dry_run_is_not_a_launch_and_traces_nothing():
    troot = str(scratch_dir("sc-wire-dry-"))
    r = _launch("--dry-run", "--no-preflight", troot=troot)
    assert r.returncode == 0 and "exec" in r.stdout
    time.sleep(1.0)                                      # give a wrong wire time to land
    assert _wait_records(troot, want=1, timeout=0.1) == [], \
        "a dry-run crossed no door; a record here is an invented firing"


if __name__ == "__main__":
    failed = 0
    for tooth in (test_a_bypassed_preflight_is_a_named_send_back,
                  test_a_real_launch_fires_exactly_once_with_an_honest_event,
                  test_a_dry_run_is_not_a_launch_and_traces_nothing):
        try:
            tooth()
            print(f"  green  {tooth.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  RED    {tooth.__name__}: {exc}")
    print(f"\n{3 - failed}/3 teeth green")
    sys.exit(1 if failed else 0)

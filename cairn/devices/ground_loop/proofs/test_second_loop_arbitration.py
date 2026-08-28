"""Proof for a-second-loop-arbitrates-on-the-device-list.

Teeth a hollow build could not pass:

  - A STALE INCUMBENT IS REPLACED. When the liveness record is older than 120s,
    arbitrate_newcomer returns action="takeover" with the incumbent's pid.
  - A HEALTHY INCUMBENT IS RESPECTED. When the liveness record is fresh (<=120s),
    arbitrate_newcomer returns action="exit" — the newcomer backs off.
  - AN ABSENT RECORD IS AN EXIT. When no liveness record exists, the newcomer
    exits — there is nothing to measure staleness against.
  - THE THRESHOLD IS 120s, NOT 300s. The arbitration uses its own threshold
    (two beat cycles at 60s cadence), distinct from the liveness staleness
    threshold used for diagnostic display.

    python3 cairn/devices/ground_loop/proofs/test_second_loop_arbitration.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.ground_loop.loop import (
    arbitrate_newcomer,
    ARBITRATION_THRESHOLD_S,
)
from cairn.devices.ground_loop.liveness import RECORD_NAME

PASSES = 0


def ok(name: str, cond: bool, detail: str = ""):
    global PASSES
    if not cond:
        print(f"RED  {name}  {detail}")
        raise SystemExit(1)
    PASSES += 1
    print(f"  ok {name}")


def _write_liveness(home: Path, age_s: float, pid: int = 12345):
    now = datetime.now(timezone.utc)
    last_run = now - timedelta(seconds=age_s)
    record = {"last_run": last_run.isoformat(), "state": {}, "pid": pid}
    home.mkdir(parents=True, exist_ok=True)
    (home / RECORD_NAME).write_text(json.dumps(record))
    return now


def main() -> int:
    ok("threshold is 120s", ARBITRATION_THRESHOLD_S == 120.0,
       f"got {ARBITRATION_THRESHOLD_S}")

    with tempfile.TemporaryDirectory() as d:
        home = Path(d) / "gl" / "0"

        # ── stale incumbent: takeover ────────────────────────────────────
        now = _write_liveness(home, age_s=200.0, pid=99999)
        decision = arbitrate_newcomer(now, home)
        ok("stale incumbent → takeover",
           decision["action"] == "takeover", str(decision))
        ok("stale decision names the pid",
           decision["pid"] == 99999, str(decision))
        ok("stale decision reports the age",
           decision["age_s"] is not None and decision["age_s"] > 120.0,
           str(decision))

        # ── healthy incumbent: exit ──────────────────────────────────────
        now = _write_liveness(home, age_s=30.0, pid=88888)
        decision = arbitrate_newcomer(now, home)
        ok("healthy incumbent → exit",
           decision["action"] == "exit", str(decision))
        ok("healthy decision names the pid",
           decision["pid"] == 88888, str(decision))

        # ── borderline: exactly at threshold → exit (<=, not <) ──────────
        now = _write_liveness(home, age_s=120.0, pid=77777)
        decision = arbitrate_newcomer(now, home)
        ok("at-threshold incumbent → exit (<=)",
           decision["action"] == "exit", str(decision))

        # ── just past threshold → takeover ───────────────────────────────
        now = _write_liveness(home, age_s=120.1, pid=66666)
        decision = arbitrate_newcomer(now, home)
        ok("past-threshold incumbent → takeover",
           decision["action"] == "takeover", str(decision))

    with tempfile.TemporaryDirectory() as d:
        home = Path(d) / "gl" / "0"
        home.mkdir(parents=True, exist_ok=True)
        # ── absent record: exit ──────────────────────────────────────────
        now = datetime.now(timezone.utc)
        decision = arbitrate_newcomer(now, home)
        ok("absent record → exit",
           decision["action"] == "exit", str(decision))
        ok("absent record has no pid",
           decision["pid"] is None, str(decision))
        ok("absent reason mentions the lack",
           decision["reason"] is not None, str(decision))

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

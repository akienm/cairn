"""PROOF — the commit door refuses incomplete checkpoints and traces both exits.

Teeth a hollow build could not pass (Law 8), every root injected. The commit skill
has four contract fields and no semantic judge — the flat contract is the whole door.
A blank message should be refused here rather than inside git.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/commit/proofs/test_commit_door.py
Run twice; never trust the first green.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))

from cairn.machines.learning_block.learning_block import DoorRefused, read_trace  # noqa: E402
from cairn.machines.skill_block import skill_block as sb                          # noqa: E402
from cairn.machines.skill_block.skill_block import read_berth                     # noqa: E402
from cairn.devices.tester.scratch import scratch_dir                              # noqa: E402

PASSES = 0


def ok(name: str, cond: bool, detail: str = ""):
    global PASSES
    if not cond:
        print(f"RED  {name}  {detail}")
        raise SystemExit(1)
    PASSES += 1
    print(f"  ok {name}")


def fields_of(exc: DoorRefused) -> list[str]:
    return sorted(l["field"] for l in (getattr(exc, "lacks", None) or []))


BULLET = [{"text": "commit proof fixture", "stratum": "code"}]

GOOD = {
    "message": "add feature X",
    "scope": "all changes",
    "exit": "routed_forward",
    "bullets": BULLET,
}


def main() -> int:
    tmp = scratch_dir("commit-door-proof-")
    traces, berths = tmp / "traces", tmp / "berths"
    kw = dict(trace_root=traces, berths=berths)

    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:commit.jsonl"
    live_before = live_trace.read_bytes() if live_trace.exists() else None

    # ── the entry gate: every lack in ONE raise ───────────────────────────────
    try:
        sb.fire("commit", {}, **kw)
        ok("empty packet refused", False, "the door opened on nothing")
    except DoorRefused as exc:
        ok("entry gate: all four lacks in one raise",
           fields_of(exc) == ["bullets", "exit", "message", "scope"],
           str(fields_of(exc)))

    # ── conforming packet passes and berths ──────────────────────────────────
    res = sb.fire("commit", dict(GOOD), **kw)
    ok("conforming pass berths", bool(res.get("berth")) and Path(res["berth"]).exists())
    berth = read_berth(res["berth"])
    ok("berth names the skill", berth is not None and berth["skill"] == "commit")
    ok("berth carries the commit message",
       berth["answers"]["message"] == "add feature X")

    # ── both exits berth ─────────────────────────────────────────────────────
    out = sb.fire("commit", {**GOOD, "exit": "routed_out"}, **kw)
    ok("routed_out berths too", bool(out.get("berth")) and Path(out["berth"]).exists())
    ok("routed_out exit is recorded",
       read_berth(out["berth"])["exit"] == "routed_out")

    # ── whitespace message refused ───────────────────────────────────────────
    try:
        sb.fire("commit", {**GOOD, "message": "   "}, **kw)
        ok("whitespace message refused", False, "blank message passed")
    except DoorRefused as exc:
        ok("whitespace message refused", "message" in fields_of(exc))

    # ── both edges traced in the injected root ───────────────────────────────
    recs = read_trace("skill:commit", root=traces)
    ok("passes traced",
       any(r["event"] == "door_pass" for r in recs))
    ok("refusals traced",
       any(r["event"] == "send_back" for r in recs))

    # ── the generic CLI path ─────────────────────────────────────────────────
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "CAIRN_LB_TRACE_ROOT": str(traces), "CAIRN_SKILL_BERTHS": str(berths)}
    pkt = tmp / "cli_good.json"
    pkt.write_text(json.dumps(GOOD))
    p = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                        "fire", "commit", str(pkt)],
                       capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI exits 0", p.returncode == 0, p.stderr[:200])
    cli_result = json.loads(p.stdout)
    ok("generic CLI berths", bool(cli_result.get("berth")))

    bad = tmp / "cli_bad.json"
    bad.write_text(json.dumps({"message": "", "scope": "all"}))
    p2 = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                         "fire", "commit", str(bad)],
                        capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI refuses incomplete (exit 2)", p2.returncode == 2, p2.stderr[:200])

    # ── live trace untouched ─────────────────────────────────────────────────
    live_after = live_trace.read_bytes() if live_trace.exists() else None
    ok("live trace untouched by the proof", live_before == live_after)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

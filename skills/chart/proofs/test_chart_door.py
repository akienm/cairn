"""PROOF — the chart door refuses incomplete packets and validates task_or_ticket.

Teeth a hollow build could not pass (Law 8), every root injected. The door gates the
chain's ENTRY — what was asked and whether it is a ticket or a task — so its teeth are
entry-shaped: the contract is complete, the semantic vocabulary is enforced, and both
exits berth.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/chart/proofs/test_chart_door.py
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

sys.path.insert(0, str(_REPO / "skills" / "chart"))
import door  # noqa: E402

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


BULLET = [{"text": "charted the request", "stratum": "code"}]


def main() -> int:
    tmp = scratch_dir("chart-door-proof-")
    traces, berths = tmp / "traces", tmp / "berths"
    kw = dict(trace_root=traces, berths=berths)

    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:chart.jsonl"
    live_before = live_trace.read_text() if live_trace.exists() else None

    good = {
        "request": "build the dashboard pane",
        "task_or_ticket": "ticket",
        "exit": "routed_forward",
        "bullets": BULLET,
    }

    # ── the entry gate: every lack in ONE raise ───────────────────────────────
    try:
        door.fire({}, **kw)
        ok("empty packet refused", False, "the door opened a chart on nothing")
    except DoorRefused as exc:
        ok("entry gate: all four lacks in one raise",
           fields_of(exc) == ["bullets", "exit", "request", "task_or_ticket"],
           str(fields_of(exc)))

    # ── the semantic judge: task_or_ticket vocabulary ─────────────────────────
    try:
        door.fire({**good, "task_or_ticket": "feature"}, **kw)
        ok("bad task_or_ticket refused", False, "a free-text value passed")
    except DoorRefused as exc:
        ok("bad task_or_ticket refused", fields_of(exc) == ["task_or_ticket"])
        ok("bad task_or_ticket why names the vocabulary",
           "'ticket'" in str(exc) and "'task'" in str(exc))

    # ── flat + semantic lacks in ONE refusal ──────────────────────────────────
    try:
        door.fire({"task_or_ticket": "feature", "exit": "routed_forward",
                   "bullets": BULLET}, **kw)
        ok("flat+semantic one pass", False)
    except DoorRefused as exc:
        f = fields_of(exc)
        ok("flat+semantic one pass", "request" in f and "task_or_ticket" in f, str(f))

    # ── conforming forward: berths ────────────────────────────────────────────
    res = door.fire(dict(good), **kw)
    berth = read_berth(res["berth"])
    ok("conforming forward berths", berth is not None and berth["skill"] == "chart")
    ok("berth carries the request",
       berth["answers"]["request"] == good["request"])

    # ── conforming routed_out: also berths ────────────────────────────────────
    out = door.fire({**good, "exit": "routed_out"}, **kw)
    out_berth = read_berth(out["berth"])
    ok("routed_out berths too", out_berth is not None)
    ok("routed_out exit recorded", out_berth["exit"] == "routed_out")

    # ── both edges traced ─────────────────────────────────────────────────────
    recs = read_trace("skill:chart", root=traces)
    ok("both edges traced",
       any(r["event"] == "door_pass" for r in recs) and
       any(r["event"] == "send_back" for r in recs))

    # ── the CLI ───────────────────────────────────────────────────────────────
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "CAIRN_LB_TRACE_ROOT": str(traces), "CAIRN_SKILL_BERTHS": str(berths)}
    pkt = tmp / "good.json"
    pkt.write_text(json.dumps(good))
    p = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                        "fire", "chart", str(pkt)],
                       capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI exits 0", p.returncode == 0, p.stderr[:200])
    result = json.loads(p.stdout)
    ok("generic CLI berths", bool(result.get("berth")))

    bad = tmp / "bad.json"
    bad.write_text(json.dumps({"task_or_ticket": "feature", "exit": "routed_forward",
                               "bullets": BULLET}))
    p = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                        "fire", "chart", str(bad)],
                       capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI refuses bad packet", p.returncode == 2, p.stderr[:200])

    # ── live trace untouched ──────────────────────────────────────────────────
    live_after = live_trace.read_text() if live_trace.exists() else None
    ok("live trace untouched by this proof", live_after == live_before)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

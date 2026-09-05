"""PROOF — the moreabout door refuses incomplete packets and traces both exits.

Teeth a hollow build could not pass (Law 8), every root injected. /moreabout has a
flat contract only (no semantic judges) — so the teeth are presence-shaped: every
required field named in one refuse, both exits berth and trace.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/moreabout/proofs/test_moreabout_door.py
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


BULLET = [{"text": "expansion found", "stratum": "tree"}]


def main() -> int:
    tmp = scratch_dir("moreabout-door-proof-")
    traces, berths = tmp / "traces", tmp / "berths"
    kw = dict(trace_root=traces, berths=berths)

    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:moreabout.jsonl"
    live_before = live_trace.read_text() if live_trace.exists() else None

    good = {
        "ask": "expand the survey holdings field",
        "context": "build",
        "exit": "routed_forward",
        "bullets": BULLET,
    }

    # ── the entry gate: every lack in ONE raise ───────────────────────────────
    try:
        sb.fire("moreabout", {}, **kw)
        ok("empty packet refused", False, "the door opened on nothing")
    except DoorRefused as exc:
        ok("entry gate: all four lacks in one raise",
           fields_of(exc) == ["ask", "bullets", "context", "exit"],
           str(fields_of(exc)))

    # ── conforming forward: berths ────────────────────────────────────────────
    res = sb.fire("moreabout", dict(good), **kw)
    berth = read_berth(res["berth"])
    ok("conforming forward berths", berth is not None and berth["skill"] == "moreabout")
    ok("berth carries the ask",
       berth["answers"]["ask"] == good["ask"])

    # ── conforming routed_out: also berths ────────────────────────────────────
    out = sb.fire("moreabout", {**good, "exit": "routed_out"}, **kw)
    out_berth = read_berth(out["berth"])
    ok("routed_out berths too", out_berth is not None)
    ok("routed_out exit recorded", out_berth["exit"] == "routed_out")

    # ── both edges traced ─────────────────────────────────────────────────────
    recs = read_trace("skill:moreabout", root=traces)
    ok("both edges traced",
       any(r["event"] == "door_pass" for r in recs) and
       any(r["event"] == "send_back" for r in recs))

    # ── the CLI ───────────────────────────────────────────────────────────────
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "CAIRN_LB_TRACE_ROOT": str(traces), "CAIRN_SKILL_BERTHS": str(berths)}
    pkt = tmp / "good.json"
    pkt.write_text(json.dumps(good))
    p = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                        "fire", "moreabout", str(pkt)],
                       capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI exits 0", p.returncode == 0, p.stderr[:200])
    result = json.loads(p.stdout)
    ok("generic CLI berths", bool(result.get("berth")))

    bad = tmp / "bad.json"
    bad.write_text(json.dumps({"context": "build"}))
    p = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                        "fire", "moreabout", str(bad)],
                       capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI refuses bad packet", p.returncode == 2, p.stderr[:200])

    # ── live trace untouched ──────────────────────────────────────────────────
    live_after = live_trace.read_text() if live_trace.exists() else None
    ok("live trace untouched by this proof", live_after == live_before)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""PROOF — the sail door refuses incomplete packets and enforces its semantic judges.

/sail's input_contract declares five fields (request, task_or_ticket, exit, disposition,
bullets) with a semantic judge (skills/sail/door.py) that enforces:
  - task_or_ticket must be 'ticket' (never 'task' — /sail always builds a cast ticket)
  - exit/disposition coherence: routed_forward requires 'built',
    routed_out requires 'not-ready' or 'kicked-back:<reason>'

DISTINCT FROM test_sail_pins_its_refusals.py, which pins the PROSE contract (SKILL.md's
step order, refusal conditions, gate name resolution). This proof pins the PACKET
contract — the structured fields the seam validates at the door.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/sail/proofs/test_sail_door.py
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

sys.path.insert(0, str(_REPO / "skills" / "sail"))
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


BULLET = [{"text": "fixture voyage complete", "stratum": "code"}]


def main() -> int:
    tmp = scratch_dir("sail-door-proof-")
    traces, berths = tmp / "traces", tmp / "berths"
    kw = dict(trace_root=traces, berths=berths)

    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:sail.jsonl"
    live_before = live_trace.read_bytes() if live_trace.exists() else None

    # ── the entry gate: every lack in ONE raise ───────────────────────────────
    try:
        sb.fire("sail", {}, **kw)
        ok("empty packet refused", False, "the door passed an empty packet")
    except DoorRefused as exc:
        ok("entry gate: all five lacks in one raise",
           fields_of(exc) == ["bullets", "disposition", "exit", "request",
                              "task_or_ticket"],
           str(fields_of(exc)))
        ok("refusal carries the WHY, not just the name",
           all(len(l["why"]) > 20 for l in exc.lacks))

    # ── conforming routed_forward with disposition='built' ────────────────────
    good_fwd = {"request": "implement the widget system",
                "task_or_ticket": "ticket",
                "exit": "routed_forward",
                "disposition": "built",
                "bullets": BULLET}
    res_fwd = sb.fire("sail", dict(good_fwd), **kw)
    berth_fwd = read_berth(res_fwd["berth"])
    ok("conforming forward berths", berth_fwd is not None and berth_fwd["skill"] == "sail")
    ok("berth carries the request", berth_fwd["answers"]["request"] == good_fwd["request"])
    ok("berth carries disposition", berth_fwd["answers"]["disposition"] == "built")

    # ── conforming routed_out with disposition='not-ready' ────────────────────
    good_out = {**good_fwd, "exit": "routed_out", "disposition": "not-ready"}
    res_out = sb.fire("sail", dict(good_out), **kw)
    berth_out = read_berth(res_out["berth"])
    ok("routed_out berths too", berth_out is not None and berth_out["exit"] == "routed_out")

    # ── routed_out with kicked-back ───────────────────────────────────────────
    kicked = {**good_fwd, "exit": "routed_out", "disposition": "kicked-back:proof failed"}
    res_kick = sb.fire("sail", dict(kicked), **kw)
    ok("kicked-back disposition passes",
       read_berth(res_kick["berth"])["answers"]["disposition"] == "kicked-back:proof failed")

    # ── SEMANTIC: task_or_ticket='task' refused ───────────────────────────────
    try:
        sb.fire("sail", {**good_fwd, "task_or_ticket": "task"}, **kw)
        ok("task refused", False, "a task passed /sail's door")
    except DoorRefused as exc:
        ok("task_or_ticket='task' refused", "task_or_ticket" in fields_of(exc))
        ok("task why says sail only builds tickets",
           "cast" in str(exc).lower() or "ticket" in str(exc).lower())

    # ── SEMANTIC: incoherent disposition (forward + not-ready) ────────────────
    try:
        sb.fire("sail", {**good_fwd, "disposition": "not-ready"}, **kw)
        ok("incoherent disposition refused", False, "forward+not-ready passed")
    except DoorRefused as exc:
        ok("incoherent disposition (forward + not-ready) refused",
           "disposition" in fields_of(exc))

    # ── SEMANTIC: incoherent disposition (out + built) ────────────────────────
    try:
        sb.fire("sail", {**good_fwd, "exit": "routed_out", "disposition": "built"}, **kw)
        ok("incoherent disposition out+built refused", False)
    except DoorRefused as exc:
        ok("incoherent disposition (out + built) refused",
           "disposition" in fields_of(exc))

    # ── flat + semantic lacks in ONE refusal ──────────────────────────────────
    try:
        sb.fire("sail", {"request": "x", "task_or_ticket": "task",
                         "exit": "routed_forward", "disposition": "not-ready"}, **kw)
        ok("flat+semantic one pass", False)
    except DoorRefused as exc:
        f = fields_of(exc)
        ok("flat+semantic lacks in ONE refusal",
           "bullets" in f and "task_or_ticket" in f and "disposition" in f, str(f))

    # ── bad exit refused ──────────────────────────────────────────────────────
    try:
        sb.fire("sail", {**good_fwd, "exit": "completed"}, **kw)
        ok("bad exit refused", False)
    except DoorRefused as exc:
        ok("bad exit refused", "exit" in fields_of(exc))

    # ── both edges traced ─────────────────────────────────────────────────────
    recs = read_trace("skill:sail", root=traces)
    ok("both edges traced",
       any(r["event"] == "door_pass" for r in recs) and
       any(r["event"] == "send_back" for r in recs))
    ok("refusal trace names the judge",
       any(r["event"] == "send_back" and r["data"].get("judge") == "sail-door"
           for r in recs))

    # ── the generic CLI path ──────────────────────────────────────────────────
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "CAIRN_LB_TRACE_ROOT": str(traces), "CAIRN_SKILL_BERTHS": str(berths)}
    pkt = tmp / "cli_packet.json"
    pkt.write_text(json.dumps(good_fwd))
    p = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                        "fire", "sail", str(pkt)],
                       capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI exits 0 for sail", p.returncode == 0, p.stderr[:200])
    result = json.loads(p.stdout)
    ok("generic CLI berths sail", bool(result.get("berth")))

    # CLI refusal
    bad_pkt = tmp / "bad.json"
    bad_pkt.write_text(json.dumps({"request": "x", "task_or_ticket": "task"}))
    p2 = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                         "fire", "sail", str(bad_pkt)],
                        capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI refuses incomplete sail", p2.returncode == 2, p2.stderr[:200])

    # ── live trace untouched ──────────────────────────────────────────────────
    live_after = live_trace.read_bytes() if live_trace.exists() else None
    ok("live trace untouched by this proof", live_before == live_after)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

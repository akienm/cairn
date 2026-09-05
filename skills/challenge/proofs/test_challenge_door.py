"""PROOF — the challenge door refuses incomplete passes and enforces the back_up vocabulary.

Teeth a hollow build could not pass (Law 8), every root injected. The challenge skill
has eight contract fields and a semantic judge: ``back_up`` must be one of proceed,
revise, or abandon — three values, no fourth. A free-text disposition defeats the count.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/challenge/proofs/test_challenge_door.py
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

sys.path.insert(0, str(_REPO / "skills" / "challenge"))
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


BULLET = [{"text": "challenge proof fixture", "stratum": "code"}]

GOOD = {
    "target": "the design of the challenge door itself",
    "better_approach": "considered — this is the pattern every other door uses",
    "prior_art": "sorted door is prior art; this door is simpler",
    "hidden_assumption": "assumes back_up vocabulary is stable",
    "real_collision": "none — this door and the intent challenge field are complementary",
    "back_up": "proceed",
    "exit": "routed_forward",
    "bullets": BULLET,
}


def main() -> int:
    tmp = scratch_dir("challenge-door-proof-")
    traces, berths = tmp / "traces", tmp / "berths"
    kw = dict(trace_root=traces, berths=berths)

    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:challenge.jsonl"
    live_before = live_trace.read_bytes() if live_trace.exists() else None

    # ── the entry gate: every lack in ONE raise ───────────────────────────────
    try:
        door.fire({}, **kw)
        ok("empty packet refused", False, "the door opened on nothing")
    except DoorRefused as exc:
        ok("entry gate: all eight lacks in one raise",
           fields_of(exc) == ["back_up", "better_approach", "bullets",
                               "exit", "hidden_assumption", "prior_art",
                               "real_collision", "target"],
           str(fields_of(exc)))

    # ── conforming packet passes and berths ──────────────────────────────────
    res = door.fire(dict(GOOD), **kw)
    ok("conforming pass berths", bool(res.get("berth")) and Path(res["berth"]).exists())
    berth = read_berth(res["berth"])
    ok("berth names the skill", berth is not None and berth["skill"] == "challenge")
    ok("berth carries the back_up answer",
       berth["answers"]["back_up"] == "proceed")

    # ── both exits berth ─────────────────────────────────────────────────────
    out = door.fire({**GOOD, "exit": "routed_out"}, **kw)
    ok("routed_out berths too", bool(out.get("berth")) and Path(out["berth"]).exists())
    ok("routed_out exit is recorded",
       read_berth(out["berth"])["exit"] == "routed_out")

    # ── bad back_up refused (the semantic judge) ─────────────────────────────
    try:
        door.fire({**GOOD, "back_up": "maybe"}, **kw)
        ok("bad back_up refused", False, "the door accepted a free-text disposition")
    except DoorRefused as exc:
        ok("bad back_up refused", fields_of(exc) == ["back_up"])
        ok("bad back_up why names the vocabulary",
           "proceed" in str(exc) and "revise" in str(exc) and "abandon" in str(exc))

    # ── each legal back_up value passes ──────────────────────────────────────
    for val in door.BACK_UP_VALUES:
        r = door.fire({**GOOD, "back_up": val}, **kw)
        ok(f"back_up={val!r} passes", bool(r.get("berth")))

    # ── flat + semantic lacks in ONE refusal ──────────────────────────────────
    try:
        door.fire({**GOOD, "back_up": "maybe", "bullets": []}, **kw)
        ok("flat+semantic one pass", False)
    except DoorRefused as exc:
        f = fields_of(exc)
        ok("flat+semantic one pass", "back_up" in f and "bullets" in f, str(f))

    # ── both edges traced in the injected root ───────────────────────────────
    recs = read_trace("skill:challenge", root=traces)
    ok("passes traced",
       any(r["event"] == "door_pass" for r in recs))
    ok("refusals traced",
       any(r["event"] == "send_back" and r["data"].get("judge") == "challenge-door"
           for r in recs))

    # ── the generic CLI path ─────────────────────────────────────────────────
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "CAIRN_LB_TRACE_ROOT": str(traces), "CAIRN_SKILL_BERTHS": str(berths)}
    pkt = tmp / "cli_good.json"
    pkt.write_text(json.dumps(GOOD))
    p = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                        "fire", "challenge", str(pkt)],
                       capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI exits 0", p.returncode == 0, p.stderr[:200])
    cli_result = json.loads(p.stdout)
    ok("generic CLI berths", bool(cli_result.get("berth")))

    bad = tmp / "cli_bad.json"
    bad.write_text(json.dumps({**GOOD, "back_up": "maybe"}))
    p2 = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                         "fire", "challenge", str(bad)],
                        capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI refuses bad back_up (exit 2)", p2.returncode == 2, p2.stderr[:200])

    # ── live trace untouched ─────────────────────────────────────────────────
    live_after = live_trace.read_bytes() if live_trace.exists() else None
    ok("live trace untouched by the proof", live_before == live_after)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

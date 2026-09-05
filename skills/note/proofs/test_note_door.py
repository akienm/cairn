"""PROOF — the note door refuses incomplete packets and traces both edges.

/note is a flat-contract-only skill (no semantic judge): text, exit, bullets.
The thinnest contract in the roster — capture must be near-zero friction — so
the proof pins the minimum: every lack in one pass, both exits berth, both
edges traced, and the live trace is never touched by this proof.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/note/proofs/test_note_door.py
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


BULLET = [{"text": "fixture note captured", "stratum": "code"}]


def main() -> int:
    tmp = scratch_dir("note-proof-")
    traces, berths = tmp / "traces", tmp / "berths"
    kw = dict(trace_root=traces, berths=berths)

    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:note.jsonl"
    live_before = live_trace.read_bytes() if live_trace.exists() else None

    # ── the entry gate: every lack in ONE raise ───────────────────────────────
    try:
        sb.fire("note", {}, **kw)
        ok("empty packet refused", False, "the door passed an empty capture")
    except DoorRefused as exc:
        ok("entry gate: all three lacks in one raise",
           fields_of(exc) == ["bullets", "exit", "text"], str(fields_of(exc)))
        ok("refusal carries the WHY, not just the name",
           all(len(l["why"]) > 20 for l in exc.lacks))

    # ── whitespace text refused ───────────────────────────────────────────────
    try:
        sb.fire("note", {"text": "   ", "exit": "routed_forward",
                         "bullets": BULLET}, **kw)
        ok("whitespace text refused", False, "blank text passed as captured note")
    except DoorRefused as exc:
        ok("whitespace text refused", "text" in fields_of(exc))

    # ── empty bullets refused ─────────────────────────────────────────────────
    try:
        sb.fire("note", {"text": "a real note", "exit": "routed_forward",
                         "bullets": []}, **kw)
        ok("empty bullets refused", False, "an empty list passed as bullets")
    except DoorRefused as exc:
        ok("empty bullets refused", "bullets" in fields_of(exc))

    # ── conforming routed_forward ─────────────────────────────────────────────
    good = {"text": "the API changed shape between v2 and v3",
            "exit": "routed_forward",
            "bullets": BULLET}
    res = sb.fire("note", dict(good), **kw)
    berth = read_berth(res["berth"])
    ok("conforming forward berths", berth is not None and berth["skill"] == "note")
    ok("berth carries the text", berth["answers"]["text"] == good["text"])

    # ── conforming routed_out ─────────────────────────────────────────────────
    out = sb.fire("note", {**good, "exit": "routed_out"}, **kw)
    berth_out = read_berth(out["berth"])
    ok("routed_out berths too", berth_out is not None and berth_out["exit"] == "routed_out")

    # ── bad exit refused ──────────────────────────────────────────────────────
    try:
        sb.fire("note", {**good, "exit": "captured"}, **kw)
        ok("bad exit refused", False, "a non-standard exit passed")
    except DoorRefused as exc:
        ok("bad exit refused", "exit" in fields_of(exc))

    # ── both edges traced ─────────────────────────────────────────────────────
    recs = read_trace("skill:note", root=traces)
    ok("both edges traced",
       any(r["event"] == "door_pass" for r in recs) and
       any(r["event"] == "send_back" for r in recs))

    # ── the generic CLI path ──────────────────────────────────────────────────
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "CAIRN_LB_TRACE_ROOT": str(traces), "CAIRN_SKILL_BERTHS": str(berths)}
    pkt = tmp / "cli_packet.json"
    pkt.write_text(json.dumps(good))
    p = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                        "fire", "note", str(pkt)],
                       capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI exits 0 for note", p.returncode == 0, p.stderr[:200])
    result = json.loads(p.stdout)
    ok("generic CLI berths note", bool(result.get("berth")))

    # CLI refusal
    bad_pkt = tmp / "bad.json"
    bad_pkt.write_text(json.dumps({"text": "x"}))
    p2 = subprocess.run([sys.executable, "-m", "cairn.machines.skill_block",
                         "fire", "note", str(bad_pkt)],
                        capture_output=True, text=True, timeout=30, env=env)
    ok("generic CLI refuses incomplete note", p2.returncode == 2, p2.stderr[:200])

    # ── live trace untouched ──────────────────────────────────────────────────
    live_after = live_trace.read_bytes() if live_trace.exists() else None
    ok("live trace untouched by this proof", live_before == live_after)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

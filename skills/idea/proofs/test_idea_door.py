"""PROOF — the idea door captures verbatim, refuses complete, and pollutes nothing.

Teeth a hollow build could not pass (Law 8), every root injected: this proof's fixtures
never reach the live trace or the live CairnCommons/ideas/, and one tooth pins exactly
that.

The tooth that matters most is VERBATIM. The whole why of this step is that capture is
the one moment where translation loss is zero, so a door that normalised, trimmed or
re-encoded the prose would defeat the step while passing every other check.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/idea/proofs/test_idea_door.py
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

from cairn.learning_block.learning_block import DoorRefused, read_trace  # noqa: E402
from cairn.skill_block.skill_block import read_berth                     # noqa: E402
from cairn.tester.scratch import scratch_dir                # noqa: E402

sys.path.insert(0, str(_REPO / "skills" / "idea"))
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


BULLET = [{"text": "nothing noticed at capture", "stratum": "code"}]
PROSE = ("  a ticket, a probe and a task are the SAME thing — one root,\n"
         "  per-level additions. (and yes, i mean it.)  ")


def main() -> int:
    tmp = scratch_dir("idea-proof-")
    traces, berths, commons = tmp / "traces", tmp / "berths", tmp / "commons"
    kw = dict(trace_root=traces, berths=berths, commons=commons)

    live_ideas = _REPO.parent / "CairnCommons" / "ideas"
    live_before = sorted(p.name for p in live_ideas.glob("*.json")) if live_ideas.is_dir() else []
    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:idea.jsonl"
    live_trace_before = live_trace.read_text() if live_trace.exists() else None

    # ── the entry gate: every lack in ONE raise ───────────────────────────────
    try:
        door.fire({}, **kw)
        ok("empty packet refused", False, "the door passed an empty capture")
    except DoorRefused as exc:
        ok("entry gate: all three lacks in one raise",
           fields_of(exc) == ["author", "bullets", "prose"], str(fields_of(exc)))
        ok("refusal carries the WHY, not just the name",
           all(len(l["why"]) > 40 for l in exc.lacks))

    try:
        door.fire({"prose": "   ", "author": "Akien", "bullets": BULLET}, **kw)
        ok("whitespace prose refused", False, "blank prose passed as captured text")
    except DoorRefused as exc:
        ok("whitespace prose refused", fields_of(exc) == ["prose"])

    try:
        door.fire({"prose": "x", "author": "Akien", "bullets": []}, **kw)
        ok("empty bullets refused", False, "an empty list passed as a bullet list")
    except DoorRefused as exc:
        ok("empty bullets refused", fields_of(exc) == ["bullets"])

    # ── the capture itself ────────────────────────────────────────────────────
    res = door.fire({"prose": PROSE, "author": "Akien", "bullets": BULLET}, **kw)
    rec = json.loads(Path(res["idea"]).read_text())

    ok("THE VERBATIM TOOTH: prose stored byte-identical", rec["prose"] == PROSE,
       repr(rec["prose"]))
    ok("author preserved", rec["author"] == "Akien")
    ok("interpretation is marked deferred", rec["interpretation"] == "deferred")
    ok("record cites its trace and its finding",
       rec["trace_id"] == res["trace_id"] and rec["finding_id"] == res["finding_id"])
    ok("record id is the file stem", rec["id"] == Path(res["idea"]).stem)
    ok("id is date-prefixed and readable", rec["id"].startswith(rec["date"][:10]))
    ok("slug is derived from the prose, not random",
       "ticket" in rec["id"] and "probe" in rec["id"], rec["id"])
    ok("slug is deterministic",
       door.slug_of(PROSE) == door.slug_of(PROSE) == "a-ticket-a-probe-and-a-task")
    ok("record landed in the INJECTED commons",
       str(res["idea"]).startswith(str(commons)))

    berth = read_berth(res["berth"])
    ok("berth exists and names the skill", berth is not None and berth["skill"] == "idea")
    ok("berth carries the finding id", berth["finding_id"] == res["finding_id"])
    ok("berth is instance-space, not the commons",
       str(res["berth"]).startswith(str(berths)))

    # ── collision: same day, same opening words ───────────────────────────────
    second = door.fire({"prose": PROSE, "author": "CC", "bullets": BULLET}, **kw)
    ok("collision does not overwrite", second["idea"] != res["idea"])
    ok("both records survive", json.loads(Path(res["idea"]).read_text())["author"] == "Akien")
    ok("collision suffix keeps the readable stem",
       second["id"].startswith(door.slug_of(PROSE)[:10]) or "a-ticket" in second["id"],
       second["id"])

    # ── the trace: both firings recorded, refusals too ────────────────────────
    recs = read_trace("skill:idea", root=traces)
    events = [r["event"] for r in recs]
    ok("every refusal traced", events.count("send_back") == 3, str(events))
    ok("every capture traced", events.count("door_pass") == 2, str(events))
    ok("a finding rides each capture", events.count("finding") == 2, str(events))

    # ── the CLI, which is what the skill actually calls ───────────────────────
    # The subprocess gets the roots too, or the CLI tooth pollutes the very denominator
    # the skilldial reads. Found by the last tooth in this file on its first run: the
    # proof was writing a send_back into the live trace for skill:idea, which would have
    # made a fixture indistinguishable from a real refused capture.
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "CAIRN_LB_TRACE_ROOT": str(traces), "CAIRN_SKILL_BERTHS": str(berths)}
    bad = tmp / "bad.json"
    bad.write_text(json.dumps({"prose": "x"}))
    p = subprocess.run([sys.executable, str(_REPO / "skills/idea/door.py"), str(bad)],
                       capture_output=True, text=True, env=env)
    ok("CLI refusal: exit 2", p.returncode == 2, p.stderr[:200])
    ok("CLI refusal names both lacks on stderr",
       "author" in p.stderr and "bullets" in p.stderr, p.stderr[:200])

    # ── nothing live was touched ──────────────────────────────────────────────
    live_after = sorted(p.name for p in live_ideas.glob("*.json")) if live_ideas.is_dir() else []
    ok("live commons/ideas untouched by this proof", live_after == live_before)
    live_trace_after = live_trace.read_text() if live_trace.exists() else None
    ok("live trace untouched by this proof", live_trace_after == live_trace_before)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

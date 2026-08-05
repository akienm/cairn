"""PROOF — the intent door makes the fan-out edge real and the challenge floor physics.

Teeth a hollow build could not pass (Law 8), every root injected. Two judges, and both
enforce something this skill's charter ALREADY DECLARED and nothing checked:

- ``from_idea`` must RESOLVE. The tooth that matters: an origin that reads plausibly
  but opens nothing is refused. That is the whole difference between an edge and a
  claim about one — and without it, three intentions born of one idea could say they
  were siblings without any of them being able to prove it.
- ``challenge`` must carry all five answers. A one-key object satisfied ``check_input``
  and therefore satisfied nothing; the charter's floor was prose. The tooth pins the
  partial pass, which is the case a naive build lets through.

ZERO SEAM CHANGE is this build's own falsifier, exactly as it was for the sorted door:
a clean packet must ride ``skill_block.fire`` unchanged.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/intent/proofs/test_intent_door.py
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

sys.path.insert(0, str(_REPO / "skills" / "intent"))
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


def why_of(exc: DoorRefused, field: str) -> str:
    return " | ".join(l["why"] for l in exc.lacks if l["field"] == field)


FIVE = ("better_approach", "prior_art", "hidden_assumption", "real_collision", "back_up")


def main() -> int:
    tmp = scratch_dir("intent-proof-")
    traces, berths, commons = tmp / "traces", tmp / "berths", tmp / "commons"
    (commons / "ideas").mkdir(parents=True)
    (commons / "ideas" / "2026-08-04-a-real-idea.json").write_text(
        json.dumps({"id": "2026-08-04-a-real-idea", "prose": "p", "author": "Akien"}))
    kw = dict(trace_root=traces, berths=berths, commons=commons)

    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:intent.jsonl"
    live_before = live_trace.read_text() if live_trace.exists() else None

    good = {"from_idea": "2026-08-04-a-real-idea",
            "what": "unify ticket, probe and task", "how": "one root, per-level additions",
            "traces_to": "Law 1", "shape": "new track", "falsifier": "one root ships",
            "challenge": {k: "considered, and here is what I found" for k in FIVE},
            "exit": "routed_forward",
            "bullets": [{"text": "prior art: tickets/ticket-and-task.json", "stratum": "tree"}]}

    # ── the entry gate ────────────────────────────────────────────────────────
    try:
        door.fire({}, **kw)
        ok("empty packet refused", False)
    except DoorRefused as exc:
        ok("entry gate: all nine lacks in one raise",
           fields_of(exc) == ["bullets", "challenge", "exit", "falsifier", "from_idea",
                              "how", "shape", "traces_to", "what"], str(fields_of(exc)))

    # ── from_idea: the fan-out edge ───────────────────────────────────────────
    try:
        door.fire({**good, "from_idea": "2026-08-04-an-idea-that-was-never-captured"}, **kw)
        ok("THE EDGE TOOTH: unresolvable origin refused", False,
           "a plausible-looking id opened the door")
    except DoorRefused as exc:
        ok("THE EDGE TOOTH: unresolvable origin refused", fields_of(exc) == ["from_idea"])
        ok("edge why sends the caller to /idea", "/idea" in why_of(exc, "from_idea"))
        ok("edge why names the sibling problem", "siblings" in why_of(exc, "from_idea"))

    by_path = door.fire({**good, "from_idea":
                         str(commons / "ideas" / "2026-08-04-a-real-idea.json")}, **kw)
    ok("an idea PATH resolves as well as an id", read_berth(by_path["berth"]) is not None)

    try:
        door.fire({**good, "from_idea": "none, because it just came up"}, **kw)
        ok("hollow exemption refused", False)
    except DoorRefused as exc:
        ok("hollow exemption refused", fields_of(exc) == ["from_idea"])
        ok("hollow-exemption why names the three referent kinds",
           all(k in why_of(exc, "from_idea") for k in ("path", "ticket", "bin/cmd")))

    try:
        door.fire({**good, "from_idea": "none"}, **kw)
        ok("bare 'none' refused", False)
    except DoorRefused as exc:
        ok("bare 'none' refused, distinctly from the exemption",
           "silence with extra words" in why_of(exc, "from_idea"))

    exempt = door.fire({**good, "from_idea":
                        "none, because this was found while running bin/cmd/skilldial, not captured as an idea"}, **kw)
    ok("referent-carrying exemption passes", read_berth(exempt["berth"]) is not None)

    # ── challenge: the floor the charter declared ─────────────────────────────
    for missing in FIVE:
        partial = {k: "considered" for k in FIVE if k != missing}
        try:
            door.fire({**good, "challenge": partial}, **kw)
            ok(f"partial challenge missing {missing} refused", False)
        except DoorRefused as exc:
            ok(f"THE FLOOR TOOTH: challenge missing {missing} refused",
               fields_of(exc) == ["challenge"] and missing in why_of(exc, "challenge"))

    try:
        door.fire({**good, "challenge": {k: "  " for k in FIVE}}, **kw)
        ok("all-blank challenge refused", False)
    except DoorRefused as exc:
        ok("blank answers count as absent, not present",
           all(f in why_of(exc, "challenge") for f in FIVE))

    try:
        door.fire({**good, "challenge": "I challenged it"}, **kw)
        ok("prose challenge refused", False)
    except DoorRefused as exc:
        ok("prose where the five answers belong is refused",
           fields_of(exc) == ["challenge"])

    # ── one pass, and the kill still fires ────────────────────────────────────
    try:
        door.fire({**good, "from_idea": "nope", "challenge": {"prior_art": "x"}}, **kw)
        ok("multi-lack refused", False)
    except DoorRefused as exc:
        ok("ONE PASS: both semantic lacks raised together",
           fields_of(exc) == ["challenge", "from_idea"])

    killed = door.fire({**good, "exit": "routed_out",
                        "bullets": [{"text": "nothing traced", "stratum": "code"}]}, **kw)
    ok("THE KILL STILL BERTHS", read_berth(killed["berth"])["exit"] == "routed_out")

    # ── zero seam change: a clean packet berths exactly as before ─────────────
    clean = door.fire(good, **kw)
    berth = read_berth(clean["berth"])
    ok("conforming birth berths", berth is not None and berth["skill"] == "intent")
    ok("the origin rides the berth",
       berth["answers"]["from_idea"] == "2026-08-04-a-real-idea")
    ok("the finding rides the birth", berth["finding_id"] == clean["finding_id"])

    recs = read_trace("skill:intent", root=traces)
    sends = [r for r in recs if r["event"] == "send_back"]
    ok("every refusal traced", len(sends) == 12, str(len(sends)))
    ok("refusal trace names the judge",
       all(r["data"].get("judge") == "intent-door" for r in sends))

    # ── the CLI ───────────────────────────────────────────────────────────────
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "CAIRN_LB_TRACE_ROOT": str(traces), "CAIRN_SKILL_BERTHS": str(berths)}
    bad = tmp / "bad.json"
    bad.write_text(json.dumps({**good, "from_idea": "never-captured"}))
    p = subprocess.run([sys.executable, str(_REPO / "skills/intent/door.py"), str(bad)],
                       capture_output=True, text=True, env=env)
    ok("CLI refusal: exit 2", p.returncode == 2, p.stderr[:200])
    ok("CLI refusal points at /idea on stderr", "/idea" in p.stderr, p.stderr[:200])

    live_after = live_trace.read_text() if live_trace.exists() else None
    ok("live trace untouched by this proof", live_after == live_before)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

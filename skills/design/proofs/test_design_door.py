"""PROOF — the design door refuses entry on nothing, on a corpse, and on a paragraph.

Teeth a hollow build could not pass (Law 8), every root injected. The door gates an
ENTRY rather than a finished packet, so its teeth are entry-shaped: the berth must
resolve, must come from the right door, and must not have been killed at birth.

The sharpest tooth is the CORPSE one. A berth that exists and reads cleanly but exited
``routed_out`` is the case a naive implementation passes — it is present, it is
well-formed, it is a real berth. Designing on it spends the resolver on a node the
cheapest gate in the system already turned away, which is exactly the waste Law 1 names.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/design/proofs/test_design_door.py
Run twice; never trust the first green.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))

from cairn.learning_block.learning_block import DoorRefused, read_trace  # noqa: E402
from cairn.skill_block import skill_block as sb                          # noqa: E402
from cairn.skill_block.skill_block import read_berth                     # noqa: E402

sys.path.insert(0, str(_REPO / "skills" / "design"))
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


BULLET = [{"text": "congruency lab: ticket-and-task is prior art", "stratum": "tree"}]


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="design-proof-"))
    traces, berths = tmp / "traces", tmp / "berths"
    kw = dict(trace_root=traces, berths=berths)

    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:design.jsonl"
    live_before = live_trace.read_text() if live_trace.exists() else None

    # ── fixtures: real berths, made through the real seam ─────────────────────
    intent_packet = {
        "from_idea": "none, because ideas/_charter+why.json records the split",
        "what": "x", "how": "y", "traces_to": "Law 1", "shape": "new track",
        "falsifier": "z", "exit": "routed_forward",
        "challenge": {k: "considered" for k in
                      ("better_approach", "prior_art", "hidden_assumption",
                       "real_collision", "back_up")},
        "bullets": [{"text": "t", "stratum": "code"}]}
    alive = sb.fire("intent", intent_packet, **kw)["berth"]
    corpse = sb.fire("intent", {**intent_packet, "exit": "routed_out"}, **kw)["berth"]
    sorted_berth = sb.fire("sorted", {
        "assumption_check": "a", "missing_check": "b", "falsifier_check": "c",
        "collision_check": "d", "node_class": "code-seam", "workflow": "w",
        "gates_bound": "g", "watchme": "none, because x", "children": "none, because y",
        "exit": "routed_out", "disposition": "back-to-design",
        "bullets": [{"text": "t", "stratum": "code"}]}, **kw)["berth"]

    good = {"intent_berth": alive, "entering_from": "intent",
            "open_questions": ["who owns the probe roster?"],
            "ready_when": "the gates can be bound", "bullets": BULLET}

    # ── the entry gate: every lack in ONE raise ───────────────────────────────
    try:
        door.fire({}, **kw)
        ok("empty packet refused", False, "the door opened a design session on nothing")
    except DoorRefused as exc:
        ok("entry gate: all five lacks in one raise",
           fields_of(exc) == ["bullets", "entering_from", "intent_berth",
                              "open_questions", "ready_when"], str(fields_of(exc)))

    # ── the berth judges ──────────────────────────────────────────────────────
    try:
        door.fire({**good, "intent_berth": str(tmp / "nope.json")}, **kw)
        ok("missing berth refused", False)
    except DoorRefused as exc:
        ok("missing berth refused", fields_of(exc) == ["intent_berth"])
        ok("missing-berth why names the path", "nope.json" in why_of(exc, "intent_berth"))

    try:
        door.fire({**good, "intent_berth": sorted_berth}, **kw)
        ok("wrong-skill berth refused", False)
    except DoorRefused as exc:
        ok("wrong-skill berth refused", fields_of(exc) == ["intent_berth"])
        ok("wrong-skill why names both doors",
           "'sorted'" in why_of(exc, "intent_berth") and "'intent'" in why_of(exc, "intent_berth"))

    try:
        door.fire({**good, "intent_berth": corpse}, **kw)
        ok("THE CORPSE TOOTH: routed_out berth refused", False,
           "the door designed on a node the trace question killed")
    except DoorRefused as exc:
        ok("THE CORPSE TOOTH: routed_out berth refused", fields_of(exc) == ["intent_berth"])
        ok("corpse why says a kill is a new birth, not a design session",
           "new birth" in why_of(exc, "intent_berth"))

    try:
        door.fire({**good, "intent_berth": "none, because we talked about it"}, **kw)
        ok("hollow exemption refused", False, "a plausible sentence opened the door")
    except DoorRefused as exc:
        ok("hollow exemption refused", fields_of(exc) == ["intent_berth"])
        ok("hollow-exemption why names the three referent kinds",
           all(k in why_of(exc, "intent_berth") for k in ("path", "ticket", "bin/cmd")))

    try:
        door.fire({**good, "intent_berth": "none"}, **kw)
        ok("bare 'none' refused", False)
    except DoorRefused as exc:
        ok("bare 'none' refused, distinctly from the exemption",
           "silence with extra words" in why_of(exc, "intent_berth"))

    res = door.fire({**good, "intent_berth":
                     "none, because ideas/_charter+why.json is the record"}, **kw)
    ok("referent-carrying exemption passes", read_berth(res["berth"]) is not None)

    # ── entering_from: the back-edge, made countable ──────────────────────────
    try:
        door.fire({**good, "entering_from": "we came back to it"}, **kw)
        ok("free-prose entry refused", False)
    except DoorRefused as exc:
        ok("free-prose entry refused", fields_of(exc) == ["entering_from"])
        ok("entry why names both legal values",
           "'intent'" in why_of(exc, "entering_from") and "sorted:" in why_of(exc, "entering_from"))

    try:
        door.fire({**good, "entering_from": f"sorted:{tmp / 'nope.json'}"}, **kw)
        ok("sorted return with unresolvable berth refused", False)
    except DoorRefused as exc:
        ok("sorted return with unresolvable berth refused",
           fields_of(exc) == ["entering_from"])

    back = door.fire({**good, "entering_from": f"sorted:{sorted_berth}"}, **kw)
    ok("a real return trip is recorded", read_berth(back["berth"])["answers"]
       ["entering_from"].startswith("sorted:"))
    ok("THE COUNTABLE TOOTH: the return trip is distinguishable from a first pass",
       read_berth(back["berth"])["answers"]["entering_from"] !=
       read_berth(res["berth"])["answers"]["entering_from"])

    # ── open_questions: a list, and a list of things ──────────────────────────
    try:
        door.fire({**good, "open_questions": "a paragraph about several things"}, **kw)
        ok("paragraph refused where a list belongs", False)
    except DoorRefused as exc:
        ok("paragraph refused where a list belongs", fields_of(exc) == ["open_questions"])
        ok("paragraph why names the plural problem",
           "wearing a plural" in why_of(exc, "open_questions"))

    try:
        door.fire({**good, "open_questions": ["real one", "  "]}, **kw)
        ok("blank list entry refused", False)
    except DoorRefused as exc:
        ok("blank list entry refused", fields_of(exc) == ["open_questions"])
        ok("blank-entry why names the index", "[1]" in why_of(exc, "open_questions"))

    # ── one pass, not a dribble ───────────────────────────────────────────────
    try:
        door.fire({"intent_berth": corpse, "entering_from": "nonsense",
                   "open_questions": "a paragraph", "bullets": BULLET}, **kw)
        ok("multi-lack refused", False)
    except DoorRefused as exc:
        ok("ONE PASS: flat and semantic lacks raised together",
           fields_of(exc) == ["entering_from", "intent_berth", "open_questions",
                              "ready_when"], str(fields_of(exc)))

    # ── the conforming opening ────────────────────────────────────────────────
    clean = door.fire(good, **kw)
    berth = read_berth(clean["berth"])
    ok("conforming opening berths", berth is not None and berth["skill"] == "design")
    ok("berth carries the work list",
       berth["answers"]["open_questions"] == good["open_questions"])
    ok("no exit is recorded — the step's exits are /sorted's",
       berth["exit"] is None, str(berth["exit"]))

    # ── the trace ─────────────────────────────────────────────────────────────
    recs = read_trace("skill:design", root=traces)
    sends = [r for r in recs if r["event"] == "send_back"]
    ok("every refusal traced", len(sends) == 11, str(len(sends)))
    ok("refusal trace names the judge",
       all(r["data"].get("judge") == "design-door" for r in sends))
    ok("every opening traced",
       len([r for r in recs if r["event"] == "door_pass"]) == 3)

    # ── the CLI ───────────────────────────────────────────────────────────────
    env = {**os.environ, "PYTHONPATH": str(_REPO),
           "CAIRN_LB_TRACE_ROOT": str(traces), "CAIRN_SKILL_BERTHS": str(berths)}
    bad = tmp / "bad.json"
    bad.write_text(json.dumps({"intent_berth": corpse, "entering_from": "intent",
                               "open_questions": ["q"], "ready_when": "r",
                               "bullets": BULLET}))
    p = subprocess.run([sys.executable, str(_REPO / "skills/design/door.py"), str(bad)],
                       capture_output=True, text=True, env=env)
    ok("CLI refusal: exit 2", p.returncode == 2, p.stderr[:200])
    ok("CLI refusal explains the corpse on stderr", "new birth" in p.stderr, p.stderr[:200])

    live_after = live_trace.read_text() if live_trace.exists() else None
    ok("live trace untouched by this proof", live_after == live_before)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

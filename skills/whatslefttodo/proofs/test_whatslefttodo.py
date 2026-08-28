"""PROOF — /whatslefttodo's door refuses a skipped gather AND a stale one.

Teeth a hollow build could not pass (Law 8). The skill's charter carried its debt in
exactly two halves — "nothing detects a /whatslefttodo that skipped a gather **or
reported a stale count**" — so a proof that only checked field presence would go green
having closed one of them, which is the shape of a tooth that passes because of the
defect.

**NOT ONE TOOTH ASSERTS A SNAPSHOT.** The world this door reads moves: the gate had 104
findings when the door was written and will not have 104 tomorrow. A tooth pinned to
that number goes red at the moment its condition is satisfied — the failure mode this
corpus has now met three times. So every refusal tooth injects the measurement and
asserts the RELATION (reported != measured => refused, both values named), and the
live-world tooth asserts only the SHAPE of what comes back.

The pass/refuse PAIR is what makes the pass non-tautological: the same packet, built
from the live world, is fired once whole (passes) and once with a single figure moved
(refused). A door that returned no lacks ever would pass the first and fail the second.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/whatslefttodo/proofs/test_whatslefttodo.py
Run twice; never trust the first green.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))

from cairn.machines.learning_block.learning_block import DoorRefused, read_trace   # noqa: E402
from cairn.machines.skill_block.skill_block import fire, judge_for, read_berth     # noqa: E402
from cairn.devices.tester.scratch import scratch_dir                             # noqa: E402

sys.path.insert(0, str(_REPO / "skills" / "whatslefttodo"))
import door  # noqa: E402

PASSES = 0


def ok(name: str, cond: bool, detail: str = ""):
    global PASSES
    if not cond:
        print(f"RED  {name}  {detail}")
        raise SystemExit(1)
    PASSES += 1
    print(f"  ok {name}")


def whys(lacks: list[dict], field: str) -> str:
    return " ".join(l["why"] for l in lacks if l["field"] == field)


def fields_of(exc: DoorRefused) -> list[str]:
    return sorted(l["field"] for l in (getattr(exc, "lacks", None) or []))


# A fixture WORLD — what the four readers would return at some instant. Injected rather
# than read, so the teeth below say what they mean instead of racing the live commons.
WORLD = {
    "rulings_count": 7,
    "rulings_oldest_id": "aaaa1111bbbb",
    "live_troubles": ["one-trouble", "two-trouble"],
    "open_questions": 3,
    "newest_slate": "2026-08-12-a-fixture-slate",
}

BULLETS = [{"text": "the gather ran; nothing surprised it", "stratum": "code"}]


def packet_for(world: dict) -> dict:
    """The packet an honest firing would carry against ``world``."""
    return {
        "rulings": {"ran": "bin/cmd/recordverdict",
                    "count": world["rulings_count"],
                    "oldest_id": world["rulings_oldest_id"]},
        "alarms": {"ran": ["bin/cmd/slate", "bin/cmd/probescan", "bin/cmd/test -q"],
                   "live_troubles": list(world["live_troubles"]),
                   "probes": "19 probes / 0 whole / 19 broken",
                   "proofs": "88 green, 1 red"},
        "questions": {"ran": "ls CairnCommons/questions/", "open": world["open_questions"]},
        "slate": {"ran": "bin/cmd/slate", "slate_id": world["newest_slate"]},
        "overview": "Rulings first: the gate is the bulk of it. My read of the order is …",
        "bullets": BULLETS,
        "exit": "routed_forward",
    }


def main() -> int:
    tmp = scratch_dir("whatslefttodo-proof-")
    traces, berths = tmp / "traces", tmp / "berths"

    live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:whatslefttodo.jsonl"
    live_trace_before = live_trace.read_text() if live_trace.exists() else None

    # ── the four gathers are the charter's four, not a second list ────────────
    charter = json.loads((_REPO / "skills/whatslefttodo/intention+why.json").read_text())
    contract = charter["input_contract"]
    ok("the door's INSTRUMENTS are exactly the charter's four gathers",
       sorted(door.INSTRUMENTS) == sorted(k for k in contract
                                          if k not in ("overview", "bullets", "exit")),
       f"{sorted(door.INSTRUMENTS)} vs {sorted(contract)}")
    # ONE STRICTNESS, TWO ENTRANCES. Not an identity check: the seam loads door.py by
    # path into its own module object, so `is` would compare two loads of one file and
    # fail for a reason that has nothing to do with strictness. What matters is that the
    # seam's judge and this one refuse the SAME packet the same way.
    seam_judge = judge_for("whatslefttodo")
    ok("the seam resolves a judge from the skill's own address", callable(seam_judge))
    drifted = packet_for(WORLD)
    drifted["rulings"]["count"] = WORLD["rulings_count"] + 5
    ok("the seam's judge and this one name the same lacks on the same packet",
       [l["field"] for l in seam_judge(drifted, world=WORLD)]
       == [l["field"] for l in door.judge_packet(drifted, world=WORLD)])

    # ── the flat contract: a skipped gather is a lack, every one in ONE raise ─
    try:
        fire("whatslefttodo", {}, trace_root=traces, berths=berths)
        ok("empty packet refused", False, "the door passed a firing with no gathers at all")
    except DoorRefused as exc:
        ok("entry gate: all seven fields named in one raise",
           fields_of(exc) == ["alarms", "bullets", "exit", "overview",
                              "questions", "rulings", "slate"], str(fields_of(exc)))

    # ── the instrument half: a gather reported without running its instrument ─
    p = packet_for(WORLD)
    p["rulings"] = {"count": 7, "oldest_id": "aaaa1111bbbb"}      # no 'ran'
    lacks = door.judge_packet(p, world=WORLD)
    ok("a gather with no 'ran' is refused", any(l["field"] == "rulings" for l in lacks))
    ok("and the refusal names the missing instrument",
       "recordverdict" in whys(lacks, "rulings"), whys(lacks, "rulings"))

    p = packet_for(WORLD)
    p["alarms"]["ran"] = ["bin/cmd/slate"]                        # two of three run
    lacks = door.judge_packet(p, world=WORLD)
    ok("a gather that ran SOME of its instruments is refused",
       any(l["field"] == "alarms" for l in lacks))
    ok("and the refusal names WHICH instruments went unrun",
       "probescan" in whys(lacks, "alarms") and "test" in whys(lacks, "alarms"),
       whys(lacks, "alarms"))

    # ── the STALE half — the part presence alone can never catch ──────────────
    p = packet_for(WORLD)
    p["rulings"]["count"] = WORLD["rulings_count"] - 1
    lacks = door.judge_packet(p, world=WORLD)
    ok("a stale rulings count is refused", any(l["field"] == "rulings" for l in lacks))
    ok("and the refusal names BOTH numbers, so the fix is one edit",
       "6" in whys(lacks, "rulings") and "7" in whys(lacks, "rulings"),
       whys(lacks, "rulings"))

    p = packet_for(WORLD)
    p["rulings"]["oldest_id"] = "not-the-oldest"
    lacks = door.judge_packet(p, world=WORLD)
    ok("a wrong oldest_id is refused — the id is the part a banner cannot supply",
       "aaaa1111bbbb" in whys(lacks, "rulings"), whys(lacks, "rulings"))

    p = packet_for(WORLD)
    p["alarms"]["live_troubles"] = ["one-trouble"]                # one cleared, or one missed
    lacks = door.judge_packet(p, world=WORLD)
    ok("a drifted live-trouble SET is refused, not just a wrong count",
       "two-trouble" in whys(lacks, "alarms"), whys(lacks, "alarms"))

    p = packet_for(WORLD)
    p["questions"]["open"] = 99
    lacks = door.judge_packet(p, world=WORLD)
    ok("a stale open-question count is refused",
       any(l["field"] == "questions" for l in lacks))
    ok("and the refusal says the lane is HALF the corpus by construction",
       "projector" in whys(lacks, "questions"), whys(lacks, "questions"))

    p = packet_for(WORLD)
    p["slate"]["slate_id"] = "2026-01-01-some-older-slate"
    lacks = door.judge_packet(p, world=WORLD)
    ok("a slate that is not the newest is refused",
       "2026-08-12-a-fixture-slate" in whys(lacks, "slate"), whys(lacks, "slate"))

    # ── the residue, held open rather than assumed away ───────────────────────
    p = packet_for(WORLD)
    p["alarms"].pop("probes")
    lacks = door.judge_packet(p, world=WORLD)
    ok("a missing probescan figure is refused — the un-re-run half still has to be there",
       "probes" in whys(lacks, "alarms"), whys(lacks, "alarms"))

    # ── THE HOLLOW TOOTH: an unreachable instrument must REFUSE, never pass ───
    blind = {"rulings_unreachable": "the gate could not be read — PermissionError()"}
    lacks = door.judge_packet(packet_for(WORLD), world=blind)
    ok("an instrument the judge cannot reach is a REFUSAL, not a quiet pass",
       any(l["field"] == "rulings" for l in lacks), str(lacks))
    ok("and it says so in the judge's own voice",
       "COULD NOT MEASURE" in whys(lacks, "rulings"), whys(lacks, "rulings"))

    # ── the pass, and it is not tautological: same packet, one figure moved ───
    ok("a current, complete packet draws no semantic lack",
       door.judge_packet(packet_for(WORLD), world=WORLD) == [])

    result = fire("whatslefttodo", packet_for(WORLD), trace_root=traces, berths=berths,
                  judge_kwargs={"world": WORLD})
    ok("a current firing berths", Path(result["berth"]).is_file(), result["berth"])
    berth = read_berth(result["berth"])
    ok("the berth carries the gathers it was fired on",
       berth["answers"]["rulings"]["oldest_id"] == WORLD["rulings_oldest_id"])
    ok("the berth carries the exit", berth["exit"] == "routed_forward")
    ok("a berth id rides the firing", bool(result["finding_id"]))

    recs = read_trace("skill:whatslefttodo", root=traces)
    events = [r["event"] for r in recs]
    ok("every refusal above was traced, not swallowed", events.count("send_back") >= 1,
       str(events))
    ok("the passing firing is traced", events.count("door_pass") == 1, str(events))

    # ── the LIVE world: shape asserted, never a value ─────────────────────────
    w = door.measure_the_world()
    ok("the live readers answer, or say why they could not",
       any(k in w for k in ("rulings_count", "rulings_unreachable")), str(sorted(w)))
    if "rulings_count" in w:
        ok("the live gate count is an int (invariant, not a number this tooth remembers)",
           isinstance(w["rulings_count"], int))
    if "live_troubles" in w:
        ok("the live trouble set is a sorted list of ids",
           isinstance(w["live_troubles"], list)
           and w["live_troubles"] == sorted(w["live_troubles"]))
    if "newest_slate" in w:
        ok("the newest slate is composed from bin/cmd/slate's own ranking",
           isinstance(w["newest_slate"], str) and w["newest_slate"]
           and not w["newest_slate"].startswith("_"))

    live_packet = {
        "rulings": {"ran": "bin/cmd/recordverdict", "count": w.get("rulings_count"),
                    "oldest_id": w.get("rulings_oldest_id")},
        "alarms": {"ran": ["bin/cmd/slate", "bin/cmd/probescan", "bin/cmd/test -q"],
                   "live_troubles": list(w.get("live_troubles") or []),
                   "probes": "measured elsewhere", "proofs": "measured elsewhere"},
        "questions": {"ran": "ls CairnCommons/questions/", "open": w.get("open_questions")},
        "slate": {"ran": "bin/cmd/slate", "slate_id": w.get("newest_slate")},
        "overview": "x", "bullets": BULLETS, "exit": "routed_forward",
    }
    ok("a packet built from the LIVE readers draws no lack",
       door.judge_packet(live_packet) == [], str(door.judge_packet(live_packet)))
    stale = json.loads(json.dumps(live_packet))
    stale["rulings"]["count"] = (w.get("rulings_count") or 0) + 1
    ok("and moving ONE figure in that same packet refuses it — the check bites",
       any(l["field"] == "rulings" for l in door.judge_packet(stale)))

    # ── nothing live was touched ──────────────────────────────────────────────
    live_after = live_trace.read_text() if live_trace.exists() else None
    ok("live trace untouched by this proof", live_after == live_trace_before)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""PROOF — the slate door refuses complete, writes only what passed, pollutes nothing.

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 skills/saveslate/proofs/test_slate_door.py
Run twice; never trust the first green.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))

from cairn.machines.learning_block.learning_block import DoorRefused, read_trace  # noqa: E402

sys.path.insert(0, str(_REPO / "skills" / "saveslate"))
import door  # noqa: E402

PASSES = 0
def ok(name, cond, detail=""):
    global PASSES
    if not cond:
        print(f"RED  {name}  {detail}")
        raise SystemExit(1)
    PASSES += 1
    print(f"  ok {name}")


def fields_of(exc): return [l["field"] for l in (getattr(exc, "lacks", None) or [])]


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        slates = tmp / "slates"; slates.mkdir()
        berths = tmp / "berths"; traces = tmp / "traces"
        HEADS = {"cairn": "aaa111", "CairnCommons": "bbb222"}
        roots = dict(heads=HEADS, slates_dir=slates, berths=berths, trace_root=traces)

        GOOD = {
            "slate_id": "2026-08-03-fixture-close",
            "at_sea": "fixture voyage at PROVED",
            "next_direction": "fixture next",
            "open_threads": ["one thread"],
            "instruments_read": {"git_heads": dict(HEADS),
                                 "cursors_touched": "t1 -> PROVED"},
            "bullets": [{"text": "fixture close", "stratum": "code"}],
            "exit": "routed_forward",
        }

        live_trace = Path.home() / ".cairn/devices/learning_block/0/traces/skill:saveslate.jsonl"
        live_before = live_trace.read_bytes() if live_trace.exists() else None

        # 1. stale heads refuse, naming live vs packet, and write NO slate — twice, same set
        stale = dict(GOOD, instruments_read={"git_heads": {"cairn": "old", "CairnCommons": "bbb222"}})
        for attempt in (1, 2):
            try:
                door.fire(stale, **roots)
                ok(f"stale heads refused (pass {attempt})", False)
            except DoorRefused as exc:
                msg = str(exc)
                ok(f"stale heads refused (pass {attempt})",
                   "never looked at the world" in msg and "old" in msg and "aaa111" in msg, msg)
        ok("refusal wrote no slate", not any(slates.iterdir()))

        # 2. missing git_heads refused with the instrument named
        headless = dict(GOOD, instruments_read={"cursors_touched": "x"})
        try:
            door.fire(headless, **roots)
            ok("headless refused", False)
        except DoorRefused as exc:
            ok("headless refused", "git rev-parse HEAD" in str(exc))

        # 3. extra keys refused naming the reader's closed set
        try:
            door.fire(dict(GOOD, how_this_session_went="great"), **roots)
            ok("extra key refused", False)
        except DoorRefused as exc:
            ok("extra key refused", "CLOSED SET" in str(exc) and
               "how_this_session_went" in str(exc))

        # 4. over-ceiling refused naming the standing cost and the measured corpus
        try:
            door.fire(dict(GOOD, at_sea="x" * (door.CEILING + 1)), **roots)
            ok("ceiling refused", False)
        except DoorRefused as exc:
            ok("ceiling refused", "standing tax" in str(exc) and "6,880" in str(exc))

        # 5. flat + semantic lacks in ONE refusal
        try:
            door.fire({k: v for k, v in stale.items() if k != "bullets"}, **roots)
            ok("flat+semantic one pass", False)
        except DoorRefused as exc:
            f = fields_of(exc)
            ok("flat+semantic one pass", "bullets" in f and "instruments_read" in f, f)

        # 6-8. a conforming close berths AND writes the slate with exactly the template keys
        result = door.fire(dict(GOOD), session="sess-1", **roots)
        ok("conforming close berths", bool(result.get("berth")) and Path(result["berth"]).exists())
        slate_path = Path(result["slate"])
        ok("the slate is written by the same act", slate_path.exists())
        rec = json.loads(slate_path.read_text())
        ok("the slate carries exactly the template keys",
           sorted(rec) == sorted(("id", "date", "written_at", "session", "author",
                                  "at_sea", "next_direction", "open_threads"))
           and rec["session"] == "sess-1" and rec["id"] == GOOD["slate_id"], rec)

        # 8b. written_at is the INSTANT, not the day again. The hollow build stamps
        # when.date() into it: the key exists, the shape looks right, and the reader
        # still cannot rank two slates written the same day — which is the entire
        # defect this field was added for (2026-08-03: three slates, one date, the
        # 15:50 one named current over the 16:41 one). So two fires on the SAME DAY
        # must produce written_at values that differ and order in write order.
        d1, d2 = datetime(2026, 8, 3, 15, 50, 12), datetime(2026, 8, 3, 16, 41, 35)
        r1 = door.fire(dict(GOOD, slate_id="2026-08-03-fixture-earlier"),
                       now=d1, **roots)
        r2 = door.fire(dict(GOOD, slate_id="2026-08-03-fixture-later"),
                       now=d2, **roots)
        e = json.loads(Path(r1["slate"]).read_text())
        l = json.loads(Path(r2["slate"]).read_text())
        ok("same-day writes share a date", e["date"] == l["date"] == "2026-08-03")
        ok("written_at still tells them apart",
           e["written_at"] != l["written_at"], (e["written_at"], l["written_at"]))
        ok("written_at orders in write order", e["written_at"] < l["written_at"],
           (e["written_at"], l["written_at"]))
        ok("written_at is the door's own instant, not a re-derived day",
           l["written_at"] == "2026-08-03T16:41:35", l["written_at"])

        # 8c. an author-supplied stamp is refused WITH THE TRUE WHY. The charter
        # template names written_at, so a packet-composer will plausibly supply it.
        # The refusal must not say "a key nothing reads" — the reader reads it;
        # it is refused because only the door may mint it (an author-supplied
        # value could backdate the record — the two-witness argument again).
        try:
            door.fire(dict(GOOD, slate_id="2026-08-03-fixture-backdate",
                           written_at="1999-01-01T00:00:00"), **roots)
            ok("author-supplied written_at refused", False)
        except DoorRefused as exc:
            ok("author-supplied written_at refused", "written_at" in fields_of(exc))
            ok("...with the true why, not 'a key nothing reads'",
               "backdate" in str(exc) and "nothing reads" not in str(exc), str(exc)[:200])
        ok("the backdate refusal wrote no slate",
           not (slates / "2026-08-03-fixture-backdate.json").exists())

        # 9. id collision refuses (a slate is never an overwrite)
        try:
            door.fire(dict(GOOD), **roots)
            ok("id collision refused", False)
        except DoorRefused as exc:
            ok("id collision refused", "never an overwrite" in str(exc))

        # 10. both edges traced in the injected root, judge named
        recs = read_trace("skill:saveslate", root=traces)
        ok("both edges traced",
           any(r["event"] == "door_pass" for r in recs) and
           any(r["event"] == "send_back" and r["data"].get("judge") == "slate-door"
               for r in recs))

        # 11. the coinage is named at both mouths
        charter = json.loads((_REPO / "skills/saveslate/intention+why.json").read_text())
        ok("the coined convention is written down",
           "coined" in charter["input_contract"]["instruments_read"]
           and "coined" in (door.judge_packet.__doc__ or "") + (door.__doc__ or ""))

        # 12. live default heads read the real repos (shape only — hashes are 40-hex)
        live = door.live_git_heads()
        ok("live heads provider reads the world",
           all(isinstance(v, str) and len(v) == 40 for v in live.values()), live)

        # 13. the live trace is byte-identical across the whole proof run
        live_after = live_trace.read_bytes() if live_trace.exists() else None
        ok("live trace untouched by the proof", live_before == live_after)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

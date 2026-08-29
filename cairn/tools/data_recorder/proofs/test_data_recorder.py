"""Proof: data_recorder — write/read/clear on structured feedback records.

Teeth a hollow build could not pass: every tooth exercises the real module and
asserts observable behavior, not structure.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

PASS = 0
FAIL = 0


def ok(label: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  pass  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}  — {detail}")


def run() -> int:
    global PASS, FAIL
    PASS = FAIL = 0

    from cairn.tools.data_recorder.data_recorder import DataRecorder, REQUIRED_KEYS

    with tempfile.TemporaryDirectory() as td:
        dr = DataRecorder(td)

        # 1. read() on empty returns empty list
        ok("empty read returns []", dr.read() == [], repr(dr.read()))

        # 2. write(record) returns a string id
        rec = {
            "finding": "test finding",
            "inspector_target": "test_inspector",
            "probe_source": "test_probe",
            "timestamp": "2026-08-28T12:00:00+00:00",
        }
        rid = dr.write(rec)
        ok("write returns a string id", isinstance(rid, str) and len(rid) > 0, repr(rid))

        # 3. read() after write returns the record with its id
        records = dr.read()
        ok("read after write returns 1 record", len(records) == 1, repr(len(records)))
        ok("record has the assigned id", records[0].get("id") == rid, repr(records[0].get("id")))
        ok("record carries the finding", records[0].get("finding") == "test finding",
           repr(records[0].get("finding")))

        # 4. write a second record
        rec2 = {
            "finding": "second finding",
            "inspector_target": "test_inspector",
            "probe_source": "test_probe_2",
            "timestamp": "2026-08-28T12:01:00+00:00",
        }
        rid2 = dr.write(rec2)
        ok("two writes produce different ids", rid != rid2, f"{rid} == {rid2}")
        records = dr.read()
        ok("read returns 2 records after 2 writes", len(records) == 2, repr(len(records)))

        # 5. clear(ids) removes only the named ids
        removed = dr.clear([rid])
        ok("clear returns count of removed", removed == 1, repr(removed))
        records = dr.read()
        ok("after clear, only second record remains", len(records) == 1, repr(len(records)))
        ok("remaining record is the second one", records[0].get("id") == rid2,
           repr(records[0].get("id")))

        # 6. clear all remaining
        removed = dr.clear([rid2])
        ok("clear last record", removed == 1, repr(removed))
        records = dr.read()
        ok("after clearing all, read returns []", records == [], repr(records))

        # 7. clear on empty is a no-op
        removed = dr.clear(["nonexistent-id"])
        ok("clear nonexistent id returns 0", removed == 0, repr(removed))

        # 8. JSONL format — each write is one line
        dr2 = DataRecorder(os.path.join(td, "jsonl_test"))
        dr2.write({"finding": "a", "inspector_target": "t", "probe_source": "p",
                    "timestamp": "2026-01-01T00:00:00+00:00"})
        dr2.write({"finding": "b", "inspector_target": "t", "probe_source": "p",
                    "timestamp": "2026-01-01T00:01:00+00:00"})
        raw = dr2.path.read_text(encoding="utf-8")
        lines = [l for l in raw.splitlines() if l.strip()]
        ok("JSONL: 2 writes produce 2 lines", len(lines) == 2, repr(len(lines)))
        for i, line in enumerate(lines):
            try:
                json.loads(line)
                ok(f"JSONL: line {i} is valid JSON", True)
            except json.JSONDecodeError as e:
                ok(f"JSONL: line {i} is valid JSON", False, str(e))

        # 9. schema enforcement — missing required keys refused
        for key in ("finding", "inspector_target", "probe_source"):
            bad = dict(rec)
            del bad[key]
            try:
                dr.write(bad)
                ok(f"missing {key} refused", False, "write accepted without required key")
            except (ValueError, TypeError):
                ok(f"missing {key} refused", True)

        # 10. non-dict refused
        try:
            dr.write("not a dict")
            ok("non-dict refused", False, "write accepted a string")
        except TypeError:
            ok("non-dict refused", True)

        # 11. timestamp auto-populated if missing
        dr3 = DataRecorder(os.path.join(td, "ts_test"))
        no_ts = {"finding": "f", "inspector_target": "t", "probe_source": "p"}
        dr3.write(no_ts)
        recs = dr3.read()
        ok("timestamp auto-populated", "timestamp" in recs[0] and recs[0]["timestamp"],
           repr(recs[0].get("timestamp")))

        # 12. multiple inspectors get separate paths (the holder assembles one per inspector)
        dr_a = DataRecorder(os.path.join(td, "inspector_a"))
        dr_b = DataRecorder(os.path.join(td, "inspector_b"))
        dr_a.write({"finding": "for a", "inspector_target": "a", "probe_source": "p",
                     "timestamp": "2026-01-01T00:00:00+00:00"})
        dr_b.write({"finding": "for b", "inspector_target": "b", "probe_source": "p",
                     "timestamp": "2026-01-01T00:00:00+00:00"})
        ok("separate inspectors get separate records",
           len(dr_a.read()) == 1 and len(dr_b.read()) == 1
           and dr_a.read()[0]["finding"] == "for a"
           and dr_b.read()[0]["finding"] == "for b",
           f"a={len(dr_a.read())} b={len(dr_b.read())}")

        # 13. clear with empty list is no-op
        before = dr_a.read()
        dr_a.clear([])
        after = dr_a.read()
        ok("clear([]) is no-op", before == after, f"before={len(before)} after={len(after)}")

    print(f"\n{PASS + FAIL} teeth: {PASS} pass, {FAIL} fail")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(run())

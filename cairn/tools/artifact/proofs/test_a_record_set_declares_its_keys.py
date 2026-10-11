"""Proof for ticket 1fc53d5d96cc — the artifact door refuses a key a record set does not declare.

The plan holds the plan (Akien 2026-10-09/10): a ticket is rewritten in place and its trail goes
to the .log.jsonl beside it. cast_ticket already refuses an undeclared key at casting; every
OTHER writer of a ticket (set_phase, rehearse --decide, a hand) went through the door with no
such check. The tickets record set now declares ``keys_from`` and the door reads it.

1. a ticket body with only declared keys lands, journaled;
2. a body with one extra key is refused naming it and pointing at the log; file and journal
   unchanged;
3. with no charter, or a charter lacking the field, every ticket write is refused; the charter
   file itself writes freely.

All on a SCRATCH CairnCommons root (``set_diagnostic_roots``) with its own charter. The live
jurisdiction is read, never written. ``artifact`` is imported inside ``main``.

Run bare:  PYTHONPATH=. python3 cairn/tools/artifact/proofs/test_a_record_set_declares_its_keys.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "1fc53d5d96cc": {
        "1": "a_body_of_declared_keys_lands",
        "2": "an_extra_key_is_refused_by_name",
        "3": "no_charter_refuses_and_the_charter_writes_freely",
    },
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail[:300]}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _body(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    from cairn.tools.artifact import artifact as A
    with tempfile.TemporaryDirectory(prefix="cairn-record-keys-proof-") as d:
        commons = Path(d) / "CairnCommons"
        tickets = commons / "tickets"
        tickets.mkdir(parents=True)
        charter = tickets / "_charter+why.json"
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
        try:
            A.write(charter, _body({"plan_fields": ["id", "title"]}), verb="cast", why="proof charter")
            journal = A.journal_path(commons)
            t = tickets / "aaaaaaaaaaa1-a-plan.json"

            name = PROVES["1fc53d5d96cc"]["1"]
            try:
                out = A.write(t, _body({"id": "aaaaaaaaaaa1", "title": "a plan"}), verb="cast", why="proof")
                check(name, out["journaled"] and t.exists(), json.dumps(out)[:200])
            except Exception as exc:  # noqa: BLE001
                check(name, False, f"{type(exc).__name__}: {exc}")

            name = PROVES["1fc53d5d96cc"]["2"]
            before, jbefore = t.read_bytes(), journal.read_bytes()
            try:
                A.write(t, _body({"id": "aaaaaaaaaaa1", "title": "a plan", "notes_trail": "x"}),
                        verb="cast", why="proof")
                check(name, False, "the extra key was admitted")
            except A.Refused as exc:
                msg = str(exc)
                check(name, "notes_trail" in msg and ".log.jsonl" in msg
                      and t.read_bytes() == before and journal.read_bytes() == jbefore, msg)

            name = PROVES["1fc53d5d96cc"]["3"]
            results = {}
            A.write(charter, _body({"other_field": ["id"]}), verb="cast", why="proof: field gone")
            results["charter_writes_without_the_field"] = True
            for label in ("field_missing", "charter_missing"):
                if label == "charter_missing":
                    A.remove(charter, why="proof: charter gone")
                try:
                    A.write(tickets / f"aaaaaaaaaaa2-{label}.json", _body({"id": "aaaaaaaaaaa2"}),
                            verb="cast", why="proof")
                    results[label] = "admitted"
                except A.Refused as exc:
                    results[label] = "refused" if "plan_fields" in str(exc) else f"refused-elsewise: {exc}"
            A.write(charter, _body({"plan_fields": ["id"]}), verb="cast", why="proof: charter back")
            results["charter_rewritten"] = charter.exists()
            check(name, results == {"charter_writes_without_the_field": True, "field_missing": "refused",
                                    "charter_missing": "refused", "charter_rewritten": True},
                  json.dumps(results))
        finally:
            A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

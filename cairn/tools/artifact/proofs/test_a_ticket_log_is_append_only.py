#!/usr/bin/env python3
"""Proof that the artifact door keeps a ticket log append-only (9df0f230a087).

WHAT IT PROVES: a ticket is two files (Akien 2026-10-10, "Flat plan + .log.jsonl"): the plan
``tickets/<id>-<slug>.json``, rewritten in place, and the log ``tickets/<id>-<slug>.log.jsonl``
beside it, one JSON object per line, only ever grown. The log is a record of truth (Law 7), so
"only ever grown" is the door's rule, judged by byte prefix: the new bytes start with the old
ones, and what they add is whole lines, each a JSON object.

Teeth, one per falsifier clause (PROVES below), over a scratch world (``set_diagnostic_roots``):
  (1) a log is created through write() with one object line and journals; a second write equal
      to old + one more object line lands and journals;
  (2) a write that changes an earlier byte, one that drops an earlier byte, a tail without a
      trailing newline, a tail line that is not JSON and a tail line that is a JSON list each
      raise Refused, and the file and journal stay byte-identical;
  (3) the jurisdiction classifies tickets/x-y.log.jsonl as a record and tickets/x-y.json still
      as one, and the other tickets/ names keep their classification (fnmatch '*.json' does not
      match a .log.jsonl name, measured here).

    bin/cairn test cairn/tools/artifact/proofs/test_a_ticket_log_is_append_only.py
"""

from __future__ import annotations

import fnmatch
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

# Bound at CALL time, never at import, so a reverted subject reds the teeth instead of
# crashing the reader (the seam test_a_json_record_lands_in_one_canonical_form.py uses).
A = None  # type: ignore[assignment]

PROVES = {"9df0f230a087": {
    "1": "test_a_log_is_created_and_appended_through_the_door",
    "2": "test_every_non_append_write_is_refused_and_nothing_moves",
    "3": "test_the_jurisdiction_names_a_ticket_log_as_a_record",
}}

FAILURES: list[str] = []
LOG = "tickets/abc123def456-a-proof-world.log.jsonl"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _line(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False) + "\n"


def _world(tmp: Path) -> Path:
    commons = tmp / "CairnCommons"
    (commons / "tickets").mkdir(parents=True)
    cairn = tmp / "cairn"
    cairn.mkdir()
    for r in (commons, cairn):
        subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    return commons


def _journal(commons: Path) -> bytes:
    j = A.journal_path(commons)
    return j.read_bytes() if j.exists() else b""


def test_a_log_is_created_and_appended_through_the_door(commons: Path) -> None:
    log = commons / LOG
    first = _line({"kind": "decision", "n": 1, "text": "the first line"})
    second = first + _line({"kind": "decision", "n": 2, "text": "the second line"})
    try:
        out1 = A.write(log, first, verb="append", why="proof: create the log")
        out2 = A.write(log, second, verb="append", why="proof: append one line")
    except A.Refused as exc:
        check("test_a_log_is_created_and_appended_through_the_door", False, f"refused: {exc}")
        return
    paths = [json.loads(x).get("path") for x in _journal(commons).decode().splitlines()]
    ok = (out1["journaled"] and out2["journaled"] and log.read_text() == second
          and paths.count(LOG) == 2)
    check("test_a_log_is_created_and_appended_through_the_door", ok,
          f"journaled {out1['journaled']}/{out2['journaled']}, journal names the log {paths.count(LOG)}x")


def test_every_non_append_write_is_refused_and_nothing_moves(commons: Path) -> None:
    log = commons / "tickets" / "def456abc123-refusals.log.jsonl"
    standing = _line({"kind": "decision", "n": 1, "text": "standing"}) + _line({"n": 2})
    A.write(log, standing, verb="append", why="proof: the standing log")
    bad = {
        "a changed earlier byte": standing.replace("standing", "STANDING") + _line({"n": 3}),
        "a dropped earlier byte": standing[1:] + _line({"n": 3}),
        "a tail without trailing newline": standing + json.dumps({"n": 3}),
        "a tail line that is not JSON": standing + "not json at all\n",
        "a tail line that is a JSON list": standing + "[1, 2, 3]\n",
    }
    landed = []
    for what, body in bad.items():
        before, journal = log.read_bytes(), _journal(commons)
        try:
            A.write(log, body, verb="append", why=f"proof: {what}")
        except A.Refused as exc:
            if not (log.read_bytes() == before and _journal(commons) == journal and str(log) in str(exc)):
                landed.append(f"{what}: refused but something moved")
            continue
        landed.append(f"{what}: the door wrote it")
    check("test_every_non_append_write_is_refused_and_nothing_moves", not landed, "; ".join(landed))


def test_the_jurisdiction_names_a_ticket_log_as_a_record(commons: Path) -> None:
    t = commons / "tickets"
    names = {"x-y.log.jsonl": True, "x-y.json": True, "x-y.md": False, "x-y.jsonl.bak": False,
             "sub/x-y.log.jsonl": False}
    off = [n for n, want in names.items() if (A.locate(t / n) is not None) != want]
    # The plan's own rule cannot be what admits a log: '*.json' does not match '.log.jsonl'.
    plan_rule_matches_log = fnmatch.fnmatchcase("x-y.log.jsonl", "*.json")
    check("test_the_jurisdiction_names_a_ticket_log_as_a_record",
          not off and not plan_rule_matches_log,
          f"misclassified {off}; '*.json' matches a log: {plan_rule_matches_log}")


def main() -> int:
    global A
    try:
        from cairn.tools.artifact import artifact as door
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject cairn.tools.artifact.artifact does not load: {exc!r}")
        for n in PROVES["9df0f230a087"].values():
            check(n, False, "subject absent")
        return 1
    A = door
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-ticket-log-proof-") as d:
            tmp = Path(d)
            try:
                commons = _world(tmp)
                test_a_log_is_created_and_appended_through_the_door(commons)
                test_every_non_append_write_is_refused_and_nothing_moves(commons)
                test_the_jurisdiction_names_a_ticket_log_as_a_record(commons)
            finally:
                A.set_diagnostic_roots(None)
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["9df0f230a087"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

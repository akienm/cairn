#!/usr/bin/env python3
"""Proof that the artifact door refuses a history row without the `standing` floor (62a57b781efc).

WHAT IT PROVES, and the reason is a measured leak: on 2026-10-02 two class-space history rows
without ``standing`` (tester seq 64, counting_block seq 2) landed through ``artifact.write`` with
verb ``append`` from scratch scripts, past ``projector.append_entry``'s floor
(``projector.UNIVERSAL_REQUIRED``). The floor lived one door up, so at the door beneath it the
floor was policy (Law 4). Parent: 471aa05ba639.

Teeth, one per falsifier clause (PROVES below), over a scratch world (``set_diagnostic_roots``):
  (1) a history.json write introducing a row without standing is REFUSED, and the file's bytes
      are unchanged;
  (2) a write introducing a row carrying standing lands;
  (3) a write that keeps an old standing-less row untouched and appends a row carrying standing
      lands — rows already standing on disk are not re-judged.

    bin/cairn test cairn/tools/artifact/proofs/test_a_history_row_without_standing_is_refused.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

# Bound at CALL time, never at import, so a reverted subject reds the teeth instead of
# crashing the reader (the same seam test_artifact_door.py uses).
A = None  # type: ignore[assignment]

PROVES = {"62a57b781efc": {
    "1": "test_a_row_without_standing_is_refused_and_nothing_lands",
    "2": "test_a_row_carrying_standing_lands",
    "3": "test_an_old_row_already_standing_is_not_re_judged",
}}

FAILURES: list[str] = []
ROW1 = {"from": "THINKME", "to": "TICKETME", "standing": "TICKETME", "ticket": "abc123def456",
        "at": "2026-10-06T00:00:00", "seq": 1}
BARE = {"event": "a row a script wrote past the projector", "ticket": "abc123def456",
        "at": "2026-10-06T00:01:00", "seq": 2}
ROW3 = {"from": "TICKETME", "to": "BUILDME", "standing": "BUILDME", "ticket": "abc123def456",
        "at": "2026-10-06T00:02:00", "seq": 3}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _body(rows) -> str:
    return json.dumps(rows, indent=2, ensure_ascii=False) + "\n"


def _world(tmp: Path) -> Path:
    commons = tmp / "CairnCommons"
    commons.mkdir()
    cairn = tmp / "cairn"
    (cairn / "tools" / "fixture_component").mkdir(parents=True)
    for r in (commons, cairn):
        subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    return cairn


def _history(cairn: Path, name: str) -> Path:
    d = cairn / "tools" / name
    d.mkdir(parents=True, exist_ok=True)
    return d / "history.json"


def test_a_row_without_standing_is_refused_and_nothing_lands(cairn: Path) -> None:
    name = "test_a_row_without_standing_is_refused_and_nothing_lands"
    h = _history(cairn, "refuse_component")
    A.write(h, _body([ROW1]), verb="append", why="proof: the standing history")
    before = h.read_bytes()
    try:
        A.write(h, _body([ROW1, BARE]), verb="append", why="proof: a row the door must refuse")
    except A.Refused as exc:
        ok = h.read_bytes() == before and "standing" in str(exc)
        check(name, ok, f"refused: {str(exc)[:160]}" if ok else "the file moved")
        return
    check(name, False, "the door wrote a row without standing")


def test_a_row_carrying_standing_lands(cairn: Path) -> None:
    name = "test_a_row_carrying_standing_lands"
    h = _history(cairn, "land_component")
    try:
        A.write(h, _body([ROW1]), verb="append", why="proof: the first row")
        out = A.write(h, _body([ROW1, ROW3]), verb="append", why="proof: a row carrying standing")
    except A.Refused as exc:
        check(name, False, f"refused: {str(exc)[:160]}")
        return
    check(name, out["journaled"] and json.loads(h.read_text()) == [ROW1, ROW3])


def test_an_old_row_already_standing_is_not_re_judged(cairn: Path) -> None:
    name = "test_an_old_row_already_standing_is_not_re_judged"
    h = _history(cairn, "old_row_component")
    # The old row is planted on disk as the pre-journal exhibit is (diagnostic_inspector seq 4):
    # it was never judged by this door, and keeping it must not refuse the next append.
    h.write_text(_body([ROW1, BARE]))
    try:
        out = A.write(h, _body([ROW1, BARE, ROW3]), verb="append", why="proof: append beside an old row")
    except A.Refused as exc:
        check(name, False, f"refused: {str(exc)[:160]}")
        return
    check(name, out["journaled"] and json.loads(h.read_text()) == [ROW1, BARE, ROW3])


def main() -> int:
    global A
    try:
        from cairn.tools.artifact import artifact as door
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject cairn.tools.artifact.artifact does not load: {exc!r}")
        for n in PROVES["62a57b781efc"].values():
            check(n, False, "subject absent")
        return 1
    A = door
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-history-standing-proof-") as d:
            tmp = Path(d)
            try:
                cairn = _world(tmp)
                test_a_row_without_standing_is_refused_and_nothing_lands(cairn)
                test_a_row_carrying_standing_lands(cairn)
                test_an_old_row_already_standing_is_not_re_judged(cairn)
            finally:
                A.set_diagnostic_roots(None)
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["62a57b781efc"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

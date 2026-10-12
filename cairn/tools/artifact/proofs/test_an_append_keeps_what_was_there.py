#!/usr/bin/env python3
"""Proof that the artifact door refuses an append that drops what a record already held (a742af217819).

WHAT IT PROVES: 9528475c replaced cairn/devices/cairn/machines/bus/history.json (29 entries) with
one entry; the door journaled it as verb ``append`` and the commit passed. An append is a promise
that what stood still stands. So a verb-``append`` write to a ``.json`` record whose current value
is a JSON list must be a list that begins with every current element, unchanged and in order; the
refusal names the first index that differs or is missing, and nothing is written or journaled.
A record whose current value is not a list (projector's state.json, a dict re-projected under verb
append on every history append) is not judged by this rule, and neither is any other verb.

Teeth, one per falsifier clause (PROVES below), over a scratch world (``set_diagnostic_roots``):
  (1) an absent history lands under append; old + [x] lands and journals;
  (2) [x] over a 3-entry list, an append that edits entry 1, and a dict body over the list are
      each refused naming the index or the shape and the file, file and journal unchanged;
  (3) the same truncating body under verb 'cast' lands, and an append over a record whose
      current value is a dict (a state.json) lands.

    bin/cairn test cairn/tools/artifact/proofs/test_an_append_keeps_what_was_there.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

# Bound at CALL time, never at import, so a reverted subject reds the teeth instead of
# crashing the reader (the seam test_a_ticket_log_is_append_only.py uses).
A = None  # type: ignore[assignment]

PROVES = {"a742af217819": {
    "1": "test_an_append_that_keeps_every_entry_lands",
    "2": "test_an_append_that_drops_or_edits_an_entry_is_refused",
    "3": "test_cast_and_a_non_list_record_are_not_judged",
}}

FAILURES: list[str] = []


def _row(seq: int, text: str = "") -> dict:
    return {"from": "THINKME", "to": "TICKETME", "standing": "TICKETME", "ticket": "abc123def456",
            "at": f"2026-10-11T00:00:{seq:02d}", "seq": seq, "note": text or f"row {seq}"}


def _body(doc) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _world(tmp: Path) -> Path:
    commons = tmp / "CairnCommons"
    commons.mkdir()
    cairn = tmp / "cairn"
    for c in ("keeps", "refuses", "cast_component", "dict_component"):
        (cairn / "tools" / c).mkdir(parents=True)
    for r in (commons, cairn):
        subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    return cairn


def _journal(cairn: Path) -> bytes:
    j = A.journal_path(cairn)
    return j.read_bytes() if j.exists() else b""


def test_an_append_that_keeps_every_entry_lands(cairn: Path) -> None:
    h = cairn / "tools" / "keeps" / "history.json"
    try:
        out1 = A.write(h, _body([_row(1)]), verb="append", why="proof: the first row")
        out2 = A.write(h, _body([_row(1), _row(2)]), verb="append", why="proof: one more row")
    except A.Refused as exc:
        check("test_an_append_that_keeps_every_entry_lands", False, f"refused: {exc}")
        return
    ok = (out1["journaled"] and out2["journaled"]
          and json.loads(h.read_text()) == [_row(1), _row(2)])
    check("test_an_append_that_keeps_every_entry_lands", ok,
          f"journaled {out1['journaled']}/{out2['journaled']}")


def test_an_append_that_drops_or_edits_an_entry_is_refused(cairn: Path) -> None:
    h = cairn / "tools" / "refuses" / "history.json"
    standing = [_row(1), _row(2), _row(3)]
    A.write(h, _body(standing), verb="append", why="proof: the standing history")
    bad = {
        "[x] over three entries": ([_row(4)], "index 0"),
        "an edit of entry 1": ([_row(1), _row(2, "rewritten"), _row(3), _row(4)], "index 1"),
        "a dict body over the list": ({"records": standing}, "dict"),
    }
    landed = []
    for what, (body, names) in bad.items():
        before, journal = h.read_bytes(), _journal(cairn)
        try:
            A.write(h, _body(body), verb="append", why=f"proof: {what}")
        except A.Refused as exc:
            msg = str(exc)
            if not (h.read_bytes() == before and _journal(cairn) == journal):
                landed.append(f"{what}: refused but something moved")
            elif str(h) not in msg or names not in msg:
                landed.append(f"{what}: refusal does not name the file and {names!r}: {msg}")
            continue
        landed.append(f"{what}: the door wrote it")
    check("test_an_append_that_drops_or_edits_an_entry_is_refused", not landed, "; ".join(landed))


def test_cast_and_a_non_list_record_are_not_judged(cairn: Path) -> None:
    h = cairn / "tools" / "cast_component" / "history.json"
    s = cairn / "tools" / "dict_component" / "state.json"
    try:
        A.write(h, _body([_row(1), _row(2), _row(3)]), verb="append", why="proof: the standing history")
        cast = A.write(h, _body([_row(4)]), verb="cast", why="proof: a cast is not an append")
        A.write(s, _body({"cursor": _row(1), "count": 1}), verb="append", why="proof: a state")
        dict_ = A.write(s, _body({"cursor": _row(2), "count": 2}), verb="append", why="proof: re-projected")
    except A.Refused as exc:
        check("test_cast_and_a_non_list_record_are_not_judged", False, f"refused: {exc}")
        return
    ok = cast["journaled"] and dict_["journaled"] and json.loads(h.read_text()) == [_row(4)]
    check("test_cast_and_a_non_list_record_are_not_judged", ok,
          f"cast journaled {cast['journaled']}, dict append journaled {dict_['journaled']}")


def main() -> int:
    global A
    try:
        from cairn.tools.artifact import artifact as door
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject cairn.tools.artifact.artifact does not load: {exc!r}")
        for n in PROVES["a742af217819"].values():
            check(n, False, "subject absent")
        return 1
    A = door
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-append-keeps-proof-") as d:
            tmp = Path(d)
            try:
                cairn = _world(tmp)
                test_an_append_that_keeps_every_entry_lands(cairn)
                test_an_append_that_drops_or_edits_an_entry_is_refused(cairn)
                test_cast_and_a_non_list_record_are_not_judged(cairn)
            finally:
                A.set_diagnostic_roots(None)
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["a742af217819"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

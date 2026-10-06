#!/usr/bin/env python3
"""Proof that the artifact door writes a JSON record of truth in one canonical form, or refuses it (f9ba6c89844d).

WHAT IT PROVES, and the reason is a measured stall: on 2026-10-05 ``cairn artifact write``
accepted an indent=1 ticket (48c0c58a1714); the shape check that lived only in transitions
fired at the next phase write, after commit, and a whole session's crossing stalled until
the ticket was reshaped by hand. The canonical form is the one ``transitions._ticket_shape``
already demands of a ticket and the census of 2026-10-06 measured across both repos:
``json.dumps(doc, indent=2, ensure_ascii=<either>)`` with or without one trailing newline.

Teeth, one per falsifier clause (PROVES below), over a scratch world (``set_diagnostic_roots``):
  (1) an indent=1 body to a journaled .json path is REFUSED, and the file and journal are unchanged;
  (2) an unparseable body to a journaled .json path is REFUSED, the same;
  (3) the canonical body lands and journals, in all four shapes (ensure_ascii x trailing newline);
  (4) a .md under tickets/ and a .json outside the jurisdiction are written as before, unjournaled,
      whatever their bytes (the jurisdiction declares no .md record, measured 2026-10-06);
  census: every journaled .json record in the LIVE roots is canonical (an invariant over live
      data, never a snapshot of counts).

    bin/cairn test cairn/tools/artifact/proofs/test_a_json_record_lands_in_one_canonical_form.py
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

PROVES = {"f9ba6c89844d": {
    "1": "test_an_indent_1_record_is_refused_and_nothing_lands",
    "2": "test_an_unparseable_record_is_refused_and_nothing_lands",
    "3": "test_the_canonical_record_lands_and_journals",
    "4": "test_a_non_json_or_unjournaled_write_is_as_before",
    "census": "test_every_live_json_record_is_canonical",
}}

FAILURES: list[str] = []
TICKET = {"id": "abc123def456", "title": "a proof world — ticket", "list": ["a", "b"]}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _canonical(doc, ensure_ascii=False, newline=True) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=ensure_ascii) + ("\n" if newline else "")


def _world(tmp: Path) -> Path:
    commons = tmp / "CairnCommons"
    (commons / "tickets").mkdir(parents=True)
    cairn = tmp / "cairn"
    cairn.mkdir()
    for r in (commons, cairn):
        subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    return commons


def _refused_and_untouched(name: str, commons: Path, body: str) -> None:
    t = commons / "tickets" / "abc123def456-a-proof-world.json"
    A.write(t, _canonical(TICKET), verb="cast", why="proof: the standing canonical record")
    before, journal = t.read_bytes(), A.journal_path(commons).read_bytes()
    try:
        A.write(t, body, verb="cast", why="proof: a body the door must refuse")
    except A.Refused as exc:
        ok = t.read_bytes() == before and A.journal_path(commons).read_bytes() == journal
        check(name, ok and str(t) in str(exc), f"refused: {str(exc)[:160]}" if ok else "the file or journal moved")
        return
    check(name, False, f"the door wrote it: {body[:60]!r}")


def test_an_indent_1_record_is_refused_and_nothing_lands(commons: Path) -> None:
    _refused_and_untouched("test_an_indent_1_record_is_refused_and_nothing_lands", commons,
                           json.dumps(TICKET, indent=1) + "\n")


def test_an_unparseable_record_is_refused_and_nothing_lands(commons: Path) -> None:
    _refused_and_untouched("test_an_unparseable_record_is_refused_and_nothing_lands", commons,
                           '{\n  "id": "abc123def456",\n}\n')


def test_the_canonical_record_lands_and_journals(commons: Path) -> None:
    landed = []
    for i, (ea, nl) in enumerate(((False, True), (False, False), (True, True), (True, False))):
        t = commons / "tickets" / f"canon{i:07d}-shape.json"
        body = _canonical(TICKET, ensure_ascii=ea, newline=nl)
        try:
            out = A.write(t, body, verb="cast", why=f"proof: canonical shape ascii={ea} newline={nl}")
        except A.Refused as exc:
            landed.append(f"ascii={ea} newline={nl} refused: {exc}")
            continue
        if not (out["journaled"] and t.read_text() == body):
            landed.append(f"ascii={ea} newline={nl} not journaled")
    check("test_the_canonical_record_lands_and_journals", not landed, "; ".join(landed)[:200])


def test_a_non_json_or_unjournaled_write_is_as_before(commons: Path, tmp: Path) -> None:
    bad = json.dumps(TICKET, indent=1)
    md = commons / "tickets" / "notes.md"
    out_md = A.write(md, "# a note, not JSON at all\n", verb="cast", why="proof: a non-.json file")
    outside = tmp / "scratch.json"
    out_out = A.write(outside, bad, verb="cast", why="proof: outside the jurisdiction")
    ok = (not out_md["journaled"] and md.read_text() == "# a note, not JSON at all\n"
          and not out_out["journaled"] and outside.read_text() == bad)
    check("test_a_non_json_or_unjournaled_write_is_as_before", ok)


def test_every_live_json_record_is_canonical() -> None:
    off = []
    seen = 0
    for name, root in A.roots().items():
        for rel, p in A.iter_records(name, root):
            if p.suffix != ".json":
                continue
            seen += 1
            raw = p.read_bytes()
            try:
                doc = json.loads(raw)
            except ValueError:
                off.append(f"{name}:{rel} (unparseable)")
                continue
            if raw.decode("utf-8", "replace") not in {_canonical(doc, ea, nl) for ea in (False, True)
                                                      for nl in (False, True)}:
                off.append(f"{name}:{rel}")
    # An empty population passes nothing: the corpus holds thousands of records.
    check("test_every_live_json_record_is_canonical", seen > 0 and not off,
          f"{len(off)} of {seen} non-canonical, e.g. {off[:3]}" if off else f"{seen} records")


def main() -> int:
    global A
    try:
        from cairn.tools.artifact import artifact as door
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject cairn.tools.artifact.artifact does not load: {exc!r}")
        for n in PROVES["f9ba6c89844d"].values():
            check(n, False, "subject absent")
        return 1
    A = door
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-canonical-json-proof-") as d:
            tmp = Path(d)
            try:
                commons = _world(tmp)
                test_an_indent_1_record_is_refused_and_nothing_lands(commons)
                test_an_unparseable_record_is_refused_and_nothing_lands(commons)
                test_the_canonical_record_lands_and_journals(commons)
                test_a_non_json_or_unjournaled_write_is_as_before(commons, tmp)
            finally:
                A.set_diagnostic_roots(None)
        test_every_live_json_record_is_canonical()
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["f9ba6c89844d"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

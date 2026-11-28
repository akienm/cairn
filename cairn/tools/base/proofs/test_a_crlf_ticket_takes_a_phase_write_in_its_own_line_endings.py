"""Proof: the ticket door accepts a CRLF ticket on read and normalises it to LF on write.

Measured 2026-11-28 on akiendell (Windows, main ea759d750): fixtures that wrote a ticket with
``Path.write_text`` got CRLF bytes, and ``ticket_file.ticket_shape`` refused them (IllegalTransition:
"the ticket's serialisation cannot be reproduced ...") because it compared the file's RAW bytes with
``json.dumps(...).encode()``, which has only LF. That took teeth red across four outline_check
proofs (opens_a_question_per_conflict, reuses_a_hand_opened_question,
opens_only_on_a_line_the_ticket_touches, and one tooth of reads_the_requirements_folder) that are
green on Linux.

The ruling (Akien: "the door accepts and normalises"): LF stays the one canonical form. The artifact
door already refuses CRLF on WRITE (f9ba6c89844d, _refuse_non_canonical), so only READS need the
tolerance: ticket_shape reads a CRLF file as its LF self, the write that follows is canonical LF,
and write_ticket names the normalisation in the journal why.

The fixture writes raw CRLF bytes with Path.write_bytes and skips the artifact door, the way a Windows
write_text or a git checkout with autocrlf does in real life. That is the only way a CRLF ticket ever
reaches the disk, since the door would refuse it.

  1. a CRLF ticket takes a phase write: ticket_shape accepts it and the result is canonical LF;
  2. the journal why says the file was normalised from CRLF;
  3. an LF ticket is unchanged: no CR, and no normalisation note.

    python3 cairn/tools/base/proofs/test_a_crlf_ticket_takes_a_phase_write_in_its_own_line_endings.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"ff0959ce2955": {
    "1": "test_a_crlf_ticket_takes_a_phase_write_and_lands_lf",
    "2": "test_the_journal_why_names_the_normalisation",
    "3": "test_an_lf_ticket_stays_lf_and_says_nothing",
}}

TICKET = "c41f0000d00r"
PLAN = {"id": TICKET, "title": "the proof's fixture ticket", "why": "fixture", "how": "none"}
NOTE = "normalised CRLF -> LF"
CR, LF, CRLF, NL = chr(13).encode(), chr(10).encode(), (chr(13) + chr(10)).encode(), chr(10)


def _live_charter() -> Path:
    for c in (REPO.parent / "CairnCommons", Path.home() / "dev" / "src" / "CairnCommons"):
        f = c / "tickets" / "_charter+why.json"
        if f.is_file():
            return f
    raise FileNotFoundError("no live tickets/_charter+why.json beside the repo or under ~/dev/src")


def _world(eol: bytes):
    """A scratch commons with one plan whose raw bytes use ``eol``, written past the door."""
    from cairn.tools.artifact import artifact as A
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-crlf-door-")
    commons, cairn = tmp / "CairnCommons", tmp / "cairn"
    (commons / "tickets").mkdir(parents=True)
    cairn.mkdir()
    shutil.copy(_live_charter(), commons / "tickets" / "_charter+why.json")
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    raw = (json.dumps(PLAN, indent=2) + NL).encode("utf-8").replace(LF, eol)
    plan = commons / "tickets" / f"{TICKET}-the-proof-s-fixture-ticket.json"
    plan.write_bytes(raw)                       # not the door: it refuses CRLF
    return tmp, plan, raw


def _phase_write(plan: Path, raw: bytes):
    """Phase-write one key; returns (bytes after, the why the door was handed)."""
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base import ticket_file as tf
    seen: list[str] = []
    real = A.write

    def spy(path, content, **kw):
        if Path(path) == plan:
            seen.append(kw.get("why", ""))
        return real(path, content, **kw)

    A.write = spy
    try:
        tf.ticket_shape(raw, json.loads(raw.decode("utf-8")))     # must accept the file as it stands
        tf.rewrite_ticket(plan, {**PLAN, "how": "a phase wrote this"}, why="crlf door proof", verb="phase")
        return plan.read_bytes(), seen[0]
    finally:
        A.write = real
        A.set_diagnostic_roots(None)


def test_a_crlf_ticket_takes_a_phase_write_and_lands_lf():
    tmp, plan, raw = _world(CRLF)
    try:
        assert raw.count(CRLF) == raw.count(LF) > 3, "the fixture is not CRLF throughout"
        got, _ = _phase_write(plan, raw)
        assert CR not in got, f"the door wrote CRLF back: {got[:80]!r}"
        assert json.loads(got.decode("utf-8"))["how"] == "a phase wrote this"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_the_journal_why_names_the_normalisation():
    tmp, plan, raw = _world(CRLF)
    try:
        _, why = _phase_write(plan, raw)
        assert NOTE in why, f"a CRLF file was reformatted without saying so: {why!r}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_an_lf_ticket_stays_lf_and_says_nothing():
    tmp, plan, raw = _world(LF)
    try:
        got, why = _phase_write(plan, raw)
        assert CR not in got
        assert NOTE not in why, f"an LF file was reported as normalised: {why!r}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

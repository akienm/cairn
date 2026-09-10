"""A ticket's crossings come from the journals, and the derivation loses nothing.

Ticket: CairnCommons/tickets/d2ecdb867bc9-a-crossing-is-derived-from-the-journal-never-stored-on-the-ticket.json

EVERY TOOTH HERE RUNS ON A FIXTURE WORLD, ON PURPOSE. The obvious proof — "the derived set
matches the 42 stored arrays" — dies the moment piece 8 deletes those arrays, and a proof
that can only be taken once is not an instrument. So the corpus comparison was the voyage's
measurement, and what stands here are the INVARIANTS that comparison discovered, each with a
fixture that reds if the rule is dropped.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from cairn.tools.base import crossings as X


def _world(tmp: str) -> dict[str, Path]:
    repo = Path(tmp) / "cairn"
    commons = Path(tmp) / "CairnCommons"
    (repo / "cairn" / "devices" / "alpha").mkdir(parents=True)
    commons.mkdir(parents=True)
    return {"repo": repo, "commons": commons, "instance": Path(tmp) / ".cairn"}


def _journal(root: Path, rel: str, entries: list[dict]) -> None:
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries), encoding="utf-8")


def _cross(to: str, at: str, ticket: str = "t1", direction: str = "forward", **rest) -> dict:
    return {"to": to, "from": None, "at": at, "ticket": ticket, "direction": direction, **rest}


def test_ALSO_PROVEN_BY_IS_READ_or_the_derivation_LOSES_a_proof():
    """The one key that made the derivation lossless, and the only tooth that catches its loss.

    Measured 2026-09-10: one journal entry of 677 carries ``also_proven_by`` — trouble's PROVEME
    crossing for 9579a6f9cec6 — and it is precisely the entry the stored/derived comparison
    flagged at risk. Its stored crossing named three proofs; the journal's ``proven_by`` named
    one and the other two sat in ``also_proven_by``. Read one key and hollow's instrument set
    for that ticket loses ``test_raise_trouble.py``; read both and the sets are identical.
    Delete the ``also_proven_by`` branch in ``_named`` and this tooth reds.
    """
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00", proven_by="p/one.py"),
            _cross("PROVEME", "2026-01-02T10:00:00", proven_by="p/one.py",
                   also_proven_by=["p/two.py", "p/three.py"]),
        ])
        got = X.proven_by_since_buildme("t1", roots=w)
        assert got == ["p/one.py", "p/two.py", "p/three.py"], (
            f"also_proven_by was not read: {got}")
        assert X.proven_by_latest("t1", roots=w) == ["p/one.py", "p/two.py", "p/three.py"], (
            "the latest-crossing read must see the same key")


def test_the_UNION_CUTS_AT_THE_LATEST_BUILDME_so_an_abandoned_proof_is_not_carried():
    """A kicked-back ticket re-crosses BUILDME, and the proof it abandoned must not be checked.

    This is the rule ``proof_coverage._proven_by``'s docstring argues for when it says "latest,
    not first", applied to the union. Measured over 42 tickets it was the only one of three
    candidate rules with zero loss: union-over-everything lost one, latest-only disagreed twice.
    """
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00", proven_by="p/abandoned.py"),
            _cross("PROVEME", "2026-01-02T10:00:00", proven_by="p/also_abandoned.py"),
            _cross("BUILDME", "2026-01-03T10:00:00", proven_by="p/kept.py"),
            _cross("PROVEME", "2026-01-04T10:00:00", proven_by="p/kept_too.py"),
        ])
        got = X.proven_by_since_buildme("t1", roots=w)
        assert got == ["p/kept.py", "p/kept_too.py"], (
            f"the union did not cut at the latest BUILDME: {got}")


def test_the_LATEST_READ_NAMES_ONE_CROSSING_and_is_never_the_union():
    """Two verbs, two questions. The gate asks what THIS crossing stands on; hollow asks what
    could measure the build at all. Collapsing them is the defect recorded at ticket
    proven-by-answers-two-questions-and-one-reader-serves-both — so if ``proven_by_latest``
    ever starts unioning, this reds while the tooth above stays green."""
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00", proven_by="p/early.py"),
            _cross("PROVEME", "2026-01-02T10:00:00", proven_by="p/late.py"),
        ])
        assert X.proven_by_latest("t1", roots=w) == ["p/late.py"]
        assert X.proven_by_since_buildme("t1", roots=w) == ["p/early.py", "p/late.py"]


def test_a_CROSSING_THAT_NAMES_NO_PROOF_is_stepped_over_not_treated_as_an_answer():
    """"The latest crossing" and "the latest crossing that NAMES a proof" differ on every
    ticket whose last act named none — and the second is the one both consumers implemented."""
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00", proven_by="p/one.py"),
            _cross("PROVED", "2026-01-02T10:00:00"),
        ])
        assert X.proven_by_latest("t1", roots=w) == ["p/one.py"]


def test_DIRECTION_IS_CHECKED_which_the_stored_array_could_not_do():
    """A stored crossing carried no ``direction`` at all, so a disposition into BUILDME and a
    forward crossing into it were the same record. The journal carries the field; reading it is
    strictly more measurement than the arrays could hold, and it is why the derivation is not
    merely a re-encoding of what a hand wrote."""
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00", proven_by="p/real.py"),
            _cross("PROVEME", "2026-01-02T10:00:00", proven_by="p/later.py"),
            _cross("BUILDME", "2026-01-03T10:00:00", direction="disposition",
                   proven_by="p/dispositioned.py"),
        ])
        bm = X.buildme_crossing("t1", roots=w)
        assert bm["at"] == "2026-01-01T10:00:00", (
            f"a disposition was mistaken for the build's start: {bm}")
        assert X.proven_by_since_buildme("t1", roots=w) == [
            "p/real.py", "p/later.py", "p/dispositioned.py"]


def test_BOTH_ROOTS_ARE_SCANNED_because_a_concept_piece_journals_only_to_the_commons():
    """A first scan of class-space alone left three stored entries with no journal match;
    adding the two commons journals dropped that to two. A concept-piece ticket crosses into
    ``intentions-not-beside-code/history.json`` and nowhere else — drop the commons root and
    those tickets derive to nothing at all, which reads as "never crossed" rather than as a bug.
    """
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["commons"], "intentions-not-beside-code/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00", proven_by="p/prose.md"),
        ])
        assert X.has_crossings("t1", roots=w), "a commons-only ticket derived to nothing"
        assert X.proven_by_since_buildme("t1", roots=w) == ["p/prose.md"]
        assert X.crossings_for("t1", roots=w)[0]["journal"] == (
            "CairnCommons/intentions-not-beside-code/history.json"), (
            "a commons journal must carry its CairnCommons prefix — that is the string the "
            "stored arrays used and the string a joining consumer already matches on")


def test_AN_ABSOLUTE_PROOF_PATH_NORMALISES_so_a_set_comparison_is_not_a_prefix_test():
    """The journals carry the same file both ways. One of the two disagreements under the
    latest-crossing rule was exactly this and nothing else — a real difference measured where
    there was none."""
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00",
                   proven_by=str(w["repo"] / "cairn" / "devices" / "alpha" / "proofs" / "t.py")),
        ])
        assert X.proven_by_since_buildme("t1", roots=w) == [
            "cairn/devices/alpha/proofs/t.py"]


def test_EVERY_DERIVED_CROSSING_CARRIES_A_TIME_which_the_stored_record_never_did():
    """hollow reverted to ``git rev-list -1 --before=<date>`` when the crossing carried only a
    day, and that resolves to the last commit before the day STARTED — silently reverting a
    same-day build to a whole day earlier. The journal has always had the second; the stored
    array never did. Deriving retires that fallback rather than patching it."""
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T14:32:07", proven_by="p/one.py"),
        ])
        bm = X.buildme_crossing("t1", roots=w)
        assert bm["at"] == "2026-01-01T14:32:07", bm
        assert "T" in bm["at"] and len(bm["at"]) >= 19, (
            "a derived crossing must carry the second, not the day")
        assert bm["date"] == "2026-01-01", "the day is still offered for a caller that wants it"


def test_A_TICKET_THAT_NEVER_CROSSED_derives_to_nothing_and_says_so_without_raising():
    """``crossing_record_absent`` and ``proof_named`` are different findings — archaeology
    versus an actionable lack — and proof_coverage draws that line. The derivation has to be
    able to say "no record" as an answer, not as an exception."""
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00", ticket="somebody-else"),
        ])
        assert X.has_crossings("t1", roots=w) is False
        assert X.crossings_for("t1", roots=w) == []
        assert X.proven_by_latest("t1", roots=w) == []
        assert X.buildme_crossing("t1", roots=w) is None


def test_A_JOURNAL_ENTRY_WITH_NO_TICKET_belongs_to_nobody_and_is_never_borrowed():
    """94 of 677 journal entries carry no ticket (measured 2026-09-10) — pre-ticket crossings and
    component-level records. Attaching them to whatever ticket asked would manufacture evidence,
    which is exactly the shape of a hand-written crossing this whole voyage exists to remove."""
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            {"to": "BUILDME", "at": "2026-01-01T10:00:00", "direction": "forward",
             "proven_by": "p/orphan.py"},
            _cross("BUILDME", "2026-01-02T10:00:00", proven_by="p/mine.py"),
        ])
        assert X.proven_by_since_buildme("t1", roots=w) == ["p/mine.py"]


def test_THE_INDEX_REFRESHES_when_a_journal_moves_so_a_reader_sees_its_own_crossing():
    """/sail crosses BUILDME and then reads the chain in the same process. A cache that outlives
    the write turns "the crossing I just made" into "no crossing" — the failure mode a daemon
    would be reached for; the reader IS the event instead."""
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        rel = "cairn/devices/alpha/history.json"
        _journal(w["repo"], rel, [_cross("BUILDME", "2026-01-01T10:00:00", proven_by="p/one.py")])
        assert X.proven_by_since_buildme("t1", roots=w) == ["p/one.py"]
        _journal(w["repo"], rel, [
            _cross("BUILDME", "2026-01-01T10:00:00", proven_by="p/one.py"),
            _cross("PROVEME", "2026-01-02T10:00:00", proven_by="p/two.py"),
        ])
        assert X.proven_by_since_buildme("t1", roots=w) == ["p/one.py", "p/two.py"], (
            "the index did not refresh after the journal moved")


def test_NO_TICKET_IN_THE_LIVE_COMMONS_CARRIES_A_STORED_CROSSINGS_KEY():
    """The migration's standing invariant, over the real corpus — the one tooth here that is not
    a fixture, because the claim IS about the world. 42 tickets carried a list and 1 carried
    prose on 2026-09-10; a hand that writes one back reds here and at the WATCHME probe.
    """
    from cairn.tools.base.address import ROOTS
    tickets = Path(ROOTS["commons"]) / "tickets"
    if not tickets.is_dir():
        pytest.skip("no live commons on this box")
    carriers = []
    for path in sorted(tickets.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and "crossings" in doc:
            carriers.append(path.name)
    assert carriers == [], (
        f"{len(carriers)} ticket(s) carry a stored crossings key, which no writer writes and "
        f"four gate-reading sites would believe: {carriers[:5]}")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

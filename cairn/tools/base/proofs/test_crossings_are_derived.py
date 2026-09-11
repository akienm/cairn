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

class _TheDerivation:
    """Bind the derivation AT CALL TIME, never at import — and that is a measured requirement.

    ``cairn/tools/base/crossings.py`` DID NOT EXIST before this build. The hollow reader proves a
    build is load-bearing by taking each written file away and re-running this proof, and a
    module-level ``from cairn.tools.base import crossings`` turns that removal into a COLLECTION
    ERROR: pytest never reaches a tooth, nothing prints, and the reader records UNRAN — the
    verdict meaning "nothing here says whether a tooth checks this file." A proof that cannot
    survive its own subject being taken away is not an instrument for measuring whether it checks
    that subject.

    So the name resolves on first attribute access, inside the tooth that wants it. Take
    ``crossings.py`` away and each tooth that touches the derivation reds BY NAME; the teeth that
    do not touch it still run and still report. This is the same defect that made a sibling
    voyage's hollow reading turn on alphabetical order, arriving by the other door.
    """

    def __getattr__(self, name):
        from cairn.tools.base import crossings
        return getattr(crossings, name)


X = _TheDerivation()


PROVES = {
    # 2026-09-10, ticket d2ecdb867bc9 — a crossing is derived from the journal, never stored on
    # the ticket. Lettered clauses because that ticket's falsifier enumerates (a)..(d).
    "d2ecdb867bc9": {
        "a": "test_ALSO_PROVEN_BY_IS_READ_or_the_derivation_LOSES_a_proof",
        "b": "test_EVERY_GATE_READER_ASKS_THE_JOURNALS_and_none_reads_a_stored_array",
        "c": "test_NO_TICKET_IN_THE_LIVE_COMMONS_CARRIES_A_STORED_CROSSINGS_KEY",
        "d": "test_THE_BUILDME_TIME_HAS_NO_COARSER_FALLBACK_LEFT_TO_BE_WRONG",
    },
}


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


def test_ONE_ACT_JOURNALED_AT_FOUR_ADDRESSES_is_read_as_four_proofs_not_one():
    """THE READING THAT WAS RETIRED THE DAY IT SHIPPED, and this tooth is what stops it coming back.

    A crossing ACT is journaled at EVERY component address it touches (Law 5), so a voyage that
    proves a seam at four addresses leaves four PROVED entries, each naming that address's share
    of the evidence. A reader that takes "the latest crossing that names a proof" therefore
    resolves to the LAST RECORD — one component's share — and calls it the act.

    This module shipped with exactly that reader, named ``proven_by_latest``, citing a ticket
    called proven-by-answers-two-questions-and-one-reader-serves-both. A grep of both roots
    returns nothing: that ticket does not exist and never did, and the citation was authored in
    this module's own build commit. Measured against the stored arrays at b9828a2^, the
    last-record reading loses proofs on 4 of the 42 migrated tickets — 9579a6f9cec6 loses five
    at once — while the union since the latest forward BUILDME loses none. The verb is gone and
    all three consumers read the union.

    The four journals below are ONE act. Reintroduce a last-record read anywhere and this reds.
    """
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00"),
            _cross("PROVED", "2026-01-02T10:00:00", proven_by="p/alpha.py"),
        ])
        for i, device in enumerate(("beta", "gamma", "delta"), start=1):
            _journal(w["repo"], f"cairn/devices/{device}/history.json", [
                _cross("PROVED", f"2026-01-02T10:00:0{i}", proven_by=f"p/{device}.py")])
        got = X.proven_by_since_buildme("t1", roots=w)
        assert got == ["p/alpha.py", "p/beta.py", "p/gamma.py", "p/delta.py"], (
            "one PROVED act journaled at four addresses must read as four proofs, not as the "
            f"share of whichever address journaled last: {got}")
        assert not hasattr(X, "proven_by_latest"), (
            "the retired verb is back. It reads the last journal RECORD and calls it the act, "
            "which loses evidence on any seam proved at more than one address.")


def test_a_CROSSING_THAT_NAMES_NO_PROOF_is_stepped_over_not_treated_as_an_answer():
    """A ticket whose LAST act named no proof still stands on what its earlier acts named.

    A PROVED crossing routinely names none — the evidence was declared at PROVEME — so a reader
    that stopped at the last record would answer "nothing" for a fully proved boat. The union
    steps over the silent entry instead of treating it as the answer."""
    with tempfile.TemporaryDirectory() as tmp:
        w = _world(tmp)
        _journal(w["repo"], "cairn/devices/alpha/history.json", [
            _cross("BUILDME", "2026-01-01T10:00:00", proven_by="p/one.py"),
            _cross("PROVED", "2026-01-02T10:00:00"),
        ])
        assert X.proven_by_since_buildme("t1", roots=w) == ["p/one.py"]


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
        assert X.proven_by_since_buildme("t1", roots=w) == []
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
    """CLAUSE (c) — the key is gone from the corpus, and the watch that keeps it gone is armed.

    THE SKIP THAT USED TO GUARD THE CORPUS HALF IS GONE, and removing it was a measured fix, not
    tidying. ``ROOTS["commons"]`` is derived as the repo's SIBLING, so inside the git worktree
    the hollow reader builds there is no commons to read and this tooth called
    ``pytest.skip``. A skipped tooth is neither green nor red — which is exactly right, and
    exactly why it could not serve as hollow evidence: the reader saw the one tooth declared for
    this clause fail to go green at HEAD and refused to attribute any reversion reading at all.
    So the corpus half now runs WHEN THERE IS A CORPUS (always in the live tree, which is where
    the seal is taken) and the watch half runs ANYWHERE.

    Both halves are the same claim at two horizons. 42 tickets carried a list and 1 carried
    prose on 2026-09-10; the scan says none does NOW, and the probe is what can still say so in
    a month. The ticket's horizon asks for the span, not the instant.
    """
    from cairn.tools.base.address import ROOTS
    tickets = Path(ROOTS["commons"]) / "tickets"
    carriers = []
    for path in (sorted(tickets.glob("*.json")) if tickets.is_dir() else []):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and "crossings" in doc:
            carriers.append(path.name)
    assert carriers == [], (
        f"{len(carriers)} ticket(s) carry a stored crossings key, which no writer writes and "
        f"four gate-reading sites would believe: {carriers[:5]}")

    # THE WATCH THAT KEEPS THIS TRUE AFTER TODAY — and the half of this tooth that runs no
    # matter where the proof is standing, because the probe berths beside the proof rather than
    # in the commons. Measured 2026-09-10 across 281 decompose berths carrying a writes_to: 42
    # name a probes/ module and no proof in the corpus reads one, so a voyage can be REQUIRED to
    # write a watch that nothing is able to fail on. Take the probe away and this clause reds.
    probe_path = Path(__file__).resolve().parents[1] / "probes" / "no_ticket_carries_a_stored_crossing.py"
    assert probe_path.is_file(), f"the watch this ticket carries is not at its berth: {probe_path}"
    import importlib.util
    spec = importlib.util.spec_from_file_location("_no_ticket_carries_a_stored_crossing", probe_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    probe = getattr(mod, "PROBE", None)
    assert probe is not None, "the probe module declares no module-level PROBE"
    assert getattr(probe, "carry", None) is not None, "the PROBE declares no carry"
    assert getattr(probe, "enough", None) is not None, "the PROBE declares no enough"


def test_EVERY_GATE_READER_ASKS_THE_JOURNALS_and_none_reads_a_stored_array():
    """CLAUSE (b) — the three sites that hand a gate its evidence ask the record of truth.

    This is the clause the derivation existed to satisfy, and it is the one a fixture cannot
    reach: whether ``proof_coverage``, ``hollow`` and the codemother shim READ the journals is a
    fact about those three files, not about any world this proof can build. So the tooth reads
    them, which is the honest instrument for the claim actually made.

    Measured at the pre-build commit 8bca770403d8: all three carried ``ticket.get("crossings")``
    — proof_coverage at two sites, hollow at two, the shim at one. Each of those is a gate input
    typed by a hand: clearance refuses PROVED on a boat proof_coverage calls uncovered, and
    hollow reverts to the commit the BUILDME entry names. Revert any one of the three and this
    tooth names it.

    THE PROBE IS DELIBERATELY NOT IN THIS SET. ``no_ticket_carries_a_stored_crossing.py`` reads
    the key ON PURPOSE — finding one is its whole job — so folding it in would make the tooth
    red for the one file whose reading of the key is correct.
    """
    root = Path(__file__).resolve().parents[4]   # proofs/ base/ tools/ cairn/ -> the repo
    readers = {
        "cairn/tools/proof_coverage/proof_coverage.py": "clearance refuses PROVED on an uncovered boat",
        "cairn/devices/tester/hollow.py": "the hollow reading reverts to the commit this names",
        "cairn/devices/codemother/shim.py": "the shim names the proofs a review reads",
    }
    stored_reads, no_import = [], []
    for rel, what_it_gates in readers.items():
        text = (root / rel).read_text(encoding="utf-8")
        code = "\n".join(line for line in text.splitlines()
                          if not line.lstrip().startswith("#"))
        for shape in ('ticket.get("crossings")', "ticket.get('crossings')",
                      'ticket["crossings"]', "ticket['crossings']"):
            if shape in code:
                stored_reads.append(f"{rel} reads {shape} — and {what_it_gates}")
        if "cairn.tools.base.crossings" not in code:
            no_import.append(rel)
    assert stored_reads == [], (
        "a gate reader still takes its evidence from the ticket's stored array, which no writer "
        "writes and a hand therefore typed: " + "; ".join(stored_reads))
    assert no_import == [], (
        "a gate reader names the derivation nowhere, so it is getting its crossings from "
        "somewhere this tooth cannot see: " + ", ".join(no_import))


def test_THE_BUILDME_TIME_HAS_NO_COARSER_FALLBACK_LEFT_TO_BE_WRONG():
    """CLAUSE (d) — hollow resolves the pre-build moment to the second or refuses to guess.

    The retired branch read the stored crossing's ``date``, which is a DAY. ``git rev-list -1
    --before=2026-09-07`` resolves a bare date to the last commit before that day STARTED, so a
    ticket built and committed on one day reverted to a whole day earlier and the hollow reading
    measured a world the build never stood in — a wrong answer delivered with no sign it was
    wrong, which Law 3 calls a hypothesis wearing a measurement's clothes.

    Deriving from the journal means every crossing carries an ``at`` with a time, so the branch
    that could be wrong has nothing left to be wrong about. At the pre-build commit this same
    call returned ``"2026-09-01"``; now it refuses.
    """
    from cairn.devices.tester.hollow import HollowUnmeasurable, _buildme_at
    ticket = {"id": "t1", "crossings": [{"to": "BUILDME", "date": "2026-09-01"}]}
    crossing = {"to": "BUILDME", "date": "2026-09-01"}   # a day, and no 'at'
    with pytest.raises(HollowUnmeasurable) as red:
        _buildme_at(ticket, crossing)
    assert "at" in str(red.value), (
        "hollow refused, but not for the missing time — the message must name what is absent")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

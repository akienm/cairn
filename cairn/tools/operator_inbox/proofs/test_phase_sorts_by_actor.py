"""PROOF — the pickup phase is the operator inbox's SIEVE, and it sorts by who acts next.

Ticket ``6ec9b384b451`` (the-pickup-phase-says-why-a-ticket-is-not-moving), ruling
``2026-09-08-a-fleet-of-one-reshapes-the-pickup-phase``.

THE LIVED SYMPTOM, MEASURED THE DAY THE TICKET WAS CAST: 51 of 258 tickets wore
``:waiting`` and 205 wore a bare cursor, so every one of them read the same on every
surface. The handful that actually needed Akien — a design he has to rule on, a dependency
that will never clear — sat inside the same undifferentiated pile as the work CC simply had
not got to. The inbox could not compute the difference, because the phase slot answered WHO
HOLDS IT and nobody but CC ever holds anything.

WHAT A HOLLOW BUILD LOOKS LIKE HERE, and what each tooth is aimed at:

  - THE LABEL DROPS THE PHASE. Before this ticket ``status_label`` recognised ``:waiting``
    and let every other phase fall on the floor — sound with two words, catastrophic with
    five, because the four it would drop are exactly the ones a human needs. So the round
    trip is driven over ALL FIVE, plus the WATCHME-object form the three readers used to
    disagree on.
  - THE SORT IS ALPHABETICAL BY ACCIDENT. ``blocked`` before ``hold`` before ``waiting`` is
    the right order AND the alphabetical one, so a tooth that only checked those three would
    be green for the wrong reason. ``queued`` is the discriminator: it sorts LAST, against
    the alphabet, because nobody acts on it.
  - THE SIEVE LETS EVERYTHING THROUGH. Membership is asserted as an EXACT SET over a corpus
    holding one ticket of every phase, so an inbox that simply stopped filtering reds.
  - THE STAGE KEY MOVED. Every surface in the system lists by stage; the phase is the
    SECONDARY key and this ticket had no licence to change that.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.transitions import _PHASES  # noqa: E402
from cairn.tools.operator_inbox import inbox  # noqa: E402

_PHASE_IDS = {
    "waiting":    "aaaaaaaaaaaa",
    "in-process": "bbbbbbbbbbbb",
    "queued":     "cccccccccccc",
    "hold":       "dddddddddddd",
    "blocked":    "eeeeeeeeeeee",
}
_BARE_ID = "ffffffffffff"
_TERMINAL_ID = "999999999999"


def _fixture(dirpath: Path) -> None:
    """One live ticket per phase, plus a bare-cursor legacy ticket and a terminal. Written as
    files, through the real reader, because a sieve tested at the function boundary is a
    sieve nobody proved reads tickets."""
    for phase, tid in _PHASE_IDS.items():
        (dirpath / f"{tid}.json").write_text(json.dumps({
            "id": tid, "title": f"a {phase} ticket", "date": "2026-09-08",
            "workflow_and_state":
                f"code-seam@v2: THINKME -> TICKETME -> [BUILDME:{phase}] -> PROVEME -> PROVED",
        }))
    (dirpath / f"{_BARE_ID}.json").write_text(json.dumps({
        "id": _BARE_ID, "title": "the legacy corpus", "date": "2026-08-01",
        "workflow_and_state":
            "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED",
    }))
    (dirpath / f"{_TERMINAL_ID}.json").write_text(json.dumps({
        "id": _TERMINAL_ID, "title": "done", "date": "2026-08-01",
        "workflow_and_state":
            "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]",
    }))


def test_the_label_round_trips_every_word_of_the_vocabulary():
    for phase in _PHASES:
        assert inbox.status_label(f"BUILDME:{phase}") == f"BUILDME:{phase}", phase
        assert inbox.phase_of(f"BUILDME:{phase}") == phase, phase
    # the WATCHME object is stripped and the phase survives it — the form the three readers
    # disagreed on before ticket 3feb201c84ea
    assert inbox.status_label("WATCHME(a-thing-it-watches):blocked") == "WATCHME:blocked"
    # a bare cursor is a bare label, and makes no phase claim
    assert inbox.status_label("BUILDME") == "BUILDME"
    assert inbox.phase_of("BUILDME") is None
    assert inbox.status_label(None) == inbox.UNPARSED


def test_the_sort_puts_akiens_work_first_and_queued_LAST_against_the_alphabet():
    labels = [f"BUILDME:{p}" for p in _PHASES] + ["BUILDME"]
    ordered = sorted(labels, key=inbox.label_sort_key)
    assert ordered == ["BUILDME", "BUILDME:blocked", "BUILDME:hold",
                       "BUILDME:in-process", "BUILDME:waiting", "BUILDME:queued"], ordered
    # THE DISCRIMINATOR: alphabetically 'queued' precedes 'waiting'. It sorts after, because
    # the key is WHO ACTS NEXT and on a queued ticket the answer is nobody. A sort that was
    # accidentally alphabetical passes every other row of this tooth and fails this one.
    assert ordered.index("BUILDME:queued") > ordered.index("BUILDME:waiting")
    assert sorted(["BUILDME:queued", "BUILDME:waiting"]) == ["BUILDME:queued", "BUILDME:waiting"]


def test_the_stage_stays_the_primary_key():
    """Every surface lists by stage; the phase is secondary. A blocked PROVED must not climb
    over a waiting BUILDME — that contract is older than this ticket and not its to change."""
    ordered = sorted(["BUILDME:waiting", "PROVEME:blocked", "PROVEME:waiting", "BUILDME:blocked"],
                     key=inbox.label_sort_key)
    assert ordered == ["PROVEME:blocked", "PROVEME:waiting",
                       "BUILDME:blocked", "BUILDME:waiting"], ordered


def test_an_unknown_phase_sorts_after_the_vocabulary_never_silently_first():
    ordered = sorted(["BUILDME:waiting", "BUILDME:not-a-phase", "BUILDME:blocked"],
                     key=inbox.label_sort_key)
    assert ordered[0] == "BUILDME:blocked" and ordered[-1] == "BUILDME:not-a-phase", ordered


def test_the_inbox_holds_EXACTLY_the_hold_and_blocked_tickets():
    """An exact set, not a membership check: an inbox that stopped filtering would pass
    'blocked is in' and 'hold is in' and fail only here."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _fixture(p)
        got = inbox.read_operator_tickets(tickets_dir=p)
        ids = {r["id"] for r in got["records"]}
        assert ids == {_PHASE_IDS["hold"], _PHASE_IDS["blocked"]}, sorted(ids)
        assert got["count"] == 2, got["count"]
        # and the ones deliberately OUT are each out for their own stated reason
        assert _PHASE_IDS["waiting"] not in ids, "CC's own queue is reference, not inbox"
        assert _PHASE_IDS["queued"] not in ids, "a self-clearing wait needs no operator"
        assert _PHASE_IDS["in-process"] not in ids, "work in flight is the opposite of an inbox"
        assert _BARE_ID not in ids, "a bare cursor makes no claim, so it makes no inbox claim"
        assert _TERMINAL_ID not in ids, "a terminal is done"


def test_the_sieve_names_its_membership_once_and_the_reader_uses_that_name():
    """A second, drifting copy of the membership rule is how the three readers disagreed
    before ticket 3feb201c84ea. There is one tuple, and it is the one the reader reads."""
    assert inbox.PHASE_INBOX == ("blocked", "hold"), inbox.PHASE_INBOX
    assert set(inbox.PHASE_INBOX) <= set(_PHASES), "the sieve names a word the grammar lacks"
    assert set(inbox.PHASE_RANK) - {None} == set(_PHASES), \
        "the rank table and the grammar's vocabulary drifted apart"


def test_a_ticket_that_does_not_parse_is_still_LOUD_never_a_quiet_bucket():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "111111111111.json").write_text(json.dumps({
            "id": "111111111111", "title": "prose where a workflow should be",
            "workflow_and_state": "somebody should look at this one",
        }))
        records = inbox.read_tickets(tickets_dir=p)["records"]
        assert [r["label"] for r in records] == [inbox.UNPARSED], records


def test_the_live_inbox_reads_without_raising_and_every_member_earns_its_seat():
    """Over the LIVE corpus, asserting the INVARIANT rather than a count: the corpus moves
    daily, but every record the inbox shows must carry a phase the sieve names, and none may
    be terminal. A snapshot count here would red on the next ticket cast."""
    got = inbox.read_operator_tickets()
    for record in got["records"]:
        assert inbox.phase_of(record["label"]) in inbox.PHASE_INBOX, record
        assert record["label"].split(":")[0] not in inbox.TERMINAL_STATES, record
    assert got["count"] == len(got["records"])


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)

"""PROBE PROOF — the vocabulary is WRITTEN, not merely legal, and the watch can un-clear.

Ticket ``6ec9b384b451``. The probe under test is
``cairn/tools/base/probes/the_vocabulary_is_written_not_just_legal.py``.

WHAT A HOLLOW BUILD OF THIS WATCH LOOKS LIKE, EXACTLY, because it already happened once at
this address: ``a_pickup_is_witnessed`` cleared on ``pickups >= 1``, took its one record in
August 2026, and read green for a month while the door it watched had no caller. An
existence claim cannot regress, so a watch built on one stops watching the moment it clears.

So the teeth here are not "does it say the right thing about today's corpus" — that is a
snapshot, and tomorrow's corpus would red it. They are:

  - IT IS FALSE ON A CORPUS THAT WEARS ONLY ``waiting``, at any size. The failure the ticket
    names.
  - IT GOES BACK DOWN. Cleared on a corpus, then the corpus loses its written phases, then
    it is false again. This is the one property the sibling lacked, and it is proved by
    driving the clear in both directions rather than by reading the clause.
  - EVERY CLAUSE IS LOAD-BEARING — each of the three is dropped in turn and the clear fails
    for that reason alone, so a clause that stopped mattering cannot hide behind the others.
  - IT WALKS ONCE PER MOVE, not once per beat. Live trouble
    ``beat-tail-re-walks-corpora-no-sieve-counts``; the counter is ``settled.DERIVATIONS``,
    which is the only surface that can tell a memo from a re-derivation.
  - THE PROBE IS SHAPED, so the emission gate's ARMED read is not the only thing standing
    between this and an unfired watch.
"""

from __future__ import annotations

import dataclasses
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.base import settled as S  # noqa: E402
from cairn.tools.base import transitions as T  # noqa: E402
from cairn.tools.base.probes import the_vocabulary_is_written_not_just_legal as W  # noqa: E402


def _a_non_terminal_ticket_id() -> str:
    """A ticket id read OUT of the live corpus whose cursor has not reached a terminal.

    THIS CONSTANT USED TO BE THE STRING ``6ec9b384b451`` — this proof's own ticket — carrying
    the comment "not terminal while this proof exists". It stopped being true SIX HOURS after
    it was written, on 2026-09-08, when that ticket reached PROVED and every ``queued`` fixture
    naming it went correctly STALE. The proof went red for the one reason that is not a defect:
    the door's self-clearing clause firing exactly as designed.

    The file's own docstring had already named the rule it then broke four lines later — "that
    is a snapshot, and tomorrow's corpus would red it". A snapshot does not become an invariant
    by sitting in a constant instead of an assertion. Which ticket is unfinished is the world's
    business; that SOME ticket is unfinished is what these teeth actually need, and if the day
    ever comes when none is, that is a real finding and this raises rather than guesses."""
    for path in sorted(T._TICKETS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            here = T.parse_workflow(doc["workflow_and_state"]).here
        except Exception:
            continue
        if doc.get("id") and not T.is_terminal(here):
            return doc["id"]
    raise AssertionError("no non-terminal ticket in the live corpus — the tooth measured nothing")


_LIVE_TICKET = _a_non_terminal_ticket_id()   # DERIVED, never pinned — see above
_RESOLVING = "CLAUDE.md"        # a path the world actually holds


def _cursor(phase: str | None) -> str:
    tail = f"BUILDME:{phase}" if phase else "BUILDME"
    return f"code-seam@v2: THINKME -> TICKETME -> [{tail}] -> PROVEME -> PROVED"


def _corpus(dirpath: Path, spec: list[tuple[str, str | None, object]]) -> None:
    """``spec`` is (id, phase, release) per ticket. Written as files because the probe reads
    files — a corpus faked at the function boundary would not exercise the walk."""
    for tid, phase, release in spec:
        doc = {"id": tid, "workflow_and_state": _cursor(phase)}
        if release is not None:
            doc["release"] = release
        (dirpath / f"{tid}.json").write_text(json.dumps(doc))


def _walk(dirpath: Path) -> dict:
    before = W._TICKETS
    try:
        W._TICKETS = dirpath
        return W._walk_tickets()
    finally:
        W._TICKETS = before


def test_an_all_waiting_corpus_never_clears_however_large():
    """The named failure: the words land, nothing writes them. Size must not rescue it —
    a hundred tickets wearing one word is the defect at scale, not evidence against it."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _corpus(p, [(f"{i:012x}", "waiting", None) for i in range(100)])
        s = _walk(p)
        assert s["live_tickets"] == 100, s
        assert s["words_used"] == [] and s["write_rate"] == 0.0, s
        assert W._enough({"corpus": s}) is False
        # and the trigger FIRES here — an unwritten vocabulary is the finding, not silence
        assert W._trigger(None, {"corpus": s}) is True


def test_the_clear_goes_up_AND_BACK_DOWN():
    """THE TOOTH THE SIBLING PROBE COULD NOT HAVE PASSED. Cleared, then the written phases
    leave the live corpus, then un-cleared — a watch that coasts on a historical fact reds
    on the second half of this."""
    spec = [(f"{i:012x}", "hold", _RESOLVING) for i in range(5)]
    spec += [(f"{i:012x}", "queued", _LIVE_TICKET) for i in range(5, 9)]
    spec += [(f"{i:012x}", "blocked", _RESOLVING) for i in range(9, 12)]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _corpus(p, spec)
        s = _walk(p)
        assert not s["words_unused"], s
        assert len(s["non_default_tickets"]) >= W._ENOUGH_DISTINCT, s
        assert not s["releases_lacking"], s["releases_lacking"]
        assert W._enough({"corpus": s}) is True, "a genuinely used vocabulary did not clear"
        # a cleared watch is not a finished one: the same probe on a corpus that reverted
        for f in p.glob("*.json"):
            f.unlink()
        _corpus(p, [(f"{i:012x}", "waiting", None) for i in range(40)])
        again = _walk(p)
        assert W._enough({"corpus": again}) is False, \
            "the clear survived the corpus that earned it — the watch stopped watching"


def test_each_clause_of_the_clear_is_load_bearing():
    """Three clauses, dropped one at a time. A clause that no longer decides anything is a
    clause that can rot unnoticed behind the other two."""
    base = [(f"{i:012x}", "hold", _RESOLVING) for i in range(5)]
    base += [(f"{i:012x}", "queued", _LIVE_TICKET) for i in range(5, 9)]
    base += [(f"{i:012x}", "blocked", _RESOLVING) for i in range(9, 12)]

    # (1) a word unused — twelve tickets, but the grammar collapsed to two words in practice
    no_blocked = [(t, ("hold" if ph == "blocked" else ph), r) for t, ph, r in base]
    # (2) too few distinct tickets — the handful an author writes to prove a point
    thin = base[:3] + [(f"{i:012x}", "waiting", None) for i in range(20, 40)]
    # (3) a release that stopped resolving — a corpus telling on itself at rest
    lacking = [(t, ph, ("nowhere-on-this-disk" if i == 0 else r))
               for i, (t, ph, r) in enumerate(base)]

    for name, spec, why in (
        ("a word unused", no_blocked, "words_unused"),
        ("too few tickets", thin, "non_default_tickets"),
        ("a release lacking", lacking, "releases_lacking"),
    ):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            _corpus(p, spec)
            s = _walk(p)
            assert W._enough({"corpus": s}) is False, f"the clear ignored: {name} ({why})"


def test_a_queued_goes_STALE_at_rest_when_its_dependency_reaches_a_terminal():
    """The self-clearing clause, measured against the LIVE corpus rather than a fixture: the
    door refuses a stale queued when it is WRITTEN, and nothing re-checks one already on
    disk. This is what looks."""
    from cairn.tools.base import transitions
    terminal = None
    for path in sorted(transitions._TICKETS.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            if transitions.is_terminal(transitions.parse_workflow(
                    doc["workflow_and_state"]).here) and doc.get("id"):
                terminal = doc["id"]
                break
        except Exception:
            continue
    assert terminal, "no terminal ticket in the live corpus — the tooth measured nothing"
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _corpus(p, [("aaaaaaaaaaaa", "queued", terminal)])
        s = _walk(p)
        assert len(s["releases_lacking"]) == 1, s["releases_lacking"]
        assert "STALE" in s["releases_lacking"][0]["lack"], s["releases_lacking"]


def test_the_trigger_and_the_clear_can_never_both_be_true():
    """Mutual exclusion is claimed in the probe's docstring; a claim in a docstring is a
    hypothesis (Law 3). Driven over corpora spanning both ends and the middle."""
    shapes = [
        [(f"{i:012x}", "waiting", None) for i in range(30)],
        [(f"{i:012x}", "hold", _RESOLVING) for i in range(12)],
        [(f"{i:012x}", "waiting", None) for i in range(30)]
        + [(f"{i:012x}", "hold", _RESOLVING) for i in range(30, 33)],
        [],
    ]
    for spec in shapes:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            _corpus(p, spec)
            s = _walk(p)
            ctx = {"corpus": s}
            assert not (W._trigger(None, ctx) and W._enough(ctx)), s


def test_the_walk_is_settled_and_re_reads_nothing_over_an_unmoved_corpus():
    """Live trouble ``beat-tail-re-walks-corpora-no-sieve-counts``: ~78 probes re-walk
    corpora that did not move, once per beat, forever, and nothing reds the 79th. This
    counts derivations, because a re-derived answer and a remembered one are identical."""
    S.forget()
    cold = W.survey_the_corpus()
    before = S.DERIVATIONS
    for _ in range(5):
        assert W.survey_the_corpus() == cold, "the answer moved while the corpus did not"
    assert S.DERIVATIONS == before, (
        f"the walk re-derived {S.DERIVATIONS - before} times over an unmoved corpus — "
        "this probe is the 79th")
    assert cold["live_tickets"] > 0, "a memo over a vacuous walk proves nothing"


def test_the_probe_is_a_frozen_shape_carrying_both_a_carry_and_a_clear():
    from cairn.tools.base.probe import Probe
    assert isinstance(W.PROBE, Probe)
    assert dataclasses.is_dataclass(W.PROBE) and W.PROBE.__dataclass_params__.frozen
    assert callable(W.PROBE.carry) and callable(W.PROBE.enough) and callable(W.PROBE.trigger)
    body = W.PROBE.carry({})
    for field in ("finding", "counts", "ticket", "against_falsifier", "suggests"):
        assert body.get(field), f"the carry rides back without {field}"
    assert W.PROBE.horizon and W.PROBE.horizon > 0


def test_in_process_is_absent_from_the_counted_words_because_it_cannot_be_written():
    """A clause that can never rise is as dead as one that can never fall: counting a phase
    the corpus is incapable of holding would pin the clear permanently false."""
    assert "in-process" not in W._NON_DEFAULT, W._NON_DEFAULT
    assert set(W._NON_DEFAULT) == {"queued", "hold", "blocked"}


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

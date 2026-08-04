"""Proof: the FIFTH SEAT — a forward crossing out of WATCHME must have EMITTED.

Ticket ``watchme-emits-a-probe`` (2026-07-30), triage position 6, piece (c-i). The ticket's
falsifier (1), verbatim: *a WATCHME crossing is accepted that emitted no armed probe — the
gate must check EMISSION (the probe exists, is armed, and carries its trigger,
enough-condition, carrier, nexus and consumer), which is the clause that makes 'not optional
once present' physics rather than prose.*

WHAT v1 MEASURED, and why a fifth seat rather than a clause on an existing one. ``LEARNME``
sat in the backbone, MANDATORY for every node of both classes, and carried NO GATE: the build
gate fires at the PROVEME crossing, the entry gate into BUILDME, the exit gate into PROVED.
It was the one summons in the path that was forced and unchecked — crossed by every voyage,
satisfied by none. The other four seats sit at fixed backbone crossings; a FREE summons can
appear zero or more times at any position, so 'mandatory to satisfy ONCE CARRIED' had nowhere
to sit but its own seat.

ARMED IS MEASURED AGAINST THE REAL PROBE. The ticket corpus is a fixture here — a proof that
wrote test tickets into CairnCommons/tickets/ would pollute the commons to prove a point —
but ``cairn/base/probes/does_optional_mean_never_carried.py`` is the REAL berth, loaded from
disk by the REAL ``armed_error``, in every green row. So the fixture is the paperwork; the
thing being measured is not.

THE TWO LOAD-BEARING ROWS:
  - ``test_a_back_edge_into_watchme_is_ungated`` — re-arming a watch whose verdict came back
    failed is the OWNER's act (Law 6). A gate on the retreat would trap the boat at the one
    state it exists to be able to return to, and would make a failed intention permanent.
  - ``test_a_refusal_journals_absolutely_nothing`` — a refused move must leave no partial
    record (Law 7: a record of truth is never changed in place, and a half-written crossing
    is worse than no crossing).

    python3 cairn/base/proofs/test_emission_gate.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base import transitions, watchme_spec
from cairn.charter import projector

_CD = transitions.load_class_def("code-seam")
_REAL_BERTH = "cairn/base/probes/does_optional_mean_never_carried.py"
_OBJ = "does-optional-mean-never-carried"

_AT_WATCH = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
             "[WATCHME(%s)] -> PROVED" % _OBJ)
_AT_PROVED = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
              "WATCHME(%s) -> [PROVED]" % _OBJ)

# THE ISOLATING STRING. Crossing forward out of the first watch lands on the SECOND watch,
# not on PROVED — so neither the ticket-required gate nor the exit gate is in play and a
# refusal can only have come from this seat. Measured need, not caution: the first draft
# refused these rows at PROVED, where TicketRequiredRed fires too, and a red there would have
# proved the wrong gate works.
_TWO = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
        "[WATCHME(%s)] -> WATCHME(second-question) -> PROVED" % _OBJ)


def _spec(**over):
    s = {"object": _OBJ,
         "trigger": "twelve or more v2 tickets exist and not one carries a watch",
         "enough": "any node has carried a watch — the question is answered",
         "carrier": "the corpus counts, against the ticket's falsifier",
         "nexus": "hypothesize",
         "consumer": "the owner, who back-edges at the register",
         "probe": _REAL_BERTH}
    s.update(over)
    return s


class _Corpus:
    """A fixture ticket corpus. Repoints the gate's ``_TICKETS`` — the PAPERWORK — while
    leaving ``armed_error`` reading the real berth off the real disk."""

    def __init__(self, tickets: dict):
        self._tickets = tickets

    def __enter__(self):
        self._td = tempfile.TemporaryDirectory()
        d = Path(self._td.name)
        for name, body in self._tickets.items():
            (d / f"{name}.json").write_text(json.dumps(body), encoding="utf-8")
        self._saved = transitions._TICKETS
        transitions._TICKETS = d
        return d

    def __exit__(self, *a):
        transitions._TICKETS = self._saved
        self._td.cleanup()
        return False


def _cross(workflow, target, *, ticket=None, td=None):
    """Cross through the REAL chokepoint at a throwaway address. Returns (new_str, history).

    THE ADDRESS IS NESTED ONE LEVEL ON PURPOSE. ``_build_gate`` reads the component as the
    directory holding ``history_path`` and censuses that directory's PARENT. A history written
    straight into ``td`` therefore made the parent ``/tmp`` — so a PROVEME crossing censused
    every temp directory on the box, and one unreadable systemd private dir crashed the run
    (measured 2026-08-03: 11/12, and it read as environmental for two sessions). Nesting makes
    the censused tree exactly ``td``, which the fixture owns. The census's own crash on an
    unreadable entry was the other half and is fixed at the census (orient.device_census).
    """
    extra = {"ticket": ticket} if ticket is not None else {}
    comp = Path(td) / "fixture_component"
    comp.mkdir(exist_ok=True)
    hist, state = f"{comp}/history.json", f"{comp}/state.json"
    new = transitions.emit(workflow, target, history_path=hist, state_path=state,
                           why="the watch is answered", **extra)
    return new, projector.read_history(hist)


def _expect_red(fn):
    try:
        fn()
    except transitions.WatchmeEmissionRed as e:
        return e
    raise AssertionError("expected WatchmeEmissionRed, got a pass")


def test_an_emitted_watch_crosses_and_the_journal_names_the_berth():
    with _Corpus({"t": {"state": _AT_WATCH, "watchme": [_spec()]}}), \
            tempfile.TemporaryDirectory() as td:
        new, hist = _cross(_AT_WATCH, "PROVED", ticket="t", td=td)
        assert "[PROVED]" in new, new
        note = hist[-1]["emission_gate"]
        assert _REAL_BERTH in note and _OBJ in note, note
        assert "clean" in note, \
            "the record of truth must say WHICH probe answered — a year from now 'something " \
            "was learned' is not a record"


def test_a_crossing_with_no_ticket_cannot_be_measured_so_it_is_refused():
    with _Corpus({}), tempfile.TemporaryDirectory() as td:
        e = _expect_red(lambda: _cross(_TWO, "WATCHME", td=td))
        assert "names no cast ticket" in str(e), e
        assert "Nothing was journaled" in str(e), e


def test_a_carried_watch_with_no_spec_on_the_ticket_is_refused():
    with _Corpus({"t": {"state": _TWO}}), tempfile.TemporaryDirectory() as td:
        e = _expect_red(lambda: _cross(_TWO, "WATCHME", ticket="t", td=td))
        assert "carries no watchme spec" in str(e) and _OBJ in str(e), e
        assert e.findings and e.findings[0]["judge"] == "watchme_spec", e.findings


def test_a_promised_probe_the_world_does_not_hold_is_refused():
    spec = _spec(probe="cairn/base/probes/a_probe_nobody_wrote.py")
    with _Corpus({"t": {"state": _TWO, "watchme": [spec]}}), \
            tempfile.TemporaryDirectory() as td:
        e = _expect_red(lambda: _cross(_TWO, "WATCHME", ticket="t", td=td))
        assert "no probe is berthed at" in str(e), e
        assert "a_probe_nobody_wrote.py" in str(e), \
            "the refusal names the path it looked at — done is verified in the world"


def test_a_berth_that_declares_no_probe_is_not_armed():
    with tempfile.TemporaryDirectory() as td:
        hollow = Path(td) / "hollow.py"
        hollow.write_text("# a module, but not a declaration\nX = 1\n", encoding="utf-8")
        err = watchme_spec.armed_error(_spec(probe=str(hollow)))
        assert "declares no module-level PROBE" in err, err


def test_a_probe_that_cannot_gather_is_berthed_but_not_armed():
    """ACCUMULATION, NOT EMISSION — the phrase the ticket refuses, made a measurement."""
    with tempfile.TemporaryDirectory() as td:
        for name, body, want in (
            ("no_carry", "carry=None, enough=lambda c: True", "carries no `carry`"),
            ("no_enough", "carry=lambda c: {}, enough=None", "declares no `enough`"),
        ):
            f = Path(td) / f"{name}.py"
            f.write_text(
                "from cairn.base.probe import Probe\n"
                "PROBE = Probe(why='w', trigger=lambda n, c: True, to='harbor_master', %s)\n"
                % body, encoding="utf-8")
            err = watchme_spec.armed_error(_spec(probe=str(f)))
            assert err and want in err, f"{name}: {err}"
            assert "berthed but not armed" in err, err


def test_a_back_edge_into_watchme_is_ungated():
    """LOAD-BEARING. The owner re-arms a watch whose verdict came back failed; gating the
    retreat would trap the boat at the one state it must be able to return to (Law 6)."""
    with _Corpus({}), tempfile.TemporaryDirectory() as td:
        new, hist = _cross(_AT_PROVED, "WATCHME", td=td)      # no ticket, no spec, no probe
        assert f"[WATCHME({_OBJ})]" in new, new
        assert hist[-1]["direction"] == "back", hist[-1]
        assert "emission_gate" not in hist[-1], \
            "a retreat is not a gated crossing — and must not journal as if it were"


def test_a_refusal_journals_absolutely_nothing():
    """LOAD-BEARING. A refused move leaves no partial record."""
    with _Corpus({}), tempfile.TemporaryDirectory() as td:
        _expect_red(lambda: _cross(_TWO, "WATCHME", td=td))
        assert not Path(f"{td}/history.json").exists(), \
            "the gate raised BEFORE the write — a half-written crossing is worse than none"
        assert not Path(f"{td}/state.json").exists()


def test_it_is_a_sibling_not_a_subclass_of_the_other_four():
    for other in (transitions.EntryGateRed, transitions.BuildGateRed,
                  transitions.ExitGateRed, transitions.TicketRequiredRed):
        assert not issubclass(transitions.WatchmeEmissionRed, other), other
        assert not issubclass(other, transitions.WatchmeEmissionRed), other
    assert issubclass(transitions.WatchmeEmissionRed, transitions.IllegalTransition), \
        "every gate refusal is still an IllegalTransition — one handler can catch them all " \
        "on purpose, but never one by accident"


def test_a_node_that_carries_no_watch_is_untouched():
    """The crossing must COMPLETE, not merely avoid this seat's refusal.

    STRENGTHENED 2026-08-03. It used to cross PROVEME -> PROVED and accept any
    ``IllegalTransition`` as "some other gate's business". That made it green for a weaker
    reason than it claimed: PROVEME-forward is the BUILD gate's crossing, so the tooth was
    passing because ``BuildGateRed`` refused first — it never reached a state where the
    emission gate's silence was the thing being observed. A synthetic fixture can never clear
    the build gate (no charter, no proofs), so the answer is not a richer fixture: it is to
    cross where NO OTHER GATE SITS. BUILDME -> PROVEME is that crossing — the build gate reads
    ``here == PROVEME``, the entry gate ``target == BUILDME``, the exit gate
    ``target == PROVED``, and none of them is this. What is left is exactly this seat, silent,
    and a completed crossing proves the silence.
    """
    bare = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"
    with _Corpus({}), tempfile.TemporaryDirectory() as td:
        try:
            new, hist = _cross(bare, "PROVEME", ticket="nope", td=td)
        except transitions.WatchmeEmissionRed as e:
            raise AssertionError(
                f"the emission gate fired at a crossing with no WATCHME in it: {e}") from e
        assert "[PROVEME]" in new, new
        assert "emission_gate" not in hist[-1], \
            "a crossing that carries no watch must journal no emission_gate note — a gate " \
            f"that annotates a crossing it does not govern is claiming jurisdiction: {hist[-1]}"


def test_the_gate_reads_the_watch_the_boat_STANDS_at():
    """Two watches, two obligations: crossing out of the first must be answered by the FIRST
    object's spec. A gate that matched any spec on the ticket would let one probe discharge
    every watch the node carries."""
    two = ("code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
           "[WATCHME(first-question)] -> WATCHME(second-question) -> PROVED")
    tick = {"state": two, "watchme": [_spec(object="second-question")]}
    with _Corpus({"t": tick}), tempfile.TemporaryDirectory() as td:
        e = _expect_red(lambda: _cross(two, "WATCHME", ticket="t", td=td))
        assert "first-question" in str(e), e

    tick["watchme"].append(_spec(object="first-question"))
    with _Corpus({"t": tick}), tempfile.TemporaryDirectory() as td:
        new, hist = _cross(two, "WATCHME", ticket="t", td=td)
        assert "[WATCHME(second-question)]" in new, new
        assert "first-question" in hist[-1]["emission_gate"], hist[-1]


def test_the_real_berth_in_this_repo_is_armed():
    """No fixture at all — the probe this voyage actually berthed, measured on real disk."""
    assert watchme_spec.armed_error({"probe": _REAL_BERTH}) is None, \
        watchme_spec.armed_error({"probe": _REAL_BERTH})


TESTS = [
    test_an_emitted_watch_crosses_and_the_journal_names_the_berth,
    test_a_crossing_with_no_ticket_cannot_be_measured_so_it_is_refused,
    test_a_carried_watch_with_no_spec_on_the_ticket_is_refused,
    test_a_promised_probe_the_world_does_not_hold_is_refused,
    test_a_berth_that_declares_no_probe_is_not_armed,
    test_a_probe_that_cannot_gather_is_berthed_but_not_armed,
    test_a_back_edge_into_watchme_is_ungated,
    test_a_refusal_journals_absolutely_nothing,
    test_it_is_a_sibling_not_a_subclass_of_the_other_four,
    test_a_node_that_carries_no_watch_is_untouched,
    test_the_gate_reads_the_watch_the_boat_STANDS_at,
    test_the_real_berth_in_this_repo_is_armed,
]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as e:                    # noqa: BLE001 — a crash is a fail, not an
            failures += 1                         # abort: a hollowing run must stay readable
            print(f"  FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)

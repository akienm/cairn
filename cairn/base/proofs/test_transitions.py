"""Proof: the EMIT-CHOKEPOINT (cairn/base/transitions.py) makes the state vocabulary PHYSICS.

The gate a hollow build could not pass (tickets/state-machine-physics.json): a node whose
workflow attempts an ILLEGAL transition is REFUSED (a skip past a gate summons, a target
outside the vocabulary, an unknown class/version, a no-op, a drifted path, a PROVEME exit
while the component reds the build_inspector); a LEGAL transition
moves the cursor AND journals the crossing append-only; the string is version-validated against
a KNOWN node-class definition; a back-edge (kick-back) is legal and carries its severity.

Non-hollow: validated against the REAL registered table (node_classes/code-seam.json) and the
REAL projector door — not a stand-in — and it parses an actual ticket's live workflow string
(trailing prose and all). A green over a toy table or a swallowed refusal would be hollow.

Dependency-light: pure parsing + the projector's pure core. Runs bare.

    python3 cairn/base/proofs/test_transitions.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base import transitions
from cairn.charter import projector

_CODE_SEAM = "code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"


def _expect_refused(fn, exc=transitions.IllegalTransition):
    try:
        fn()
    except exc:
        return
    raise AssertionError("expected a refusal (a silent pass would be policy, not physics — Law 4/7)")


def test_a_legal_forward_advance_journals_the_crossing():
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        new = transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        assert "[PROVEME]" in new and "[BUILDME]" not in new, f"cursor did not move to PROVEME: {new}"
        log = projector.read_history(hist)
        assert len(log) == 1, "the crossing was not journaled exactly once (Law 7 append-only)"
        rec = log[0]
        assert rec["from"] == "BUILDME" and rec["to"] == "PROVEME" and rec["direction"] == "forward"
        assert rec["workflow"] == new, "the journal did not record the resulting workflow string"


def test_the_crossing_carries_where_the_boat_now_stands():
    """The emitter derives ``standing``; no caller has to remember it.

    FOUND BY THE APPEND DOOR'S SHAPE GATE, 2026-07-25, before this emitter had ever written
    to a live history: it journaled from/to/workflow/direction and NO ``standing``, which is
    the one field harbor_master's register reads to place a boat. Every such record would
    have been permanently unreadable (Law 7 — append-only, no edit afterwards). The gate
    refused it at the door instead, which is the whole reason the gate exists.
    """
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        rec = projector.read_history(hist)[0]
    assert rec["standing"] == "PROVEME", \
        f"a crossing that does not say where the boat stands cannot be read — got {rec.get('standing')!r}"
    assert all(rec.get(k) for k in projector.UNIVERSAL_REQUIRED), \
        "the emitter's record must clear the door's floor by construction, not by luck"


def test_a_caller_may_say_it_richer_but_may_not_drop_it():
    """``journal_extra`` overrides the derived standing (a berth line says more than a gate
    name) — the default is a FLOOR, not a ceiling. What it cannot do is omit it."""
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state,
                         standing="PROVEME — green under the tester, VALIDATION sealed beside it")
        rec = projector.read_history(hist)[0]
    assert rec["standing"].startswith("PROVEME — green"), "the caller's richer line must win"
    assert rec["to"] == "PROVEME", "and the machine-readable target is untouched beside it"


def test_the_leaf_fork_thinkme_may_go_to_ticketme_or_buildme():
    at_think = "code-seam@v1: [THINKME] -> TICKETME -> BUILDME -> PROVEME -> LEARNME -> PROVED"
    # decompose (parent) and build (leaf, skipping the skippable TICKETME) are BOTH legal
    assert "[TICKETME]" in transitions.emit(at_think, "TICKETME")
    assert "[BUILDME]" in transitions.emit(at_think, "BUILDME")


def test_a_forward_skip_past_a_gate_summons_is_refused():
    # BUILDME -> PROVED would skip PROVEME (a non-skippable gate summons) — physics refuses it
    _expect_refused(lambda: transitions.emit(_CODE_SEAM, "PROVED"))
    _expect_refused(lambda: transitions.emit(_CODE_SEAM, "LEARNME"))   # skips PROVEME too


def test_a_target_outside_the_vocabulary_is_refused():
    _expect_refused(lambda: transitions.emit(_CODE_SEAM, "FROBME"))


def test_a_no_op_self_transition_is_refused():
    _expect_refused(lambda: transitions.emit(_CODE_SEAM, "BUILDME"))


def test_an_unknown_class_or_version_is_refused():
    _expect_refused(lambda: transitions.emit("no-such-class@v1: [THINKME] -> PROVED", "PROVED"))
    _expect_refused(lambda: transitions.emit(
        "code-seam@v9: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED", "PROVEME"))


def test_a_drifted_path_that_claims_v1_is_refused():
    # claims code-seam@v1 but the path is mangled (TICKETME dropped) — not a valid v1 instance
    drifted = "code-seam@v1: THINKME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"
    _expect_refused(lambda: transitions.emit(drifted, "PROVEME"), exc=transitions.MalformedWorkflow)


_SKILL_V1 = "skill@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"


def test_a_skill_v1_workflow_validates_and_journals_a_crossing_at_a_fixture_skill_address():
    """ticket skills-ride-the-chokepoint: class skill@v1 is now registered
    (CairnCommons/node_classes/skill.json), so a skill node rides the SAME
    chokepoint a code-seam does — zero new code paths, only the registry the
    loader already reads. A fixture skill address (skills/fixture-skill/) proves
    it journals exactly like a code-seam crossing: workflow/standing/direction
    all present, the append door happy."""
    with tempfile.TemporaryDirectory() as d:
        comp = Path(d) / "skills" / "fixture-skill"
        comp.mkdir(parents=True)
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        new = transitions.emit(_SKILL_V1, "PROVEME", history_path=hist, state_path=state)
        assert "[PROVEME]" in new and "[BUILDME]" not in new, f"cursor did not move: {new}"
        rec = projector.read_history(hist)[0]
        assert rec["from"] == "BUILDME" and rec["to"] == "PROVEME" and rec["direction"] == "forward"
        assert rec["standing"] == "PROVEME" and rec["workflow"] == new


def test_a_drifted_skill_path_that_claims_v1_is_refused():
    # claims skill@v1 but the path is mangled (TICKETME dropped) — not a valid v1 instance,
    # the same conformance check code-seam@v1 rides, applied to the new class with zero
    # new code (_conform reads node_classes/skill.json's registered path generically).
    drifted = "skill@v1: THINKME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"
    _expect_refused(lambda: transitions.emit(drifted, "PROVEME"), exc=transitions.MalformedWorkflow)


def test_an_unknown_class_still_refuses_after_skill_registration():
    # Registering class skill must not widen the door for a class that was never
    # registered at all — the fix must not widen the door (the ticket's falsifier).
    _expect_refused(lambda: transitions.emit("never-registered@v1: [THINKME] -> PROVED", "PROVED"))


def test_a_back_edge_kickback_is_legal_and_carries_severity():
    at_prove = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> LEARNME -> PROVED"
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        new = transitions.emit(at_prove, "BUILDME", history_path=hist, state_path=state)
        assert "[BUILDME]" in new, f"kick-back did not move the cursor: {new}"
        rec = projector.read_history(hist)[0]
        assert rec["direction"] == "back" and rec["severity"] == 1, f"severity not carried: {rec}"
        # a deeper kick-back to THINKME is legal with greater severity (2)
        assert transitions.parse_workflow(transitions.emit(at_prove, "THINKME")).here == "THINKME"
    # the last forward advance into the rest is legal — LEARNME -> PROVED reaches the rest
    at_learn = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> [LEARNME] -> PROVED"
    assert "[PROVED]" in transitions.emit(at_learn, "PROVED"), "the PROVED rest is unreachable"


def test_it_parses_a_real_live_ticket_workflow_string():
    # A real on-disk ticket with trailing prose after the cursor — proves the parser survives the
    # wild format and that the ticket is a CONFORMANT v1 instance. Picks ANY live code-seam@v1 ticket
    # from CairnCommons/tickets/ rather than a pinned filename: a ticket legitimately berths beside its
    # code and leaves the open lane (harbor-master did, 2026-07-24), so pinning one file re-derives a
    # moving target (Law 1). Asserts INVARIANTS on whichever ticket it finds — never a live cursor value.
    # VERSION-AGNOSTIC SINCE 2026-08-03, and that is the same lesson twice. This tooth already
    # stopped pinning a FILENAME (a ticket berths beside its code and leaves the lane); it was
    # still pinning a VERSION, and Akien's scrub sweep migrated the last v1 ticket off the disk,
    # so it went red announcing an absent fixture rather than a defect. The parser does not care
    # which version a string claims — take any live code-seam ticket and conform it against the
    # registered path for the version IT claims. Asserts INVARIANTS, never a live cursor value.
    tickets_dir = _REPO_ROOT.parent / "CairnCommons" / "tickets"
    versions = transitions.load_class_def("code-seam")["workflow_versions"]
    found = None
    for t in sorted(tickets_dir.glob("*.json")):
        try:
            state = json.loads(t.read_text()).get("state")
            wf = transitions.parse_workflow(state) if isinstance(state, str) else None
        except (ValueError, OSError):
            continue                      # prose state / garbled ticket — not a code-seam workflow string
        if not (wf and wf.node_class == "code-seam" and wf.version in versions):
            continue
        reg = versions[wf.version]
        free = set(reg.get("free_summons", []))
        if [x for x in wf.path if x not in free] == list(reg["path"]):
            found = (t.name, wf, tuple(reg["path"]), free)
            break
    assert found, ("no live code-seam ticket in CairnCommons/tickets/ conforms to any registered "
                   "version — the real-ticket tooth needs at least one on-disk code-seam ticket "
                   "(a green over zero would be hollow, Law 8)")
    name, wf, canonical, free = found
    assert wf.here in canonical or wf.here in free, \
        f"cursor mis-parsed from the real string ({name}, not a real stage): {wf.here}"


def test_prose_after_the_last_state_cannot_feed_phantom_states_onto_the_path():
    """An ARROW INSIDE THE TRAILING NOTE must not extend the path. Regression, 2026-07-26.

    The parser split on '->' across the whole remainder and only stopped at a segment that failed to
    start with a state token — so a note naming another workflow appended its states to this one.
    state-machine-physics.json's real 6-state path parsed as 9, and nothing raised: `here`,
    `legal_targets` and every reader of `path` were handed fiction. A silent wrong answer is the
    costly direction (Law 7), and _conform caught it only by accident of comparing whole paths.

    THE TOOTH ABOVE COULD NOT CATCH THIS, and that is the instructive part: it searches for a ticket
    whose path already equals canonical, so a ticket parsing to 9 states silently failed to match and
    the scan moved on to a healthy one. A proof that skips the malformed case passes because of the
    defect. This tooth asserts the path EXACTLY, on a string built to carry the trap.
    """
    canonical = tuple(transitions.load_class_def("code-seam")["workflow_versions"]["v1"]["path"])
    trap = ("code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED   "
            "(cursor at BUILDME: the concept-piece workflow THINKME -> REVIEWME -> PROVED is a "
            "child of this node, and mentioning it here must not extend this path)")
    wf = transitions.parse_workflow(trap)
    assert wf.path == canonical, (
        f"prose bled into the path: parsed {wf.path}, expected {canonical} — an arrow inside the "
        "trailing note must not append states")
    assert wf.here == "BUILDME", f"cursor moved under the prose: {wf.here}"
    # And it must still CONFORM, which is the reader that got lucky last time.
    transitions.legal_targets(wf, class_def=transitions.load_class_def("code-seam"))


def _component(root: Path, name: str, *, charter=True) -> Path:
    """A minimal census-visible component: code + proofs (+ charter unless withheld) — the
    build gate judges the component AT THE CROSSING'S ADDRESS, so the fixture is a directory,
    not a mock. A plain module (no BaseDevice), so silence is legitimately fine."""
    d = root / name
    (d / "proofs").mkdir(parents=True)
    (d / "proofs" / "test_x.py").write_text("assert True\n")
    (d / "lib.py").write_text("def helper():\n    return 1\n")
    if charter:
        (d / "intention+why.json").write_text('{"component": "%s"}' % name)
    return d


_AT_PROVE = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> LEARNME -> PROVED"


def test_the_build_gate_refuses_a_proveme_exit_while_the_inspector_reds():
    """build_inspector edge (a) LANDED: the forward crossing OUT of PROVEME is refused while
    the component at the crossing's own address reds the gate — and NOTHING is journaled, so
    a refused promotion leaves no partial record. The findings ride the exception complete on
    the first pass (no 'run the inspector for details')."""
    with tempfile.TemporaryDirectory() as d:
        comp = _component(Path(d), "chartless", charter=False)
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        try:
            transitions.emit(_AT_PROVE, "LEARNME", history_path=hist, state_path=state)
        except transitions.BuildGateRed as e:
            assert [f["filter"] for f in e.findings] == ["charter_on_disk"], e.findings
            assert "charter_on_disk" in str(e) and "Law 8" in str(e), \
                "the refusal must carry the findings and the why, first pass, in the message"
        else:
            raise AssertionError("a red component crossed the PROVEME gate — the lever is not wired")
        assert not Path(hist).exists(), "a REFUSED crossing must write no record of truth"


def test_a_clean_component_crosses_and_the_journal_carries_the_gate_verdict():
    with tempfile.TemporaryDirectory() as d:
        comp = _component(Path(d), "healthy")
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        new = transitions.emit(_AT_PROVE, "LEARNME", history_path=hist, state_path=state)
        assert "[LEARNME]" in new
        rec = projector.read_history(hist)[0]
        assert rec["build_gate"].startswith("clean — build_inspector"), \
            f"a promotion's evidence must travel with the crossing: {rec}"


def test_a_kickback_out_of_proveme_is_never_gated():
    # Retreating on a red is the CORRECT move — the same red component that cannot go
    # forward must always be allowed back to BUILDME, or the gate becomes a trap.
    with tempfile.TemporaryDirectory() as d:
        comp = _component(Path(d), "chartless", charter=False)
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        new = transitions.emit(_AT_PROVE, "BUILDME", history_path=hist, state_path=state)
        assert "[BUILDME]" in new and projector.read_history(hist)[0]["direction"] == "back"


def test_jurisdiction_an_unaddressed_proveme_exit_is_a_string_calculation_only():
    # No history_path → no journal → the record of truth does not move, so there is no
    # component address to inspect and nothing the gate protects. (The register reads
    # project(history); a promotion that writes no truth has not happened anywhere.)
    assert "[LEARNME]" in transitions.emit(_AT_PROVE, "LEARNME")


def test_an_address_the_census_cannot_see_is_refused_not_waved_through():
    # NO SIDE DOOR (Law 8): a history homed where the census sees no component (here: a bare
    # directory with no code — the bin/ shape) reds the crossing loudly, and the refusal
    # names the growth path instead of silently skipping the gate.
    with tempfile.TemporaryDirectory() as d:
        bare = Path(d) / "codeless"
        bare.mkdir()
        (Path(d) / "neighbor" / "proofs").mkdir(parents=True)  # census has a world to see
        (Path(d) / "neighbor" / "x.py").write_text("pass\n")
        hist, state = str(bare / "history.json"), str(bare / "state.json")
        try:
            transitions.emit(_AT_PROVE, "LEARNME", history_path=hist, state_path=state)
        except transitions.BuildGateRed as e:
            assert "census" in str(e) and "grow" in str(e), \
                "an uninspectable address must be refused WITH its disposition named"
        else:
            raise AssertionError("an uninspectable address slipped past the gate — the side door is open")
        assert not Path(hist).exists()


_AT_TICKET = "code-seam@v1: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> LEARNME -> PROVED"


def _entry_world(d: Path, *, cast=("widget",), claims=()):
    """A fixture commons-tickets + chart-berths pair for the ENTRY GATE teeth —
    both chokepoint globals patched, so no tooth reads live instance-space."""
    tickets = d / "tickets"
    tickets.mkdir()
    for t in cast:
        (tickets / f"{t}.json").write_text("{}")
    berths = d / "berths"
    (berths / "0" / "packets").mkdir(parents=True)
    for i, t in enumerate(claims):
        (berths / "0" / "packets" / f"validate-20260729T00000{i}-feed.json").write_text(
            json.dumps({"ticket": t}))
    return tickets, berths


def test_the_entry_gate_refuses_a_chartless_buildme_for_a_cast_ticket():
    """buildme-rides-the-chart LANDED: the forward crossing INTO BUILDME naming a cast
    ticket is refused while no berthed chart chain claims it — and NOTHING is journaled.
    The findings ride the exception complete on the first pass; the refusal names the
    disposition (run /chart), the same physics as skipping a stage inside the chain."""
    import cairn.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _entry_world(Path(d), cast=("widget",), claims=())
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            try:
                transitions.emit(_AT_TICKET, "BUILDME",
                                 history_path=hist, state_path=state, ticket="widget")
            except transitions.EntryGateRed as e:
                assert [f["filter"] for f in e.findings] == ["buildme_rides_the_chart"], e.findings
                assert "widget" in str(e) and "/chart" in str(e), \
                    "the refusal must name the ticket and the disposition, first pass"
            else:
                raise AssertionError("a chartless BUILDME crossed — the entry gate is not wired")
            assert not Path(hist).exists(), "a REFUSED crossing must write no record of truth"
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


def test_a_charted_buildme_crosses_and_the_journal_carries_the_entry_verdict():
    import cairn.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _entry_world(Path(d), cast=("widget",), claims=("widget",))
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            new = transitions.emit(_AT_TICKET, "BUILDME",
                                   history_path=hist, state_path=state, ticket="widget")
            assert "[BUILDME]" in new
            rec = projector.read_history(hist)[0]
            assert rec["entry_gate"].startswith("clean — a berthed chart chain claims"), \
                f"the crossing's evidence must say the entry gate ran: {rec}"
            assert rec["ticket"] == "widget"
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


def test_the_entry_gate_requires_a_named_cast_ticket_backedges_stay_ungated():
    """ticket a-voyage-names-its-ticket, 2026-07-29: REWRITES the tooth above, which
    asserted the OPPOSITE — unnamed/uncast crossed ungated. The jurisdiction inverted:
    an unnamed forward BUILDME crossing now refuses (routing to /sorted), a
    named-but-uncast one refuses with DISTINCT wording (never treated as exempt), and
    both refuse BEFORE anything is written (no history file exists at all — the
    exit-gate tooth below covers the byte-identical-with-a-prior-record case). A
    kick-back INTO BUILDME (retreating is the correct move) is UNTOUCHED — still
    crosses ungated, exactly as before this stone (bounds: back-edges are OUT)."""
    with tempfile.TemporaryDirectory() as d:
        tickets, _ = _entry_world(Path(d), cast=("widget",), claims=())
        saved = transitions._TICKETS
        transitions._TICKETS = tickets
        try:
            base = Path(d)
            # unnamed: refuses, routes to /sorted, nothing journaled
            hist, state = str(base / "h_unnamed.json"), str(base / "s_unnamed.json")
            try:
                transitions.emit(_AT_TICKET, "BUILDME", history_path=hist, state_path=state)
            except transitions.TicketRequiredRed as e:
                unnamed_msg = str(e)
                assert "no ticket is named" in unnamed_msg and "/sorted" in unnamed_msg
            else:
                raise AssertionError("an unnamed forward BUILDME crossed — the door is not wired")
            assert not Path(hist).exists(), "a refused crossing must write no record of truth"
            # named-but-uncast: refuses too, but with DISTINCT wording — never exempt
            hist2, state2 = str(base / "h_uncast.json"), str(base / "s_uncast.json")
            try:
                transitions.emit(_AT_TICKET, "BUILDME", history_path=hist2, state_path=state2,
                                 ticket="ghost-never-cast")
            except transitions.TicketRequiredRed as e:
                uncast_msg = str(e)
                assert "not cast" in uncast_msg and "ghost-never-cast" in uncast_msg
                assert "no ticket is named" not in uncast_msg, "wording must differ from the unnamed case"
                assert "not cast" not in unnamed_msg, "wording must differ from the uncast case"
            else:
                raise AssertionError("a named-but-uncast BUILDME crossed — treated as exempt, wrongly")
            assert not Path(hist2).exists(), "a refused crossing must write no record of truth"
            # a kick-back INTO BUILDME, no ticket at all — still crosses ungated (untouched)
            hist3, state3 = str(base / "hb.json"), str(base / "sb.json")
            new = transitions.emit(_AT_PROVE, "BUILDME", history_path=hist3, state_path=state3)
            rec = projector.read_history(hist3)[0]
            assert "[BUILDME]" in new and rec["direction"] == "back"
            assert "entry_gate" not in rec, "a kick-back into BUILDME is never gated"
        finally:
            transitions._TICKETS = saved


def test_the_entry_gate_exempt_roster_entry_passes_gated_and_clean():
    """The explicit exempt roster (ticket a-voyage-names-its-ticket): EMPTY in v0 by
    measure (asserted below as an invariant on the shipped module), but a FIXTURE
    entry proves the machinery — an unnamed crossing whose own component name is on
    the roster passes, and the pass is JOURNALED as an exemption (gated-and-clean,
    never silent), through the same ``entry_gate`` key the real gate uses."""
    assert transitions._EXEMPT_ROSTER == frozenset(), \
        "the shipped roster must be empty by measure — a real entry is a deliberate act"
    with tempfile.TemporaryDirectory() as d:
        comp = Path(d) / "legacy-component"
        comp.mkdir()
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        saved = transitions._EXEMPT_ROSTER
        transitions._EXEMPT_ROSTER = frozenset({"legacy-component"})
        try:
            new = transitions.emit(_AT_TICKET, "BUILDME", history_path=hist, state_path=state)
            assert "[BUILDME]" in new
            rec = projector.read_history(hist)[0]
            assert rec["entry_gate"].startswith("exempt —"), \
                f"an exempt pass must journal its exemption, never silently: {rec}"
            assert "legacy-component" in rec["entry_gate"]
        finally:
            transitions._EXEMPT_ROSTER = saved


_AT_TICKET_SKILL = "skill@v1: THINKME -> [TICKETME] -> BUILDME -> PROVEME -> LEARNME -> PROVED"


def test_the_entry_gate_refuses_a_chartless_skill_buildme_for_a_cast_ticket():
    """ticket skills-ride-the-chokepoint: the entry gate is class-agnostic — it keys
    on the crossing's own named ticket, never on node_class — so a skill-class
    voyage naming a cast ticket with no berthed chart chain refuses IDENTICALLY to
    a code-seam one (mirrors test_the_entry_gate_refuses_a_chartless_buildme_for_a_cast_ticket
    above, skill@v1 in place of code-seam@v1)."""
    import cairn.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _entry_world(Path(d), cast=("widget",), claims=())
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            try:
                transitions.emit(_AT_TICKET_SKILL, "BUILDME",
                                 history_path=hist, state_path=state, ticket="widget")
            except transitions.EntryGateRed as e:
                assert [f["filter"] for f in e.findings] == ["buildme_rides_the_chart"], e.findings
                assert "widget" in str(e) and "/chart" in str(e), \
                    "the refusal must name the ticket and the disposition, first pass"
            else:
                raise AssertionError("a chartless skill-class BUILDME crossed — the entry gate is not wired for class skill")
            assert not Path(hist).exists(), "a REFUSED crossing must write no record of truth"
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


def test_a_charted_skill_buildme_crosses_and_the_journal_carries_the_entry_verdict():
    """The mirror pass: a skill-class voyage naming a cast ticket a berthed chart
    chain DOES claim crosses gated-and-clean, journal shape identical to a
    code-seam crossing — the entry gate is physics over the ticket, not the class."""
    import cairn.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _entry_world(Path(d), cast=("widget",), claims=("widget",))
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            new = transitions.emit(_AT_TICKET_SKILL, "BUILDME",
                                   history_path=hist, state_path=state, ticket="widget")
            assert "[BUILDME]" in new
            rec = projector.read_history(hist)[0]
            assert rec["entry_gate"].startswith("clean — a berthed chart chain claims"), \
                f"the crossing's evidence must say the entry gate ran: {rec}"
            assert rec["ticket"] == "widget"
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


_AT_LEARN = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> [LEARNME] -> PROVED"


def _exit_world(d: Path, *, cast=("widget",), claim=True, verdict=None):
    """A fixture commons-tickets + chart-berths pair for the EXIT GATE teeth — a
    claiming chain deep enough to owe answers (hypothesize <- validate), plus an
    optional verdict artifact in the named shape. Both chokepoint globals patched
    by the caller, so no tooth reads live instance-space."""
    tickets = d / "tickets"
    tickets.mkdir()
    for t in cast:
        (tickets / f"{t}.json").write_text("{}")
    berths = d / "berths"
    packets = berths / "0" / "packets"
    packets.mkdir(parents=True)
    if claim:
        hyp = packets / "hypothesize-20260729T000000-feed.json"
        hyp.write_text(json.dumps({"hypotheses": [
            {"piece": "p1", "expect": "e1", "falsifier": "f", "instrument": "i"}]}))
        val = packets / "validate-20260729T000001-feed.json"
        val.write_text(json.dumps({"ticket": "widget", "hypothesize_ref": str(hyp),
                                   "criteria": [{"claim": "c1", "instrument": "cmd",
                                                 "covers": ["p1"]}]}))
        if verdict is not None:
            (packets / "verdict-20260729T000002-feed.json").write_text(json.dumps(
                {"ticket": "widget", "validate_ref": str(val), **verdict}))
    return tickets, berths


_ANSWERED = {
    "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                  "evidence": "seen: exit 0 twice"}],
    "dispositions": [{"piece": "p1", "expect": "e1", "disposition": "confirmed",
                      "by": "the run observed"}],
}


def test_the_exit_gate_refuses_an_unanswered_proved_and_the_record_stands_still():
    """proved-answers-the-chart LANDED: the forward crossing INTO PROVED naming a cast,
    CLAIMED ticket is refused while the chart is unanswered — and the record of truth
    is byte-identical after the refusal (nothing journaled, nothing touched). The
    findings ride the exception complete on the first pass; a FAILED criterion refuses
    as loudly as an unanswered one (PROVED asserts done; a fail is a kick-back)."""
    import hashlib as _hashlib
    import cairn.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _exit_world(Path(d), verdict=None)  # claimed, never answered
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            # a real prior record on disk — the refusal must leave it byte-identical
            # (named here — ticket a-voyage-names-its-ticket tightened the entry door
            # this setup rides too, so its scaffolding crossing names its ticket now)
            transitions.emit(_AT_TICKET, "BUILDME", history_path=hist, state_path=state,
                             ticket="widget")
            before = _hashlib.sha256(Path(hist).read_bytes()).hexdigest()
            try:
                transitions.emit(_AT_LEARN, "PROVED",
                                 history_path=hist, state_path=state, ticket="widget")
            except transitions.ExitGateRed as e:
                assert [f["filter"] for f in e.findings] == ["proved_answers_the_chart"], \
                    e.findings
                assert "widget" in str(e) and "write_verdict" in str(e), \
                    "the refusal must name the ticket and the disposition, first pass"
            else:
                raise AssertionError("an unanswered PROVED crossed — the exit gate is not wired")
            assert _hashlib.sha256(Path(hist).read_bytes()).hexdigest() == before, \
                "a REFUSED crossing must leave the record of truth byte-identical"
            # answered-and-FAILED: still refused, and the refusal says FAILED
            packets = berths / "0" / "packets"
            (packets / "verdict-20260729T000002-feed.json").write_text(json.dumps(
                {"ticket": "widget",
                 "validate_ref": str(packets / "validate-20260729T000001-feed.json"),
                 "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "fail",
                               "evidence": "it broke"}],
                 "dispositions": _ANSWERED["dispositions"]}))
            try:
                transitions.emit(_AT_LEARN, "PROVED",
                                 history_path=hist, state_path=state, ticket="widget")
            except transitions.ExitGateRed as e:
                assert "FAILED" in str(e), "a failed criterion must refuse BY NAME"
            else:
                raise AssertionError("a FAILED criterion crossed into PROVED")
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


def test_an_answered_proved_crosses_and_the_journal_carries_the_exit_verdict():
    import cairn.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _exit_world(Path(d), verdict=_ANSWERED)
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            new = transitions.emit(_AT_LEARN, "PROVED",
                                   history_path=hist, state_path=state, ticket="widget")
            assert "[PROVED]" in new
            rec = projector.read_history(hist)[0]
            assert rec["exit_gate"].startswith("clean — no unanswered chart claim"), \
                f"the crossing's evidence must say the exit gate ran: {rec}"
            assert rec["ticket"] == "widget"
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


def test_the_exit_gate_requires_a_named_cast_ticket_unclaimed_stays_gated_clean():
    """ticket a-voyage-names-its-ticket, 2026-07-29: REWRITES the tooth above, which
    asserted unnamed/uncast crossed ungated. Inverted: unnamed and named-but-uncast
    forward PROVED crossings now refuse (TicketRequiredRed, distinct wording), and a
    PRIOR record on disk is left byte-identical (sha256) — the same discipline the
    unanswered-PROVED tooth pins. UNTOUCHED: a CAST ticket no chart claims still
    crosses PROVED gated-and-clean (the gate ran, the record says so honestly) — that
    behavior belongs to ``_exit_gate`` below the new precondition and this stone does
    not touch it."""
    import hashlib as _hashlib
    import cairn.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _exit_world(Path(d), claim=False)  # cast, but NO claiming chart
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            base = Path(d)
            hist, state = str(base / "history.json"), str(base / "state.json")
            # a real prior record on disk — refusal must leave it byte-identical. A
            # neutral non-BUILDME/PROVED crossing builds it (untouched by this stone,
            # so it needs no ticket) rather than a BUILDME/PROVED crossing, which would
            # now collide with the very rule this tooth tests.
            transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
            before = _hashlib.sha256(Path(hist).read_bytes()).hexdigest()
            # unnamed: refuses, routes to /sorted
            try:
                transitions.emit(_AT_LEARN, "PROVED", history_path=hist, state_path=state)
            except transitions.TicketRequiredRed as e:
                unnamed_msg = str(e)
                assert "no ticket is named" in unnamed_msg and "/sorted" in unnamed_msg
            else:
                raise AssertionError("an unnamed forward PROVED crossed — the door is not wired")
            assert _hashlib.sha256(Path(hist).read_bytes()).hexdigest() == before, \
                "a refused crossing must leave the record of truth byte-identical"
            # named-but-uncast: refuses too, with DISTINCT wording — never exempt
            try:
                transitions.emit(_AT_LEARN, "PROVED", history_path=hist, state_path=state,
                                 ticket="ghost-never-cast")
            except transitions.TicketRequiredRed as e:
                uncast_msg = str(e)
                assert "not cast" in uncast_msg and "ghost-never-cast" in uncast_msg
                assert "no ticket is named" not in uncast_msg, "wording must differ from the unnamed case"
            else:
                raise AssertionError("a named-but-uncast PROVED crossed — treated as exempt, wrongly")
            assert _hashlib.sha256(Path(hist).read_bytes()).hexdigest() == before, \
                "a refused crossing must leave the record of truth byte-identical"
            # UNTOUCHED: a cast ticket NO chart claims still crosses, gated-and-clean
            hist2, state2 = str(base / "hu.json"), str(base / "su.json")
            new = transitions.emit(_AT_LEARN, "PROVED",
                                   history_path=hist2, state_path=state2, ticket="widget")
            rec = projector.read_history(hist2)[0]
            assert "[PROVED]" in new
            assert rec["exit_gate"].startswith("clean — no unanswered chart claim"), \
                "a cast-but-unclaimed crossing is gated-and-clean, on the record — untouched by this stone"
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


def test_the_exit_gate_exempt_roster_entry_passes_gated_and_clean():
    """The explicit exempt roster reaches the exit door too (the same helper serves
    both — ticket a-voyage-names-its-ticket): a fixture roster entry proves an
    unnamed forward PROVED crossing at that component's address passes, journaled as
    an exemption through the ``exit_gate`` key, never silently. No prior crossing is
    needed at this address (mirrors the other exit-gate-only teeth above) — a fresh
    history is the cleanest proof that nothing but the roster let this pass."""
    with tempfile.TemporaryDirectory() as d:
        comp = Path(d) / "legacy-component"
        comp.mkdir()
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        saved = transitions._EXEMPT_ROSTER
        transitions._EXEMPT_ROSTER = frozenset({"legacy-component"})
        try:
            new = transitions.emit(_AT_LEARN, "PROVED", history_path=hist, state_path=state)
            assert "[PROVED]" in new
            rec = projector.read_history(hist)[0]
            assert rec["exit_gate"].startswith("exempt —"), \
                f"an exempt pass must journal its exemption, never silently: {rec}"
            assert "legacy-component" in rec["exit_gate"]
        finally:
            transitions._EXEMPT_ROSTER = saved


def _ledger_world(d: Path, **kw):
    """The exit world plus a FIXTURE ledger path and berths root patched into
    cairn.chart.verdict — the enqueue's two module globals, so no tooth here can
    touch the live instance-space ledger. Returns (tickets, berths, ledger)."""
    import cairn.chart.verdict as _verdict
    tickets, berths = _exit_world(d, **kw)
    ledger = d / "ledger" / "verdict-deposits.jsonl"
    return tickets, berths, ledger, _verdict


def test_a_clean_answered_proved_crossing_enqueues_its_verdict_berth():
    """the-deposit-rides-the-read LANDED: the deposit of a verdict into the tree
    stops being a sail step someone remembers. An exit-gate-CLEAN forward crossing
    into PROVED appends exactly ONE enqueued record naming the artifact that
    answered — and the crossing's own journal carries the berth it filed, so the
    obligation and the crossing share an address (Law 5). File-only: nothing on
    this path reaches a db, an embed host, or the network, which is why a
    netns-sealed crossing enqueues identically (build_inspector edge (l))."""
    import cairn.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths, ledger, _verdict = _ledger_world(Path(d), verdict=_ANSWERED)
        saved = (transitions._TICKETS, _insp._CHART_BERTHS,
                 _verdict.LEDGER_PATH, _verdict.BERTHS_ROOT)
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        _verdict.LEDGER_PATH, _verdict.BERTHS_ROOT = str(ledger), str(berths)
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            artifact = str(berths / "0" / "packets" / "verdict-20260729T000002-feed.json")
            transitions.emit(_AT_LEARN, "PROVED", history_path=hist, state_path=state,
                             ticket="widget")
            lines = [json.loads(line) for line in
                     ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
            assert len(lines) == 1, f"a clean crossing enqueues EXACTLY one record: {lines}"
            assert lines[0]["kind"] == "enqueued" and lines[0]["berth"] == artifact, lines
            assert lines[0]["ticket"] == "widget" and lines[0]["at"], lines
            rec = projector.read_history(hist)[0]
            assert rec["deposit_enqueued"] == artifact, \
                f"the crossing must name the deposit it filed: {rec}"
        finally:
            (transitions._TICKETS, _insp._CHART_BERTHS,
             _verdict.LEDGER_PATH, _verdict.BERTHS_ROOT) = saved


def test_a_refusal_an_unclaimed_crossing_and_a_back_edge_enqueue_nothing():
    """The three silences, each measured. A REFUSED crossing writes no record of
    truth and no ledger line (the gate raises before the enqueue). An UNCLAIMED
    cast ticket crosses gated-and-CLEAN — and enqueues nothing, because the enqueue
    keys on the ARTIFACT, never on the clean note (the exit stone's kill: a clean
    note does not imply an artifact exists; keying on the note would file a pending
    deposit for a file nobody wrote). A BACK-EDGE is never gated and never
    enqueues — retreating owes the tree nothing."""
    import cairn.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        # (1) refusal: claimed, unanswered
        tickets, berths, ledger, _verdict = _ledger_world(Path(d), verdict=None)
        saved = (transitions._TICKETS, _insp._CHART_BERTHS,
                 _verdict.LEDGER_PATH, _verdict.BERTHS_ROOT)
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        _verdict.LEDGER_PATH, _verdict.BERTHS_ROOT = str(ledger), str(berths)
        try:
            hist, state = str(Path(d) / "h1.json"), str(Path(d) / "s1.json")
            _expect_refused(lambda: transitions.emit(
                _AT_LEARN, "PROVED", history_path=hist, state_path=state,
                ticket="widget"), transitions.ExitGateRed)
            assert not ledger.exists(), \
                "a REFUSED crossing must leave no ledger line — not even an empty file"
            # (3) back-edge out of LEARNME: ungated, and owes nothing
            hist3, state3 = str(Path(d) / "h3.json"), str(Path(d) / "s3.json")
            transitions.emit(_AT_LEARN, "BUILDME", history_path=hist3, state_path=state3)
            rec = projector.read_history(hist3)[0]
            assert rec["direction"] == "back" and "deposit_enqueued" not in rec
            assert not ledger.exists(), "a back-edge must enqueue nothing"
        finally:
            (transitions._TICKETS, _insp._CHART_BERTHS,
             _verdict.LEDGER_PATH, _verdict.BERTHS_ROOT) = saved
    with tempfile.TemporaryDirectory() as d:
        # (2) unclaimed: cast ticket, NO claiming chart — gated-and-clean, no artifact
        tickets, berths, ledger, _verdict = _ledger_world(Path(d), claim=False)
        saved = (transitions._TICKETS, _insp._CHART_BERTHS,
                 _verdict.LEDGER_PATH, _verdict.BERTHS_ROOT)
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        _verdict.LEDGER_PATH, _verdict.BERTHS_ROOT = str(ledger), str(berths)
        try:
            hist, state = str(Path(d) / "h2.json"), str(Path(d) / "s2.json")
            transitions.emit(_AT_LEARN, "PROVED", history_path=hist, state_path=state,
                             ticket="widget")
            rec = projector.read_history(hist)[0]
            assert rec["exit_gate"].startswith("clean — no unanswered chart claim"), rec
            assert "deposit_enqueued" not in rec, \
                "a clean note is not an artifact — an unclaimed crossing files nothing"
            assert not ledger.exists(), "an unclaimed gated-and-clean crossing enqueues nothing"
        finally:
            (transitions._TICKETS, _insp._CHART_BERTHS,
             _verdict.LEDGER_PATH, _verdict.BERTHS_ROOT) = saved


def test_the_enqueue_seam_stays_file_only_on_the_fire_path():
    """The netns constraint as structure (build_inspector edge (l)): the enqueue's
    only door is cairn.chart.verdict — itself tree-free by its own allowlist tooth —
    and the chokepoint's source names no tree, db, embed, or inference machinery at
    all. If a future edit reaches a host from here, sealed crossings stop enqueueing
    identically to live ones and THIS tooth is what says so."""
    src = Path(transitions.__file__).read_text(encoding="utf-8")
    for host_door in ("cairn.chart.tree", "cairn.librarian", "cairn.db_domain",
                      "cairn.inference_domain", "embed_via_domain"):
        assert host_door not in src, (
            f"transitions.py reaches {host_door} — the crossing side of the deposit "
            "writes a FILE and nothing else; a host on the fire path breaks netns "
            "sealing, which is the whole reason the deposit is split in two")
    assert "from cairn.chart.verdict import enqueue_verdict" in src, \
        "the enqueue's one door is chart's tree-free ledger module, lazily imported"


def test_the_four_gate_exceptions_are_siblings_not_a_hierarchy():
    """The four gate exceptions (``EntryGateRed``, ``BuildGateRed``, ``ExitGateRed``,
    and the new ``TicketRequiredRed``) each subclass ``IllegalTransition`` directly —
    none subclasses another. A handler written for one gate must not silently catch
    another (the discipline the docstrings claim, pinned as an isolation invariant)."""
    siblings = [transitions.EntryGateRed, transitions.BuildGateRed,
                transitions.ExitGateRed, transitions.TicketRequiredRed]
    for s in siblings:
        assert issubclass(s, transitions.IllegalTransition), f"{s} must share the parent"
    for a in siblings:
        for b in siblings:
            if a is not b:
                assert not issubclass(a, b), f"{a} must not subclass sibling {b}"


def _main() -> int:
    checks = [
        test_a_legal_forward_advance_journals_the_crossing,
        test_the_crossing_carries_where_the_boat_now_stands,
        test_a_caller_may_say_it_richer_but_may_not_drop_it,
        test_the_leaf_fork_thinkme_may_go_to_ticketme_or_buildme,
        test_a_forward_skip_past_a_gate_summons_is_refused,
        test_a_target_outside_the_vocabulary_is_refused,
        test_a_no_op_self_transition_is_refused,
        test_an_unknown_class_or_version_is_refused,
        test_a_drifted_path_that_claims_v1_is_refused,
        test_a_skill_v1_workflow_validates_and_journals_a_crossing_at_a_fixture_skill_address,
        test_a_drifted_skill_path_that_claims_v1_is_refused,
        test_an_unknown_class_still_refuses_after_skill_registration,
        test_a_back_edge_kickback_is_legal_and_carries_severity,
        test_it_parses_a_real_live_ticket_workflow_string,
        test_prose_after_the_last_state_cannot_feed_phantom_states_onto_the_path,
        test_the_build_gate_refuses_a_proveme_exit_while_the_inspector_reds,
        test_a_clean_component_crosses_and_the_journal_carries_the_gate_verdict,
        test_a_kickback_out_of_proveme_is_never_gated,
        test_jurisdiction_an_unaddressed_proveme_exit_is_a_string_calculation_only,
        test_an_address_the_census_cannot_see_is_refused_not_waved_through,
        test_the_entry_gate_refuses_a_chartless_buildme_for_a_cast_ticket,
        test_a_charted_buildme_crosses_and_the_journal_carries_the_entry_verdict,
        test_the_entry_gate_requires_a_named_cast_ticket_backedges_stay_ungated,
        test_the_entry_gate_exempt_roster_entry_passes_gated_and_clean,
        test_the_entry_gate_refuses_a_chartless_skill_buildme_for_a_cast_ticket,
        test_a_charted_skill_buildme_crosses_and_the_journal_carries_the_entry_verdict,
        test_the_exit_gate_refuses_an_unanswered_proved_and_the_record_stands_still,
        test_an_answered_proved_crosses_and_the_journal_carries_the_exit_verdict,
        test_the_exit_gate_requires_a_named_cast_ticket_unclaimed_stays_gated_clean,
        test_the_exit_gate_exempt_roster_entry_passes_gated_and_clean,
        test_a_clean_answered_proved_crossing_enqueues_its_verdict_berth,
        test_a_refusal_an_unclaimed_crossing_and_a_back_edge_enqueue_nothing,
        test_the_enqueue_seam_stays_file_only_on_the_fire_path,
        test_the_four_gate_exceptions_are_siblings_not_a_hierarchy,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the emit-chokepoint refuses illegal transitions (skip-past-gate, off-vocabulary, "
          "unknown class/version, no-op, drifted path), journals legal crossings append-only, "
          "version-validates against the real node-class table, carries kick-back severity, and "
          "holds the BUILD GATE at the PROVEME exit (red component → refused, nothing written; "
          "kick-backs never gated; no side door for an uninspectable address), and holds the "
          "ENTRY GATE at the BUILDME entry (a cast ticket with no berthed chart chain → refused, "
          "nothing written), and holds the EXIT GATE at the PROVED entry (a claimed ticket with "
          "an unanswered chart → refused, record byte-identical; a FAILED criterion refuses by "
          "name; unclaimed gated-and-clean on the record) — and now THE JURISDICTION TIGHTENS "
          "(ticket a-voyage-names-its-ticket) at BOTH doors: a forward BUILDME/PROVED crossing "
          "naming no ticket, or a named-but-uncast one, refuses before anything is written "
          "(TicketRequiredRed, distinct wording, sibling to the three gates above, never each "
          "other); the explicit _EXEMPT_ROSTER (empty in v0) passes gated-and-clean, never "
          "silently — and THE DEPOSIT RIDES THE CROSSING (ticket "
          "the-deposit-rides-the-read): an exit-gate-clean answered PROVED entry "
          "appends exactly one enqueued record naming the artifact that answered and "
          "journals the berth it filed, while a refusal, an unclaimed gated-and-clean "
          "crossing (the enqueue keys on the ARTIFACT, never the clean note) and a "
          "back-edge each enqueue nothing; the seam stays file-only, so a sealed "
          "crossing enqueues identically to a live one — the state vocabulary is "
          "physics (Law 4), not /sorted's prose. AND NOW A SECOND CLASS RIDES THE SAME "
          "DOOR (ticket skills-ride-the-chokepoint): class skill@v1 registered in "
          "node_classes/skill.json alone (ZERO changes to this module) — a skill "
          "crossing validates, journals, and drifts identically to a code-seam one, "
          "an unknown class still refuses after the registration, and the entry gate "
          "fires identically on a skill-class voyage naming a cast ticket (chartless "
          "refuses, charted crosses gated-and-clean) — the registry is the door, proven "
          "on a second tenant")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

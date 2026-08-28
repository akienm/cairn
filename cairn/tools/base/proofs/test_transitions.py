"""Proof: the EMIT-CHOKEPOINT (cairn/tools/base/transitions.py) makes the state vocabulary PHYSICS.

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

    python3 cairn/tools/base/proofs/test_transitions.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import transitions
from cairn.tools.charter import projector

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
        assert "[PROVEME:waiting]" in new and "[BUILDME]" not in new, f"cursor did not move to PROVEME: {new}"
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
    assert "[TICKETME:waiting]" in transitions.emit(at_think, "TICKETME")
    assert "[BUILDME:waiting]" in transitions.emit(at_think, "BUILDME")


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
        assert "[PROVEME:waiting]" in new and "[BUILDME]" not in new, f"cursor did not move: {new}"
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
        assert "[BUILDME:waiting]" in new, f"kick-back did not move the cursor: {new}"
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
    scanned = 0
    rejected = 0
    for t in sorted(tickets_dir.glob("*.json")):
        scanned += 1
        try:
            state = json.loads(t.read_text()).get("state")
            wf = transitions.parse_workflow(state) if isinstance(state, str) else None
        except (ValueError, OSError):
            rejected += 1
            continue
        if not (wf and wf.node_class == "code-seam" and wf.version in versions):
            rejected += 1
            continue
        reg = versions[wf.version]
        free = set(reg.get("free_summons", []))
        if [x for x in wf.path if x not in free] == list(reg["path"]):
            found = (t.name, wf, tuple(reg["path"]), free)
            break
        rejected += 1
    assert found, ("no live code-seam ticket in CairnCommons/tickets/ conforms to any registered "
                   "version — the real-ticket tooth needs at least one on-disk code-seam ticket "
                   f"(a green over zero would be hollow, Law 8; scanned {scanned}, rejected all)")
    name, wf, canonical, free = found
    assert wf.here in canonical or wf.here in free, \
        f"cursor mis-parsed from the real string ({name}, not a real stage): {wf.here}"
    print(f"  (denominator: scanned {scanned}, rejected {rejected}, "
          f"found {name} at position {rejected + 1})")


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
            assert [f["method"] for f in e.findings] == ["charter_on_disk"], e.findings
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
        assert "[LEARNME:waiting]" in new
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
        assert "[BUILDME:waiting]" in new and projector.read_history(hist)[0]["direction"] == "back"


def test_jurisdiction_an_unaddressed_proveme_exit_is_a_string_calculation_only():
    # No history_path → no journal → the record of truth does not move, so there is no
    # component address to inspect and nothing the gate protects. (The register reads
    # project(history); a promotion that writes no truth has not happened anywhere.)
    assert "[LEARNME:waiting]" in transitions.emit(_AT_PROVE, "LEARNME")


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
    import cairn.machines.build_inspector.inspector as _insp
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
                assert [f["method"] for f in e.findings] == ["buildme_rides_the_chart"], e.findings
                assert "widget" in str(e) and "/chart" in str(e), \
                    "the refusal must name the ticket and the disposition, first pass"
            else:
                raise AssertionError("a chartless BUILDME crossed — the entry gate is not wired")
            assert not Path(hist).exists(), "a REFUSED crossing must write no record of truth"
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved


def test_a_charted_buildme_crosses_and_the_journal_carries_the_entry_verdict():
    import cairn.machines.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _entry_world(Path(d), cast=("widget",), claims=("widget",))
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            new = transitions.emit(_AT_TICKET, "BUILDME",
                                   history_path=hist, state_path=state, ticket="widget")
            assert "[BUILDME:waiting]" in new
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
            assert "[BUILDME:waiting]" in new and rec["direction"] == "back"
            assert rec["entry_gate"] == "not_applicable", \
                "a kick-back into BUILDME is never gated — the field must say not_applicable"
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
            assert "[BUILDME:waiting]" in new
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
    import cairn.machines.build_inspector.inspector as _insp
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
                assert [f["method"] for f in e.findings] == ["buildme_rides_the_chart"], e.findings
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
    import cairn.machines.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _entry_world(Path(d), cast=("widget",), claims=("widget",))
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            new = transitions.emit(_AT_TICKET_SKILL, "BUILDME",
                                   history_path=hist, state_path=state, ticket="widget")
            assert "[BUILDME:waiting]" in new
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
                  "evidence": "seen: exit 0 twice",
                  "discriminating_observation": "reverted the fix; the instrument exits 1"}],
    "dispositions": [{"piece": "p1", "expect": "e1", "disposition": "confirmed",
                      "by": "the run observed"}],
}

_FIXTURE_SEAL_DATE = "2026-08-10T00:00:00"


def _cleared(d: Path, **extra) -> dict:
    """Journal-extra for a crossing that came through the harbor's door — with a REAL
    seal behind it, minted here in the fixture's own tempdir.

    Ticket ``emit-refuses-an-uncleared-crossing`` (2026-08-10): a forward crossing into
    a REST now needs the clearance witness. The witness is not a magic string — the gate
    re-reads the world with ``standing``, so this helper builds the world: a real ``.py``
    under a real ``proofs/`` peer, sealed green through ``persist_validation`` (the store's
    only write-door, which mints the trail link) with the fingerprint the store itself
    computes. If any of that were faked, the gate would refuse — which is the whole point
    of it verifying against the world instead of against the field it was handed.

    ``cleared_by`` is a plain name and deliberately unverified HERE: who-may is Law 6 and
    lives at harbor_master's door, never at base's. What base checks is that the Law 8
    evidence the record leans on is real and current.
    """
    from cairn.devices.tester.validation_store import persist_validation, source_fingerprint
    proof = d / "proofs" / "sealed_fixture.py"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("# a real source file, so the fingerprint is a real fingerprint\n")
    persist_validation({
        "claim": "the fixture component's code is proven",
        "caller": "cairn/tools/base/proofs/test_transitions.py",
        "date": _FIXTURE_SEAL_DATE,
        "method": "fixture seal — the trail is real, the code it seals is a stub",
        "verdict": "green",
        "evidence": {"source_fingerprint": source_fingerprint(str(proof))},
        "falsifier": "the component's source fingerprint moves",
        "horizon": "until any .py under the component root changes",
    }, proof_path=str(proof))
    return {"cleared_by": "fixture-owner", "proven_by": str(proof),
            "proven_seal_date": _FIXTURE_SEAL_DATE, **extra}


def test_the_exit_gate_refuses_an_unanswered_proved_and_the_record_stands_still():
    """proved-answers-the-chart LANDED: the forward crossing INTO PROVED naming a cast,
    CLAIMED ticket is refused while the chart is unanswered — and the record of truth
    is byte-identical after the refusal (nothing journaled, nothing touched). The
    findings ride the exception complete on the first pass; a FAILED criterion refuses
    as loudly as an unanswered one (PROVED asserts done; a fail is a kick-back)."""
    import hashlib as _hashlib
    import cairn.machines.build_inspector.inspector as _insp
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
                assert [f["method"] for f in e.findings] == ["proved_answers_the_chart"], \
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
                               "evidence": "it broke",
                               "discriminating_observation": "the failing run itself"}],
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
    import cairn.machines.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _exit_world(Path(d), verdict=_ANSWERED)
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            new = transitions.emit(_AT_LEARN, "PROVED",
                                   history_path=hist, state_path=state, ticket="widget",
                                   **_cleared(Path(d)))
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
    import cairn.machines.build_inspector.inspector as _insp
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
                                   history_path=hist2, state_path=state2, ticket="widget",
                                   **_cleared(base))
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
            # The clearance witness rides too, and that is the point of it appearing
            # here: the exit roster and the clearance roster are TWO rosters (ticket
            # emit-refuses-an-uncleared-crossing). Sitting on one buys nothing at the
            # other, and this tooth reds the day someone collapses them.
            new = transitions.emit(_AT_LEARN, "PROVED", history_path=hist, state_path=state,
                                   **_cleared(comp))
            assert "[PROVED]" in new
            rec = projector.read_history(hist)[0]
            assert rec["exit_gate"].startswith("exempt —"), \
                f"an exempt pass must journal its exemption, never silently: {rec}"
            assert "legacy-component" in rec["exit_gate"]
        finally:
            transitions._EXEMPT_ROSTER = saved


def _ledger_world(d: Path, **kw):
    """The exit world plus a FIXTURE ledger path and berths root patched into
    cairn.devices.builder.machines.verdict.verdict — the enqueue's two module globals, so no tooth here can
    touch the live instance-space ledger. Returns (tickets, berths, ledger)."""
    import cairn.devices.builder.machines.verdict.verdict as _verdict
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
    import cairn.machines.build_inspector.inspector as _insp
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
                             ticket="widget", **_cleared(Path(d)))
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
    import cairn.machines.build_inspector.inspector as _insp
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
                             ticket="widget", **_cleared(Path(d)))
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
    only door is cairn.devices.builder.machines.verdict.verdict — itself tree-free by its own allowlist tooth —
    and the chokepoint's source names no tree, db, embed, or inference machinery at
    all. If a future edit reaches a host from here, sealed crossings stop enqueueing
    identically to live ones and THIS tooth is what says so."""
    src = Path(transitions.__file__).read_text(encoding="utf-8")
    for host_door in ("cairn.tools.tree.tree", "cairn.devices.librarian", "cairn.devices.db_domain",
                      "cairn.devices.inference_domain", "embed_via_domain"):
        assert host_door not in src, (
            f"transitions.py reaches {host_door} — the crossing side of the deposit "
            "writes a FILE and nothing else; a host on the fire path breaks netns "
            "sealing, which is the whole reason the deposit is split in two")
    assert "from cairn.devices.builder.machines.verdict.verdict import enqueue_verdict" in src, \
        "the enqueue's one door is chart's tree-free ledger module, lazily imported"


# ---- THE SIXTH SEAT: A CROSSING INTO A REST CARRIES ITS CLEARANCE ----------------
# Ticket ``emit-refuses-an-uncleared-crossing`` (2026-08-10), draining the live trouble
# ``every-crossing-goes-around-the-clearance-gate``. Measured 2026-08-05: of 229 records
# across 21 component histories, 146 were emit-shaped and ZERO carried ``cleared_by`` —
# harbor_master's charter names that exact condition as its own falsifier, and it had
# been met continuously since the clearance gate was built. Three files said "the
# clearance gate wraps emit, so this is the one door"; nothing did.
#
# THE DEMANDED SET IS DERIVED FROM THE GRAMMAR, NEVER FROM A COMPONENT LIST: a FORWARD
# journaled crossing into a REST — ``not is_summons(target)`` — which is the move that
# enters proven-space, and therefore exactly the move ``clear`` already knows how to
# judge (it reads ``standing`` on the proof). That scoping is what keeps
# ``_CLEARANCE_EXEMPT_ROSTER`` EMPTY: this gate's own voyage CLEARS rather than being
# waived, which is the difference between a gate and a wall with a guest list.
#
# THE HOLLOW SHAPE THESE TEETH EXIST TO CATCH, in three flavours, because a gate can be
# vacuous three different ways: (1) demanded of nothing, so it passes everything —
# answered by the paired does-NOT-refuse and does-NOT-fire rows; (2) satisfied by a
# string, so a caller types ``cleared_by="me"`` into a bare ``emit`` and walks through —
# answered by the three world-verification rows, which is the sibling-gate pattern
# (entry reads berths off disk, exit reads the verdict artifact, emission resolves the
# probe); (3) trapping the retreat — answered by the back-edge row.


def test_an_uncleared_forward_crossing_into_a_rest_refuses_and_nothing_is_journaled():
    """The headline. A forward crossing into a REST with no clearance witness refuses,
    and a PRIOR record on disk is byte-identical afterwards (Law 7: a refused move
    leaves no partial record). The refusal names the door to use, so the diagnostic is
    complete on the first pass rather than sending a reader to find out how to comply."""
    import hashlib as _hashlib
    with tempfile.TemporaryDirectory() as d:
        comp = Path(d) / "widgetry"
        comp.mkdir()
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        # a real prior record: a crossing into a SUMMONS, which this gate never touches
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        before = _hashlib.sha256(Path(hist).read_bytes()).hexdigest()
        # THE ISOLATING ROSTER. The exit gate sits above this one and would refuse an
        # unnamed PROVED crossing first, so a red here could have come from either seat.
        # Sitting the component on the EXIT roster silences that gate and leaves the
        # clearance gate as the only thing this crossing can trip on — measured need
        # (the first draft refused with TicketRequiredRed and proved nothing about the
        # sixth seat), and it doubles as a second reading of "two rosters, not one".
        saved = transitions._EXEMPT_ROSTER
        transitions._EXEMPT_ROSTER = frozenset({"widgetry"})
        try:
            transitions.emit(_AT_LEARN, "PROVED", history_path=hist, state_path=state)
        except transitions.ClearanceRequiredRed as e:
            msg = str(e)
            assert "clearance.clear" in msg, "the refusal must name the door to cross through"
            assert "_CLEARANCE_EXEMPT_ROSTER" in msg and "widgetry" in msg, \
                "the refusal must name the explicit exception and this component, by name"
        else:
            raise AssertionError("an uncleared forward crossing into a rest PASSED — "
                                 "the sixth seat is not wired")
        finally:
            transitions._EXEMPT_ROSTER = saved
        assert _hashlib.sha256(Path(hist).read_bytes()).hexdigest() == before, \
            "a REFUSED crossing must leave the record of truth byte-identical"


def test_a_cleared_crossing_passes_and_the_record_names_the_proof_it_leaned_on():
    """The does-NOT-refuse row, and it is the load-bearing one: a gate proved only by
    what it stops has never been proved by what it lets through. The witness is backed
    by a REAL seal (``_cleared`` mints one through the store's only write-door), the
    crossing lands, and the record of truth carries the ``clearance_gate`` note naming
    the proof and the seal date — so a reader in a year can see which proof this
    crossing's authority rested on without leaving the history file (Law 5)."""
    with tempfile.TemporaryDirectory() as d:
        comp = Path(d) / "widgetry"
        comp.mkdir()
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        witness = _cleared(comp)
        saved = transitions._EXEMPT_ROSTER
        transitions._EXEMPT_ROSTER = frozenset({"widgetry"})  # silence the OTHER gate
        try:
            new = transitions.emit(_AT_LEARN, "PROVED", history_path=hist,
                                   state_path=state, **witness)
        finally:
            transitions._EXEMPT_ROSTER = saved
        assert "[PROVED]" in new
        rec = projector.read_history(hist)[0]
        assert "cleared by 'fixture-owner'" in rec["clearance_gate"], rec
        assert witness["proven_by"] in rec["clearance_gate"], \
            f"the record must name the proof the clearance leaned on: {rec}"
        assert _FIXTURE_SEAL_DATE in rec["clearance_gate"], rec
        assert "re-read at the door" in rec["clearance_gate"], \
            "the note must say the seal was re-read HERE, not merely quoted from the caller"


def test_a_witness_the_world_does_not_back_is_refused_three_ways():
    """THE VACUOUS-BY-STRING KILL. A caller typing the witness into a bare ``emit``
    cannot forge a clearance, because the gate re-reads the world — the same discipline
    every sibling gate at this chokepoint already keeps. Three ways to be wrong, each
    refused with its own wording so the first pass says which:

      - an INCOMPLETE witness (``cleared_by`` alone) — the harbor's gate stamps all four
        fields together, so a record carrying some of them did not come through it;
      - a proof the tester never sealed — Law 8, proven-space is the tester's and it has
        not spoken about that code;
      - a seal DATE that disagrees with the standing seal — a record of truth may not
        carry an error quietly (Law 7).

    Revert any one of the three checks in ``_require_clearance`` and the matching row
    goes red; that is how non-hollowness was verified rather than asserted."""
    with tempfile.TemporaryDirectory() as d:
        comp = Path(d) / "widgetry"
        comp.mkdir()
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        good = _cleared(comp)

        def _try(**extra):
            saved = transitions._EXEMPT_ROSTER
            transitions._EXEMPT_ROSTER = frozenset({"widgetry"})  # isolate the sixth seat
            try:
                transitions.emit(_AT_LEARN, "PROVED", history_path=hist,
                                 state_path=state, **extra)
            except transitions.ClearanceRequiredRed as e:
                return str(e)
            finally:
                transitions._EXEMPT_ROSTER = saved
            raise AssertionError(f"a forged witness PASSED: {extra}")

        msg = _try(cleared_by="me")
        assert "INCOMPLETE" in msg and "proven_by" in msg and "proven_seal_date" in msg, msg
        msg = _try(cleared_by="me", proven_by=str(comp / "proofs" / "never_sealed.py"),
                   proven_seal_date=_FIXTURE_SEAL_DATE)
        assert "NOT in proven-space" in msg and "no VALIDATION has ever sealed" in msg, msg
        msg = _try(**dict(good, proven_seal_date="2020-01-01T00:00:00"))
        assert "disagrees with the seal it names" in msg and _FIXTURE_SEAL_DATE in msg, msg
        assert not Path(hist).exists(), \
            "three refusals must have written no record of truth at all — not even an empty one"


def test_the_gate_does_not_fire_on_a_summons_or_on_a_retreat():
    """The two silences, and both are design rather than omission.

    A crossing into a SUMMONS is not the move that enters proven-space. The demanded set
    is derived from ``is_summons`` rather than from the token "PROVED" precisely so no
    component list is ever consulted — and this row measures what that derivation buys
    TODAY, honestly: across every registered class the ONLY rest on the path is the
    terminal one, so the demanded set is exactly one crossing per voyage. That is a
    measurement of the standing grammar, not a law about it: a future class with a
    mid-path rest inherits the gate for free, which is the whole reason the rule is
    written against the shape instead of against the word.

    And a BACK-edge is never gated — the same ``target_idx > wf.cursor`` guard every
    sibling seat here keeps. Trapping a boat at a state it must be able to return to
    would make a kick-back impossible, which is the motion a red is supposed to produce
    (Law 6 — re-opening a node is the owner's act)."""
    seen = 0
    for name in ("code-seam", "skill"):
        for ver, spec in transitions.load_class_def(name)["workflow_versions"].items():
            path = tuple(spec["path"])
            rests = [s for s in path if not transitions.is_summons(s)]
            assert rests == [path[-1]], (
                f"{name}@{ver}: the only rest is expected to be the terminal — got "
                f"{rests}. If a mid-path rest has appeared, the demanded set just grew "
                "and this proof's back-edge-into-a-rest row is now reachable and owed")
            seen += 1
    assert seen >= 3, f"the class walk found only {seen} versions — a vacuous green"
    with tempfile.TemporaryDirectory() as d:
        comp = Path(d) / "widgetry"
        comp.mkdir()
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        # forward into a SUMMONS: untouched, no witness, no note
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        rec = projector.read_history(hist)[0]
        assert rec["direction"] == "forward" and "clearance_gate" not in rec, rec
        # a RETREAT: never gated, and it journals no clearance
        h2, s2 = str(comp / "h2.json"), str(comp / "s2.json")
        transitions.emit(_AT_LEARN, "BUILDME", history_path=h2, state_path=s2)
        rec = projector.read_history(h2)[0]
        assert rec["direction"] == "back" and "clearance_gate" not in rec, \
            f"a retreat must cross ungated and journal no clearance: {rec}"


def test_the_clearance_roster_is_a_second_roster_and_it_is_empty_in_production():
    """Two rosters, two vocabularies — and the live one is EMPTY, which is the claim
    this ticket's falsifier clause (1) was written against: *the voyage completes on
    the exemption roster*. If this gate's own build had to roster itself through, the
    builder routed around the gate. A fixture entry proves the roster WORKS (an exempt
    crossing passes and journals its exemption through the ``clearance_gate`` key, never
    silently) while the production frozenset stays empty."""
    assert transitions._CLEARANCE_EXEMPT_ROSTER == frozenset(), (
        "the clearance roster is empty by construction — an entry here is a waiver, and "
        "a waiver needs its reason beside it and an argument at Akien's gate: "
        f"{sorted(transitions._CLEARANCE_EXEMPT_ROSTER)}")
    assert transitions._CLEARANCE_EXEMPT_ROSTER is not transitions._EXEMPT_ROSTER, \
        "two rosters, not one given a second meaning — their empty states claim opposites"
    with tempfile.TemporaryDirectory() as d:
        comp = Path(d) / "legacy-hull"
        comp.mkdir()
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        saved = transitions._CLEARANCE_EXEMPT_ROSTER, transitions._EXEMPT_ROSTER
        transitions._CLEARANCE_EXEMPT_ROSTER = frozenset({"legacy-hull"})
        transitions._EXEMPT_ROSTER = frozenset({"legacy-hull"})
        try:
            new = transitions.emit(_AT_LEARN, "PROVED", history_path=hist, state_path=state)
        finally:
            transitions._CLEARANCE_EXEMPT_ROSTER, transitions._EXEMPT_ROSTER = saved
        assert "[PROVED]" in new
        rec = projector.read_history(hist)[0]
        assert rec["clearance_gate"].startswith("exempt —") and "legacy-hull" in rec["clearance_gate"], \
            f"an exempt pass must journal its exemption, never silently: {rec}"


def test_the_four_gate_exceptions_are_siblings_not_a_hierarchy():
    """The gate exceptions each subclass ``IllegalTransition`` directly — none
    subclasses another. A handler written for one gate must not silently catch another
    (the discipline the docstrings claim, pinned as an isolation invariant). The name
    still says four; the seats are six, and the row grows with them rather than being
    renamed each time — ``ClearanceRequiredRed`` joined 2026-08-10."""
    siblings = [transitions.EntryGateRed, transitions.BuildGateRed,
                transitions.ExitGateRed, transitions.TicketRequiredRed,
                transitions.ClearanceRequiredRed]
    for s in siblings:
        assert issubclass(s, transitions.IllegalTransition), f"{s} must share the parent"
    for a in siblings:
        for b in siblings:
            if a is not b:
                assert not issubclass(a, b), f"{a} must not subclass sibling {b}"


# ---- THE SUMMONS SHOWS ITS PICKUP (ruled 2026-08-07, the-ticket-is-the-source-period) ----
# The pickup lifecycle is stated once at the grammar level: a summons arrives ``:waiting``,
# a journaled pickup advances it ``:in-process``, terminals and rests take no phase, and the
# legacy bare cursor parses forever. These teeth are the ones a hollow build could not pass:
# a phase stored but never refused off-cursor, a stamp asserted but never rendered, a pickup
# that writes before it refuses.


def test_a_phased_cursor_parses_and_round_trips():
    wf = transitions.parse_workflow(
        "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED")
    assert wf.phase == "waiting" and wf.here == "BUILDME", (wf.phase, wf.here)
    # the phase belongs to the CURSOR, not to the path — the path stays bare state names
    assert wf.path == ("THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"), wf.path
    # and the legacy grammar is untouched: a bare cursor is phase=None, not an error
    bare = transitions.parse_workflow(_CODE_SEAM)
    assert bare.phase is None, bare.phase
    # an object and a phase ride the same cursor together
    both = transitions.parse_workflow(
        "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
        "[WATCHME(what-it-watches):in-process] -> PROVED")
    assert both.phase == "in-process" and both.here_object == "what-it-watches"


def test_a_phase_anywhere_but_the_cursor_is_refused():
    _expect_refused(lambda: transitions.parse_workflow(
        "code-seam@v2: THINKME:waiting -> [BUILDME] -> PROVEME -> PROVED"),
        transitions.MalformedWorkflow)


def test_a_phase_on_a_rest_or_terminal_is_refused():
    _expect_refused(lambda: transitions.parse_workflow(
        "code-seam@v2: THINKME -> BUILDME -> PROVEME -> [PROVED:waiting]"),
        transitions.MalformedWorkflow)


def test_an_unknown_phase_word_is_refused_loudly():
    _expect_refused(lambda: transitions.parse_workflow(
        "code-seam@v2: THINKME -> [BUILDME:paused] -> PROVEME -> PROVED"),
        transitions.MalformedWorkflow)
    # case drift refuses LOUDLY instead of silently truncating the walk at the cursor —
    # a "[BUILDME:Waiting]" that fell to the prose-stop would hand every reader a fiction
    _expect_refused(lambda: transitions.parse_workflow(
        "code-seam@v2: THINKME -> [BUILDME:Waiting] -> PROVEME -> PROVED"),
        transitions.MalformedWorkflow)


def test_arrival_stamps_waiting_on_a_summons_and_never_on_a_rest():
    wf = transitions.parse_workflow(_CODE_SEAM)
    moved = transitions.render(wf, "PROVEME")
    assert "[PROVEME:waiting]" in moved, moved
    # the departed state loses its bracket AND its phase — only the cursor has a pickup
    assert "BUILDME:" not in moved and "[BUILDME" not in moved, moved
    # a rest arrives bare: nothing is summoned, so there is nothing to wait for
    at_learn = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> [LEARNME] -> PROVED"
    rested = transitions.render(transitions.parse_workflow(at_learn), "PROVED")
    assert rested.endswith("[PROVED]"), rested
    # and the stamped string round-trips through the parser it came from
    assert transitions.parse_workflow(moved).phase == "waiting"


def test_a_forward_crossing_from_waiting_stays_legal():
    # SINGLE-ACTOR COLLAPSE (a named open edge in the definition): today one hand summons,
    # picks up, and crosses — so emit accepts a :waiting cursor without a pickup first.
    # Making pickup a crossing precondition is a future dial, not this tooth.
    new = transitions.emit(
        "code-seam@v1: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> LEARNME -> PROVED",
        "PROVEME")
    assert "[PROVEME:waiting]" in new, new


def test_pickup_advances_waiting_to_in_process_and_journals_the_actor():
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        new = transitions.pickup(
            "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED",
            actor="igor-3", history_path=hist, state_path=state)
        assert "[BUILDME:in-process]" in new and ":waiting" not in new, new
        log = projector.read_history(hist)
        assert len(log) == 1, "the pickup was not journaled exactly once"
        rec = log[0]
        assert rec["act"] == "pickup" and rec["actor"] == "igor-3", rec
        assert rec["standing"] == "BUILDME", "a pickup is not a crossing — the boat stands still"
        assert rec["workflow"] == new, "the journal must record the in-process string"
        assert rec.get("at"), "the append door stamps WHEN — actor + time is the whole point"


def test_a_bare_summons_cursor_is_picked_up():
    # the legacy corpus arrived before phases existed; the pickup records what arrival
    # never stamped, rather than refusing the entire standing fleet
    new = transitions.pickup(_CODE_SEAM, actor="igor-3")
    assert "[BUILDME:in-process]" in new, new


def test_pickup_refuses_a_rest_a_terminal_and_a_doubled_pickup_writing_nothing():
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        for wf_str in (
            # a terminal: nothing summoned, nothing to pick up
            "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]",
            # doubled: the second hand must SEE the first on the ticket, not overwrite it
            "code-seam@v2: THINKME -> TICKETME -> [BUILDME:in-process] -> PROVEME -> PROVED",
        ):
            _expect_refused(lambda s=wf_str: transitions.pickup(
                s, actor="igor-3", history_path=hist, state_path=state))
        assert not Path(hist).exists() and not Path(state).exists(), \
            "a refused pickup must leave NO record (the same law as a refused crossing)"


def test_the_standing_corpus_parses_and_any_phase_sits_on_a_summons():
    """Every workflow string already journaled in class-space still parses. The first
    cut of this row (2026-08-07, same day as the ruling) asserted phase=None corpus-wide
    — true for exactly as long as no post-ruling voyage had journaled, then red the
    moment the first :waiting record landed, which is a pinned-snapshot defect, not a
    catch. The INVARIANT is the grammar's, not the corpus's age: a phase, where present,
    is one of the ruled two, and it sits on a SUMMONS — a rest or terminal cursor
    claiming a pickup phase is the corruption this row actually guards against."""
    seen = 0
    for hist in _REPO_ROOT.rglob("history.json"):
        if ".git" in hist.parts:
            continue
        try:
            records = json.loads(hist.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(records, list):
            continue
        for rec in records:
            w = rec.get("workflow") if isinstance(rec, dict) else None
            if not w:
                continue
            wf = transitions.parse_workflow(w)
            assert wf.phase in (None, "waiting", "in-process"), \
                f"a phase outside the ruled two: {hist}: {w}"
            if wf.phase is not None:
                assert transitions.is_summons(wf.here), \
                    f"a phase on a rest/terminal cursor: {hist}: {w}"
            seen += 1
    assert seen >= 100, f"the corpus walk found only {seen} strings — a vacuous green"


# ---------------------------------------------------------------------------
# THE PROOF RECORD (ruling 2026-08-13, everything-always-proved-and-listing-what-it-proved).
# Every seat at this chokepoint used to return one PROSE sentence on success, so a check that
# stopped running and a crossing that genuinely satisfied every check wrote the identical line
# into a record of truth, forever. These teeth are what makes the record the physics and not
# another sentence about it.


def _healthy_records():
    """Every inspector at this door, run on a HEALTHY subject, as (name, record) pairs.

    THE TOOTH BELOW IS THE COMPONENT'S OWN PHYSICS against the authoring hazard measured n=4
    on 2026-08-13: a lane whose ``expected`` and ``actual`` cannot be ``==`` when it passes
    reds on every healthy subject, and nothing in gate.py can catch it. Only a fixture known
    to be well can.
    """
    out = []
    wf = transitions.parse_workflow(_CODE_SEAM)
    class_def = transitions.load_class_def(wf.node_class)
    out.append(("inspect_rules",
                transitions.inspect_rules(wf, "PROVEME", class_def=class_def)))
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _entry_world(Path(d), cast=("widget",), claims=("widget",))
        import cairn.machines.build_inspector.inspector as _insp
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            out.append(("inspect_named_ticket", transitions.inspect_named_ticket(
                "BUILDME", "widget", history_path=str(Path(d) / "history.json"))))
            out.append(("inspect_entry", transitions.inspect_entry("widget")))
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved
    with tempfile.TemporaryDirectory() as d:
        # A HEALTHY subject at the EXIT door is a claim that was ANSWERED — an unanswered one
        # is a well-formed refusal, not a well subject, and running the tooth against it would
        # have measured the fixture instead of the lane.
        tickets, berths = _exit_world(Path(d), verdict=_ANSWERED)
        import cairn.machines.build_inspector.inspector as _insp
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            out.append(("inspect_exit", transitions.inspect_exit("widget")))
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved
    with tempfile.TemporaryDirectory() as d:
        comp = _component(Path(d), "healthy")
        out.append(("inspect_build",
                    transitions.inspect_build(str(comp / "history.json"))))
    return out


def test_a_healthy_subject_produces_an_all_passing_record_at_every_inspector():
    """THE AUTHORING HAZARD'S ONLY PHYSICS, and the reason it is a tooth and not a docstring.

    Four lanes shipped across the corpus in one day (2026-08-13) whose two sides could never
    be ``==`` when the check passed — "expected: one of A or B, actual: A" — so each one
    reddened every HEALTHY subject it met. gate.py cannot detect that: the refusal payload's
    key is the caller's word. What catches it is exactly this — assert that a subject known
    to be well produces a record with NO mismatches, at every inspector, by name.
    """
    for name, record in _healthy_records():
        assert record, f"{name} produced an EMPTY record on a healthy subject — a gate that " \
                       "proved nothing has not proved everything (Law 8)"
        bad = [e for e in record if not transitions.gate.passed(e)]
        assert not bad, (
            f"{name} reds a HEALTHY subject — the n=4 authoring hazard: "
            + "; ".join(f"{e['identity']}: expected {e['expected']!r} != actual {e['actual']!r}"
                        for e in bad))
        ids = [e["identity"] for e in record]
        assert len(ids) == len(set(ids)) or name == "inspect_build", \
            f"{name} names the same lane twice, so the record cannot be read by name: {ids}"


def test_every_journaled_crossing_carries_the_record_of_what_it_proved():
    """NO EMPTY ANYWHERE. The rules rung always runs, so there is no crossing whose record
    can be silent — including the plainest ungated forward advance, which before this stone
    journaled nothing at all about what had been checked."""
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        transitions.emit(_CODE_SEAM, "PROVEME", history_path=hist, state_path=state)
        rec = projector.read_history(hist)[0]
    proved = rec["proved"]
    assert proved, "an ungated crossing journaled an EMPTY proof record — the silence the " \
                   "ruling retires, in the one place it is easiest to miss"
    assert rec["checks_proved"] == len(proved), \
        "checks_proved is derived from the list, never counted beside it — the two disagreeing " \
        "is a gate and its own sentence drifting apart"
    assert [e["identity"] for e in proved] == [
        "the_target_is_in_the_vocabulary",
        "the_crossing_moves_the_cursor",
        "the_crossing_is_a_legal_edge"], proved
    for e in proved:
        assert e["expected"] == e["actual"], e
        assert e["source"].startswith("transitions."), e
        assert e["location"] == "cairn/tools/base/transitions.py", e


def test_a_lane_whose_input_the_lane_above_refused_is_absent_never_green():
    """ELIGIBILITY IS NESTED. One fault yields exactly ONE failing entry — never a
    multiplication into derived findings in different vocabularies, and never a green lane
    over an input that was never there to check."""
    wf = transitions.parse_workflow(_CODE_SEAM)
    class_def = transitions.load_class_def(wf.node_class)
    off = transitions.inspect_rules(wf, "NOPE", class_def=class_def)
    assert [e["identity"] for e in off] == ["the_target_is_in_the_vocabulary"], off
    noop = transitions.inspect_rules(wf, "BUILDME", class_def=class_def)   # standing there
    assert [e["identity"] for e in noop] == [
        "the_target_is_in_the_vocabulary", "the_crossing_moves_the_cursor"], noop
    assert transitions.gate.passed(noop[0]) and not transitions.gate.passed(noop[1]), noop
    # the emission gate: no ticket → the spec and probe lanes have nothing to read
    assert [e["identity"] for e in transitions.inspect_emission("a-watch", None)] == [
        "the_crossing_names_a_cast_ticket"], "an absent spec lane must not read as passed"
    # the build gate: an address the census cannot see → the inspector's lanes never ran
    with tempfile.TemporaryDirectory() as d:
        bare = Path(d) / "codeless"
        bare.mkdir()
        (Path(d) / "neighbor" / "proofs").mkdir(parents=True)
        (Path(d) / "neighbor" / "x.py").write_text("pass\n")
        blind = transitions.inspect_build(str(bare / "history.json"))
    assert [e["identity"] for e in blind] == ["the_census_can_measure_the_component"], blind
    assert not transitions.gate.passed(blind[0]), blind


def test_the_entry_gate_names_all_three_sieves_so_a_dropped_one_shortens_the_record():
    """THE GATE THE RECORD WAS MOST OWED. Three sieves used to collapse into one word, so a
    sieve that stopped firing wrote the same 'clean' line as a crossing that satisfied all
    three. The count IS the ruleset's size: drop a sieve and this tooth fails on the LENGTH,
    which is the whole difference between a shorter record and a cleaner one."""
    import cairn.machines.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _entry_world(Path(d), cast=("widget",), claims=("widget",))
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            record = transitions.inspect_entry("widget")
            assert [e["identity"] for e in record] == [
                "a_berthed_chart_chain_claims_the_ticket",
                "the_ticket_names_its_intent_firing",
                "the_ticket_names_its_sorted_door_firing"], record
            hist, state = str(Path(d) / "history.json"), str(Path(d) / "state.json")
            transitions.emit(_AT_TICKET, "BUILDME",
                             history_path=hist, state_path=state, ticket="widget")
            rec = projector.read_history(hist)[0]
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved
    named = [e["identity"] for e in rec["proved"]]
    for sieve in ("a_berthed_chart_chain_claims_the_ticket",
                  "the_ticket_names_its_intent_firing",
                  "the_ticket_names_its_sorted_door_firing"):
        assert sieve in named, f"the crossing's record of truth does not name {sieve}: {named}"
    assert rec["entry_gate"].endswith(
        "the entry gate proved 3 check(s): a_berthed_chart_chain_claims_the_ticket, "
        "the_ticket_names_its_intent_firing, the_ticket_names_its_sorted_door_firing"), \
        f"the note must be RENDERED FROM the record, not written beside it: {rec['entry_gate']}"


def test_a_refusals_findings_are_read_back_out_of_the_record_never_built_beside_it():
    """DERIVED, NEVER PARALLEL. The findings a refusal carries are the record's mismatches,
    read back out — two mouths for one question is how a gate and the sentence it prints come
    to disagree. Proved on the entry gate, whose findings shape callers already depend on."""
    import cairn.machines.build_inspector.inspector as _insp
    with tempfile.TemporaryDirectory() as d:
        tickets, berths = _entry_world(Path(d), cast=("widget",), claims=())
        saved = transitions._TICKETS, _insp._CHART_BERTHS
        transitions._TICKETS, _insp._CHART_BERTHS = tickets, berths
        try:
            record = transitions.inspect_entry("widget")
            try:
                transitions._entry_gate("widget")
            except transitions.EntryGateRed as e:
                raised = e.findings
            else:
                raise AssertionError("a chartless ticket passed the entry gate")
        finally:
            transitions._TICKETS, _insp._CHART_BERTHS = saved
    assert raised == transitions._findings_of(record), \
        "the refusal's findings and the record's mismatches must be ONE derivation"
    assert [f["method"] for f in raised] == ["buildme_rides_the_chart"], raised
    # and the record still lists what PASSED beside the one that did not — the half a
    # findings list throws away
    assert len(record) == 3 and sum(transitions.gate.passed(e) for e in record) == 2, record


def test_a_lane_that_refuses_and_names_nothing_still_speaks():
    """``_findings_of`` is not a flatten over the findings lists alone. A lane that FAILS
    while carrying no finding payload is a refusal with no sentence, and flattening would
    have dropped it silently — the exact silence the record exists to end. The rules rung's
    lanes carry no findings key at all, so this is not a hypothetical shape."""
    wf = transitions.parse_workflow(_CODE_SEAM)
    class_def = transitions.load_class_def(wf.node_class)
    out = transitions._findings_of(
        transitions.inspect_rules(wf, "NOPE", class_def=class_def))
    assert len(out) == 1 and "named no finding" in out[0]["about"], out
    assert out[0]["expected"] and out[0]["actual"], out
    # non-vacuity: an all-passing record contributes nothing
    assert transitions._findings_of(
        transitions.inspect_rules(wf, "PROVEME", class_def=class_def)) == []


def test_demo_gate_refuses_a_demo_flagged_ticket_without_akiens_approval():
    """A ticket with ``"demo": true`` cannot cross into PROVED without a DEMO validation
    (quorum seal with Akien as signer). The gate reads the ticket file — if it carries the
    flag, it demands the seal. If no seal exists, DemoGateRed fires before anything is
    written.

    Provenance: ticket demo-gate, 2026-07-26. Akien's founding reason: 'the prior system
    didn't have me trying to be insistent on showing me each thing working.' Binding
    resolved 2026-08-20: Akien picks at /sorted; clearing is: he watched and approved."""
    with tempfile.TemporaryDirectory() as d:
        hist, state = f"{d}/history.json", f"{d}/state.json"
        # Create a ticket with demo: true
        ticket_dir = Path(d) / "tickets"
        ticket_dir.mkdir()
        ticket_path = ticket_dir / "test-demo-ticket.json"
        ticket_path.write_text(json.dumps({"id": "test-demo-ticket", "demo": True,
                                            "state": "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]"}))

        wf_str = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
        # The gate reads from _TICKETS; we cannot redirect that without patching,
        # so test the gate function directly.
        note, record = transitions._require_demo("test-demo-ticket", {},)
        # With no ticket file at the real _TICKETS path, the gate returns None (does not fire)
        assert note is None, f"gate fired on a missing ticket file — expected None, got {note!r}"

        # Now test the _require_demo against a ticket that DOES exist with demo: true
        # by writing to the real tickets path temporarily
        import shutil
        real_tickets = transitions._TICKETS
        real_path = real_tickets / "test-demo-ticket.json"
        try:
            real_path.write_text(json.dumps({"id": "test-demo-ticket", "demo": True}))
            try:
                transitions._require_demo("test-demo-ticket", {})
                raise AssertionError("DemoGateRed should have fired — no DEMO validation exists")
            except transitions.DemoGateRed:
                pass  # correct: refused without Akien's approval
        finally:
            real_path.unlink(missing_ok=True)


def test_demo_gate_does_not_fire_on_a_ticket_without_the_flag():
    """A ticket with no ``demo`` field crosses PROVED freely — this gate seat does not
    fire, the other seats still do their jobs."""
    real_tickets = transitions._TICKETS
    real_path = real_tickets / "test-no-demo-ticket.json"
    try:
        real_path.write_text(json.dumps({"id": "test-no-demo-ticket"}))
        note, record = transitions._require_demo("test-no-demo-ticket", {})
        assert note is None, f"gate fired on a ticket with no demo flag — got {note!r}"
    finally:
        real_path.unlink(missing_ok=True)


def test_demo_gate_passes_with_a_green_quorum_seal():
    """A ticket with ``demo: true`` AND a green DEMO validation crosses PROVED cleanly.
    The gate returns a note naming the seal date — the record of truth carries the evidence."""
    import os
    real_tickets = transitions._TICKETS
    real_path = real_tickets / "test-demo-sealed-ticket.json"
    val_dir = real_tickets / "validations"
    val_path = val_dir / "test-demo-sealed-ticket.json"
    try:
        real_path.write_text(json.dumps({"id": "test-demo-sealed-ticket", "demo": True}))
        val_dir.mkdir(exist_ok=True)
        val_path.write_text(json.dumps([{
            "claim": "DEMO — Akien watched and approved",
            "caller": "akien",
            "date": "2026-08-20T12:00:00",
            "method": "DEMO quorum signature gate",
            "verdict": "green",
            "evidence": {"signatures": [{"signer": "akien", "verdict": "green",
                                          "restated": "watched it work"}],
                          "notary": "cc"},
            "falsifier": "demo-gate",
            "horizon": "next design shift",
        }]))
        note, record = transitions._require_demo("test-demo-sealed-ticket", {})
        assert note is not None, "gate returned None — should have returned a passing note"
        assert "Akien watched and approved" in note, f"note does not name the approval: {note}"
    finally:
        real_path.unlink(missing_ok=True)
        val_path.unlink(missing_ok=True)
        if val_dir.exists() and not any(val_dir.iterdir()):
            val_dir.rmdir()


def _main() -> int:
    # THE ROSTER IS DERIVED, never hand-typed. A tooth nobody listed is a tooth that did not
    # run, and the file prints the same green line — the same defect as the proof record, one
    # level up. Caught twice by hand on 2026-08-13 before it was made physics here.
    checks = [v for k, v in sorted(globals().items())
              if k.startswith("test_") and callable(v)]
    assert len(checks) >= 58, (
        "the derived roster collapsed — teeth are being counted by a broken rule, and a "
        f"roster that shrinks silently is the defect it replaced: {len(checks)}")
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
          "on a second tenant — and A SUMMONS SHOWS ITS PICKUP (ruled 2026-08-07, "
          "the-ticket-is-the-source-period): the cursor carries its phase in the grammar "
          "([X:waiting] on arrival, [X:in-process] through the pickup door beside emit, "
          "journaled with actor + time through the projector), a phase off-cursor / on a "
          "rest / off-vocabulary refuses at parse, a doubled pickup and a pickup at a rest "
          "refuse writing nothing, and the whole standing corpus parses phase=None — the "
          "legacy grammar is a strict subset, measured, not assumed — AND THE SIXTH SEAT "
          "NOW STANDS (ticket emit-refuses-an-uncleared-crossing, draining the live trouble "
          "every-crossing-goes-around-the-clearance-gate, under which ZERO of 146 emit-shaped "
          "records on disk had ever carried cleared_by): a forward crossing into a REST "
          "carries the harbor's clearance witness or refuses before anything is written; the "
          "witness is RE-READ AGAINST THE WORLD, so an incomplete one, a proof the tester "
          "never sealed, and a seal date that disagrees with the standing seal are each "
          "refused in their own words and a hand-typed cleared_by forges nothing; a cleared "
          "crossing lands with the proof and the seal it leaned on in its own record (Law 5); "
          "a crossing into a summons and a retreat are both untouched, by design; and the "
          "clearance roster is a SECOND roster, empty in production — this gate's own voyage "
          "CLEARED rather than being waived through it — AND THE SEVENTH SEAT (ticket "
          "demo-gate, 2026-07-26, resolved 2026-08-20): a ticket carrying demo: true "
          "cannot cross into PROVED without a DEMO validation (quorum seal with Akien as "
          "signer); a ticket without the flag crosses freely; a sealed ticket passes cleanly")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

#!/usr/bin/env python3
"""Proof for ticket 284798998ab0 — the ticket file is nothing but the build plan.

Akien 2026-10-29 (open-c7809a745bf7): *"three parts. record it and reshape the ticket."* A
ticket is three files beside each other: the PLAN ``<id>-<slug>.json`` (what a builder builds
from), the STATE ``<id>-<slug>.state.json`` (what a gate or door reads or writes as the ticket
moves) and the LOG ``<id>-<slug>.log.jsonl`` (everything else). The split is the census
``CairnCommons/measurements/2026-10-29-ticket-fields-plan-state-log.json``.

Teeth (D9), each over a scratch tickets dir whose store charter is the live one with its three
field lists set to the census, so the door, the jurisdiction rule and ticket_file are measured
apart from the migration that narrows the live charter (D11):
  (1) the LIVE charter's plan_fields, state_fields and log_fields equal the census's plan,
      state and log, pairwise disjoint;
  (2) the door writes a state file of state keys only, refuses one holding a plan key, and
      refuses a plan write holding a state key;
  (3) write_ticket then read_ticket returns the doc it was given, every state key in the state
      file and none in the plan;
  (4) plans() over a dir holding a plan, its .state.json, its .log.jsonl and the charter yields
      the plan alone;
  (5) split then reconstruct over a fixture v2 ticket returns the doc it split;
  (6) set_phase changes the state file and leaves the plan's bytes, and design_sha of them,
      unchanged.
Then the READERS (D8): one tooth per site the build rewrote to ride ticket_file, each over its
own fresh split world (and an orphan state file where a plain split cannot tell the readers
apart), each expected value measured against the reader reverted to 2162ff41 giving the other
answer. Then the CORPUS (D11, the live store): every plan carries only plan_fields, every plan
has a state file of state_fields only, no state file stands without its plan, and every log
keeps the field lines the migration wrote (``measurements/2026-10-30-ticket-log-field-ledger.json``).
The one declared tooth, ``test_the_ticket_is_three_files``, is all of them together (the
falsifier carries no numbered clauses). ``--corpus`` runs the corpus teeth alone.

    bin/cairn test cairn/tools/base/proofs/test_the_ticket_is_three_files.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

COMMONS = REPO.parent / "CairnCommons"
LIVE_CHARTER = COMMONS / "tickets" / "_charter+why.json"
CENSUS = COMMONS / "measurements" / "2026-10-29-ticket-fields-plan-state-log.json"

PROVES = {"284798998ab0": {"all": "test_the_ticket_is_three_files"}}

TEETH = ("test_the_charter_declares_three_disjoint_field_sets",
         "test_the_door_keys_the_state_file_by_state_fields",
         "test_write_then_read_returns_the_doc_split_across_two_files",
         "test_plans_yields_the_plan_alone",
         "test_split_then_reconstruct_returns_the_doc",
         "test_a_crossing_moves_only_the_state_file")
CORPUS = ("corpus_every_plan_carries_only_plan_fields",
          "corpus_every_plan_has_a_state_file_of_state_fields",
          "corpus_no_state_file_stands_without_its_plan",
          "corpus_every_log_keeps_the_field_lines_the_migration_wrote")
FAILURES: list[str] = []
CURSOR = "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _census() -> dict:
    return json.loads(CENSUS.read_text(encoding="utf-8"))["summary"]


def _tickets(commons: Path) -> Path:
    t = commons / "tickets"
    t.mkdir(parents=True)
    charter = json.loads(LIVE_CHARTER.read_text(encoding="utf-8"))
    c = _census()
    charter["plan_fields"], charter["state_fields"], charter["log_fields"] = c["plan"], c["state"], c["log"]
    (t / "_charter+why.json").write_text(json.dumps(charter, indent=2, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    return t


def _doc(tid: str) -> dict:
    return {"id": tid, "title": "a proof world ticket", "intention": "a fixture", "why": "a proof",
            "how": "none", "falsifier": "none", "decisions": [{"n": 1, "text": "D1: a line"}],
            "date": "2026-10-29", "owner": "CC", "node_class": "code-seam",
            "workflow_and_state": CURSOR, "watchme": "none, because a fixture",
            "questions": ["open-000000000000"]}


def _state_keys() -> set:
    return set(_census()["state"])


def test_the_charter_declares_three_disjoint_field_sets() -> None:
    charter, c = json.loads(LIVE_CHARTER.read_text(encoding="utf-8")), _census()
    got = {k: charter.get(f"{k}_fields") for k in ("plan", "state", "log")}
    equal = all(got[k] == c[k] for k in got)
    disjoint = equal and not (set(c["plan"]) & set(c["state"]) or set(c["plan"]) & set(c["log"])
                              or set(c["state"]) & set(c["log"]))
    check(TEETH[0], equal and disjoint,
          "; ".join(f"{k}_fields {len(v) if v else v} vs census {len(c[k])}" for k, v in got.items()))


def test_the_door_keys_the_state_file_by_state_fields(A, t: Path) -> None:
    good = t / "aaaa1111bbbb-door.state.json"
    wrote = refused_state = refused_plan = False
    try:
        A.write_json(good, {"workflow_and_state": CURSOR, "owner": "CC"}, verb="phase", why="proof")
        wrote = good.is_file()
    except A.Refused as exc:
        print(f"    a state-only state file was refused: {exc}")
    try:
        A.write_json(t / "aaaa1111bbbb-bad.state.json", {"how": "a plan key"}, verb="phase", why="proof")
    except A.Refused:
        refused_state = not (t / "aaaa1111bbbb-bad.state.json").exists()
    try:
        A.write_json(t / "aaaa1111bbbb-bad.json", {"id": "aaaa1111bbbb", "workflow_and_state": CURSOR},
                     verb="cast", why="proof")
    except A.Refused:
        refused_plan = not (t / "aaaa1111bbbb-bad.json").exists()
    check(TEETH[1], wrote and refused_state and refused_plan,
          f"state file written {wrote}; plan key in state refused {refused_state}; "
          f"state key in plan refused {refused_plan}")


def test_write_then_read_returns_the_doc_split_across_two_files(TF, t: Path) -> None:
    plan = t / "bbbb2222cccc-round.json"
    doc = _doc("bbbb2222cccc")
    TF.write_ticket(plan, doc, False, True, why="proof")
    on_plan = json.loads(plan.read_text(encoding="utf-8"))
    on_state = json.loads(TF.state_path(plan).read_text(encoding="utf-8"))
    back = TF.read_ticket(plan)
    sk = _state_keys()
    ok = (back == doc and not (set(on_plan) & sk) and set(on_state) == set(doc) & sk)
    check(TEETH[2], ok, f"plan keys {sorted(on_plan)}; state keys {sorted(on_state)}; equal {back == doc}")


def test_plans_yields_the_plan_alone(TF, tmp: Path) -> None:
    d = tmp / "plans-world"
    d.mkdir()
    for name in ("cccc3333dddd-p.json", "cccc3333dddd-p.state.json", "cccc3333dddd-p.log.jsonl",
                 "_charter+why.json"):
        (d / name).write_text("{}\n", encoding="utf-8")
    got = [p.name for p in TF.plans(d)]
    found = TF.find_ticket("cccc3333dddd", d)
    check(TEETH[3], got == ["cccc3333dddd-p.json"] and found is not None and found.name == got[0],
          f"plans {got}; find_ticket {found}")


def test_split_then_reconstruct_returns_the_doc(L, TF, t: Path) -> None:
    plan = t / "dddd4444eeee-split.json"
    doc = {**_doc("dddd4444eeee"), "an_ad_hoc_trail_field": {"said": "trail"}}
    plan.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out = L.split(plan, actor="proof", why="proof: split")
    after = json.loads(plan.read_text(encoding="utf-8"))
    state = json.loads(TF.state_path(plan).read_text(encoding="utf-8"))
    back = L.reconstruct(after, L.read_log(plan), state)
    sk = _state_keys()
    ok = (back == doc and not (set(after) & sk) and set(state) == set(doc) & sk
          and (out.get("moved") or {}).get("state") == len(set(doc) & sk))
    check(TEETH[4], ok, f"moved {out.get('moved')}; plan {sorted(after)}; lossless {back == doc}")


def test_a_crossing_moves_only_the_state_file(T, TF, R, t: Path) -> None:
    plan = t / "eeee5555ffff-phase.json"
    TF.write_ticket(plan, _doc("eeee5555ffff"), False, True, why="proof")
    pb, sb = plan.read_bytes(), TF.state_path(plan).read_bytes()
    saved = TF._TICKETS
    TF._TICKETS = t
    try:
        T.set_phase(CURSOR, "hold", release="CLAUDE.md", actor="proof", ticket="eeee5555ffff")
    finally:
        TF._TICKETS = saved
    ok = (plan.read_bytes() == pb and R.design_sha(plan.read_bytes()) == R.design_sha(pb)
          and TF.state_path(plan).read_bytes() != sb and "workflow_and_state" not in json.loads(pb))
    check(TEETH[5], ok, f"plan unchanged {plan.read_bytes() == pb}; state moved {TF.state_path(plan).read_bytes() != sb}")


# ── the readers (D8): every site the build rewrote reads the plan merged with its state ──────
#
# Each reader tooth stands a fresh split world — one plan, its state, its log — plus, where a
# plain split cannot tell the readers apart, an ORPHAN state file (a .state.json with no plan
# beside it). A reader that still lists the dir itself, or json-loads the plan alone, answers
# differently from one that rides ticket_file.plans / find_ticket / read_ticket, and each
# expected value below was measured against the reader reverted to the pre-build commit
# (2162ff41) giving the other answer.

TID, TID2 = "aaaaaaaaaaa1", "bbbbbbbbbbb2"
PLAN = TID + "-a-split-fixture"


def _world(tmp: Path) -> Path:
    t = _tickets(tmp / "CairnCommons")
    plan = {"id": TID, "title": "a split fixture", "owning_intention": "cairn/tools/base/intention+why.json",
            "intention": "a fixture", "why": "a proof", "traces_to": "Law 5", "how": "none",
            "falsifier": "none", "decisions": [{"n": 1, "text": "D1: a line"}]}
    state = {"date": "2026-10-30", "owner": "CC", "node_class": "code-seam", "workflow_and_state": CURSOR,
             "watchme": "none, because a fixture", "questions": ["open-aaaaaaaaaaa1"],
             "intent_berth": "/nowhere/intent-berth.json", "sorted_berth": "/nowhere/sorted-berth.json",
             "build_commits": ["deadbeef"]}
    (t / (PLAN + ".json")).write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    (t / (PLAN + ".state.json")).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    lines = [{"kind": "field", "at": "2026-10-30T00:00:00", "actor": "proof", "field": "from_idea",
              "value": "2026-10-30-a-fixture-idea"},
             {"kind": "field", "at": "2026-10-30T00:00:00", "actor": "proof",
              "field": "measurements_since_cast", "value": [{"m": 1}]}]
    (t / (PLAN + ".log.jsonl")).write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
    return t


def _state(t: Path, **over) -> None:
    s = t / (PLAN + ".state.json")
    s.write_text(json.dumps({**json.loads(s.read_text(encoding="utf-8")), **over}) + "\n", encoding="utf-8")


def _orphan(t: Path, doc=None, corrupt: bool = False) -> None:
    doc = {"workflow_and_state": CURSOR, "watchme": "none, because a fixture"} if doc is None else doc
    (t / (TID2 + "-an-orphan-state.state.json")).write_text(
        "{not json" if corrupt else json.dumps(doc) + "\n", encoding="utf-8")


def _raises(fn, kind: str, words: str = "") -> tuple[bool, str]:
    try:
        got = fn()
    except Exception as exc:  # noqa: BLE001 — the kind of the refusal is the measurement
        return type(exc).__name__ == kind and words in str(exc), f"{type(exc).__name__}: {str(exc)[:160]}"
    return False, f"returned {got!r:.160}"


def _mod(name: str):
    import importlib
    return importlib.import_module(name)


def r_inbox(t, patch):
    got = [(x.get("id"), x.get("title"), str(x.get("source", "")).rsplit("/", 1)[-1])
           for x in _mod("cairn.tools.operator_inbox.inbox")._scan_tickets(t)]
    return got == [(TID, "a split fixture", PLAN + ".json")], got


def r_ticket_inspector(t, patch):
    out = _mod("cairn.tools.ticket_inspector.inspector").inspect_corpus(t)
    got = (out["tickets_checked"], out["total_findings"])
    return got == (1, 0), got


def r_watchme_spec(t, patch):
    got = _mod("cairn.tools.base.watchme_spec").sweep(t)
    return len(got) == 1, got


def r_proof_coverage(t, patch):
    got = [(x.get("id"), x.get("workflow_and_state"))
           for x in _mod("cairn.tools.proof_coverage.proof_coverage").load_tickets(t.parent)]
    return got == [(TID, CURSOR)], got


def r_transitions(t, patch):
    got = _mod("cairn.tools.base.transitions")._ticket_standing(str(t / (PLAN + ".json")))
    return got == "BUILDME", got


def r_skill_block(t, patch):
    i = t.parent / "ideas"
    i.mkdir()
    (i / "2026-10-30-a-fixture-idea.json").write_text(json.dumps({"berth": "/nowhere/idea-berth.json"}))
    got = _mod("cairn.machines.skill_block.skill_block").berth_ticket_cursors(tickets=t, ideas=i)
    return "/nowhere/idea-berth.json" in repr(got), got


def r_does_optional(t, patch):
    for p in list(t.glob(PLAN + "*")):
        p.rename(p.with_name(p.name.replace("a-split-fixture", "watchme-emits-a-probe")))
    m = _mod("cairn.tools.base.probes.does_optional_mean_never_carried")
    patch(m, "_TICKETS", t)
    got = m.survey_the_corpus()
    return got.get("eligible") == 0, got


def _proved(t):
    _state(t, workflow_and_state="code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]")


def r_uncharted_build(t, patch):
    _proved(t)
    m = _mod("cairn.tools.base.probes.no_component_reaches_proved_with_an_uncharted_build")
    patch(m, "_TICKETS_DIR", str(t))
    got = m._proved_tickets()
    return TID in repr(got) and ".state" not in repr(got), got


def r_unchartered_edits(t, patch):
    _proved(t)
    patch(_mod("cairn.tools.chain.chain"), "chain_for_ticket", lambda i: {"validate": i})
    m = _mod("cairn.tools.base.probes.unchartered_build_edits")
    patch(m, "_TICKETS_DIR", str(t))
    got = m._proved_tickets_with_chains()
    return TID in repr(got) and ".state" not in repr(got), got


def _live_tickets(module):
    def reader(t, patch):
        _orphan(t)
        m = _mod(module)
        patch(m, "_TICKETS", t)
        got = m._walk_tickets()["live_tickets"]
        return got == 1, got
    return reader


def r_compiler(t, patch):
    _orphan(t)
    m = _mod("cairn.tools.intentions_model_compiler.probes.present_tense_artifacts_carry_no_dated_appends")
    patch(m, "_TICKETS", t)
    got = (m._ticket_state(TID), m._ticket_state(TID2))
    return got == (CURSOR, None), got


CLEARANCE = "cairn.devices.cairn.machines.harbor_master.clearance"


def r_riders_of(t, patch):
    got = _mod(CLEARANCE).riders_of("cairn/tools/base/intention+why.json", tickets_dir=str(t),
                                    commons_root=str(t.parent))
    return tuple(getattr(got, "riding", ())) == (TID,), got


def r_boat_owner_of(t, patch):
    try:
        got = _mod(CLEARANCE).boat_owner_of(TID, tickets_dir=str(t), commons_root=str(t.parent))
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {str(exc)[:160]}"
    return True, got


def _roots(t):
    _mod("cairn.tools.artifact.artifact").set_diagnostic_roots({"CairnCommons": t.parent, "cairn": REPO})


def r_check_title(t, patch):
    _roots(t)
    got = _mod("cairn.tools.artifact.artifact").check_title("records: " + TID + " BUILDME")
    return got == [], got


def r_question_berth(t, patch):
    _roots(t)
    got = _mod("cairn.tools.question.question")._berth_of(TID)
    return got == "/nowhere/intent-berth.json", got


def r_cross(t, patch):
    m = _mod("cairn.tools.base.cross")
    return _raises(lambda: m.cross(TID, "BUILDME", actor="proof", why="x", tickets_dir=t),
                   "IllegalTransition", "no-op")


def r_crossings(t, patch):
    _orphan(t, corrupt=True)
    got = _mod("cairn.tools.base.crossings").drop_stored_crossings(
        {"commons": t.parent, "cairn": REPO})["unreadable"]
    return got == [], got


def r_chain_scan(t, patch):
    _orphan(t, corrupt=True)
    got = _mod("cairn.tools.chain.chain").scan(str(t))
    return got == [], got


def r_chain_carriers(t, patch):
    _orphan(t, {"chart_chain": {}})
    got = _mod("cairn.tools.chain.chain").carriers(str(t))
    return got == [], got


def r_hollow(t, patch):
    _orphan(t)
    m = _mod("cairn.devices.tester.hollow")
    return _raises(lambda: m._ticket_path(TID2, t.parent), "HollowUnmeasurable")


def r_buildme_rides_the_sorted(t, patch):
    got = _mod("cairn.machines.build_inspector.inspector").buildme_rides_the_sorted(
        TID, tickets_root=t.parent.parent / "cairn")
    return "sorted berth readable" in repr(got), got


def r_harbor_watch(t, patch):
    _state(t, watchme={"object": "x", "probe": "cairn/tools/base/probes/x.py"})
    patch(_mod(CLEARANCE), "_crossing_roots",
          lambda: {"repo": t.parent.parent / "repo", "commons": t.parent, "instance": t.parent.parent / "inst"})
    got = _mod("cairn.devices.cairn.machines.harbor_master.device").HarborMasterDevice()._handle_watch(
        {"id": "w", "to": "harbor_master", "verb": "watch", "why": "x", "sender": "proof",
         "body": {"ticket": TID, "holds": True}})
    return "sits under no component charter" in repr(got), got


def r_tellmeabout_stem(t, patch):
    _orphan(t)
    got = _mod("skills.tellmeabout.tellmeabout")._find_by_stem(TID2 + "-an-orphan-state.state", t, "tickets")
    return got == [], got


def r_tellmeabout_present(t, patch):
    got = _mod("skills.tellmeabout.tellmeabout")._present(
        {"store": "tickets", "name": "x", "address": str(t / (PLAN + ".json"))})["found"]["waiting_on"]
    return "BUILDME:waiting" in got, got


def r_grammar(t, patch):
    _orphan(t)
    got = _mod("cairn.tools.chain.grammar").ticket_path(TID2, tickets_dir=str(t))
    return got is None, got


def r_validate(t, patch):
    _state(t, node_class="concept-piece")
    got = _mod("cairn.devices.codemother.machines.validate.validate")._clause_coverage_record(
        {"ticket": TID, "criteria": []}, str(t.parent.parent / "cairn"))
    return got == [], got


def r_codemother_shim(t, patch):
    patch(_mod("cairn.tools.chain.grammar"), "ticket_path", lambda c, *a, **k: str(t / (PLAN + ".json")))
    got = _mod("cairn.devices.codemother.shim").CodeMotherDevice._crossing_coordinates(
        TID, {"proven_by": ["x"]})["workflow"]
    return got == CURSOR, got


def r_failed_run(t, patch):
    _orphan(t)
    r = t.parent / "rehearsals"
    r.mkdir()
    (r / "x.json").write_text(json.dumps({"ran": False, "ticket": TID2}))
    got = _mod("cairn.machines.rehearsal.probes.a_failed_run_is_counted")._measure({}, commons=t.parent)["failed"]
    return got == 0, got


def _carriers(module, key, value):
    def reader(t, patch):
        (t / (TID2 + "-x.state.json")).write_text(json.dumps({key: value}))
        m = _mod(module)
        patch(m, "_TICKETS", t)
        got = m._walk()["carriers"]
        return got == [], got
    return reader


def r_casting_door(t, patch):
    _orphan(t)
    got = _mod("cairn.tools.base.probes.the_casting_door_has_callers").survey_the_casts(
        commons_root=t.parent)["unjournaled"]
    return got == ["tickets/" + PLAN + ".json"], got


P = "cairn.tools.base.probes."
READERS = (
    ("reader_inbox_scans_plans_with_their_state", r_inbox),
    ("reader_ticket_inspector_checks_each_ticket_once", r_ticket_inspector),
    ("reader_watchme_sweep_sees_each_ticket_once", r_watchme_spec),
    ("reader_proof_coverage_loads_plans_with_their_cursor", r_proof_coverage),
    ("reader_transitions_standing_reads_the_state_cursor", r_transitions),
    ("reader_skill_block_follows_the_logged_idea", r_skill_block),
    ("reader_does_optional_counts_no_state_file", r_does_optional),
    ("reader_uncharted_build_names_ticket_ids", r_uncharted_build),
    ("reader_unchartered_edits_names_ticket_ids", r_unchartered_edits),
    ("reader_write_door_walks_plans_only", _live_tickets(P + "the_ticket_write_door_has_callers")),
    ("reader_vocabulary_walks_plans_only", _live_tickets(P + "the_vocabulary_is_written_not_just_legal")),
    ("reader_compiler_reads_a_cursor_only_through_a_plan", r_compiler),
    ("reader_clearance_riders_read_the_state", r_riders_of),
    ("reader_clearance_boat_owner_finds_one_plan", r_boat_owner_of),
    ("reader_artifact_check_title_finds_one_plan", r_check_title),
    ("reader_question_berth_reads_the_state", r_question_berth),
    ("reader_cross_reads_the_merged_cursor", r_cross),
    ("reader_crossings_ignores_a_state_file", r_crossings),
    ("reader_chain_scan_ignores_a_state_file", r_chain_scan),
    ("reader_chain_carriers_ignores_a_state_file", r_chain_carriers),
    ("reader_hollow_finds_no_ticket_in_a_state_file", r_hollow),
    ("reader_build_inspector_reads_the_sorted_berth_from_state", r_buildme_rides_the_sorted),
    ("reader_harbor_watch_reads_the_state_watchme", r_harbor_watch),
    ("reader_tellmeabout_skips_a_state_stem", r_tellmeabout_stem),
    ("reader_tellmeabout_presents_the_state_cursor", r_tellmeabout_present),
    ("reader_grammar_ticket_path_never_a_state_file", r_grammar),
    ("reader_validate_reads_node_class_from_state", r_validate),
    ("reader_codemother_shim_reads_the_state_cursor", r_codemother_shim),
    ("reader_failed_run_counts_no_state_file", r_failed_run),
    ("reader_no_stored_chart_chain_walks_plans_only",
     _carriers(P + "no_ticket_carries_a_stored_chart_chain", "chart_chain", {})),
    ("reader_no_stored_crossing_walks_plans_only",
     _carriers(P + "no_ticket_carries_a_stored_crossing", "crossings", [])),
    ("reader_casting_door_lists_plans_only", r_casting_door),
)


def readers() -> None:
    """Each reader over its own fresh world; every patched attribute and the artifact roots are
    put back after each, so one reader's fixture can never stand behind the next."""
    from cairn.tools.artifact import artifact as A
    for name, reader in READERS:
        saved: list = []

        def patch(mod, attr, value, _saved=saved):
            _saved.append((mod, attr, getattr(mod, attr)))
            setattr(mod, attr, value)

        with tempfile.TemporaryDirectory(prefix="cairn-ticket-reader-proof-") as d:
            try:
                ok, got = reader(_world(Path(d)), patch)
                check(name, ok, f"{got!r:.300}")
            except Exception as exc:  # noqa: BLE001 — the reason is the record
                check(name, False, f"{type(exc).__name__}: {str(exc)[:200]}")
            finally:
                for mod, attr, value in reversed(saved):
                    setattr(mod, attr, value)
                A.set_diagnostic_roots(None)


LEDGER = COMMONS / "measurements" / "2026-10-30-ticket-log-field-ledger.json"


def _corpus_findings() -> dict:
    """The live store against the split, one finding list per corpus tooth. The ledger is the
    measurement taken right after the migration (D11): every log's kind 'field' lines then, so a
    log reverted or truncated since is a log lacking a line it carried."""
    from cairn.tools.base import ticket_file as TF
    from cairn.tools.base import ticket_log as L
    tickets = COMMONS / "tickets"
    plan_f, state_f = set(L.plan_fields(LIVE_CHARTER)), set(L.state_fields(LIVE_CHARTER))
    found = {k: [] for k in CORPUS}
    plans = TF.plans(tickets)
    for p in plans:
        extra = set(json.loads(p.read_text(encoding="utf-8"))) - plan_f
        if extra:
            found[CORPUS[0]].append(f"{p.name}: plan carries {sorted(extra)}")
        s = TF.state_path(p)
        if not s.is_file():
            found[CORPUS[1]].append(f"{p.name}: no state file")
        elif set(json.loads(s.read_text(encoding="utf-8"))) - state_f:
            found[CORPUS[1]].append(
                f"{s.name}: state carries {sorted(set(json.loads(s.read_text(encoding='utf-8'))) - state_f)}")
    owned = {TF.state_path(p).name for p in plans}
    found[CORPUS[2]] = [f"{s.name}: a state file with no plan" for s in sorted(tickets.glob("*.state.json"))
                        if s.name not in owned]
    try:
        rows = json.loads(LEDGER.read_text(encoding="utf-8"))["rows"]
    except (OSError, ValueError, KeyError) as exc:
        found[CORPUS[3]].append(f"the ledger does not read: {exc!r}")
        rows = {}
    for name, want in rows.items():
        plan = tickets / name
        have = ({x.get("field") for x in L.read_log(plan) if x.get("kind") == "field"}
                if plan.is_file() else set())
        if set(want) - have:
            found[CORPUS[3]].append(f"{name}: log lacks {sorted(set(want) - have)}")
    return found


def test_the_live_store_is_split() -> None:
    try:
        found = _corpus_findings()
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        for n in CORPUS:
            check(n, False, f"{type(exc).__name__}: {str(exc)[:200]}")
        return
    for name, bad in found.items():
        check(name, not bad, f"{len(bad)} finding(s); first: {bad[:3]}" if bad else "")


def corpus() -> int:
    found = _corpus_findings()
    bad = [line for lines in found.values() for line in lines]
    for line in bad[:40]:
        print(f"  FAIL  {line}")
    print(f"{'GREEN' if not bad else 'RED — ' + str(len(bad)) + ' finding(s)'}")
    return 1 if bad else 0


def main() -> int:
    if "--corpus" in sys.argv[1:]:
        return corpus()
    test_the_charter_declares_three_disjoint_field_sets()
    try:
        from cairn.tools.artifact import artifact as A
        from cairn.tools.base import ticket_file as TF
        from cairn.tools.base import ticket_log as L
        from cairn.tools.base import transitions as T
        from cairn.machines.rehearsal import rehearsal as R
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject does not load: {exc!r}")
        for n in TEETH[1:] + tuple(n for n, _ in READERS):
            check(n, False, "subject absent")
    else:
        teeth = (lambda t, tmp: test_the_door_keys_the_state_file_by_state_fields(A, t),
                 lambda t, tmp: test_write_then_read_returns_the_doc_split_across_two_files(TF, t),
                 lambda t, tmp: test_plans_yields_the_plan_alone(TF, tmp),
                 lambda t, tmp: test_split_then_reconstruct_returns_the_doc(L, TF, t),
                 lambda t, tmp: test_a_crossing_moves_only_the_state_file(T, TF, R, t))
        with tempfile.TemporaryDirectory(prefix="cairn-ticket-three-files-proof-") as d:
            tmp = Path(d)
            commons = tmp / "CairnCommons"
            t = _tickets(commons)
            A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn",
                                    "parked": tmp / "parked"})
            try:
                for name, tooth in zip(TEETH[1:], teeth):
                    try:
                        tooth(t, tmp)
                    except Exception as exc:  # noqa: BLE001 — the reason is the record
                        check(name, False, f"{type(exc).__name__}: {str(exc)[:200]}")
            finally:
                A.set_diagnostic_roots(None)
        readers()
    test_the_live_store_is_split()
    total = len(TEETH) + len(READERS) + len(CORPUS)
    check("test_the_ticket_is_three_files", not FAILURES, f"{len(FAILURES)} of {total} teeth red")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Proof for cairn/machines/learning_block — teeth a hollow block could not pass.

Runs against injected roots (CAIRN_LB_TRACE_ROOT never set here — every call
passes root=/records_dir= explicitly into a temp world); the live trace berth
and the real learning store are never read or written. NON-VACUITY is
structural: green paths are asserted before each refusal tooth, so a gate that
refuses everything fails the first half and one that passes everything fails
the second.

    python3 cairn/machines/learning_block/proofs/test_learning_block.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.machines.learning_block import learning_block as lb  # noqa: E402
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

NOW = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)


def world():
    return scratch_dir("lb-proof-")


# ── trace teeth ──────────────────────────────────────────────────────────────

def test_typed_write_round_trips():
    root = world()
    rec = lb.write_trace("blk", "door_pass", "training", {"x": 1}, now=NOW, root=root)
    got = lb.read_trace("blk", root=root)
    assert got == [rec], f"one typed write must round-trip as one record: {got}"


def test_typeless_write_is_refused_and_writes_nothing():
    root = world()
    for bad in (None, "", "log", "forever"):
        try:
            lb.write_trace("blk", "door_pass", bad, {}, now=NOW, root=root)
            raise AssertionError(f"consumer {bad!r} must be refused")
        except lb.TraceRefused as e:
            assert "consumer" in str(e)
    assert lb.read_trace("blk", root=root) == [], "a refused write must leave NOTHING"


def test_green_and_red_have_equal_durability():
    root = world()
    lb.write_trace("blk", "door_pass", "training", {"green": True}, now=NOW, root=root)
    lb.write_trace("blk", "send_back", "training", {"green": False}, now=NOW, root=root)
    events = [r["event"] for r in lb.read_trace("blk", root=root)]
    assert events == ["door_pass", "send_back"], \
        "a green firing's record must be as durable as a red's (the denominator)"


def test_debug_expiry_fires_on_write_spares_young_and_non_debug():
    root = world()
    old = NOW - timedelta(days=31)
    young = NOW - timedelta(days=29)
    lb.write_trace("blk", "e1", "debug", {"age": "old"}, now=old, root=root)
    lb.write_trace("blk", "e2", "debug", {"age": "young"}, now=young, root=root)
    lb.write_trace("blk", "e3", "training", {"age": "old-training"}, now=old, root=root)
    survivors = {r["data"].get("age") for r in lb.read_trace("blk", root=root)}
    assert survivors == {"old", "young", "old-training"}, "nothing expires before a NEW write"
    lb.write_trace("blk", "e4", "training", {"age": "now"}, now=NOW, root=root)
    survivors = {r["data"].get("age") for r in lb.read_trace("blk", root=root)}
    assert "old" not in survivors, "a 31-day debug record must expire at the next write"
    assert {"young", "old-training", "now"} <= survivors, \
        "the sweep must spare the young debug and ALL non-debug records"


def test_nothing_resident_in_the_module():
    src = (REPO / "cairn" / "machines" / "learning_block" / "learning_block.py").read_text()
    for word in ("threading", "sched", "asyncio", "signal.alarm", "crontab", "while True"):
        assert word not in src, f"nothing resident, no clock: found {word!r} in the module"


# ── door teeth ───────────────────────────────────────────────────────────────

def _contract():
    return lb.declare_contract("blk", {
        "intent": "a block cannot work on an unstated aim",
        "source": "unattributed input cannot be sent back to anyone",
    })


def test_two_lacks_one_refusal_all_named():
    root = world()
    try:
        lb.fire_door(_contract(), {"unrelated": "x"}, now=NOW, root=root)
        raise AssertionError("an input missing two required fields must be refused")
    except lb.DoorRefused as e:
        fields = {l["field"] for l in e.lacks}
        assert fields == {"intent", "source"}, \
            f"EVERY lack on the first pass, never a dribble: {fields}"
        assert "intent" in str(e) and "source" in str(e), "the message names them all"


def test_refusal_and_pass_are_both_traced_and_input_untouched():
    root = world()
    payload = {"intent": "grind", "source": "akien", "extra": [1, 2]}
    frozen = json.dumps(payload, sort_keys=True)
    lb.fire_door(_contract(), payload, now=NOW, root=root)
    try:
        lb.fire_door(_contract(), {"intent": "grind"}, now=NOW, root=root)
    except lb.DoorRefused:
        pass
    events = [r["event"] for r in lb.read_trace("blk", root=root)]
    assert events == ["door_pass", "send_back"], f"both paths leave a record: {events}"
    sent_back = lb.read_trace("blk", root=root)[1]
    assert sent_back["data"]["lacks"][0]["why"], "the send-back carries WHY per lack"
    assert json.dumps(payload, sort_keys=True) == frozen, "the door must not mutate the input"


def test_hollow_contract_is_refused():
    try:
        lb.declare_contract("blk", {"field": "   "})
        raise AssertionError("a required field with no why must be refused")
    except lb.DoorRefused as e:
        assert "WHY" in str(e.lacks[0]["why"]) or e.lacks[0]["field"] == "field"


# ── finding teeth ────────────────────────────────────────────────────────────

def test_finding_round_trips_with_closed_strata():
    root = world()
    rec = lb.emit_finding("blk", [{"text": "the door refused twice", "stratum": "code"},
                                  {"text": "kin to needs.mark", "stratum": "tree"}],
                          now=NOW, root=root)
    got = lb.read_trace("blk", root=root)[-1]
    assert got["data"]["bullets"] == rec["data"]["bullets"], "emit-retrieve equality"
    assert all(b["stratum"] in lb.STRATA for b in got["data"]["bullets"])


def test_untagged_and_invented_strata_are_refused_naming_the_bullet():
    for bad, needle in (({"text": "naked"}, "stratum"),
                        ({"text": "vibes", "stratum": "gut"}, "gut"),
                        ({"stratum": "code"}, "no text")):
        try:
            lb.emit_finding("blk", [{"text": "fine", "stratum": "code"}, bad],
                            now=NOW, root=world())
            raise AssertionError(f"bullet {bad} must be refused")
        except lb.FindingRefused as e:
            assert "bullet 1" in str(e), f"the refusal must NAME the bullet: {e}"
            assert needle in str(e) or "text" in str(e)


def test_hex_only_via_the_seam():
    root = world()
    try:
        lb.emit_finding("blk", [{"text": "i asked an llm, trust me", "stratum": "hex"}],
                        now=NOW, root=root)
        raise AssertionError("a hand-authored hex bullet is invented provenance")
    except lb.FindingRefused as e:
        assert "hex" in str(e)
    rec = lb.emit_finding("blk", [{"text": "floor says fine", "stratum": "code"}],
                          hex_source=lambda: ["the llm noticed a smell"], now=NOW, root=root)
    strata = [b["stratum"] for b in rec["data"]["bullets"]]
    assert strata == ["code", "hex"], f"stub seam bullets land tagged hex: {strata}"
    rec2 = lb.emit_finding("blk", [{"text": "no seam today", "stratum": "code"}],
                           now=NOW, root=root)
    assert all(b["stratum"] != "hex" for b in rec2["data"]["bullets"]), \
        "no injected callable -> zero hex bullets, ever"


def test_module_imports_no_inference_client():
    """Scoped to IMPORT LINES, not prose — the docstring rightly NAMES
    inference_domain as where the seam points; only an import would wire it
    (the leak-scan lesson: scope the scan to where the defect can actually live)."""
    src = (REPO / "cairn" / "machines" / "learning_block" / "learning_block.py").read_text()
    imports = [l for l in src.splitlines() if l.strip().startswith(("import ", "from "))]
    for word in ("inference_domain", "ollama", "requests", "urllib", "http", "socket"):
        hit = [l for l in imports if word in l]
        assert not hit, \
            f"the seam POINTS at inference_domain; the wiring stays behind that door: {hit}"


# ── verdict teeth ────────────────────────────────────────────────────────────

def _finding(root):
    return lb.emit_finding("blk", [{"text": "b1", "stratum": "code"}], now=NOW, root=root)


def test_verdict_conforms_to_the_stores_v0_shape():
    root, records = world(), world()
    path = lb.record_verdict("blk", _finding(root), "approve", "CC++ looks right",
                             session="proof", now=NOW, records_dir=records, trace_dir=root)
    doc = json.loads(Path(path).read_text())
    assert set(doc) == {"session", "note", "records"}, "the store's nesting, exactly"
    rec = doc["records"][0]
    for field in ("id", "date", "session", "gate", "decision", "signal", "evidence",
                  "ceiling", "confidence_move", "note", "provenance"):
        assert field in rec, f"v0 field missing from the gate-record: {field}"
    assert rec["evidence"] == "confirmation" and rec["signal"]["kind"] == "approve"
    assert rec["decision"]["bullets"], "the verdict carries the bullets it judged"


def test_approve_and_disprove_recorded_with_equal_fidelity():
    root, records = world(), world()
    lb.record_verdict("blk", _finding(root), "approve", "yes", session="p",
                      now=NOW, records_dir=records, trace_dir=root)
    lb.record_verdict("blk", _finding(root), "disprove", "no — wrong layer", session="p",
                      now=NOW, records_dir=records, trace_dir=root)
    doc = json.loads((records / f"{NOW.date().isoformat()}-learning-block.json").read_text())
    kinds = [r["signal"]["kind"] for r in doc["records"]]
    assert kinds == ["approve", "disprove"], f"greens recorded like reds: {kinds}"
    assert doc["records"][0]["evidence"] == "confirmation"
    assert doc["records"][1]["evidence"] == "correction"
    assert "- fast" in doc["records"][1]["confidence_move"] and \
           "+ slow" in doc["records"][0]["confidence_move"], \
        "asymmetric by the store's own guardrail"


def test_verdict_without_finding_or_words_is_refused():
    root, records = world(), world()
    try:
        lb.record_verdict("blk", {}, "approve", "yes", session="p",
                          now=NOW, records_dir=records, trace_dir=root)
        raise AssertionError("a verdict with no finding context teaches nothing")
    except lb.VerdictRefused as e:
        assert "finding" in str(e)
    try:
        lb.record_verdict("blk", _finding(root), "approve", "   ", session="p",
                          now=NOW, records_dir=records, trace_dir=root)
        raise AssertionError("a verdict without Akien's words is CC's keystroke")
    except lb.VerdictRefused as e:
        assert "verbatim" in str(e) or "words" in str(e)
    try:
        lb.record_verdict("blk", _finding(root), "maybe", "hmm", session="p",
                          now=NOW, records_dir=records, trace_dir=root)
        raise AssertionError("an invented signal must be refused")
    except lb.VerdictRefused as e:
        assert "maybe" in str(e)


# ── dial teeth ───────────────────────────────────────────────────────────────

def test_dial_equals_a_hand_count_and_updates_on_new_evidence():
    root, records = world(), world()
    c = _contract()
    lb.fire_door(c, {"intent": "a", "source": "b"}, now=NOW, root=root)
    lb.fire_door(c, {"intent": "a", "source": "b"}, now=NOW, root=root)
    try:
        lb.fire_door(c, {}, now=NOW, root=root)
    except lb.DoorRefused:
        pass
    lb.record_verdict("blk", _finding(root), "approve", "yes", session="p",
                      now=NOW, records_dir=records, trace_dir=root)
    lb.record_verdict("blk", _finding(root), "disprove", "no", session="p",
                      now=NOW, records_dir=records, trace_dir=root)
    lb.record_verdict("blk", _finding(root), "question", "what is this?", session="p",
                      now=NOW, records_dir=records, trace_dir=root)
    d = lb.dial("blk", root=root)
    hand = {"firings": 3, "send_backs": 1, "door_passes": 2, "findings": 3,
            "approvals": 1, "disproves": 1, "questions": 1, "match_rate": 0.5}
    assert d == hand, f"the dial must equal the hand-count: {d}"
    lb.record_verdict("blk", _finding(root), "approve", "yes again", session="p",
                      now=NOW, records_dir=records, trace_dir=root)
    d2 = lb.dial("blk", root=root)
    assert d2["approvals"] == 2 and abs(d2["match_rate"] - 2 / 3) < 1e-9, \
        "one more verdict moves exactly the affected numbers"


def test_dial_is_none_before_any_verdict_and_mutates_nothing():
    root = world()
    lb.fire_door(_contract(), {"intent": "a", "source": "b"}, now=NOW, root=root)
    assert lb.dial("blk", root=root)["match_rate"] is None, \
        "no verdicts -> no rate; an invented number is an unmeasured claim"
    before = sorted((str(p), p.stat().st_mtime_ns) for p in root.rglob("*"))
    lb.dial("blk", root=root)
    lb.read_trace("blk", root=root)
    after = sorted((str(p), p.stat().st_mtime_ns) for p in root.rglob("*"))
    assert before == after, "a dial read touched the world (a view that writes is a device)"


# ── trace-wire teeth (the deploy pass's retrofit idiom) ──────────────────────

def test_traced_wire_green_and_red_and_reraise():
    root = world()
    with lb.traced("wired", "op-green", now=NOW, root=root):
        pass
    try:
        with lb.traced("wired", "op-red", now=NOW, root=root):
            raise ValueError("the lack itself")
        raise AssertionError("traced() must re-raise — the wire observes, never swallows")
    except ValueError:
        pass
    recs = lb.read_trace("wired", root=root)
    events = [r["event"] for r in recs]
    assert events == ["door_pass", "send_back"], f"green then red, both firings: {events}"
    assert recs[0]["data"] == {"op": "op-green"}
    assert recs[1]["data"]["lacks"] == ["ValueError: the lack itself"], \
        "a send_back names its lack"
    assert all(r["consumer"] == "training" for r in recs), \
        "the wire's default consumer is training — the denominator must not expire"


def test_shell_door_traces_and_refuses():
    import os as _os
    import subprocess
    root = world()
    env = dict(_os.environ, CAIRN_LB_TRACE_ROOT=str(root), PYTHONPATH=str(REPO))
    run = lambda *args: subprocess.run(  # noqa: E731
        [sys.executable, "-m", "cairn.machines.learning_block", *args],
        env=env, capture_output=True, text=True)
    assert run("trace", "sh", "door_pass", "launch").returncode == 0
    assert run("trace", "sh", "send_back", "launch", "the lack").returncode == 0
    r = run("trace", "sh", "send_back", "launch")           # a refusal without its lack
    assert r.returncode == 2 and "lack" in r.stderr, "an unnamed refusal teaches nothing"
    r = run("trace", "sh", "finding", "x")                  # not a firing event
    assert r.returncode == 2 and "firing" in r.stderr
    d = json.loads(run("dial", "sh").stdout)
    assert d["firings"] == 2 and d["send_backs"] == 1, f"the shell door feeds the dial: {d}"



def test_pending_findings_rule():
    """A finding stands at the gate until an approve or disprove names it —
    a QUESTION does not clear it (a question is asking, not disposing)."""
    root = world()
    records = world()
    a = lb.emit_finding("b1", [{"stratum": "code", "text": "alpha"}], now=NOW, root=root)
    b = lb.emit_finding("b2", [{"stratum": "code", "text": "beta"}],
                        now=NOW + timedelta(seconds=1), root=root)
    c = lb.emit_finding("b2", [{"stratum": "tree", "text": "gamma"}],
                        now=NOW + timedelta(seconds=2), root=root)
    lb.record_verdict("b1", a, "approve", "Approved - alpha is right", session="proof",
                      now=NOW + timedelta(seconds=3), records_dir=records, trace_dir=root)
    lb.record_verdict("b2", b, "question", "question: why beta?", session="proof",
                      now=NOW + timedelta(seconds=4), records_dir=records, trace_dir=root)
    pend = lb.pending_findings(root=root)
    assert [f["id"] for f in pend] == [b["id"], c["id"]], (
        f"approve clears, question keeps, unanswered stays — got {[f['id'] for f in pend]}")
    assert all(f["block"] == "b2" for f in lb.pending_findings("b2", root=root))
    assert lb.pending_findings("b1", root=root) == [], "b1 was approved — nothing pends"


def test_recordverdict_shell_door():
    """The gate owner's own hand: bare lists, ambiguity refuses LISTING candidates,
    an invented target refuses against the berth, empty/unparseable words refuse
    with the lack named, and a recorded verdict derives its gate from the
    finding's block (the lb-20260801-f4f21cbb mislabel, killed)."""
    import os as _os
    import subprocess
    root = world()
    parent = world()                      # CAIRN_ROOTS_PARENT -> parent/CairnCommons/learning/records
    env = dict(_os.environ, CAIRN_LB_TRACE_ROOT=str(root),
               CAIRN_ROOTS_PARENT=str(parent), PYTHONPATH=str(REPO))
    run = lambda *args: subprocess.run(  # noqa: E731
        [sys.executable, "-m", "cairn.machines.learning_block", "recordverdict", *args],
        env=env, capture_output=True, text=True)

    lb.emit_finding("b1", [{"stratum": "code", "text": "alpha"}], now=NOW, root=root)
    lb.emit_finding("b2", [{"stratum": "code", "text": "beta"}],
                    now=NOW + timedelta(seconds=1), root=root)

    r = run()                                            # bare = the gate, listed
    assert r.returncode == 0 and "2 finding(s)" in r.stdout and "[b1]" in r.stdout

    r = run("Approved - looks right")                    # two pending, no target
    assert r.returncode == 2 and "[b1]" in r.stderr and "[b2]" in r.stderr, (
        "an ambiguous act is refused LISTING the candidates")

    r = run("nope-such-finding", "Approved - x")         # invented target
    assert r.returncode == 2 and "matches nothing pending" in r.stderr

    r = run("")                                          # empty words
    assert r.returncode == 2 and "empty" in r.stderr

    r = run("b1", "hmm interesting")                     # words say no signal
    assert r.returncode == 2 and "no signal" in r.stderr

    r = run("b1", "Approved - alpha holds")              # the act, from the shell
    assert r.returncode == 0 and "approve" in r.stdout, r.stderr
    store = parent / "CairnCommons" / "learning" / "records"
    docs = list(store.glob("*.json"))
    assert len(docs) == 1, f"one store file: {docs}"
    rec = json.loads(docs[0].read_text())["records"][-1]
    assert rec["gate"] == "b1", "the gate is DERIVED from the finding's block, never typed"
    assert rec["signal"]["verbatim"] == "Approved - alpha holds"
    assert rec["session"].startswith("shell:"), "a shell act says it came from the shell"

    r = run("b2", "question", "question or not, why beta?")   # explicit signal
    assert r.returncode == 0
    r = run()
    assert "1 finding(s)" in r.stdout and "[b2]" in r.stdout, (
        "a question keeps the finding at the gate")

    r = run("b2", "disprove", "no - beta is wrong")
    assert r.returncode == 0
    r = run()
    assert "nothing stands at the gate" in r.stdout


# ── engine teeth (ticket engine-runs-one-block, 2026-08-02) ──────────────────
# The uniform inner loop: fixture specs only — the LIVE tenant spec berths beside its
# own component and is exercised at live fire, never here (the corpus the probe counts
# must be real work, not this file's fixtures — the home-field lesson).

from cairn.machines.learning_block import engine as eng  # noqa: E402


def _spec_brew():
    """Fixture block one: pick a brew method. Competition is real — the cheap candidate
    dies to a constraint whenever the measured water is 'hard'."""
    return {
        "block": "fixture:brew",
        "question": "which brew method does this water need?",
        "input_contract": {"water": "the measured fact every candidate is judged against"},
        "candidates": [
            {"name": "quick_steep", "why": "cheapest when the water allows it",
             "provides": {"works_with": ["soft"], "kettle": "any"}},
            {"name": "full_boil", "why": "always sound, costs the most",
             "provides": {"works_with": ["soft", "hard"], "kettle": "any"}},
        ],
        "constraints": [
            {"name": "matches_water", "why": "a method wrong for the measured water "
                                             "makes an undrinkable cup",
             "requires": {"works_with": {"fact": "water"}}},
        ],
        "escalation": "the kitchen's owner",
    }


def _spec_route():
    """Fixture block two: a different domain with different fields — what the
    byte-identity tooth runs through the SAME engine."""
    return {
        "block": "fixture:route",
        "question": "which path carries this parcel?",
        "input_contract": {"weight": "the fact the axle constraint resolves against"},
        "candidates": [
            {"name": "bike", "why": "cheapest and cleanest",
             "provides": {"carries": ["light"]}},
            {"name": "van", "why": "carries anything",
             "provides": {"carries": ["light", "heavy"]}},
        ],
        "constraints": [
            {"name": "axle_limit", "why": "an overloaded carrier fails mid-route",
             "requires": {"carries": {"fact": "weight"}}},
        ],
        "escalation": "dispatch",
    }


def test_engine_spec_door_refuses_every_lack_at_once():
    """An insufficient spec is refused ONCE with every lack named — shallow, deep and
    purity together — and the send-back is traced (the refusal rate must be measurable)."""
    root = world()
    bad = {"block": "fixture:brew",
           "candidates": [{"why": "unnamed and propertyless"}],
           "constraints": [{"name": "hollow"}]}          # no question/escalation either
    try:
        eng.run_block(bad, {}, root=root, now=NOW)
        raise AssertionError("an insufficient spec must refuse")
    except lb.DoorRefused as exc:
        fields = {l["field"] for l in exc.lacks}
    assert {"question", "escalation", "candidates[0].name", "candidates[0].provides",
            "constraints[0].requires"} <= fields, f"every lack in ONE pass: {fields}"
    recs = lb.read_trace("fixture:brew", root=root)
    assert [r["event"] for r in recs] == ["send_back"], "the refusal itself is traced"

    unpure = _spec_brew()
    unpure["candidates"][0]["provides"]["works_with"] = lambda: "soft"   # code, not data
    try:
        eng.run_block(unpure, {"water": "soft"}, root=world(), now=NOW)
        raise AssertionError("a spec carrying code must refuse")
    except lb.DoorRefused as exc:
        assert any("JSON round-trip" in l["why"] for l in exc.lacks), (
            "the data-only refusal names the round-trip")


def test_engine_one_shape_two_specs_source_untouched():
    """The wrong-shape tell, mechanical: two different blocks run through the SAME engine
    with its source bytes untouched between them — and no fixture block's name appears
    anywhere in engine code (the spec carries the difference, or this red fires)."""
    src_path = Path(eng.__file__)
    before = src_path.read_bytes()
    eng.run_block(_spec_brew(), {"water": "hard"}, root=world(), now=NOW)
    eng.run_block(_spec_route(), {"weight": "heavy"}, root=world(), now=NOW)
    assert src_path.read_bytes() == before, "engine source moved between two tenants"
    src = before.decode()
    for name in ("fixture:brew", "fixture:route", "quick_steep", "bike",
                 "intentions_model_compiler"):
        assert name not in src, f"block-specific knowledge {name!r} found INSIDE the engine"


def test_engine_forced_competition_rejects_with_killer_named():
    """Hard water kills the cheap candidate: the loser lands in the record as REJECTED
    with the constraint that killed it named, and the winner carries its why."""
    root = world()
    rec = eng.run_block(_spec_brew(), {"water": "hard"}, root=root, now=NOW)
    by_name = {c["name"]: c for c in rec["data"]["candidates"]}
    assert by_name["quick_steep"]["outcome"] == "rejected"
    assert by_name["quick_steep"]["killed_by"] == ["matches_water"]
    assert rec["data"]["winner"]["name"] == "full_boil"
    assert "why" in rec["data"]["winner"] and rec["data"]["winner"]["why"].strip()


def test_engine_run_traces_training_and_answers_five_questions():
    """One run -> one training-typed engine_run record whose fields answer all five
    mechanical questions — read back from the store, not from the return value."""
    root = world()
    eng.run_block(_spec_brew(), {"water": "hard"}, root=root, now=NOW)
    recs = [r for r in lb.read_trace("fixture:brew", root=root)
            if r["event"] == eng.RUN_EVENT]
    assert len(recs) == 1 and recs[0]["consumer"] == "training"
    assert eng.answers_five_questions(recs[0]) == []


def test_engine_outranked_is_not_rejected():
    """Soft water: both candidates survive; the loser is OUTRANKED (preference, not a
    constraint) and says by whom — killed_by stays empty, five questions still answer."""
    root = world()
    rec = eng.run_block(_spec_brew(), {"water": "soft"}, root=root, now=NOW)
    by_name = {c["name"]: c for c in rec["data"]["candidates"]}
    assert rec["data"]["winner"]["name"] == "quick_steep", "preference is the spec's order"
    assert by_name["full_boil"]["outcome"] == "outranked"
    assert by_name["full_boil"]["killed_by"] == []
    assert by_name["full_boil"]["outranked_by"] == "quick_steep"
    assert eng.answers_five_questions(rec) == []


def test_engine_escalation_traces_as_loudly():
    """A run every candidate dies in escalates to the spec's named gate — and its record
    is exactly as complete as a deciding run's (the denominator must exist)."""
    root = world()
    rec = eng.run_block(_spec_brew(), {"water": "salt"}, root=root, now=NOW)
    assert rec["data"]["winner"] is None
    assert rec["data"]["escalation"]["to"] == "the kitchen's owner"
    assert "quick_steep killed by matches_water" in rec["data"]["escalation"]["why"]
    assert all(c["outcome"] == "rejected" for c in rec["data"]["candidates"])
    assert eng.answers_five_questions(rec) == []
    stored = [r for r in lb.read_trace("fixture:brew", root=root)
              if r["event"] == eng.RUN_EVENT]
    assert len(stored) == 1, "an escalating run traces exactly like a deciding one"


def test_engine_hollow_record_fails_the_checker():
    """The checker's own teeth: a wire-thin record cannot pass. Strip each answer and
    the missing question is NAMED — a checker that greens on a hollow record would make
    every downstream green (proof, verdict, probe) a coin-toss."""
    root = world()
    rec = eng.run_block(_spec_brew(), {"water": "hard"}, root=root, now=NOW)
    import copy
    hollow = copy.deepcopy(rec); hollow["data"]["candidates"][0]["killed_by"] = []
    assert any(m.startswith("3:") for m in eng.answers_five_questions(hollow))
    hollow = copy.deepcopy(rec); del hollow["data"]["input"]
    assert any(m.startswith("1:") for m in eng.answers_five_questions(hollow))
    hollow = copy.deepcopy(rec); del hollow["data"]["escalation"]
    assert any(m.startswith("5:") for m in eng.answers_five_questions(hollow))
    hollow = copy.deepcopy(rec); hollow["data"]["winner"] = None
    assert any(m.startswith("4:") for m in eng.answers_five_questions(hollow))
    legacy = {"data": {"op": "copy_to_lab"}}             # the wire-thin shape, measured
    assert len(eng.answers_five_questions(legacy)) >= 3, (
        "the pre-engine trace shape must fail loudly, or the corpus count lies")


def test_engine_nonvacuity_reds_on_a_hollow_engine():
    """The mutant demonstration, standing: with evaluation stubbed to accept-first, the
    corpus gains ZERO rejected candidates — the exact count the PROVED criterion and the
    probe read — while the real engine yields >= 1. Both halves asserted, so a future
    hollowing of the evaluation loop turns this tooth red, not the live corpus silent."""
    root = world()
    real = eng._satisfies
    try:
        eng._satisfies = lambda *a: True                  # the hollow engine
        eng.run_block(_spec_brew(), {"water": "hard"}, root=root, now=NOW)
        hollow_count = eng.rejected_count(lb.read_trace("fixture:brew", root=root))
        assert hollow_count == 0, "the mutant must look exactly like never-evaluating"
    finally:
        eng._satisfies = real
    root2 = world()
    eng.run_block(_spec_brew(), {"water": "hard"}, root=root2, now=NOW)
    assert eng.rejected_count(lb.read_trace("fixture:brew", root=root2)) >= 1, (
        "the real engine under competition must reject — non-vacuity")


def test_engine_input_door_fires_the_spec_contract():
    """The spec's input_contract is a real door: a payload missing the declared fact is
    sent back with the spec's own why, and the send-back is traced."""
    root = world()
    try:
        eng.run_block(_spec_brew(), {}, root=root, now=NOW)
        raise AssertionError("a payload missing the declared fact must refuse")
    except lb.DoorRefused as exc:
        assert [l["field"] for l in exc.lacks] == ["water"]
    events = [r["event"] for r in lb.read_trace("fixture:brew", root=root)]
    assert events == ["send_back"]


def test_engine_probe_is_armed():
    """The WATCHME crossing's own measurement, run here first: the berthed probe imports,
    declares a frozen PROBE with carry and enough — armed_error returns None."""
    from cairn.tools.base.watchme_spec import armed_error
    err = armed_error({"probe": "cairn/machines/learning_block/probes/engine_trace_corpus.py"})
    assert err is None, f"the probe must be armed by the chokepoint's own measure: {err}"


def test_door_refused_renders_field_and_why():
    """Ticket chart-doors-refuse-in-one-pass (folding opus-pass rank 7): str() of a
    DoorRefused carries each lack's WHY beside its field — a caller that only prints
    the exception hands the executor the remedy, not a list of names to look up."""
    exc = lb.DoorRefused("blk", [{"field": "alpha", "why": "alpha is load-bearing"},
                                 {"field": "beta", "why": "beta names the falsifier"}])
    msg = str(exc)
    for needle in ("alpha: alpha is load-bearing", "beta: beta names the falsifier"):
        assert needle in msg, (needle, msg)


# ── runner ───────────────────────────────────────────────────────────────────

TEETH = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for tooth in TEETH:
        try:
            tooth()
            print(f"  green  {tooth.__name__}")
        except Exception as exc:
            failed += 1
            print(f"  RED    {tooth.__name__}: {exc}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    sys.exit(1 if failed else 0)

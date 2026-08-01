"""Proof for cairn/learning_block — teeth a hollow block could not pass.

Runs against injected roots (CAIRN_LB_TRACE_ROOT never set here — every call
passes root=/records_dir= explicitly into a temp world); the live trace berth
and the real learning store are never read or written. NON-VACUITY is
structural: green paths are asserted before each refusal tooth, so a gate that
refuses everything fails the first half and one that passes everything fails
the second.

    python3 cairn/learning_block/proofs/test_learning_block.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from cairn.learning_block import learning_block as lb  # noqa: E402

NOW = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)


def world():
    return Path(tempfile.mkdtemp(prefix="lb-proof-"))


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
    src = (REPO / "cairn" / "learning_block" / "learning_block.py").read_text()
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
    src = (REPO / "cairn" / "learning_block" / "learning_block.py").read_text()
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
        [sys.executable, "-m", "cairn.learning_block", *args],
        env=env, capture_output=True, text=True)
    assert run("trace", "sh", "door_pass", "launch").returncode == 0
    assert run("trace", "sh", "send_back", "launch", "the lack").returncode == 0
    r = run("trace", "sh", "send_back", "launch")           # a refusal without its lack
    assert r.returncode == 2 and "lack" in r.stderr, "an unnamed refusal teaches nothing"
    r = run("trace", "sh", "finding", "x")                  # not a firing event
    assert r.returncode == 2 and "firing" in r.stderr
    d = json.loads(run("dial", "sh").stdout)
    assert d["firings"] == 2 and d["send_backs"] == 1, f"the shell door feeds the dial: {d}"


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

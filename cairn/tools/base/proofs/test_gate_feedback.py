"""Proof — TransitionGate feedback collection and parameter adjustment.

Criterion 2: TransitionGate.run() produces a structured feedback record on both
green and red paths, and the record carries sieve input, output, and verdict.

Criterion 3: TransitionGate.adjust() validates proposals, writes to the
instance-space sieve tree, and rejects malformed input.

Ticket: scheduled-llm-gate-inspection (b0c0c47835c1).
"""
import json
import os
import shutil
import sys
import tempfile

from cairn.tools.gate import gate
from cairn.tools.base.gate_class import TransitionGate


class GateTestException(Exception):
    def __init__(self, msg, findings=None):
        super().__init__(msg)
        self.findings = findings or []


def _make_gate(tmp):
    g = TransitionGate("test_gate", exception_class=GateTestException)
    seeds_dir = os.path.join(tmp, "seeds")
    os.makedirs(seeds_dir)
    for name in ("alpha", "beta"):
        with open(os.path.join(seeds_dir, "%s.json" % name), "w") as f:
            json.dump({"name": name, "band": 1, "band_name": "record", "dials": {}}, f)
    instance_root = os.path.join(tmp, "instance")
    os.makedirs(instance_root, exist_ok=True)
    g.construct(seeds_dir, instance_root)
    return g


def _green_record():
    return [
        gate.proved(identity="check_a", expected=1.0, actual=1.0,
                    location="test", code="T1", source="proof"),
        gate.proved(identity="check_b", expected=1.0, actual=1.0,
                    location="test", code="T2", source="proof"),
    ]


def _red_record():
    return [
        gate.proved(identity="check_a", expected=1.0, actual=1.0,
                    location="test", code="T1", source="proof"),
        gate.proved(identity="check_fail", expected=1.0, actual=0.0,
                    location="test", code="T2", source="proof"),
    ]


def test_green_produces_feedback():
    with tempfile.TemporaryDirectory() as tmp:
        g = _make_gate(tmp)
        note, record = g.run(_green_record())
        fb_dir = g._feedback_dir
        assert fb_dir is not None, "feedback dir not set"
        assert fb_dir.is_dir(), "feedback dir not created"
        files = list(fb_dir.glob("*.json"))
        assert len(files) == 1, "expected 1 feedback file, got %d" % len(files)
        fb = json.loads(files[0].read_text())
        assert fb["gate"] == "test_gate"
        assert fb["verdict"] == "green"
        assert fb["checks_total"] == 2
        assert fb["checks_passed"] == 2
        assert fb["checks_failed"] == 0
        assert isinstance(fb["record"], list)
        assert len(fb["record"]) == 2
        assert "mismatches" not in fb
        print("  [a] green path produces feedback record .......... OK")


def test_red_produces_feedback():
    with tempfile.TemporaryDirectory() as tmp:
        g = _make_gate(tmp)
        try:
            g.run(_red_record())
            assert False, "expected GateTestException"
        except GateTestException:
            pass
        fb_dir = g._feedback_dir
        files = list(fb_dir.glob("*.json"))
        assert len(files) == 1, "expected 1 feedback file, got %d" % len(files)
        fb = json.loads(files[0].read_text())
        assert fb["gate"] == "test_gate"
        assert fb["verdict"] == "red"
        assert fb["checks_total"] == 2
        assert fb["checks_passed"] == 1
        assert fb["checks_failed"] == 1
        assert isinstance(fb["record"], list)
        assert isinstance(fb["mismatches"], list)
        assert len(fb["mismatches"]) == 1
        assert fb["mismatches"][0]["identity"] == "check_fail"
        print("  [b] red path produces feedback record ............ OK")


def test_feedback_carries_sieve_data():
    with tempfile.TemporaryDirectory() as tmp:
        g = _make_gate(tmp)
        g.run(_green_record())
        fb_dir = g._feedback_dir
        fb = json.loads(list(fb_dir.glob("*.json"))[0].read_text())
        for entry in fb["record"]:
            assert "identity" in entry, "record entry missing identity"
            assert "expected" in entry, "record entry missing expected"
            assert "actual" in entry, "record entry missing actual"
        print("  [c] feedback record carries sieve input/output ... OK")


def test_no_feedback_without_construct():
    g = TransitionGate("bare_gate", exception_class=GateTestException)
    note, record = g.run(_green_record())
    assert g._feedback_dir is None
    print("  [d] no feedback without construct ................. OK")


def test_adjust_valid_proposal():
    with tempfile.TemporaryDirectory() as tmp:
        g = _make_gate(tmp)
        result = g.adjust("alpha", "threshold", 0.8)
        assert result["sieve"] == "alpha"
        assert result["dial"] == "threshold"
        assert result["prior"] is None
        assert result["new"] == 0.8
        data = json.loads((g._tree / "alpha.json").read_text())
        assert data["dials"]["threshold"] == 0.8
        print("  [e] adjust() writes valid proposal to tree ....... OK")


def test_adjust_revert():
    with tempfile.TemporaryDirectory() as tmp:
        g = _make_gate(tmp)
        g.adjust("alpha", "threshold", 0.8)
        result = g.adjust("alpha", "threshold", 0.5)
        assert result["prior"] == 0.8
        assert result["new"] == 0.5
        data = json.loads((g._tree / "alpha.json").read_text())
        assert data["dials"]["threshold"] == 0.5
        print("  [f] adjust() returns prior for revert ............ OK")


def test_adjust_rejects_missing_sieve():
    with tempfile.TemporaryDirectory() as tmp:
        g = _make_gate(tmp)
        try:
            g.adjust("nonexistent", "threshold", 0.8)
            assert False, "expected ValueError"
        except ValueError as e:
            assert "nonexistent" in str(e)
        print("  [g] adjust() rejects missing sieve .............. OK")


def test_adjust_rejects_empty_dial():
    with tempfile.TemporaryDirectory() as tmp:
        g = _make_gate(tmp)
        try:
            g.adjust("alpha", "", 0.8)
            assert False, "expected ValueError"
        except ValueError as e:
            assert "non-empty" in str(e)
        print("  [h] adjust() rejects empty dial .................. OK")


def test_adjust_rejects_no_tree():
    g = TransitionGate("bare", exception_class=GateTestException)
    try:
        g.adjust("alpha", "threshold", 0.8)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "construct" in str(e)
    print("  [i] adjust() rejects call without construct ....... OK")


def test_adjust_rejects_unserializable():
    with tempfile.TemporaryDirectory() as tmp:
        g = _make_gate(tmp)
        try:
            g.adjust("alpha", "threshold", object())
            assert False, "expected ValueError"
        except ValueError as e:
            assert "serializable" in str(e)
        print("  [j] adjust() rejects unserializable value ........ OK")


if __name__ == "__main__":
    print("test_gate_feedback — scheduled-llm-gate-inspection")
    test_green_produces_feedback()
    test_red_produces_feedback()
    test_feedback_carries_sieve_data()
    test_no_feedback_without_construct()
    test_adjust_valid_proposal()
    test_adjust_revert()
    test_adjust_rejects_missing_sieve()
    test_adjust_rejects_empty_dial()
    test_adjust_rejects_no_tree()
    test_adjust_rejects_unserializable()
    print("all 10 teeth pass")

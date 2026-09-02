"""Proof — scheduled LLM inspection probe.

Criterion 4: the scheduled inspection probe fires an LLM prompt to Hex with
accumulated feedback and routes the adjustment proposal through adjust().

Uses a mock resolver — no live inference call.
Ticket: scheduled-llm-gate-inspection (b0c0c47835c1).
"""
import json
import os
import tempfile

from cairn.tools.gate import gate
from cairn.tools.base.gate_class import TransitionGate
from cairn.tools.base.probes.gate_parameters_adjust_from_feedback import (
    PROBE, build_prompt, parse_proposals, inspect, _read_feedback,
)


class _TestException(Exception):
    def __init__(self, msg, findings=None):
        super().__init__(msg)
        self.findings = findings or []


def _setup_gate_with_feedback(tmp, n_records=5):
    from cairn.tools.base import transitions
    g = transitions.BUILD_GATE

    seeds_dir = os.path.join(tmp, "seeds")
    os.makedirs(seeds_dir, exist_ok=True)
    for name in ("alpha", "beta", "gamma"):
        with open(os.path.join(seeds_dir, "%s.json" % name), "w") as f:
            json.dump({"name": name, "band": 1, "band_name": "record", "dials": {}}, f)

    instance_root = os.path.join(tmp, "instance")
    os.makedirs(instance_root, exist_ok=True)
    old_tree = g._tree
    old_exc = g.exception_class
    g.exception_class = _TestException
    g.construct(seeds_dir, instance_root)

    record = [
        gate.proved(identity="check_a", expected=1.0, actual=1.0,
                    location="test", code="T1", source="proof"),
    ]
    for _ in range(n_records):
        g.run(record)

    return g, old_tree, old_exc


def _restore_gate(g, old_tree, old_exc):
    g._tree = old_tree
    g.exception_class = old_exc


def test_probe_declares_correctly():
    assert PROBE.trigger is not None
    assert PROBE.carry is not None
    assert PROBE.enough is not None
    assert PROBE.horizon == 500
    assert PROBE.to == "harbor_master"
    print("  [a] probe declares trigger/carry/enough/horizon ... OK")


def test_prompt_shape():
    records = [
        {"gate": "build_gate", "verdict": "green", "checks_total": 3,
         "checks_passed": 3, "checks_failed": 0, "record": []},
    ]
    prompt = build_prompt(records, {"alpha": {"threshold": 0.5}})
    assert "gate inspection feedback" in prompt
    assert "alpha" in prompt
    assert "threshold" in prompt
    assert "0.5" in prompt
    assert '"sieve"' in prompt
    print("  [b] prompt carries feedback + current dials ....... OK")


def test_parse_valid_proposals():
    response = json.dumps([
        {"sieve": "alpha", "dial": "threshold", "value": 0.7, "reason": "test"},
    ])
    proposals = parse_proposals(response)
    assert len(proposals) == 1
    assert proposals[0]["sieve"] == "alpha"
    assert proposals[0]["dial"] == "threshold"
    assert proposals[0]["value"] == 0.7
    print("  [c] parse_proposals extracts valid proposals ...... OK")


def test_parse_empty_response():
    assert parse_proposals("[]") == []
    assert parse_proposals("no json here") == []
    assert parse_proposals('{"not": "array"}') == []
    print("  [d] parse_proposals handles empty/bad responses ... OK")


def test_inspect_calls_resolver_and_adjust():
    with tempfile.TemporaryDirectory() as tmp:
        g, old_tree, old_exc = _setup_gate_with_feedback(tmp, n_records=5)
        try:
            calls = []

            def mock_resolver(prompt):
                calls.append(prompt)
                return json.dumps([
                    {"sieve": "alpha", "dial": "threshold", "value": 0.9,
                     "reason": "test adjustment"},
                ])

            records = _read_feedback()
            assert len(records) == 5, "expected 5 feedback records, got %d" % len(records)

            result = inspect(records, mock_resolver)

            assert len(calls) == 1, "resolver called %d times" % len(calls)
            assert "gate inspection feedback" in calls[0]

            assert len(result["proposals"]) == 1
            assert result["proposals"][0]["sieve"] == "alpha"
            assert result["adjustments"][0]["sieve"] == "alpha"
            assert result["adjustments"][0]["new"] == 0.9

            data = json.loads((g._tree / "alpha.json").read_text())
            assert data["dials"]["threshold"] == 0.9
            print("  [e] inspect() calls resolver and routes adjust .. OK")
        finally:
            _restore_gate(g, old_tree, old_exc)


def test_inspect_rejects_bad_proposal():
    with tempfile.TemporaryDirectory() as tmp:
        g, old_tree, old_exc = _setup_gate_with_feedback(tmp, n_records=5)
        try:
            def mock_resolver(prompt):
                return json.dumps([
                    {"sieve": "nonexistent", "dial": "x", "value": 1},
                ])

            records = _read_feedback()
            result = inspect(records, mock_resolver)
            assert "error" in result["adjustments"][0]
            print("  [f] inspect() reports bad proposals as errors .... OK")
        finally:
            _restore_gate(g, old_tree, old_exc)


def test_trigger_fires_on_threshold():
    with tempfile.TemporaryDirectory() as tmp:
        g, old_tree, old_exc = _setup_gate_with_feedback(tmp, n_records=5)
        try:
            import time
            assert PROBE.trigger(time.time(), {}) is True
            print("  [g] trigger fires at threshold ................... OK")
        finally:
            _restore_gate(g, old_tree, old_exc)


def test_carry_without_resolver():
    with tempfile.TemporaryDirectory() as tmp:
        g, old_tree, old_exc = _setup_gate_with_feedback(tmp, n_records=5)
        try:
            result = PROBE.carry({})
            assert "error" in result
            assert "resolver" in result["error"]
            print("  [h] carry without resolver reports the lack ..... OK")
        finally:
            _restore_gate(g, old_tree, old_exc)


if __name__ == "__main__":
    print("test_llm_inspection_probe — scheduled-llm-gate-inspection")
    test_probe_declares_correctly()
    test_prompt_shape()
    test_parse_valid_proposals()
    test_parse_empty_response()
    test_inspect_calls_resolver_and_adjust()
    test_inspect_rejects_bad_proposal()
    test_trigger_fires_on_threshold()
    test_carry_without_resolver()
    print("all 8 teeth pass")

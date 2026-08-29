"""Proofs for the CC learning store — teeth a hollow build could not pass.

Falsifier: a real feedback-record is captured, points at a specific gate, and
is surfaced when a like decision recurs later (the read half).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def store_dir():
    d = tempfile.mkdtemp(prefix="cairn-cc-learning-test-")
    yield Path(d)
    shutil.rmtree(d)


def test_write_record_creates_a_file_at_the_store_path(store_dir):
    from cairn.devices.cc.learning import write_record

    rec = write_record(
        gate="test-gate",
        decision="chose option A",
        signal="confirmation",
        verbatim="yes",
        root=store_dir,
    )
    assert rec["gate"] == "test-gate"
    assert rec["decision"] == "chose option A"
    assert rec["evidence"] == "confirmation"
    files = list(store_dir.glob("cc-*.json"))
    assert len(files) == 1


def test_read_records_retrieves_what_was_written(store_dir):
    from cairn.devices.cc.learning import read_records, write_record

    write_record(
        gate="build-now-vs-defer",
        decision="built immediately",
        signal="confirmation",
        verbatim="good call",
        root=store_dir,
    )
    found = read_records(gate="build-now-vs-defer", root=store_dir)
    assert len(found) == 1
    assert found[0]["gate"] == "build-now-vs-defer"
    assert found[0]["signal"]["verbatim"] == "good call"


def test_read_records_filters_by_gate(store_dir):
    from cairn.devices.cc.learning import read_records, write_record

    write_record(gate="gate-a", decision="d1", signal="confirmation", verbatim="ok", root=store_dir)
    write_record(gate="gate-b", decision="d2", signal="correction", verbatim="no", root=store_dir)
    assert len(read_records(gate="gate-a", root=store_dir)) == 1
    assert len(read_records(gate="gate-b", root=store_dir)) == 1
    assert len(read_records(root=store_dir)) == 2


def test_write_refuses_invalid_signal(store_dir):
    from cairn.devices.cc.learning import write_record

    with pytest.raises(ValueError, match="signal"):
        write_record(gate="g", decision="d", signal="invalid", verbatim="x", root=store_dir)


def test_write_refuses_empty_gate(store_dir):
    from cairn.devices.cc.learning import write_record

    with pytest.raises(ValueError, match="gate"):
        write_record(gate="", decision="d", signal="confirmation", verbatim="x", root=store_dir)


def test_record_has_v0_required_fields(store_dir):
    from cairn.devices.cc.learning import write_record

    rec = write_record(
        gate="repo-visibility",
        decision="kept private",
        signal="confirmation",
        verbatim="correct",
        root=store_dir,
    )
    for field in ("id", "date", "gate", "decision", "signal", "evidence",
                  "ceiling", "confidence_move", "provenance"):
        assert field in rec, f"missing v0 field: {field}"


def test_read_records_returns_empty_for_missing_dir():
    from cairn.devices.cc.learning import read_records

    found = read_records(gate="anything", root="/tmp/nonexistent-cc-learning-test-dir")
    assert found == []

"""Proofs for the watcher face — codemother/watch.py.

Tests the core activation logic, file-to-area mapping, and the
escalation path. Does NOT test live inference (that would need the
embed host up) — tests the shapes and plumbing.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cairn.devices.codemother.watch import (
    _files_to_areas,
    _extract_findings,
    _log_activation,
    activate,
    on_commit,
    on_question,
)


class TestFilesToAreas:

    def test_device_path(self):
        areas = _files_to_areas(["cairn/devices/codemother/watch.py"])
        assert "cairn/devices/codemother" in areas

    def test_machine_path(self):
        areas = _files_to_areas(["cairn/machines/build_inspector/inspector.py"])
        assert "cairn/machines/build_inspector" in areas

    def test_tool_path(self):
        areas = _files_to_areas(["cairn/tools/base/transitions.py"])
        assert "cairn/tools/base" in areas

    def test_skill_path(self):
        areas = _files_to_areas(["skills/chart/live.py"])
        assert "skills/chart" in areas

    def test_multiple_files_same_area(self):
        areas = _files_to_areas([
            "cairn/devices/codemother/watch.py",
            "cairn/devices/codemother/shim.py",
        ])
        assert areas == ["cairn/devices/codemother"]

    def test_multiple_areas(self):
        areas = _files_to_areas([
            "cairn/devices/codemother/watch.py",
            "cairn/tools/base/transitions.py",
        ])
        assert len(areas) == 2

    def test_empty_files(self):
        areas = _files_to_areas([])
        assert areas == []

    def test_unknown_path_falls_back_to_parent(self):
        areas = _files_to_areas(["some/other/file.py"])
        assert len(areas) == 1


class TestExtractFindings:

    def test_dict_with_content(self):
        hits = [{"content": "found something", "similarity": 0.9}]
        findings = _extract_findings(hits, source="tree")
        assert len(findings) == 1
        assert findings[0]["content"] == "found something"
        assert findings[0]["source"] == "tree"
        assert findings[0]["relevance"] == 0.9

    def test_dict_with_text(self):
        hits = [{"text": "found via text key"}]
        findings = _extract_findings(hits, source="hex")
        assert findings[0]["content"] == "found via text key"

    def test_string_hit(self):
        findings = _extract_findings(["plain string"], source="tree")
        assert findings[0]["content"] == "plain string"

    def test_empty_hits(self):
        assert _extract_findings([], source="tree") == []


class TestLogActivation:

    def test_writes_to_instance_space(self):
        with tempfile.TemporaryDirectory() as td:
            with patch("cairn.devices.codemother.watch._ACTIVATIONS_DIR", Path(td)):
                _log_activation({
                    "timestamp": "2026-09-03T00:00:00+00:00",
                    "area": "test/area",
                    "reason": "test",
                })
                files = list(Path(td).glob("activation-*.json"))
                assert len(files) == 1
                data = json.loads(files[0].read_text())
                assert data["area"] == "test/area"


class TestActivate:

    def test_returns_structure_on_embed_failure(self):
        with patch("cairn.devices.codemother.watch._embed", side_effect=RuntimeError("no host")):
            with tempfile.TemporaryDirectory() as td:
                with patch("cairn.devices.codemother.watch._ACTIVATIONS_DIR", Path(td)):
                    result = activate("test/area", "testing")
                    assert result["findings"] == []
                    assert result["escalated"] is False
                    assert "error" in result

    def test_escalates_when_no_tree_hits(self):
        mock_embed = MagicMock(return_value=[0.1] * 384)
        with patch("cairn.devices.codemother.watch._embed", mock_embed):
            with patch("cairn.devices.codemother.watch._escalate_to_hex") as mock_hex:
                mock_hex.return_value = {"nodes": []}
                with patch("cairn.tools.tree.tree.counsel", return_value=[]):
                    with tempfile.TemporaryDirectory() as td:
                        with patch("cairn.devices.codemother.watch._ACTIVATIONS_DIR", Path(td)):
                            result = activate("test/area", "testing")
                            assert result["escalated"] is True
                            mock_hex.assert_called_once()


class TestOnCommit:

    def test_returns_structure(self):
        with patch("cairn.devices.codemother.watch.activate") as mock_activate:
            mock_activate.return_value = {"findings": [], "escalated": False, "tree_hits": 0}
            result = on_commit("abc123", ["cairn/devices/codemother/watch.py"], "test commit")
            assert result["commit"] == "abc123"
            assert result["areas_checked"] >= 1


class TestOnQuestion:

    def test_delegates_to_activate(self):
        with patch("cairn.devices.codemother.watch.activate") as mock_activate:
            mock_activate.return_value = {"findings": [], "escalated": False, "tree_hits": 0}
            on_question("what patterns exist in the bus?", area="cairn/devices/cairn/machines/bus")
            mock_activate.assert_called_once()
            call_args = mock_activate.call_args
            assert call_args[0][0] == "cairn/devices/cairn/machines/bus"

"""Proofs for the-axis-is-named-and-ruled: runtime_role on the complexity axis.

Ticket: the-axis-is-named-and-ruled
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
CAIRN_ROOT = REPO_ROOT / "cairn"

VALID_ROLES = {"tool", "machine", "device"}

RUNG_SEGMENTS = {
    "tools": "tool",
    "machines": "machine",
    "devices": "device",
}


def _all_charters():
    """Return (path, charter_dict) for every intention+why.json."""
    charters = []
    for root, dirs, files in os.walk(str(CAIRN_ROOT)):
        if "intention+why.json" in files and "__pycache__" not in root:
            p = Path(root) / "intention+why.json"
            with open(p) as f:
                charters.append((p, json.load(f)))
    return charters


def _derive_rung(charter_path: Path) -> str:
    """Derive the expected rung from directory structure."""
    parts = charter_path.relative_to(CAIRN_ROOT).parts
    for segment, role in RUNG_SEGMENTS.items():
        if segment in parts:
            if segment == "devices" and "machines" in parts:
                return "machine"
            return role
    return "unknown"


class TestRuntimeRoleOnCharters:

    @pytest.fixture
    def charters(self):
        return _all_charters()

    def test_at_least_40_charters(self, charters):
        assert len(charters) >= 40, f"expected >= 40 charters, got {len(charters)}"

    def test_every_charter_has_runtime_role(self, charters):
        missing = []
        for path, d in charters:
            if "runtime_role" not in d:
                missing.append(str(path.relative_to(REPO_ROOT)))
        assert not missing, f"charters missing runtime_role: {missing}"

    def test_runtime_role_is_valid(self, charters):
        invalid = []
        for path, d in charters:
            role = d.get("runtime_role", "")
            if role not in VALID_ROLES:
                invalid.append((str(path.relative_to(REPO_ROOT)), role))
        assert not invalid, f"charters with invalid runtime_role: {invalid}"

    def test_runtime_role_matches_directory_rung(self, charters):
        mismatched = []
        for path, d in charters:
            expected = _derive_rung(path)
            actual = d.get("runtime_role", "")
            if expected != "unknown" and actual != expected:
                mismatched.append((str(path.relative_to(REPO_ROOT)), actual, expected))
        assert not mismatched, f"runtime_role mismatches: {mismatched}"


class TestInspectorSieve:

    def test_sieve_fires_on_missing_role(self, tmp_path):
        charter = {"component": "test_comp", "what": "test"}
        (tmp_path / "intention+why.json").write_text(json.dumps(charter))
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.machines.build_inspector.inspector import runtime_role_declared
        row = {"component": "test_comp", "dir": "test/test_comp"}
        findings = runtime_role_declared(row, tmp_path)
        assert len(findings) == 1, "sieve should fire on missing runtime_role"
        assert findings[0]["method"] == "runtime_role_declared"

    def test_sieve_clean_on_present_role(self, tmp_path):
        charter = {"component": "test_comp", "runtime_role": "tool", "what": "test"}
        (tmp_path / "intention+why.json").write_text(json.dumps(charter))
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.machines.build_inspector.inspector import runtime_role_declared
        row = {"component": "test_comp", "dir": "test/test_comp"}
        findings = runtime_role_declared(row, tmp_path)
        assert findings == [], "sieve should not fire when runtime_role is present"

    def test_sieve_fires_on_invalid_role(self, tmp_path):
        charter = {"component": "test_comp", "runtime_role": "bogus", "what": "test"}
        (tmp_path / "intention+why.json").write_text(json.dumps(charter))
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.machines.build_inspector.inspector import runtime_role_declared
        row = {"component": "test_comp", "dir": "test/test_comp"}
        findings = runtime_role_declared(row, tmp_path)
        assert len(findings) == 1, "sieve should fire on invalid runtime_role"


class TestCensusCarriesRole:

    def test_census_rows_have_runtime_role(self):
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.tools.orient.orient import device_census
        census = device_census(root=CAIRN_ROOT)
        rows = census["measured"]["components"]
        missing = [
            r["component"] for r in rows
            if not r.get("runtime_role") and r.get("charter_on_disk")
        ]
        assert not missing, f"census rows with charter but missing runtime_role: {missing}"

    def test_census_runtime_role_matches_charter(self):
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.tools.orient.orient import device_census
        census = device_census(root=CAIRN_ROOT)
        rows = census["measured"]["components"]
        mismatched = []
        for r in rows:
            charter_path = CAIRN_ROOT / r["dir"] / "intention+why.json"
            if charter_path.is_file():
                charter = json.loads(charter_path.read_text())
                if r.get("runtime_role") != charter.get("runtime_role"):
                    mismatched.append((r["component"], r.get("runtime_role"), charter.get("runtime_role")))
        assert not mismatched, f"census/charter runtime_role mismatches: {mismatched}"


class TestGatedByDeclaredSieve:

    def test_sieve_fires_on_missing_gated_by(self, tmp_path):
        charter = {"component": "test_comp", "runtime_role": "tool", "what": "test"}
        (tmp_path / "intention+why.json").write_text(json.dumps(charter))
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.machines.build_inspector.inspector import gated_by_declared
        row = {"component": "test_comp", "dir": "test/test_comp"}
        findings = gated_by_declared(row, tmp_path)
        assert len(findings) == 1, "sieve should fire on missing gated_by"
        assert findings[0]["method"] == "gated_by_declared"

    def test_sieve_clean_on_present_gated_by(self, tmp_path):
        charter = {"component": "test_comp", "runtime_role": "tool",
                    "gated_by": ["CC"], "what": "test"}
        (tmp_path / "intention+why.json").write_text(json.dumps(charter))
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.machines.build_inspector.inspector import gated_by_declared
        row = {"component": "test_comp", "dir": "test/test_comp"}
        findings = gated_by_declared(row, tmp_path)
        assert findings == [], "sieve should not fire when gated_by is present"

    def test_sieve_fires_on_empty_gated_by(self, tmp_path):
        charter = {"component": "test_comp", "runtime_role": "tool",
                    "gated_by": [], "what": "test"}
        (tmp_path / "intention+why.json").write_text(json.dumps(charter))
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.machines.build_inspector.inspector import gated_by_declared
        row = {"component": "test_comp", "dir": "test/test_comp"}
        findings = gated_by_declared(row, tmp_path)
        assert len(findings) == 1, "sieve should fire on empty gated_by list"

    def test_sieve_fires_on_non_list_gated_by(self, tmp_path):
        charter = {"component": "test_comp", "runtime_role": "tool",
                    "gated_by": "CC", "what": "test"}
        (tmp_path / "intention+why.json").write_text(json.dumps(charter))
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.machines.build_inspector.inspector import gated_by_declared
        row = {"component": "test_comp", "dir": "test/test_comp"}
        findings = gated_by_declared(row, tmp_path)
        assert len(findings) == 1, "sieve should fire on non-list gated_by"

    def test_sieve_fires_on_empty_string_in_gated_by(self, tmp_path):
        charter = {"component": "test_comp", "runtime_role": "tool",
                    "gated_by": ["CC", ""], "what": "test"}
        (tmp_path / "intention+why.json").write_text(json.dumps(charter))
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.machines.build_inspector.inspector import gated_by_declared
        row = {"component": "test_comp", "dir": "test/test_comp"}
        findings = gated_by_declared(row, tmp_path)
        assert len(findings) == 1, "sieve should fire on empty string in gated_by"

    def test_sieve_clean_on_multi_hand_gated_by(self, tmp_path):
        charter = {"component": "test_comp", "runtime_role": "tool",
                    "gated_by": ["Akien", "CC"], "what": "test"}
        (tmp_path / "intention+why.json").write_text(json.dumps(charter))
        sys.path.insert(0, str(REPO_ROOT))
        from cairn.machines.build_inspector.inspector import gated_by_declared
        row = {"component": "test_comp", "dir": "test/test_comp"}
        findings = gated_by_declared(row, tmp_path)
        assert findings == [], "sieve should pass on multi-hand gated_by"


ROSTER_MIN = 15


def test_roster_minimum():
    tests = [name for name in dir() if name.startswith("test_") and callable(eval(name))]
    for cls_name, cls_obj in list(globals().items()):
        if isinstance(cls_obj, type):
            tests.extend(m for m in dir(cls_obj) if m.startswith("test_"))
    assert len(tests) >= ROSTER_MIN, (
        f"need >= {ROSTER_MIN} teeth, have {len(tests)}: {sorted(tests)}"
    )


if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    teeth = sum(1 for name in dir() if name.startswith("test_") and callable(eval(name)))
    for cls_name, cls_obj in list(globals().items()):
        if isinstance(cls_obj, type):
            teeth += sum(1 for m in dir(cls_obj) if m.startswith("test_"))
    color = "\033[32m" if result.returncode == 0 else "\033[31m"
    print(f"\n{color}{teeth} teeth {'green' if result.returncode == 0 else 'RED'}\033[0m")
    sys.exit(result.returncode)

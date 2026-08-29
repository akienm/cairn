"""Proofs for the corrosion sieve (constraint_enforcement_holds).

Each tooth corresponds to a clause in the ticket's falsifier. A hollow
implementation that always returns green would fail teeth 1, 3, and 4.

Provenance: ticket a-constraint-that-stopped-constraining-carries-a-ruling.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

PASS = 0
FAIL = 0


def _tmp_corrosion_component(constraints: list[dict] | None = None) -> tuple[Path, Path]:
    """Create a temporary repo-like structure with a corrosion component."""
    root = Path(tempfile.mkdtemp(prefix="corrosion_"))
    (root / ".git").mkdir()
    comp_dir = root / "cairn" / "machines" / "corrosion"
    comp_dir.mkdir(parents=True)
    (comp_dir / "__init__.py").touch()
    (comp_dir / "proofs").mkdir()
    (comp_dir / "probes").mkdir()
    if constraints is not None:
        cset = {"schema_version": "constraint-set-v1", "constraints": constraints}
        (comp_dir / "constraint_set.json").write_text(
            json.dumps(cset, indent=2), encoding="utf-8")
    return root, comp_dir


def _row(component: str = "corrosion") -> dict:
    return {
        "component": component,
        "dir": "cairn/machines/corrosion",
        "charter_on_disk": True,
        "proofs": 1,
        "validations": [],
        "device_subclasses": [],
        "self_emit_call_sites_outside_proofs": 0,
    }


def test_weakening_without_ruling_reds():
    """A constraint-bearing artifact is ABSENT with no ruling covering it — must fire."""
    global PASS, FAIL
    root, comp_dir = _tmp_corrosion_component([
        {"id": "test-constraint", "path": "cairn/nonexistent/file.py",
         "description": "a constraint that no longer exists", "kind": "check"}
    ])
    try:
        from cairn.machines.build_inspector.inspector import constraint_enforcement_holds
        with patch("cairn.machines.corrosion.citation.ruling_covers_path", return_value=None):
            findings = constraint_enforcement_holds(_row(), comp_dir)
        has_finding = any(f.get("values", {}).get("constraint_id") == "test-constraint"
                         for f in findings)
        if has_finding:
            PASS += 1
            print("PASS: weakening without ruling fires a finding")
        else:
            FAIL += 1
            print(f"FAIL: expected finding for test-constraint, got {findings}")
    finally:
        shutil.rmtree(root)


def test_weakening_with_ruling_greens():
    """A constraint-bearing artifact is absent BUT a ruling covers it — must NOT fire."""
    global PASS, FAIL
    root, comp_dir = _tmp_corrosion_component([
        {"id": "test-ruled-constraint", "path": "cairn/nonexistent/ruled.py",
         "description": "a constraint changed under a ruling", "kind": "check"}
    ])
    try:
        from cairn.machines.build_inspector.inspector import constraint_enforcement_holds
        with patch("cairn.machines.corrosion.citation.ruling_covers_path",
                   return_value="2026-08-14-some-ruling"):
            findings = constraint_enforcement_holds(_row(), comp_dir)
        has_finding = any(f.get("values", {}).get("constraint_id") == "test-ruled-constraint"
                         for f in findings)
        if not has_finding:
            PASS += 1
            print("PASS: ruled weakening does NOT fire (beneficial drift)")
        else:
            FAIL += 1
            print(f"FAIL: ruled weakening should not fire, got {findings}")
    finally:
        shutil.rmtree(root)


def test_strengthening_untouched():
    """A constraint-bearing artifact EXISTS — no finding regardless of ruling."""
    global PASS, FAIL
    root, comp_dir = _tmp_corrosion_component([
        {"id": "test-present", "path": "cairn/machines/corrosion/constraint_set.json",
         "description": "an artifact that exists", "kind": "check"}
    ])
    try:
        from cairn.machines.build_inspector.inspector import constraint_enforcement_holds
        findings = constraint_enforcement_holds(_row(), comp_dir)
        constraint_findings = [f for f in findings
                               if f.get("values", {}).get("constraint_id") == "test-present"]
        if not constraint_findings:
            PASS += 1
            print("PASS: present constraint is untouched (no finding)")
        else:
            FAIL += 1
            print(f"FAIL: present constraint should not fire, got {constraint_findings}")
    finally:
        shutil.rmtree(root)


def test_self_reference_narrowing_reds():
    """The constraint set EXCLUDES itself — the self-reference check must fire."""
    global PASS, FAIL
    root, comp_dir = _tmp_corrosion_component([
        {"id": "something-else", "path": "cairn/CLAUDE.md",
         "description": "not the set itself", "kind": "why"}
    ])
    (root / "cairn" / "CLAUDE.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "cairn" / "CLAUDE.md").touch()
    try:
        from cairn.machines.build_inspector.inspector import constraint_enforcement_holds
        findings = constraint_enforcement_holds(_row(), comp_dir)
        has_self_ref_finding = any("includes itself" in f.get("about", "") for f in findings)
        if has_self_ref_finding:
            PASS += 1
            print("PASS: constraint set excluding itself fires self-reference finding")
        else:
            FAIL += 1
            print(f"FAIL: expected self-reference finding, got {findings}")
    finally:
        shutil.rmtree(root)


def test_stale_ruling_does_not_satisfy():
    """A ruling that does NOT cover the constraint's path must not suppress the finding."""
    global PASS, FAIL
    root, comp_dir = _tmp_corrosion_component([
        {"id": "test-stale", "path": "cairn/nonexistent/stale.py",
         "description": "covered by nothing", "kind": "falsifier"}
    ])
    try:
        from cairn.machines.build_inspector.inspector import constraint_enforcement_holds

        def mock_covers(path):
            if path == "cairn/some/other/path.py":
                return "2026-01-01-unrelated-ruling"
            return None

        with patch("cairn.machines.corrosion.citation.ruling_covers_path",
                   side_effect=mock_covers):
            findings = constraint_enforcement_holds(_row(), comp_dir)
        has_finding = any(f.get("values", {}).get("constraint_id") == "test-stale"
                         for f in findings)
        if has_finding:
            PASS += 1
            print("PASS: stale unrelated ruling does NOT satisfy the check")
        else:
            FAIL += 1
            print(f"FAIL: stale ruling should not suppress, got {findings}")
    finally:
        shutil.rmtree(root)


def test_all_four_kinds_same_predicate():
    """All four constraint kinds (why, check, falsifier, threshold) use one predicate."""
    global PASS, FAIL
    root, comp_dir = _tmp_corrosion_component([
        {"id": "kind-why", "path": "cairn/nonexistent/why.md", "description": "a why", "kind": "why"},
        {"id": "kind-check", "path": "cairn/nonexistent/check.py", "description": "a check", "kind": "check"},
        {"id": "kind-falsifier", "path": "cairn/nonexistent/falsifier.py", "description": "a falsifier", "kind": "falsifier"},
        {"id": "kind-threshold", "path": "cairn/nonexistent/threshold.py", "description": "a threshold", "kind": "threshold"},
    ])
    try:
        from cairn.machines.build_inspector.inspector import constraint_enforcement_holds
        with patch("cairn.machines.corrosion.citation.ruling_covers_path", return_value=None):
            findings = constraint_enforcement_holds(_row(), comp_dir)
        found_kinds = {f.get("values", {}).get("constraint_kind") for f in findings
                       if f.get("values", {}).get("constraint_id", "").startswith("kind-")}
        expected = {"why", "check", "falsifier", "threshold"}
        if found_kinds == expected:
            PASS += 1
            print("PASS: all four constraint kinds caught by the same predicate")
        else:
            FAIL += 1
            print(f"FAIL: expected {expected}, got {found_kinds}")
    finally:
        shutil.rmtree(root)


def test_non_corrosion_component_skips():
    """The sieve returns [] for any component that is not 'corrosion'."""
    global PASS, FAIL
    from cairn.machines.build_inspector.inspector import constraint_enforcement_holds
    row = _row(component="builder")
    findings = constraint_enforcement_holds(row, Path("/tmp/nonexistent"))
    if findings == []:
        PASS += 1
        print("PASS: non-corrosion component returns empty (no false positives)")
    else:
        FAIL += 1
        print(f"FAIL: non-corrosion component should skip, got {findings}")


def test_missing_constraint_set_reds():
    """No constraint_set.json at all — the sieve must fire, not silently pass."""
    global PASS, FAIL
    root, comp_dir = _tmp_corrosion_component(constraints=None)
    try:
        from cairn.machines.build_inspector.inspector import constraint_enforcement_holds
        findings = constraint_enforcement_holds(_row(), comp_dir)
        has_finding = any("constraint set exists" in f.get("about", "") for f in findings)
        if has_finding:
            PASS += 1
            print("PASS: missing constraint set fires a finding")
        else:
            FAIL += 1
            print(f"FAIL: missing constraint set should fire, got {findings}")
    finally:
        shutil.rmtree(root)


def test_empty_constraint_set_reds():
    """Empty constraint set — the sieve must fire (a set watching nothing catches nothing)."""
    global PASS, FAIL
    root, comp_dir = _tmp_corrosion_component(constraints=[])
    try:
        from cairn.machines.build_inspector.inspector import constraint_enforcement_holds
        findings = constraint_enforcement_holds(_row(), comp_dir)
        has_finding = any("non-empty" in f.get("about", "") for f in findings)
        if has_finding:
            PASS += 1
            print("PASS: empty constraint set fires a finding")
        else:
            FAIL += 1
            print(f"FAIL: empty constraint set should fire, got {findings}")
    finally:
        shutil.rmtree(root)


if __name__ == "__main__":
    test_weakening_without_ruling_reds()
    test_weakening_with_ruling_greens()
    test_strengthening_untouched()
    test_self_reference_narrowing_reds()
    test_stale_ruling_does_not_satisfy()
    test_all_four_kinds_same_predicate()
    test_non_corrosion_component_skips()
    test_missing_constraint_set_reds()
    test_empty_constraint_set_reds()
    print(f"\n{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

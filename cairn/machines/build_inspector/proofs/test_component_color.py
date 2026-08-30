"""Proofs for component_color sieve and unbuilt_intentions scan.

Teeth a hollow sieve could not pass: healthy component is green (no finding),
code-changed-since-seal is red (finding), never-proved is red (finding),
unbuilt intention is red (finding).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector.inspector import (  # noqa: E402
    component_color, unbuilt_intentions, _source_fingerprint,
)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402


def _row(name, d=None):
    return {"component": name, "dir": d or name, "charter_on_disk": True,
            "proofs": 1, "validations": [], "device_subclasses": [],
            "self_emit_call_sites_outside_proofs": 0}


def _make_component(root, name, *, proof_code="pass", seal_verdict=None,
                    seal_fingerprint=None):
    comp = root / name
    comp.mkdir(parents=True, exist_ok=True)
    (comp / "intention+why.json").write_text(
        json.dumps({"component": name}), encoding="utf-8")
    proofs = comp / "proofs"
    proofs.mkdir(exist_ok=True)
    (proofs / "test_thing.py").write_text(
        f"# proof\n{proof_code}\n", encoding="utf-8")
    if seal_verdict is not None:
        vals = comp / "validations"
        vals.mkdir(exist_ok=True)
        evidence = {}
        if seal_fingerprint is not None:
            evidence["source_fingerprint"] = seal_fingerprint
        record = {
            "claim": "test",
            "caller": "test",
            "date": "2026-08-29T00:00:00",
            "method": "test",
            "verdict": seal_verdict,
            "evidence": evidence,
            "falsifier": "test",
            "horizon": "test",
        }
        (vals / "test_thing.json").write_text(
            json.dumps([record]), encoding="utf-8")
    return comp


def test_healthy_component_is_green():
    """A component with all proofs sealed green and matching fingerprint draws no finding."""
    with scratch_dir("component_color_healthy") as root:
        comp = _make_component(root, "healthy", seal_verdict="green")
        fp = _source_fingerprint(comp)
        evidence = json.loads(
            (comp / "validations" / "test_thing.json").read_text()
        )
        evidence[0]["evidence"]["source_fingerprint"] = fp
        (comp / "validations" / "test_thing.json").write_text(
            json.dumps(evidence), encoding="utf-8")
        findings = component_color(_row("healthy"), comp)
        assert findings == [], f"healthy component should draw no finding, got {findings}"


def test_code_changed_since_seal_is_red():
    """Code changed after sealing — fingerprint mismatch fires a finding."""
    with scratch_dir("component_color_changed") as root:
        comp = _make_component(root, "changed", seal_verdict="green",
                               seal_fingerprint="stale_fingerprint_000000")
        findings = component_color(_row("changed"), comp)
        assert len(findings) >= 1, f"expected finding for stale fingerprint, got {findings}"
        assert any("fingerprint" in f["about"] for f in findings), \
            f"finding should mention fingerprint: {findings}"


def test_never_proved_is_red():
    """A component with proofs but no validation seal fires a finding."""
    with scratch_dir("component_color_unproved") as root:
        comp = _make_component(root, "unproved")
        findings = component_color(_row("unproved"), comp)
        assert len(findings) >= 1, f"expected finding for missing seal, got {findings}"
        assert any("seal" in f["about"] for f in findings), \
            f"finding should mention seal: {findings}"


def test_red_verdict_is_red():
    """A component with a red seal fires a finding."""
    with scratch_dir("component_color_red") as root:
        comp = _make_component(root, "red_sealed", seal_verdict="red",
                               seal_fingerprint="doesnt_matter")
        findings = component_color(_row("red_sealed"), comp)
        assert len(findings) >= 1, f"expected finding for red verdict, got {findings}"
        assert any("green" in f["about"] for f in findings), \
            f"finding should mention green: {findings}"


def test_no_proofs_defers_to_proofs_exist():
    """A component with zero proofs is NOT flagged by component_color (proofs_exist handles it)."""
    with scratch_dir("component_color_noproofs") as root:
        comp = root / "empty"
        comp.mkdir(parents=True)
        (comp / "intention+why.json").write_text("{}")
        row = _row("empty")
        row["proofs"] = 0
        findings = component_color(row, comp)
        assert findings == [], \
            f"component_color should defer no-proofs to proofs_exist, got {findings}"


def test_unbuilt_intention_is_red():
    """An intention with no corresponding component fires a finding."""
    with scratch_dir("unbuilt_intention") as root:
        # Mirror production layout: root/dev/src/cairn/cairn and root/dev/src/CairnCommons
        dev_src = root / "dev" / "src"
        dev_src.mkdir(parents=True)
        cairn_pkg = dev_src / "cairn" / "cairn"
        cairn_pkg.mkdir(parents=True)
        commons = dev_src / "CairnCommons"
        intentions = commons / "intentions-not-beside-code"
        intentions.mkdir(parents=True)
        (intentions / "I-something-that-does-not-exist.md").write_text(
            "# Something that does not exist\n")
        census_rows = [_row("widget", d="tools/widget")]
        findings = unbuilt_intentions(census_rows, cairn_pkg)
        assert len(findings) >= 1, f"expected finding for unbuilt intention, got {findings}"
        assert any("something" in f["component"] for f in findings), \
            f"finding should name the intention: {findings}"


def test_existing_component_not_flagged_as_unbuilt():
    """An intention whose slug matches a census component is not flagged."""
    with scratch_dir("built_intention") as root:
        dev_src = root / "dev" / "src"
        dev_src.mkdir(parents=True)
        cairn_pkg = dev_src / "cairn" / "cairn"
        cairn_pkg.mkdir(parents=True)
        commons = dev_src / "CairnCommons"
        intentions = commons / "intentions-not-beside-code"
        intentions.mkdir(parents=True)
        (intentions / "I-the-cairn-device.md").write_text(
            "# The cairn device\n")
        census_rows = [
            _row("cairn", d="devices/cairn"),
        ]
        findings = unbuilt_intentions(census_rows, cairn_pkg)
        matched = [f for f in findings if "cairn" in f.get("component", "")]
        assert matched == [], \
            f"cairn-device intention should match census, got findings: {matched}"


if __name__ == "__main__":
    teeth = [
        test_healthy_component_is_green,
        test_code_changed_since_seal_is_red,
        test_never_proved_is_red,
        test_red_verdict_is_red,
        test_no_proofs_defers_to_proofs_exist,
        test_unbuilt_intention_is_red,
        test_existing_component_not_flagged_as_unbuilt,
    ]
    failed = []
    for t in teeth:
        try:
            t()
            print(f"  GREEN  {t.__name__}")
        except Exception as e:
            print(f"  RED    {t.__name__}: {e}")
            failed.append(t.__name__)
    if failed:
        print(f"\nbuild_inspector component_color proofs: {len(failed)} red — {failed}")
        sys.exit(1)
    print(f"\nbuild_inspector component_color proofs: all teeth green")

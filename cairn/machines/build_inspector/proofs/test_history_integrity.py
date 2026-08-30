"""Proofs for history_integrity sieve — in-place edits and uncommitted appends
are caught, clean components pass, and components without history are skipped.

Each tooth sets up a real git repo with committed history/state files, then
modifies the working copy to exercise the finding class it claims.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector.inspector import history_integrity  # noqa: E402
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args],
                   check=True, capture_output=True, text=True)


def _init_repo(root):
    _git(root, "init")
    _git(root, "config", "user.email", "test@test")
    _git(root, "config", "user.name", "test")


def _commit_component(root, comp_name, history_entries, state=None):
    comp = root / comp_name
    comp.mkdir(parents=True, exist_ok=True)
    (comp / "intention+why.json").write_text(
        json.dumps({"component": comp_name}), encoding="utf-8")
    (comp / "history.json").write_text(
        json.dumps(history_entries, indent=2), encoding="utf-8")
    if state is None:
        state = {"standing": "PROVED"} if history_entries else {}
    (comp / "state.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8")
    _git(root, "add", str(comp / "intention+why.json"),
         str(comp / "history.json"), str(comp / "state.json"))
    _git(root, "commit", "-m", f"add {comp_name}")


def _row(name):
    return {"component": name, "dir": name, "charter_on_disk": True}


def test_modified_past_entry_reds():
    """A committed entry changed in the working copy fires a finding."""
    with scratch_dir("history_integrity_modified") as root:
        _init_repo(root)
        entries = [
            {"ticket": "first-ticket", "to": "PROVED", "note": "original"},
            {"ticket": "second-ticket", "to": "BUILDME", "note": "unchanged"},
        ]
        _commit_component(root, "widget", entries)
        tampered = list(entries)
        tampered[0] = dict(tampered[0], note="tampered")
        (root / "widget" / "history.json").write_text(
            json.dumps(tampered, indent=2), encoding="utf-8")
        findings = history_integrity(_row("widget"), root / "widget")
        assert len(findings) >= 1, f"expected finding for modified entry, got {findings}"
        assert any(f["method"] == "history_integrity" for f in findings)
        assert any("entry 0" in f["about"] for f in findings), \
            f"finding should name entry 0: {findings}"


def test_uncommitted_append_flags():
    """An entry appended to working copy but not committed fires a finding."""
    with scratch_dir("history_integrity_append") as root:
        _init_repo(root)
        entries = [{"ticket": "first", "to": "PROVED"}]
        _commit_component(root, "gadget", entries)
        appended = entries + [{"ticket": "second", "to": "BUILDME"}]
        (root / "gadget" / "history.json").write_text(
            json.dumps(appended, indent=2), encoding="utf-8")
        findings = history_integrity(_row("gadget"), root / "gadget")
        assert len(findings) >= 1, f"expected finding for uncommitted append, got {findings}"
        assert any("uncommitted" in f["about"] for f in findings), \
            f"finding should mention uncommitted: {findings}"


def test_untouched_passes():
    """A component whose history.json matches committed produces no findings."""
    with scratch_dir("history_integrity_clean") as root:
        _init_repo(root)
        entries = [{"ticket": "clean-ticket", "to": "PROVED"}]
        _commit_component(root, "clean_comp", entries)
        findings = history_integrity(_row("clean_comp"), root / "clean_comp")
        assert findings == [], f"expected no findings for clean component, got {findings}"


def test_no_history_skips():
    """A component with no history.json produces no findings."""
    with scratch_dir("history_integrity_nohistory") as root:
        _init_repo(root)
        comp = root / "bare_comp"
        comp.mkdir(parents=True)
        (comp / "intention+why.json").write_text('{"component": "bare_comp"}')
        _git(root, "add", str(comp / "intention+why.json"))
        _git(root, "commit", "-m", "add bare")
        findings = history_integrity(_row("bare_comp"), root / "bare_comp")
        assert findings == [], f"expected no findings for component without history, got {findings}"


def test_state_json_tamper_detected():
    """A state.json changed from committed version without history change fires a finding."""
    with scratch_dir("history_integrity_state") as root:
        _init_repo(root)
        entries = [{"ticket": "t1", "to": "PROVED"}]
        state = {"standing": "PROVED"}
        _commit_component(root, "stateful", entries, state=state)
        tampered_state = {"standing": "BUILDME", "injected": True}
        (root / "stateful" / "state.json").write_text(
            json.dumps(tampered_state, indent=2), encoding="utf-8")
        findings = history_integrity(_row("stateful"), root / "stateful")
        assert len(findings) >= 1, f"expected finding for tampered state.json, got {findings}"
        assert any("state.json" in f["about"] for f in findings), \
            f"finding should mention state.json: {findings}"


def test_deleted_entry_reds():
    """Committed entries deleted from working copy fire a finding."""
    with scratch_dir("history_integrity_deleted") as root:
        _init_repo(root)
        entries = [
            {"ticket": "first", "to": "PROVED"},
            {"ticket": "second", "to": "BUILDME"},
        ]
        _commit_component(root, "shrunk", entries)
        (root / "shrunk" / "history.json").write_text(
            json.dumps([entries[0]], indent=2), encoding="utf-8")
        findings = history_integrity(_row("shrunk"), root / "shrunk")
        assert len(findings) >= 1, f"expected finding for deleted entry, got {findings}"
        assert any("entry 1" in f["about"] for f in findings), \
            f"finding should name entry 1: {findings}"


TEETH = [
    test_modified_past_entry_reds,
    test_uncommitted_append_flags,
    test_untouched_passes,
    test_no_history_skips,
    test_state_json_tamper_detected,
    test_deleted_entry_reds,
]


if __name__ == "__main__":
    failed = []
    for fn in TEETH:
        name = fn.__name__
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed.append(name)
    if failed:
        print(f"\n{len(failed)} FAILED: {', '.join(failed)}")
        sys.exit(1)
    print(f"\n{len(TEETH)} teeth, all green.")

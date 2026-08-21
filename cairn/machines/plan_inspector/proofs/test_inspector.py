"""Proofs for the plan inspector — reads charters' filed_edges and finds open work.

FALSIFIER REQUIREMENT: inference_domain and db_domain must both produce findings
on today's tree. A hollow run that greens everything is worse than a red (Law 8).

Two teeth per sieve: one plants a defect, one plants a clean component.
Plus: a letter-prefixed CLOSED edge is correctly detected as closed (bug found
and fixed 2026-08-20 — edge "(b) CLOSED 2026-08-08..." read as open).
Plus: live-tree invariants — inference_domain and db_domain must RED.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
from cairn.machines.plan_inspector.inspector import (  # noqa: E402
    inspect, _is_closed, _is_landed, _strip_letter_prefix,
)


def _charter(root: Path, name: str, data: dict) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "intention+why.json").write_text(json.dumps(data))
    return d


def test_open_filed_edges_catches_open():
    tmp = scratch_dir("plan-inspector-proof-")
    _charter(tmp, "widget", {
        "component": "widget",
        "filed_edges": [
            "this edge is open and unbuilt",
            "CLOSED 2026-08-01 — this one is done",
        ],
    })
    findings = inspect(root=tmp)
    open_findings = [f for f in findings if f["sieve"] == "open_filed_edges"]
    assert len(open_findings) == 1, f"expected 1 open_filed_edges finding, got {len(open_findings)}"
    assert open_findings[0]["evidence"]["open_count"] == 1
    assert open_findings[0]["evidence"]["closed_count"] == 1
    print("  PASS: open_filed_edges catches open edge and counts closed")


def test_open_filed_edges_clean():
    tmp = scratch_dir("plan-inspector-proof-clean-")
    _charter(tmp, "clean_widget", {
        "component": "clean_widget",
        "filed_edges": [
            "CLOSED 2026-08-01 — done",
            "[CLOSED] also done",
        ],
    })
    findings = inspect(root=tmp)
    open_findings = [f for f in findings if f["sieve"] == "open_filed_edges"]
    assert len(open_findings) == 0, f"expected 0 findings on clean component, got {len(open_findings)}"
    print("  PASS: all-closed component produces no open_filed_edges findings")


def test_charter_asserts_unbuilt_catches():
    tmp = scratch_dir("plan-inspector-proof-unbuilt-")
    _charter(tmp, "gadget", {
        "component": "gadget",
        "filed_edges": [
            "the frobulator is not yet wired to the bus",
            "CLOSED 2026-08-01 — old edge",
        ],
    })
    findings = inspect(root=tmp)
    unbuilt = [f for f in findings if f["sieve"] == "charter_asserts_unbuilt"]
    assert len(unbuilt) == 1, f"expected 1 charter_asserts_unbuilt finding, got {len(unbuilt)}"
    print("  PASS: charter_asserts_unbuilt catches 'not yet wired'")


def test_charter_asserts_unbuilt_clean():
    tmp = scratch_dir("plan-inspector-proof-unbuilt-clean-")
    _charter(tmp, "solid", {
        "component": "solid",
        "filed_edges": [
            "this edge is open but does not name unbuilt work",
        ],
    })
    findings = inspect(root=tmp)
    unbuilt = [f for f in findings if f["sieve"] == "charter_asserts_unbuilt"]
    assert len(unbuilt) == 0, f"expected 0 charter_asserts_unbuilt on edge without unbuilt patterns, got {len(unbuilt)}"
    print("  PASS: open edge without unbuilt pattern does not trigger charter_asserts_unbuilt")


def test_letter_prefix_closed():
    """The bug: '(b) CLOSED 2026-08-08...' read as open because _is_closed checked
    the raw string starting with '(' not 'CLOSED'. Fixed by stripping letter prefixes."""
    assert _is_closed("(b) CLOSED 2026-08-08 and replaced by residues")
    assert _is_closed("(a) [CLOSED] done")
    assert _is_closed("CLOSED 2026-08-01 — done")
    assert not _is_closed("(a) this is still open")
    assert not _is_closed("this edge mentions CLOSED in the middle")

    assert _is_landed("(c) LANDED 2026-08-01")
    assert _is_landed("LANDED here")
    assert not _is_landed("(a) still open")

    assert _strip_letter_prefix("(b) CLOSED") == "CLOSED"
    assert _strip_letter_prefix("(ab) CLOSED") == "CLOSED"
    assert _strip_letter_prefix("CLOSED") == "CLOSED"
    print("  PASS: letter-prefixed CLOSED/LANDED edges are correctly detected")


def test_letter_prefix_in_charter():
    """End-to-end: a charter with lettered edges, some closed, correctly counted."""
    tmp = scratch_dir("plan-inspector-proof-lettered-")
    _charter(tmp, "domain", {
        "component": "domain",
        "filed_edges": [
            "(a) this edge is open",
            "(b) CLOSED 2026-08-08 — done and replaced by residues",
            "(c) also open, not yet wired",
            "(d) LANDED 2026-08-10 — built and proven",
        ],
    })
    findings = inspect(root=tmp)
    open_findings = [f for f in findings if f["sieve"] == "open_filed_edges"]
    assert len(open_findings) == 1
    ev = open_findings[0]["evidence"]
    assert ev["open_count"] == 2, f"expected 2 open, got {ev['open_count']}"
    assert ev["closed_count"] == 2, f"expected 2 closed (1 CLOSED + 1 LANDED), got {ev['closed_count']}"
    print("  PASS: lettered charter counts open/closed correctly")


def test_live_tree_inference_domain_reds():
    """FALSIFIER: inference_domain must produce findings on the real tree."""
    findings = inspect(component_filter="inference_domain", root=_REPO_ROOT)
    assert len(findings) > 0, "FALSIFIER FAILED: inference_domain produced 0 findings — the inspector is blind"
    print(f"  PASS: inference_domain REDs with {len(findings)} finding(s)")


def test_live_tree_db_domain_reds():
    """FALSIFIER: db_domain must produce findings on the real tree."""
    findings = inspect(component_filter="db_domain", root=_REPO_ROOT)
    assert len(findings) > 0, "FALSIFIER FAILED: db_domain produced 0 findings — the inspector is blind"
    print(f"  PASS: db_domain REDs with {len(findings)} finding(s)")


def main() -> None:
    tests = [
        test_open_filed_edges_catches_open,
        test_open_filed_edges_clean,
        test_charter_asserts_unbuilt_catches,
        test_charter_asserts_unbuilt_clean,
        test_letter_prefix_closed,
        test_letter_prefix_in_charter,
        test_live_tree_inference_domain_reds,
        test_live_tree_db_domain_reds,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__}: {e}")
            failed += 1

    print(f"\nplan_inspector proofs: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

"""Proofs for run_record — persistent check-run records for cross-run comparison.

Ticket: the-proof-record-persists-so-runs-can-be-compared (2026-08-14).
Teeth a hollow recorder could not pass: green is recorded (not just red),
silent-stop is detected, verdict-change is detected, never-redded is correct.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector.run_record import (  # noqa: E402
    persist_run,
    read_run,
    compare_runs,
    never_redded,
    list_runs,
)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402


def _fake_result(gradation: dict, scope: str = "all") -> dict:
    """Build a minimal inspect()-shaped result from a gradation dict."""
    return {
        "scope": scope,
        "components_inspected": len(gradation),
        "sieves_run": sorted(
            {s for sieves in gradation.values() for s in sieves}
        ),
        "gradation": gradation,
    }


def test_persist_and_read_round_trip():
    """A persisted run record round-trips correctly with greens AND reds."""
    with scratch_dir("run_record_round_trip") as root:
        records = root / "records"
        grad = {
            "devices/foo": {
                "charter_on_disk": 1.0,
                "proofs_exist": 1.0,
                "component_color": 0.0,
            },
            "tools/bar": {
                "charter_on_disk": 1.0,
                "proofs_exist": 0.0,
                "component_color": 1.0,
            },
        }
        result = _fake_result(grad)
        path = persist_run(result, "build_inspector", records)
        assert path.exists(), f"record file should exist at {path}"

        loaded = read_run(path)
        assert loaded["surface"] == "build_inspector"
        assert loaded["scope"] == "all"
        assert loaded["components_inspected"] == 2

        checks = loaded["checks"]
        assert "devices/foo" in checks, "devices/foo missing from record"
        assert "tools/bar" in checks, "tools/bar missing from record"

        # GREEN is recorded — the founding constraint
        assert checks["devices/foo"]["charter_on_disk"]["score"] == 1.0, \
            "green check should be recorded as 1.0"
        # RED is recorded
        assert checks["devices/foo"]["component_color"]["score"] == 0.0, \
            "red check should be recorded as 0.0"
        # Both present — can distinguish green from absent
        assert len(checks["devices/foo"]) == 3, \
            f"all 3 sieves should be in record, got {len(checks['devices/foo'])}"


def test_silent_stop_detected():
    """A check present in run 1 and absent in run 2 is reported as removed."""
    with scratch_dir("run_record_silent_stop") as root:
        records = root / "records"

        # Run 1: two components, three sieves each
        grad1 = {
            "devices/alpha": {"sieve_a": 1.0, "sieve_b": 1.0},
            "devices/beta": {"sieve_a": 1.0, "sieve_b": 0.0},
        }
        # Run 2: beta is gone (its sieves silently stopped running)
        grad2 = {
            "devices/alpha": {"sieve_a": 1.0, "sieve_b": 1.0},
        }

        p1 = persist_run(_fake_result(grad1), "build_inspector", records)
        p2 = persist_run(_fake_result(grad2), "build_inspector", records)

        old = read_run(p1)
        new = read_run(p2)
        diff = compare_runs(old, new)

        assert len(diff["removed"]) == 2, \
            f"beta's 2 sieves should be removed, got {diff['removed']}"
        removed_comps = {r["component"] for r in diff["removed"]}
        assert "devices/beta" in removed_comps, \
            f"beta should be in removed, got {removed_comps}"
        assert diff["added"] == [], f"no checks added, got {diff['added']}"


def test_verdict_change_detected():
    """A check that changes from green to red (or vice versa) is reported."""
    with scratch_dir("run_record_verdict_change") as root:
        records = root / "records"

        grad1 = {"devices/gamma": {"sieve_x": 1.0, "sieve_y": 0.0}}
        grad2 = {"devices/gamma": {"sieve_x": 0.0, "sieve_y": 1.0}}

        p1 = persist_run(_fake_result(grad1), "build_inspector", records)
        p2 = persist_run(_fake_result(grad2), "build_inspector", records)

        diff = compare_runs(read_run(p1), read_run(p2))

        assert len(diff["changed"]) == 2, \
            f"both sieves changed, got {diff['changed']}"
        changes = {c["sieve"]: (c["old_score"], c["new_score"]) for c in diff["changed"]}
        assert changes["sieve_x"] == (1.0, 0.0), \
            f"sieve_x went green->red, got {changes.get('sieve_x')}"
        assert changes["sieve_y"] == (0.0, 1.0), \
            f"sieve_y went red->green, got {changes.get('sieve_y')}"


def test_never_redded_correct():
    """A check green in all runs is never-redded; one that went red is excluded."""
    with scratch_dir("run_record_never_redded") as root:
        records = root / "records"

        # Run 1: both green
        grad1 = {"devices/delta": {"always_green": 1.0, "sometimes_red": 1.0}}
        # Run 2: sometimes_red goes red
        grad2 = {"devices/delta": {"always_green": 1.0, "sometimes_red": 0.0}}
        # Run 3: sometimes_red back to green
        grad3 = {"devices/delta": {"always_green": 1.0, "sometimes_red": 1.0}}

        persist_run(_fake_result(grad1), "build_inspector", records)
        persist_run(_fake_result(grad2), "build_inspector", records)
        persist_run(_fake_result(grad3), "build_inspector", records)

        result = never_redded(records)
        assert ("devices/delta", "always_green") in result, \
            f"always_green should be never-redded, got {result}"
        assert ("devices/delta", "sometimes_red") not in result, \
            f"sometimes_red should NOT be never-redded (it was red in run 2), got {result}"


def test_check_added_detected():
    """A new check in run 2 that was not in run 1 is reported as added."""
    with scratch_dir("run_record_added") as root:
        records = root / "records"

        grad1 = {"devices/epsilon": {"existing": 1.0}}
        grad2 = {"devices/epsilon": {"existing": 1.0, "new_sieve": 0.0}}

        p1 = persist_run(_fake_result(grad1), "build_inspector", records)
        p2 = persist_run(_fake_result(grad2), "build_inspector", records)

        diff = compare_runs(read_run(p1), read_run(p2))
        assert len(diff["added"]) == 1, f"one check added, got {diff['added']}"
        assert diff["added"][0]["sieve"] == "new_sieve"


def test_list_runs_chronological():
    """list_runs returns records in filename (chronological) order."""
    with scratch_dir("run_record_list") as root:
        records = root / "records"

        for i in range(3):
            persist_run(
                _fake_result({"comp": {"s": float(i)}}),
                "build_inspector",
                records,
            )

        runs = list_runs(records)
        assert len(runs) == 3, f"expected 3 runs, got {len(runs)}"
        names = [r.name for r in runs]
        assert names == sorted(names), f"runs should be sorted, got {names}"


def test_empty_records_dir():
    """never_redded and list_runs handle missing/empty dirs gracefully."""
    with scratch_dir("run_record_empty") as root:
        records = root / "records"
        assert list_runs(records) == [], "missing dir should return empty list"
        assert never_redded(records) == set(), "missing dir should return empty set"


if __name__ == "__main__":
    teeth = [
        test_persist_and_read_round_trip,
        test_silent_stop_detected,
        test_verdict_change_detected,
        test_never_redded_correct,
        test_check_added_detected,
        test_list_runs_chronological,
        test_empty_records_dir,
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
        print(f"\nrun_record proofs: {len(failed)} red — {failed}")
        sys.exit(1)
    print(f"\nrun_record proofs: all {len(teeth)} teeth green")

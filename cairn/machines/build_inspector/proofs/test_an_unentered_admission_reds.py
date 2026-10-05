"""A sole-path file admission with no exemption entry at its seat reds (ticket b364df579e49).

sole_path_admissions_are_entered reads every import_sieve rule literal (a dict carrying
'modules' and 'only') and needs an exemption_set entry, matched on seat path + member text,
for each member that admits a single file past the door. Four teeth seed tmp roots and call
the sieve directly; the fifth runs inspect(component='exemptions') over the live repo. The
inspector is imported inside each tooth, so a reverted inspector.py reds a tooth instead of
breaking the file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"b364df579e49": {
    "1": "test_an_unentered_file_admission_reds_once",
    "2": "test_an_entry_at_the_seat_clears_it",
    "3": "test_a_directory_member_needs_no_entry",
    "4": "test_a_rule_under_fixtures_is_skipped",
    "5": "test_the_live_repo_reads_clean",
}}

_SEAT = "tools/x/rules.py"


def _seed(only: str, entries: list[dict], seat: str = _SEAT) -> Path:
    root = scratch_dir("cairn-unentered-admission-")
    (root / ".git").mkdir()
    (root / seat).parent.mkdir(parents=True, exist_ok=True)
    (root / seat).write_text('RULE = {"modules": ("socket",), "only": %s}\n' % only)
    comp = root / "cairn" / "machines" / "exemptions"
    comp.mkdir(parents=True)
    (comp / "exemption_set.json").write_text(json.dumps({"exemptions": entries}))
    return comp


def _run(comp: Path) -> list[dict]:
    from cairn.machines.build_inspector import inspector
    return inspector.sole_path_admissions_are_entered({"component": "exemptions"}, comp)


def test_an_unentered_file_admission_reds_once():
    found = _run(_seed("('x_domain/', 'tools/y/z.py')", []))
    abouts = [f.get("about", "") for f in found]
    assert len(found) == 1 and _SEAT in abouts[0] and "tools/y/z.py" in abouts[0], abouts


def test_an_entry_at_the_seat_clears_it():
    found = _run(_seed("('x_domain/', 'tools/y/z.py')",
                       [{"id": "x-admits-z", "path": _SEAT, "symbol": '"tools/y/z.py"'}]))
    assert found == [], [f.get("about") for f in found]


def test_a_directory_member_needs_no_entry():
    found = _run(_seed("('x_domain/',)", []))
    assert found == [], [f.get("about") for f in found]


def test_a_rule_under_fixtures_is_skipped():
    found = _run(_seed("('x_domain/', 'tools/y/z.py')", [], seat="tools/fixtures/rules.py"))
    assert found == [], [f.get("about") for f in found]


def test_the_live_repo_reads_clean():
    from cairn.machines.build_inspector import inspector
    assert "sole_path_admissions_are_entered" in inspector.SIEVES
    report = inspector.inspect(component="exemptions")
    mine = [f for f in report["findings"] if f.get("method") == "sole_path_admissions_are_entered"]
    assert mine == [], [f.get("about") for f in mine]


def main() -> int:
    fails = 0
    for name in PROVES["b364df579e49"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

"""Proof: cairn install lays the journal merge driver in every repo root (ticket 7cfbc64b2a67).

Ticket b7d2e05a1c93 built the driver that re-links two sessions' artifact journals, but it
lives in .git/config, which git does not carry: a box nobody configured silently falls back
to git's text merge, and the chain can fork. These teeth hold the installer to laying it.

Teeth 1-4 run over scratch repos (git init under a scratch dir) passed in as roots; the
live repos' config is never written. Tooth 5 runs `cairn install --dry-run`, which reads only.
The installer's new step is imported inside each tooth, so a hollow build reds per tooth.

    python3 cairn/devices/recovery/machines/installer/proofs/test_install_lays_the_journal_merge_driver.py
"""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
assert (REPO / "bin" / "cairn").exists(), f"REPO {REPO} does not hold bin/cairn"
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"7cfbc64b2a67": {
    "1": "test_an_unset_driver_is_offered_and_left_unwritten",
    "2": "test_a_run_lays_it_in_every_root_and_a_second_reads_applied",
    "3": "test_a_driver_naming_a_gone_interpreter_is_relaid",
    "4": "test_a_root_that_is_not_a_repository_is_skipped",
    "5": "test_cairn_install_dry_run_lists_the_step",
}}

KEY = "merge.cairn-journal.driver"


def _repo(name: str) -> Path:
    d = scratch_dir(f"journal-driver-{name}-")
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    return d


def _driver(d: Path) -> str:
    return subprocess.run(["git", "-C", str(d), "config", "--get", KEY],
                          capture_output=True, text=True).stdout.strip()


def test_an_unset_driver_is_offered_and_left_unwritten() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_journal_merge_driver
    a, b = _repo("a"), _repo("b")
    r = ensure_journal_merge_driver(roots={"cairn": a, "CairnCommons": b}, dry_run=True)
    assert r["status"] == "offered", r
    assert "not configured" in r["detail"], r
    assert _driver(a) == "" and _driver(b) == "", "dry run wrote a driver"


def test_a_run_lays_it_in_every_root_and_a_second_reads_applied() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_journal_merge_driver
    a, b = _repo("a"), _repo("b")
    roots = {"cairn": a, "CairnCommons": b}
    r = ensure_journal_merge_driver(roots=roots)
    assert r["status"] == "applied", r
    for d in (a, b):
        drv = _driver(d)
        assert "-m cairn.tools.artifact merge-journal %O %A %B" in drv, drv
        assert f"PYTHONPATH={REPO}" in drv, drv
    again = ensure_journal_merge_driver(roots=roots)
    assert again["status"] == "already_applied", again


def test_a_driver_naming_a_gone_interpreter_is_relaid() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_journal_merge_driver
    a = _repo("stale")
    stale = f"PYTHONPATH={REPO} /nonexistent/python3 -m cairn.tools.artifact merge-journal %O %A %B"
    subprocess.run(["git", "-C", str(a), "config", KEY, stale], check=True)
    seen = ensure_journal_merge_driver(roots={"cairn": a}, dry_run=True)
    assert seen["status"] == "offered" and "/nonexistent/python3" in seen["detail"], seen
    r = ensure_journal_merge_driver(roots={"cairn": a})
    assert r["status"] == "applied", r
    assert "/nonexistent/python3" not in _driver(a), _driver(a)
    assert sys.executable in _driver(a) or Path(_driver(a).split()[1]).exists(), _driver(a)


def test_a_root_that_is_not_a_repository_is_skipped() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_journal_merge_driver
    a = _repo("real")
    bare = scratch_dir("journal-driver-norepo-")
    r = ensure_journal_merge_driver(roots={"cairn": a, "CairnCommons": bare})
    assert r["status"] == "applied", r
    assert f"CairnCommons skipped ({bare} is not a git repository)" in r["detail"], r
    assert not (bare / ".git").exists()


def test_cairn_install_dry_run_lists_the_step() -> None:
    from cairn.devices.recovery.machines.installer import installer
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        installer.main(["--dry-run"])
    assert "] journal-merge-driver:" in out.getvalue(), out.getvalue()


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 5 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

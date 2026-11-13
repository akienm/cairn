"""Proof: the install inspector reds every lack and the gate refuses while one stands (ticket bdd0ed77930f).

Clauses 1-3 drive the inspector; clause 4 drives the installer's fix_reds (the seam D3 names).

Teeth drive injected fake checks (callables shaped {id,status,detail}) and the real
ensure_journal_merge_driver over a scratch git repo; the live repos' config is never written.
The inspector is imported inside each tooth, so a hollow build reds per tooth.
"""

from __future__ import annotations

import functools
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
assert (REPO / "bin" / "cairn").exists(), f"REPO {REPO} does not hold bin/cairn"
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"bdd0ed77930f": {
    "1": "test_inspect_reds_the_offered_and_the_raising_and_not_the_green",
    "2": "test_installed_is_false_with_the_reds_then_true_once_all_are_green",
    "3": "test_inspect_measures_with_dry_run_and_writes_nothing",
    "4": "test_fix_reds_calls_each_red_once_with_dry_run_false_and_no_green",
}}


def _check(sid: str, status: str, calls: list):
    def check(dry_run: bool = False) -> dict:
        calls.append((sid, dry_run))
        return {"id": sid, "status": status, "detail": f"{sid} is {status}"}
    return check


def _raiser(calls: list):
    def check(dry_run: bool = False) -> dict:
        calls.append(("boom", dry_run))
        raise RuntimeError("the probe fell over")
    return check


def test_inspect_reds_the_offered_and_the_raising_and_not_the_green() -> None:
    from cairn.devices.recovery.machines.install_inspector.inspector import inspect
    calls: list = []
    reds = inspect([_check("green", "already_applied", calls), _check("lack", "offered", calls),
                    _raiser(calls)])
    assert len(reds) == 2, reds
    by_id = {r["id"]: r for r in reds}
    assert "lack is offered" in by_id["lack"]["detail"], reds
    boom = next(r for r in reds if r["id"] != "lack")
    assert "RuntimeError" in boom["detail"] and "the probe fell over" in boom["detail"], boom


def test_installed_is_false_with_the_reds_then_true_once_all_are_green() -> None:
    from cairn.devices.recovery.machines.install_inspector.inspector import installed
    calls: list = []
    ok, reds = installed([_check("green", "already_applied", calls), _check("lack", "offered", calls)])
    assert ok is False and [r["id"] for r in reds] == ["lack"], (ok, reds)
    ok, reds = installed([_check("a", "already_applied", calls), _check("b", "already_applied", calls)])
    assert ok is True and reds == [], (ok, reds)


def test_inspect_measures_with_dry_run_and_writes_nothing() -> None:
    from cairn.devices.recovery.machines.install_inspector.inspector import inspect
    from cairn.devices.recovery.machines.installer.installer import ensure_journal_merge_driver
    calls: list = []
    inspect([_check("a", "already_applied", calls), _check("b", "offered", calls)])
    assert calls and all(dry for _, dry in calls), f"a check ran with dry_run False: {calls}"
    repo = scratch_dir("install-gate-repo-")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    cfg = repo / ".git" / "config"
    before = cfg.read_bytes()
    reds = inspect([functools.partial(ensure_journal_merge_driver, roots={"cairn": repo})])
    assert len(reds) == 1 and reds[0]["status"] == "offered", reds
    assert cfg.read_bytes() == before, "inspect wrote the scratch repo's git config"


def test_fix_reds_calls_each_red_once_with_dry_run_false_and_no_green() -> None:
    from cairn.devices.recovery.machines.installer.installer import fix_reds
    from cairn.devices.recovery.machines.install_inspector.inspector import installed
    calls: list = []
    state = {"lack": "offered"}

    def lack(dry_run: bool = False) -> dict:
        calls.append(("lack", dry_run))
        if not dry_run:
            state["lack"] = "already_applied"
        return {"id": "lack", "status": state["lack"], "detail": "lack"}

    checks = [_check("green", "already_applied", calls), lack]
    fixed = fix_reds(checks)
    real = [c for c in calls if c[1] is False]
    assert real == [("lack", False)], f"the fix pass must call the red once, dry_run=False, and no green: {calls}"
    assert [r["id"] for r in fixed] == ["lack"], fixed
    ok, reds = installed(checks)
    assert ok is True and reds == [], (ok, reds)


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

"""A reseal that cannot run raises a trouble, and the commit still lands.

WHAT IS BEING PROVED (ticket b0e65cf8a77e). Measured 2026-11-12: a full /tmp crashed
``cairn test --reseal --stage`` inside the pre-commit hook, the hook's ``|| true`` swallowed it,
and the commit landed rc 0 with no seals staged and nothing recorded. The hook never blocks
(Akien 2026-09-30) and Law 7 wants the crash permanent in a record, so ``reseal.run_or_record``
turns a crash into the trouble ``tester-reseal-could-not-run`` and the hook still exits 0.

(1) a run that raises OSError(ENOSPC) returns 3 and raises exactly one trouble under that key,
    carrying the error and the traceback tail;
(2) a run that completes returns its own code, and clears that trouble only when it stands;
(3) a KeyboardInterrupt passes through and raises nothing (a kill is 143e3974647b's);
(4) the CLI's ``_reseal_run`` goes through the door: a staged-file read that fails with ENOSPC
    yields 3 and the trouble, and the hook still runs the reseal under ``|| true`` and exits 0.

No tooth files a trouble into the live store: the raiser is a fake, injected or patched in.
A hollow build could not pass: without run_or_record every tooth fails to import or re-raises.
"""
from __future__ import annotations

import argparse
import errno
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester import reseal  # noqa: E402

PROVES = {"b0e65cf8a77e": {
    "1": "test_a_crashed_run_returns_3_and_raises_one_trouble",
    "2": "test_a_completed_run_keeps_its_code_and_clears_only_a_standing_trouble",
    "3": "test_a_kill_passes_through_and_raises_nothing",
    "4": "test_the_cli_and_the_hook_go_through_the_door",
}}


class _FakeRaiser:
    def __init__(self, *a, **k):
        self.raised, self.cleared = [], []

    def raise_trouble(self, identity, *, why, detail=None):
        self.raised.append({"identity": identity, "why": why, "detail": detail or {}})

    def clear_trouble(self, identity, *, by, what_changed):
        self.cleared.append({"identity": identity, "by": by})


def _enospc():
    raise OSError(errno.ENOSPC, "No space left on device", "/tmp/x")


def test_a_crashed_run_returns_3_and_raises_one_trouble() -> None:
    r = _FakeRaiser()
    code = reseal.run_or_record(_enospc, raiser=r, standing=lambda: False)
    assert code == 3, code
    assert [t["identity"] for t in r.raised] == [reseal.RUN_CRASH_IDENTITY], r.raised
    d = r.raised[0]["detail"]
    assert d["error"] == "OSError" and "No space left on device" in d["message"], d
    assert "_enospc" in d["traceback_tail"], d["traceback_tail"]
    assert r.cleared == [], r.cleared
    print("ok test_a_crashed_run_returns_3_and_raises_one_trouble")


def test_a_completed_run_keeps_its_code_and_clears_only_a_standing_trouble() -> None:
    r = _FakeRaiser()
    assert reseal.run_or_record(lambda: 1, raiser=r, standing=lambda: False) == 1
    assert r.cleared == [] and r.raised == [], (r.cleared, r.raised)
    r2 = _FakeRaiser()
    assert reseal.run_or_record(lambda: 0, raiser=r2, standing=lambda: True) == 0
    assert [c["identity"] for c in r2.cleared] == [reseal.RUN_CRASH_IDENTITY], r2.cleared
    assert r2.raised == [], r2.raised
    print("ok test_a_completed_run_keeps_its_code_and_clears_only_a_standing_trouble")


def test_a_kill_passes_through_and_raises_nothing() -> None:
    r = _FakeRaiser()

    def killed():
        raise KeyboardInterrupt

    try:
        reseal.run_or_record(killed, raiser=r, standing=lambda: False)
    except KeyboardInterrupt:
        pass
    else:
        raise AssertionError("a kill was swallowed")
    assert r.raised == [] and r.cleared == [], (r.raised, r.cleared)
    print("ok test_a_kill_passes_through_and_raises_nothing")


def test_the_cli_and_the_hook_go_through_the_door() -> None:
    from cairn.devices.tester import cli
    import cairn.tools.base.diagnostic as diagnostic

    made = []

    class _Patched(_FakeRaiser):
        def __init__(self, *a, **k):
            super().__init__()
            made.append(self)

    saved = (reseal.staged_files, diagnostic.ModuleRaiser)
    reseal.staged_files, diagnostic.ModuleRaiser = _enospc, _Patched
    try:
        code = cli._reseal_run(argparse.Namespace(targets=[], ruling=None, timeout=120,
                                                  stage=True, quiet=True))
    finally:
        reseal.staged_files, diagnostic.ModuleRaiser = saved
    assert code == 3, code
    assert [t["identity"] for m in made for t in m.raised] == [reseal.RUN_CRASH_IDENTITY], made

    hook = (_REPO_ROOT / "cairn/devices/tester/hooks/pre-commit").read_text().splitlines()
    calls = [ln for ln in hook if "cairn.devices.tester.cli --reseal" in ln]
    assert calls and all(ln.rstrip().endswith("|| true") for ln in calls), calls
    assert hook[-1].strip() == "exit 0", hook[-1]
    print("ok test_the_cli_and_the_hook_go_through_the_door")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

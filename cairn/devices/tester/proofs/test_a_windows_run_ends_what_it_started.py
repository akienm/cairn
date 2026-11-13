"""Proof — the tester runs a proof in a Windows job with no console, so what the proof started dies with it.

Measured 2026-11-13 on Windows: runs.kill_what_it_started answered "process environments cannot be
enumerated on Windows" and reaped nothing, and device.py ran the proof with subprocess.run and no
creationflags, so a proof's scratch processes outlived it and each opened a console.

Spawns nothing: kernel32 and subprocess are replaced, so it runs on any host (a real Windows spawn
waits on Q#92). One tooth per falsifier clause.

    python3 cairn/devices/tester/proofs/test_a_windows_run_ends_what_it_started.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEVICE = ROOT / "cairn" / "devices" / "tester" / "device.py"
KILL_ON_CLOSE, NO_WINDOW = 0x2000, 0x08000000

PROVES = {"715d2205a2ec": {
    "1": "test_nt_starts_the_run_in_a_kill_on_close_job_with_no_window",
    "2": "test_posix_is_subprocess_run_unchanged",
    "3": "test_device_has_no_bare_subprocess_run_left",
    "4": "test_nt_no_longer_says_it_cannot_enumerate",
}}


class _K32:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def call(*a):
            self.calls.append((name, a))
            return 7
        return call

    def names(self):
        return [c[0] for c in self.calls]


def _fake_popen(timeout_first=False):
    proc = mock.MagicMock()
    proc.returncode = 0
    proc._handle = 5
    if timeout_first:
        proc.communicate.side_effect = [subprocess.TimeoutExpired("x", 1), ("", "")]
    else:
        proc.communicate.return_value = ("out", "err")
    return mock.MagicMock(return_value=proc)


def _run_nt(timeout_first=False, **kw):
    from cairn.devices.tester import runs
    k, popen = _K32(), _fake_popen(timeout_first)
    with mock.patch.object(runs, "_is_nt", lambda: True), \
         mock.patch.object(runs, "_kernel32", lambda: k), \
         mock.patch.object(runs.subprocess, "Popen", popen):
        try:
            res = runs.run_owned(["x"], capture_output=True, text=True, timeout=1, **kw)
        except subprocess.TimeoutExpired:
            res = None
    return k, popen, res


def test_nt_starts_the_run_in_a_kill_on_close_job_with_no_window():
    k, popen, res = _run_nt()
    names = k.names()
    assert names.index("CreateJobObjectW") < names.index("SetInformationJobObject") \
        < names.index("AssignProcessToJobObject") < names.index("CloseHandle"), names
    info = [c for c in k.calls if c[0] == "SetInformationJobObject"][0][1]
    buf = next(a for a in info if hasattr(a, "raw") or isinstance(a, (bytes, bytearray)))
    raw = buf.raw if hasattr(buf, "raw") else bytes(buf)
    assert int.from_bytes(raw[16:20], "little") & KILL_ON_CLOSE, raw[:24]
    assert popen.call_args.kwargs["creationflags"] & NO_WINDOW, popen.call_args
    assert res is not None and res.stdout == "out" and res.returncode == 0, res
    k2, _, res2 = _run_nt(timeout_first=True)
    assert res2 is None and "TerminateJobObject" in k2.names(), k2.names()


def test_posix_is_subprocess_run_unchanged():
    from cairn.devices.tester import runs
    with mock.patch.object(runs, "_is_nt", lambda: False), \
         mock.patch.object(runs.subprocess, "run", return_value="R") as run:
        got = runs.run_owned(["a", "b"], capture_output=True, text=True, timeout=3, env={"k": "v"})
    assert got == "R", got
    run.assert_called_once_with(["a", "b"], capture_output=True, text=True, timeout=3, env={"k": "v"})


def test_device_has_no_bare_subprocess_run_left():
    src = DEVICE.read_text(encoding="utf-8")
    assert "subprocess.run(" not in src, "device.py still calls subprocess.run directly"
    assert src.count("run_owned(") >= 2, src.count("run_owned(")


def test_nt_no_longer_says_it_cannot_enumerate():
    from cairn.devices.tester import runs
    with mock.patch.object(runs, "_is_nt", lambda: True), \
         mock.patch.object(runs, "stop_its_units", lambda t: []):
        got = runs.kill_what_it_started("test-abc")
    assert "cannot be enumerated" not in repr(got), got


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

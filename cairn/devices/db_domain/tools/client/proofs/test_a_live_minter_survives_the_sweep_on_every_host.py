"""Proof: a live process is a live minter on every host, so the scratch sweep never drops its tables.

Measured 2026-11-14 on akiendell: ``store.process_start`` read ``/proc``, which Windows lacks, so it
answered None for EVERY pid, a live one included. ``minter_alive`` then read the caller's own process
as dead and ``sweep_scratch()`` dropped the caller's own live scratch table (probe: one scratch table
held, one ``sweep_scratch()``, table gone and unregistered). The tester sweeps before every ``--seal``,
so a proof opening fixture buses (test_the_seal_announces_itself) lost its tables mid-run, the bus
re-created them unregistered, and the run left 24 ``seal_ann_*_delivery`` tables behind.

  1. ``process_start`` of a running child is its creation time (within a minute of now), and
     ``minter_alive`` for this process and for the child is True.
  2. ``process_start`` of a pid that has exited is None and ``minter_alive`` is False for it.
  3. ``sweep_scratch()`` leaves this process's own live scratch table standing and registered.

On Linux the first two readings come from /proc as they always did; the proof is red-first on Windows.

    python3 cairn/devices/db_domain/tools/client/proofs/test_a_live_minter_survives_the_sweep_on_every_host.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"winprocstart": {
    "1": "test_a_running_process_has_a_start_time_and_is_a_live_minter",
    "2": "test_an_exited_process_has_none_and_is_not_a_live_minter",
    "3": "test_the_sweep_leaves_this_process_own_live_scratch_table",
}}


def _child() -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def test_a_running_process_has_a_start_time_and_is_a_live_minter():
    from cairn.devices.db_domain.tools.client import store
    child = _child()
    try:
        started = store.process_start(child.pid)
        assert started is not None, "a running child has no start time"
        assert abs(time.time() - started) < 60, f"the child's start time is not recent: {started} vs {time.time()}"
        now = datetime.now(timezone.utc)
        assert store.minter_alive(child.pid, now) is True, "a running child reads as a dead minter"
        assert store.minter_alive(os.getpid(), now) is True, "this process reads as a dead minter"
    finally:
        child.kill()
        child.wait()


def test_an_exited_process_has_none_and_is_not_a_live_minter():
    from cairn.devices.db_domain.tools.client import store
    child = _child()
    pid = child.pid
    child.kill()
    child.wait()
    assert store.process_start(pid) is None, "an exited pid still has a start time"
    assert store.minter_alive(pid, datetime.now(timezone.utc)) is False


def test_the_sweep_leaves_this_process_own_live_scratch_table():
    from cairn.devices.db_domain.tools.client import store
    with store.scratch("db_domain", "live_minter_probe", {"k": "text PRIMARY KEY"}) as table:
        store.sweep_scratch()
        conn = store.connect()
        standing = store.query("select 1 as x from pg_tables where tablename = %s", tables={}, params=(table,), conn=conn)
        assert standing, "sweep_scratch dropped this process's own live scratch table"
        assert store.is_scratch(table, conn=conn), "sweep_scratch unregistered this process's own live scratch table"


TEETH = [test_a_running_process_has_a_start_time_and_is_a_live_minter,
         test_an_exited_process_has_none_and_is_not_a_live_minter,
         test_the_sweep_leaves_this_process_own_live_scratch_table]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except BaseException as e:  # noqa: BLE001 - a proof reports, never hides
            failed += 1
            print(f"  RED  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"{'GREEN' if not failed else 'RED'} - {len(TEETH) - failed}/{len(TEETH)} teeth")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

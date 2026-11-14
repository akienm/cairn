"""Proof (ticket 9484180b4ff4): a run of test_the_seal_announces_itself leaves no table behind.

Measured 2026-11-14 on akiendell: 24 ``seal_ann_<pid>_<n>_delivery`` tables stood on the cairn database
(owner bus, 0 rows, no cairn_scratch row, transit tables gone), and ONE run of
cairn/devices/tester/proofs/test_the_seal_announces_itself.py took the count from 21 to 24, three per
run, one for each fixture bus its teeth open.

ROOT CAUSE, bisected 2026-11-14 (not in this proof's fixture): on Windows ``store.process_start`` read
/proc, answered None for every pid, and ``minter_alive`` read the run's own live process as dead, so the
sweep the tester fires before every ``--seal`` (cli.py) dropped the run's live scratch families and their
registry rows mid-run; the bus re-created its tables unregistered; the exit then dropped each transit
table by name and left each ``_delivery`` companion with no row to find it by. The fix is db_domain's
(store._windows_process_start, its own ticket and proof); this proof is the detector that sits where the
leak was seen.

  1. After one full run of test_the_seal_announces_itself the number of tables named seal_ann_% is the
     same as before it (was +3 on Windows).
  2. A fixture bus whose process is KILLED mid-run leaves nothing behind once the next sweep runs: the
     dead minter's family, companion included, is dropped.

    python3 cairn/devices/tester/proofs/test_a_seal_announcement_run_leaves_no_table_behind.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"9484180b4ff4": {
    "1": "test_one_run_of_the_seal_announcement_proof_leaves_the_table_list_as_it_found_it",
    "2": "test_a_killed_fixture_bus_leaves_nothing_after_the_next_sweep",
}}

LEAKER = REPO / "cairn" / "devices" / "tester" / "proofs" / "test_the_seal_announces_itself.py"


def _tables(prefix: str) -> list[str]:
    from cairn.devices.db_domain.tools.client import store
    rows = store.query("select tablename from pg_tables where schemaname = 'public' and tablename like %s order by 1",
                       tables={}, params=(prefix + "%",), conn=store.connect())
    return [r["tablename"] for r in rows]


def test_one_run_of_the_seal_announcement_proof_leaves_the_table_list_as_it_found_it():
    before = _tables("seal_ann_")
    done = subprocess.run([sys.executable, str(LEAKER)], cwd=str(REPO), capture_output=True, text=True, timeout=600,
                          env={**os.environ, "PYTHONPATH": str(REPO)})
    assert done.returncode == 0, f"the proof under measurement did not run green: {done.stdout[-600:]}{done.stderr[-600:]}"
    after = _tables("seal_ann_")
    added = sorted(set(after) - set(before))
    assert not added, f"one run left {len(added)} table(s) behind: {added}"


_KILLED = ("import os, sys, time\n"
           "from cairn.devices.cairn.tools.scratch_bus.scratch_bus import scratch_bus\n"
           "with scratch_bus(sys.argv[1]) as bus:\n"
           "    bus._ensure()\n"
           "    print('READY', flush=True)\n"
           "    time.sleep(120)\n")


def test_a_killed_fixture_bus_leaves_nothing_after_the_next_sweep():
    from cairn.devices.db_domain.tools.client import store
    prefix = f"killed_bus_{os.getpid()}"
    child = subprocess.Popen([sys.executable, "-c", _KILLED, prefix], cwd=str(REPO), stdout=subprocess.PIPE,
                             text=True, env={**os.environ, "PYTHONPATH": str(REPO)})
    try:
        assert child.stdout.readline().strip() == "READY", "the fixture bus did not come up"
        assert _tables(prefix), "the fixture bus minted no table to kill"
    finally:
        child.kill()
        child.wait()
    store.sweep_scratch()
    left = _tables(prefix)
    assert not left, f"a killed fixture bus left {left} after the sweep"


TEETH = [test_one_run_of_the_seal_announcement_proof_leaves_the_table_list_as_it_found_it,
         test_a_killed_fixture_bus_leaves_nothing_after_the_next_sweep]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except BaseException as e:  # noqa: BLE001 - a proof reports, never hides
            failed += 1
            print(f"  RED  {t.__name__}: {type(e).__name__}: {str(e)[:500]}")
    print(f"{'GREEN' if not failed else 'RED'} - {len(TEETH) - failed}/{len(TEETH)} teeth")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

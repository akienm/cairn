"""Proof for ticket 201a37bf1613 — a scratch table cannot outlive its process.

Measured 2026-09-06: 9,773 tables in the cairn database, 454 MB, 21 of them live — every
other one minted by a proof under a ``_NONCE`` and left behind when the proof was killed
before its ``finally``. The falsifier is numbered, so six teeth (PROVES keys follow the
falsifier markers):

(1) the tester's seal sweeps first and the seal's evidence carries what it dropped, by name
    (``scratch_sweep``), the CLI prints the count, and ``run_proof`` REFUSES to seal without
    a sweep — a seal that says nothing about the sweep is refused, not recorded as zero;
(2) a minter killed with SIGKILL after minting (a forked child that never reaches its
    ``finally``) leaves its table AND the ``_delivery`` companion the bus registered, and
    the next ``sweep_scratch()`` drops both — gone from pg_tables and from both registries;
(3) a normal exit — and an exception exit — leaves neither table nor row;
(4) no proof under any ``proofs/`` drops a table by hand or mints its own nonce: a grep for
    the two spellings the leak was made of comes back empty;
(5) the proofs the move touched stay green: test_db_domain, test_bus, test_delivery,
    test_librarian_trees, test_inspector_nexus — each run as the tester runs it, exit 0;
(6) the sweep never touches a live table (the WRONG INTENT clause): the live set is the
    registry's non-scratch rows, never a name pattern — a live table NAMED like a scratch
    one, with a dead pid in its name and no ``cairn_scratch`` row, survives a sweep, and a
    companion cannot be registered under it.

A hollow build could not pass: tooth 2's drop is the sweep's own predicate over a pid that
is really dead; tooth 6's survival is the same predicate refusing a name; tooth 1's refusal
is the run door itself. Teeth 2 and 6 read the live database and assert INVARIANTS
(registry == pg_tables), never a snapshot.

    PYTHONPATH=. python3 cairn/devices/db_domain/proofs/test_scratch_cannot_outlive_its_process.py
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cairn.devices.db_domain import store  # noqa: E402
from cairn.devices.db_domain.store import OwnershipError  # noqa: E402

PROVES = {"201a37bf1613": {
    "1": "test_a_seal_sweeps_first_and_says_so",
    "2": "test_a_killed_minter_is_swept_with_its_delivery_companion",
    "3": "test_a_normal_exit_leaves_neither_table_nor_row",
    "4": "test_no_proof_drops_a_table_by_hand",
    "5": "test_the_moved_proofs_stay_green",
    "6": "test_the_sweep_never_touches_a_live_table",
}}

_OWNER = "tester"
_COLUMNS = {"x": "text"}
_MOVED = (
    "cairn/devices/db_domain/proofs/test_db_domain.py",
    "cairn/devices/cairn/machines/bus/proofs/test_bus.py",
    "cairn/devices/cairn/machines/bus/proofs/test_delivery.py",
    "cairn/devices/librarian/proofs/test_librarian_trees.py",
    "cairn/machines/build_inspector/proofs/test_inspector_nexus.py",
)
# the two spellings the leak was made of — built by concatenation so THIS file is not a hit
_LEAK_SPELLINGS = ("DROP " + "TABLE", "_NON" + "CE =")


# --- the harness ------------------------------------------------------------------------

def _pg_tables() -> set[str]:
    with store.connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        return {r[0] for r in cur.fetchall()}


def _registry_agrees() -> None:
    """The invariant every tooth leaves standing: cairn_owned names exactly pg_tables."""
    owned = {r["table_name"] for r in store.read(store._REGISTRY)}
    assert owned == _pg_tables(), (
        f"registry and pg_tables disagree — only in registry: {sorted(owned - _pg_tables())}, "
        f"only in pg: {sorted(_pg_tables() - owned)}")


def _fork_minter(prefix: str, *, with_bus: bool) -> tuple[int, str]:
    """Fork a child that mints a scratch table (and, with the bus, its receipt companion),
    reports the name up a pipe, then sleeps inside the ``with`` — never reaching its
    ``finally``. Returns (pid, table)."""
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:  # the child
        os.close(r)
        try:
            from cairn.devices.cairn.machines.bus.bus import (
                _BUS_OWNER, _TRAFFIC_COLUMNS, BusDevice)
            owner, cols = (_BUS_OWNER, _TRAFFIC_COLUMNS) if with_bus else (_OWNER, _COLUMNS)
            with store.scratch(owner, prefix, cols) as table:
                if with_bus:
                    BusDevice(table=table, device_id=f"{prefix}_rider").read()
                os.write(w, table.encode())
                os.close(w)
                signal.pause()
        finally:
            os._exit(0)
    os.close(w)
    table = os.read(r, 256).decode()
    os.close(r)
    assert table, "the child minted nothing"
    return pid, table


def _kill(pid: int) -> None:
    os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)


def _dead_pid() -> int:
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
    return pid


def _tiny_proof(dirpath: Path) -> Path:
    """A one-line green proof under a scratch component: ``<d>/proofs/test_tiny_201a.py``,
    so its seal lands at ``<d>/validations/test_tiny_201a.json`` the way every seal does."""
    (dirpath / "proofs").mkdir()
    p = dirpath / "proofs" / "test_tiny_201a.py"
    p.write_text("print('ok test_tiny')\n", encoding="utf-8")
    return p


# --- the teeth --------------------------------------------------------------------------

def test_a_seal_sweeps_first_and_says_so() -> None:
    from cairn.devices.tester.device import TesterDevice
    from cairn.devices.tester.scratch_sweep import sweep
    with tempfile.TemporaryDirectory(prefix="201a-seal-") as d:
        tiny = _tiny_proof(Path(d))
        tester = TesterDevice()
        # a seal without a sweep is refused at the run door, like a seal without a sink
        try:
            tester.run_proof(tiny, sink="validations", caller="proof 201a")
            raise AssertionError("run_proof sealed without a scratch sweep")
        except ValueError as exc:
            assert "scratch_sweep" in str(exc), exc
        # a run that seals nothing records that it swept nothing — never a made-up zero
        rec = tester.run_proof(tiny, sink="none", caller="proof 201a")
        assert rec["evidence"]["scratch_sweep"] == {"skipped": "the caller sealed nothing and swept nothing"}, rec["evidence"]
        # the seal's evidence carries what the sweep dropped, by name
        pid, table = _fork_minter("scratch_seal", with_bus=False)
        _kill(pid)
        swept = sweep()
        assert swept.get("dropped", 0) >= 1 and table in swept["tables"], swept
        rec = tester.run_proof(tiny, sink="validations", caller="proof 201a", scratch_sweep=swept)
        assert rec["evidence"]["scratch_sweep"] == swept, rec["evidence"]
        sealed = json.loads((Path(d) / "validations" / "test_tiny_201a.json").read_text())[-1]
        assert sealed["evidence"]["scratch_sweep"]["tables"] == swept["tables"], sealed["evidence"]
        # the CLI names the count on the way past
        pid, table = _fork_minter("scratch_cli", with_bus=False)
        _kill(pid)
        r = subprocess.run([sys.executable, "-m", "cairn.devices.tester.cli", "--seal", str(tiny)],
                           cwd=str(ROOT), env={**os.environ, "PYTHONPATH": str(ROOT)},
                           capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, (r.stdout, r.stderr)
        line = next((ln for ln in r.stdout.splitlines() if ln.strip().startswith("swept ")), None)
        assert line and table in line and "1 scratch table(s)" in line, r.stdout
    assert table not in _pg_tables() and not store.is_scratch(table)
    print("ok test_a_seal_sweeps_first_and_says_so")


def test_a_killed_minter_is_swept_with_its_delivery_companion() -> None:
    pid, table = _fork_minter("scratch_kill", with_bus=True)
    companion = f"{table}_delivery"
    try:
        assert {table, companion} <= _pg_tables(), "the bus did not create both tables"
        rows = {r["table_name"]: r for r in store.scratch_rows()}
        assert table in rows and rows[table]["pid"] == pid and rows[table]["companion_of"] is None
        assert companion in rows and rows[companion]["pid"] == pid and rows[companion]["companion_of"] == table, rows.get(companion)
        # alive: the sweep leaves the family alone
        report: list[str] = []
        store.sweep_scratch(report=report)
        assert table not in report and companion not in report, report
        assert {table, companion} <= _pg_tables()
    finally:
        _kill(pid)
    # dead: the next sweep drops both, by pid, and names them
    report = []
    n = store.sweep_scratch(report=report)
    assert n >= 2 and table in report and companion in report, (n, report)
    left = _pg_tables()
    assert table not in left and companion not in left, "a killed minter's tables survived the sweep"
    assert not store.is_scratch(table) and not store.is_scratch(companion)
    assert store.owner_of(table) is None and store.owner_of(companion) is None
    _registry_agrees()
    print("ok test_a_killed_minter_is_swept_with_its_delivery_companion")


def test_a_normal_exit_leaves_neither_table_nor_row() -> None:
    with store.scratch(_OWNER, "scratch_exit", _COLUMNS) as table:
        assert table in _pg_tables() and store.is_scratch(table) and store.owner_of(table) == _OWNER
        store.write(table, _OWNER, {"x": "lived"})
    assert table not in _pg_tables() and not store.is_scratch(table) and store.owner_of(table) is None
    # an exception exit is an exit
    try:
        with store.scratch(_OWNER, "scratch_raise", _COLUMNS) as table2:
            raise RuntimeError("the proof blew up mid-table")
    except RuntimeError:
        pass
    assert table2 not in _pg_tables() and not store.is_scratch(table2) and store.owner_of(table2) is None
    _registry_agrees()
    print("ok test_a_normal_exit_leaves_neither_table_nor_row")


def test_no_proof_drops_a_table_by_hand() -> None:
    offenders: dict[str, list[str]] = {}
    for path in sorted((ROOT / "cairn").rglob("proofs/*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = [s for s in _LEAK_SPELLINGS if s in text]
        if hits:
            offenders[str(path.relative_to(ROOT))] = hits
    assert not offenders, (
        f"{len(offenders)} proof(s) still mint their own nonce or drop a table by hand — "
        f"the leak's two spellings: {json.dumps(offenders, indent=1)}")
    print("ok test_no_proof_drops_a_table_by_hand")


def test_the_moved_proofs_stay_green() -> None:
    red = {}
    for rel in _MOVED:
        r = subprocess.run([sys.executable, str(ROOT / rel)], cwd=str(ROOT),
                           env={**os.environ, "PYTHONPATH": str(ROOT)},
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            red[rel] = (r.stdout + r.stderr)[-800:]
    assert not red, f"moved proofs red: {json.dumps(red, indent=1)}"
    print(f"ok test_the_moved_proofs_stay_green ({len(_MOVED)} green)")


def test_the_sweep_never_touches_a_live_table() -> None:
    # a LIVE table wearing a scratch name with a DEAD pid in it, and no cairn_scratch row
    dead = _dead_pid()
    live = f"live_{dead}_{store.scratch_name('x').rsplit('_', 1)[1]}"
    store.create_owned_table(live, _OWNER, _COLUMNS)
    try:
        assert live in _pg_tables() and not store.is_scratch(live)
        pid, table = _fork_minter("scratch_beside", with_bus=False)
        _kill(pid)
        report: list[str] = []
        store.sweep_scratch(report=report)
        assert table in report and live not in report, report
        assert live in _pg_tables() and store.owner_of(live) == _OWNER, "the sweep dropped a live table by its NAME"
        # a companion of a live table is a live table — refused
        try:
            store.register_scratch_companion(live, f"{live}_delivery")
            raise AssertionError("a companion was registered under a live table")
        except OwnershipError:
            pass
        assert not store.is_scratch(f"{live}_delivery")
        _registry_agrees()
    finally:
        store.drop_table(live, _OWNER)
    assert live not in _pg_tables()
    print("ok test_the_sweep_never_touches_a_live_table")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

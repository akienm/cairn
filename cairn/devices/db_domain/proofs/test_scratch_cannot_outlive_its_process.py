"""Proof for ticket 201a37bf1613 — a scratch table cannot outlive its process.

Measured 2026-09-06: 9,773 tables in the cairn database, 454 MB, 21 of them live — every
other one minted by a proof under a ``_NONCE`` and left behind when the proof was killed
before its ``finally``. The falsifier is numbered, so six teeth (PROVES keys follow the
falsifier markers):

(1) the tester's seal sweeps first and the seal's evidence carries what it dropped, by name
    (``scratch_sweep``), the CLI prints the count, and ``run_proof`` REFUSES to seal without
    a sweep — a seal that says nothing about the sweep is refused, not recorded as zero;
    and the ONE-TIME sweep that cleared the leak (migrate_scratch_sweep.py), driven over a
    fake connection, drops nothing without --drop, never a LIVE name with it, and refuses
    outright when any nonce pid is alive;
(2) a minter killed with SIGKILL after minting (a child process that never reaches its
    ``finally``) leaves its table AND a ``_delivery`` companion registered beside it
    (store.register_scratch_companion, the call the bus's _ensure makes), and
    the next ``sweep_scratch()`` drops both — gone from pg_tables and from both registries;
(3) a normal exit — and an exception exit — leaves neither table nor row;
(4) no proof under any ``proofs/`` drops a table by hand or mints its own nonce: an AST
    question for the two shapes the leak was made of (an ``execute`` whose SQL drops a table,
    an assignment to ``_NONCE``) comes back empty — a mention in a string is not a catch
    (ticket 74b4209b71ee; the text grep this replaced redded an injection payload);
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

import ast
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Ticket cf32e6f141e0. Measured on Windows: timed out at the default 120 s, finished in 129 s
# wall at --timeout 540. 300 s is wall plus margin; re-measure if Linux reads higher.
PROOF_TIMEOUT_S = 300

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cairn.devices.db_domain.tools.client import store  # noqa: E402
from cairn.devices.db_domain.tools.client.store import OwnershipError  # noqa: E402

PROVES = {"201a37bf1613": {
    "1": "test_a_seal_sweeps_first_and_says_so",
    "2": "test_a_killed_minter_is_swept_with_its_delivery_companion",
    "3": "test_a_normal_exit_leaves_neither_table_nor_row",
    "4": "test_no_proof_drops_a_table_by_hand",
    "5": "test_the_moved_proofs_stay_green",
    "6": "test_the_sweep_never_touches_a_live_table",
},
    # 7bc784d5a7de clause 2: the killed minter mints its companion through the store alone and
    # this tooth stays green (its reach is red-checked in test_db_domain_proofs_reach_no_device.py)
    "7bc784d5a7de": {"2": "test_a_killed_minter_is_swept_with_its_delivery_companion"},
    # aa750de17382: the minter and the dead pid are subprocess children, so the teeth run where
    # os.fork does not exist; clause 2 takes os.fork away and runs them
    "aa750de17382": {"1": "test_a_killed_minter_is_swept_with_its_delivery_companion",
                     "2": "test_the_minters_run_where_os_has_no_fork",
                     # not a falsifier clause: declared so the hollow reader measures this tooth
                     "real_minter": "test_a_killed_minters_real_process_is_dead"},
}

_OWNER = "tester"
_COLUMNS = {"x": "text"}
_MOVED = (
    "cairn/devices/db_domain/proofs/test_db_domain.py",
    "cairn/devices/cairn/machines/bus/proofs/test_bus.py",
    "cairn/devices/cairn/machines/bus/proofs/test_delivery.py",
    "cairn/devices/librarian/proofs/test_librarian_trees.py",
)
# test_inspector_nexus.py left this list with ticket 93fa3e3a6199: it berths in codemother now, and
# her proof's green is her seal's, not this proof's to run (RULE 1). 201a37bf1613/5 measures four.
# the two shapes the leak was made of, asked of the AST (ticket 74b4209b71ee): a string that only
# MENTIONS them — an injection payload, a docstring — is not a hand drop.
_DROP_TABLE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
_EXECUTES = ("execute", "executemany")


def _hand_leaks(src: str) -> list[str]:
    """Every hand drop and hand nonce in ``src``, as ``'<shape> @ <line>'``. A hand drop is a call
    to ``.execute``/``.executemany`` whose first argument holds a string saying DROP TABLE; a hand
    nonce is an assignment to the name ``_NONCE``. A source that does not parse is itself an
    offence: a tooth that cannot read a proof has not measured it."""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"unparseable @ {e.lineno}"]
    hits = []
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in _EXECUTES and n.args
                and any(isinstance(c, ast.Constant) and isinstance(c.value, str)
                        and _DROP_TABLE.search(c.value) for c in ast.walk(n.args[0]))):
            hits.append(f"execute DROP TABLE @ {n.lineno}")
        targets = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AnnAssign) else []
        if any(isinstance(t, ast.Name) and t.id == "_NONCE" for t in targets):
            hits.append(f"_NONCE assigned @ {n.lineno}")
    return hits


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


_CHILDREN: dict[int, subprocess.Popen] = {}


def _fork_minter(prefix: str, *, with_companion: bool) -> tuple[int, str]:
    """Start a child process that mints a scratch table (and, with_companion, a registered
    _delivery companion), prints the name, then sleeps inside the ``with``, never reaching its
    exit. Returns (pid, table). A subprocess, not os.fork, so the teeth run on Windows, where
    os.fork does not exist (ticket aa750de17382); the name stays, which
    test_db_domain_proofs_reach_no_device.py reads."""
    # The companion is minted through db_domain's own store — create_owned_table, then
    # register_scratch_companion, the same two calls the bus's _ensure makes for its receipt
    # table — so this tooth about db_domain's sweep reaches no device (RULE 1, ticket
    # 7bc784d5a7de).
    child_src = (
        "import os, sys, time\n"
        "from cairn.devices.db_domain.tools.client import store\n"
        "owner, prefix, with_companion = sys.argv[1], sys.argv[2], sys.argv[3] == '1'\n"
        "cols = {'x': 'text'}\n"
        "with store.scratch(owner, prefix, cols) as table:\n"
        "    if with_companion:\n"
        "        store.create_owned_table(f'{table}_delivery', owner, cols)\n"
        "        store.register_scratch_companion(table, f'{table}_delivery')\n"
        "    print(os.getpid(), table, flush=True)\n"
        "    time.sleep(600)\n"
    )
    child = subprocess.Popen([sys.executable, "-c", child_src, _OWNER, prefix,
                              "1" if with_companion else "0"], cwd=str(ROOT),
                             env={**os.environ, "PYTHONPATH": str(ROOT)},
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    said = child.stdout.readline().split()
    if len(said) != 2:
        child.kill()
        _, err = child.communicate(timeout=60)
        raise AssertionError(f"the child minted nothing: {err[-400:]}")
    # The pid the minter REPORTS, not Popen's: on Windows a venv's python.exe is a launcher
    # shim, so Popen.pid is the shim and the registry row carries the real interpreter's
    # os.getpid() (measured 2026-11-19 on akiendell: row pid 13296, Popen pid 12792).
    pid, table = int(said[0]), said[1]
    _CHILDREN[pid] = child
    return pid, table


def _running(pid: int) -> bool:
    """Is ``pid`` a running process — read without the store, which is what this proof measures.
    (Never os.kill(pid, 0) on Windows: any signal there is TerminateProcess.)"""
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
                             capture_output=True, text=True).stdout
        return f'"{pid}"' in out
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _kill(pid: int) -> None:
    """Kill the REAL minter (its reported pid) and the Popen handle (the shim, on Windows),
    then wait until the real process is gone, so the next sweep reads a dead minter."""
    child = _CHILDREN.pop(pid)
    try:
        os.kill(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
    except OSError:
        pass
    child.kill()
    child.communicate(timeout=60)
    deadline = time.time() + 30
    while _running(pid) and time.time() < deadline:
        time.sleep(0.1)


def _dead_pid() -> int:
    """The pid of a child that has already exited (a subprocess, so Windows runs it too)."""
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    assert child.wait(timeout=60) == 0, "the short-lived child failed"
    return child.pid


class _FakeConn:
    """A connection the one-time sweep can plan and drop over without a database: pg_tables
    answers ``tables``, and every composed statement (a DROP or a registry DELETE) is kept
    so the tooth can read exactly what the sweep would have done."""

    def __init__(self, tables: list[str]) -> None:
        self.tables, self.composed, self._last = sorted(tables), [], ""

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None

    def execute(self, stmt, params=None) -> None:
        if isinstance(stmt, str):
            self._last = stmt
        else:
            self.composed.append(repr(stmt))
        self.rowcount = 0

    def fetchall(self):
        return [(t,) for t in self.tables]

    def fetchone(self):
        return ("0 bytes",)

    def close(self) -> None:
        return None


def _the_one_time_sweep_keeps_the_live_set_and_refuses_a_live_pid() -> None:
    """Clause (1)'s one-time sweep (migrate_scratch_sweep.py), driven over a fake connection
    so it can never drop a real table: without --drop it drops nothing; with --drop it drops
    the nonced and the unnamed but never a LIVE name; and a nonce whose pid is alive refuses
    the whole run, --drop or not — a scratch table of a live process is not a leak."""
    import contextlib
    import io
    import types
    from cairn.devices.db_domain import migrate_scratch_sweep as mig
    live = sorted(mig.LIVE)[:3]
    dead_nonced, unnamed = f"leak_{_dead_pid()}_123456", "fixture_without_nonce"
    alive_nonced = f"leak_{os.getpid()}_123456"

    def drive(tables: list[str], argv: list[str]) -> tuple[int, _FakeConn, str]:
        conn = _FakeConn(tables)
        fake = types.SimpleNamespace(connect=lambda: conn, process_start=store.process_start,
                                     _REGISTRY=store._REGISTRY)
        real, mig.store = mig.store, fake
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                code = mig.main(argv)
        finally:
            mig.store = real
        return code, conn, out.getvalue()

    code, conn, out = drive([*live, dead_nonced, unnamed], [])
    assert code == 0 and conn.composed == [] and "dry run" in out, (code, conn.composed, out)
    code, conn, out = drive([*live, dead_nonced, unnamed], ["--drop"])
    dropped = [c for c in conn.composed if "DROP" in c]
    assert code == 0 and len(dropped) == 2, (code, conn.composed)
    assert any(repr(dead_nonced) in c for c in dropped) and any(repr(unnamed) in c for c in dropped), dropped
    assert not any(repr(n) in c for c in conn.composed for n in live), "the one-time sweep touched a LIVE name"
    code, conn, out = drive([*live, dead_nonced, alive_nonced], ["--drop"])
    assert code == 2 and conn.composed == [] and "REFUSING" in out, (code, conn.composed, out)


# --- the teeth --------------------------------------------------------------------------

def test_a_seal_sweeps_first_and_says_so() -> None:
    # The tester half of this clause — the run door's refusal, the skipped and swept evidence,
    # the CLI's 'swept' line — measures the tester, so it is the tester's own tooth now
    # (ticket 67b78ae59c1d, RULE 1): cairn/devices/tester/proofs/test_the_teeth_that_measure_the_tester.py.
    # What stays is db_domain's half: the ONE-TIME sweep clause (1) counts — the migration that
    # cleared the leak.
    _the_one_time_sweep_keeps_the_live_set_and_refuses_a_live_pid()
    print("ok test_a_seal_sweeps_first_and_says_so")


def test_a_killed_minter_is_swept_with_its_delivery_companion() -> None:
    pid, table = _fork_minter("scratch_kill", with_companion=True)
    companion = f"{table}_delivery"
    try:
        assert {table, companion} <= _pg_tables(), "the minter did not create both tables"
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
        hits = _hand_leaks(path.read_text(encoding="utf-8", errors="replace"))
        if hits:
            offenders[str(path.relative_to(ROOT))] = hits
    assert not offenders, (
        f"{len(offenders)} proof(s) still mint their own nonce or drop a table by hand — "
        f"the leak's two shapes: {json.dumps(offenders, indent=1)}")
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


def test_the_minters_run_where_os_has_no_fork() -> None:
    """aa750de17382 clause 2: with os.fork taken away, as on Windows, _fork_minter still mints a
    scratch table the next sweep drops after a kill, and _dead_pid still names an exited pid. A
    forking helper reds here with AttributeError, on Linux as on Windows."""
    fork = getattr(os, "fork", None)
    if fork is not None:
        del os.fork
    try:
        pid, table = _fork_minter("scratch_nofork", with_companion=False)
        dead = _dead_pid()
    finally:
        if fork is not None:
            os.fork = fork
    try:
        assert store.is_scratch(table), table
        assert dead > 0 and dead != os.getpid(), dead
    finally:
        _kill(pid)
    report: list[str] = []
    store.sweep_scratch(report=report)
    assert table in report and table not in _pg_tables() and not store.is_scratch(table), report
    _registry_agrees()
    print("ok test_the_minters_run_where_os_has_no_fork")


def test_the_sweep_never_touches_a_live_table() -> None:
    # a LIVE table wearing a scratch name with a DEAD pid in it, and no cairn_scratch row
    dead = _dead_pid()
    live = f"live_{dead}_{store.scratch_name('x').rsplit('_', 1)[1]}"
    store.create_owned_table(live, _OWNER, _COLUMNS)
    try:
        assert live in _pg_tables() and not store.is_scratch(live)
        pid, table = _fork_minter("scratch_beside", with_companion=False)
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


def test_a_killed_minters_real_process_is_dead() -> None:
    """aa750de17382: _fork_minter reports the minter's OWN os.getpid(), and _kill ends THAT
    process, not only the Popen handle. On Windows a venv's python.exe is a launcher shim whose
    pid is not the minter's, so a kill of the handle alone can leave the real minter alive and
    the sweep tooth measures nothing. Read here by a liveness probe that is not the store."""
    pid, table = _fork_minter("scratch_realpid", with_companion=False)
    assert _CHILDREN[pid].pid != pid or os.name != "nt", "on Windows the handle is the shim, not the minter"
    assert _running(pid), "the reported pid is not a running process"
    assert store.is_scratch(table) and {r["table_name"]: r for r in store.scratch_rows()}[table]["pid"] == pid
    _kill(pid)
    assert not _running(pid), f"the real minter {pid} survived the kill"
    report: list[str] = []
    store.sweep_scratch(report=report)
    assert table in report and not store.is_scratch(table), report
    print("ok test_a_killed_minters_real_process_is_dead")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

"""Proof for ticket b69e5c658b1c — the bus's serve() returns only after its backlog pass.

MEASURED 2026-11-08 while building 7bc784d5a7de: db_domain's registry invariant redded on 50
public tables in pg_tables with no cairn_owned row (48 bus_stop_proof_*, 2 bus_proc_*), and one
run of test_every_stop_records_its_cause.py added two more. serve() started its bus-backlog
thread as a daemon and never joined it; when serve_forever returned at once, the scratch exit
dropped the bus's tables while the pass (return_the_backlog -> undelivered -> _ensure) was
re-creating them, with no owner row. With a join before final_flush the same run added none.

  1. test_a_driven_stop_leaves_no_orphan: the stop proof's 'clean' and 'raise' drivers add no
     ownerless bus_* table (any it adds are dropped again, so a red run leaves the database as
     it found it);
  2. test_serve_joins_its_backlog_before_final_flush: serve()'s source joins before it flushes;
  3. test_no_bus_table_lacks_an_owner: no public bus_* table in pg_tables lacks an owner row.

The stop proof is loaded from its file at call time, the house way of reusing a sibling's
driver; db_domain is reached through its store, the bus's own door to the database.

    python3 cairn/devices/cairn/machines/bus/proofs/test_serve_returns_after_its_threads.py
"""
from __future__ import annotations

import ast
import importlib.util
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"b69e5c658b1c": {
    "1": "test_a_driven_stop_leaves_no_orphan",
    "2": "test_serve_joins_its_backlog_before_final_flush",
    "3": "test_no_bus_table_lacks_an_owner",
}}

_HERE = Path(__file__).resolve().parent
_STOP_PROOF = _HERE / "test_every_stop_records_its_cause.py"
_SERVER = _HERE.parent / "server.py"
_DROPPER = "bus"  # drop_table gates only a recorded owner; these have none

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""), flush=True)
    if not ok:
        FAILURES.append(name)


def _store():
    from cairn.devices.db_domain.tools.client import store
    return store


def _ownerless() -> set[str]:
    store = _store()
    with store.connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
                    "AND tablename LIKE %s", ("bus\\_%",))
        names = [r[0] for r in cur.fetchall()]
    return {t for t in names if store.owner_of(t) is None}


def _stop_proof():
    spec = importlib.util.spec_from_file_location("_bus_stop_proof", _STOP_PROOF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_driven_stop_leaves_no_orphan() -> None:
    before = _ownerless()
    stop = _stop_proof()
    for mode in ("clean", "raise"):
        stop._driven(mode)
    new = _ownerless() - before
    store = _store()
    for t in sorted(new):
        store.drop_table(t, _DROPPER)
    assert not new, f"a driven stop left {len(new)} ownerless table(s): {sorted(new)}"


def test_serve_joins_its_backlog_before_final_flush() -> None:
    text = _SERVER.read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(text))
              if isinstance(n, ast.FunctionDef) and n.name == "serve")
    src = ast.get_source_segment(text, fn) or ""
    join, flush = src.find(".join("), src.find("final_flush(bus, home)")
    assert flush >= 0, "serve() no longer calls final_flush(bus, home)"
    assert 0 <= join < flush, "serve() does not join its backlog thread before final_flush"


def test_no_bus_table_lacks_an_owner() -> None:
    left = sorted(_ownerless())
    assert not left, f"{len(left)} ownerless bus table(s) stand, e.g. {left[:5]}"


def main() -> int:
    os.chdir(_REPO)
    for tooth in (test_a_driven_stop_leaves_no_orphan,
                  test_serve_joins_its_backlog_before_final_flush,
                  test_no_bus_table_lacks_an_owner):
        try:
            tooth()
            check(tooth.__name__, True)
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"{type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}",
          flush=True)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""ONE-TIME SWEEP of the tables that leaked before the store had a word for scratch.

Ticket 201a37bf1613 (Akien 2026-09-06: "we have 9075 tables? wow! we should clear those
up."). Run once, by hand, from the repo root:

    PYTHONPATH=. python3 cairn/devices/db_domain/migrate_scratch_sweep.py            # measure only
    PYTHONPATH=. python3 cairn/devices/db_domain/migrate_scratch_sweep.py --drop     # do it

WHAT IT KEEPS: the live set, named — measured 2026-09-18 as the tables in `cairn` that
carry no per-run nonce and that a running component owns (``LIVE`` below; 20 tables, the
ticket's list of 17 plus cairn_threads, chart_verdict_nodes and codemother_root_nodes,
born since the ticket was cast). A keep list is the safe direction for a one-shot: the
sweep that runs forever (``store.sweep_scratch``) reads the registry and never a name.

WHAT IT DROPS: every other table in `cairn`, and its cairn_owned row — after asserting
that NO pid carried in any nonce is alive. Every leaked table's pid was dead when the
ticket was cast (0 alive of 8,270) and this refuses to run if that has changed. Tables
that are neither live nor nonce-shaped (an old fixture without a nonce, e.g.
``test_chat_pane_transit``) are listed under their own heading so the reader sees them
go, rather than folded into the count.

Prints the count dropped and the database size before and after — the numbers the ticket's
deposits carry.
"""
from __future__ import annotations

import re
import sys

from psycopg2 import sql

from cairn.devices.db_domain import store

LIVE = frozenset({
    "cairn_owned", "cairn_scratch", "inference_calls",
    "bus_traffic", "bus_traffic_delivery",
    "build_inspector_failures_nodes",
    "chart_constrain_nodes", "chart_decompose_nodes", "chart_hypothesize_nodes",
    "chart_orient_nodes", "chart_survey_nodes", "chart_triage_nodes",
    "chart_validate_nodes", "chart_verdict_nodes",
    "librarian_nodes", "orient_corrections_nodes", "codemother_root_nodes",
    "cairn_links", "cairn_nodes", "cairn_embeddings", "cairn_threads",
})

# `<word>_<pid>_<HHMMSS[ffffff]>` — the proofs' nonce grammar; the pid is what we check
_PID_NONCE = re.compile(r"_(\d{1,7})_(\d{6,12})(?:_|$)")


def _tables(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1")
        return [r[0] for r in cur.fetchall()]


def _size(conn) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        return cur.fetchone()[0]


def plan(conn) -> dict:
    names = _tables(conn)
    keep = [n for n in names if n in LIVE]
    drop_nonced, drop_other, pids = [], [], set()
    for n in names:
        if n in LIVE:
            continue
        m = _PID_NONCE.search(n)
        if m:
            drop_nonced.append(n)
            pids.add(int(m.group(1)))
        else:
            drop_other.append(n)
    alive = sorted(p for p in pids if store.process_start(p) is not None)
    return {"total": len(names), "keep": keep, "drop_nonced": drop_nonced,
            "drop_other": drop_other, "pids": len(pids), "alive": alive}


def main(argv: list[str]) -> int:
    do_drop = "--drop" in argv
    conn = store.connect()
    try:
        before = _size(conn)
        p = plan(conn)
        print(f"tables: {p['total']}  keep: {len(p['keep'])}  nonced-to-drop: {len(p['drop_nonced'])}"
              f"  other-to-drop: {len(p['drop_other'])}  nonce pids: {p['pids']}  alive: {p['alive']}")
        print(f"size before: {before}")
        print("keeping: " + ", ".join(sorted(p["keep"])))
        missing = sorted(LIVE - set(p["keep"]))
        if missing:
            print(f"live-set names not present (fine, nothing to keep): {', '.join(missing)}")
        if p["drop_other"]:
            print("dropping (no nonce, not live): " + ", ".join(p["drop_other"]))
        if p["alive"]:
            print(f"REFUSING: {len(p['alive'])} nonce pid(s) alive: {p['alive']} — a scratch "
                  "table of a live process is not a leak; wait or stop it")
            return 2
        if not do_drop:
            print("dry run — nothing dropped (pass --drop)")
            return 0
        dropped = 0
        with conn.cursor() as cur:
            for n in [*p["drop_nonced"], *p["drop_other"]]:
                cur.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(n)))
                cur.execute(
                    sql.SQL("DELETE FROM {reg} WHERE table_name = %s").format(
                        reg=sql.Identifier(store._REGISTRY)), (n,))
                dropped += 1
            # registry rows whose table is already gone (dropped by hand, never deregistered)
            cur.execute(
                sql.SQL("DELETE FROM {reg} WHERE table_name NOT IN "
                        "(SELECT tablename FROM pg_tables WHERE schemaname = 'public')").format(
                    reg=sql.Identifier(store._REGISTRY)))
            orphan_rows = cur.rowcount
            cur.execute("VACUUM")  # autocommit connection: VACUUM is legal here
        after = _size(conn)
        remaining = _tables(conn)
        print(f"dropped: {dropped} table(s); orphan registry rows removed: {orphan_rows}")
        print(f"remaining: {len(remaining)} table(s): {', '.join(remaining)}")
        print(f"size after: {after}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

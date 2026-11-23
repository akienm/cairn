"""db_domain — the ONE path to durable state, and the owner-gate every write passes.

THE FOUNDING LAW (MAP.md:367, generalizing UU's button pattern; Law 6): **every table
has exactly one owner — a class, an instance, or a human — and the owner gates every
write to it.** The owner is declared at creation and recorded in metadata; an ownerless
table cannot come into existence. Tables are provisioned only through here.

WHY THIS IS PHYSICS, NOT POLICY (Law 4). "Everything has an owner" is a rule that matters,
so it is enforced by the schema, not by a convention each writer remembers: the owner
registry carries `CHECK (owner <> '')`, so an ownerless row is rejected by Postgres
itself, and `create_owned_table` is the only door to a table — a table that skipped the
registry did not come from db_domain, and db_domain is the only module that holds a
connection. The gate is the kernel's, not the caller's goodwill.

CONNECTION (ratified by Akien, 2026-07-18): peer auth over the Postgres **Unix socket**,
as the OS user, to a dedicated `cairn` database. No password, no vault yet — the vault
(credentials composed at connect-time, MAP.md:361) is a later need, deferred until a
non-OS-user instance or a remote pulls it. The socket is a FILE, so it SURVIVES a
`--unshare-net` seal (cairn/devices/tester/isolation.py): a sealed build has no route to 5432 over
the network, yet still reaches the DB — *only* through this domain. That asymmetry is the
sole-route half of CLAUDE.md's "port 5432 is reached only through db_domain".

ONE-TIME PROVISIONING (instance setup, not class-space code — it is privileged and
machine-specific): the OS-named login role must exist. `CREATE ROLE <you> LOGIN CREATEDB;`
run once as the postgres superuser. Given that role, db_domain creates the `cairn`
database itself (`ensure_database`), so the manual surface is exactly one role.

WHAT DURABLE STATE LIVES HERE (narrowed 2026-07-22): the relational / graph-tree data —
the trees the database is uniquely good at. VALIDATIONS used to be db_domain's first
consumer; they MOVED OUT to beside-code git-JSON, next to the ``proofs/`` they seal
(``cairn/tools/validation_store/validation_store.py``; ruling in tickets/charter-state-history-split.json
child b). Build-provenance is knowledge frozen at PROVED — it belongs beside the code it
explains (Law 5), and git is already durable, so a truth record no longer sits in exactly
one un-backed place. The database ends up holding ONLY what is genuinely relational.

OPEN EDGES, filed not faked (round-three: the sole-route/owner-gate physics first):
  - Reads are not owner-gated here — Law 6 gates WRITES; a read gate (row-level, per
    consumer) is a later need no consumer has pulled yet.
  - Connect-per-operation, no pool — correctness now, pooling when a real load pulls it.
  - The tester import-scan that reds any OTHER module opening a connection (making
    "sole path" physics rather than convention) is the tester's later tooth, not built
    here; today db_domain is the sole connection by construction.
  - The `cairn_owned` registry records ownership; ownership TRANSFER and delegated access
    (Law 6's "only through the owner's gate") are later capabilities.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

# Peer auth over the Unix socket: host is the socket directory, role is the OS user, and
# the database is Cairn's own. A socket is a file — it crosses a network namespace freely.
SOCKET_DIR = "/var/run/postgresql"
# Where there is no socket (Windows) the route is TCP loopback, and Postgres demands a password
# there. The secret berths in db_domain's instance space (Akien 2026-11-08, open-d0399bd1d6f1:
# "the answer is in ~/.cairn/devices/<device>"); this module names the PATH and never a secret —
# libpq reads its own pgpass format from it, and ignores a passfile that is absent.
_TCP_HOST, _TCP_PORT = "127.0.0.1", 5432
_SOCKET_FILE = ".s.PGSQL.5432"
# The box's own instance root, derived the way address derives it and independent of import order: a proof
# may repoint address.ROOTS["instance"] at a scratch dir, and a credential the scratch dir does not hold is
# still the box's (ticket fc4bb2062253).
from cairn.tools.base.address import _INSTANCE as _STARTUP_INSTANCE  # noqa: E402 — address owns the spelling
DB_NAME = "cairn"
# A TEST RUN WRITES TO ITS OWN DATABASE (ticket e4fd7f28faaf, outline 4.3.1.5.1.5.2). The tester
# hands every subject its run id in this variable; it is read as a STRING, so this tool imports
# nothing of the tester (RULE 1). Under it every write lands in TESTING_DB_NAME; reads go to a
# table the run created there, else to live through a read-only connection (testing first, live
# underneath, at table grain).
TESTING_DB_NAME = "cairn_testing"
_TEST_ID_ENV = "CAIRN_TESTER_TEST_ID"
_BOOTSTRAP_DB = "postgres"  # the always-present database we connect to only to create ours

# db_domain owns its own metadata table — the registry that makes ownership a fact.
_REGISTRY = "cairn_owned"
# ...and the registry of SCRATCH: tables born through ``scratch()`` that belong to one
# process for exactly its lifetime (ticket 201a37bf1613). A row here is what makes a
# table sweepable; a name is never the predicate.
_SCRATCH = "cairn_scratch"
_OWN_REGISTRIES = frozenset({_REGISTRY, _SCRATCH})  # db_domain's bookkeeping: a test run reads its own


class OwnershipError(Exception):
    """A write or a creation that the owner-gate refused. Loud, never swallowed (Law 7)."""


# ── connection: the one door to 5432 ─────────────────────────────────────────


def _conn_args() -> dict:
    """Where to dial, chosen by whether the socket FILE exists (ticket 3dc005de27cf).

    The socket dir is CAIRN_PG_SOCKET_DIR (default SOCKET_DIR, the name bin/cairn reads), read
    at call time. Socket present: peer auth over it, unchanged. Absent: TCP loopback, with the
    passfile in db_domain's instance space. Pure apart from the one existence check.
    """
    sock = os.environ.get("CAIRN_PG_SOCKET_DIR", SOCKET_DIR)
    if os.path.exists(os.path.join(sock, _SOCKET_FILE)):
        return {"host": sock}
    from cairn.tools.base.address import instance_path
    passfile = instance_path("db_domain", 0) / "pgpass"
    # Fallbacks in order: the root the process started with (a proof repointed ROOTS in-process,
    # fc4bb2062253), then the box a scratch-HOME child was moved off (scratch.home_env names it
    # in CAIRN_SCRATCH_BOX_INSTANCE; on Windows that child's own home is the scratch, 6c3f73bde8fd).
    # The variable is read as a string so this module imports nothing from the scratch tool.
    box = os.environ.get("CAIRN_SCRATCH_BOX_INSTANCE")
    for root in (_STARTUP_INSTANCE, Path(box) if box else None):
        if passfile.is_file() or root is None:
            break
        candidate = Path(root) / "devices" / "db_domain" / "0" / "pgpass"
        if candidate.is_file():
            passfile = candidate
    return {"host": _TCP_HOST, "port": _TCP_PORT, "passfile": str(passfile)}



# ── the dial: a refused loopback dial wakes the database proxy (ticket 9166782e6101) ──
# On a cache box the route is TCP loopback to the local database proxy, and nothing starts that
# proxy after a reboot. Measured 2026-11-18 on akiendelllinux: every db call failed 'Connection
# refused' at 127.0.0.1:5432. A refusal on that route asks the bus, once per process, to start the
# proxy, then retries the dial. The target is a STRING, so this module imports nothing of dbproxy.
_PROXY_SHIM = "cairn.devices.dbproxy.shim:DatabaseProxyShim"
_WAKE_SECONDS = 60.0
_WAKE_POLL = 0.5
_woken = False


def _refused(exc: Exception) -> bool:
    return "connection refused" in str(exc).lower()


def _wake_proxy() -> None:
    """Ask the bus to start the database proxy. Raises naming why when the wake fails."""
    from cairn.tools.bus_client import remote   # at call time: the bus is optional to a socket box
    remote.ensure_bus()
    reply = remote.RemoteBus().verbs(_PROXY_SHIM, ["start"])
    if not isinstance(reply, dict) or reply.get("exit") != 0:
        said = reply.get("text") if isinstance(reply, dict) else reply
        raise RuntimeError(f"the bus answered start on {_PROXY_SHIM} with {said!r}")


def _dial(dbname: str):
    """psycopg2.connect over _conn_args(); a refused TCP dial wakes the proxy and retries.

    A socket dial, or any failure that is not a refusal, raises at once. A wake that fails, or a
    refusal still standing after _WAKE_SECONDS, re-raises the refusal naming why (Law 7)."""
    global _woken
    import time
    args = _conn_args()
    try:
        return psycopg2.connect(dbname=dbname, **args)
    except psycopg2.OperationalError as exc:
        if args.get("host") != _TCP_HOST or not _refused(exc):
            raise
        first = exc
    if not _woken:
        _woken = True
        try:
            _wake_proxy()
        except Exception as wake:  # noqa: BLE001 — every wake failure is named on the refusal
            raise psycopg2.OperationalError(
                f"{first} — and waking the database proxy failed: {wake}") from wake
    deadline = time.monotonic() + _WAKE_SECONDS
    while True:
        time.sleep(_WAKE_POLL)
        try:
            return psycopg2.connect(dbname=dbname, **args)
        except psycopg2.OperationalError as exc:
            if not _refused(exc):
                raise
            if time.monotonic() >= deadline:
                raise psycopg2.OperationalError(
                    f"{exc} — still refused {_WAKE_SECONDS:g}s after waking the database proxy "
                    f"({_PROXY_SHIM})") from exc


def database_name() -> str:
    """The database this process writes: TESTING_DB_NAME under a test run, else DB_NAME.
    Read at call time, so a proof can set and clear the id around one call."""
    return TESTING_DB_NAME if os.environ.get(_TEST_ID_ENV) else DB_NAME


def ensure_database(name: str | None = None) -> None:
    """Create ``name`` (default: database_name()) if it is absent. Idempotent; needs CREATEDB.

    CREATE DATABASE cannot run inside a transaction, so this connects with autocommit to
    the always-present bootstrap database and issues the DDL only when ours is missing.
    """
    name = name or database_name()
    conn = _dial(_BOOTSTRAP_DB)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    finally:
        conn.close()


def connect():
    """A connection to database_name() — the only route to durable state, and the one every
    write goes through (under a test run, ``cairn_testing``; ticket e4fd7f28faaf).

    Ensures the database and the owner registry exist first, so a fresh machine reaches a
    working store through this one call.
    """
    name = database_name()
    ensure_database(name)
    conn = _dial(name)
    conn.autocommit = True
    _ensure_registry(conn)
    return conn


def _read_connection(tables) -> "psycopg2.extensions.connection":
    """The connection a read of ``tables`` goes through (tickets e4fd7f28faaf, b7b90c36cb37).

    No test run: connect(), unchanged. Under one: cairn_testing when THIS run created one of the
    named tables (the run's id is in that table's ``cairn_owned.test_ids``, stamped by
    create_owned_table) or names db_domain's own registries there; else live opened read-only,
    so a write sent down a read path raises ReadOnlySqlTransaction instead of touching the live
    record. Measured 2026-11-23 (a4c8bf408dc2): "cairn_testing holds it" is not "this run created
    it". Earlier runs' tables stand in cairn_testing, and a live read-only tooth read 224 of their
    rows instead of live's 20216."""
    if database_name() == DB_NAME:
        return connect()
    testing = connect()
    names = [t for t in tables if t]
    if any(t in _OWN_REGISTRIES for t in names):
        return testing
    if names:
        with testing.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT 1 FROM {reg} o JOIN pg_tables p ON p.tablename = o.table_name "
                        "AND p.schemaname = current_schema() "
                        "WHERE o.table_name = ANY(%s) AND %s = ANY(o.test_ids) LIMIT 1"
                        ).format(reg=sql.Identifier(_REGISTRY)),
                (names, os.environ.get(_TEST_ID_ENV)))
            if cur.fetchone() is not None:
                return testing
    testing.close()
    ensure_database(DB_NAME)
    live = _dial(DB_NAME)
    live.autocommit = True
    with live.cursor() as cur:
        cur.execute("SET default_transaction_read_only = on")
    return live


def _stamp_creator(table: str, conn) -> None:
    """Under a test run, add this run's id to ``table``'s set of creating runs (b7b90c36cb37).

    Appended, never replaced, so two runs that both create a table both read it from testing;
    an id is never removed and nothing is dropped here (outline 4.3.1.5.1.5.2 (6) is not this)."""
    test_id = os.environ.get(_TEST_ID_ENV)
    if not test_id or conn.info.dbname != TESTING_DB_NAME:
        return
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("UPDATE {reg} SET test_ids = array_append(test_ids, %s) "
                    "WHERE table_name = %s AND NOT (%s = ANY(test_ids))"
                    ).format(reg=sql.Identifier(_REGISTRY)),
            (test_id, table, test_id))


def _ensure_registry(conn) -> None:
    """The registry that turns 'has an owner' into a schema fact, not a hope.

    `CHECK (owner <> '')` is the physics: Postgres itself refuses an ownerless row, so no
    amount of caller sloppiness can register a table without an owner. The registry owns
    itself (owner = 'db_domain') — the base case that makes every other table's ownership
    a lookup rather than a special case.
    """
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "CREATE TABLE IF NOT EXISTS {reg} ("
                "  table_name text PRIMARY KEY,"
                "  owner text NOT NULL CHECK (owner <> ''),"
                "  created timestamptz NOT NULL DEFAULT now()"
                ")"
            ).format(reg=sql.Identifier(_REGISTRY))
        )
        cur.execute(
            sql.SQL(
                "INSERT INTO {reg} (table_name, owner) VALUES (%s, %s) "
                "ON CONFLICT (table_name) DO NOTHING"
            ).format(reg=sql.Identifier(_REGISTRY)),
            (_REGISTRY, "db_domain"),
        )
        if conn.info.dbname == TESTING_DB_NAME:
            # The set of runs that created each testing table (b7b90c36cb37). Checked before it
            # is altered: ALTER TABLE takes an exclusive lock even when the column already exists.
            cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() "
                        "AND table_name = %s AND column_name = 'test_ids'", (_REGISTRY,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("ALTER TABLE {reg} ADD COLUMN IF NOT EXISTS test_ids text[] "
                                    "NOT NULL DEFAULT '{{}}'").format(reg=sql.Identifier(_REGISTRY)))


# ── owner-gated schema + writes ──────────────────────────────────────────────


def owner_of(table: str, *, conn=None) -> str | None:
    """The recorded owner of `table`, or None if db_domain never created it."""
    own_conn = conn or connect()
    try:
        with own_conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT owner FROM {reg} WHERE table_name = %s").format(
                    reg=sql.Identifier(_REGISTRY)
                ),
                (table,),
            )
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        if conn is None:
            own_conn.close()


def create_owned_table(table: str, owner: str, columns: dict[str, str], *, conn=None) -> None:
    """Create `table` with a declared `owner`, recording the ownership as it is born.

    An ownerless table cannot come into existence: an empty owner is refused here AND by
    the registry's CHECK. Creating an already-registered table under a *different* owner is
    refused too — ownership is exactly one, and it does not silently change.
    """
    if not owner:
        raise OwnershipError(f"refusing to create {table!r} with no owner — every table has exactly one (Law 6)")
    if not columns:
        raise ValueError(f"{table!r} needs at least one column")

    own_conn = conn or connect()
    try:
        existing = owner_of(table, conn=own_conn)
        if existing is not None and existing != owner:
            raise OwnershipError(
                f"{table!r} is already owned by {existing!r}; refusing to re-create it under {owner!r}"
            )
        cols = sql.SQL(", ").join(
            sql.SQL("{} {}").format(sql.Identifier(name), sql.SQL(coltype))
            for name, coltype in columns.items()
        )
        with own_conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE TABLE IF NOT EXISTS {tbl} ({cols})").format(
                    tbl=sql.Identifier(table), cols=cols
                )
            )
            cur.execute(
                sql.SQL(
                    "INSERT INTO {reg} (table_name, owner) VALUES (%s, %s) "
                    "ON CONFLICT (table_name) DO NOTHING"
                ).format(reg=sql.Identifier(_REGISTRY)),
                (table, owner),
            )
        _stamp_creator(table, own_conn)
    finally:
        if conn is None:
            own_conn.close()


def add_owned_constraint(table: str, owner: str, name: str, expression: str, *, conn=None) -> None:
    """Add a CHECK constraint to an already-created, owned table — owner-gated (Law 6).

    Idempotent: a startup path can call this beside create_owned_table without caring
    whether the constraint is already there. Postgres validates against every existing row
    and refuses if any violate — no NOT VALID escape hatch.

    Takes a NAME and an EXPRESSION, never a statement. That bound keeps the one door from
    becoming a DDL passthrough.
    """
    recorded = owner_of(table, conn=conn)
    if recorded is None:
        raise OwnershipError(f"{table!r} was not created through db_domain — it has no owner to gate a constraint")
    if recorded != owner:
        raise OwnershipError(f"{owner!r} may not constrain {table!r} — its owner is {recorded!r} (Law 6)")
    if not name or not name.strip():
        raise ValueError("a constraint needs a name")
    if not expression or not expression.strip():
        raise ValueError("a constraint needs an expression")

    own_conn = conn or connect()
    try:
        with own_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.table_constraints "
                "WHERE table_schema = 'public' AND table_name = %s AND constraint_name = %s",
                (table, name),
            )
            if cur.fetchone() is not None:
                return
            cur.execute(
                sql.SQL("ALTER TABLE {tbl} ADD CONSTRAINT {cname} CHECK ({expr})").format(
                    tbl=sql.Identifier(table),
                    cname=sql.Identifier(name),
                    expr=sql.SQL(expression),
                )
            )
    finally:
        if conn is None:
            own_conn.close()


def add_owned_index(table: str, owner: str, name: str, columns, *, conn=None) -> None:
    """Add a btree index over ``columns`` to an already-created, owned table — owner-gated (Law 6).

    Idempotent (CREATE INDEX IF NOT EXISTS): a startup path can call it beside
    create_owned_table on a table that may already carry it. Takes a NAME and column NAMES,
    each quoted as an identifier — never a statement, never an expression.
    """
    recorded = owner_of(table, conn=conn)
    if recorded is None:
        raise OwnershipError(f"{table!r} was not created through db_domain — it has no owner to gate an index")
    if recorded != owner:
        raise OwnershipError(f"{owner!r} may not index {table!r} — its owner is {recorded!r} (Law 6)")
    if not name or not name.strip():
        raise ValueError("an index needs a name")
    columns = list(columns)
    if not columns or any(not c or not str(c).strip() for c in columns):
        raise ValueError("an index needs at least one named column")

    own_conn = conn or connect()
    try:
        with own_conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE INDEX IF NOT EXISTS {iname} ON {tbl} ({cols})").format(
                    iname=sql.Identifier(name),
                    tbl=sql.Identifier(table),
                    cols=sql.SQL(", ").join(sql.Identifier(c) for c in columns),
                )
            )
    finally:
        if conn is None:
            own_conn.close()

def write(table: str, owner: str, row: dict, *, conn=None) -> None:
    """Insert `row` into `table` — but only if `owner` is the table's recorded owner.

    Law 6: the owner alone gates writes. A write by anyone else is refused, loudly. A write
    to a table db_domain never created is refused too (it has no owner to gate it).
    """
    recorded = owner_of(table, conn=conn)
    if recorded is None:
        raise OwnershipError(f"{table!r} was not created through db_domain — it has no owner to gate a write")
    if recorded != owner:
        raise OwnershipError(f"{owner!r} may not write to {table!r} — its owner is {recorded!r} (Law 6)")

    own_conn = conn or connect()
    try:
        names = list(row.keys())
        # jsonb columns want a JSON string, not a Python dict, on the wire.
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in row.values()]
        stmt = sql.SQL("INSERT INTO {tbl} ({cols}) VALUES ({ph})").format(
            tbl=sql.Identifier(table),
            cols=sql.SQL(", ").join(sql.Identifier(n) for n in names),
            ph=sql.SQL(", ").join(sql.Placeholder() * len(names)),
        )
        with own_conn.cursor() as cur:
            cur.execute(stmt, values)
    finally:
        if conn is None:
            own_conn.close()


def update(table: str, owner: str, changes: dict, *, where: str, params: tuple = (), conn=None) -> int:
    """Mutate named columns of EXISTING rows — the second write face, gated exactly like the first.

    Law 6: the owner alone gates writes, and a mutation is a write. Same refusals as
    `write` (wrong owner, table db_domain never created), checked before anything touches
    the wire. `where` is mandatory: an implicit whole-table mutation is a defect, not a
    default — a caller that truly means every row says so in its own where clause.

    Returns the number of rows changed, so a caller can tell "mutated" from "matched
    nothing" without a second read. Pulled by the librarian's tenure loop (promotion
    writes `standing`, corroboration appends ride `provenance`), which mutates rows that
    already exist — INSERT can never say that.
    """
    recorded = owner_of(table, conn=conn)
    if recorded is None:
        raise OwnershipError(f"{table!r} was not created through db_domain — it has no owner to gate a write")
    if recorded != owner:
        raise OwnershipError(f"{owner!r} may not write to {table!r} — its owner is {recorded!r} (Law 6)")
    if not changes:
        raise ValueError(f"an update to {table!r} needs at least one column to change")
    if not where or not where.strip():
        raise ValueError(f"refusing a where-less update to {table!r} — a whole-table mutation is never implicit")

    own_conn = conn or connect()
    try:
        names = list(changes.keys())
        # jsonb columns want a JSON string, not a Python dict, on the wire — same as write.
        values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in changes.values()]
        stmt = sql.SQL("UPDATE {tbl} SET {assigns} WHERE ").format(
            tbl=sql.Identifier(table),
            assigns=sql.SQL(", ").join(
                sql.SQL("{} = {}").format(sql.Identifier(n), sql.Placeholder()) for n in names
            ),
        ) + sql.SQL(where)
        with own_conn.cursor() as cur:
            cur.execute(stmt, values + list(params))
            return cur.rowcount
    finally:
        if conn is None:
            own_conn.close()


def read(table: str, *, where: str | None = None, params: tuple = (), conn=None) -> list[dict]:
    """Read rows from `table` as dicts. Reads are not owner-gated (Law 6 gates writes).
    Under a test run the read is routed by _read_connection."""
    own_conn = conn or _read_connection([table])
    try:
        stmt = sql.SQL("SELECT * FROM {tbl}").format(tbl=sql.Identifier(table))
        if where:
            stmt = stmt + sql.SQL(" WHERE ") + sql.SQL(where)
        with own_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(stmt, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        if conn is None:
            own_conn.close()


def query(template: str, *, tables: dict[str, str], params: tuple = (), conn=None) -> list[dict]:
    """Execute a SELECT with safely-quoted table identifiers, returning dicts.

    ``template`` is a SQL string with ``{name}`` placeholders for table identifiers.
    ``tables`` maps each placeholder name to the real table name, which is quoted
    through ``sql.Identifier``. Value parameters use ``%s`` as usual.

    Reads are not owner-gated (Law 6 gates writes). This is the door for JOINs and
    other multi-table reads that ``read()`` cannot express. Under a test run the read is routed
    by _read_connection over the named tables.
    """
    own_conn = conn or _read_connection(tables.values())
    try:
        stmt = sql.SQL(template).format(**{k: sql.Identifier(v) for k, v in tables.items()})
        with own_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(stmt, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        if conn is None:
            own_conn.close()


def delete(table: str, owner: str, *, where: str | None = None, params: tuple = (), conn=None) -> int:
    """Delete rows from ``table`` — owner-gated like every other write (Law 6).

    Without ``where``, deletes ALL rows (the caller said so explicitly). Returns the
    count of rows removed.
    """
    recorded = owner_of(table, conn=conn)
    if recorded is None:
        raise OwnershipError(f"{table!r} was not created through db_domain — it has no owner to gate a delete")
    if recorded != owner:
        raise OwnershipError(f"{owner!r} may not delete from {table!r} — its owner is {recorded!r} (Law 6)")

    own_conn = conn or connect()
    try:
        stmt = sql.SQL("DELETE FROM {tbl}").format(tbl=sql.Identifier(table))
        if where:
            stmt = stmt + sql.SQL(" WHERE ") + sql.SQL(where)
        with own_conn.cursor() as cur:
            cur.execute(stmt, params)
            return cur.rowcount
    finally:
        if conn is None:
            own_conn.close()


def drop_table(table: str, owner: str, *, conn=None) -> bool:
    """Drop ``table`` and remove its registry entry — owner-gated (Law 6).

    Returns True if the table existed, False if it was already gone. The registry
    entry is removed either way (idempotent cleanup).
    """
    recorded = owner_of(table, conn=conn)
    if recorded is not None and recorded != owner:
        raise OwnershipError(f"{owner!r} may not drop {table!r} — its owner is {recorded!r} (Law 6)")

    own_conn = conn or connect()
    try:
        with own_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = %s", (table,)
            )
            existed = cur.fetchone() is not None
            if existed:
                cur.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(table)))
            cur.execute(
                sql.SQL("DELETE FROM {reg} WHERE table_name = %s").format(
                    reg=sql.Identifier(_REGISTRY)
                ),
                (table,),
            )
            return existed
    finally:
        if conn is None:
            own_conn.close()


# ── scratch: a table that cannot outlive the process that minted it ──────────
#
# Ticket 201a37bf1613 (Akien 2026-09-06: "we have 9075 tables? wow!"). Measured that
# evening: 9,087 tables, 12 live, and every proof hand-rolling its own teardown against a
# store that had no word for "mine until I exit". This section is the word (Law 4):
#
#   - ``scratch(owner, prefix, columns)`` mints ``<prefix>_<pid>_<HHMMSSffff>`` through
#     ``create_owned_table`` (the owner gate is untouched — scratch rides it), records
#     (table, pid, created) in ``cairn_scratch``, and drops the table, its registered
#     companions and their rows on exit WHATEVER the exit.
#   - ``register_scratch_companion(table, companion)`` — a machine that creates a table
#     beside one it was handed (the bus's ``_delivery``, the librarian's split children)
#     registers it under the parent's pid so it drops with its parent.
#   - ``sweep_scratch()`` drops every cairn_scratch row whose minter is dead — pid absent
#     from /proc, or present with a start time later than the row's ``created`` (pid
#     reuse) — and its companions, and returns the count. The tester calls it before
#     every seal: the one event every proof already passes through, so no clock and no
#     daemon (memory reaching-for-daemons-is-drift). A proof killed with SIGKILL mid-run
#     is cleaned by the next seal, not by a finally block it never reached.
#
# THE SWEEP NEVER TOUCHES A TABLE WITHOUT A cairn_scratch ROW. The live set is the
# registry's non-scratch rows, never a name pattern (the ticket's WRONG INTENT clause).


def _ensure_scratch_registry(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "CREATE TABLE IF NOT EXISTS {reg} ("
                "  table_name text PRIMARY KEY,"
                "  pid integer NOT NULL,"
                "  created timestamptz NOT NULL DEFAULT now(),"
                "  companion_of text NULL"
                ")"
            ).format(reg=sql.Identifier(_SCRATCH))
        )
        cur.execute(
            sql.SQL(
                "INSERT INTO {reg} (table_name, owner) VALUES (%s, %s) "
                "ON CONFLICT (table_name) DO NOTHING"
            ).format(reg=sql.Identifier(_REGISTRY)),
            (_SCRATCH, "db_domain"),
        )


def scratch_name(prefix: str, suffix: str = "") -> str:
    """The name rule: ``<prefix>_<pid>_<HHMMSSffff>[_<suffix>]`` — the leaker stays legible
    if it ever leaks again (memory self-describing-fixture-names). The prefix is the
    caller's own word (bus_traffic, chat_pane, trees); no leading underscore, the registry
    is the truth. The suffix is for a name a derivation ends in (a nexus's ``_nodes``) —
    the pid and stamp still sit where the sweep's eye and the probe's regex look."""
    for role, word in (("prefix", prefix), ("suffix", suffix)):
        if word == "" and role == "suffix":
            continue
        if not word or not word.replace("_", "").isalnum():
            raise ValueError(f"scratch {role} {word!r} is not a legal identifier fragment")
    now = datetime.now()
    name = f"{prefix}_{os.getpid()}_{now.strftime('%H%M%S')}{now.microsecond // 100:04d}"
    return f"{name}_{suffix}" if suffix else name


def _windows_process_start(pid: int) -> float | None:
    """Creation time of a running pid as epoch seconds, None when it is gone or cannot be opened."""
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    k32.GetProcessTimes.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
                                    ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME))
    k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = k32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        code = wintypes.DWORD()
        if not k32.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259:   # STILL_ACTIVE
            return None   # a handle to an exited process still opens: it is not a live minter
        created, ended, kernel, user = (wintypes.FILETIME() for _ in range(4))
        if not k32.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(ended), ctypes.byref(kernel),
                                   ctypes.byref(user)):
            return None
        ticks = (created.dwHighDateTime << 32) | created.dwLowDateTime   # 100 ns since 1601-01-01
        return (ticks - 116444736000000000) / 1e7
    finally:
        k32.CloseHandle(handle)


def process_start(pid: int) -> float | None:
    """The epoch second a live pid started, or None when /proc has no such pid.

    /proc/<pid>/stat field 22 is start time in clock ticks since boot; /proc/stat ``btime``
    is boot time in epoch seconds. Together they date the process, which is what tells a
    reused pid from the minter it replaced.

    WINDOWS HAS NO /proc, and the old answer there was None for EVERY pid, a LIVE one included:
    ``minter_alive`` then read the caller's own process as dead and ``sweep_scratch`` dropped its
    live scratch tables (measured 2026-11-14 on akiendell: ``sweep_scratch()`` from a process
    holding one scratch table dropped it; the tester sweeps before every ``--seal``, so a proof
    that opens fixture buses lost its tables mid-run, the bus re-created them unregistered, and
    24 ``seal_ann_*_delivery`` tables outlived their runs). There the start time is the process
    creation time (``GetProcessTimes``) in epoch seconds, None when the pid is not running."""
    if os.name == "nt":
        return _windows_process_start(pid)
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as fh:
            stat = fh.read()
        with open("/proc/stat", encoding="utf-8") as fh:
            btime = next(int(line.split()[1]) for line in fh if line.startswith("btime "))
    except (OSError, StopIteration, ValueError):
        return None
    # the comm field may carry spaces; everything after the last ')' is positional
    fields = stat.rsplit(")", 1)[1].split()
    ticks = int(fields[19])  # field 22, counted from field 3
    return btime + ticks / os.sysconf("SC_CLK_TCK")


def minter_alive(pid: int, created: datetime) -> bool:
    """Is the process that minted a scratch row still the one that holds it? Absent from
    /proc → dead. Present but started after the row was created → a reused pid, dead.
    One tick of slack (clock ticks are 10ms; ``created`` is Postgres now())."""
    start = process_start(pid)
    if start is None:
        return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return start <= created.timestamp() + 1.0


def is_scratch(table: str, *, conn=None) -> bool:
    """Does ``table`` have a cairn_scratch row — parent or companion?"""
    own_conn = conn or connect()
    try:
        _ensure_scratch_registry(own_conn)
        with own_conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT 1 FROM {reg} WHERE table_name = %s").format(
                    reg=sql.Identifier(_SCRATCH)),
                (table,),
            )
            return cur.fetchone() is not None
    finally:
        if conn is None:
            own_conn.close()


def scratch_rows(*, conn=None) -> list[dict]:
    """Every cairn_scratch row: table_name, pid, created, companion_of."""
    own_conn = conn or connect()
    try:
        _ensure_scratch_registry(own_conn)
        with own_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                sql.SQL("SELECT table_name, pid, created, companion_of FROM {reg} "
                        "ORDER BY created, table_name").format(reg=sql.Identifier(_SCRATCH)))
            return [dict(r) for r in cur.fetchall()]
    finally:
        if conn is None:
            own_conn.close()


def register_scratch_companion(table: str, companion: str, *, conn=None) -> None:
    """Record ``companion`` as born beside the scratch ``table``, under the same pid, so it
    drops with its parent on exit and on sweep. Refused when ``table`` is not scratch —
    a companion of a live table is a live table."""
    own_conn = conn or connect()
    try:
        _ensure_scratch_registry(own_conn)
        with own_conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT pid, companion_of FROM {reg} WHERE table_name = %s").format(
                    reg=sql.Identifier(_SCRATCH)),
                (table,),
            )
            row = cur.fetchone()
            if row is None:
                raise OwnershipError(
                    f"{table!r} is not a scratch table — refusing to register {companion!r} "
                    "as its companion (a companion of a live table is a live table)")
            pid, parent = row
            cur.execute(
                sql.SQL(
                    "INSERT INTO {reg} (table_name, pid, companion_of) VALUES (%s, %s, %s) "
                    "ON CONFLICT (table_name) DO NOTHING"
                ).format(reg=sql.Identifier(_SCRATCH)),
                (companion, pid, parent or table),
            )
    finally:
        if conn is None:
            own_conn.close()


def _drop_scratch_family(table: str, conn) -> list[str]:
    """Drop ``table`` and every companion registered under it, plus their rows in both
    registries. Owner-gated through ``drop_table`` under each table's recorded owner —
    the store dropping what the store minted."""
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT table_name FROM {reg} WHERE companion_of = %s").format(
                reg=sql.Identifier(_SCRATCH)),
            (table,),
        )
        companions = [r[0] for r in cur.fetchall()]
    dropped = []
    for name in [*companions, table]:
        owner = owner_of(name, conn=conn) or "db_domain"
        drop_table(name, owner, conn=conn)
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("DELETE FROM {reg} WHERE table_name = %s").format(
                    reg=sql.Identifier(_SCRATCH)),
                (name,),
            )
        dropped.append(name)
    return dropped


@contextmanager
def scratch(owner: str, prefix: str, columns: dict[str, str], *, conn=None, suffix: str = ""):
    """A table that is yours until you exit — and no longer.

    Mints ``<prefix>_<pid>_<HHMMSSffff>[_<suffix>]``, creates it owned by ``owner`` through the one
    door, records it in cairn_scratch under this pid, yields the name, and on exit — normal,
    exception, anything a finally can catch — drops it with its companions and rows. What a
    finally cannot catch (SIGKILL, OOM) the next ``sweep_scratch`` catches by the pid."""
    name = scratch_name(prefix, suffix)
    own_conn = conn or connect()
    try:
        _ensure_scratch_registry(own_conn)
        create_owned_table(name, owner, columns, conn=own_conn)
        with own_conn.cursor() as cur:
            cur.execute(
                sql.SQL("INSERT INTO {reg} (table_name, pid) VALUES (%s, %s)").format(
                    reg=sql.Identifier(_SCRATCH)),
                (name, os.getpid()),
            )
        try:
            yield name
        finally:
            _drop_scratch_family(name, own_conn)
    finally:
        if conn is None:
            own_conn.close()


def sweep_scratch(*, conn=None, report: list | None = None) -> int:
    """Drop every scratch family whose minter is dead; return how many tables were dropped.

    The predicate is the registry row and the pid — never a name. A companion whose parent
    row is gone is swept on its own pid. Pass a list as ``report`` to receive the dropped
    names (the tester logs them on the seal's evidence, so a leaker is named, not counted)."""
    own_conn = conn or connect()
    try:
        rows = scratch_rows(conn=own_conn)
        dropped: list[str] = []
        parents = {r["table_name"] for r in rows if r["companion_of"] is None}
        for r in rows:
            if r["table_name"] in dropped:
                continue
            if r["companion_of"] is not None and r["companion_of"] in parents:
                continue  # rides its parent's verdict
            if minter_alive(r["pid"], r["created"]):
                continue
            dropped.extend(_drop_scratch_family(r["table_name"], own_conn))
        if report is not None:
            report.extend(dropped)
        return len(dropped)
    finally:
        if conn is None:
            own_conn.close()

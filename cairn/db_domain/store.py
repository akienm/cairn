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
`--unshare-net` seal (cairn/tester/isolation.py): a sealed build has no route to 5432 over
the network, yet still reaches the DB — *only* through this domain. That asymmetry is the
sole-route half of CLAUDE.md's "port 5432 is reached only through db_domain".

ONE-TIME PROVISIONING (instance setup, not class-space code — it is privileged and
machine-specific): the OS-named login role must exist. `CREATE ROLE <you> LOGIN CREATEDB;`
run once as the postgres superuser. Given that role, db_domain creates the `cairn`
database itself (`ensure_database`), so the manual surface is exactly one role.

WHAT DURABLE STATE LIVES HERE (narrowed 2026-07-22): the relational / graph-tree data —
the trees the database is uniquely good at. VALIDATIONS used to be db_domain's first
consumer; they MOVED OUT to beside-code git-JSON, next to the ``proofs/`` they seal
(``cairn/tester/validation_store.py``; ruling in tickets/charter-state-history-split.json
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

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

# Peer auth over the Unix socket: host is the socket directory, role is the OS user, and
# the database is Cairn's own. A socket is a file — it crosses a network namespace freely.
SOCKET_DIR = "/var/run/postgresql"
DB_NAME = "cairn"
_BOOTSTRAP_DB = "postgres"  # the always-present database we connect to only to create ours

# db_domain owns its own metadata table — the registry that makes ownership a fact.
_REGISTRY = "cairn_owned"


class OwnershipError(Exception):
    """A write or a creation that the owner-gate refused. Loud, never swallowed (Law 7)."""


# ── connection: the one door to 5432 ─────────────────────────────────────────


def ensure_database() -> None:
    """Create the `cairn` database if it is absent. Idempotent; needs CREATEDB on the role.

    CREATE DATABASE cannot run inside a transaction, so this connects with autocommit to
    the always-present bootstrap database and issues the DDL only when ours is missing.
    """
    conn = psycopg2.connect(host=SOCKET_DIR, dbname=_BOOTSTRAP_DB)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
    finally:
        conn.close()


def connect():
    """A connection to the `cairn` database — the only route to durable state.

    Ensures the database and the owner registry exist first, so a fresh machine reaches a
    working store through this one call.
    """
    ensure_database()
    conn = psycopg2.connect(host=SOCKET_DIR, dbname=DB_NAME)
    conn.autocommit = True
    _ensure_registry(conn)
    return conn


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


def read(table: str, *, where: str | None = None, params: tuple = (), conn=None) -> list[dict]:
    """Read rows from `table` as dicts. Reads are not owner-gated (Law 6 gates writes)."""
    own_conn = conn or connect()
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

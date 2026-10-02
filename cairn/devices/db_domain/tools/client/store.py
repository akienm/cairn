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
(``cairn/devices/tester/validation_store.py``; ruling in tickets/charter-state-history-split.json
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
# ...and the registry of SCRATCH: tables born through ``scratch()`` that belong to one
# process for exactly its lifetime (ticket 201a37bf1613). A row here is what makes a
# table sweepable; a name is never the predicate.
_SCRATCH = "cairn_scratch"


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


def query(template: str, *, tables: dict[str, str], params: tuple = (), conn=None) -> list[dict]:
    """Execute a SELECT with safely-quoted table identifiers, returning dicts.

    ``template`` is a SQL string with ``{name}`` placeholders for table identifiers.
    ``tables`` maps each placeholder name to the real table name, which is quoted
    through ``sql.Identifier``. Value parameters use ``%s`` as usual.

    Reads are not owner-gated (Law 6 gates writes). This is the door for JOINs and
    other multi-table reads that ``read()`` cannot express.
    """
    own_conn = conn or connect()
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


def process_start(pid: int) -> float | None:
    """The epoch second a live pid started, or None when /proc has no such pid.

    /proc/<pid>/stat field 22 is start time in clock ticks since boot; /proc/stat ``btime``
    is boot time in epoch seconds. Together they date the process, which is what tells a
    reused pid from the minter it replaced."""
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

"""A remote box's database syncs the home box's learning (ticket 3ef8654a8027, outline 11.3.5.1).

THE UNIT, AS ANSWERED (open-675330928c01): the outline stands. The memory model's learning tables
(4.3.1.5): the one long node list ``cairn_nodes``, its embeddings, links and threads, and the trees
that index them as tables of their own, each with one owner (11.3.6). ``sync_from_home`` moves them
from a HOME database to a REMOTE one through the owner-gated store door and nothing else:

  * a table the home holds is CREATED on the remote under the SAME owner, with the same columns and
    primary key (``create_owned_table``, which records the ownership as it is born);
  * a row the home holds whose primary key the remote lacks is WRITTEN (``store.write``, the owner
    gate). A row both hold is never touched: the sync INSERTS, it never updates and never deletes,
    so it is idempotent and a second run copies nothing. A row only the remote holds stays.

WHAT THE OUTLINE DOES NOT SETTLE AND THIS BUILD DEFAULTS AROUND (each is a question on the ticket,
and each default is the conservative, reversible one):
  1. Row identity. The outline says a row number is a slot reserved from the home librarian
     (4.3.1.5.1.1); the code keys nodes by a content hash (``trees.node_id_for``). With hashes the
     same node is the same row everywhere and the sync is a primary-key union; the slot and its blanks
     are not built here (the librarian is out of this ticket's bounds).
  2. Direction. Home to remote only. 11.3.5.1 also says "the sync is the backup" (remote to home);
     that direction is not built.
  3. Authority (Law 6). The sync writes into tables other devices own. It does so only for owners
     the caller names in ``owners``, an argument with no default: an unnamed owner's table is listed
     as skipped, never created and never written.
  4. Conflict. A row both boxes hold with different contents is left as the remote has it and is
     COUNTED in ``differing``, not resolved.

Two connections, not two boxes: how the remote reaches the home's rows (the bus, CAIRN_HOME_HOST) is
the transport and is not this module's concern; a caller hands it a reader on the home database.
A table without a single-column primary key is refused by name and never copied blind.
"""
from __future__ import annotations

import json

from cairn.devices.db_domain.tools.client import store

_SKIP = {"cairn_owned"}   # the registry names itself; the remote's own is born with its connection

_COLUMNS = (
    "SELECT a.attname AS name, format_type(a.atttypid, a.atttypmod) AS type, a.attnotnull AS notnull "
    "FROM pg_attribute a WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped "
    "ORDER BY a.attnum")
_PRIMARY = (
    "SELECT a.attname AS name FROM pg_index i JOIN pg_attribute a "
    "ON a.attrelid = i.indrelid AND a.attnum = ANY (i.indkey) WHERE i.indrelid = %s::regclass AND i.indisprimary")


def _rows(conn, template: str, param: str) -> list[dict]:
    return store.query(template, tables={}, params=(param,), conn=conn)


def _shape(conn, table: str) -> tuple[dict[str, str], list[str]]:
    """The table's columns as ``create_owned_table`` takes them, and its primary-key columns."""
    pk = [r["name"] for r in _rows(conn, _PRIMARY, f'"{table}"')]
    columns = {}
    for r in _rows(conn, _COLUMNS, f'"{table}"'):
        spec = r["type"] + (" PRIMARY KEY" if pk == [r["name"]] else (" NOT NULL" if r["notnull"] else ""))
        columns[r["name"]] = spec
    return columns, pk


def sync_from_home(home_conn, remote_conn, *, owners: set[str] | frozenset[str]) -> dict[str, dict]:
    """Bring the home database's learning tables, for the named ``owners``, to the remote one.

    Returns ``{table: {...}}``: ``created`` (the table was absent), ``copied`` (rows written),
    ``present`` (rows both hold, identical), ``differing`` (rows both hold that differ, left alone)
    for a synced table, or ``{"skipped": <owner>}`` / ``{"refused": <why>}`` otherwise."""
    if not owners:
        raise ValueError("sync_from_home needs the owners it may write for: an empty set syncs nothing and says so")
    registry = store.read("cairn_owned", conn=home_conn)
    out: dict[str, dict] = {}
    for entry in sorted(registry, key=lambda r: r["table_name"]):
        table, owner = entry["table_name"], entry["owner"]
        if table in _SKIP:
            continue
        if store.is_scratch(table, conn=home_conn):
            continue   # a proof's throwaway, swept by its own door, is not learning
        if owner not in owners:
            out[table] = {"skipped": owner}
            continue
        columns, pk = _shape(home_conn, table)
        if len(pk) != 1:
            out[table] = {"refused": f"needs exactly one primary-key column to be synced without a blind copy, has {pk}"}
            continue
        key = pk[0]
        created = store.owner_of(table, conn=remote_conn) is None
        store.create_owned_table(table, owner, columns, conn=remote_conn)
        have = {r[key]: r for r in store.read(table, conn=remote_conn)}
        copied = present = differing = 0
        for row in store.read(table, conn=home_conn):
            standing = have.get(row[key])
            if standing is None:
                store.write(table, owner, {k: (json.dumps(v) if columns[k].startswith("jsonb") else v)
                                           for k, v in row.items()}, conn=remote_conn)
                copied += 1
            elif standing == row:
                present += 1
            else:
                differing += 1
        out[table] = {"owner": owner, "created": created, "copied": copied, "present": present,
                      "differing": differing}
    return out

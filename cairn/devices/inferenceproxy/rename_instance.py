"""rename_instance — carry the inference proxy's instance-space life to its outline address.

Ticket f942a413f26d, decision D4. The class moved from ``cairn/devices/inference_domain/`` to
``cairn/devices/inferenceproxy/`` (outline 11.4) in git; what git cannot see moves here, by a
replayable recipe:

- ``~/.cairn/devices/inference_domain/`` -> ``~/.cairn/devices/inferenceproxy/`` and
  ``~/.cairn/logs/inference_domain/`` -> ``~/.cairn/logs/inferenceproxy/``. When both stand, the
  old one is merged into the new one entry by entry; a file that stands in both keeps the new
  one's bytes at its name and the old one's beside it as ``<name>.from-inference_domain``, so a
  merge never drops a byte.
- the answer tree's leaf table ``inference_domain_answers_nodes`` -> ``inferenceproxy_answers_nodes``
  (``ALTER TABLE IF EXISTS``, its two indexes with it), and the owner registry's row for it is
  rewritten to the new table name and the new owner through the store's owner-gated ``update``.
  When both tables stand (the renamed code already made the new one: measured 2026-11-13, 99 rows
  beside the old 15017), the new one's rows are folded into the old one first, a row the old one
  already holds keeping the old one's bytes, and the new one is dropped through the store's
  owner-gated ``drop_table``; then the rename runs as above.

The metric rows recorded under ``inference_domain`` stay as they were recorded: a metric's
source is a record of who measured it then, and the new rows carry ``inferenceproxy``.

Usage::

    python3 -m cairn.devices.inferenceproxy.rename_instance apply    # idempotent
    python3 -m cairn.devices.inferenceproxy.rename_instance verify   # exit 0 = nothing old stands

``verify`` is red while any old-name directory, table or registry row stands.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# The old names. These constants, and the device's history.json, are the only live spellings
# of the old name in class-space once the move lands (ticket f942a413f26d, D5 clause 1).
OLD = "inference_domain"
NEW = "inferenceproxy"
TABLES = (("inference_domain_answers_nodes", "inferenceproxy_answers_nodes"),)
MERGED_SUFFIX = ".from-inference_domain"


def _instance_root(home: Path | str | None) -> Path:
    return (Path(home) if home is not None else Path.home()) / ".cairn"


def dir_pairs(home: Path | str | None = None) -> list[tuple[Path, Path]]:
    root = _instance_root(home)
    return [(root / tier / OLD, root / tier / NEW) for tier in ("devices", "logs")]


def _merge(src: Path, dst: Path, moved: list[str]) -> None:
    """Move ``src``'s entries into ``dst`` without overwriting anything, then drop ``src``."""
    for entry in sorted(src.iterdir()):
        target = dst / entry.name
        if not target.exists() and not target.is_symlink():
            shutil.move(str(entry), str(target))
            moved.append(f"{entry} -> {target}")
        elif entry.is_dir() and not entry.is_symlink() and target.is_dir() and not target.is_symlink():
            _merge(entry, target, moved)
        else:
            aside = target.with_name(target.name + MERGED_SUFFIX)
            n = 1
            while aside.exists() or aside.is_symlink():
                n += 1
                aside = target.with_name(f"{target.name}{MERGED_SUFFIX}.{n}")
            shutil.move(str(entry), str(aside))
            moved.append(f"{entry} -> {aside}")
    src.rmdir()


def apply_dirs(home: Path | str | None = None) -> list[str]:
    moved: list[str] = []
    for old, new in dir_pairs(home):
        if not (old.exists() or old.is_symlink()):
            continue
        if not (new.exists() or new.is_symlink()):
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old), str(new))
            moved.append(f"{old} -> {new}")
        else:
            _merge(old, new, moved)
    return moved


def _store():
    from cairn.devices.db_domain.tools.client import store   # db_domain's published client
    return store


def _table_exists(cur, table: str) -> bool:
    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' "
                "AND table_name = %s", (table,))
    return cur.fetchone() is not None


def _fold_new_into_old(cur, store, sql, old, new, old_owner, new_owner, conn) -> list[str]:
    """Both tables stand: the renamed code already made the new one (a restart, or a proof run
    before the recipe — measured 2026-11-13: 99 rows). Its rows join the old table, a row the old
    one already holds (same primary key) staying as the old one wrote it, and the new table drops,
    so the rename below has its name free. A merge never drops a row the old table lacks."""
    for table, owner in ((old, old_owner), (new, new_owner)):
        recorded = store.owner_of(table, conn=conn)
        if recorded != owner:
            raise RuntimeError(f"{table} is owned by {recorded!r}, not {owner!r}; refusing to fold")
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s "
                "ORDER BY ordinal_position", (old,))
    cols = [r[0] for r in cur.fetchall()]
    names = sql.SQL(", ").join(sql.Identifier(c) for c in cols)
    cur.execute(sql.SQL("INSERT INTO {old} ({c}) SELECT {c} FROM {new} ON CONFLICT DO NOTHING").format(
        old=sql.Identifier(old), new=sql.Identifier(new), c=names))
    carried = cur.rowcount
    store.drop_table(new, new_owner, conn=conn)
    return [f"folded {carried} row(s) of {new} into {old}", f"dropped {new}"]


def apply_tables(tables=TABLES, *, old_owner: str = OLD, new_owner: str = NEW, conn=None) -> list[str]:
    """Rename each ``(old, new)`` table, its indexes, and its registry row. Idempotent: a pair
    whose old table and old row are both gone changes nothing."""
    store = _store()
    from psycopg2 import sql
    own = conn or store.connect()
    done: list[str] = []
    try:
        for old, new in tables:
            with own.cursor() as cur:
                if _table_exists(cur, old):
                    if _table_exists(cur, new):
                        done.extend(_fold_new_into_old(cur, store, sql, old, new, old_owner, new_owner, own))
                    cur.execute(sql.SQL("ALTER TABLE IF EXISTS {} RENAME TO {}").format(
                        sql.Identifier(old), sql.Identifier(new)))
                    done.append(f"table {old} -> {new}")
                    for suffix in ("_pkey", "_key"):
                        cur.execute("SELECT 1 FROM pg_indexes WHERE indexname = %s", (old + suffix,))
                        if cur.fetchone() is not None:
                            cur.execute(sql.SQL("ALTER INDEX {} RENAME TO {}").format(
                                sql.Identifier(old + suffix), sql.Identifier(new + suffix)))
                            done.append(f"index {old}{suffix} -> {new}{suffix}")
            if store.owner_of(old, conn=own) is not None:
                if store.owner_of(new, conn=own) is not None:
                    store.delete(store._REGISTRY, "db_domain", where="table_name = %s", params=(old,), conn=own)
                    done.append(f"registry row {old} dropped ({new} already registered)")
                else:
                    store.update(store._REGISTRY, "db_domain", {"table_name": new, "owner": new_owner},
                                 where="table_name = %s AND owner = %s", params=(old, old_owner), conn=own)
                    done.append(f"registry {old}/{old_owner} -> {new}/{new_owner}")
    finally:
        if conn is None:
            own.close()
    return done


def apply(home: Path | str | None = None, tables=TABLES, **kw) -> list[str]:
    return apply_dirs(home) + apply_tables(tables, **kw)


def verify(home: Path | str | None = None, tables=TABLES, *, conn=None) -> list[str]:
    """Every old-name thing that still stands; empty is green."""
    lacks = [f"{old} stands" for old, _new in dir_pairs(home) if old.exists() or old.is_symlink()]
    if tables:
        store = _store()
        own = conn or store.connect()
        try:
            with own.cursor() as cur:
                for old, _new in tables:
                    if _table_exists(cur, old):
                        lacks.append(f"table {old} stands")
                    if store.owner_of(old, conn=own) is not None:
                        lacks.append(f"registry row {old} stands")
        finally:
            if conn is None:
                own.close()
    return lacks


def main(argv: list[str]) -> int:
    if argv[:1] == ["apply"]:
        print(json.dumps({"applied": apply()}, indent=2))
        argv = ["verify"]
    if argv[:1] == ["verify"]:
        lacks = verify()
        print(json.dumps({"green": not lacks, "lacks": lacks}, indent=2))
        return 0 if not lacks else 1
    print("usage: rename_instance apply|verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

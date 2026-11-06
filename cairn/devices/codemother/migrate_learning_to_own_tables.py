"""codemother/migrate_learning_to_own_tables.py — one-shot: her learning moves into tables she owns.

Ticket 2b3d842bc118. Until 2026-11-06 codemother's eight tree-tool calls passed no owner, so her
learning indexes sat in leaf tables owned by 'chart' (chart_<nexus>_nodes). Akien 2026-11-05:
"yes, codemother's learning goes in its own tables." The leaves are an index over the
librarian's one shared node list; the nodes themselves do not move.

For each nexus: if chart_<n>_nodes exists, ensure codemother_<n>_nodes (owned by codemother,
the trees leaf columns), copy every leaf row whose leaf_id the destination lacks, then require
that every source node id is in the destination. Only on a match is chart_<n>_nodes dropped
(as its owner, 'chart'). A destination owned by anyone but codemother is refused untouched.
One line per table; a mismatch or refusal makes the run not ok and the CLI exit non-zero, so
nothing is lost silently (Law 7). A second run finds no source and changes nothing.

Run live once, after a pg_dump -t backup of the source tables:
    PYTHONPATH=. python3 -m cairn.devices.codemother.migrate_learning_to_own_tables
"""
from __future__ import annotations

import sys

OWNER = "codemother"
FROM_OWNER = "chart"
NEXI = ("constrain", "decompose", "hypothesize", "orient", "survey", "triage", "validate",
        "verdict", "codemother")


def _move_one(nexus: str, *, conn=None) -> tuple[bool, str]:
    from cairn.devices.db_domain.tools.client import store
    from cairn.devices.librarian.tools.trees import trees
    from cairn.tools.tree.tree import nexus_table
    # The source is named by hand, not through nexus_table: every codemother call into the tree
    # tool names owner codemother (ticket 2b3d842bc118 clause 1), and this is the one place the
    # old chart-owned name is read. It is the shape nexus_table gives (tree.py: owner_nexus_nodes).
    src, dst = f"{FROM_OWNER}_{nexus}_nodes", nexus_table(nexus, owner=OWNER)
    if store.owner_of(src, conn=conn) != FROM_OWNER:
        return True, f"{nexus}: {src} absent — nothing to move"
    dst_owner = store.owner_of(dst, conn=conn)
    if dst_owner not in (None, OWNER):
        return False, f"{nexus}: REFUSED — {dst} is owned by {dst_owner!r}, not {OWNER!r}"
    trees.ensure_trees(table=dst, owner=OWNER, conn=conn)
    rows = store.read(src, conn=conn)
    have = {r["leaf_id"] for r in store.read(dst, conn=conn)}
    copied = 0
    for r in rows:
        if r["leaf_id"] not in have:
            store.write(dst, OWNER, {k: r[k] for k in ("leaf_id", "node_id", "embedding_id")},
                        conn=conn)
            copied += 1
    want = {r["node_id"] for r in rows}
    got = {r["node_id"] for r in store.read(dst, conn=conn)}
    missing = want - got
    if missing:
        return False, (f"{nexus}: MISMATCH — {len(missing)} of {len(want)} node ids from {src} "
                       f"are not in {dst}; copied {copied}, dropped nothing")
    store.drop_table(src, FROM_OWNER, conn=conn)
    return True, (f"{nexus}: {src} -> {dst}: {len(rows)} rows, copied {copied}, "
                  f"{len(got)} in {dst}; dropped {src}")


def migrate(nexi=NEXI, *, conn=None) -> dict:
    """Move each nexus's leaf table; returns {"ok": bool, "lines": [one per table]}."""
    lines, ok = [], True
    for n in nexi:
        good, line = _move_one(n, conn=conn)
        ok = ok and good
        lines.append(line)
    return {"ok": ok, "lines": lines}


def main(argv=None) -> int:
    nexi = tuple((argv if argv is not None else sys.argv[1:]) or NEXI)
    got = migrate(nexi)
    for line in got["lines"]:
        print(line)
    print("ok" if got["ok"] else "NOT OK — see the lines above")
    return 0 if got["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

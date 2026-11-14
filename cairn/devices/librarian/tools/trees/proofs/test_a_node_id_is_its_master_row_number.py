"""A librarian node id is its master row number, and a node row is VOID, NOTCACHED or data (ticket 06db586bedfd).

Akien, Q#104, 2026-11-14 (outline 4.3.1.5.1.2): "there shall be no data node ids based on anything
other than master row number ... any other data node lookup method requires a search. row ID does
not and is direct." Measured 2026-11-14: ``node_id_for`` was sha256(content)[:16], cairn_nodes keyed
by it, no state column.

  1. deposit returns an integer node_id equal to the row it wrote, and that row reads back as data
     with the content; the row carries no legacy hash id;
  2. a write at row 123 into a list whose last row is 12 lays 13..122 NOTCACHED and 123 as data, and
     a read of row 50 with a master-fetch returns the master's data and leaves row 50 data locally;
  3. void(row) leaves the row VOID with its data cleared, and the next reserve on the home box hands
     that row back before any new row;
  4. on a remote box (CAIRN_HOME_HOST set) reserve asks the injected home-reserver and mints no row
     itself; with no reserver it refuses, naming the home host, and nothing lands;
  5. a state off void/notcached/data, or a data row with no content, is refused by the write door
     naming the state and by the table's own CHECK;
  6. the same content deposited into two trees lands one node row and two leaves, and the second
     deposit appends an attestation;
  7. migrate_to_row_ids over scratch hash-keyed tables: the dry run writes nothing; the write lays one
     data row per old node in created order, maps every legacy id, carries embeddings and links onto
     rows, leaves every old table's rows as they were, keeps a legacy leaf walkable and a legacy keyed
     leaf findable, and a second write changes nothing.

THE WORLD: every table this proof touches is a ``store.scratch`` table, the trees module's table
names patched onto them for the length of a tooth. No live table is read or written.

    bin/cairn test cairn/devices/librarian/tools/trees/proofs/test_a_node_id_is_its_master_row_number.py
"""
from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"06db586bedfd": {
    "1": "test_a_deposit_returns_the_row_it_wrote",
    "2": "test_a_write_past_the_end_lays_the_gap_notcached_and_a_miss_is_fed_from_master",
    "3": "test_a_voided_row_is_cleared_and_handed_back_first",
    "4": "test_a_remote_box_asks_the_home_for_its_slot",
    "5": "test_a_state_off_the_three_is_refused_by_the_door_and_the_table",
    "6": "test_the_same_content_in_two_trees_is_one_row",
    "7": "test_the_migration_moves_hash_rows_to_row_numbers_and_drops_nothing",
}}

PROOF_TIMEOUT_S = 240

_PROV = {"source": "proof 06db586bedfd"}
_V = [1.0, 0.0, 0.0]


@contextlib.contextmanager
def _home(host: str | None):
    saved = os.environ.pop("CAIRN_HOME_HOST", None)
    if host is not None:
        os.environ["CAIRN_HOME_HOST"] = host
    try:
        yield
    finally:
        os.environ.pop("CAIRN_HOME_HOST", None)
        if saved is not None:
            os.environ["CAIRN_HOME_HOST"] = saved


@contextlib.contextmanager
def _world():
    """Scratch node, embedding, link and content-index tables patched onto trees; the home box."""
    from cairn.devices.db_domain.tools.client import store
    from cairn.devices.librarian.tools.trees import trees as t
    with contextlib.ExitStack() as stack:
        names = {
            "NODES_TABLE": stack.enter_context(store.scratch(t.OWNER, "rowid_nodes", t._NODE_COLUMNS)),
            "EMBEDDINGS_TABLE": stack.enter_context(store.scratch(t.OWNER, "rowid_emb", t._EMBEDDING_COLUMNS)),
            "LINKS_TABLE": stack.enter_context(store.scratch(t.OWNER, "rowid_links", t._LINK_COLUMNS)),
            "CONTENT_INDEX": stack.enter_context(store.scratch(t.OWNER, "rowid_index", t._CONTENT_INDEX_COLUMNS)),
        }
        saved = {k: getattr(t, k) for k in names}
        for k, v in names.items():
            setattr(t, k, v)
        stack.enter_context(_home(None))
        try:
            yield t, names
        finally:
            for k, v in saved.items():
                setattr(t, k, v)


def _rows(t):
    from cairn.devices.db_domain.tools.client import store
    return {r["node_id"]: r for r in store.read(t.NODES_TABLE)}


def test_a_deposit_returns_the_row_it_wrote():
    with _world() as (t, _):
        with t.scratch_leaf("rowid_leaf1") as leaf:
            r = t.deposit("a node addressed by its row, tooth one", _V, _PROV, table=leaf)
            nid = r["node_id"]
            assert isinstance(nid, int) and not isinstance(nid, bool), f"node_id is not a row number: {r}"
            got = t.read_node(nid)
            assert got["state"] == t.DATA and got["content"] == "a node addressed by its row, tooth one", got
            assert got.get("legacy_id") is None, f"a new row carries a hash id: {got}"
            assert not hasattr(t, "node_id_for"), "node_id_for (a content hash id) still stands"


def test_a_write_past_the_end_lays_the_gap_notcached_and_a_miss_is_fed_from_master():
    with _world() as (t, _):
        for row in range(1, 13):
            t.write_node(row, f"row {row} of the first twelve", _PROV)
        t.write_node(123, "row one hundred twenty three", _PROV)
        rows = _rows(t)
        assert sorted(rows) == list(range(1, 124)), f"rows held: {len(rows)}"
        gap = {rows[r]["state"] for r in range(13, 123)}
        assert gap == {t.NOTCACHED}, f"the gap is not NOTCACHED: {gap}"
        assert rows[123]["state"] == t.DATA, rows[123]
        asked = []

        def fetch(row):
            asked.append(row)
            return {"content": f"row {row} as the master holds it", "provenance": _PROV,
                    "standing": "hypothesis"}
        got = t.read_node(50, fetch=fetch)
        assert asked == [50], f"the master was asked for {asked}"
        assert got["state"] == t.DATA and got["content"] == "row 50 as the master holds it", got
        assert _rows(t)[50]["state"] == t.DATA, "the fed row did not populate the local copy"
        assert t.read_node(51)["state"] == t.NOTCACHED, "a read with no master-fetch invented data"


def test_a_voided_row_is_cleared_and_handed_back_first():
    with _world() as (t, _):
        for row in range(1, 4):
            t.write_node(row, f"row {row} before the void", _PROV)
        t.void(2)
        got = t.read_node(2)
        assert got["state"] == t.VOID and got["content"] is None and got["provenance"] is None, got
        assert t.reserve() == 2, "the voided row was not handed back first"
        assert t.reserve() == 4, "after the void is used, the next row is not max+1"


def test_a_remote_box_asks_the_home_for_its_slot():
    with _world() as (t, _):
        t.write_node(1, "row one on the remote box", _PROV)
        with _home("homebox"):
            asked = []
            got = t.reserve(reserver=lambda: asked.append(1) or 40)
            assert got == 40 and asked == [1], (got, asked)
            assert max(_rows(t)) <= 40, f"the remote minted past the home's slot: {max(_rows(t))}"
            before = len(_rows(t))
            try:
                t.reserve()
            except t.ReserveRefused as e:
                assert "homebox" in str(e), str(e)
            else:
                raise AssertionError("a remote box reserved a slot with no home-reserver")
            assert len(_rows(t)) == before, "a refused reserve landed a row"


def test_a_state_off_the_three_is_refused_by_the_door_and_the_table():
    from cairn.devices.db_domain.tools.client import store
    with _world() as (t, _):
        t.ensure_nodes()
        for bad in ({"state": "reserved"}, {"state": t.DATA, "content": None}):
            try:
                t.write_node(7, bad.get("content", "content long enough"), _PROV, state=bad["state"])
            except t.DepositRefused as e:
                assert str(bad["state"]) in str(e), str(e)
            else:
                raise AssertionError(f"the door wrote {bad}")
            try:
                store.write(t.NODES_TABLE, t.OWNER, {"node_id": 7, "state": bad["state"],
                                                     "content": bad.get("content", "x" * 12)})
            except Exception as e:  # noqa: BLE001
                assert "check" in str(e).lower(), str(e)
            else:
                raise AssertionError(f"the table took {bad}")
        assert 7 not in _rows(t), "a refused state landed"


def test_the_same_content_in_two_trees_is_one_row():
    with _world() as (t, _):
        with t.scratch_leaf("rowid_leafa") as a, t.scratch_leaf("rowid_leafb") as b:
            text = "one claim held by two trees, tooth six"
            ra = t.deposit(text, _V, _PROV, table=a)
            rb = t.deposit(text, _V, {"source": "the second tree"}, table=b)
            assert ra["node_id"] == rb["node_id"], (ra, rb)
            held = [r for r in _rows(t).values() if r["content"] == text]
            assert len(held) == 1, f"{len(held)} rows hold the one content"
            assert len(held[0]["provenance"].get("attestations") or []) == 1, held[0]["provenance"]
            from cairn.devices.db_domain.tools.client import store
            assert len(store.read(a)) == 1 and len(store.read(b)) == 1


def test_the_migration_moves_hash_rows_to_row_numbers_and_drops_nothing():
    from cairn.devices.db_domain.tools.client import store
    from cairn.devices.librarian.tools.trees import migrate_to_row_ids as M
    with _world() as (t, _), contextlib.ExitStack() as stack:
        old_nodes = stack.enter_context(store.scratch(t.OWNER, "rowid_old_nodes", M.LEGACY_NODE_COLUMNS))
        old_emb = stack.enter_context(store.scratch(t.OWNER, "rowid_old_emb", M.LEGACY_EMBEDDING_COLUMNS))
        old_links = stack.enter_context(store.scratch(t.OWNER, "rowid_old_links", M.LEGACY_LINK_COLUMNS))
        vleaf = stack.enter_context(store.scratch("codemother", "rowid_old_vleaf", M.LEGACY_LEAF_COLUMNS))
        kleaf = stack.enter_context(store.scratch("codemother", "rowid_old_kleaf", t._KEYED_LEAF_COLUMNS))
        hashes = ["aaaa000000000001", "aaaa000000000002", "aaaa000000000003"]
        for i, h in enumerate(hashes):
            store.write(old_nodes, t.OWNER, {
                "node_id": h, "content": f"legacy node number {i + 1}", "provenance": _PROV,
                "standing": "hypothesis", "created": f"2026-01-0{i + 1}T00:00:00+00:00"})
        for i, h in enumerate(hashes[:2]):
            store.write(old_emb, t.OWNER, {"embedding_id": f"e{i}", "node_id": h,
                                           "vector": [1.0, float(i), 0.0], "render_method": "embed:default"})
            store.write(vleaf, "codemother", {"leaf_id": f"l{i}", "node_id": h, "embedding_id": f"e{i}"})
        store.write(kleaf, "codemother", {"leaf_id": "k0", "key": "the legacy key", "node_id": hashes[2]})
        store.write(old_links, t.OWNER, {"link_id": "x0", "source_id": hashes[0], "target_id": hashes[1],
                                         "weight": 0.5})
        legacy = {"nodes": old_nodes, "embeddings": old_emb, "links": old_links}
        counts = lambda: {k: len(store.read(v)) for k, v in legacy.items()}  # noqa: E731
        before = counts()

        dry = M.migrate(legacy=legacy, write=False)
        assert _rows(t) == {} and store.read(t.EMBEDDINGS_TABLE) == [], "the dry run wrote"
        assert dry["would_lay"] == 3, dry

        done = M.migrate(legacy=legacy, write=True)
        rows = _rows(t)
        by_legacy = {r["legacy_id"]: n for n, r in rows.items()}
        assert [by_legacy[h] for h in hashes] == sorted(by_legacy.values()), \
            f"rows not laid in created order: {by_legacy}"
        assert all(rows[n]["state"] == t.DATA for n in by_legacy.values()), rows
        emb = {e["embedding_id"]: e["node_id"] for e in store.read(t.EMBEDDINGS_TABLE)}
        assert emb == {"e0": by_legacy[hashes[0]], "e1": by_legacy[hashes[1]]}, emb
        lk = store.read(t.LINKS_TABLE)
        assert [(l["source_id"], l["target_id"]) for l in lk] == [(by_legacy[hashes[0]], by_legacy[hashes[1]])], lk
        assert counts() == before, f"an old table changed: {before} -> {counts()}"
        assert done["unmapped"] == 0, done

        walked = sorted(r["node_id"] for r in t._leaf_rows(table=vleaf, conn=store.connect()))
        assert walked == sorted([by_legacy[hashes[0]], by_legacy[hashes[1]]]), walked
        found = t.find("the legacy key", table=kleaf)
        assert [f["node_id"] for f in found] == [by_legacy[hashes[2]]], found

        again = M.migrate(legacy=legacy, write=True)
        assert again["laid"] == 0 and len(_rows(t)) == 3 and counts() == before, again


TEETH = [test_a_deposit_returns_the_row_it_wrote,
         test_a_write_past_the_end_lays_the_gap_notcached_and_a_miss_is_fed_from_master,
         test_a_voided_row_is_cleared_and_handed_back_first,
         test_a_remote_box_asks_the_home_for_its_slot,
         test_a_state_off_the_three_is_refused_by_the_door_and_the_table,
         test_the_same_content_in_two_trees_is_one_row,
         test_the_migration_moves_hash_rows_to_row_numbers_and_drops_nothing]


def main() -> int:
    failed = 0
    for tooth in TEETH:
        try:
            tooth()
            print(f"  ok    {tooth.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {str(e)[:1200]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

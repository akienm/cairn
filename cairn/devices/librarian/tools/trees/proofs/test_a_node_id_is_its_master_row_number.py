"""A librarian node is addressed by its master row: the Q#108 memory schema (ticket 06db586bedfd).

Akien, Q#104, 2026-11-14 (outline 4.3.1.5.1.2): "there shall be no data node ids based on anything
other than master row number". Q#108 (4.3.1.5.1.6): every reference is one 64-bit address, a 16-bit
table tag over a 48-bit row; nodes, lists, links and blobs; gen; void walks `in`; seq feeds the sync;
confidence lives in meta. Q#109: dedup stays, "already there?" asks a keyed content index, never a
node search. Q#111: the storage layer is blob rows (row/gen/state/kind/bytes), nothing file-based.

  1. deposit returns a nodes-tag address whose row reads back as data with the content; the leaf
     row stores the address and carries its own row; the node's in-list holds the leaf's address,
     whose tag the home's tag registry handed out from 0x0100; node_id_for is gone;
  2. a write at row 123 into a list whose last row is 12 lays 13..122 NOTCACHED, and a read of row
     50 with a master-fetch returns the master's data and leaves row 50 data locally;
  3. void walks the node's in-list: it removes itself from each linked source's out-list, drops the
     leaf that held it, clears its data and bumps gen; a Ref taken before reads Gone; the next home
     reserve hands the row back first;
  4. on a remote box reserve asks the injected home-reserver and mints nothing itself; with no
     reserver it refuses, naming the home host, and nothing lands;
  5. the door refuses a state off the three and a data row with no payload; the tables' own CHECKs
     refuse a state off the three, a data node with neither payload nor blob, a VOID node holding
     data, and a list whose weights do not pair with its items;
  6. a link is one row held in a.out and b.in; linking the pair again, either way round, is that
     row; traverse bumps traversals on it;
  7. a list longer than a chunk chains through next, every chunk within the chunk size, and reads
     back whole and in order;
  8. a payload past the inline bound lands as a blob row (kind text) the node points at, reads back
     whole, and the blob table is row/gen/state/kind/bytes/seq and nothing file-based;
  9. seq strictly increases across a node's write, its meta update and its void;
 10. a fresh node carries no confidence key and reads "unscored";
 11. the same content deposited into two trees is one node with two leaves and one attestation, and
     deposit asks "already held?" only through the seam: the content index is touched by the seam
     alone, and whatever node the seam names is the node the deposit attests onto;
 12. the sibling keyed-find proof is green, and migrate_to_row_ids is gone from the tool.

THE WORLD: every table this proof touches is a ``store.scratch`` table, the trees module's table
names patched onto them for the length of a tooth. No live table is read or written.

    bin/cairn test cairn/devices/librarian/tools/trees/proofs/test_a_node_id_is_its_master_row_number.py
"""
from __future__ import annotations

import ast
import contextlib
import importlib
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"06db586bedfd": {
    "1": "test_a_deposit_returns_a_node_address_its_leaf_holds_back",
    "2": "test_a_write_past_the_end_lays_the_gap_notcached_and_a_miss_is_fed_from_master",
    "3": "test_void_walks_in_unhooks_its_sources_and_a_stale_ref_reads_gone",
    "4": "test_a_remote_box_asks_the_home_for_its_slot",
    "5": "test_a_row_off_its_shape_is_refused_by_the_door_and_the_tables",
    "6": "test_a_link_is_one_row_held_by_both_endpoints",
    "7": "test_a_long_list_chains_through_next",
    "8": "test_a_large_payload_is_a_blob_row",
    "9": "test_seq_strictly_increases_on_every_write",
    "10": "test_a_fresh_node_is_unscored",
    "11": "test_dedup_asks_one_seam_and_the_same_content_is_one_node",
    "12": "test_the_sibling_proof_is_green_and_the_old_migration_is_gone",
}}

PROOF_TIMEOUT_S = 240

_PROV = {"source": "proof 06db586bedfd"}
_V = [1.0, 0.0, 0.0]
_TOOL = Path(__file__).resolve().parents[1]


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
def _patched(mod, **values):
    saved = {k: getattr(mod, k) for k in values}
    for k, v in values.items():
        setattr(mod, k, v)
    try:
        yield
    finally:
        for k, v in saved.items():
            setattr(mod, k, v)


@contextlib.contextmanager
def _world():
    """Scratch nodes, lists, links, blobs, content index, embeddings and tag registry, patched
    onto trees; the home box."""
    from cairn.devices.db_domain.tools.client import store
    from cairn.devices.librarian.tools.trees import trees as t
    with contextlib.ExitStack() as stack:
        def s(prefix, cols):
            return stack.enter_context(store.scratch(t.OWNER, prefix, cols))
        names = {
            "NODES_TABLE": s("mem_nodes", t._NODE_COLUMNS),
            "LISTS_TABLE": s("mem_lists", t._LIST_COLUMNS),
            "LINKS_TABLE": s("mem_links", t._LINK_COLUMNS),
            "BLOBS_TABLE": s("mem_blobs", t._BLOB_COLUMNS),
            "TAGS_TABLE": s("mem_tags", t._TAG_COLUMNS),
            "EMBEDDINGS_TABLE": s("mem_emb", t._EMBEDDING_COLUMNS),
            "CONTENT_INDEX": s("mem_index", t._CONTENT_INDEX_COLUMNS),
        }
        stack.enter_context(_patched(t, **names))
        stack.enter_context(_home(None))
        yield t, names


def _rows(t, table=None):
    from cairn.devices.db_domain.tools.client import store
    return {r["row"]: r for r in store.read(table or t.NODES_TABLE)}


def _A():
    from cairn.tools.node_address import node_address as A
    return A


def test_a_deposit_returns_a_node_address_its_leaf_holds_back():
    A = _A()
    from cairn.devices.db_domain.tools.client import store
    with _world() as (t, names):
        with t.scratch_leaf("mem_leaf1") as leaf:
            r = t.deposit("a node addressed by its row, tooth one", _V, _PROV, table=leaf)
            addr = r["node_id"]
            assert isinstance(addr, int) and not isinstance(addr, bool), r
            assert A.tag_of(addr) == A.tag_for("nodes"), f"not a nodes address: {r}"
            got = t.read_node(addr)
            assert got["state"] == t.DATA and got["content"] == "a node addressed by its row, tooth one", got
            assert got["row"] == A.row_of(addr), got
            leaves = store.read(leaf)
            assert len(leaves) == 1 and int(leaves[0]["node_id"]) == addr, leaves
            assert isinstance(leaves[0]["row"], int) and leaves[0]["row"] >= 1, leaves
            tag = t.leaf_tag(leaf)
            assert tag >= 0x0100, f"a leaf tag below the registry's floor: {tag:#x}"
            assert {r["name"]: r["tag"] for r in store.read(names["TAGS_TABLE"])}.get(leaf) == tag
            assert A.pack(tag, leaves[0]["row"]) in t.list_items(got["in_list"]), \
                "the node's in-list does not hold its leaf"
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


def test_void_walks_in_unhooks_its_sources_and_a_stale_ref_reads_gone():
    A = _A()
    from cairn.devices.db_domain.tools.client import store
    with _world() as (t, _):
        with t.scratch_leaf("mem_leaf3") as leaf:
            a = t.deposit("the node that will be voided, tooth three", _V, _PROV, table=leaf)["node_id"]
            src = t.write_node(2, "a source that links to the voided node", _PROV)
            dst = t.write_node(3, "a target the voided node links to", _PROV)
            t.link(src, a, 0.5)
            t.link(a, dst, 0.7)
            before = t.read_node(a)
            ref = A.Ref(a, before["gen"])
            assert t.list_items(t.read_node(src)["out_list"]), "the source's out-list is empty before"
            t.void(a)
            got = t.read_node(a)
            assert got["state"] == t.VOID and got["content"] is None and got["meta"] is None, got
            assert got["gen"] == before["gen"] + 1, (before["gen"], got["gen"])
            assert t.list_items(t.read_node(src)["out_list"]) == [], "the source still holds a link to it"
            assert t.list_items(t.read_node(dst)["in_list"]) == [], "the target still holds its link"
            assert store.read(leaf) == [], "the leaf that held it still stands"
            try:
                t.read_node(ref)
            except t.Gone as e:
                assert str(A.row_of(a)) in str(e), str(e)
            else:
                raise AssertionError("a Ref from before the void read the row")
            assert t.reserve() == A.row_of(a), "the voided row was not handed back first"
            assert t.reserve() == 4, "after the void is used, the next row is not max+1"


def test_a_remote_box_asks_the_home_for_its_slot():
    with _world() as (t, _):
        t.write_node(1, "row one on the remote box", _PROV)
        with _home("homebox"):
            asked = []
            got = t.reserve(reserver=lambda kind: asked.append(kind) or 40)
            assert got == 40 and asked == ["nodes"], (got, asked)
            assert max(_rows(t)) <= 40, f"the remote minted past the home's slot: {max(_rows(t))}"
            before = len(_rows(t))
            try:
                t.reserve()
            except t.ReserveRefused as e:
                assert "homebox" in str(e), str(e)
            else:
                raise AssertionError("a remote box reserved a slot with no home-reserver")
            assert len(_rows(t)) == before, "a refused reserve landed a row"


def _table_refuses(table, owner, row):
    from cairn.devices.db_domain.tools.client import store
    try:
        store.write(table, owner, row)
    except Exception as e:  # noqa: BLE001
        assert "check" in str(e).lower(), str(e)
    else:
        raise AssertionError(f"{table} took {row}")


def test_a_row_off_its_shape_is_refused_by_the_door_and_the_tables():
    with _world() as (t, names):
        t.ensure_nodes()
        for state, content in (("reserved", "content long enough"), (t.DATA, None)):
            try:
                t.write_node(7, content, _PROV, state=state)
            except t.DepositRefused as e:
                assert str(state) in str(e), str(e)
            else:
                raise AssertionError(f"the door wrote state={state!r} content={content!r}")
        n = names["NODES_TABLE"]
        _table_refuses(n, t.OWNER, {"row": 7, "gen": 0, "seq": 901, "state": "reserved"})
        _table_refuses(n, t.OWNER, {"row": 7, "gen": 0, "seq": 902, "state": t.DATA, "kind": "text",
                                    "meta": {"provenance": _PROV}})
        _table_refuses(n, t.OWNER, {"row": 7, "gen": 0, "seq": 903, "state": t.VOID,
                                    "payload": "a void row holding data"})
        _table_refuses(names["LISTS_TABLE"], t.OWNER, {"row": 1, "gen": 0, "seq": 904, "state": t.DATA,
                                                       "items": "{1,2,3}", "weights": "{0.5}"})
        assert 7 not in _rows(t), "a refused row landed"


def test_a_link_is_one_row_held_by_both_endpoints():
    A = _A()
    with _world() as (t, names):
        a = t.write_node(1, "endpoint a of tooth six", _PROV)
        b = t.write_node(2, "endpoint b of tooth six", _PROV)
        first = t.link(a, b, 0.4)
        again = t.link(b, a, 0.9)
        links = _rows(t, names["LINKS_TABLE"])
        assert len(links) == 1, f"{len(links)} link rows for one pair"
        laddr = first["link"]
        assert again["link"] == laddr and A.tag_of(laddr) == A.tag_for("links"), (first, again)
        assert t.list_items(t.read_node(a)["out_list"]) == [laddr], "a.out does not hold the link"
        assert t.list_items(t.read_node(b)["in_list"]) == [laddr], "b.in does not hold the link"
        assert abs(links[A.row_of(laddr)]["weight"] - 0.9) < 1e-6, links
        t.traverse_link(a, b)
        t.traverse_link(b, a)
        assert _rows(t, names["LINKS_TABLE"])[A.row_of(laddr)]["traversals"] == 2


def test_a_long_list_chains_through_next():
    from cairn.devices.db_domain.tools.client import store
    with _world() as (t, names):
        with _patched(t, LIST_CHUNK=3):
            a = t.write_node(1, "the hub of tooth seven", _PROV)
            targets = [t.write_node(r, f"spoke {r} of tooth seven", _PROV) for r in range(2, 9)]
            made = [t.link(a, x, 0.5)["link"] for x in targets]
            head = t.read_node(a)["out_list"]
            assert t.list_items(head) == made, "the chained list does not read back whole and in order"
            chunks = [r for r in store.read(names["LISTS_TABLE"]) if r["state"] == t.DATA]
            assert all(len(c["items"]) <= 3 for c in chunks), [len(c["items"]) for c in chunks]
            assert sum(1 for c in chunks if c["next"]) >= 2, "seven items in chunks of three never chained"


def test_a_large_payload_is_a_blob_row():
    A = _A()
    with _world() as (t, names):
        with _patched(t, INLINE_MAX=64), t.scratch_leaf("mem_leaf8") as leaf:
            text = "a payload past the inline bound, tooth eight. " * 5
            addr = t.deposit(text, _V, _PROV, table=leaf)["node_id"]
            row = _rows(t)[A.row_of(addr)]
            assert row["payload"] is None and row["blob"], row
            assert A.tag_of(row["blob"]) == A.tag_for("blobs"), row
            blob = _rows(t, names["BLOBS_TABLE"])[A.row_of(row["blob"])]
            assert blob["kind"] == "text" and bytes(blob["bytes"]).decode() == text, blob["kind"]
            assert t.read_node(addr)["content"] == text
        assert set(t._BLOB_COLUMNS) == {"row", "gen", "state", "kind", "bytes", "seq"}, t._BLOB_COLUMNS


def test_seq_strictly_increases_on_every_write():
    with _world() as (t, _):
        seen = []
        r = t.write_node(1, "a row whose seq is watched, tooth nine", _PROV)
        seen.append(_rows(t)[1]["seq"])
        t.write_node(2, "a second row", _PROV)
        seen.append(_rows(t)[2]["seq"])
        t.corroborate(r, "a question that touches row one's meta", promote_at=99)
        seen.append(_rows(t)[1]["seq"])
        t.void(r)
        seen.append(_rows(t)[1]["seq"])
        assert all(b > a for a, b in zip(seen, seen[1:])), seen


def test_a_fresh_node_is_unscored():
    with _world() as (t, _):
        with t.scratch_leaf("mem_leaf10") as leaf:
            addr = t.deposit("a node nobody has scored, tooth ten", _V, _PROV, table=leaf)["node_id"]
            meta = t.read_node(addr)["meta"]
            assert "confidence" not in meta, meta
            assert t.confidence(addr) == "unscored", t.confidence(addr)


def test_dedup_asks_one_seam_and_the_same_content_is_one_node():
    from cairn.devices.db_domain.tools.client import store
    with _world() as (t, _):
        with t.scratch_leaf("mem_leafa") as a, t.scratch_leaf("mem_leafb") as b:
            text = "one claim held by two trees, tooth eleven"
            ra = t.deposit(text, _V, _PROV, table=a)
            rb = t.deposit(text, _V, {"source": "the second tree"}, table=b)
            assert ra["node_id"] == rb["node_id"], (ra, rb)
            held = [r for r in _rows(t).values() if r["payload"] == text]
            assert len(held) == 1, f"{len(held)} rows hold the one content"
            assert len(held[0]["meta"]["provenance"].get("attestations") or []) == 1, held[0]["meta"]
            assert len(store.read(a)) == 1 and len(store.read(b)) == 1
            other = t.write_node(9, "a node only the patched seam names, tooth eleven", _PROV)
            with _patched(t, already_held=lambda content, *, conn: other):
                rc = t.deposit("content no index holds, tooth eleven", _V, _PROV, table=a)
            assert rc["node_id"] == other and rc["provenance_appended"], \
                f"deposit did not believe the seam: {rc}"
    src = (_TOOL / "trees.py").read_text(encoding="utf-8")
    users = set()
    for fn in ast.walk(ast.parse(src)):
        if isinstance(fn, ast.FunctionDef):
            if any(isinstance(n, ast.Name) and n.id == "CONTENT_INDEX" for n in ast.walk(fn)):
                users.add(fn.name)
    assert users <= {"already_held", "_hold_content", "_unhold_content", "ensure_nodes"}, \
        f"the content index is touched outside the seam: {sorted(users)}"


def test_the_sibling_proof_is_green_and_the_old_migration_is_gone():
    assert not (_TOOL / "migrate_to_row_ids.py").exists(), "migrate_to_row_ids.py still stands"
    sib = importlib.import_module(
        "cairn.devices.librarian.tools.trees.proofs.test_a_node_without_an_embedding_is_found_by_its_key")
    ran = [name for name in sorted(vars(sib)) if name.startswith("test_") and callable(getattr(sib, name))]
    assert ran, "the sibling proof has no teeth"
    for name in ran:
        getattr(sib, name)()


if __name__ == "__main__":
    failed = 0
    for name in sorted(PROVES["06db586bedfd"].items(), key=lambda kv: int(kv[0])):
        fn = globals()[name[1]]
        try:
            fn()
            print(f"ok   {name[1]}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name[1]}: {type(e).__name__}: {e}")
    print(f"{12 - failed}/12")
    sys.exit(1 if failed else 0)

"""Proof for ticket 26acbf5314a5: the hash-keyed librarian memory moves onto T2's rows
(migrate_to_row_ids.py), dropping nothing, idempotently.

One tooth per numbered falsifier clause:

  1. every legacy node lands as exactly one DATA row at a row trees.reserve() handed out, kind
     text, content inline (or a blob past INLINE_MAX), meta.provenance / meta.standing the
     legacy row's, meta.legacy_id the old hash;
  2. confidence is ABSENT from every migrated node's meta, even where the legacy provenance
     carries one (it stays inside meta.provenance), and trees.confidence reads unscored;
  3. every leaf table, vector and keyed, has row 1..n (no gap, null or duplicate; max(row) = n),
     held by a UNIQUE index that refuses a second row of the same value; node_id is the address
     as digits, legacy_node_id / legacy_leaf_id the old ids, leaf_id the one a deposit would
     compute, the tag from the registry at 0x0100 or above, and the node's in_list holds the leaf;
  4. embeddings land at trees.embedding_id_for(address, render_method) with the address, links
     land as one row each through trees.link with weight and traversals kept, and re-depositing
     migrated content after --write moves neither the embedding count nor the leaf count;
  5. the legacy nodes, embeddings and links keep their counts and contents, a leaf table its row
     count, and an embedding, link or leaf naming no node is named in the report, untouched;
  6. content already held at an address maps the legacy hash onto it, the legacy provenance
     appended as an attestation, and no second node row is laid;
  7. the dry run writes nothing, and a second --write lays no row, column, index or tag.

THE WORLD: store.scratch tables only. T2's seven tables as scratch with the trees module's names
patched onto them (CAIRN_HOME_HOST unset: the home), the three legacy tables in their pre-T2
shapes, and one vector and one keyed leaf in the legacy leaf shapes under a tenant owner.

    bin/cairn test cairn/devices/librarian/tools/trees/proofs/test_the_hash_keyed_memory_moves_onto_rows.py
"""
from __future__ import annotations

import contextlib
import hashlib
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"26acbf5314a5": {
    "1": "test_every_legacy_node_lands_as_one_data_row",
    "2": "test_confidence_is_absent",
    "3": "test_every_leaf_table_gains_its_rows",
    "4": "test_embeddings_and_links_follow_and_a_redeposit_lands_nothing",
    "5": "test_nothing_is_dropped_and_the_unmapped_are_named",
    "6": "test_held_content_takes_the_legacy_hash",
    "7": "test_the_dry_run_writes_nothing_and_a_second_write_lays_nothing",
}}

PROOF_TIMEOUT_S = 600

TENANT = "testing26ac"
METHOD = "embed:default"
_V1, _V2, _V3 = [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]


def _t():
    from cairn.devices.librarian.tools.trees import trees
    return trees


def _m():
    from cairn.devices.librarian.tools.trees import migrate_to_row_ids
    return migrate_to_row_ids


def _store():
    from cairn.devices.db_domain.tools.client import store
    return store


def _A():
    from cairn.tools.node_address import node_address
    return node_address


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


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


# The legacy corpus. N_CONF carries a confidence inside its provenance; N_LONG is past INLINE_MAX;
# N_HELD is deposited through T2 before the migration runs (clause 6).
N1 = "testing 26ac: the archive opens at nine on weekdays"
N_CONF = "testing 26ac: the stacks are shut on mondays entirely"
N_LONG = "testing 26ac: a long note. " + "the reading room keeps its ledgers. " * 140
N_HELD = "testing 26ac: content a deposit laid after T2 landed"
DEAD = "dead00000000beef"   # a hash no legacy node carries
PROV1 = {"source": "testing: 26acbf5314a5 legacy", "via": "a fold"}
PROV_CONF = {"source": "testing: 26acbf5314a5 legacy", "confidence": 0.8}


class World:
    """Names of every table the run holds, and the legacy ids it laid."""


@contextlib.contextmanager
def _world(*, held_first: bool = False):
    t, store, m = _t(), _store(), _m()
    saved_home = os.environ.pop("CAIRN_HOME_HOST", None)
    try:
        with contextlib.ExitStack() as stack:
            def s(owner, prefix, cols):
                return stack.enter_context(store.scratch(owner, f"m26ac_{prefix}", cols))
            new = {
                "NODES_TABLE": s(t.OWNER, "mem_nodes", t._NODE_COLUMNS),
                "LISTS_TABLE": s(t.OWNER, "mem_lists", t._LIST_COLUMNS),
                "LINKS_TABLE": s(t.OWNER, "mem_links", t._LINK_COLUMNS),
                "BLOBS_TABLE": s(t.OWNER, "mem_blobs", t._BLOB_COLUMNS),
                "TAGS_TABLE": s(t.OWNER, "mem_tags", t._TAG_COLUMNS),
                "EMBEDDINGS_TABLE": s(t.OWNER, "mem_emb", t._EMBEDDING_COLUMNS),
                "CONTENT_INDEX": s(t.OWNER, "mem_index", t._CONTENT_INDEX_COLUMNS),
            }
            w = World()
            w.new = new
            w.legacy = {"nodes": s(t.OWNER, "old_nodes", m.LEGACY_NODE_COLUMNS),
                        "embeddings": s(t.OWNER, "old_emb", m.LEGACY_EMBEDDING_COLUMNS),
                        "links": s(t.OWNER, "old_links", m.LEGACY_LINK_COLUMNS)}
            w.vec = s(TENANT, "old_leaf", m.LEGACY_LEAF_COLUMNS)
            w.keyed = s(TENANT, "old_keyed", m.LEGACY_KEYED_LEAF_COLUMNS)
            w.legacy_map = {**w.legacy, "leaves": [w.vec, w.keyed]}
            stack.enter_context(_patched(t, **new))
            _lay_legacy(w)
            if held_first:
                w.held_leaf = stack.enter_context(t.scratch_leaf("m26ac_held"))
                w.held_addr = t.deposit(N_HELD, _V3, {"source": "testing: 26ac after T2"},
                                        table=w.held_leaf)["node_id"]
            yield w
    finally:
        if saved_home is not None:
            os.environ["CAIRN_HOME_HOST"] = saved_home


def _lay_legacy(w) -> None:
    t, store = _t(), _store()
    w.h = {c: _hash(c) for c in (N1, N_CONF, N_LONG, N_HELD)}
    nodes = [(N1, PROV1, "hypothesis"), (N_CONF, PROV_CONF, "earned"),
             (N_LONG, PROV1, "hypothesis"), (N_HELD, PROV1, "hypothesis")]
    for content, prov, standing in nodes:
        store.write(w.legacy["nodes"], t.OWNER, {"node_id": w.h[content], "content": content,
                                                 "provenance": prov, "standing": standing})
    w.eid = {}
    for content, vec in ((N1, _V1), (N_CONF, _V2), (N_HELD, _V3)):
        eid = t.embedding_id_for(w.h[content], METHOD)
        w.eid[content] = eid
        store.write(w.legacy["embeddings"], t.OWNER, {"embedding_id": eid, "node_id": w.h[content],
                                                      "vector": vec, "render_method": METHOD})
    w.orphan_eid = t.embedding_id_for(DEAD, METHOD)
    store.write(w.legacy["embeddings"], t.OWNER, {"embedding_id": w.orphan_eid, "node_id": DEAD,
                                                  "vector": _V1, "render_method": METHOD})
    w.link_id, w.orphan_link = "l26ac0000000good", "l26ac00000000bad"
    store.write(w.legacy["links"], t.OWNER, {"link_id": w.link_id, "source_id": w.h[N1],
                                             "target_id": w.h[N_CONF], "weight": 0.75,
                                             "traversals": 4})
    store.write(w.legacy["links"], t.OWNER, {"link_id": w.orphan_link, "source_id": w.h[N1],
                                             "target_id": DEAD, "weight": 0.5, "traversals": 1})
    w.vec_leaves = {}
    for content in (N1, N_CONF, N_HELD):
        lid = t.leaf_id_for(w.h[content], w.eid[content])
        w.vec_leaves[content] = lid
        store.write(w.vec, TENANT, {"leaf_id": lid, "node_id": w.h[content],
                                    "embedding_id": w.eid[content]})
    w.orphan_leaf = t.leaf_id_for(DEAD, w.orphan_eid)
    store.write(w.vec, TENANT, {"leaf_id": w.orphan_leaf, "node_id": DEAD,
                                "embedding_id": w.orphan_eid})
    w.keys = {N1: "k-archive", N_LONG: "k-long", N_HELD: "k-held"}
    for content, key in w.keys.items():
        store.write(w.keyed, TENANT, {"leaf_id": t.leaf_id_for(w.h[content], key), "key": key,
                                      "node_id": w.h[content], "meta": {"verdict": "kept"}})


def _run(w, *, write: bool) -> dict:
    return _m().migrate(legacy=w.legacy_map, write=write)


def _data_nodes() -> list[dict]:
    t = _t()
    return _store().read(t.NODES_TABLE, where="state = %s", params=(t.DATA,))


def _node_by_content(content: str) -> list[dict]:
    t = _t()
    return [t._view(r, conn=None) for r in _data_nodes()
            if t._view(r, conn=None)["content"] == content]


def _addr_of(content: str) -> int:
    got = _node_by_content(content)
    assert len(got) == 1, f"{len(got)} DATA nodes hold {content[:40]!r}"
    return got[0]["node_id"]


def test_every_legacy_node_lands_as_one_data_row():
    t = _t()
    with _world() as w:
        handed: list[int] = []
        real = t.reserve

        def recording(**kw):
            row = real(**kw)
            handed.append(row)
            return row
        with _patched(t, reserve=recording):
            rep = _run(w, write=True)
        assert not _m().failed(rep), rep
        assert rep["nodes"]["laid"] == 4, rep["nodes"]
        legacy = {r["node_id"]: r for r in _store().read(w.legacy["nodes"])}
        for h, old in legacy.items():
            views = _node_by_content(old["content"])
            assert len(views) == 1, f"{h}: {len(views)} DATA rows"
            v = views[0]
            assert v["row"] in handed, f"{h} sits at row {v['row']}, not one reserve() handed out"
            assert v["kind"] == "text", v["kind"]
            assert v["meta"]["provenance"] == old["provenance"], (v["meta"], old["provenance"])
            assert v["meta"]["standing"] == old["standing"], v["meta"]
            assert v["meta"]["legacy_id"] == h, v["meta"]
            if len(old["content"]) > t.INLINE_MAX:
                assert v["payload"] is None and v["blob"], "a long node is not a blob"
            else:
                assert v["payload"] == old["content"] and not v["blob"], v
        assert len(_data_nodes()) == 4, f"{len(_data_nodes())} DATA nodes for 4 legacy nodes"


def test_confidence_is_absent():
    t = _t()
    with _world() as w:
        _run(w, write=True)
        for r in _data_nodes():
            assert "confidence" not in (r["meta"] or {}), f"row {r['row']} meta: {r['meta']}"
        conf = _node_by_content(N_CONF)[0]
        assert conf["meta"]["provenance"]["confidence"] == 0.8, conf["meta"]
        for content in (N1, N_CONF, N_LONG):
            assert t.confidence(_addr_of(content)) == "unscored", content[:30]
        assert "confidence" not in t.read_node(_addr_of(N_CONF)).get("meta", {}), "read_node"


def _indexes(table: str) -> list[dict]:
    return _store().query("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = %s",
                          tables={}, params=(table,))


def test_every_leaf_table_gains_its_rows():
    t, store, A = _t(), _store(), _A()
    with _world() as w:
        rep = _run(w, write=True)
        found, skipped = _m().standing_leaves(legacy=w.legacy, conn=None)
        assert w.vec in skipped and w.keyed in skipped and w.vec not in found, \
            "a scratch-shaped leaf is not read as scratch"
        tags = {r["name"]: r["tag"] for r in store.read(t.TAGS_TABLE)}
        for table, n in ((w.vec, 4), (w.keyed, 3)):
            rows = store.read(table)
            assert sorted(r["row"] for r in rows) == list(range(1, n + 1)), \
                (table, [r["row"] for r in rows])
            top = store.query("SELECT max(row) AS m FROM {t}", tables={"t": table})[0]["m"]
            assert top == n, (table, top)
            assert any("UNIQUE" in i["indexdef"] and i["indexdef"].replace('"', '').endswith("(row)")
                       for i in _indexes(table)), _indexes(table)
            assert table in tags and tags[table] >= t.LEAF_TAG_FLOOR, tags
            keyed = table == w.keyed
            for r in rows:
                if r["node_id"] == DEAD:
                    continue
                addr = int(r["node_id"])
                assert r["legacy_node_id"] in w.h.values(), r
                content = next(c for c, h in w.h.items() if h == r["legacy_node_id"])
                assert addr == _addr_of(content), r
                if keyed:
                    assert r["legacy_leaf_id"] == t.leaf_id_for(r["legacy_node_id"], r["key"])
                    assert r["leaf_id"] == t.leaf_id_for(addr, r["key"]), r
                else:
                    assert r["legacy_leaf_id"] == w.vec_leaves[content], r
                    assert r["embedding_id"] == t.embedding_id_for(addr, METHOD), r
                    assert r["leaf_id"] == t.leaf_id_for(addr, r["embedding_id"]), r
                in_list = t.list_items(store.read(t.NODES_TABLE, where="row = %s",
                                                  params=(A.row_of(addr),))[0]["in_list"])
                assert A.pack(tags[table], r["row"]) in in_list, (table, r["row"], in_list)
        # the row column is held by the UNIQUE index: a second row of the same value is refused
        try:
            store.write(w.keyed, TENANT, {"leaf_id": "testing26acdup", "key": "k-dup",
                                          "node_id": "1", "row": 1})
        except Exception as e:  # noqa: BLE001 — the database's own refusal is the measurement
            assert "duplicate key" in str(e) or "unique" in str(e).lower(), str(e)
        else:
            raise AssertionError("a second leaf with row 1 was not refused")
        assert len(store.read(w.keyed)) == 3, "the refused duplicate landed"
        assert rep["legacy_unchanged"], rep


def test_embeddings_and_links_follow_and_a_redeposit_lands_nothing():
    t, store, A = _t(), _store(), _A()
    with _world() as w:
        rep = _run(w, write=True)
        embs = {r["embedding_id"]: r for r in store.read(t.EMBEDDINGS_TABLE)}
        assert len(embs) == 3, sorted(embs)
        for content in (N1, N_CONF, N_HELD):
            addr = _addr_of(content)
            eid = t.embedding_id_for(addr, METHOD)
            assert eid in embs and int(embs[eid]["node_id"]) == addr, (content[:30], embs.get(eid))
        links = store.read(t.LINKS_TABLE, where="state = %s", params=(t.DATA,))
        assert len(links) == 1, links
        a, b = _addr_of(N1), _addr_of(N_CONF)
        lk = links[0]
        assert {lk["a"], lk["b"]} == {a, b}, lk
        assert abs(lk["weight"] - 0.75) < 1e-6 and lk["traversals"] == 4, lk
        got = [x for x in t.linked(a) if {x["source_id"], x["target_id"]} == {a, b}]
        assert len(got) == 1, t.linked(a)
        assert rep["links"]["laid"] == 1, rep["links"]

        # a deposit of migrated content lands no second embedding and no second leaf
        n_emb, n_vec, n_key = (len(store.read(x)) for x in (t.EMBEDDINGS_TABLE, w.vec, w.keyed))
        again = t.deposit(N1, _V1, {"source": "testing: 26ac re-deposit"}, table=w.vec,
                          owner=TENANT, render_method=METHOD)
        assert again["node_id"] == a, again
        t.deposit_keyed(N1, w.keys[N1], {"source": "testing: 26ac re-deposit"}, table=w.keyed,
                        owner=TENANT)
        assert len(store.read(t.EMBEDDINGS_TABLE)) == n_emb, "a re-deposit laid an embedding"
        assert len(store.read(w.vec)) == n_vec, "a re-deposit laid a second vector leaf"
        assert len(store.read(w.keyed)) == n_key, "a re-deposit laid a second keyed leaf"
        assert again["duplicate"], again


def _snapshot(table: str) -> list:
    rows = _store().read(table)
    return sorted((sorted((k, repr(v)) for k, v in r.items()) for r in rows))


def test_nothing_is_dropped_and_the_unmapped_are_named():
    store = _store()
    with _world() as w:
        before = {k: _snapshot(v) for k, v in w.legacy.items()}
        counts = {x: len(store.read(x)) for x in (w.vec, w.keyed)}
        rep = _run(w, write=True)
        assert {k: _snapshot(v) for k, v in w.legacy.items()} == before, "a legacy row moved"
        assert {x: len(store.read(x)) for x in (w.vec, w.keyed)} == counts, "a leaf row went"
        assert rep["legacy_unchanged"] and not _m().failed(rep), rep
        assert rep["embeddings"]["unmapped"] == [w.orphan_eid], rep["embeddings"]
        assert rep["links"]["unmapped"] == [w.orphan_link], rep["links"]
        vec_rep = next(x for x in rep["leaves"] if x["table"] == w.vec)
        assert vec_rep["unmapped"] == [w.orphan_leaf], vec_rep
        orphan = store.read(w.vec, where="node_id = %s", params=(DEAD,))
        assert len(orphan) == 1 and orphan[0]["leaf_id"] == w.orphan_leaf \
            and orphan[0]["legacy_node_id"] is None \
            and orphan[0]["embedding_id"] == w.orphan_eid, orphan


def test_held_content_takes_the_legacy_hash():
    store = _store()
    with _world(held_first=True) as w:
        rep = _run(w, write=True)
        assert rep["nodes"]["mapped_onto_held"] == 1 and rep["nodes"]["laid"] == 3, rep["nodes"]
        views = _node_by_content(N_HELD)
        assert len(views) == 1, f"{len(views)} DATA nodes hold the held content"
        v = views[0]
        assert v["node_id"] == w.held_addr, (v["node_id"], w.held_addr)
        attests = v["meta"]["provenance"].get("attestations") or []
        mine = [a for a in attests if a.get("legacy_id") == w.h[N_HELD]]
        assert len(mine) == 1 and mine[0]["source"] == PROV1["source"], attests
        key_leaf = store.read(w.keyed, where="key = %s", params=(w.keys[N_HELD],))[0]
        assert int(key_leaf["node_id"]) == w.held_addr, key_leaf
        assert len(_data_nodes()) == 4, "a second node row was laid for held content"


def _census(w) -> dict:
    t, store = _t(), _store()
    tables = [*w.new.values(), *w.legacy.values(), w.vec, w.keyed]
    return {
        "rows": {x: _snapshot(x) for x in tables},
        "columns": {x: sorted(_m()._columns(x, conn=None)) for x in (w.vec, w.keyed)},
        "indexes": {x: sorted(i["indexname"] for i in _indexes(x)) for x in (w.vec, w.keyed)},
        "tags": _snapshot(t.TAGS_TABLE),
    }


def test_the_dry_run_writes_nothing_and_a_second_write_lays_nothing():
    with _world() as w:
        before = _census(w)
        dry = _run(w, write=False)
        assert _census(w) == before, "the dry run wrote"
        assert dry["nodes"]["laid"] == 4 and dry["links"]["laid"] == 1, dry
        assert all(x["columns_added"] == ["row", "legacy_node_id", "legacy_leaf_id"]
                   for x in dry["leaves"]), dry["leaves"]
        _run(w, write=True)
        first = _census(w)
        second = _run(w, write=True)
        after = _census(w)
        for part in ("columns", "indexes", "tags"):
            assert after[part] == first[part], f"a second --write moved the {part}"
        moved = [x for x in first["rows"]
                 if len(after["rows"][x]) != len(first["rows"][x])]
        assert not moved, f"a second --write laid rows in {moved}"
        assert second["nodes"]["laid"] == 0 and second["nodes"]["already"] == 4, second["nodes"]
        assert second["embeddings"]["laid"] == 0 and second["links"]["laid"] == 0, second
        assert all(x["columns_added"] == [] and x["rows_filled"] == 0 and x["rewritten"] == 0
                   for x in second["leaves"]), second["leaves"]


TEETH = [test_every_legacy_node_lands_as_one_data_row,
         test_confidence_is_absent,
         test_every_leaf_table_gains_its_rows,
         test_embeddings_and_links_follow_and_a_redeposit_lands_nothing,
         test_nothing_is_dropped_and_the_unmapped_are_named,
         test_held_content_takes_the_legacy_hash,
         test_the_dry_run_writes_nothing_and_a_second_write_lays_nothing]


if __name__ == "__main__":
    passed = failed = 0
    for fn in TEETH:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
            failed += 1
            print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
        else:
            passed += 1
            print(f"  green {fn.__name__}")
    print(f"{passed} passed, {failed} failed out of {passed + failed}")
    sys.exit(1 if failed else 0)

"""Proof for ticket e62f40f35f59 — the trees tool keeps a node without an embedding and finds
it by its key.

Outline 4.3.1.6 (Akien 2026-11-05): "Not every node gets one ... A node without an embedding is
found by its key (eg an exact request)." This proof measures the trees tool's keyed leaf shape:
what deposit_keyed lands in the shared tables and a scratch keyed leaf, what find returns, and
that each shape's doors refuse the other.

One tooth per numbered falsifier clause:

  1. deposit_keyed lands one cairn_nodes row, no cairn_embeddings row, and one leaf row carrying
     the key and the meta.
  2. find(key) returns the node's content, provenance, standing and meta, newest first; an
     unknown key returns [].
  3. The same content under the same key twice leaves one leaf and appends an attestation; the
     same content under a second key leaves two leaves over one node.
  4. nearest and neighbors over a keyed table raise WalkRefused naming it keyed; deposit into a
     keyed table and deposit_keyed into a vectored one raise DepositRefused; nothing lands.
  5. deposit_keyed applies deposit's content floor and provenance rule, and refuses a blank key.
  6. A vectored deposit and walk are unchanged: one embedding row, found at similarity 1.
  7. The charter beside trees.py names deposit_keyed, find and the keyed leaf in its `what`.

Requires the db_domain provisioning; both leaf tables are scratch, and their nodes are forgotten
before they drop.

    bin/cairn test cairn/devices/librarian/tools/trees/proofs/test_a_node_without_an_embedding_is_found_by_its_key.py
"""

from __future__ import annotations

import contextlib
import json
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"e62f40f35f59": {
    "1": "a_keyed_deposit_lands_a_node_and_a_leaf_and_no_embedding",
    "2": "find_returns_the_nodes_under_a_key_newest_first",
    "3": "a_repeat_attests_and_a_second_key_adds_a_leaf",
    "4": "each_shape_refuses_the_other",
    "5": "the_keyed_door_judges_as_deposit_does",
    "6": "a_vectored_deposit_and_walk_are_unchanged",
    "7": "the_charter_names_the_keyed_shape",
}}

CHARTER = _REPO_ROOT / "cairn" / "devices" / "librarian" / "tools" / "trees" / "intention+why.json"
_RUN = uuid.uuid4().hex[:8]
_SCRATCH = contextlib.ExitStack()
_TABLES: dict[str, str] = {}
PROV = {"source": "testing: e62f40f35f59 proof"}

PASS = 0
FAIL = 0


def _trees():
    from cairn.devices.librarian.tools.trees import trees
    return trees


def _store():
    from cairn.devices.db_domain.tools.client import store
    return store


def _keyed() -> str:
    if "keyed" not in _TABLES:
        _TABLES["keyed"] = _SCRATCH.enter_context(_trees().scratch_leaf("keyedproof", keyed=True))
    return _TABLES["keyed"]


def _vectored() -> str:
    if "vectored" not in _TABLES:
        _TABLES["vectored"] = _SCRATCH.enter_context(_trees().scratch_leaf("vectoredproof"))
    return _TABLES["vectored"]


def _text(tag: str) -> str:
    return f"testing {_RUN}: {tag} — a stored answer found by its exact request"


def _node(nid: str) -> list[dict]:
    return _store().read(_trees().NODES_TABLE, where="node_id = %s", params=(nid,))


def _embeddings(nid: str) -> list[dict]:
    return _store().read(_trees().EMBEDDINGS_TABLE, where="node_id = %s", params=(nid,))


def _leaves(table: str, nid: str) -> list[dict]:
    return _store().read(table, where="node_id = %s", params=(nid,))


def _refused(exc_type, fn, *args, **kwargs) -> str:
    try:
        fn(*args, **kwargs)
    except exc_type as exc:
        return str(exc)
    raise AssertionError(f"{fn.__name__} was not refused with {exc_type.__name__}")


def a_keyed_deposit_lands_a_node_and_a_leaf_and_no_embedding():
    t = _trees()
    table = _keyed()
    r = t.deposit_keyed(_text("one"), f"key-one-{_RUN}", PROV, table=table, owner=t.OWNER,
                        meta={"verdict": "miss", "cost": 7})
    nid = r["node_id"]
    assert nid == t.node_id_for(_text("one")), r
    assert len(_node(nid)) == 1, _node(nid)
    assert _embeddings(nid) == [], _embeddings(nid)
    leaves = _leaves(table, nid)
    assert len(leaves) == 1, leaves
    assert leaves[0]["key"] == f"key-one-{_RUN}", leaves[0]
    assert leaves[0]["meta"] == {"verdict": "miss", "cost": 7}, leaves[0]
    assert "embedding_id" not in leaves[0], leaves[0]


def find_returns_the_nodes_under_a_key_newest_first():
    t = _trees()
    table = _keyed()
    key = f"key-two-{_RUN}"
    t.deposit_keyed(_text("two older"), key, PROV, table=table, owner=t.OWNER, meta={"n": 1})
    t.deposit_keyed(_text("two newer"), key, PROV, table=table, owner=t.OWNER, meta={"n": 2})
    found = t.find(key, table=table)
    assert [f["content"] for f in found] == [_text("two newer"), _text("two older")], found
    top = found[0]
    assert top["meta"] == {"n": 2}, top
    assert top["standing"] == "hypothesis", top
    assert top["provenance"]["source"] == PROV["source"], top
    assert t.find(f"no-such-key-{_RUN}", table=table) == []


def a_repeat_attests_and_a_second_key_adds_a_leaf():
    t = _trees()
    table = _keyed()
    content, key = _text("three"), f"key-three-{_RUN}"
    nid = t.deposit_keyed(content, key, PROV, table=table, owner=t.OWNER)["node_id"]
    again = t.deposit_keyed(content, key, PROV, table=table, owner=t.OWNER)
    assert again["duplicate"] is True, again
    assert len(_leaves(table, nid)) == 1, _leaves(table, nid)
    attests = (_node(nid)[0]["provenance"] or {}).get("attestations") or []
    assert len(attests) == 1, attests
    t.deposit_keyed(content, f"key-three-b-{_RUN}", PROV, table=table, owner=t.OWNER)
    assert sorted(l["key"] for l in _leaves(table, nid)) == sorted(
        [key, f"key-three-b-{_RUN}"]), _leaves(table, nid)
    assert len(_node(nid)) == 1


def each_shape_refuses_the_other():
    t = _trees()
    keyed, vectored = _keyed(), _vectored()
    t.deposit_keyed(_text("four seed"), f"key-four-{_RUN}", PROV, table=keyed, owner=t.OWNER)
    msg = _refused(t.WalkRefused, t.nearest, [1.0, 0.0], table=keyed)
    assert "keyed" in msg and keyed in msg, msg
    msg = _refused(t.WalkRefused, t.neighbors, t.node_id_for(_text("four seed")), table=keyed)
    assert "keyed" in msg and keyed in msg, msg
    stray = _text("four vectored into keyed")
    msg = _refused(t.DepositRefused, t.deposit, stray, [1.0, 0.0], PROV, table=keyed)
    assert "keyed" in msg, msg
    assert _node(t.node_id_for(stray)) == [], "a refused deposit landed a node"
    stray = _text("four keyed into vectored")
    msg = _refused(t.DepositRefused, t.deposit_keyed, stray, f"key-four-b-{_RUN}", PROV,
                   table=vectored, owner=t.OWNER)
    assert "vectored" in msg or "embedding" in msg, msg
    assert _node(t.node_id_for(stray)) == [], "a refused deposit_keyed landed a node"


def the_keyed_door_judges_as_deposit_does():
    t = _trees()
    table = _keyed()
    _refused(t.DepositRefused, t.deposit_keyed, "tiny", f"key-five-{_RUN}", PROV,
             table=table, owner=t.OWNER)
    content = _text("five no provenance")
    _refused(t.DepositRefused, t.deposit_keyed, content, f"key-five-{_RUN}", {},
             table=table, owner=t.OWNER)
    _refused(t.DepositRefused, t.deposit_keyed, content, "  ", PROV, table=table, owner=t.OWNER)
    assert _node(t.node_id_for(content)) == [], "a refused deposit_keyed landed a node"
    assert t.find(f"key-five-{_RUN}", table=table) == []


def a_vectored_deposit_and_walk_are_unchanged():
    t = _trees()
    table = _vectored()
    content = _text("six vectored")
    nid = t.deposit(content, [0.6, 0.8], PROV, table=table)["node_id"]
    assert len(_embeddings(nid)) == 1, _embeddings(nid)
    hits = t.nearest([0.6, 0.8], k=1, table=table)
    assert hits and hits[0]["node_id"] == nid, hits
    assert abs(hits[0]["similarity"] - 1.0) < 1e-9, hits


def the_charter_names_the_keyed_shape():
    what = json.loads(CHARTER.read_text())["what"]
    for word in ("deposit_keyed", "find", "keyed leaf"):
        assert word in what, f"the charter's what does not name {word!r}"


TEETH = [a_keyed_deposit_lands_a_node_and_a_leaf_and_no_embedding,
         find_returns_the_nodes_under_a_key_newest_first,
         a_repeat_attests_and_a_second_key_adds_a_leaf,
         each_shape_refuses_the_other,
         the_keyed_door_judges_as_deposit_does,
         a_vectored_deposit_and_walk_are_unchanged,
         the_charter_names_the_keyed_shape]


def _forget() -> None:
    for table in _TABLES.values():
        try:
            _trees().forget_leaf(table)
        except Exception as exc:  # noqa: BLE001 — loud, never hidden
            print(f"  cleanup: forget_leaf({table}) failed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    try:
        for fn in TEETH:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
                FAIL += 1
                print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
            else:
                PASS += 1
                print(f"  green {fn.__name__}")
    finally:
        _forget()
        _SCRATCH.close()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

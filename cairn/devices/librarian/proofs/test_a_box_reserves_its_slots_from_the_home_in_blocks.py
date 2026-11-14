"""Proof for ticket d32faaf16223 — a box that is not the home gets its row slots from the home
librarian in blocks, and its leaf tags from the home, over the librarian's ``reserve`` verb.

Outline 4.3.1.5.1.1: a row number is the same on every box, so only the home's librarian hands
one out. 4.3.1.5.1.6.9: slots are reserved in blocks, not per row, and reserved rows not yet
used sit VOID. T2 (06db586bedfd) left the trees tool taking an injected ``reserver``; this is
the librarian device's two halves of it (cairn/devices/librarian/home_reserver.py).

One tooth per numbered falsifier clause:

  1. the home's answer to a block ask is ``count`` distinct rows, each held NOTCACHED at the
     home, and the next block shares no row with it; a tag ask is answered from 0x0100 up, the
     same tag every time for one table;
  2. on a remote box, deposits through a BlockReserver ask the home once per block, land at rows
     of that block, and leave the block's unused rows VOID on the remote, while the home holds
     them NOTCACHED and its own next reserve hands out none of them;
  3. a deposit past the block asks for the next block, and no row is handed out twice;
  4. the answer refuses off the home, refuses an unknown kind or a bad count, and a home that
     answers no rows is refused by the reserver, with nothing landed;
  5. the librarian device declares the ``reserve`` verb, routes it to the answer, and its
     deposits pass the reserver: none on the home, a BlockReserver off it.

THE WORLD: two sets of ``store.scratch`` tables, one the home's and one the remote's, the trees
module's table names patched onto whichever box is answering. No live table is read or written.

    bin/cairn test cairn/devices/librarian/proofs/test_a_box_reserves_its_slots_from_the_home_in_blocks.py
"""
from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"d32faaf16223": {
    "1": "test_the_home_hands_out_a_block_and_a_tag",
    "2": "test_a_remote_deposit_lands_in_its_block_and_the_rest_sit_void",
    "3": "test_past_the_block_the_next_is_asked_and_no_row_repeats",
    "4": "test_a_bad_ask_is_refused_and_nothing_lands",
    "5": "test_the_device_declares_the_verb_and_passes_the_reserver",
}}

PROOF_TIMEOUT_S = 240

_PROV = {"source": "testing: proof d32faaf16223"}
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
def _patched(mod, **values):
    saved = {k: getattr(mod, k) for k in values}
    for k, v in values.items():
        setattr(mod, k, v)
    try:
        yield
    finally:
        for k, v in saved.items():
            setattr(mod, k, v)


def _t():
    from cairn.devices.librarian.tools.trees import trees
    return trees


def _hr():
    from cairn.devices.librarian import home_reserver
    return home_reserver


def _store():
    from cairn.devices.db_domain.tools.client import store
    return store


def _box(stack, tag: str) -> dict:
    t, store = _t(), _store()

    def s(prefix, cols):
        return stack.enter_context(store.scratch(t.OWNER, f"{tag}_{prefix}", cols))
    return {
        "NODES_TABLE": s("mem_nodes", t._NODE_COLUMNS),
        "LISTS_TABLE": s("mem_lists", t._LIST_COLUMNS),
        "LINKS_TABLE": s("mem_links", t._LINK_COLUMNS),
        "BLOBS_TABLE": s("mem_blobs", t._BLOB_COLUMNS),
        "TAGS_TABLE": s("mem_tags", t._TAG_COLUMNS),
        "EMBEDDINGS_TABLE": s("mem_emb", t._EMBEDDING_COLUMNS),
        "CONTENT_INDEX": s("mem_index", t._CONTENT_INDEX_COLUMNS),
    }


@contextlib.contextmanager
def _two_boxes():
    """The home's tables and the remote's. Yields (home, remote, as_home, as_remote): the last
    two are context managers that put the trees module on that box."""
    t = _t()
    with contextlib.ExitStack() as stack:
        home, remote = _box(stack, "home"), _box(stack, "far")

        @contextlib.contextmanager
        def on(names, host):
            with _patched(t, **names), _home(host):
                yield
        yield home, remote, (lambda: on(home, None)), (lambda: on(remote, "the-home-box"))


def _rows(table) -> dict:
    return {r["row"]: r for r in _store().read(table)}


def _home_ask(as_home, as_remote, log: list):
    """The bus ask, in-process: the remote's request is answered on the home's tables, then the
    trees module goes back to the remote."""
    def ask(body):
        log.append(dict(body))
        with as_home():
            reply = _hr().answer(body)
        return reply
    return ask


def test_the_home_hands_out_a_block_and_a_tag():
    t = _t()
    with _two_boxes() as (home, _remote, as_home, _as_remote), as_home():
        first = _hr().answer({"kind": "nodes", "count": 5})["rows"]
        assert len(first) == 5 and len(set(first)) == 5, first
        held = _rows(home["NODES_TABLE"])
        assert all(held[r]["state"] == t.NOTCACHED for r in first), \
            {r: held[r]["state"] for r in first}
        second = _hr().answer({"kind": "nodes", "count": 5})["rows"]
        assert not set(first) & set(second), (first, second)
        tag = _hr().answer({"kind": "tag", "table": "testing_d32f_leaf"})["tag"]
        assert tag >= t.LEAF_TAG_FLOOR, f"{tag:#x}"
        assert _hr().answer({"kind": "tag", "table": "testing_d32f_leaf"})["tag"] == tag
        other = _hr().answer({"kind": "tag", "table": "testing_d32f_other"})["tag"]
        assert other != tag and other >= t.LEAF_TAG_FLOOR, (tag, other)


def test_a_remote_deposit_lands_in_its_block_and_the_rest_sit_void():
    t = _t()
    with _two_boxes() as (home, remote, as_home, as_remote):
        log: list = []
        reserver = _hr().BlockReserver(_home_ask(as_home, as_remote, log), block=6)
        with as_remote(), t.scratch_leaf("testing_d32f_far") as leaf:
            got = [t.deposit(f"testing d32f: remote node {i}", _V, _PROV, table=leaf,
                             reserver=reserver)["node_id"] for i in range(3)]
            from cairn.tools.node_address import node_address as A
            rows = [A.row_of(n) for n in got]
            node_asks = [b for b in log if b.get("kind") == "nodes"]
            assert len(node_asks) == 1, log
            block = set(rows) | set(reserver.held("nodes"))
            assert len(block) == 6, (rows, reserver.held("nodes"))
            far = _rows(remote["NODES_TABLE"])
            assert all(far[r]["state"] == t.DATA for r in rows), {r: far[r]["state"] for r in rows}
            unused = reserver.held("nodes")
            assert unused and all(far[r]["state"] == t.VOID for r in unused), \
                {r: far[r]["state"] for r in unused}
            assert any(b.get("kind") == "tag" for b in log), f"the leaf's tag was not asked: {log}"
        with as_home():
            near = _rows(home["NODES_TABLE"])
            assert all(near[r]["state"] == t.NOTCACHED for r in block), \
                {r: near.get(r, {}).get("state") for r in block}
            own = t.reserve()
            assert own not in block, f"the home handed out {own}, a row of the remote's block"


def test_past_the_block_the_next_is_asked_and_no_row_repeats():
    t = _t()
    with _two_boxes() as (_home_names, _remote, as_home, as_remote):
        log: list = []
        reserver = _hr().BlockReserver(_home_ask(as_home, as_remote, log), block=2)
        with as_remote():
            handed = [t.reserve(reserver=reserver) for _ in range(5)]
        assert len(set(handed)) == 5, handed
        assert len([b for b in log if b.get("kind") == "nodes"]) == 3, log


def test_a_bad_ask_is_refused_and_nothing_lands():
    t, hr = _t(), _hr()
    with _two_boxes() as (home, remote, as_home, as_remote):
        with as_remote():
            for body in ({"kind": "nodes", "count": 3}, {"kind": "tag", "table": "x"}):
                try:
                    hr.answer(body)
                except t.ReserveRefused as e:
                    assert "the-home-box" in str(e), str(e)
                else:
                    raise AssertionError(f"a remote box answered {body}")
        with as_home():
            for body in ({"kind": "rows", "count": 3}, {"kind": "nodes", "count": 0},
                         {"kind": "nodes", "count": "9"}, {"kind": "tag"}):
                try:
                    hr.answer(body)
                except (t.ReserveRefused, hr.ReserveAnswerRefused):
                    pass
                else:
                    raise AssertionError(f"the home answered {body}")
            assert not _rows(home["NODES_TABLE"]), "a refused ask landed a home row"
        empty = hr.BlockReserver(lambda body: {"kind": body["kind"], "rows": []}, block=4)
        with as_remote():
            try:
                t.reserve(reserver=empty)
            except t.ReserveRefused as e:
                assert "no nodes rows" in str(e), str(e)
            else:
                raise AssertionError("a reserver with an empty home answer handed out a row")
            assert not _rows(remote["NODES_TABLE"]), "an empty answer landed a remote row"


def test_the_device_declares_the_verb_and_passes_the_reserver():
    from cairn.devices.librarian.device import LibrarianDevice
    t, hr = _t(), _hr()
    with _two_boxes() as (_h, _r, as_home, as_remote):
        dev = LibrarianDevice()
        verbs = dev.declared_verbs()
        assert "reserve" in verbs, sorted(verbs)
        with as_home():
            reply = verbs["reserve"]({"body": {"kind": "nodes", "count": 2}})
            assert len(reply["rows"]) == 2, reply
            assert dev.reserver() is None, "the home's deposits must reserve for themselves"
        far = LibrarianDevice()
        with as_remote():
            assert isinstance(far.reserver(), hr.BlockReserver), far.reserver()
            seen = []
            far._reserver = hr.BlockReserver(_home_ask(as_home, as_remote, seen), block=3)
            with t.scratch_leaf("testing_d32f_dev") as leaf:
                far.deposit("testing d32f: a device deposit off the home", _V, _PROV, table=leaf)
            assert any(b.get("kind") == "nodes" for b in seen), \
                f"the device's deposit did not ask the home: {seen}"


TEETH = [test_the_home_hands_out_a_block_and_a_tag,
         test_a_remote_deposit_lands_in_its_block_and_the_rest_sit_void,
         test_past_the_block_the_next_is_asked_and_no_row_repeats,
         test_a_bad_ask_is_refused_and_nothing_lands,
         test_the_device_declares_the_verb_and_passes_the_reserver]


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

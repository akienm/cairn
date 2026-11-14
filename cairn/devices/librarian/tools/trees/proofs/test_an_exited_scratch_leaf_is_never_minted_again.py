"""Proof for ticket 1a3a55a314eb — a deposit into a scratch leaf whose run has exited is refused,
never re-minted as a standing table.

Measured 2026-11-14: six testing_e8fe leaf tables (chart_ and codemother_) stood live with no
cairn_scratch row. D0 reproduced the write that makes one: a scratch nexus held under owner
`chart` (chart_testing_<pid>_<stamp>_nodes) while the orient deposit writes as owner `codemother`,
so trees.deposit -> ensure_trees minted codemother_testing_<pid>_<stamp>_nodes — a second owner's
derived name, scratch-shaped, unregistered, and left standing when the scratch dropped. ensure_trees
minted any name it was given; it now refuses a scratch-shaped name the registry does not hold.

One tooth per numbered falsifier clause:

  1. a deposit into a scratch leaf's name after its with-block has exited raises TreeRefused
     naming the table and "its scratch is gone", and no table of that name exists afterwards.
  2. a deposit inside the held scratch leaf lands as before.
  3. a standing name (no pid-stamp shape) is minted by ensure_trees as before; store.scratch_name's
     own output has the shape the refusal reads.
  4. the D0 write — the second owner's derived name beside a held scratch — ends in that refusal,
     and the run leaves no unregistered scratch-shaped table behind.

Requires the db_domain provisioning; every leaf but clause 3's standing one is scratch, and that
one is dropped before the run ends.

    bin/cairn test cairn/devices/librarian/tools/trees/proofs/test_an_exited_scratch_leaf_is_never_minted_again.py
"""
from __future__ import annotations

import hashlib
import re
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"1a3a55a314eb": {
    "1": "test_a_deposit_after_the_scratch_exits_is_refused",
    "2": "test_a_deposit_inside_the_held_scratch_lands",
    "3": "test_a_standing_name_is_minted_as_before",
    "4": "test_the_second_owners_name_is_refused_and_nothing_leaks",
}}

_RUN = uuid.uuid4().hex[:8]
PROV = {"source": "testing: 1a3a55a314eb proof"}
PASS = 0
FAIL = 0


def _trees():
    from cairn.devices.librarian.tools.trees import trees
    return trees


def _store():
    from cairn.devices.db_domain.tools.client import store
    return store


def _vec(text: str) -> list[float]:
    h = hashlib.sha256(text.encode()).digest()
    return [((b % 17) + 1) / 17.0 for b in h] * 24


def _deposit(t, table: str, owner: str, what: str) -> dict:
    content = f"testing {_RUN}: {what}"
    return t.deposit(content, _vec(content), PROV, tree=f"testing_1a3a_{_RUN}",
                     table=table, owner=owner)


def _exists(table: str) -> bool:
    return _store().owner_of(table) is not None


def test_a_deposit_after_the_scratch_exits_is_refused():
    t = _trees()
    with t.scratch_leaf(f"testing_1a3a_{_RUN}", suffix="nodes") as table:
        pass
    assert not _exists(table), f"{table} still stands after its scratch exited"
    try:
        _deposit(t, table, t.OWNER, "a late write after the scratch dropped")
    except t.TreeRefused as exc:
        assert table in str(exc) and "its scratch is gone" in str(exc), str(exc)
    else:
        raise AssertionError(f"a deposit into the exited scratch {table} was not refused")
    assert not _exists(table), f"the late write re-minted {table}"


def test_a_deposit_inside_the_held_scratch_lands():
    t = _trees()
    with t.scratch_leaf(f"testing_1a3a_{_RUN}", suffix="nodes") as table:
        got = _deposit(t, table, t.OWNER, "a write inside the held scratch")
        assert got.get("node_id") is not None, got
        rows = _store().read(table)
        assert [str(r["node_id"]) for r in rows] == [str(got["node_id"])], rows
        t.forget_leaf(table)


def test_a_standing_name_is_minted_as_before():
    t, store = _trees(), _store()
    shape = getattr(t, "_SCRATCH_SHAPE", None) or re.compile(r"_[0-9]+_[0-9]{10}(?:_\w+)?$")
    assert shape.search(store.scratch_name("testing_1a3a", "nodes")), \
        "store.scratch_name's output no longer has the shape ensure_trees reads"
    table = f"testing_1a3a_standing_{_RUN}_nodes"
    assert not shape.search(table), f"{table} reads as scratch-shaped"
    try:
        t.ensure_trees(table=table, owner=t.OWNER)
        assert store.owner_of(table) == t.OWNER, f"{table} was not minted under {t.OWNER}"
    finally:
        if _exists(table):
            store.drop_table(table, store.owner_of(table))
    assert not _exists(table), f"cleanup left {table} standing"


def _unregistered_of_this_run(store) -> list[str]:
    reg = {r["table_name"] for r in store.scratch_rows()}
    rows = store.query("SELECT tablename FROM pg_tables WHERE tablename LIKE %s",
                       tables={}, params=(f"%testing_1a3a_{_RUN}%",))
    return sorted(r["tablename"] for r in rows if r["tablename"] not in reg)


def test_the_second_owners_name_is_refused_and_nothing_leaks():
    t, store = _trees(), _store()
    with t.scratch_leaf(f"chart_testing_1a3a_{_RUN}", owner="chart", suffix="nodes") as held:
        other = "codemother_" + held[len("chart_"):]
        try:
            _deposit(t, other, "codemother", "the orient deposit under the other owner")
        except t.TreeRefused as exc:
            assert other in str(exc) and "its scratch is gone" in str(exc), str(exc)
        else:
            raise AssertionError(f"the second owner's name {other} was minted beside {held}")
        assert not _exists(other), f"{other} stands beside the held {held}"
    leaked = _unregistered_of_this_run(store)
    assert not leaked, f"the run left unregistered scratch-shaped tables: {leaked}"


TEETH = [test_a_deposit_after_the_scratch_exits_is_refused,
         test_a_deposit_inside_the_held_scratch_lands,
         test_a_standing_name_is_minted_as_before,
         test_the_second_owners_name_is_refused_and_nothing_leaks]


def _sweep_this_run() -> None:
    """A red build may have minted the names the teeth refuse; drop them so a red run leaks
    nothing either (each is this run's own, named by _RUN)."""
    store = _store()
    for table in _unregistered_of_this_run(store):
        try:
            _trees().forget_leaf(table)
            store.drop_table(table, store.owner_of(table))
            print(f"  cleanup: dropped {table}")
        except Exception as exc:  # noqa: BLE001 — loud, never hidden
            print(f"  cleanup: {table} failed: {type(exc).__name__}: {exc}")


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
        _sweep_this_run()
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

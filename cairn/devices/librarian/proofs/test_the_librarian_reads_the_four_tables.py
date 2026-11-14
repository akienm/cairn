"""Proof for ticket d32faaf16223, clauses 6-8: the librarian device reads and writes memory through
T2's four Q#108 tables (06db586bedfd), and the hash-keyed helpers are gone from all of it.

One tooth per numbered falsifier clause:

  6. librarian device code reads the four tables: ingest's carried calls come from
     meta.provenance of DATA nodes (an ingested call is not deposited twice), summarize's region
     id is computed over node addresses, and the standing_moves_under_live_use probe reads a
     leaf's node through trees.read_node;
  7. every proof under cairn/devices/librarian/proofs is green on the T2 schema, and none of
     them, and no librarian device module, names node_id_for, link_id_for, or a 'node_id = '
     read of the nodes table;
  8. migrate_to_three_tables.py is gone.

THE WORLD for clause 6: ``store.scratch`` tables for the seven Q#108 tables, the trees module's
(and the two readers') table names patched onto them. No live table is read or written.
Clause 7 runs each sibling proof as its own process (they hold the live tables' scratch leaves
themselves) and reads the device's source.

    bin/cairn test cairn/devices/librarian/proofs/test_the_librarian_reads_the_four_tables.py
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"d32faaf16223": {
    "6": "test_the_device_code_reads_the_four_tables",
    "7": "test_every_librarian_proof_is_green_and_names_no_hash_helper",
    "8": "test_the_three_table_migration_is_gone",
}}

PROOF_TIMEOUT_S = 3000

_DEVICE = _REPO_ROOT / "cairn" / "devices" / "librarian"
_PROOFS = _DEVICE / "proofs"
_SELF = Path(__file__).resolve()
_V = [1.0, 0.0, 0.0]


def _t():
    from cairn.devices.librarian.tools.trees import trees
    return trees


def _store():
    from cairn.devices.db_domain.tools.client import store
    return store


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
def _scratch_world():
    """The seven tables as scratch, the trees module on them, CAIRN_HOME_HOST unset (the home)."""
    t, store = _t(), _store()
    saved_home = os.environ.pop("CAIRN_HOME_HOST", None)
    with contextlib.ExitStack() as stack:
        def s(prefix, cols):
            return stack.enter_context(store.scratch(t.OWNER, f"d32f4_{prefix}", cols))
        names = {
            "NODES_TABLE": s("mem_nodes", t._NODE_COLUMNS),
            "LISTS_TABLE": s("mem_lists", t._LIST_COLUMNS),
            "LINKS_TABLE": s("mem_links", t._LINK_COLUMNS),
            "BLOBS_TABLE": s("mem_blobs", t._BLOB_COLUMNS),
            "TAGS_TABLE": s("mem_tags", t._TAG_COLUMNS),
            "EMBEDDINGS_TABLE": s("mem_emb", t._EMBEDDING_COLUMNS),
            "CONTENT_INDEX": s("mem_index", t._CONTENT_INDEX_COLUMNS),
        }
        try:
            with _patched(t, **names):
                yield names
        finally:
            if saved_home is not None:
                os.environ["CAIRN_HOME_HOST"] = saved_home


_CALLS = [
    {"canonical": json.dumps({"kind": "generate", "prompt": "d32f ingest tooth, resolved"}),
     "verdict": "miss", "created": "2026-11-14T08:00:00-07:00",
     "answer": {"body": {"response": "testing d32f: an answer the host gave, worth keeping"}}},
    {"canonical": json.dumps({"kind": "generate", "prompt": "d32f ingest tooth, refused"}),
     "verdict": "refused", "created": "2026-11-14T08:00:01-07:00", "answer": None},
]


def test_the_device_code_reads_the_four_tables():
    t = _t()
    from cairn.devices.librarian import ingest as ing
    from cairn.devices.librarian import summarize as summ
    from cairn.devices.librarian.probes import standing_moves_under_live_use as probe
    with _scratch_world() as names, _patched(ing, NODES_TABLE=names["NODES_TABLE"]), \
            t.scratch_leaf("testing_d32f_ingest") as leaf:
        ask = lambda body: {"calls": [dict(r) for r in _CALLS]}   # noqa: E731
        embed = lambda text: list(_V)                               # noqa: E731
        first = ing.ingest(ask, embed, table=leaf)
        assert first["deposited"] == 1, first
        cid = ing.call_id(_CALLS[0])
        assert cid in ing._carried(None), "ingest's carried calls do not see meta.provenance"
        again = ing.ingest(ask, embed, table=leaf)
        assert again["deposited"] == 0 and again["skipped"]["already"] == 1, again
        nodes = _store().read(names["NODES_TABLE"], where="state = %s", params=(t.DATA,))
        assert len(nodes) == 1, f"{len(nodes)} DATA nodes after two ingests"

        addrs = [t._addr("nodes", r["row"]) for r in nodes] + [t._addr("nodes", 999)]
        region = [{"node_id": a} for a in addrs]
        digest = summ.region_digest(region)
        assert digest == summ.region_digest(list(reversed(region))), "the region id is not set-stable"
        assert digest != summ.region_digest(region[:1]), "the region id ignores a member"

        with _patched(probe, NODES=leaf):
            seen = probe.survey_the_tree()
        assert "unreadable" not in seen, seen
        assert seen["standing_distribution"] == {"hypothesis": 1}, seen


_DEAD = re.compile(r"\bnode_id_for\b|\blink_id_for\b")
# a by-node_id read of the NODES table: the old hash-keyed key. The leaf and embedding tables
# still carry a node_id column (an address), so only a NODES_TABLE read is the dead one.
_DEAD_READ = re.compile(r"NODES_TABLE[^)\n]*where\s*=\s*[\"']node_id\s*=")


def _sources() -> list[Path]:
    return [p for p in sorted(_DEVICE.rglob("*.py"))
            if "/tools/" not in p.as_posix() and p.resolve() != _SELF]


def test_every_librarian_proof_is_green_and_names_no_hash_helper():
    named = [f"{p.relative_to(_REPO_ROOT)}: {m.group(0)}" for p in _sources()
             for m in [*_DEAD.finditer(p.read_text()), *_DEAD_READ.finditer(p.read_text())]]
    assert not named, f"the hash-keyed helpers still stand: {named}"
    red = []
    for proof in sorted(_PROOFS.glob("test_*.py")):
        if proof.resolve() == _SELF:
            continue
        got = subprocess.run([sys.executable, str(proof)], cwd=_REPO_ROOT, capture_output=True,
                             text=True, timeout=900)
        if got.returncode != 0:
            red.append(f"{proof.name} rc={got.returncode}: "
                       f"{(got.stdout + got.stderr).strip().splitlines()[-3:]}")
    assert not red, "librarian proofs red on the T2 schema:\n" + "\n".join(red)


def test_the_three_table_migration_is_gone():
    gone = _DEVICE / "migrate_to_three_tables.py"
    assert not gone.exists(), f"{gone.relative_to(_REPO_ROOT)} still stands"
    citing = [str(p.relative_to(_REPO_ROOT)) for p in _sources()
              if "migrate_to_three_tables" in p.read_text()]
    assert not citing, f"still cited by: {citing}"


TEETH = [test_the_device_code_reads_the_four_tables,
         test_every_librarian_proof_is_green_and_names_no_hash_helper,
         test_the_three_table_migration_is_gone]


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

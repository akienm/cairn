"""Proof for ticket 784eb1e92866 — test_librarian_trees writes only run-marked rows and removes them.

Measured 2026-11-19 on akiendell: the librarian proof alone is green (10 of 10), but two copies at
once were red in 6 of 6 copies (UniqueViolation on cairn_nodes_pkey / cairn_embeddings_pkey, and the
links/provenance teeth), because node ids are sha256(content) and both runs landed the same fixture
content in the shared live tables. These teeth run the librarian proof the way the collision was
found: as subprocesses, two at once, and count what each leaves in the three shared tables.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 900   # two concurrent copies (~100 s each alone, measured) plus a lone run, plus margin

PROVES = {"784eb1e92866": {
    "1": "test_two_concurrent_copies_both_stay_green",
    "2": "test_a_run_leaves_no_row_of_its_id_and_the_tables_unchanged",
    "3": "test_a_lone_copy_stays_green",
}}

_LIBRARIAN = _REPO_ROOT / "cairn" / "devices" / "librarian" / "proofs" / "test_librarian_trees.py"
_CONCURRENT: dict = {}


def _counts() -> dict:
    from cairn.devices.db_domain.tools.client import store
    from cairn.devices.librarian.tools.trees import trees
    return {t: len(store.read(t)) for t in (trees.NODES_TABLE, trees.EMBEDDINGS_TABLE, trees.LINKS_TABLE)}


def _marked_nodes(run_id: str) -> int:
    from cairn.devices.db_domain.tools.client import store
    from cairn.devices.librarian.tools.trees import trees
    return len(store.read(trees.NODES_TABLE, where="content LIKE %s", params=(f"%[{run_id}]%",)))


def _launch(run_id: str) -> subprocess.Popen:
    env = dict(os.environ, PYTHONPATH=str(_REPO_ROOT), CAIRN_LIBRARIAN_TRIALS_RUN_ID=run_id)
    return subprocess.Popen([sys.executable, str(_LIBRARIAN)], cwd=str(_REPO_ROOT), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")


def _two_at_once() -> dict:
    if not _CONCURRENT:
        before = _counts()
        procs = [_launch("c1" + "a" * 6), _launch("c2" + "b" * 6)]
        outs = [p.communicate(timeout=700)[0] for p in procs]
        _CONCURRENT.update(before=before, after=_counts(), rcs=[p.returncode for p in procs], outs=outs)
    return _CONCURRENT


def test_two_concurrent_copies_both_stay_green():
    r = _two_at_once()
    bad = [line.strip() for o in r["outs"] for line in o.splitlines() if "FAIL" in line]
    assert r["rcs"] == [0, 0] and not bad, f"rcs={r['rcs']} teeth={bad[:4]}"


def test_a_run_leaves_no_row_of_its_id_and_the_tables_unchanged():
    r = _two_at_once()
    left = {rid: _marked_nodes(rid) for rid in ("c1" + "a" * 6, "c2" + "b" * 6)}
    assert not any(left.values()), f"rows carrying a run id remain in the nodes table: {left}"
    assert r["after"] == r["before"], f"table counts moved: before={r['before']} after={r['after']}"


def test_a_lone_copy_stays_green():
    p = _launch("d3" + "c" * 6)
    out = p.communicate(timeout=300)[0]
    assert p.returncode == 0 and "FAIL" not in out, out[-600:]


def main() -> int:
    fails = 0
    for name in PROVES["784eb1e92866"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

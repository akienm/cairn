"""Proof for tickets 784eb1e92866 and a80d9ff575da: two copies of test_librarian_trees run at once stay
green, and leave unchanged the live rows they could have written.

Measured 2026-11-19 on akiendell (784eb): the librarian proof alone is green, but two copies at once
were red in 6 of 6 (UniqueViolation on cairn_nodes_pkey / cairn_embeddings_pkey), because node ids are
sha256(content) and both runs landed the same fixture content in one shared table. Measured 2026-11-20 on
akiendelllinux (a80d): that is still true inside cairn_testing, which is one shared schema; with one
token forced on both copies, copy 1 bit 6 teeth and copy 2 bit 8. So each copy gets its own token
(CAIRN_LIBRARIAN_TRIALS_RUN_ID), which rides in every node's content.

The rows a copy could have written in live are the cairn_nodes whose content carries its token, and the
cairn_embeddings and cairn_links joined to them by id. Only those are asserted. The live totals are
reported and never asserted: another live writer moves them (31ba1dd472d6's shape, 692bf2ab6).

    bin/cairn test cairn/devices/librarian/proofs/test_librarian_trees_runs_alongside_itself.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 900   # two concurrent copies (~100 s each alone, measured) plus a lone run, plus margin

PROVES = {
    "784eb1e92866": {
        "1": "test_two_concurrent_copies_both_stay_green",
        "2": "test_a_run_leaves_the_live_rows_it_could_write_unchanged",
        "3": "test_a_lone_copy_stays_green",
    },
    "a80d9ff575da": {
        "1": "test_two_concurrent_copies_both_stay_green",
    },
}

_LIBRARIAN = _REPO_ROOT / "cairn" / "devices" / "librarian" / "proofs" / "test_librarian_trees.py"
_TABLES = ("cairn_nodes", "cairn_embeddings", "cairn_links")
_TOKENS = ("c1" + "a" * 6, "c2" + "b" * 6)
_CONCURRENT: dict = {}

# Read in a child with the tester's test id removed, so the store dials LIVE (read-only use).
_LIVE_COUNT = r'''
import json, sys
from cairn.devices.db_domain.tools.client import store
names = {"n": "cairn_nodes", "e": "cairn_embeddings", "l": "cairn_links"}
out = {}
for t, k in (("cairn_nodes", "n"), ("cairn_embeddings", "e"), ("cairn_links", "l")):
    out[t] = store.query("SELECT count(*) AS n FROM {" + k + "}", tables=names)[0]["n"]
for tok in sys.argv[1:]:
    like = ("%[" + tok + "]%",)
    mine = "SELECT node_id FROM {n} WHERE content LIKE %s"
    out["cairn_nodes:" + tok] = store.query("SELECT count(*) AS n FROM {n} WHERE content LIKE %s",
                                            tables=names, params=like)[0]["n"]
    out["cairn_embeddings:" + tok] = store.query(
        "SELECT count(*) AS n FROM {e} WHERE node_id IN (" + mine + ")", tables=names, params=like)[0]["n"]
    out["cairn_links:" + tok] = store.query(
        "SELECT count(*) AS n FROM {l} WHERE source_id IN (" + mine + ") OR target_id IN (" + mine + ")",
        tables=names, params=like * 2)[0]["n"]
print(json.dumps(out))
'''


def _live_counts(tokens) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "CAIRN_TESTER_TEST_ID"}
    env["PYTHONPATH"] = str(_REPO_ROOT)
    r = subprocess.run([sys.executable, "-c", _LIVE_COUNT, *tokens], cwd=str(_REPO_ROOT), env=env,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"the live count failed: {r.stderr[-800:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def _launch(token: str) -> subprocess.Popen:
    env = dict(os.environ, PYTHONPATH=str(_REPO_ROOT), CAIRN_LIBRARIAN_TRIALS_RUN_ID=token)
    return subprocess.Popen([sys.executable, str(_LIBRARIAN)], cwd=str(_REPO_ROOT), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")


def _two_at_once() -> dict:
    if not _CONCURRENT:
        before = _live_counts(_TOKENS)
        procs = [_launch(t) for t in _TOKENS]
        outs = [p.communicate(timeout=700)[0] for p in procs]
        _CONCURRENT.update(before=before, after=_live_counts(_TOKENS),
                           rcs=[p.returncode for p in procs], outs=outs)
    return _CONCURRENT


def test_two_concurrent_copies_both_stay_green():
    r = _two_at_once()
    bad = [line.strip() for o in r["outs"] for line in o.splitlines() if "FAIL" in line]
    died = {i: o[-1500:] for i, (rc, o) in enumerate(zip(r["rcs"], r["outs"])) if rc != 0}
    assert r["rcs"] == [0, 0] and not bad, f"rcs={r['rcs']} teeth={bad[:4]} tails={died}"


def test_a_run_leaves_the_live_rows_it_could_write_unchanged():
    r = _two_at_once()
    mine = [k for k in r["before"] if ":" in k]
    moved = {k: (r["before"][k], r["after"][k]) for k in mine if r["before"][k] != r["after"][k]}
    totals = {k: (r["before"][k], r["after"][k]) for k in r["before"] if k not in mine}
    assert len(mine) == len(_TABLES) * len(_TOKENS), f"the live count read {sorted(r['before'])}"
    assert not moved, (f"live rows carrying a run token moved across two runs (before, after): {moved}; "
                       f"totals, not asserted: {totals}")


def test_a_lone_copy_stays_green():
    p = _launch("d3" + "c" * 6)
    out = p.communicate(timeout=300)[0]
    assert p.returncode == 0 and "FAIL" not in out, out[-1500:]


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

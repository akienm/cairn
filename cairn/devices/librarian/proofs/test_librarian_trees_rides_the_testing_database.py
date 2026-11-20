"""Proof for ticket a80d9ff575da: test_librarian_trees rides the testing database. It marks nothing as
testing and deletes nothing by hand, and a run leaves the live rows it could have written unchanged.

Measured 2026-11-20 on akiendelllinux: test_librarian_trees carried 784eb1e92866's mark-and-clean code
(a "testing"/"run" provenance pair on every fixture row, and store.delete of its nodes, embeddings and
links in its finally block), which contradicts outline 4.3.1.5.1.5.2: under the tester, isolation comes
from the store, which dials cairn_testing for every write (e4fd7f28faaf). The per-run token stays in the
content, because cairn_testing is one shared schema and a node id is sha256(content) (measured the same
day: with one token shared, two concurrent copies bit 6 and 8 teeth on cairn_embeddings_pkey).

  2. across one run (under this run's tester test id), the live cairn_nodes whose content carries the
     run's token, and the cairn_embeddings and cairn_links joined to them, are unchanged; the live
     totals are reported and never asserted;
  3. that copy, run alone, exits 0 and passes every tooth name it passed at 7ade65adb;
  4. test_librarian_trees.py carries no testing or run provenance key and no hand cleanup (no
     store.delete, no raw SQL DELETE or TRUNCATE), except one: the cairn_threads rows this run minted,
     removed by thread_id.

    bin/cairn test cairn/devices/librarian/proofs/test_librarian_trees_rides_the_testing_database.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 600   # one copy (~100 s alone, measured) plus two live counts, plus margin

PROVES = {"a80d9ff575da": {
    "2": "test_a_run_leaves_the_live_rows_it_could_write_unchanged",
    "3": "test_a_lone_copy_passes_every_tooth_it_passed_at_7ade65adb",
    "4": "test_the_source_marks_nothing_as_testing_and_deletes_nothing",
}}

_REL = "cairn/devices/librarian/proofs/test_librarian_trees.py"
_SUBJECT = _REPO_ROOT / _REL
_BASELINE = "7ade65adb"
_TOKEN = "r1" + "e" * 6
_RUN: dict = {}

_LIVE_COUNT = r'''
import json, sys
from cairn.devices.db_domain.tools.client import store
names = {"n": "cairn_nodes", "e": "cairn_embeddings", "l": "cairn_links"}
out = {}
for t, k in (("cairn_nodes", "n"), ("cairn_embeddings", "e"), ("cairn_links", "l")):
    out[t] = store.query("SELECT count(*) AS n FROM {" + k + "}", tables=names)[0]["n"]
like = ("%[" + sys.argv[1] + "]%",)
mine = "SELECT node_id FROM {n} WHERE content LIKE %s"
out["cairn_nodes:mine"] = store.query("SELECT count(*) AS n FROM {n} WHERE content LIKE %s",
                                      tables=names, params=like)[0]["n"]
out["cairn_embeddings:mine"] = store.query(
    "SELECT count(*) AS n FROM {e} WHERE node_id IN (" + mine + ")", tables=names, params=like)[0]["n"]
out["cairn_links:mine"] = store.query(
    "SELECT count(*) AS n FROM {l} WHERE source_id IN (" + mine + ") OR target_id IN (" + mine + ")",
    tables=names, params=like * 2)[0]["n"]
print(json.dumps(out))
'''


def _live_counts() -> dict:
    """Read in a child with the tester's test id removed, so the store dials live."""
    env = {k: v for k, v in os.environ.items() if k != "CAIRN_TESTER_TEST_ID"}
    env["PYTHONPATH"] = str(_REPO_ROOT)
    r = subprocess.run([sys.executable, "-c", _LIVE_COUNT, _TOKEN], cwd=str(_REPO_ROOT), env=env,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"the live count failed: {r.stderr[-800:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def _once() -> dict:
    """One copy of the subject, inheriting this run's environment (the tester's test id included)."""
    if not _RUN:
        before = _live_counts()
        env = dict(os.environ, PYTHONPATH=str(_REPO_ROOT), CAIRN_LIBRARIAN_TRIALS_RUN_ID=_TOKEN)
        p = subprocess.run([sys.executable, str(_SUBJECT)], cwd=str(_REPO_ROOT), env=env,
                           capture_output=True, text=True, encoding="utf-8", timeout=400)
        _RUN.update(before=before, after=_live_counts(), rc=p.returncode, out=p.stdout + p.stderr)
    return _RUN


def _passed(out: str) -> set[str]:
    return set(re.findall(r"(?m)^\s+PASS\s+(test_\w+)", out))


def _baseline_names() -> set[str]:
    src = subprocess.run(["git", "-C", str(_REPO_ROOT), "show", f"{_BASELINE}:{_REL}"],
                         capture_output=True, text=True)
    assert src.returncode == 0, src.stderr
    block = re.search(r"checks = \[(.*?)\]", src.stdout, re.S)
    assert block, f"no checks list in {_REL} at {_BASELINE}"
    return set(re.findall(r"\btest_\w+", block.group(1)))


def test_a_run_leaves_the_live_rows_it_could_write_unchanged():
    r = _once()
    mine = [k for k in r["before"] if k.endswith(":mine")]
    moved = {k: (r["before"][k], r["after"][k]) for k in mine if r["before"][k] != r["after"][k]}
    totals = {k: (r["before"][k], r["after"][k]) for k in r["before"] if k not in mine}
    assert len(mine) == 3, f"the live count read {sorted(r['before'])}"
    assert not moved, (f"live rows carrying the token {_TOKEN} moved across one run (before, after): "
                       f"{moved}; totals, not asserted: {totals}")


def test_a_lone_copy_passes_every_tooth_it_passed_at_7ade65adb():
    r = _once()
    want = _baseline_names()
    missing = sorted(want - _passed(r["out"]))
    assert len(want) >= 30, f"the baseline names only {len(want)} teeth"
    assert r["rc"] == 0 and not missing, f"rc={r['rc']} not passed: {missing} tail={r['out'][-1200:]}"


# The one hand removal clause 4 names: the cairn_threads rows this run minted, by thread_id. The warm teeth
# need it (MAX_THREADS = 7 caps the table), and a thread id is minted per call (trees._thread_id), so it
# can never name a concurrent copy's thread.
_THREAD_CLEANUP = '''            for tid in _WARM_CREATED_THREADS:
                cur.execute(f'DELETE FROM "{THREADS_TABLE}" WHERE thread_id = %s', (tid,))'''


def test_the_source_marks_nothing_as_testing_and_deletes_nothing():
    src = _SUBJECT.read_text(encoding="utf-8")
    assert src.count(_THREAD_CLEANUP) <= 1, "the named thread cleanup appears more than once"
    rest = src.replace(_THREAD_CLEANUP, "")
    found = {name: re.findall(pat, rest) for name, pat in (
        ("a testing provenance key", r"[\"']testing[\"']\s*:"),
        ("a run provenance key", r"[\"']run[\"']\s*:"),
        ("a store.delete", r"\bstore\.delete\("),
        ("a raw SQL DELETE", r"(?i)\bDELETE\s+FROM\b"),
        ("a raw SQL TRUNCATE", r"(?i)\bTRUNCATE\b"))}
    hits = {k: len(v) for k, v in found.items() if v}
    assert not hits, f"{_REL} still carries hand cleanup beyond the named thread cleanup: {hits}"


def main() -> int:
    fails = 0
    for name in PROVES["a80d9ff575da"].values():
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

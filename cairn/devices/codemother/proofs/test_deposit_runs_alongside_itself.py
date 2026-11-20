"""Proof for ticket 42b9ca9594e8: test_deposit rides the testing database, leaving live counts unchanged.

MEASURED 2026-11-20 on akiendelllinux, read-only and with nothing run against live (the
ticket's `measured`): rows from this proof's runs stand in the live cairn_nodes and
cairn_embeddings with provenance under a chart_verdict_proof_ scratch dir, none marked as testing. Its
scratch nexus drops only the leaf table, and trees.deposit writes the node and the embedding to
the shared live tables. The isolation is e4fd7f28faaf's, by construction (outline
4.3.1.5.1.5.2): the runner sets the test id, and under it every writing connection dials
cairn_testing. test_deposit itself is not changed.

These teeth run test_deposit as the collision and the leak were found, as subprocesses
inheriting this run's environment (CAIRN_TESTER_TEST_ID included, which the tester sets). The
live counts are read in a child process with CAIRN_TESTER_TEST_ID removed, so the count is
the live database's whether or not e4fd has landed. It is a SELECT count(*) and writes
nothing.

  1. two copies of test_deposit run at the same time, both exit 0 with no FAIL tooth;
  2. across a run of test_deposit, the live cairn_nodes, cairn_embeddings and cairn_links counts
     are unchanged: zero rows left in live;
  3. one copy of test_deposit run alone still exits 0.

RED ON MAIN until e4fd7f28faaf lands. That red is measured by the ticket's read-only count,
not by running this proof against live, because a run on main leaves its rows there.

    bin/cairn test cairn/devices/codemother/proofs/test_deposit_runs_alongside_itself.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 1800   # two concurrent copies plus a lone run, plus margin

PROVES = {"42b9ca9594e8": {
    "1": "test_two_concurrent_copies_both_stay_green",
    "2": "test_a_run_leaves_the_live_counts_unchanged",
    "3": "test_a_lone_copy_stays_green",
}}

_SUBJECT = Path(__file__).resolve().parent / "test_deposit.py"
_TABLES = ("cairn_nodes", "cairn_embeddings", "cairn_links")
_PREFIX = "chart_verdict_proof_"
_CONCURRENT: dict = {}

# Run in a child with the test id removed: the store dials the live database, and reads only.
_LIVE_COUNT = r"""
import json, sys
from cairn.devices.db_domain.tools.client import store
tables, prefix = json.loads(sys.argv[1]), sys.argv[2]
out = {}
for t in tables:
    out[t] = store.query("SELECT count(*) AS n FROM {t}", tables={"t": t})[0]["n"]
for t in ("cairn_nodes", "cairn_embeddings"):
    out[t + ":" + prefix] = store.query("SELECT count(*) AS n FROM {t} WHERE provenance::text LIKE %s",
                                        tables={"t": t}, params=("%" + prefix + "%",))[0]["n"]
print(json.dumps(out))
"""


def _live_counts() -> dict:
    env = {k: v for k, v in os.environ.items() if k != "CAIRN_TESTER_TEST_ID"}
    env["PYTHONPATH"] = str(_REPO_ROOT)
    p = subprocess.run([sys.executable, "-c", _LIVE_COUNT, json.dumps(list(_TABLES)), _PREFIX],
                       cwd=str(_REPO_ROOT), env=env, capture_output=True, text=True, timeout=300)
    if p.returncode != 0:
        raise RuntimeError(f"the live count did not read: {p.stderr[-600:]}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def _launch() -> subprocess.Popen:
    env = dict(os.environ, PYTHONPATH=str(_REPO_ROOT))
    return subprocess.Popen([sys.executable, str(_SUBJECT)], cwd=str(_REPO_ROOT), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")


def _two_at_once() -> dict:
    if not _CONCURRENT:
        before = _live_counts()
        procs = [_launch(), _launch()]
        outs = [p.communicate(timeout=PROOF_TIMEOUT_S // 2)[0] for p in procs]
        _CONCURRENT.update(before=before, after=_live_counts(), rcs=[p.returncode for p in procs], outs=outs)
    return _CONCURRENT


def test_two_concurrent_copies_both_stay_green():
    r = _two_at_once()
    bad = [line.strip() for o in r["outs"] for line in o.splitlines() if "FAIL" in line]
    assert r["rcs"] == [0, 0] and not bad, f"rcs={r['rcs']} teeth={bad[:4]}"


def test_a_run_leaves_the_live_counts_unchanged():
    r = _two_at_once()
    moved = {k: (r["before"][k], r["after"][k]) for k in r["before"] if r["before"][k] != r["after"][k]}
    assert not moved, (f"live counts moved across two runs of {_SUBJECT.name} (before, after): {moved}; "
                       f"a move in the {_PREFIX} rows is this proof's leak, a move in the totals "
                       f"alone is another writer")


def test_a_lone_copy_stays_green():
    p = _launch()
    out = p.communicate(timeout=PROOF_TIMEOUT_S // 2)[0]
    assert p.returncode == 0 and "FAIL" not in out, out[-600:]


def main() -> int:
    fails = 0
    for name in PROVES["42b9ca9594e8"].values():
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

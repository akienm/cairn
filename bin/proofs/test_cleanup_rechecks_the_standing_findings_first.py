"""Proof for ticket 95557c2ed44f, clause 4: ``cairn cleanup`` hands the build inspector's recheck
every standing inspector-new-finding-* trouble id, and only those, before the drain.

Measured 2026-11-16: bin/cmd/cleanup had one step, ``cairn trouble drain``, and nothing re-ran a
sieve when a voyage ended, so a finding trouble whose cause the voyage fixed stood until a hand
ran the whole-repo sweep. Clauses 1-3 (the recheck clears only what no longer fires) berth with
the inspector: cairn/machines/build_inspector/proofs/test_cleanup_clears_only_the_finding_whose_cause_is_gone.py.

The world: a scratch copy of bin/cmd/cleanup beside a stub ``cairn`` (answering ``trouble live
--json`` from a fixture and logging every call) and a stub inspector module on the scratch
root, so nothing live is drained or rechecked.

    python3 bin/proofs/test_cleanup_rechecks_the_standing_findings_first.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"95557c2ed44f": {"4": "test_cleanup_hands_the_recheck_every_standing_finding_id"}}

_FAKE_CAIRN = """#!/usr/bin/env bash
echo "cairn $*" >> "$TESTING_9555_LOG"
case "$*" in
  "trouble live --json") cat "$TESTING_9555_LIVE" ;;
  "trouble drain") echo '{"folded_count": 0, "refused": []}' ;;
  *) exit 1 ;;
esac
"""
_FAKE_INSPECTOR = """import os, sys
with open(os.environ["TESTING_9555_LOG"], "a") as f:
    f.write("inspector " + " ".join(sys.argv[1:]) + "\\n")
print('{"rechecked": [], "cleared": [], "standing": [], "unknown": []}')
"""


def test_cleanup_hands_the_recheck_every_standing_finding_id():
    top = scratch_dir("testing-9555-bin-")
    (top / "bin" / "cmd").mkdir(parents=True)
    shutil.copyfile(_REPO_ROOT / "bin" / "cmd" / "cleanup", top / "bin" / "cmd" / "cleanup")
    (top / "bin" / "cairn").write_text(_FAKE_CAIRN, encoding="utf-8")
    os.chmod(top / "bin" / "cairn", 0o755)
    stub = top / "cairn" / "machines" / "build_inspector"
    stub.mkdir(parents=True)
    (stub / "inspector.py").write_text(_FAKE_INSPECTOR, encoding="utf-8")
    live = top / "live.json"
    live.write_text(json.dumps([
        {"id": "inspector-new-finding-testing-a", "standing": "OPEN"},
        {"id": "working-tree-clean", "standing": "OPEN"},
        {"id": "inspector-new-finding-testing-b", "standing": "OPEN"}]), encoding="utf-8")
    log = top / "calls.log"
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.update(TESTING_9555_LOG=str(log), TESTING_9555_LIVE=str(live))
    out = subprocess.run(["bash", str(top / "bin" / "cmd" / "cleanup")], env=env,
                         capture_output=True, text=True, timeout=60)
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    want = "inspector --recheck inspector-new-finding-testing-a inspector-new-finding-testing-b"
    assert want in calls, f"cleanup never handed the recheck the standing ids; calls: {calls}\n{out.stdout}{out.stderr}"
    assert "cairn trouble drain" in calls and calls.index(want) < calls.index("cairn trouble drain"), (
        f"the recheck did not run before the drain: {calls}")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

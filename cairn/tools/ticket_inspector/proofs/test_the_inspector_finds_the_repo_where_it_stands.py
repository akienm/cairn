"""Proof that ticket_inspector resolves an owning intention against the repo it stands in.

Measured 2026-11-13 on Windows: ``CAIRN_ROOT`` was ``~/dev/src/cairn``, a path that exists only on a
box that keeps the repo there. On any other box (this one keeps it at C:\\automation\\local\\cairn)
``owning_intention_resolves`` reported a real, existing intention as unresolved, and
cairn/tools/base/proofs/test_the_ticket_is_three_files.py's reader_ticket_inspector tooth went red.
The repo's own address is ``cairn.tools.base.address.ROOTS["repo"]``.

Each tooth runs the inspector in a child whose HOME and USERPROFILE are an empty scratch directory,
so ``~/dev/src/cairn`` cannot exist: the red does not depend on where this box keeps the repo, and
reds on Linux too.

    python <this file>
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

PROVES = {
    "06f4cff87495": {
        "1": "an_existing_owning_intention_resolves_when_the_repo_is_not_under_home",
        "2": "an_owning_intention_that_does_not_exist_is_still_reported",
    },
}

_CHILD = (
    "import json, sys\n"
    "from cairn.tools.ticket_inspector.inspector import inspect_ticket\n"
    "t = {'id': 'x', 'owning_intention': sys.argv[1]}\n"
    "print('FINDINGS=' + json.dumps([f['check'] for f in inspect_ticket(t)]))\n"
)


def _checks(owning: str) -> list[str]:
    from cairn.tools.scratch.scratch import scratch_dir
    home = str(scratch_dir("cairn-inspector-home-"))
    env = dict(os.environ, HOME=home, USERPROFILE=home, PYTHONPATH=str(REPO))
    r = subprocess.run([sys.executable, "-c", _CHILD, owning], env=env, cwd=home,
                       capture_output=True, text=True, timeout=120)
    line = next((l for l in r.stdout.splitlines() if l.startswith("FINDINGS=")), None)
    assert line is not None, (r.stdout, r.stderr[-400:])
    return json.loads(line[len("FINDINGS="):])


def test_an_existing_owning_intention_resolves_when_the_repo_is_not_under_home():
    owning = "cairn/tools/ticket_inspector/intention+why.json"
    assert (REPO / owning).exists(), f"fixture intention is gone: {owning}"
    got = _checks(owning)
    assert "owning_intention_resolves" not in got, got


def test_an_owning_intention_that_does_not_exist_is_still_reported():
    got = _checks("cairn/tools/no_such_component/intention+why.json")
    assert "owning_intention_resolves" in got, got


def main() -> int:
    sys.path.insert(0, str(REPO))
    bad = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except Exception as e:  # noqa: BLE001
                bad += 1
                print(f"  FAIL {name}: {e}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

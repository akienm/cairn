"""Proof for ticket c54fd914f05a: the tester's red cast commits by naming its paths, past the
commons' armed artifact check, so the next red casts too.

Measured 2026-11-16 on akiendelllinux, sealing two red proofs from the component-color-reseals
worktree. Both casts (f9c7ac6a69ba, 6fb272ba3d64) landed in the worktree's commons, and both
commits were refused by the commons' pre-commit hook: "artifact check: commit names its paths:
git commit -m ... -- <paths>; another session's staged work is in this index (index)".
red_tickets._commit stages each file by name, then runs a plain ``git commit -q -m``, and a
plain commit hands the hook the shared index, which ``check_shared_index`` refuses (ticket
23c822fe8095). Each run raised RedTicketRefused and left its cast staged. The second proof's
run then found that staged cast, took it for another writer's work, and held its own red
(``_hold``) instead of casting it, until a hand committed the first.

  1. a red cast under the armed check commits: one new commons commit carries the cast, and
     the commons is left with nothing staged;
  2. a second red, cast after the first in the same process, casts and commits too, and
     nothing is held.

The world: the sibling proof's (test_red_tickets_asks_the_commons_git_not_the_hooks.py) scratch
repo with red proofs and an outline, a scratch commons in git with the live store charter, and a
fake claude reader. The commons' pre-commit hook is armed with the artifact door's own
``check_shared_index``, the predicate that refused the live commits, run from this checkout.

    bin/cairn test cairn/devices/tester/proofs/test_a_cast_red_commits_past_the_armed_path_check.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"c54fd914f05a": {
    "1": "test_a_cast_commits_past_the_armed_path_check",
    "2": "test_a_second_red_casts_instead_of_holding"}}

PROOF_TIMEOUT_S = 600

RED_ONE = "cairn/a/proofs/test_one.py"
RED_TWO = "cairn/a/proofs/test_two.py"
OUTLINE = "1 Cairn\n  1.1 the tester\n"

_FAKE = r'''#!/usr/bin/env python3
"""testing: a fake claude reader for ticket c54fd914f05a."""
import json, sys
sys.stdin.read()
print(json.dumps({"is_error": False, "structured_output": {"touches": [], "conflicts": []}}))
'''

# The armed check: the artifact door's shared-index predicate, as the live hook runs it first.
_HOOK = """#!/usr/bin/env bash
# testing: the commons' path check for ticket c54fd914f05a
exec env PYTHONPATH={repo} python3 -c '
import os, sys
from pathlib import Path
from cairn.tools.artifact.artifact import check_shared_index
faults = check_shared_index(Path(os.getcwd()), os.environ.get("GIT_INDEX_FILE"))
for f in faults:
    print("artifact check: " + f, file=sys.stderr)
sys.exit(1 if faults else 0)
'
"""


def _git(where: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    got = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True, env=env)
    assert got.returncode == 0, (args, got.stderr)
    return got.stdout.strip()


def _world(tag: str, monkeypatch) -> types.SimpleNamespace:
    from cairn.devices.tester import red_tickets
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    top = Path(scratch_dir(f"testing-c54f-{tag}-"))
    repo, commons, reader = top / "repo", top / "CairnCommons", top / "reader"
    (repo / "cairn" / "a" / "proofs").mkdir(parents=True)
    (repo / "press_office").mkdir()
    (repo / "press_office" / "CairnComponentOutline.txt").write_text(OUTLINE, encoding="utf-8")
    (repo / "cairn" / "a" / "intention+why.json").write_text(json.dumps({"component": "a"}), encoding="utf-8")
    for red in (RED_ONE, RED_TWO):
        (repo / red).write_text('"""testing: a proof that reds."""\nraise SystemExit(1)\n', encoding="utf-8")
    for cmd in (["init", "-q"], ["add", "-A"]):
        _git(repo, *cmd)
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    live = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    shutil.copyfile(live, tickets / "_charter+why.json")
    for cmd in (["init", "-q"], ["config", "user.name", "testing"],
                ["config", "user.email", "testing@invalid"], ["add", "-A"],
                ["commit", "-q", "-m", "testing: the store charter"]):
        _git(commons, *cmd)
    hook = commons / ".git" / "hooks" / "pre-commit"
    hook.write_text(_HOOK.format(repo=_REPO_ROOT), encoding="utf-8")
    hook.chmod(0o755)
    reader.mkdir()
    fake = reader / "claude"
    fake.write_text(_FAKE, encoding="utf-8")
    fake.chmod(0o755)
    raiser = {"repo": top / "world", "commons": top / "world", "instance": top / "world"}
    monkeypatch.setattr(red_tickets, "ROOTS", {"repo": repo, "tickets": tickets, "commons": commons,
                                               "berths": top / "berths", "trace": top / "trace",
                                               "raiser": raiser, "claude": fake})
    held: list = []
    monkeypatch.setattr(red_tickets, "_hold", lambda items, staged, top, run_record: held.append(
        {"paths": [i["path"] for i in items], "staged": staged}))
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": repo})
    from cairn.tools.base import transitions
    monkeypatch.setenv(transitions.PROOF_ENV, "testing-c54fd914f05a")
    return types.SimpleNamespace(top=top, repo=repo, commons=commons, held=held)


def _restore():
    from cairn.tools.artifact import artifact as A
    A.set_diagnostic_roots(None)


def _red(proof: str) -> list[dict]:
    return [{"proof": proof, "verdict": "red", "teeth_red": ["test_it"]}]


def _staged(commons: Path) -> list[str]:
    return [x for x in _git(commons, "diff", "--cached", "--name-only").splitlines() if x]


def test_a_cast_commits_past_the_armed_path_check(monkeypatch):
    from cairn.devices.tester import red_tickets
    w = _world("one", monkeypatch)
    try:
        before = _git(w.commons, "rev-parse", "HEAD")
        plans = red_tickets.ticket_what_is_new(_red(RED_ONE))
        assert len(plans) == 1, plans
        assert len(_git(w.commons, "rev-list", f"{before}..HEAD").split()) == 1, "no commit landed"
        files = set(_git(w.commons, "diff", "--name-only", before, "HEAD").split())
        assert plans[0].resolve().relative_to(w.commons.resolve()).as_posix() in files, files
        assert _staged(w.commons) == [], f"the cast left staged: {_staged(w.commons)}"
    finally:
        _restore()


def test_a_second_red_casts_instead_of_holding(monkeypatch):
    from cairn.devices.tester import red_tickets
    w = _world("two", monkeypatch)
    try:
        before = _git(w.commons, "rev-parse", "HEAD")
        try:
            red_tickets.ticket_what_is_new(_red(RED_ONE))
        except red_tickets.RedTicketRefused:
            pass   # clause 1's failure; this tooth measures what the second red meets after it
        second = red_tickets.ticket_what_is_new(_red(RED_TWO))
        assert w.held == [], f"the second red was held, not cast: {w.held}"
        assert len(second) == 1, second
        assert len(_git(w.commons, "rev-list", f"{before}..HEAD").split()) == 2, "two casts, two commits"
        assert _staged(w.commons) == [], f"left staged: {_staged(w.commons)}"
    finally:
        _restore()


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

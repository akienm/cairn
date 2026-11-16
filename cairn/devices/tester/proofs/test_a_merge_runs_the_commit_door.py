#!/usr/bin/env python3
"""Proof that a merge into cairn runs the commit door (ticket db250e9bf3f9).

WHAT IT PROVES: a land is a git merge, and a merge that needs no conflict resolved runs the
pre-merge-commit hook, never pre-commit. With none installed, every land on main walked
around the artifact check (measured 2026-11-16: 7 of the last 40 cairn main commits were
merges). The tester now installs a pre-merge-commit that execs the installed pre-commit.

HOW: a scratch git repo holds STUB doors where the hook looks for the real ones:
``cairn/tools/artifact/__main__.py`` refuses any staged path containing ``hand-edit`` and
records the GIT_INDEX_FILE it was handed, and ``cairn/devices/tester/cli.py`` is the reseal
step that does nothing. The hooks are installed with the real ``install_hook`` and git merges
for real. The stubs make the door's answer known, so the teeth measure the WIRING: whether a
merge asks the door at all, and what index name the door is handed.

    python3 cairn/devices/tester/proofs/test_a_merge_runs_the_commit_door.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"db250e9bf3f9": {
    "1": "test_both_hooks_install_and_verify_together",
    "2": "test_a_merge_the_door_refuses_does_not_land",
    "3": "test_a_clean_merge_lands_and_the_door_saw_no_shared_index",
}}

FAILURES: list[str] = []

_STUB_ARTIFACT = '''import os, subprocess, sys
from pathlib import Path
seen = Path(os.environ["DOOR_SEEN"])
seen.write_text(os.environ.get("GIT_INDEX_FILE", "<unset>"))
staged = subprocess.run(["git", "diff", "--cached", "--name-only", "HEAD"],
                        capture_output=True, text=True, check=True).stdout.split()
bad = [p for p in staged if "hand-edit" in p]
if bad:
    print(f"artifact check: REFUSED {bad}", file=sys.stderr)
    sys.exit(2)
print("artifact check: every staged record is journaled")
'''

_ENV = {"GIT_AUTHOR_NAME": "proof", "GIT_AUTHOR_EMAIL": "proof@scratch",
        "GIT_COMMITTER_NAME": "proof", "GIT_COMMITTER_EMAIL": "proof@scratch",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0"}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _git(repo: Path, *args: str, ok: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                       env={**os.environ, **_ENV, "DOOR_SEEN": str(repo.parent / "door_seen")})
    if ok and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p


def _scratch_repo() -> Path:
    repo = scratch_dir("cairn-merge-door-proof-") / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    for rel, body in {"cairn/tools/artifact/artifact.py": "",
                      "cairn/tools/artifact/__main__.py": _STUB_ARTIFACT,
                      "cairn/devices/tester/reseal.py": "",
                      "cairn/devices/tester/cli.py": ""}.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(body, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-verify", "-m", "stub doors")
    return repo


def _branch_with(repo: Path, branch: str, rel: str) -> None:
    """A branch adding ``rel``, and main moved past the fork, so the merge is a true merge."""
    _git(repo, "checkout", "-q", "-b", branch, "main")
    (repo / rel).write_text(branch, encoding="utf-8")
    _git(repo, "add", "--", rel)
    _git(repo, "commit", "-q", "--no-verify", "-m", branch)
    _git(repo, "checkout", "-q", "main")
    (repo / f"main-{branch}.txt").write_text("main moves", encoding="utf-8")
    _git(repo, "add", "--", f"main-{branch}.txt")
    _git(repo, "commit", "-q", "--no-verify", "-m", f"main past {branch}")


def test_both_hooks_install_and_verify_together(repo: Path) -> None:
    from cairn.devices.tester import reseal
    name = PROVES["db250e9bf3f9"]["1"]
    res = reseal.install_hook(repo)
    merge_hook = Path(_git(repo, "rev-parse", "--path-format=absolute",
                           "--git-path", "hooks/pre-merge-commit").stdout.strip())
    src = getattr(reseal, "MERGE_HOOK_SOURCE", None)
    got = merge_hook.read_bytes() if merge_hook.exists() else b""
    want = src.read_bytes().replace(b"\r\n", b"\n") if src else None
    green = reseal.verify_hook(repo)
    removed = None
    if merge_hook.exists():
        saved = merge_hook.read_bytes()
        merge_hook.unlink()
        removed = reseal.verify_hook(repo)
        merge_hook.write_bytes(saved)
        merge_hook.chmod(0o755)
    check(name, res["installed"] and got == want and b"\r" not in got
          and os.access(merge_hook, os.X_OK) and green["green"]
          and removed is not None and not removed["green"],
          f"pre-merge-commit installed={merge_hook.exists()} equals source={got == want} "
          f"verify both={green['green']} verify without it={removed and removed['green']}")


def test_a_merge_the_door_refuses_does_not_land(repo: Path) -> None:
    name = PROVES["db250e9bf3f9"]["2"]
    _branch_with(repo, "refused", "state-hand-edit.json")
    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    m = _git(repo, "merge", "--no-ff", "--no-edit", "refused", ok=False)
    after = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "merge", "--abort", ok=False)
    check(name, m.returncode != 0 and after == before and "REFUSED" in m.stderr,
          f"merge rc={m.returncode} HEAD moved={after != before} "
          f"door refusal on stderr={'REFUSED' in m.stderr}")


def test_a_clean_merge_lands_and_the_door_saw_no_shared_index(repo: Path) -> None:
    name = PROVES["db250e9bf3f9"]["3"]
    seen = repo.parent / "door_seen"
    if seen.exists():
        seen.unlink()
    _branch_with(repo, "clean", "clean.txt")
    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    m = _git(repo, "merge", "--no-ff", "--no-edit", "clean", ok=False)
    parents = _git(repo, "log", "-1", "--format=%P").stdout.split()
    saw = seen.read_text() if seen.exists() else "<the door never ran>"
    check(name, m.returncode == 0 and len(parents) == 2 and before in parents
          and saw == "<unset>",
          f"merge rc={m.returncode} parents={len(parents)} door saw GIT_INDEX_FILE={saw!r}")


def main() -> int:
    repo = _scratch_repo()  # tooth 1 installs the hooks the other two merge under
    for tooth in (test_both_hooks_install_and_verify_together,
                  test_a_merge_the_door_refuses_does_not_land,
                  test_a_clean_merge_lands_and_the_door_saw_no_shared_index):
        try:
            tooth(repo)
        except Exception as exc:  # noqa: BLE001
            check(tooth.__name__, False, f"the tooth could not run to the end: {exc!r}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

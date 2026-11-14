"""Proof for ticket 23c822fe8095: a commit takes only the paths its author names.

Two sessions commit from one working tree and one git index, so a plain `git commit` carries
whatever the other session staged. Inside a pre-commit hook git names the index it hands over
in GIT_INDEX_FILE: the shared ``index`` for a plain commit (and --amend), ``index.lock`` for
-a, and a temp ``next-index-<pid>.lock`` for ``git commit -- <paths>`` (measured on Linux and
on git for Windows, recorded on the ticket). The artifact check now refuses every index but the
temp one, unless a merge, cherry-pick or revert is in progress. After a path commit it also
refreshes the shared index (git's ``index.lock``, which becomes ``index``) for each path the
hook staged into the temp index, so `git status` does not afterwards show a staged change
nobody made. It does this in pre-commit; nothing hangs off post-commit (Q#60).

The falsifier carries no (N) markers, so it is one clause, ``all``. Its tooth runs the four
narrow teeth end to end, each printing on its own, and reds when any reds:

T1  a plain `git commit` and `git commit -a` are refused, naming `git commit -m ... -- <paths>`;
T2  `git commit -- a` with b staged by "the other session" commits a and the hook-staged
    journal, and leaves b staged and uncommitted;
T3  after T2 the shared index holds no stale pre-commit blob for any path the commit wrote,
    and b's staged blob is byte-identical to before;
T4  a commit with MERGE_HEAD present is not refused.

Hermetic: a scratch CairnCommons git repo under a temp dir with the REAL artifact hook,
installed by `cairn artifact install-hook` and pointed at it through CAIRN_ARTIFACT_ROOTS.

Run bare:  PYTHONPATH=. python3 cairn/tools/artifact/proofs/test_a_commit_takes_only_the_paths_its_author_names.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"23c822fe8095": {"all": "a_commit_takes_only_the_paths_its_author_names"}}

FAILURES: list[str] = []
JOURNAL = ".artifact-journal.jsonl"


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:400]}")
    if not ok:
        FAILURES.append(name)
    return ok


def _run(args, cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), env=env, capture_output=True, text=True)


def _git(root: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    return _run(["git", "-C", str(root), *args], root, env)


def _out(root: Path, env: dict, *args: str) -> str:
    r = _git(root, env, *args)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def _door_write(root: Path, env: dict, rel: str, doc: dict) -> None:
    """A record write through the door, so the journal moves and the hook has a path to stage."""
    # bytes, not text=True: a text-mode pipe on Windows turns "\n" into "\r\n", and the door
    # rightly refuses a JSON record that is not canonical (LF) — the fixture must hand it LF
    r = subprocess.run([sys.executable, "-m", "cairn.tools.artifact", "write", str(root / rel),
                        "--verb", "cast", "--why", "proof fixture", "--stdin"], cwd=str(REPO), env=env,
                       capture_output=True, input=(json.dumps(doc, indent=2) + "\n").encode("utf-8"))
    if r.returncode:
        raise RuntimeError(f"door write {rel}: {r.stderr.decode('utf-8', 'replace').strip()[-300:]}")


def _world(tmp: Path) -> tuple[Path, dict]:
    root = tmp / "CairnCommons"
    (root / "ideas").mkdir(parents=True)
    from cairn.tools.scratch.scratch import home_env
    env = {k: v for k, v in home_env(tmp).items() if not k.startswith("GIT_")}
    env.update({"PYTHONPATH": str(REPO), "CAIRN_REPO": str(REPO),
                "CAIRN_ARTIFACT_ROOTS": json.dumps({"CairnCommons": str(root), "parked": str(tmp / "parked")}),
                "GIT_CONFIG_NOSYSTEM": "1"})
    _out(root, env, "init", "-q")
    for k, v in (("user.email", "proof@cairn"), ("user.name", "proof"), ("commit.gpgsign", "false")):
        _out(root, env, "config", k, v)
    for name in ("a", "b"):
        (root / f"{name}.txt").write_text(f"{name}0\n")
    _door_write(root, env, "ideas/first.json", {"id": "first"})
    _out(root, env, "add", "--", "a.txt", "b.txt", "ideas/first.json", JOURNAL)
    _out(root, env, "commit", "-q", "--no-verify", "-m", "fixture")
    r = _run([sys.executable, "-m", "cairn.tools.artifact", "install-hook", "CairnCommons"], REPO, env)
    if r.returncode or not (root / ".git" / "hooks" / "pre-commit").exists():
        raise RuntimeError(f"install-hook: {r.stdout.strip()} {r.stderr.strip()[-300:]}")
    return root, env


def t1_a_shared_index_commit_is_refused(root: Path, env: dict) -> bool:
    (root / "a.txt").write_text("a1\n")
    _out(root, env, "add", "--", "a.txt")
    head = _out(root, env, "rev-parse", "HEAD")
    plain = _git(root, env, "commit", "-q", "-m", "plain")
    every = _git(root, env, "commit", "-q", "-a", "-m", "all")
    still = _out(root, env, "rev-parse", "HEAD")
    named = all(r.returncode != 0 and "git commit -m ... -- <paths>" in r.stderr for r in (plain, every))
    return check("T1_a_plain_and_an_all_commit_are_refused_naming_the_path_commit",
                 named and still == head,
                 f"plain rc {plain.returncode} {plain.stderr.strip()[-160:]!r}; "
                 f"-a rc {every.returncode} {every.stderr.strip()[-160:]!r}; head moved {still != head}")


def t2_t3_a_path_commit_leaves_the_other_sessions_staging(root: Path, env: dict) -> tuple[bool, bool]:
    (root / "b.txt").write_text("b-other-session\n")
    _out(root, env, "add", "--", "b.txt")
    b_staged = _out(root, env, "rev-parse", ":b.txt")
    _door_write(root, env, "ideas/second.json", {"id": "second"})
    _out(root, env, "add", "--", "ideas/second.json")  # a path commit names only tracked paths
    (root / "a.txt").write_text("a2\n")
    parent = _out(root, env, "rev-parse", "HEAD").strip()
    r = _git(root, env, "commit", "-q", "-m", "only a", "--", "a.txt", "ideas/second.json")
    wrote = _out(root, env, "diff", "--name-only", parent, "HEAD").split()
    ok2 = check("T2_a_path_commit_carries_its_paths_and_the_journal_and_leaves_b_staged",
                r.returncode == 0 and sorted(wrote) == sorted(["a.txt", "ideas/second.json", JOURNAL])
                and "b.txt" in _out(root, env, "diff", "--cached", "--name-only").split(),
                f"rc {r.returncode} {r.stderr.strip()[-200:]!r}; wrote {wrote}")
    stale = [p for p in wrote if _out(root, env, "rev-parse", f":{p}") != _out(root, env, "rev-parse", f"HEAD:{p}")]
    staged_now = _out(root, env, "diff", "--cached", "--name-only").split()
    ok3 = check("T3_the_shared_index_holds_no_stale_blob_and_b_is_byte_identical",
                ok2 and not stale and staged_now == ["b.txt"]
                and _out(root, env, "rev-parse", ":b.txt") == b_staged,
                f"stale {stale}; staged now {staged_now}")
    return ok2, ok3


def t4_a_merge_in_progress_is_not_refused(root: Path, env: dict) -> bool:
    _out(root, env, "reset", "-q")  # T4 stands alone: whatever T1-T3 left staged is unstaged
    _out(root, env, "checkout", "-q", "--", ".")
    base = _out(root, env, "rev-parse", "HEAD").strip()
    _out(root, env, "checkout", "-q", "-b", "side")
    (root / "c.txt").write_text("c\n")
    _out(root, env, "add", "--", "c.txt")
    _out(root, env, "commit", "-q", "--no-verify", "-m", "side")
    _out(root, env, "checkout", "-q", "-")
    (root / "d.txt").write_text("d\n")
    _out(root, env, "add", "--", "d.txt")
    _out(root, env, "commit", "-q", "--no-verify", "-m", "main")
    m = _git(root, env, "merge", "--no-commit", "--no-ff", "side")
    in_merge = (root / ".git" / "MERGE_HEAD").exists()
    r = _git(root, env, "commit", "-q", "-m", "merge side")
    parents = _out(root, env, "rev-list", "--parents", "-n", "1", "HEAD").split()
    return check("T4_a_commit_with_MERGE_HEAD_present_is_not_refused",
                 in_merge and r.returncode == 0 and len(parents) == 3 and base not in parents[:1],
                 f"merge rc {m.returncode}; MERGE_HEAD {in_merge}; commit rc {r.returncode} "
                 f"{r.stderr.strip()[-200:]!r}; parents {len(parents) - 1}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cairn-commit-names-paths-proof-") as d:
        root, env = _world(Path(d))
        ok1 = t1_a_shared_index_commit_is_refused(root, env)
        ok2, ok3 = t2_t3_a_path_commit_leaves_the_other_sessions_staging(root, env)
        ok4 = t4_a_merge_in_progress_is_not_refused(root, env)
    check(PROVES["23c822fe8095"]["all"], ok1 and ok2 and ok3 and ok4)
    print(f"\n{len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

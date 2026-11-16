"""Proof for ticket d1f5b4ce8001: a merge into the commons runs the artifact door.

A land is a git merge, and a merge that needs no conflict resolved runs pre-merge-commit, never
pre-commit. The commons carried only pre-commit and commit-msg (measured 2026-11-16), so every
commons land walked around the artifact check. `cairn artifact install-hook` now installs
hooks/pre-merge-commit beside pre-commit; it unsets GIT_INDEX_FILE and execs the installed
pre-commit, because inside pre-merge-commit MERGE_HEAD is not yet written and the shared-index
guard would otherwise refuse every land.

Three teeth, one per falsifier clause:
1  install-hook lays pre-merge-commit beside pre-commit, LF and executable, equal to its tracked
   source, and refuses (writing nothing) over a pre-merge-commit that is not the artifact door's;
2  a non-conflicting --no-ff merge of a branch carrying a record written around the door is
   refused: git merge exits non-zero and HEAD does not move (red on origin/main, where it commits);
3  a non-conflicting --no-ff merge of a branch whose record went through the door commits.

Hermetic: a scratch CairnCommons repo with the REAL artifact door and hooks, reached through
CAIRN_ARTIFACT_ROOTS, as in test_a_commit_takes_only_the_paths_its_author_names.py.

Run bare:  PYTHONPATH=. python3 cairn/tools/artifact/proofs/test_a_commons_merge_runs_the_artifact_door.py
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

TID = "d1f5b4ce8001"
PROVES = {TID: {
    "1": "test_install_hook_lays_the_merge_hook_and_refuses_a_foreign_one",
    "2": "test_a_merge_carrying_a_record_around_the_door_is_refused",
    "3": "test_a_merge_of_a_door_written_record_commits",
}}

FAILURES: list[str] = []
JOURNAL = ".artifact-journal.jsonl"
SRC = REPO / "cairn" / "tools" / "artifact" / "hooks" / "pre-merge-commit"


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  — {detail[:400]}")
    if not ok:
        FAILURES.append(name)
    return ok


def _run(args, cwd: Path, env: dict, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), env=env, capture_output=True, text=True, input=stdin)


def _git(root: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    return _run(["git", "-C", str(root), *args], root, env)


def _out(root: Path, env: dict, *args: str) -> str:
    r = _git(root, env, *args)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def _door(env: dict, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return _run([sys.executable, "-m", "cairn.tools.artifact", *args], REPO, env, stdin=stdin)


def _door_write(root: Path, env: dict, rel: str, doc: dict) -> None:
    r = _door(env, "write", str(root / rel), "--verb", "cast", "--why", "proof fixture", "--stdin",
              stdin=json.dumps(doc, indent=2) + "\n")
    if r.returncode:
        raise RuntimeError(f"door write {rel}: {r.stderr.strip()[-300:]}")


def _world(tmp: Path) -> tuple[Path, dict]:
    root = tmp / "CairnCommons"
    (root / "ideas").mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"PYTHONPATH": str(REPO), "CAIRN_REPO": str(REPO),
                "CAIRN_ARTIFACT_ROOTS": json.dumps({"CairnCommons": str(root), "parked": str(tmp / "parked")}),
                "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(tmp), "GIT_TERMINAL_PROMPT": "0"})
    _out(root, env, "init", "-q", "-b", "main")
    for k, v in (("user.email", "proof@cairn"), ("user.name", "proof"), ("commit.gpgsign", "false")):
        _out(root, env, "config", k, v)
    (root / "a.txt").write_text("a0\n")
    _door_write(root, env, "ideas/first.json", {"id": "first"})
    _out(root, env, "add", "--", "a.txt", "ideas/first.json", JOURNAL)
    _out(root, env, "commit", "-q", "--no-verify", "-m", "fixture")
    return root, env


def test_install_hook_lays_the_merge_hook_and_refuses_a_foreign_one(root: Path, env: dict) -> None:
    name = PROVES[TID]["1"]
    hooks = root / ".git" / "hooks"
    foreign = hooks / "pre-merge-commit"
    foreign.write_text("#!/bin/sh\nexit 0\n")
    refused = _door(env, "install-hook", "CairnCommons")
    kept = foreign.read_text() == "#!/bin/sh\nexit 0\n" and not (hooks / "pre-commit").exists()
    foreign.unlink()
    r = _door(env, "install-hook", "CairnCommons")
    laid = foreign.exists() and SRC.exists() and foreign.read_bytes() == SRC.read_bytes()
    lf = laid and b"\r" not in foreign.read_bytes()
    x = laid and os.access(foreign, os.X_OK) and os.access(hooks / "pre-commit", os.X_OK)
    check(name, refused.returncode != 0 and kept and r.returncode == 0 and laid and lf and x,
          f"foreign: rc={refused.returncode} kept={kept}; install rc={r.returncode} laid={laid} lf={lf} "
          f"exec={x} {r.stderr.strip()[-160:]!r}")


def _branch_and_main(root: Path, env: dict, branch: str, rel: str, door: bool) -> None:
    _out(root, env, "checkout", "-q", "-b", branch, "main")
    if door:
        _door_write(root, env, rel, {"id": branch})
        _out(root, env, "add", "--", rel, JOURNAL)
    else:
        (root / rel).write_text(json.dumps({"id": branch}, indent=2) + "\n")
        _out(root, env, "add", "--", rel)
    _out(root, env, "commit", "-q", "--no-verify", "-m", f"{branch}: {rel}")
    _out(root, env, "checkout", "-q", "main")
    (root / "a.txt").write_text(f"a-{branch}\n")
    _out(root, env, "add", "--", "a.txt")
    _out(root, env, "commit", "-q", "--no-verify", "-m", f"main beside {branch}")


def test_a_merge_of_a_door_written_record_commits(root: Path, env: dict) -> None:
    name = PROVES[TID]["3"]
    _branch_and_main(root, env, "clean", "ideas/clean.json", door=True)
    head = _out(root, env, "rev-parse", "HEAD")
    m = _git(root, env, "merge", "-q", "--no-ff", "-m", "land clean", "clean")
    parents = _out(root, env, "rev-list", "--parents", "-n", "1", "HEAD").split()
    check(name, m.returncode == 0 and len(parents) == 3 and parents[1] == head,
          f"merge rc={m.returncode} parents={len(parents) - 1} {m.stderr.strip()[-200:]!r}")


def test_a_merge_carrying_a_record_around_the_door_is_refused(root: Path, env: dict) -> None:
    name = PROVES[TID]["2"]
    _branch_and_main(root, env, "around", "ideas/around.json", door=False)
    head = _out(root, env, "rev-parse", "HEAD")
    m = _git(root, env, "merge", "-q", "--no-ff", "-m", "land around", "around")
    moved = _out(root, env, "rev-parse", "HEAD") != head
    said = "artifact check" in m.stderr
    _git(root, env, "merge", "--abort")
    check(name, m.returncode != 0 and not moved and said,
          f"merge rc={m.returncode} HEAD moved={moved} door spoke={said} {m.stderr.strip()[-200:]!r}")


TEETH = (test_install_hook_lays_the_merge_hook_and_refuses_a_foreign_one,
         test_a_merge_of_a_door_written_record_commits,
         test_a_merge_carrying_a_record_around_the_door_is_refused)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cairn-commons-merge-door-proof-") as d:
        root, env = _world(Path(d))
        for tooth in TEETH:
            try:
                tooth(root, env)
            except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                check(tooth.__name__, False, f"{type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else f'RED — {len(FAILURES)} failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

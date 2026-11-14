"""Proof for the red_tickets git-env fix: the commons' git calls ignore the repo whose hook runs us.

``red_tickets._git`` runs ``git -C <commons> ...`` from inside cairn's pre-commit hook, which exports
GIT_INDEX_FILE (and GIT_PREFIX) for CAIRN's index; ``git -C`` does not override it, so the call read cairn's index
against the commons' objects and every red ticket cast during a hooked reseal was refused (measured by
akienasus on the Dell: 'unable to read 94b599b2', cairn's README blob). The calls now go through the one settled scrub,
cairn.tools.scratch.scratch.git_env().

The world is two scratch repos: a 'cairn' with a tracked file and a 'commons' with a different one. The caller's
environment is set as the hook sets it, GIT_INDEX_FILE pointing at cairn's index. The proof runs the REAL
``red_tickets._git`` against the commons.

    python <this file>
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.devices.tester import red_tickets  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "9f5bb43e8a64": {
        "1": "a_commons_call_run_under_cairns_index_file_still_reads_the_commons",
        "2": "the_calls_are_scrubbed_of_every_repo_location_variable",
    },
}


def _git(repo: Path, *args: str, env=None) -> str:
    e = dict(os.environ if env is None else env, GIT_AUTHOR_NAME="p", GIT_AUTHOR_EMAIL="p@p",
             GIT_COMMITTER_NAME="p", GIT_COMMITTER_EMAIL="p@p")
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=e, check=True).stdout.strip()


def _world():
    tmp = Path(str(scratch_dir("red_tickets_git_env_")))
    cairn, commons = tmp / "cairn", tmp / "commons"
    clean = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    for repo, name, body in ((cairn, "README.md", "cairn readme\n"), (commons, "ticket.json", "{}\n")):
        repo.mkdir()
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True, env=clean)
        (repo / name).write_text(body, encoding="utf-8", newline="\n")
        _git(repo, "add", name, env=clean)
        _git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "init", env=clean)
    return tmp, cairn, commons, clean


def a_commons_call_run_under_cairns_index_file_still_reads_the_commons() -> None:
    tmp, cairn, commons, clean = _world()
    saved = {k: os.environ.get(k) for k in ("GIT_INDEX_FILE", "GIT_PREFIX")}
    try:
        # exactly what a hook exports for CAIRN's commit: a relative index path and an empty prefix
        os.environ["GIT_INDEX_FILE"] = str(cairn / ".git" / "index")
        os.environ["GIT_PREFIX"] = ""
        got = red_tickets._git(commons, "ls-files")
        assert got.returncode == 0, f"a commons call under cairn's GIT_INDEX_FILE failed: {got.stderr.strip()}"
        assert got.stdout.split() == ["ticket.json"], f"the call read another repo's index: {got.stdout!r}"
        head = red_tickets._git(commons, "rev-parse", "HEAD")
        assert head.returncode == 0 and head.stdout.strip() == _git(commons, "rev-parse", "HEAD", env=clean)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


def the_calls_are_scrubbed_of_every_repo_location_variable() -> None:
    names = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY")
    saved = {k: os.environ.get(k) for k in names}
    seen = {}
    real = subprocess.run

    def spy(args, *a, **kw):
        seen["env"] = kw.get("env")
        return real(args, *a, **kw)

    try:
        for k in names:
            os.environ[k] = "/elsewhere"
        red_tickets.subprocess.run = spy
        red_tickets._git(REPO, "--version")
    finally:
        red_tickets.subprocess.run = real
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    env = seen.get("env")
    assert env is not None, "red_tickets._git passes no env: it inherits the caller's repo-location variables"
    leaked = [k for k in names if k in env]
    assert not leaked, f"red_tickets._git still passes {leaked} to git"


TEETH = [a_commons_call_run_under_cairns_index_file_still_reads_the_commons,
         the_calls_are_scrubbed_of_every_repo_location_variable]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

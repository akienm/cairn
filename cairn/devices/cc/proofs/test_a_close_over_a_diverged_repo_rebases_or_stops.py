"""Proof for ticket 979a63671481 — a close over a repo that cannot push stops loud.

Measured 2026-11-20 on akiendelllinux, closing 380d524e6e9c: close.sh's commit_all ran
``(cd $CC && cairn artifact quiet -- git pull -q --rebase --autostash && git push -q 2>&1 | tail -1)``;
the pull failed ('fatal: Cannot rebase onto multiple branches.'), the push was refused, nothing read
either status, and the close printed '--- CROSSED TO BUILDME, NOT YET PROVED' and exited 4 with the
commons 5 commits ahead of origin.

Each tooth runs close.sh AS WRITTEN (copied at call time) under a scratch HOME. That HOME holds a
scratch house (``~/dev/src/cairn``) and a scratch commons (``~/dev/src/CairnCommons``), each a clone of
its own bare origin. The house carries the real selectors (house_paths.py, commons_paths.py) and two
stubs: ``bin/cairn`` (its ``artifact`` verb runs the real door from this house, ``cleanup`` is a no-op)
and ``sail.py`` (it leaves a marker and answers an accepted PROVED crossing). The commons holds one dirty
record of the ticket, so the close's first commit puts the local commons one commit ahead of origin,
then the tooth moves origin.

    python3 cairn/devices/cc/proofs/test_a_close_over_a_diverged_repo_rebases_or_stops.py   # exit 0 = green
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
HOUSE = HERE.parents[3]
_BASH = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"  # ticket f2a3b90c2931

PROVES = {"979a63671481": {
    "1": "test_a_diverged_commons_is_rebased_and_pushed_or_named",
    "2": "test_a_pull_that_fails_stops_the_close_before_any_crossing",
    "3": "test_a_repo_in_sync_closes_as_before",
}}

TID = "aaaaaaaaaaaa"
OWN = f"tickets/{TID}-a-title.state.json"
_ID = {"GIT_AUTHOR_NAME": "proof", "GIT_AUTHOR_EMAIL": "proof@example.invalid",
       "GIT_COMMITTER_NAME": "proof", "GIT_COMMITTER_EMAIL": "proof@example.invalid"}

_CAIRN_STUB = """#!/bin/bash
# scratch bin/cairn: the artifact verb is the real door, run from the house under proof
if [ "$1" = artifact ]; then shift; PYTHONPATH="{house}" exec "{py}" -m cairn.tools.artifact "$@"; fi
echo "cleanup: nothing (scratch)"; exit 0
"""
_SAIL_STUB = """import pathlib, sys
pathlib.Path(__file__).with_name("CROSS_CALLED").write_text(" ".join(sys.argv[1:]))
print("code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]")
"""


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=proof", "-c", "user.email=proof@example.invalid",
                        "-c", "core.hooksPath=/dev/null", *args],
                       cwd=repo, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"git {args} in {repo}: {r.stderr}"
    return r.stdout.strip()


def _repo(home: Path, name: str, files: dict[str, str]) -> Path:
    """A bare origin seeded with ``files`` and a clone of it at ~/dev/src/<name>, tracking origin/main."""
    origin = home / "origins" / f"{name}.git"
    origin.mkdir(parents=True)
    _git(origin, "init", "-q", "--bare", "-b", "main")
    seed = home / "seeds" / name
    seed.mkdir(parents=True)
    _git(seed, "init", "-q", "-b", "main")
    for p, body in files.items():
        (seed / p).parent.mkdir(parents=True, exist_ok=True)
        (seed / p).write_text(body, encoding="utf-8")
    _git(seed, "add", "-A")
    _git(seed, "commit", "-qm", "seed")
    _git(seed, "remote", "add", "origin", str(origin))
    _git(seed, "push", "-q", "origin", "main")
    clone = home / "dev" / "src" / name
    clone.parent.mkdir(parents=True, exist_ok=True)
    _git(clone.parent, "clone", "-q", str(origin), name)
    _git(clone, "config", "core.hooksPath", "/dev/null")
    return clone


def _world(home: Path) -> tuple[Path, Path]:
    sc = "cairn/devices/cc/scripts"
    house = _repo(home, "cairn", {
        "bin/cairn": _CAIRN_STUB.format(house=HOUSE, py=sys.executable),
        f"{sc}/close.sh": (SCRIPTS / "close.sh").read_text(encoding="utf-8"),
        f"{sc}/house_paths.py": (SCRIPTS / "house_paths.py").read_text(encoding="utf-8"),
        f"{sc}/commons_paths.py": (SCRIPTS / "commons_paths.py").read_text(encoding="utf-8"),
        f"{sc}/sail.py": _SAIL_STUB,
        ".gitignore": "CROSS_CALLED\n",
    })
    os.chmod(house / "bin" / "cairn", 0o755)
    commons = _repo(home, "CairnCommons", {
        f"tickets/{TID}-a-title.json": "{}\n",
        OWN: "line 1\n",
        "notes/other.json": "{}\n",
    })
    with open(commons / OWN, "a", encoding="utf-8") as f:  # the close's own record, dirty
        f.write("line 2 (the close)\n")
    return house, commons


def _origin_moves(home: Path, path: str, body: str) -> None:
    """Another hand pushes a commit to the commons origin."""
    other = home / "other"
    _git(home, "clone", "-q", str(home / "origins" / "CairnCommons.git"), "other")
    (other / path).write_text(body, encoding="utf-8")
    _git(other, "commit", "-qam", "another hand")
    _git(other, "push", "-q", "origin", "main")


def _close(home: Path, house: Path) -> tuple[int, str]:
    env = {**os.environ, **_ID, "HOME": str(home), "CLAUDE_SESSION_URL": "https://example.invalid/proof",
           "GIT_CONFIG_GLOBAL": str(home / "gitconfig"), "GIT_CONFIG_NOSYSTEM": "1"}
    (home / "gitconfig").write_text("[user]\n\tname = proof\n\temail = proof@example.invalid\n"
                                    "[core]\n\thooksPath = /dev/null\n", encoding="utf-8")
    r = subprocess.run([_BASH, str(house / "cairn/devices/cc/scripts/close.sh"), TID, "a note"],
                       cwd=house, env=env, capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout + r.stderr


def _ahead(repo: Path) -> int:
    _git(repo, "fetch", "-q")
    return int(_git(repo, "rev-list", "--count", "origin/main..HEAD"))


def _crossed(house: Path) -> bool:
    return (house / "cairn/devices/cc/scripts/CROSS_CALLED").exists()


def test_a_diverged_commons_is_rebased_and_pushed_or_named():
    with tempfile.TemporaryDirectory() as t:
        home = Path(t)
        house, commons = _world(home)
        _origin_moves(home, "notes/other.json", '{"another": "hand"}\n')
        rc, out = _close(home, house)
        ahead = _ahead(commons)
        if rc == 0:
            assert ahead == 0, f"close exited 0 with the commons {ahead} commit(s) ahead of origin:\n{out}"
            assert "line 2 (the close)" in _git(commons, "show", f"origin/main:{OWN}"), \
                f"origin lacks the close's own commit:\n{out}"
            print(f"    diverged commons rebased and pushed (rc 0, 0 ahead)")
        else:
            assert "NOT PUSHED" in out and str(commons) in out, \
                f"rc {rc} with the commons {ahead} ahead, and no line names it:\n{out}"
            print(f"    diverged commons named, rc {rc}")


def test_a_pull_that_fails_stops_the_close_before_any_crossing():
    with tempfile.TemporaryDirectory() as t:
        home = Path(t)
        house, commons = _world(home)
        _origin_moves(home, OWN, "line 1\nline 2 (another hand, conflicting)\n")
        rc, out = _close(home, house)
        ahead = _ahead(commons)
        assert rc not in (0, 4), f"close exited {rc} over a failed pull ({ahead} ahead):\n{out}"
        assert rc != 0, out
        assert "NOT PUSHED" in out and str(commons) in out, f"no line names the commons (rc {rc}):\n{out}"
        assert not _crossed(house), f"the close crossed after a failed pull:\n{out}"
        said = [ln for ln in out.splitlines() if "CROSSED" in ln or "[PROVED]" in ln]
        assert not said, f"the close printed a crossing line: {said}"
        st = _git(commons, "status")
        assert "rebase" not in st, f"the commons is left mid-rebase:\n{st}"
        print(f"    failed pull: rc {rc}, named, no crossing, {ahead} ahead, no rebase left open")


def test_a_repo_in_sync_closes_as_before():
    with tempfile.TemporaryDirectory() as t:
        home = Path(t)
        house, commons = _world(home)
        rc, out = _close(home, house)
        assert rc == 0, f"close over repos in sync exited {rc}:\n{out}"
        assert _crossed(house), f"the close never crossed:\n{out}"
        assert _ahead(commons) == 0 and _ahead(house) == 0, f"a repo left ahead:\n{out}"
        assert "NOT PUSHED" not in out and "NOT COMMITTED" not in out, out
        print("    in sync: rc 0, crossed, both repos level with origin")


def main() -> int:
    bad = 0
    for name in dict.fromkeys(PROVES["979a63671481"].values()):
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            bad += 1
            print(f"  FAIL  {name}\n        {type(exc).__name__}: {str(exc)[:900]}")
    print("red" if bad else "green")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

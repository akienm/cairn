"""Proof for ticket eb583e674939 — a close pulls and pushes the commons it names, and retries a push
origin outran.

Measured 2026-11-23 on akiendelllinux: close.sh exited 5 three times after a sealed hollow and a confirmed
verdict, 'NOT PUSHED: .../CairnCommons ... ! [rejected] main -> main (fetch first)'. sync_repo ran
``cd $d && cairn artifact quiet -- git pull ...``, and ``cairn artifact quiet`` runs its command from the
cairn root (its -C picks only the lock), so the commons pull re-pulled the house and the commons push
failed whenever origin had moved at all.

Each tooth runs close.sh AS WRITTEN (copied at call time) under a scratch HOME: a scratch house and a
scratch commons, each a clone of its own bare origin (the scaffolding of 979a63671481's proof,
test_a_close_over_a_diverged_repo_rebases_or_stops.py). The race is made deterministic by a ``git`` shim
first on the close's PATH: when its subcommand is ``push`` and its directory (``-C`` or cwd) is the
scratch commons, it counts the attempt and, for the first N attempts, pushes another hand's commit to the
commons origin before running the real git. The scratch bin/cairn changes into its own repo's root
before running the artifact door, as the real bin/cmd/artifact does: that is the behaviour the bug rode.

    python3 cairn/devices/cc/proofs/test_a_close_pulls_and_pushes_the_commons_it_names.py   # exit 0 = green
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
_REAL_GIT = shutil.which("git") or "git"

PROVES = {"eb583e674939": {
    "1": "test_a_commons_origin_moved_before_the_close_is_pulled_and_pushed",
    "2": "test_a_push_origin_outran_once_is_retried_and_lands",
    "3": "test_a_push_origin_outruns_every_time_stops_after_three",
    "4": "test_a_commons_in_sync_closes_as_before",
}}

TID = "aaaaaaaaaaaa"
OWN = f"tickets/{TID}-a-title.state.json"
_ID = {"GIT_AUTHOR_NAME": "proof", "GIT_AUTHOR_EMAIL": "proof@example.invalid",
       "GIT_COMMITTER_NAME": "proof", "GIT_COMMITTER_EMAIL": "proof@example.invalid"}

_CAIRN_STUB = """#!/bin/bash
# scratch bin/cairn: the artifact verb is the real door, run from the house under proof. Like the real
# bin/cmd/artifact it first changes into its own repo's root, so a command it runs starts there.
if [ "$1" = artifact ]; then shift; cd "$(dirname "$0")/.."; PYTHONPATH="{house}" exec "{py}" -m cairn.tools.artifact "$@"; fi
echo "cleanup: nothing (scratch)"; exit 0
"""
_SAIL_STUB = """import pathlib, sys
pathlib.Path(__file__).with_name("CROSS_CALLED").write_text(" ".join(sys.argv[1:]))
print("code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]")
"""
# The race. Subcommand = first argument that is not a global option (-C <dir>, -c <k=v>, or -*).
_GIT_SHIM = """#!/bin/bash
REAL="{real}"; COMMONS="{commons}"; ORIGIN="{origin}"; COUNT="{count}"; N=$(cat "{nfile}")
dir=$PWD; sub=""; args=("$@"); i=0
while [ $i -lt ${{#args[@]}} ]; do
  a=${{args[$i]}}
  case "$a" in
    -C) i=$((i+1)); dir=${{args[$i]}};;
    -c) i=$((i+1));;
    -*) ;;
    *) sub=$a; break;;
  esac
  i=$((i+1))
done
if [ "$sub" = push ] && [ "$(cd "$dir" 2>/dev/null && pwd -P)" = "$COMMONS" ]; then
  echo push >> "$COUNT"; c=$(wc -l < "$COUNT")
  if [ "$c" -le "$N" ]; then
    o="$(dirname "$COUNT")/hand$c"
    "$REAL" clone -q "$ORIGIN" "$o" >/dev/null 2>&1
    echo "{{\\"hand\\": $c}}" > "$o/notes/hand$c.json"
    "$REAL" -C "$o" add -A >/dev/null 2>&1
    "$REAL" -C "$o" -c core.hooksPath=/dev/null commit -qm "another hand $c" >/dev/null 2>&1
    "$REAL" -C "$o" push -q origin main >/dev/null 2>&1
  fi
fi
exec "$REAL" "$@"
"""


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run([_REAL_GIT, "-c", "user.name=proof", "-c", "user.email=proof@example.invalid",
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


def _world(home: Path, races: int) -> tuple[Path, Path]:
    """The scratch house and commons, and a git shim that lets origin outrun the first ``races`` pushes."""
    sc = "cairn/devices/cc/scripts"
    house = _repo(home, "cairn", {
        "bin/cairn": _CAIRN_STUB.format(house=HOUSE, py=sys.executable),
        f"{sc}/close.sh": (SCRIPTS / "close.sh").read_text(encoding="utf-8"),
        f"{sc}/prove.sh": (SCRIPTS / "prove.sh").read_text(encoding="utf-8"),
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
    race = home / "race"
    race.mkdir()
    (race / "n").write_text(str(races), encoding="utf-8")
    (race / "count").write_text("", encoding="utf-8")
    shim = home / "shimbin"
    shim.mkdir()
    (shim / "git").write_text(_GIT_SHIM.format(
        real=_REAL_GIT, commons=os.path.realpath(commons), origin=home / "origins" / "CairnCommons.git",
        count=race / "count", nfile=race / "n"), encoding="utf-8")
    os.chmod(shim / "git", 0o755)
    return house, commons


def _origin_moves(home: Path) -> None:
    """Another hand pushes a commit to the commons origin, before the close begins."""
    other = home / "other"
    _git(home, "clone", "-q", str(home / "origins" / "CairnCommons.git"), "other")
    (other / "notes/other.json").write_text('{"another": "hand"}\n', encoding="utf-8")
    _git(other, "commit", "-qam", "another hand, before the close")
    _git(other, "push", "-q", "origin", "main")


def _env(home: Path) -> dict:
    env = {**os.environ, **_ID, "HOME": str(home), "CLAUDE_SESSION_URL": "https://example.invalid/proof",
           "GIT_CONFIG_GLOBAL": str(home / "gitconfig"), "GIT_CONFIG_NOSYSTEM": "1",
           "PATH": f"{home / 'shimbin'}{os.pathsep}{os.environ.get('PATH', '')}"}
    (home / "gitconfig").write_text("[user]\n\tname = proof\n\temail = proof@example.invalid\n"
                                    "[core]\n\thooksPath = /dev/null\n", encoding="utf-8")
    return env


def _close(home: Path, house: Path) -> tuple[int, str]:
    r = subprocess.run([_BASH, str(house / "cairn/devices/cc/scripts/close.sh"), TID, "a note"],
                       cwd=house, env=_env(home), capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout + r.stderr


def _ahead(repo: Path) -> int:
    _git(repo, "fetch", "-q")
    return int(_git(repo, "rev-list", "--count", "origin/main..HEAD"))


def _crossed(house: Path) -> bool:
    return (house / "cairn/devices/cc/scripts/CROSS_CALLED").exists()


def _pushes(home: Path) -> int:
    return len((home / "race" / "count").read_text(encoding="utf-8").splitlines())


def _on_origin(commons: Path, path: str) -> str:
    return _git(commons, "show", f"origin/main:{path}")


def test_a_commons_origin_moved_before_the_close_is_pulled_and_pushed():
    with tempfile.TemporaryDirectory() as t:
        home = Path(t)
        house, commons = _world(home, races=0)
        _origin_moves(home)
        rc, out = _close(home, house)
        assert rc == 0, f"close exited {rc} over a commons whose origin had moved:\n{out}"
        ahead = _ahead(commons)
        assert ahead == 0, f"the commons is {ahead} commit(s) ahead of origin:\n{out}"
        assert "line 2 (the close)" in _on_origin(commons, OWN), f"origin lacks the close's record:\n{out}"
        assert '"another"' in _on_origin(commons, "notes/other.json"), "origin lost the other hand's commit"
        print("    origin moved before: rc 0, 0 ahead, both commits on origin")


def test_a_push_origin_outran_once_is_retried_and_lands():
    with tempfile.TemporaryDirectory() as t:
        home = Path(t)
        house, commons = _world(home, races=1)
        rc, out = _close(home, house)
        assert rc == 0, f"close exited {rc} when origin outran one push ({_pushes(home)} push(es)):\n{out}"
        ahead = _ahead(commons)
        assert ahead == 0, f"the commons is {ahead} commit(s) ahead of origin:\n{out}"
        assert "line 2 (the close)" in _on_origin(commons, OWN), f"origin lacks the close's record:\n{out}"
        assert '"hand": 1' in _on_origin(commons, "notes/hand1.json"), "origin lost the racing hand's commit"
        print(f"    outran once: rc 0, 0 ahead, {_pushes(home)} pushes, both commits on origin")


def test_a_push_origin_outruns_every_time_stops_after_three():
    with tempfile.TemporaryDirectory() as t:
        home = Path(t)
        house, commons = _world(home, races=99)
        rc, out = _close(home, house)
        n = _pushes(home)
        assert rc == 5, f"close exited {rc} when origin outran every push ({n} push(es)):\n{out}"
        assert "NOT PUSHED" in out and str(commons) in out, f"no line names the commons:\n{out}"
        assert n == 3, f"the close pushed the commons {n} time(s), not 3:\n{out}"
        assert "rebase" not in _git(commons, "status"), "the commons is left mid-rebase"
        print(f"    outran always: rc 5, named, {n} pushes")


def test_a_commons_in_sync_closes_as_before():
    with tempfile.TemporaryDirectory() as t:
        home = Path(t)
        house, commons = _world(home, races=0)
        rc, out = _close(home, house)
        assert rc == 0, f"close over repos in sync exited {rc}:\n{out}"
        assert _ahead(commons) == 0 and _ahead(house) == 0, f"a repo left ahead:\n{out}"
        assert "NOT PUSHED" not in out, out
        assert _crossed(house), f"the close never crossed:\n{out}"
        print("    in sync: rc 0, crossed, both repos level with origin")


def main() -> int:
    bad = 0
    for name in dict.fromkeys(PROVES["eb583e674939"].values()):
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

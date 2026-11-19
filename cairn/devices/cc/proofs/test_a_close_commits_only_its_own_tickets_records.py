"""Proof for ticket d3b8cdf81a41 — a close or prove commits only its own ticket's commons records.

Measured 2026-11-19: close.sh and prove.sh staged the commons with ``git add -A tickets/ certificates/
questions/ outline_checks/ [berths/] .artifact-journal.jsonl``, so 17 commits since 2026-10-15 under a
close/prove subject carried another ticket's records (aa7d25c1: dd0f3e0e7225's close committed only
4de7baf7e255's state). Each tooth builds a scratch git commons dirty with own and foreign records in all
five dirs, then runs the selector or the script's own commons staging line as written.

    python3 cairn/devices/cc/proofs/test_a_close_commits_only_its_own_tickets_records.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
HOUSE = HERE.parents[3]
_BASH = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"  # ticket f2a3b90c2931

PROVES = {"d3b8cdf81a41": {
    "1": "test_the_selector_names_every_own_record_and_no_foreign_one",
    "2": "test_close_commits_only_its_own_records",
    "3": "test_prove_commits_only_its_own_records",
}}

OWN, FOREIGN = "aaaaaaaaaaaa", "bbbbbbbbbbbb"
_NAME = {OWN: "c0ffee", FOREIGN: "decade"}  # the bound records' names say nothing of their ticket
JOURNAL = ".artifact-journal.jsonl"


def _records(tid: str) -> dict[str, str]:
    bound = json.dumps({"ticket": tid, "body": "x"})
    return {
        f"tickets/{tid}-a-title.json": "{}",
        f"tickets/{tid}-a-title.state.json": "{}",
        f"tickets/{tid}-a-title.log.jsonl": "{}\n",
        f"certificates/{tid}-PROVED-20261119T000000Z-0000.cert.json": "{}",
        f"outline_checks/{tid}-20261119T000000.json": "{}",
        # bound by their "ticket" field only, never by name, as the real ones are
        f"questions/open-{_NAME[tid]}000000.json": bound,
        f"berths/chart/verdict-20261119T000000-{_NAME[tid]}000000.json": bound,
    }


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=proof", "-c", "user.email=proof@example.invalid", *args],
                       cwd=repo, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"git {args}: {r.stderr}"
    return r.stdout


def _commons(tmp: Path) -> tuple[Path, set[str]]:
    """A scratch commons: own and foreign records committed, then all modified, plus new untracked ones.
    Returns the repo and the dirty paths that are OWN's (the journal among them)."""
    repo = tmp / "CairnCommons"
    repo.mkdir()
    _git(repo, "init", "-q")
    old = {**_records(OWN), **_records(FOREIGN), JOURNAL: "line 1\n"}
    for p, body in old.items():
        (repo / p).parent.mkdir(parents=True, exist_ok=True)
        (repo / p).write_text(body, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "seed")
    own = set(_records(OWN)) | {JOURNAL}
    for p in old:  # every record dirty
        with open(repo / p, "a", encoding="utf-8") as f:
            f.write("\n")
    for tid in (OWN, FOREIGN):  # and a new untracked record of each kind per ticket
        for p, body in _records(tid).items():
            q = repo / p.replace("20261119T000000", "20261119T111111").replace("a-title", "b-title") \
                         .replace("000000.json", "111111.json")
            q.write_text(body, encoding="utf-8")
            if tid == OWN:
                own.add(q.relative_to(repo).as_posix())
    return repo, own


def _dirty(repo: Path) -> set[str]:
    return {line[3:] for line in _git(repo, "status", "--porcelain", "-uall").splitlines()}


def _staging_line(script: Path) -> str:
    """The commit_all line that stages the commons ('(cd $CC ...'), continuation lines joined."""
    text = script.read_text(encoding="utf-8").replace("\\\n", " ")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("(cd $CC") and "git commit" in ln]
    assert len(lines) == 1, f"{script.name}: expected one commons staging line, found {lines}"
    return lines[0]


def _run_line(script: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        repo, own = _commons(Path(t))
        before = _dirty(repo)
        assert own <= before, f"own records not dirty: {sorted(own - before)}"
        assert before - own, "the scratch commons has no foreign dirt; the tooth would be vacuous"
        env = {**os.environ, "C": str(HOUSE), "CC": str(repo), "ID": OWN, "TR": "", "TRAILER": "",
               "GIT_AUTHOR_NAME": "proof", "GIT_AUTHOR_EMAIL": "proof@example.invalid",
               "GIT_COMMITTER_NAME": "proof", "GIT_COMMITTER_EMAIL": "proof@example.invalid"}
        r = subprocess.run([_BASH, "-c", _staging_line(script), "commit_all", "a step"], env=env,
                           capture_output=True, text=True, timeout=120)
        committed = set(_git(repo, "show", "--name-only", "--format=", "HEAD").split())
        assert committed == own, (f"{script.name} committed {sorted(committed - own)} that are not "
                                  f"{OWN}'s, and missed {sorted(own - committed)} (rc {r.returncode}: {r.stderr})")
        left = _dirty(repo)
        assert left == before - own, f"{script.name} left {sorted(left)}, expected the foreign dirt only"
        assert _git(repo, "log", "-1", "--format=%s").startswith(f"{OWN}: a step")


def test_the_selector_names_every_own_record_and_no_foreign_one():
    sel = SCRIPTS / "commons_paths.py"
    assert sel.is_file(), f"no selector at {sel}"
    with tempfile.TemporaryDirectory() as t:
        repo, own = _commons(Path(t))
        r = subprocess.run([sys.executable, str(sel), OWN], cwd=repo, capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stderr
        got = set(r.stdout.split())
        assert got == own, f"extra {sorted(got - own)}, missing {sorted(own - got)}"
    print("the selector names every own record and no foreign one")


def test_close_commits_only_its_own_records():
    _run_line(SCRIPTS / "close.sh")
    print("close.sh commits only its own ticket's records")


def test_prove_commits_only_its_own_records():
    _run_line(SCRIPTS / "prove.sh")
    print("prove.sh commits only its own ticket's records")


def main() -> int:
    bad = 0
    for t in (test_the_selector_names_every_own_record_and_no_foreign_one,
              test_close_commits_only_its_own_records, test_prove_commits_only_its_own_records):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            bad += 1
            print(f"  FAIL  {t.__name__}\n        {type(exc).__name__}: {str(exc)[:400]}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

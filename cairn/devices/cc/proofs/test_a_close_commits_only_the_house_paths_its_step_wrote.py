"""Proof for ticket 91908f3b3bb3 — a close or prove commits only the house paths its own step wrote.

Measured 2026-11-19: close.sh's commit_all ran 'git add -u' over the cairn house tree, so an uncommitted
proof edit rode into 38e3f8323 "39fdea889714: hollow sealed, verdict" and was pushed before BUILDME
refused; prove.sh's commit_all carried the same 'git add -u'. Each tooth builds a scratch git house and
a scratch commons holding the ticket's plan, dirties the house with an unrelated file, the ticket's own
proof source, a foreign ticket's seal and the ticket's own seals, then runs the script's house staging
line as written, inside a commit_all of its own.

    python3 cairn/devices/cc/proofs/test_a_close_commits_only_the_house_paths_its_step_wrote.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
_BASH = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"  # ticket f2a3b90c2931

PROVES = {"91908f3b3bb3": {
    "1": "test_close_leaves_dirt_it_did_not_write_uncommitted",
    "2": "test_prove_leaves_dirt_it_did_not_write_uncommitted",
    "3": "test_a_step_still_commits_its_own_seals",
}}

OWN, FOREIGN = "aaaaaaaaaaaa", "bbbbbbbbbbbb"
JOURNAL = ".artifact-journal.jsonl"
SELECTOR = "cairn/devices/cc/scripts/house_paths.py"
PROOF, NEW_PROOF = "comp/proofs/test_x.py", "comp/proofs/test_new.py"
SEAL, NEW_SEAL = "comp/validations/test_x.json", "comp/validations/test_new.json"
UNRELATED, FOREIGN_SEAL = "src/unrelated.py", "other/validations/test_y.json"
# the source an other hand is mid-way through, and another ticket's seal: never the step's to commit
NOT_THE_STEPS = {UNRELATED, PROOF, NEW_PROOF, FOREIGN_SEAL}
THE_STEPS = {SEAL, NEW_SEAL, JOURNAL}


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=proof", "-c", "user.email=proof@example.invalid", *args],
                       cwd=repo, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"git {args}: {r.stderr}"
    return r.stdout


def _write(root: Path, rel: str, body: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(body, encoding="utf-8")


def _world(tmp: Path) -> tuple[Path, Path]:
    commons = tmp / "CairnCommons"
    plan = {"id": OWN, "writes_to": [PROOF, SEAL],
            "decisions": [{"n": 1, "writes_to": [NEW_PROOF], "reads": []}],
            "bounds": {"in": [PROOF, SEAL, NEW_PROOF], "out": ["every other component"]}}
    _write(commons, f"tickets/{OWN}-a-title.json", json.dumps(plan))
    _write(commons, f"tickets/{OWN}-a-title.state.json", "{}")
    _write(commons, f"tickets/{FOREIGN}-b-title.json",
           json.dumps({"id": FOREIGN, "writes_to": [FOREIGN_SEAL], "bounds": {"in": [FOREIGN_SEAL]}}))
    house = tmp / "cairn"
    house.mkdir()
    _git(house, "init", "-q")
    for rel in (UNRELATED, PROOF, SEAL, FOREIGN_SEAL, JOURNAL):
        _write(house, rel, "seed\n")
    if (SCRIPTS / "house_paths.py").is_file():  # the selector the scripts call, at its house address
        _write(house, SELECTOR, (SCRIPTS / "house_paths.py").read_text(encoding="utf-8"))
    _git(house, "add", "-A")
    _git(house, "commit", "-qm", "seed")
    for rel in (UNRELATED, PROOF, SEAL, FOREIGN_SEAL, JOURNAL):
        with open(house / rel, "a", encoding="utf-8") as f:
            f.write("dirty\n")
    _write(house, NEW_PROOF, "new\n")
    _write(house, NEW_SEAL, "{}\n")
    return house, commons


def _dirty(repo: Path) -> set[str]:
    return {line[3:] for line in _git(repo, "status", "--porcelain", "-uall").splitlines()}


def _house_line(script: Path) -> str:
    """commit_all's one house staging line ('cd $C', not 'cd $CC'), continuation lines joined."""
    text = script.read_text(encoding="utf-8").replace("\\\n", " ")
    body = text.split("commit_all() {", 1)[1].split("\n}", 1)[0]
    lines = [ln.strip() for ln in body.splitlines()
             if re.search(r"cd \$C(?![A-Za-z_])", ln) and "git commit" in ln]
    assert len(lines) == 1, f"{script.name}: expected one house staging line, found {lines}"
    return lines[0]


def _run(script: Path) -> tuple[set[str], set[str]]:
    """Run the script's house staging line in a scratch world; return (committed, still dirty)."""
    with tempfile.TemporaryDirectory() as t:
        house, commons = _world(Path(t))
        before = _dirty(house)
        assert NOT_THE_STEPS | THE_STEPS <= before, f"the world is not dirty as built: {sorted(before)}"
        env = {**os.environ, "C": str(house), "CC": str(commons), "ID": OWN, "TR": "", "TRAILER": "",
               "GIT_AUTHOR_NAME": "proof", "GIT_AUTHOR_EMAIL": "proof@example.invalid",
               "GIT_COMMITTER_NAME": "proof", "GIT_COMMITTER_EMAIL": "proof@example.invalid"}
        prog = "commit_all() {\n  " + _house_line(script) + "\n}\ncommit_all \"a step\"\n"
        subprocess.run([_BASH, "-c", prog], env=env, capture_output=True, text=True, timeout=120)
        head = _git(house, "log", "-1", "--format=%s").strip()
        committed = set(_git(house, "show", "--name-only", "--format=", "HEAD").split()) if head != "seed" else set()
        if committed:
            assert head.startswith(f"{OWN}: a step"), f"{script.name} committed under {head!r}"
        return committed, _dirty(house)


def _leaves(script: Path) -> None:
    committed, left = _run(script)
    swept = committed & NOT_THE_STEPS
    assert not swept, f"{script.name} committed {sorted(swept)}, which its step did not write"
    assert NOT_THE_STEPS <= left, f"{script.name} left {sorted(left)}; expected {sorted(NOT_THE_STEPS)} still dirty"


def test_close_leaves_dirt_it_did_not_write_uncommitted():
    _leaves(SCRIPTS / "close.sh")
    print("close.sh leaves the unrelated file, the ticket's proof source and a foreign seal dirty")


def test_prove_leaves_dirt_it_did_not_write_uncommitted():
    _leaves(SCRIPTS / "prove.sh")
    print("prove.sh leaves the unrelated file, the ticket's proof source and a foreign seal dirty")


def test_a_step_still_commits_its_own_seals():
    for name in ("close.sh", "prove.sh"):
        committed, left = _run(SCRIPTS / name)
        assert committed == THE_STEPS, (f"{name} committed {sorted(committed)}; "
                                        f"expected exactly {sorted(THE_STEPS)}")
        assert not (left & THE_STEPS), f"{name} left its own {sorted(left & THE_STEPS)} dirty"
    print("close.sh and prove.sh commit the ticket's own seals (modified and new) and the journal")


def main() -> int:
    bad = 0
    for t in (test_close_leaves_dirt_it_did_not_write_uncommitted,
              test_prove_leaves_dirt_it_did_not_write_uncommitted, test_a_step_still_commits_its_own_seals):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            bad += 1
            print(f"  FAIL  {t.__name__}\n        {type(exc).__name__}: {str(exc)[:400]}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

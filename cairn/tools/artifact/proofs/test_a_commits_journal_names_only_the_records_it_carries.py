"""Proof for ticket 380b2d99901d: a commit's journal names only the records the commit carries.

Measured 2026-11-20 at commit 53c5fbc1c: the pre-commit reseal journaled five seals in the
working tree, hit ENOSPC, said "No seal was staged", and the commit still carried the five
journal lines, because ``check_staged`` ended by staging the WHOLE working journal. Any record
journaled and left unstaged had its line carried by the next path commit of anything else.

One tooth per clause, each in its own hermetic world (a scratch CairnCommons git repo, records
written through the real door, ``CAIRN_ARTIFACT_ROOTS`` pointing at it; the harness is the one in
test_a_commit_takes_only_the_paths_its_author_names.py):

1  record A journaled and left unstaged (one HEAD already journaled, one HEAD never saw), then
   ``git commit -- B`` of record B: the committed journal holds HEAD's line for the first A,
   no line for the second, and the working line for B;
2  the measured row: a pre-commit hook shaped like cairn/devices/tester/hooks/pre-commit (check,
   reseal ``|| true``, check), whose reseal step journals a seal stand-in and then raises
   OSError(ENOSPC), printing COULD NOT RUN. The crash is injected by a fake reseal written into
   the scratch hook, so cairn/devices/tester/reseal.py is not touched (decision D2). The commit
   lands, and every line of the committed journal names a sha_after its committed blob hashes to;
3  the working .artifact-journal.jsonl is byte-identical across tooth 1's commit: only the index
   blob is composed.

Run: bin/cairn test cairn/tools/artifact/proofs/test_a_commits_journal_names_only_the_records_it_carries.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"380b2d99901d": {
    "1": "test_a_path_commit_carries_only_its_own_journal_lines",
    "2": "test_a_reseal_crashed_on_space_leaves_every_committed_line_true",
    "3": "test_the_working_journal_is_untouched_by_the_check"}}

JOURNAL = ".artifact-journal.jsonl"


def _run(args, cwd: Path, env: dict, stdin: str | None = None) -> subprocess.CompletedProcess:
    r = subprocess.run(args, cwd=str(cwd), env=env, capture_output=True,
                       input=None if stdin is None else stdin.encode("utf-8"))
    return subprocess.CompletedProcess(r.args, r.returncode,
                                       r.stdout.decode("utf-8", "replace").replace("\r\n", "\n"),
                                       r.stderr.decode("utf-8", "replace").replace("\r\n", "\n"))


def _out(root: Path, env: dict, *args: str) -> str:
    r = _run(["git", "-C", str(root), *args], root, env)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def _door_write(root: Path, env: dict, rel: str, doc: dict) -> None:
    r = _run([sys.executable, "-m", "cairn.tools.artifact", "write", str(root / rel), "--verb", "cast",
              "--why", "proof fixture", "--stdin"], REPO, env, stdin=json.dumps(doc, indent=2) + "\n")
    if r.returncode:
        raise RuntimeError(f"door write {rel}: {r.stderr.strip()[-300:]}")


def _world(label: str) -> tuple[Path, dict]:
    from cairn.tools.scratch.scratch import home_env, scratch_dir
    tmp = Path(scratch_dir(f"testing-380b2d99901d-{label}-"))
    root = tmp / "CairnCommons"
    (root / "ideas").mkdir(parents=True)
    env = {k: v for k, v in home_env(tmp).items() if not k.startswith("GIT_")}
    env.update({"PYTHONPATH": str(REPO), "CAIRN_REPO": str(REPO),
                "CAIRN_ARTIFACT_ROOTS": json.dumps({"CairnCommons": str(root), "parked": str(tmp / "parked")}),
                "GIT_CONFIG_NOSYSTEM": "1"})
    _out(root, env, "init", "-q")
    for k, v in (("user.email", "proof@cairn"), ("user.name", "proof"), ("commit.gpgsign", "false")):
        _out(root, env, "config", k, v)
    (root / "a.txt").write_text("a0\n")
    _door_write(root, env, "ideas/first.json", {"id": "first", "v": 0})
    _out(root, env, "add", "--", "a.txt", "ideas/first.json", JOURNAL)
    _out(root, env, "commit", "-q", "--no-verify", "-m", "fixture")
    r = _run([sys.executable, "-m", "cairn.tools.artifact", "install-hook", "CairnCommons"], REPO, env)
    if r.returncode or not (root / ".git" / "hooks" / "pre-commit").exists():
        raise RuntimeError(f"install-hook: {r.stdout.strip()} {r.stderr.strip()[-300:]}")
    return root, env


def _lines(blob: str) -> dict[str, dict]:
    return {e["path"]: e for e in (json.loads(x) for x in blob.splitlines() if x.strip())}


def _committed(root: Path, env: dict) -> dict[str, dict]:
    return _lines(_out(root, env, "show", f"HEAD:{JOURNAL}"))


def test_a_path_commit_carries_only_its_own_journal_lines():
    root, env = _world("c1")
    head_first = _committed(root, env)["ideas/first.json"]
    _door_write(root, env, "ideas/first.json", {"id": "first", "v": 1})   # A, HEAD journaled it
    _door_write(root, env, "ideas/fresh.json", {"id": "fresh"})           # A', HEAD never saw it
    _door_write(root, env, "ideas/second.json", {"id": "second"})         # B, the commit's own
    _out(root, env, "add", "--", "ideas/second.json")
    work = _lines((root / JOURNAL).read_text(encoding="utf-8"))
    r = _run(["git", "-C", str(root), "commit", "-q", "-m", "only B", "--", "ideas/second.json"], root, env)
    assert r.returncode == 0, f"the path commit was refused: {r.stderr[-600:]}"
    got = _committed(root, env)
    assert got.get("ideas/second.json") == work["ideas/second.json"], \
        f"B's committed line is not its working line: {got.get('ideas/second.json')}"
    assert got.get("ideas/first.json") == head_first, \
        (f"A's committed line is not HEAD's: committed sha_after {got.get('ideas/first.json', {}).get('sha_after', '')[:12]}, "
         f"HEAD's {head_first['sha_after'][:12]}, working {work['ideas/first.json']['sha_after'][:12]}")
    assert "ideas/fresh.json" not in got, "a record the commit does not carry, never in HEAD's journal, rode the commit"
    tree = _out(root, env, "ls-tree", "-r", "--name-only", "HEAD").split()
    assert sorted(tree) == sorted(["a.txt", "ideas/first.json", "ideas/second.json", JOURNAL]), tree


# The reseal step of cairn/devices/tester/hooks/pre-commit, with the crash the measured row hit:
# a seal journaled through the door in the working tree, then ENOSPC, caught, said, exit 0.
_FAKE_RESEAL = r'''
import errno, json, os, subprocess, sys
root = os.environ["PROOF_ROOT"]
r = subprocess.run([sys.executable, "-m", "cairn.tools.artifact", "write", root + "/ideas/seal.json",
                    "--verb", "cast", "--why", "proof fixture: a seal the reseal wrote", "--stdin"],
                   input=(json.dumps({"seal": "stand-in"}, indent=2) + "\n").encode(), capture_output=True)
if r.returncode:
    sys.exit("fake reseal could not write its seal: " + r.stderr.decode()[-300:])
try:
    raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))
except OSError as exc:
    print(f"reseal: COULD NOT RUN ({exc}). No seal was staged; the commit is not blocked")
'''


def test_a_reseal_crashed_on_space_leaves_every_committed_line_true():
    root, env = _world("c2")
    hooks = root / ".git" / "hooks"
    (hooks / "fake_reseal.py").write_text(_FAKE_RESEAL)
    check = f'PYTHONPATH="{REPO}" "{sys.executable}" -m cairn.tools.artifact check "$PWD" || exit 2'
    (hooks / "pre-commit").write_text(
        "#!/usr/bin/env bash\nset -uo pipefail\ncd \"$(git rev-parse --show-toplevel)\" || exit 0\n"
        f"{check}\n"
        f'PYTHONPATH="{REPO}" "{sys.executable}" "{hooks / "fake_reseal.py"}" || true\n'
        f"{check}\nexit 0\n")
    os.chmod(hooks / "pre-commit", 0o755)
    (root / "a.txt").write_text("a1\n")    # the source change, as server.py was at 53c5fbc1c
    env = {**env, "PROOF_ROOT": str(root)}
    r = _run(["git", "-C", str(root), "commit", "-q", "-m", "source only", "--", "a.txt"], root, env)
    out = r.stdout + r.stderr
    assert r.returncode == 0, f"the commit did not land: {out[-600:]}"
    assert "COULD NOT RUN" in out, f"the reseal's crash was not said: {out[-600:]}"
    assert "ideas/seal.json" in _lines((root / JOURNAL).read_text(encoding="utf-8")), \
        "the fake reseal did not journal its seal, so this tooth measures nothing"
    tree = set(_out(root, env, "ls-tree", "-r", "--name-only", "HEAD").split())
    false = []
    for path, e in _committed(root, env).items():
        if e.get("sha_after") == "absent":
            if path in tree:
                false.append(f"{path}: line says absent, the commit holds it")
            continue
        if path not in tree:
            false.append(f"{path}: line names sha_after {e.get('sha_after', '')[:12]}, the commit holds no such file")
            continue
        blob = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{path}"], capture_output=True,
                              env=env, check=True).stdout
        if hashlib.sha256(blob).hexdigest() != e.get("sha_after"):
            false.append(f"{path}: line names {e.get('sha_after', '')[:12]}, the committed blob is another")
    assert not false, f"the committed journal says what the commit does not hold: {false}"


def test_the_working_journal_is_untouched_by_the_check():
    root, env = _world("c3")
    _door_write(root, env, "ideas/first.json", {"id": "first", "v": 1})
    _door_write(root, env, "ideas/second.json", {"id": "second"})
    _out(root, env, "add", "--", "ideas/second.json")
    before = (root / JOURNAL).read_bytes()
    r = _run(["git", "-C", str(root), "commit", "-q", "-m", "only B", "--", "ideas/second.json"], root, env)
    assert r.returncode == 0, f"the path commit was refused: {r.stderr[-600:]}"
    after = (root / JOURNAL).read_bytes()
    assert after == before, (f"the check rewrote the working journal: {len(before)} -> {len(after)} bytes, "
                             f"sha {hashlib.sha256(before).hexdigest()[:12]} -> {hashlib.sha256(after).hexdigest()[:12]}")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

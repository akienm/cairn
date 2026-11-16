"""Proof for ticket f09cd0588ceb: a merge that changes a lab source recompiles the lab.

Measured 2026-11-16: 9555's merge changed bin's charter and the lab copy stayed stale, so
test_compiler's test_verify_on_the_real_repo went red with nothing wrong in the code. The
house repos had no post-merge hook. This proves the tracked hook beside the compiler and the
install mode of recompile_gate.sh that lays it, over scratch git repos only.

Teeth a hollow build could not pass:

  1. A merge into cairn that changes a beside-code charter, and a merge into CairnCommons that
     changes an intentions-not-beside-code entry, each leave the lab copy byte-equal to the
     merged source. With no hook, or a hook that pokes nothing, the copy stays stale.
  2. A merge that changes no lab source leaves every lab file's bytes and mtime untouched. A
     hook that recompiles on every merge rewrites the copies and trips this.
  3. ``recompile_gate.sh install <repo>`` lays an executable post-merge in the repo's hooks
     dir, a second install leaves it byte-identical, and the gate with no args still compiles.

    PYTHONPATH=. python3 cairn/tools/intentions_model_compiler/proofs/test_a_merge_recompiles_the_lab.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

_GATE = Path(__file__).resolve().parents[1] / "recompile_gate.sh"
_CHARTER = "intention" + "+why.json"
_BASH = shutil.which("bash") or "bash"

PROVES = {"f09cd0588ceb": {
    "1": "test_a_merge_that_changes_a_lab_source_recompiles_the_lab",
    "2": "test_a_merge_that_changes_no_lab_source_leaves_the_lab_alone",
    "3": "test_install_lays_the_hook_once_and_the_gate_still_compiles",
}}


def _env(d: str) -> dict:
    commons, code = os.path.join(d, "CairnCommons"), os.path.join(d, "cairn")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"CAIRN_LB_TRACE_ROOT": str(scratch_dir("mrl-proof-traces-")),
                "CAIRN_COMMONS_ROOT": commons, "CAIRN_CODE_ROOT": code,
                "CAIRN_LAB_OUT": os.path.join(commons, "intentions-congruency-lab"),
                "CAIRN_LOG_DIR": os.path.join(d, "logs"),
                "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull})
    return env


def _git(repo: str, env: dict, *args: str) -> str:
    r = subprocess.run(["git", "-C", repo, "-c", "user.name=proof", "-c", "user.email=proof@local",
                        "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *args],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, f"git {' '.join(args)} failed: {r.stderr!r}"
    return r.stdout


def _write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _gate(env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([_BASH, _GATE.as_posix(), *args], capture_output=True, text=True, env=env)


def _pair(d: str) -> dict:
    """Two scratch repos shaped like the house pair, each committed, the hook installed in both."""
    env = _env(d)
    commons, code = env["CAIRN_COMMONS_ROOT"], env["CAIRN_CODE_ROOT"]
    _write(os.path.join(commons, "intentions-not-beside-code", "telos.md"), "the frame")
    _write(os.path.join(commons, "intentions-congruency-lab", "_charter.md"), "the store's own")
    _write(os.path.join(code, "cairn", "tools", "base", _CHARTER), json.dumps({"what": "substrate"}))
    _write(os.path.join(code, "README.md"), "readme")
    for repo in (commons, code):
        _git(repo, env, "init", "-q")
        _git(repo, env, "add", "-A")
        _git(repo, env, "commit", "-q", "-m", "base")
        r = _gate(env, "install", repo)
        assert r.returncode == 0, f"install into {repo} failed: {r.stderr!r}"
    return env


def _merge_a_branch(repo: str, env: dict, rel: str, text: str) -> None:
    """Change ``rel`` on a side branch, then land it on main with a --no-ff merge, as a land does."""
    _git(repo, env, "checkout", "-q", "-b", "side")
    _write(os.path.join(repo, rel), text)
    _git(repo, env, "add", "--", rel)
    _git(repo, env, "commit", "-q", "-m", f"change {rel}")
    _git(repo, env, "checkout", "-q", "main")
    _git(repo, env, "merge", "-q", "--no-ff", "side", "-m", "land side")
    _git(repo, env, "branch", "-q", "-D", "side")


def _read(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def test_a_merge_that_changes_a_lab_source_recompiles_the_lab():
    with tempfile.TemporaryDirectory() as d:
        env = _pair(d)
        code, commons, lab = env["CAIRN_CODE_ROOT"], env["CAIRN_COMMONS_ROOT"], env["CAIRN_LAB_OUT"]
        rel = os.path.join("cairn", "tools", "base", _CHARTER)
        _merge_a_branch(code, env, rel, json.dumps({"what": "substrate, changed by the merge"}))
        copy = os.path.join(lab, "cairn-tools-base--" + _CHARTER)
        assert os.path.exists(copy), "a merge into cairn that changed a charter compiled no lab copy"
        assert _read(copy) == _read(os.path.join(code, rel)), \
            "the lab copy is not byte-equal to the charter the merge landed"
        _merge_a_branch(commons, env, os.path.join("intentions-not-beside-code", "telos.md"),
                        "the frame, changed by the merge")
        assert _read(os.path.join(lab, "telos.md")) == b"the frame, changed by the merge", \
            "a merge into CairnCommons that changed an intentions-not-beside-code entry left the lab stale"


def test_a_merge_that_changes_no_lab_source_leaves_the_lab_alone():
    with tempfile.TemporaryDirectory() as d:
        env = _pair(d)
        lab, code = env["CAIRN_LAB_OUT"], env["CAIRN_CODE_ROOT"]
        hook = Path(_git(code, env, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()) \
            / "hooks" / "post-merge"
        assert hook.is_file(), "no post-merge is installed, so 'left alone' would prove nothing"
        r = _gate(env)
        assert r.returncode == 0, r.stderr
        before = {n: (_read(os.path.join(lab, n)), os.stat(os.path.join(lab, n)).st_mtime_ns)
                  for n in sorted(os.listdir(lab))}
        assert "telos.md" in before, f"the seeded lab holds no copies: {sorted(before)}"
        _merge_a_branch(env["CAIRN_CODE_ROOT"], env, "README.md", "readme, changed")
        after = {n: (_read(os.path.join(lab, n)), os.stat(os.path.join(lab, n)).st_mtime_ns)
                 for n in sorted(os.listdir(lab))}
        assert after == before, "a merge that changed no lab source rewrote the lab"


def test_install_lays_the_hook_once_and_the_gate_still_compiles():
    with tempfile.TemporaryDirectory() as d:
        env = _pair(d)
        code = env["CAIRN_CODE_ROOT"]
        hook = Path(_git(code, env, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()) \
            / "hooks" / "post-merge"
        assert hook.is_file() and os.access(hook, os.X_OK), f"no executable post-merge at {hook}"
        first = hook.read_bytes()
        r = _gate(env, "install", code)
        assert r.returncode == 0, r.stderr
        assert hook.read_bytes() == first, "a second install changed the hook"
        lab = env["CAIRN_LAB_OUT"]
        r = _gate(env)
        assert r.returncode == 0, r.stderr
        got = {n for n in os.listdir(lab) if not n.startswith("_")}
        assert got == {"telos.md", "cairn-tools-base--" + _CHARTER}, \
            f"the gate with no args no longer compiles both trees: {got}"


TEETH = [
    test_a_merge_that_changes_a_lab_source_recompiles_the_lab,
    test_a_merge_that_changes_no_lab_source_leaves_the_lab_alone,
    test_install_lays_the_hook_once_and_the_gate_still_compiles,
]


def _main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"  RED  {t.__name__}: {exc}")
    print(f"{'GREEN' if not failed else 'RED'} - {len(TEETH) - failed}/{len(TEETH)} teeth")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

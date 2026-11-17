"""Proof for ticket 3f2692580b2f: the lab checks out LF on every box.

Measured 2026-11-16 on yoga (2dda7060d84e's live fire): with core.autocrlf=true, the recompile
gate writes the lab as LF over a CRLF checkout. That leaves 98 of 131 lab files stat-dirty with
an empty diff, and every drain check and every dirty=0 gate on a Windows box then reads dirt
that is not real. CairnCommons/.gitattributes now pins the lab to LF.

1. clause_1_the_commons_pins_the_lab_lf: git check-attr on the commons reports text set and
   eol lf for a path under intentions-congruency-lab/;
2. clause_2_a_recompile_under_autocrlf_reads_clean: in a scratch repo with core.autocrlf=true
   and the commons' .gitattributes copied in, a lab file is committed, checked out and then
   rewritten LF (as the compiler writes it), and git status --porcelain is empty;
3. clause_3_the_journal_merge_driver_stands: .artifact-journal.jsonl still reads
   merge=cairn-journal (ticket b7d2e05a1c93).

git runs with GIT_CONFIG_NOSYSTEM=1 and a scratch HOME, so the box's own git config cannot
steer the result. This runs on Linux as well, because git converts CRLF there too when
core.autocrlf=true.

Run bare:  PYTHONPATH=. python3 cairn/tools/intentions_model_compiler/proofs/test_the_lab_checks_out_lf_under_autocrlf.py
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

PROVES = {
    "3f2692580b2f": {
        "1": "clause_1_the_commons_pins_the_lab_lf",
        "2": "clause_2_a_recompile_under_autocrlf_reads_clean",
        "3": "clause_3_the_journal_merge_driver_stands",
    },
}

FAILURES: list[str] = []
LAB_FILE = "intentions-congruency-lab/testing-3f26-fixture.json"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:600]}")
    if not ok:
        FAILURES.append(name)


def _commons() -> Path:
    """The commons beside this checkout, else the home one (a hollow worktree has none beside it)."""
    try:
        from cairn.tools.artifact import artifact as A
        c = Path(A.roots()["CairnCommons"])
        if (c / ".gitattributes").is_file():
            return c
    except Exception:  # noqa: BLE001 — fall through to the home commons
        pass
    return Path.home() / "dev" / "src" / "CairnCommons"


def _git(env: dict, cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), env=env, capture_output=True, text=True)


def _env(home: Path) -> dict:
    env = dict(os.environ)
    env.update({"HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
                "XDG_CONFIG_HOME": str(home / ".config")})
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def tooth_1(env: dict, commons: Path) -> None:
    name = PROVES["3f2692580b2f"]["1"]
    try:
        r = _git(env, commons, "check-attr", "text", "eol", "--", LAB_FILE)
        out = r.stdout
        check(name, r.returncode == 0 and f"{LAB_FILE}: text: set" in out
              and f"{LAB_FILE}: eol: lf" in out, f"commons={commons} out={out!r} err={r.stderr!r}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(env: dict, commons: Path, tmp: Path) -> None:
    name = PROVES["3f2692580b2f"]["2"]
    try:
        repo = tmp / "repo"
        repo.mkdir()
        steps = [_git(env, repo, "init", "-q"),
                 _git(env, repo, "config", "core.autocrlf", "true"),
                 _git(env, repo, "config", "user.name", "testing-3f26"),
                 _git(env, repo, "config", "user.email", "testing-3f26@example.invalid")]
        shutil.copyfile(commons / ".gitattributes", repo / ".gitattributes")
        lab = repo / LAB_FILE
        lab.parent.mkdir(parents=True)
        body = b'{\n "testing": "3f2692580b2f"\n}\n'
        lab.write_bytes(body)
        steps += [_git(env, repo, "add", "--", ".gitattributes", LAB_FILE),
                  _git(env, repo, "commit", "-q", "-m", "testing-3f26 fixture")]
        lab.unlink()
        steps.append(_git(env, repo, "checkout", "-q", "--", LAB_FILE))
        crlf_on_checkout = b"\r\n" in lab.read_bytes()
        lab.write_bytes(body)  # the compiler writes LF on every box
        os.utime(lab)
        status = _git(env, repo, "status", "--porcelain")
        bad = [s for s in steps if s.returncode != 0]
        check(name, not bad and status.returncode == 0 and status.stdout.strip() == "",
              f"crlf_on_checkout={crlf_on_checkout} status={status.stdout!r} "
              f"failed_steps={[(s.args, s.stderr) for s in bad]}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(env: dict, commons: Path) -> None:
    name = PROVES["3f2692580b2f"]["3"]
    try:
        r = _git(env, commons, "check-attr", "merge", "--", ".artifact-journal.jsonl")
        check(name, ".artifact-journal.jsonl: merge: cairn-journal" in r.stdout,
              f"out={r.stdout!r} err={r.stderr!r}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-3f2692580b2f-lab-lf-")
    home = tmp / "home"
    home.mkdir()
    env = _env(home)
    commons = _commons()
    tooth_1(env, commons)
    tooth_2(env, commons, tmp)
    tooth_3(env, commons)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

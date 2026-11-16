#!/usr/bin/env python3
"""Proof that a charter lands in cairn only after its lab twin lands in the commons (ticket 39be1c54f091).

WHAT IT PROVES: the commit door refuses a cairn commit, or a land through pre-merge-commit
(ticket db250e9bf3f9), that stages an ``intention+why.json`` unless the commons beside it holds
the same bytes at its HEAD in ``intentions-congruency-lab/``, under the compiler's name for it;
a deleted charter needs its copy gone. Only main is judged: the same change on a builder's
branch or a detached HEAD commits (teeth 7 and 8). The refusal says ``land the commons lab copy <name>
first``. Measured 2026-11-16: 77 of 304 charter writes since 10-16 left the lab stale.

HOW: a scratch world holds ``cairn/`` and ``CairnCommons/`` side by side, each a git repo. The
cairn repo carries the real hooks (installed with the real ``install_hook``), the real
``lab_twin.py`` and the real compiler module, and A1's stub artifact and reseal doors, which
pass. The commits and merges are real git.

    python3 cairn/devices/tester/proofs/test_a_charter_lands_after_its_lab_twin.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

TID = "39be1c54f091"
PROVES = {TID: {
    "1": "test_a_charter_with_no_twin_is_refused",
    "2": "test_an_uncommitted_or_different_twin_is_refused",
    "3": "test_a_charter_with_its_twin_at_commons_head_lands",
    "4": "test_a_land_of_a_charter_with_no_twin_is_refused",
    "5": "test_a_deleted_charter_waits_for_its_copy_to_go",
    "6": "test_a_charter_under_proofs_needs_no_twin",
    "7": "test_a_branch_commit_needs_no_twin",
    "8": "test_a_detached_commit_needs_no_twin",
}}

FAILURES: list[str] = []
LAB = "intentions-congruency-lab"
CHARTER = "cairn/devices/widget/intention+why.json"
NAME = "cairn-devices-widget--intention+why.json"

_STUB_ARTIFACT = 'print("artifact check: every staged record is journaled")\n'

_ENV = {"GIT_AUTHOR_NAME": "proof", "GIT_AUTHOR_EMAIL": "proof@scratch",
        "GIT_COMMITTER_NAME": "proof", "GIT_COMMITTER_EMAIL": "proof@scratch",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0"}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _git(repo: Path, *args: str, ok: bool = True) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_INDEX_FILE", "GIT_DIR")}
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                       env={**env, **_ENV})
    if ok and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p


def _world() -> tuple[Path, Path]:
    root = scratch_dir(f"testing-{TID}-lab-twin-")
    cairn, commons = root / "cairn", root / "CairnCommons"
    for repo in (cairn, commons):
        repo.mkdir()
        _git(repo, "init", "-q", "-b", "main")
    files = {"cairn/__init__.py": "", "cairn/devices/__init__.py": "",
             "cairn/devices/tester/__init__.py": "", "cairn/tools/__init__.py": "",
             "cairn/tools/intentions_model_compiler/__init__.py": "",
             "cairn/tools/artifact/artifact.py": "",
             "cairn/tools/artifact/__init__.py": "",
             "cairn/tools/artifact/__main__.py": _STUB_ARTIFACT,
             "cairn/devices/tester/reseal.py": "",
             "cairn/devices/tester/cli.py": ""}
    for rel, body in files.items():
        (cairn / rel).parent.mkdir(parents=True, exist_ok=True)
        (cairn / rel).write_text(body, encoding="utf-8")
    for rel in ("cairn/devices/tester/lab_twin.py",
                "cairn/tools/intentions_model_compiler/compiler.py"):
        if (_REPO_ROOT / rel).exists():     # absent before the build: the door then has no tooth
            (cairn / rel).write_bytes((_REPO_ROOT / rel).read_bytes())
    _git(cairn, "add", "-A")
    _git(cairn, "commit", "-q", "--no-verify", "-m", "the doors")
    (commons / LAB).mkdir()
    (commons / LAB / "_charter+why.json").write_text("{}\n", encoding="utf-8")
    _git(commons, "add", "-A")
    _git(commons, "commit", "-q", "-m", "the lab")
    from cairn.devices.tester import reseal
    reseal.install_hook(cairn)
    return cairn, commons


def _stage_charter(cairn: Path, body: str, rel: str = CHARTER) -> None:
    (cairn / rel).parent.mkdir(parents=True, exist_ok=True)
    (cairn / rel).write_text(body, encoding="utf-8")
    _git(cairn, "add", "--", rel)


def _commit(cairn: Path, msg: str) -> tuple[subprocess.CompletedProcess, bool]:
    before = _git(cairn, "rev-parse", "HEAD").stdout.strip()
    c = _git(cairn, "commit", "-q", "-m", msg, ok=False)
    return c, _git(cairn, "rev-parse", "HEAD").stdout.strip() != before


def _land_twin(commons: Path, body: str | None, msg: str) -> None:
    twin = commons / LAB / NAME
    if body is None:
        twin.unlink()
        _git(commons, "rm", "-q", "--cached", "--", f"{LAB}/{NAME}")
    else:
        twin.write_text(body, encoding="utf-8")
        _git(commons, "add", "--", f"{LAB}/{NAME}")
    _git(commons, "commit", "-q", "-m", msg)


def test_a_charter_with_no_twin_is_refused(cairn: Path, commons: Path) -> None:
    name = PROVES[TID]["1"]
    _stage_charter(cairn, '{"why": "one"}\n')
    c, moved = _commit(cairn, "a charter, no twin")
    want = f"land the commons lab copy {NAME} first"
    check(name, c.returncode != 0 and not moved and want in c.stderr,
          f"commit rc={c.returncode} HEAD moved={moved} names {want!r}={want in c.stderr}")


def test_an_uncommitted_or_different_twin_is_refused(cairn: Path, commons: Path) -> None:
    name = PROVES[TID]["2"]
    (commons / LAB / NAME).write_text('{"why": "one"}\n', encoding="utf-8")   # not committed
    c1, moved1 = _commit(cairn, "twin only in the commons working tree")
    _land_twin(commons, '{"why": "older"}\n', "a twin with other bytes")
    c2, moved2 = _commit(cairn, "twin differs")
    check(name, c1.returncode != 0 and not moved1 and c2.returncode != 0 and not moved2
          and "bytes: land the commons lab copy" in c2.stderr,
          f"uncommitted: rc={c1.returncode} moved={moved1}; different: rc={c2.returncode} "
          f"moved={moved2}")


def test_a_charter_with_its_twin_at_commons_head_lands(cairn: Path, commons: Path) -> None:
    name = PROVES[TID]["3"]
    _land_twin(commons, '{"why": "one"}\n', "the twin lands first")
    c, moved = _commit(cairn, "the charter lands after its twin")
    check(name, c.returncode == 0 and moved, f"commit rc={c.returncode} HEAD moved={moved} "
          f"stderr={c.stderr.strip()[-200:]!r}")


def test_a_land_of_a_charter_with_no_twin_is_refused(cairn: Path, commons: Path) -> None:
    name = PROVES[TID]["4"]
    _git(cairn, "checkout", "-q", "-b", "edit", "main")
    _stage_charter(cairn, '{"why": "two"}\n')
    _git(cairn, "commit", "-q", "--no-verify", "-m", "the branch edits the charter")
    _git(cairn, "checkout", "-q", "main")
    (cairn / "main-moves.txt").write_text("main moves", encoding="utf-8")
    _git(cairn, "add", "--", "main-moves.txt")
    _git(cairn, "commit", "-q", "--no-verify", "-m", "main past the fork")
    before = _git(cairn, "rev-parse", "HEAD").stdout.strip()
    m = _git(cairn, "merge", "--no-ff", "--no-edit", "edit", ok=False)
    moved = _git(cairn, "rev-parse", "HEAD").stdout.strip() != before
    _git(cairn, "merge", "--abort", ok=False)
    check(name, m.returncode != 0 and not moved
          and f"land the commons lab copy {NAME} first" in m.stderr,
          f"merge rc={m.returncode} HEAD moved={moved}")


def test_a_deleted_charter_waits_for_its_copy_to_go(cairn: Path, commons: Path) -> None:
    name = PROVES[TID]["5"]
    _git(cairn, "rm", "-q", "--", CHARTER)
    c1, moved1 = _commit(cairn, "delete the charter while its copy stands")
    _land_twin(commons, None, "the copy goes first")
    c2, moved2 = _commit(cairn, "delete the charter after its copy went")
    check(name, c1.returncode != 0 and not moved1 and f"{NAME}'s removal first" in c1.stderr
          and c2.returncode == 0 and moved2,
          f"while standing: rc={c1.returncode} moved={moved1}; after: rc={c2.returncode} "
          f"moved={moved2}")


def test_a_charter_under_proofs_needs_no_twin(cairn: Path, commons: Path) -> None:
    name = PROVES[TID]["6"]
    _stage_charter(cairn, "{}\n", "cairn/devices/widget/proofs/fixture/intention+why.json")
    c, moved = _commit(cairn, "a fixture charter")
    check(name, c.returncode == 0 and moved, f"commit rc={c.returncode} HEAD moved={moved}")


def test_a_branch_commit_needs_no_twin(cairn: Path, commons: Path) -> None:
    """The same change that reds on main (tooth 1) commits on a builder's branch: its twin can
    only land with the branch."""
    name = PROVES[TID]["7"]
    _git(cairn, "checkout", "-q", "-b", "builder", "main")
    _stage_charter(cairn, '{"why": "on a branch"}\n')
    c, moved = _commit(cairn, "a charter on a branch, no twin")
    _git(cairn, "checkout", "-q", "main")
    check(name, c.returncode == 0 and moved, f"branch commit rc={c.returncode} HEAD moved={moved} "
          f"stderr={c.stderr.strip()[-200:]!r}")


def test_a_detached_commit_needs_no_twin(cairn: Path, commons: Path) -> None:
    """A detached HEAD (how a hollow scratch worktree stands) is on no branch, so not on main."""
    name = PROVES[TID]["8"]
    _git(cairn, "checkout", "-q", "--detach", "main")
    _stage_charter(cairn, '{"why": "detached"}\n')
    c, moved = _commit(cairn, "a charter on a detached HEAD, no twin")
    _git(cairn, "checkout", "-q", "-f", "main")
    check(name, c.returncode == 0 and moved, f"detached commit rc={c.returncode} HEAD moved={moved} "
          f"stderr={c.stderr.strip()[-200:]!r}")


TEETH = (test_a_charter_with_no_twin_is_refused,
         test_an_uncommitted_or_different_twin_is_refused,
         test_a_charter_with_its_twin_at_commons_head_lands,
         test_a_land_of_a_charter_with_no_twin_is_refused,
         test_a_deleted_charter_waits_for_its_copy_to_go,
         test_a_charter_under_proofs_needs_no_twin,
         test_a_branch_commit_needs_no_twin,
         test_a_detached_commit_needs_no_twin)


def main() -> int:
    cairn, commons = _world()  # the teeth run in order over one world, each from the last state
    for tooth in TEETH:
        try:
            tooth(cairn, commons)
        except Exception as exc:  # noqa: BLE001
            check(tooth.__name__, False, f"the tooth could not run to the end: {exc!r}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

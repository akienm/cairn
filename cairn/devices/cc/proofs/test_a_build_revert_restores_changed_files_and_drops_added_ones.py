"""PROOF for ticket 3f515c7e1d31: the preflight revert restores changed build files and drops added ones.

Measured 2026-11-18 on ticket b7068b1ba431: preflight.sh reverted with one
`git checkout $PRE -- <every build file>`. One build file was new, so the checkout failed whole and
the fallback only deleted it; the changed file stayed at HEAD and the reverted run read green.

  1. over a build that modifies m and adds n, revert_build.sh <pre> m n leaves m at its pre-build bytes
  2. and leaves n absent
  3. a build that only modifies files is reverted to the pre-build bytes
  4. preflight.sh invokes revert_build.sh for its reverted run and runs no git checkout of its own

    bin/cairn test --seal cairn/devices/cc/proofs/test_a_build_revert_restores_changed_files_and_drops_added_ones.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"3f515c7e1d31": {
    "1": "test_a_changed_file_goes_back_to_its_pre_build_bytes",
    "2": "test_an_added_file_is_dropped",
    "3": "test_a_modify_only_build_is_reverted",
    "4": "test_preflight_reverts_through_revert_build_and_checks_out_nothing_itself",
}}

_BASH = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"  # ticket f2a3b90c2931
_SCRIPTS = ROOT / "cairn/devices/cc/scripts"
_REVERT = _SCRIPTS / "revert_build.sh"


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=proof", "-c", "user.email=proof@example.invalid",
                        "-c", "commit.gpgsign=false", *args],
                       cwd=repo, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"git {' '.join(args)}: {r.stderr}"
    return r.stdout.strip()


def _repo(build: dict[str, str]) -> tuple[Path, str]:
    """A scratch repo: m and k committed as 'old' (the pre-build commit), then `build` committed over it."""
    repo = Path(scratch_dir("testing-3f515c7e1d31-"))
    _git(repo, "init", "-q")
    (repo / "m").write_text("old m\n")
    (repo / "k").write_text("old k\n")
    _git(repo, "add", "m", "k")
    _git(repo, "commit", "-q", "-m", "pre-build")
    pre = _git(repo, "rev-parse", "HEAD")
    for name, text in build.items():
        (repo / name).write_text(text)
    _git(repo, "add", *build)
    _git(repo, "commit", "-q", "-m", "build")
    return repo, pre


def _revert(repo: Path, pre: str, *files: str) -> None:
    r = subprocess.run([_BASH, str(_REVERT), pre, *files], cwd=repo, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"revert_build.sh exited {r.returncode}: {r.stderr.strip() or r.stdout.strip()}"


def test_a_changed_file_goes_back_to_its_pre_build_bytes():
    repo, pre = _repo({"m": "new m\n", "n": "added n\n"})
    _revert(repo, pre, "m", "n")
    assert (repo / "m").read_text() == "old m\n", f"m reads {(repo / 'm').read_text()!r} after the revert"


def test_an_added_file_is_dropped():
    repo, pre = _repo({"m": "new m\n", "n": "added n\n"})
    _revert(repo, pre, "m", "n")
    assert not (repo / "n").exists(), "n, absent at the pre-build commit, is still on disk after the revert"


def test_a_modify_only_build_is_reverted():
    repo, pre = _repo({"m": "new m\n", "k": "new k\n"})
    _revert(repo, pre, "m", "k")
    got = {f: (repo / f).read_text() for f in ("m", "k")}
    assert got == {"m": "old m\n", "k": "old k\n"}, f"after the revert: {got}"


def test_preflight_reverts_through_revert_build_and_checks_out_nothing_itself():
    text = (_SCRIPTS / "preflight.sh").read_text()
    code = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    assert any("revert_build.sh" in ln for ln in code), "preflight.sh does not call revert_build.sh"
    own = [ln.strip() for ln in code if "git checkout" in ln]
    assert not own, f"preflight.sh still runs its own git checkout: {own}"


def main() -> int:
    fails = 0
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not fails else 'RED'} — {len(tests) - fails}/{len(tests)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

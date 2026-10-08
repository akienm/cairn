"""Proof for ticket 6e587f28ebbc — the voyage-craft note states the build commit and the predict
restore as measured.

Measured 2026-10-08 on 996668eceef1, the voyage that wrote the note: its build commit 087752e1
carried six resealed validations that the pre-commit hook staged (`cli --reseal --stage`), while
clause 1 said the build commit stages only writes_to files; and in the predict worktree
`git show 9edee02e:<charter> > <charter>` was refused by artifactgate, while clause 4 said to
restore exactly that way. `git checkout 9edee02e -- <dir>` ran. The note is standing input to
every rehearsal, so a false step there is paid for on every voyage.

  1. THE BUILD BULLET NAMES THE HOOK'S VALIDATIONS. Clause 1's build-commit bullet names the
     pre-commit hook and the validation records it stages, and no longer says the build commit
     stages only the writes_to files.
  2. THE PREDICT RESTORES WITHOUT A REDIRECT, AND IT RUNS. Clause 4 step 4's restore command
     carries no `>`, and its removal command is `git rm`. Run in a scratch git repo with A = the
     first commit, the restore brings back A's bytes of a path named intention+why.json, and the
     removal takes away a file new at the second commit.

    python3 cairn/machines/rehearsal/proofs/test_the_voyage_craft_states_what_was_measured.py   # exit 0 = green
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"6e587f28ebbc": {"1": "test_the_build_bullet_names_the_hooks_validations",
                           "2": "test_the_predict_restores_without_a_redirect_and_it_runs"}}

NOTE = Path(__file__).resolve().parents[1] / "voyage_craft.md"
CHARTER = "comp/intention+why.json"
NEW_FILE = "comp/new_in_build.md"

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  PASS  {name}")


def _clause(n: int) -> str:
    """The text of numbered clause n, up to the next top-level numbered clause."""
    text = NOTE.read_text(encoding="utf-8")
    m = re.search(rf"^{n}\. .*?(?=^{n + 1}\. |\Z)", text, re.S | re.M)
    assert m, f"voyage_craft.md has no clause {n}"
    return m.group(0)


def test_the_build_bullet_names_the_hooks_validations():
    lines = [ln for ln in _clause(1).splitlines() if ln.strip().startswith("- the build commit")]
    assert len(lines) == 1, f"clause 1 has {len(lines)} build-commit bullets, expected 1"
    bullet = lines[0]
    assert "stages only" not in bullet, (
        f"the build bullet still says the build commit stages only writes_to files — 087752e1 "
        f"carried six resealed validations: {bullet!r}")
    assert "pre-commit" in bullet and "validation" in bullet, (
        f"the build bullet does not name the pre-commit hook's validation records: {bullet!r}")


def _git(cwd: Path, *args: str) -> str:
    out = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd,
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, f"git {' '.join(args)} exited {out.returncode}: {out.stderr}"
    return out.stdout.strip()


def test_the_predict_restores_without_a_redirect_and_it_runs():
    step = re.search(r"^\s+4\. .*$", _clause(4), re.M)
    assert step, "clause 4 has no step 4"
    spans = re.findall(r"`([^`]+)`", step.group(0))
    restore = [s for s in spans if re.search(r"\bA\b", s) and "<path>" in s]
    removal = [s for s in spans if s.startswith("git rm") and "<path>" in s]
    assert len(restore) == 1, f"step 4 names {len(restore)} restore commands over A and <path>: {spans}"
    # the placeholder's own '>' is not a redirect; only what is left once it is lifted out counts
    assert ">" not in restore[0].replace("<path>", ""), (
        f"the restore redirects into the path, which artifactgate refuses when it is a charter: "
        f"{restore[0]!r}")
    assert len(removal) == 1, f"step 4 names {len(removal)} `git rm <path>` removal commands: {spans}"

    from cairn.tools.scratch.scratch import scratch_dir
    repo = Path(scratch_dir("testing-6e587f28ebbc-predict-restore-"))
    try:
        (repo / "comp").mkdir()
        _git(repo, "init", "-q")
        (repo / CHARTER).write_text('{"as": "proved"}\n', encoding="utf-8")
        _git(repo, "add", CHARTER)
        _git(repo, "commit", "-q", "-m", "A")
        a = _git(repo, "rev-parse", "HEAD")
        (repo / CHARTER).write_text('{"as": "built"}\n', encoding="utf-8")
        (repo / NEW_FILE).write_text("new in the build\n", encoding="utf-8")
        _git(repo, "add", CHARTER, NEW_FILE)
        _git(repo, "commit", "-q", "-m", "B")

        def run(cmd: str, path: str) -> None:
            cmd = re.sub(r"\bA\b", a, cmd).replace("<path>", path)
            out = subprocess.run(["bash", "-c", cmd], cwd=repo, capture_output=True, text=True,
                                 timeout=60)
            assert out.returncode == 0, f"{cmd!r} exited {out.returncode}: {out.stderr}"

        run(restore[0], CHARTER)
        got = (repo / CHARTER).read_text(encoding="utf-8")
        assert got == '{"as": "proved"}\n', f"the restore left {got!r}, not A's bytes"
        run(removal[0], NEW_FILE)
        assert not (repo / NEW_FILE).exists(), "the removal left the build-new file in place"
    finally:
        shutil.rmtree(repo, ignore_errors=True)


def _main() -> int:
    print(f"proof: the voyage-craft note states what was measured — note={NOTE}")
    _tooth("test_the_build_bullet_names_the_hooks_validations",
           test_the_build_bullet_names_the_hooks_validations)
    _tooth("test_the_predict_restores_without_a_redirect_and_it_runs",
           test_the_predict_restores_without_a_redirect_and_it_runs)
    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(_main())

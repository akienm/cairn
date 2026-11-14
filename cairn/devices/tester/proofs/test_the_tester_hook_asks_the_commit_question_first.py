#!/usr/bin/env python3
"""The tester's pre-commit hook asks the artifact door's commit question before its reseal ladder.

Moved here from cairn/tools/artifact/proofs/test_artifact_door.py (ticket 4d10cd50ef56):
the tooth reads cairn/devices/tester/hooks/pre-commit, and RULE 1 keeps a read of the
tester's code inside the tester's own proofs. The artifact door is reached only through
its published front door, ``python -m cairn.tools.artifact``.

The hook is installed into a scratch cairn clone. The reseal step is a stand-in that
prints a marker, so the ORDER is measured rather than assumed:

- a record of truth staged around the door is refused by the commit question, with the
  marker absent from the output (the reseal never ran);
- the same kind of record written THROUGH the door commits, and the marker is present
  (the question passed, then the reseal ran).

A hollow hook could not pass both: one that skips the question commits the sneak, and one
that blocks everything refuses the journaled commit.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
HOOK = REPO / "cairn" / "devices" / "tester" / "hooks" / "pre-commit"
# git hands a hook's stdout to its own stderr, so the marker is read from both streams
MARKER = "STAND-IN RESEAL LADDER RAN"

PROVES = {
    "4d10cd50ef56": {
        "1": "test_the_tester_hook_asks_the_commit_question_before_the_reseal_ladder",
        "2": "test_a_journaled_commit_passes_the_question_and_reaches_the_ladder",
        "3": "test_the_artifact_door_proof_reads_no_tester_path",
    },
    # moved with the tooth from test_artifact_door.py, keys kept
    "30531f6e1c5d": {
        "tester_hook": "test_the_tester_hook_asks_the_commit_question_before_the_reseal_ladder",
    },
    "2a208067d036": {
        "2": "test_both_hook_teeth_hold_a_journaled_commit_passes_and_the_tester_hook_asks_first",
    },
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _git(root: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          env=env, timeout=120)


def _scratch(tmp: Path) -> tuple[Path, dict]:
    commons, cairn = tmp / "CairnCommons", tmp / "cairn"
    for r in (commons, cairn):
        r.mkdir(parents=True)
        for args in (("init", "-q"), ("config", "user.email", "proof@cairn"),
                     ("config", "user.name", "proof"), ("config", "commit.gpgsign", "false"),
                     ("config", "core.autocrlf", "false")):
            _git(r, *args)
    hook = cairn / ".git" / "hooks" / "pre-commit"
    hook.write_bytes(HOOK.read_bytes())
    hook.chmod(0o755)
    # The scratch clone is a regular `cairn` package, so cwd (the hook's working dir) resolves
    # it first: the hook's guards find reseal.py and artifact.py; cairn.devices.tester.cli is
    # the stand-in marker; cairn.tools.artifact hands over to the real door from REPO.
    for rel in ("cairn/__init__.py", "cairn/devices/__init__.py", "cairn/devices/tester/__init__.py",
                "cairn/devices/tester/reseal.py", "cairn/tools/artifact/artifact.py"):
        (cairn / rel).parent.mkdir(parents=True, exist_ok=True)
        (cairn / rel).write_text("# stand-in; the real module is in REPO\n")
    (cairn / "cairn" / "devices" / "tester" / "cli.py").write_text(f"print({MARKER!r})\n")
    # the hook takes its interpreter from the repo's bootstrap, as on a live repo (a bare
    # python3 is not on every box: on Windows it is the venv's Scripts/python.exe)
    boot = cairn / "cairn" / "devices" / "recovery" / "bootstrap.sh"
    boot.parent.mkdir(parents=True)
    boot.write_bytes((REPO / "cairn" / "devices" / "recovery" / "bootstrap.sh").read_bytes())
    (cairn / "cairn" / "tools" / "artifact" / "__main__.py").write_text(
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(REPO)!r})\n"
        "for k in [k for k in sys.modules if k == 'cairn' or k.startswith('cairn.')]:\n"
        "    del sys.modules[k]\n"
        "runpy.run_module('cairn.tools.artifact', run_name='__main__', alter_sys=True)\n")
    (cairn / "cairn" / "tools" / "x").mkdir(parents=True)
    env = {**os.environ, "PYTHONPATH": str(REPO), "CAIRN_REPO": str(REPO),
           "CAIRN_ARTIFACT_ROOTS": json.dumps({"cairn": str(cairn), "CairnCommons": str(commons),
                                               "parked": str(tmp / "parked")})}
    # the stand-ins themselves are not records of truth; land them as the clone's first commit
    _git(cairn, "add", "-A")
    _git(cairn, "commit", "-qm", "scratch clone", "--no-verify", env=env)
    return cairn, env


def teeth(tmp: Path) -> None:
    print("THE TESTER'S HOOK — in a scratch cairn clone, the commit question runs first")
    cairn, env = _scratch(tmp)

    rel = "cairn/tools/x/state.json"
    (cairn / rel).write_text('{"hand": true}\n')
    _git(cairn, "add", "--", rel)
    c = _git(cairn, "commit", "-qm", "sneak a state", "--", rel, env=env)
    check("test_the_tester_hook_asks_the_commit_question_before_the_reseal_ladder",
          c.returncode != 0 and "around the artifact door" in c.stderr and MARKER not in c.stdout + c.stderr,
          f"rc={c.returncode} marker={MARKER in c.stdout + c.stderr} "
          f"{(c.stderr.strip().splitlines() or [''])[-1][:100]}")
    _git(cairn, "reset", "-q", "--", rel)
    (cairn / rel).unlink()

    src = tmp / "state-body.json"
    src.write_bytes((json.dumps({"through": "the door"}, indent=2) + "\n").encode())  # LF everywhere
    w = subprocess.run([sys.executable, "-m", "cairn.tools.artifact", "write", str(cairn / rel),
                        "--verb", "write", "--why", "proof: a journaled record", "--from", str(src)],
                       capture_output=True, text=True, cwd=REPO, env=env, timeout=120)
    _git(cairn, "add", "-A")
    staged = _git(cairn, "diff", "--cached", "--name-only").stdout.split()
    c = _git(cairn, "commit", "-qm", "a journaled state", "--", *staged, env=env)
    check("test_a_journaled_commit_passes_the_question_and_reaches_the_ladder",
          w.returncode == 0 and c.returncode == 0 and MARKER in c.stdout + c.stderr,
          f"write rc={w.returncode} {w.stderr.strip()[-120:]} commit rc={c.returncode} "
          f"marker={MARKER in c.stdout + c.stderr} {c.stderr.strip()[-160:]}")

    both = ("test_the_tester_hook_asks_the_commit_question_before_the_reseal_ladder",
            "test_a_journaled_commit_passes_the_question_and_reaches_the_ladder")
    check("test_both_hook_teeth_hold_a_journaled_commit_passes_and_the_tester_hook_asks_first",
          not any(n in FAILURES for n in both), f"{[n for n in both if n in FAILURES]}")


def tooth_no_reach() -> None:
    print("THE ARTIFACT DOOR'S PROOF — reads no tester path (RULE 1)")
    door_proof = REPO / "cairn" / "tools" / "artifact" / "proofs" / "test_artifact_door.py"
    text = door_proof.read_text(encoding="utf-8") if door_proof.exists() else ""
    reach = [n for n, line in enumerate(text.splitlines(), 1)
             if '"devices" / "tester"' in line or "devices/tester" in line]
    check("test_the_artifact_door_proof_reads_no_tester_path", bool(text) and not reach,
          f"lines {reach}" if reach else ("absent" if not text else ""))


def main() -> int:
    if not HOOK.exists():
        for keys in PROVES.values():
            for name in keys.values():
                check(name, False, "subject absent: cairn/devices/tester/hooks/pre-commit")
    else:
        try:
            with tempfile.TemporaryDirectory(prefix="cairn-tester-hook-proof-") as d:
                teeth(Path(d))
        except Exception as exc:  # noqa: BLE001 — a world that could not be built reds the teeth
            print(f"the teeth could not run to the end: {exc!r}")
            for name in PROVES["4d10cd50ef56"].values():
                if name not in FAILURES and not name.endswith("no_tester_path"):
                    check(name, False, f"aborted: {type(exc).__name__}")
        tooth_no_reach()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

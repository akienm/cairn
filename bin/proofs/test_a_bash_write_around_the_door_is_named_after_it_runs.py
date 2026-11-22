"""Proof for ticket 7989bb520e14: a Bash write around the artifact door is named right after it runs.

Measured 2026-11-18 (ticket b7068b1ba431): artifactgate's PreToolUse verdict reads only the command
text, so `python3 <script>` whose body writes a record is allowed, and the first thing to see the
write was the commit check. The PostToolUse pass asks the door, per root, which changed records
have working bytes the journal never saw.

1. a Bash command running a script file that writes a scratch-root record is allowed by
   PreToolUse and, after it runs, named by PostToolUse (exit 2, the path on stderr);
2. the same record written through artifact.write is not named, and a hand write after it is;
3. a changed file that is not a record is not named, while a record beside it is;
4. .claude/settings.json registers bin/cmd/artifactgate under PostToolUse with matcher Bash.

Every hook run is a subprocess fed the hook's stdin contract, pointed at two scratch git roots
by CAIRN_ARTIFACT_ROOTS (the door's subprocess seam). Nothing outside tmp_path is written.

    bin/cairn test bin/proofs/test_a_bash_write_around_the_door_is_named_after_it_runs.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "bin" / "cmd" / "artifactgate"

PROVES = {"7989bb520e14": {
    "1": "test_a_script_file_write_passes_before_and_is_named_after",
    "2": "test_a_door_write_is_not_named_and_a_hand_write_after_it_is",
    "3": "test_a_non_record_is_not_named_beside_a_record_that_is",
    "4": "test_the_gate_is_registered_after_bash",
}}

RECORD = "troubles/a-scratch-trouble.json"


def _body(n: int) -> str:
    """A canonical record body: the door refuses any other (f9ba6c89844d)."""
    return json.dumps({"x": n}, indent=2) + "\n"


def _roots(tmp: Path) -> dict:
    roots = {}
    for name in ("cairn", "CairnCommons"):
        r = tmp / name
        (r / "troubles").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(r)], check=True)
        roots[name] = str(r)
    return roots


# the host's bash: on Windows the one on PATH, never System32's WSL launcher (ticket 69075b0e8212)
BASH = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"


def _env(roots: dict) -> dict:
    env = dict(os.environ, CAIRN_ARTIFACT_ROOTS=json.dumps(roots), PYTHONPATH=str(REPO))
    return env


def _hook(event: str, command: str, roots: dict) -> subprocess.CompletedProcess:
    payload = {"hook_event_name": event, "tool_name": "Bash",
               "tool_input": {"command": command}, "cwd": str(REPO)}
    return subprocess.run([sys.executable, str(GATE)], input=json.dumps(payload), text=True,
                          capture_output=True, env=_env(roots), timeout=60)


def _run(command: str, roots: dict) -> None:
    subprocess.run([BASH, "-c", command], check=True, env=_env(roots), timeout=60)


def _script(tmp: Path, target: Path, body: str) -> str:
    s = tmp / "w.py"
    s.write_text("import pathlib\npathlib.Path(%r).write_text(%r)\n" % (str(target), body))
    return "%s %s" % (sys.executable, s)


def _door_write(target: Path, body: str, roots: dict) -> None:
    code = ("from cairn.tools.artifact import artifact as d; "
            "d.write(%r, %r, verb='cast', why='proof 7989bb520e14')" % (str(target), body))
    subprocess.run([sys.executable, "-c", code], check=True, env=_env(roots), cwd=str(REPO),
                   timeout=60)


def test_a_script_file_write_passes_before_and_is_named_after(tmp_path):
    roots = _roots(tmp_path)
    target = Path(roots["CairnCommons"]) / RECORD
    cmd = _script(tmp_path, target, _body(1))
    pre = _hook("PreToolUse", cmd, roots)
    assert pre.returncode == 0, pre.stderr
    _run(cmd, roots)
    post = _hook("PostToolUse", cmd, roots)
    assert post.returncode == 2, (post.returncode, post.stderr)
    assert str(target) in post.stderr, post.stderr


def test_a_door_write_is_not_named_and_a_hand_write_after_it_is(tmp_path):
    roots = _roots(tmp_path)
    target = Path(roots["CairnCommons"]) / RECORD
    _door_write(target, _body(1), roots)
    quiet = _hook("PostToolUse", "true", roots)
    assert quiet.returncode == 0, quiet.stderr
    _run(_script(tmp_path, target, _body(2)), roots)
    loud = _hook("PostToolUse", "true", roots)
    assert loud.returncode == 2 and str(target) in loud.stderr, (loud.returncode, loud.stderr)


def test_a_non_record_is_not_named_beside_a_record_that_is(tmp_path):
    roots = _roots(tmp_path)
    plain = Path(roots["cairn"]) / "notes.txt"
    target = Path(roots["CairnCommons"]) / RECORD
    plain.write_text("hello\n")
    _run(_script(tmp_path, target, _body(3)), roots)
    post = _hook("PostToolUse", "true", roots)
    assert post.returncode == 2, (post.returncode, post.stderr)
    assert str(target) in post.stderr and str(plain) not in post.stderr, post.stderr


def test_the_gate_is_registered_after_bash():
    settings = json.loads((REPO / ".claude" / "settings.json").read_text())
    after = settings.get("hooks", {}).get("PostToolUse", [])
    hit = [e for e in after if "Bash" in (e.get("matcher") or "").split("|")
           and any(h.get("command", "").endswith("bin/cmd/artifactgate") for h in e.get("hooks", []))]
    assert hit, after


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))

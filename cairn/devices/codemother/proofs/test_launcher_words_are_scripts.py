#!/usr/bin/env python3
"""Proof for ticket ed3d02b24675 — codemother's launcher words become scripts in its bin.

Measured 2026-11-05: cairn/devices/codemother/0/bin/codemother dispatched cross, watch, question,
seed and show in a case statement. Under 41a70e789682 a word with no script in the device's bin
goes onto the bus (outline 8.4.2), so those five would be stranded. One tooth per falsifier clause:

  1. each of cross, watch, question, seed, show is an executable in the class bin whose first
     comment line (after the shebang) is '# cairn codemother <word> — <what>';
  2. read-only invocations print byte-identical to the pre-build arms, and reach the class
     bin's own script: `cairn codemother show` and `show settings` match the shim the old arm
     called, and cross/watch/question with no argument print the old arms' usage lines. Each
     run goes through bin/cairn over a SCRATCH instance root that cairn_wire_instances lays
     fresh; bin/cairn's bash -x trace must exec <scratch>/codemother/0/bin/<word>, and that
     entry must resolve to the class bin's script;
  3. the launcher carries no case arm for any of the five words.

Scratch roots only: no live bus and no live store. Run serially.

    python3 cairn/devices/codemother/proofs/test_launcher_words_are_scripts.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
_BIN = _REPO / "cairn" / "devices" / "codemother" / "0" / "bin"
WORDS = ("cross", "watch", "question", "seed", "show")

PROVES = {"ed3d02b24675": {
    "1": "clause_1_each_word_is_a_named_executable_in_the_bin",
    "2": "clause_2_each_word_prints_as_before_through_its_own_script",
    "3": "clause_3_the_launcher_keeps_no_arm_for_the_five",
}}

# The no-argument usage lines of the old arms, copied from the launcher at HEAD 38293f63 (cross's since 0be964512fb0).
USAGE = {
    # Ticket 0be964512fb0 (outline 9.7): the ticket queues itself, so the mouth takes the ticket only.
    "cross": "usage: cairn codemother cross <ticket> [--timeout <s>]  "
             "(the gate derives the target and the proofs)\n",
    "watch": "usage: cairn codemother watch <area> [reason]\n",
    "question": "usage: cairn codemother question <question>\n",
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if detail:
        print(f"        {detail[:1500]}", flush=True)
    if not ok:
        FAILURES.append(name)


def _first_comment(p: Path) -> str:
    for line in p.read_text(encoding="utf-8").splitlines()[1:]:
        if line.startswith("#"):
            return line
    return ""


def clause_1_each_word_is_a_named_executable_in_the_bin() -> None:
    lacks = []
    for w in WORDS:
        p = _BIN / w
        if not (p.is_file() and os.access(p, os.X_OK)):
            lacks.append(f"{w}: not an executable in {_BIN}")
            continue
        c = _first_comment(p)
        if not re.fullmatch(rf"# cairn codemother {w} — \S.*", c):
            lacks.append(f"{w}: first comment line is {c!r}")
    check("clause_1_each_word_is_a_named_executable_in_the_bin", not lacks, "; ".join(lacks))


def _wire(root: Path) -> None:
    subprocess.run(["bash", "-c", f"source '{_REPO}/cairn/devices/recovery/bootstrap.sh' "
                    "&& cairn_wire_instances"],
                   env={**os.environ, "CAIRN_INSTANCE_ROOT": str(root)},
                   capture_output=True, text=True, timeout=120, check=False)


def _via_cairn(root: Path, argv: list[str]) -> subprocess.CompletedProcess:
    env = {**os.environ, "CAIRN_INSTANCE_ROOT": str(root), "PYTHONPATH": str(_REPO)}
    return subprocess.run(["bash", "-x", str(_REPO / "bin" / "cairn"), "codemother", *argv],
                          capture_output=True, text=True, env=env, cwd=str(_REPO), timeout=300)


def _shim(argv: list[str]) -> subprocess.CompletedProcess:
    """The body the old `show` arm ran, called directly: the before."""
    code = ("import sys; sys.path.insert(0, %r)\n"
            "from cairn.devices.codemother.shim import CodeMotherShim\n"
            "from cairn.tools.base.shim import cli_main\n"
            "sys.exit(cli_main(CodeMotherShim, sys.argv[1:]))") % str(_REPO)
    return subprocess.run([sys.executable, "-c", code, *argv], capture_output=True, text=True,
                          env={**os.environ, "PYTHONPATH": str(_REPO)}, cwd=str(_REPO), timeout=300)


def clause_2_each_word_prints_as_before_through_its_own_script() -> None:
    lacks = []
    with tempfile.TemporaryDirectory(prefix="ed3d-inst-") as d:
        root = Path(d)
        _wire(root)
        cases = [(["show"], "show", _shim(["show"])),
                 (["show", "settings"], "show", _shim(["show", "settings"]))]
        cases += [([w], w, None) for w in USAGE]
        for argv, word, before in cases:
            r = _via_cairn(root, argv)
            entry = root / "codemother" / "0" / "bin" / word
            execs = [l for l in r.stderr.splitlines() if l.startswith("+") and " exec " in f" {l.lstrip('+ ')}"]
            if not any(str(entry) in l for l in execs):
                lacks.append(f"{' '.join(argv)}: bin/cairn never execs {entry}: {execs[-2:]}")
            if entry.resolve() != (_BIN / word).resolve():
                lacks.append(f"{entry} resolves to {entry.resolve()}, not {_BIN / word}")
            want = USAGE[word] if before is None else before.stdout
            if r.stdout != want:
                lacks.append(f"{' '.join(argv)}: stdout {r.stdout[:200]!r} != before {want[:200]!r}")
            if before is not None and r.returncode != before.returncode:
                lacks.append(f"{' '.join(argv)}: rc {r.returncode} != before {before.returncode}")
            if before is None and r.returncode != 1:
                lacks.append(f"{word}: rc {r.returncode}, the old arm exited 1 on no argument")
    check("clause_2_each_word_prints_as_before_through_its_own_script", not lacks, "; ".join(lacks))


def clause_3_the_launcher_keeps_no_arm_for_the_five() -> None:
    text = (_BIN / "codemother").read_text(encoding="utf-8")
    arms = [w for w in WORDS if re.search(rf"^\s*{w}\)", text, re.M)]
    check("clause_3_the_launcher_keeps_no_arm_for_the_five", not arms,
          f"the launcher still has a case arm for {arms}" if arms else "")


def main() -> int:
    os.chdir(_REPO)
    print("ed3d02b24675 — codemother's launcher words become scripts in its bin")
    for tooth in (clause_1_each_word_is_a_named_executable_in_the_bin,
                  clause_2_each_word_prints_as_before_through_its_own_script,
                  clause_3_the_launcher_keeps_no_arm_for_the_five):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

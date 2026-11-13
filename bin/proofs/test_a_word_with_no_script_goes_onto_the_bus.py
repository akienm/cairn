"""Proof for ticket 41a70e789682 — at each `cairn <device>` segment a word naming an executable
in the device's bin runs it; no word, or a first word starting with '-', runs the self-named
launcher; any other word goes onto the bus to that device through bus_client's command mouth,
and its exit code is the command's.

Akien 2026-11-05 (Q#27, outline 8.4.2): "if there's a script for it, run it, else get on the
bus". Teeth, one per falsifier clause:

  1. with a scratch device whose bin holds `hello`, `cairn <dev> hello` runs the script;
  2. `cairn <dev> --flag` reaches the self-named launcher with --flag;
  3. `cairn <dev> zork` invokes the bus mouth with argv ['<dev>', 'zork'] (a stub mouth named
     by CAIRN_BUS_MOUTH, never a live bus) and returns its exit code, and the self-named
     launcher is never reached;
  4. bin/cmd/operator is absent and `cairn operator show inbox` still prints the inbox.

Clauses 1-3 run bin/cairn as a subprocess over a scratch CAIRN_INSTANCE_ROOT from the scratch
door; clause 4 reads the live inbox, read-only.

    python3 bin/proofs/test_a_word_with_no_script_goes_onto_the_bus.py   # exit 0 = green
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402
CAIRN = REPO / "bin" / "cairn"
DEV = "fx41a7"

PROVES = {
    "41a70e789682": {
        "1": "clause_1_a_word_naming_a_script_runs_it",
        "2": "clause_2_a_flag_reaches_the_self_named_launcher",
        "3": "clause_3_any_other_word_goes_to_the_bus_mouth",
        "4": "clause_4_the_operator_inbox_comes_through_its_device",
    },
}

FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    # the label is the tooth's PROVES name: the hollow reading reads green teeth by it
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1400]}", flush=True)
        FAILURES.append(name)


def _stub(path: Path, body: str) -> None:
    path.write_text("#!/usr/bin/env bash\n" + body + "\n")
    path.chmod(0o755)


def _world() -> tuple[Path, Path, Path]:
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir("41a7-root-")
    b = root / DEV / "0" / "bin"
    b.mkdir(parents=True)
    _stub(b / "hello", 'echo "hello:$*"')
    _stub(b / DEV, 'echo "self:$*"')
    log = root / "mouth.argv"
    mouth = root / "mouth"
    _stub(mouth, f'printf "%s\\n" "$@" > "{log}"; echo "mouth answered"; exit 7')
    return root, mouth, log


def _cairn(root: Path, mouth: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CAIRN_INSTANCE_ROOT": str(root), "CAIRN_BUS_MOUTH": str(mouth)}
    return subprocess.run([*bash_script_argv(CAIRN), *args], capture_output=True, text=True, env=env, timeout=120)


def clause_1_a_word_naming_a_script_runs_it(root: Path, mouth: Path, log: Path) -> None:
    r = _cairn(root, mouth, DEV, "Hello", "a b", "c")
    _check("clause_1_a_word_naming_a_script_runs_it",
           r.returncode == 0 and r.stdout == "hello:a b c\n" and not log.exists(),
           f"rc={r.returncode} out={r.stdout!r} err={r.stderr[-400:]!r} mouth_called={log.exists()}")


def clause_2_a_flag_reaches_the_self_named_launcher(root: Path, mouth: Path, log: Path) -> None:
    bare = _cairn(root, mouth, DEV)
    flag = _cairn(root, mouth, DEV, "--flag", "x")
    _check("clause_2_a_flag_reaches_the_self_named_launcher",
           bare.stdout == "self:\n" and flag.stdout == "self:--flag x\n" and flag.returncode == 0
           and not log.exists(),
           f"bare={bare.stdout!r} flag={flag.stdout!r} rc={flag.returncode} err={flag.stderr[-400:]!r} "
           f"mouth_called={log.exists()}")


def clause_3_any_other_word_goes_to_the_bus_mouth(root: Path, mouth: Path, log: Path) -> None:
    r = _cairn(root, mouth, DEV, "zork", "Two Words")
    argv = log.read_text().splitlines() if log.exists() else None
    _check("clause_3_any_other_word_goes_to_the_bus_mouth",
           argv == [DEV, "zork", "Two Words"] and r.returncode == 7 and "self:" not in r.stdout
           and r.stdout == "mouth answered\n",
           f"argv={argv!r} rc={r.returncode} out={r.stdout!r} err={r.stderr[-400:]!r}")


def clause_4_the_operator_inbox_comes_through_its_device() -> None:
    legacy = REPO / "bin" / "cmd" / "operator"
    r = subprocess.run([*bash_script_argv(CAIRN), "operator", "show", "inbox"], capture_output=True, text=True,
                       timeout=300)
    _check("clause_4_the_operator_inbox_comes_through_its_device",
           not legacy.exists() and r.returncode == 0 and "OPERATOR INBOX" in r.stdout,
           f"legacy_exists={legacy.exists()} rc={r.returncode} out={r.stdout[:200]!r} "
           f"err={r.stderr[-400:]!r}")


def main() -> int:
    for fn in (clause_1_a_word_naming_a_script_runs_it,
               clause_2_a_flag_reaches_the_self_named_launcher,
               clause_3_any_other_word_goes_to_the_bus_mouth):
        root, mouth, log = _world()
        fn(root, mouth, log)
    clause_4_the_operator_inbox_comes_through_its_device()
    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

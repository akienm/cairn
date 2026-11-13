#!/usr/bin/env python3
"""Proof that the tracked pre-commit hook source checks out LF on every box (ticket daaf7ac3e4ec).

WHAT IT PROVES: cairn/devices/tester/hooks/pre-commit is the shell script the reseal door copies
into .git/hooks, and .gitattributes had no pin for it, so a Windows checkout held it CRLF. The
proof copies the REAL .gitattributes into a scratch git repo and asks git itself
(``git check-attr eol``), the same pattern as the 88e30cde9bd4 proof, which is not edited.

Teeth, one per falsifier clause (PROVES below):
  (1) the hook path reads eol: lf;
  (2) the pin names the one file: a sibling under hooks/ still reads unspecified.

    python3 cairn/tools/validation_store/proofs/test_the_hook_source_checks_out_lf.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"daaf7ac3e4ec": {
    "1": "test_the_hook_source_reads_lf",
    "2": "test_the_pin_names_the_one_file",
}}

FAILURES: list[str] = []

_HOOK = "cairn/devices/tester/hooks/pre-commit"
_SIBLING = "cairn/devices/tester/hooks/some-other-file"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  [{sys.platform}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _eol(repo: Path, rel: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), "check-attr", "eol", "--", rel],
                         capture_output=True, text=True, check=True).stdout.strip()
    return out.rsplit(": ", 1)[-1]


def test_the_hook_source_reads_lf(repo: Path) -> None:
    got = _eol(repo, _HOOK)
    check(PROVES["daaf7ac3e4ec"]["1"], got == "lf", f"{_HOOK}: {got}")


def test_the_pin_names_the_one_file(repo: Path) -> None:
    got = _eol(repo, _SIBLING)
    check(PROVES["daaf7ac3e4ec"]["2"], got == "unspecified", f"{_SIBLING}: {got}")


def main() -> int:
    tmp = None
    try:
        from cairn.tools.scratch.scratch import scratch_dir
        tmp = scratch_dir("cairn-hook-pin-proof-")
        subprocess.run(["git", "-C", str(tmp), "init", "-q"], check=True)
        shutil.copyfile(_REPO_ROOT / ".gitattributes", tmp / ".gitattributes")
        test_the_hook_source_reads_lf(tmp)
        test_the_pin_names_the_one_file(tmp)
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["daaf7ac3e4ec"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

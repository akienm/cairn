#!/usr/bin/env python3
"""Proof that source files check out LF on every box (ticket 88e30cde9bd4).

WHAT IT PROVES: the validation store's fingerprint hashes raw working-tree bytes, so a CRLF
checkout (Windows, core.autocrlf=true) cannot match the Linux seal of the same commit. The repo's
own .gitattributes now pins *.py, *.md and *.txt to eol=lf (the json/jsonl/sh pins already did).
The proof copies the REAL .gitattributes into a scratch git repo and asks git itself
(``git check-attr eol``) what each path gets, so it measures the attribute the checkout uses,
not the text of the file. The fingerprint equality that motivated it (CRLF a614f1bf… vs LF
9236ec0d…, equal to Linux) is measured in the ticket, not re-asserted here.

Teeth, one per falsifier clause (PROVES below):
  (1) a .py, a .md and a .txt path read eol: lf;
  (2) the .cmd pin stays crlf and the json and sh pins stay lf.

    python3 cairn/tools/validation_store/proofs/test_source_files_are_lf_on_every_box.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"88e30cde9bd4": {
    "1": "test_py_md_and_txt_check_out_lf",
    "2": "test_the_existing_pins_are_unchanged",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  [{sys.platform}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _eol(repo: Path, rel: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), "check-attr", "eol", "--", rel],
                         capture_output=True, text=True, check=True).stdout.strip()
    return out.rsplit(": ", 1)[-1]


def _scratch() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cairn-eol-pin-proof-"))
    subprocess.run(["git", "-C", str(tmp), "init", "-q"], check=True)
    shutil.copyfile(_REPO_ROOT / ".gitattributes", tmp / ".gitattributes")
    return tmp


def test_py_md_and_txt_check_out_lf(repo: Path) -> None:
    name = PROVES["88e30cde9bd4"]["1"]
    got = {rel: _eol(repo, rel) for rel in ("cairn/x/some_module.py", "docs/notes.md", "docs/readme.txt")}
    check(name, all(v == "lf" for v in got.values()), str(got))


def test_the_existing_pins_are_unchanged(repo: Path) -> None:
    name = PROVES["88e30cde9bd4"]["2"]
    got = {rel: _eol(repo, rel) for rel in ("bin/cmd/test", "x/run.sh", "x/record.json", "x/log.jsonl", "bin/cairn.cmd")}
    want = {"bin/cmd/test": "lf", "x/run.sh": "lf", "x/record.json": "lf", "x/log.jsonl": "lf", "bin/cairn.cmd": "crlf"}
    check(name, got == want, f"got {got}")


def main() -> int:
    tmp = None
    try:
        tmp = _scratch()
        test_py_md_and_txt_check_out_lf(tmp)
        test_the_existing_pins_are_unchanged(tmp)
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["88e30cde9bd4"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

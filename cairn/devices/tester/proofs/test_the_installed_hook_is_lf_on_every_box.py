#!/usr/bin/env python3
"""Proof that the installed pre-commit hook is LF on every box (ticket 383ac6351996).

WHAT IT PROVES: ``install_hook`` copied the tracked hook with ``write_text``, which on Windows
turns each newline into CRLF, so one tracked source installed as two different byte strings
(CRLF on Windows, LF on Linux). The hook is a script a shell runs; it is written as bytes now.
The proof installs into a scratch git repo and reads the installed BYTES.

    python3 cairn/devices/tester/proofs/test_the_installed_hook_is_lf_on_every_box.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"383ac6351996": {
    "1": "test_the_installed_hook_has_no_cr_and_equals_the_source",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  [{sys.platform}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_installed_hook_has_no_cr_and_equals_the_source(repo: Path) -> None:
    from cairn.devices.tester import reseal
    name = PROVES["383ac6351996"]["1"]
    res = reseal.install_hook(repo)
    got = Path(res["path"]).read_bytes()
    want = reseal.HOOK_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    check(name, res["installed"] and b"\r" not in got and got == want,
          f"installed={res['installed']} CR bytes={got.count(b'\r')} equals source(LF)={got == want}")


def main() -> int:
    try:
        tmp = scratch_dir("cairn-hook-lf-proof-")
        subprocess.run(["git", "-C", str(tmp), "init", "-q"], check=True)
        test_the_installed_hook_has_no_cr_and_equals_the_source(tmp)
    except Exception as exc:  # noqa: BLE001
        print(f"the tooth could not run to the end: {exc!r}")
        for n in PROVES["383ac6351996"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

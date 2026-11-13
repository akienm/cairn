#!/usr/bin/env python3
"""Proof that the his_case probe's bash stubs are LF on every box (ticket 383ac6351996).

WHAT IT PROVES: the probe's ``_stub`` wrote the bash scripts its dispatcher executes with
``write_text``, which on Windows turns each newline into CRLF. A script a shell runs is written
as LF bytes now. The proof loads the probe by path (it binds the subject at call time), stubs a
script into a scratch dir and reads the BYTES.

    python3 cairn/tools/system_word/proofs/test_a_probe_stub_is_lf_on_every_box.py
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"383ac6351996": {
    "2": "test_a_probe_stub_has_no_cr_byte",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  [{sys.platform}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_a_probe_stub_has_no_cr_byte(scratch: Path) -> None:
    name = PROVES["383ac6351996"]["2"]
    path = _REPO_ROOT / "cairn" / "tools" / "system_word" / "probes" / "his_case_never_bites.py"
    spec = importlib.util.spec_from_file_location("his_case_under_proof", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._stub(scratch, "echoer", 'echo "$*"')
    got = (scratch / "echoer").read_bytes()
    check(name, b"\r" not in got and got.startswith(b"#!/usr/bin/env bash\n"),
          f"CR bytes={got.count(b'\r')}")


def main() -> int:
    tmp = None
    try:
        from cairn.tools.scratch.scratch import scratch_dir
        tmp = scratch_dir("cairn-stub-lf-proof-")
        test_a_probe_stub_has_no_cr_byte(tmp)
    except Exception as exc:  # noqa: BLE001
        print(f"the tooth could not run to the end: {exc!r}")
        for n in PROVES["383ac6351996"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Proof for ticket 3854f1aee8eb — the sudo relay's record proof generates its 10000 characters
inside the shell, and still asserts the stored stdout is the full 10000.

Measured 2026-11-12 on Windows: Git bash refuses a command line over ~8191 characters, so a proof
that submits a 10000-character argv fails there while the relay is fine. The same proof passes on
Linux, whose limit is far higher, so only a read of the proof's own source can red on Linux: the
hollow reverts ``test_sudo_relay.py``'s fix and skips that file (it is the build and the proof at
once), so these teeth live in their own file and read it.

Neither tooth spawns a process.

    python <this file>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
TARGET = REPO / "cairn/devices/sudo_relay/proofs/test_sudo_relay.py"
FUNC = "test_record_is_permanent_and_complete"

PROVES = {
    "3854f1aee8eb": {
        "1": "the_submitted_command_is_a_short_constant_not_the_output_itself",
        "2": "the_tooth_still_asserts_the_full_ten_thousand_characters_are_stored",
    },
}

LIMIT = 4000  # Git bash on Windows takes ~8191; stay well inside it


def _func() -> ast.FunctionDef:
    tree = ast.parse(TARGET.read_text(encoding="utf-8"), filename=str(TARGET))
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == FUNC:
            return n
    raise AssertionError(f"{FUNC} is gone from {TARGET}")


def the_submitted_command_is_a_short_constant_not_the_output_itself():
    calls = [n for n in ast.walk(_func())
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "submit"]
    assert calls, f"{FUNC} submits nothing"
    arg = calls[0].args[0]
    assert isinstance(arg, ast.Constant) and isinstance(arg.value, str), (
        "the submitted command is built at run time, so the output rides in argv")
    assert len(arg.value) <= LIMIT, f"the submitted command is {len(arg.value)} characters"


def the_tooth_still_asserts_the_full_ten_thousand_characters_are_stored():
    fn = _func()
    big_ok = any(
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "big" for t in n.targets)
        and isinstance(n.value, ast.BinOp) and isinstance(n.value.op, ast.Mult)
        and isinstance(n.value.left, ast.Constant) and n.value.left.value == "x"
        and isinstance(n.value.right, ast.Constant) and n.value.right.value == 10000
        for n in ast.walk(fn))
    assert big_ok, "big = 'x' * 10000 is gone"
    src = ast.dump(fn)
    cmp_ok = any(
        isinstance(n, ast.Assert) and isinstance(n.test, ast.Compare)
        and "stdout" in ast.dump(n.test) and "'big'" in ast.dump(n.test)
        for n in ast.walk(fn))
    assert cmp_ok and "len" in src, "no assert compares len(record['stdout']) with len(big)"


TEETH = [the_submitted_command_is_a_short_constant_not_the_output_itself,
         the_tooth_still_asserts_the_full_ten_thousand_characters_are_stored]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {type(e).__name__}: {e}  [{t.__name__}]")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

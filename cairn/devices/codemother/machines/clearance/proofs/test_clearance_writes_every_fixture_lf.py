"""Proof for ticket 03c41a2f00e2 — test_clearance.py writes every fixture file LF.

Measured 2026-11-13 on akiendell: test_a_refused_boat_LANDS_AT_FIXME_carrying_every_lack (test_clearance.py:2042)
failed because _fixme_world_ticket wrote a CRLF ticket (plain write_text on Windows) and clearance's
_send_to_fixme then could not rewrite it (IllegalTransition: the ticket's serialisation cannot be reproduced).
The fix is a class, not a line: every write_text call in the file passes newline="\n". This reads the file's
source with ast (nothing is run, nothing is written), so it is true on every box.

    python <this file>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "test_clearance.py"

PROVES = {
    "03c41a2f00e2": {
        "1": "every_write_text_in_test_clearance_passes_newline_lf",
    },
}


def _write_text_calls(tree: ast.AST) -> list[ast.Call]:
    return [n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "write_text"]


def _forces_lf(call: ast.Call) -> bool:
    return any(k.arg == "newline" and isinstance(k.value, ast.Constant) and k.value.value == "\n"
               for k in call.keywords)


def every_write_text_in_test_clearance_passes_newline_lf() -> None:
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    calls = _write_text_calls(tree)
    assert calls, "found no write_text call in test_clearance.py: the tooth would pass over nothing"
    bare = sorted(c.lineno for c in calls if not _forces_lf(c))
    assert not bare, (f"{len(bare)} of {len(calls)} write_text calls in test_clearance.py do not pass "
                      f"newline=\"\\n\" (CRLF on Windows): lines {bare}")


TEETH = [every_write_text_in_test_clearance_passes_newline_lf]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

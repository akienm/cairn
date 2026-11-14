"""Proof for ticket ec6dc8002b27 — the base shim no longer masks exit 3 when it starts the ground loop.

ensure_ground_loop started the loop's unit with ``-p SuccessExitStatus=3`` because the singleton loser exited 3 and a
transient unit that exits NONZERO stays loaded in ``failed`` state, blocking its name (measured 2026-08-18). Since
b38af5fd1852 the loser exits 0 quietly (Akien, Q#93, outline 5.3.5.2.1), so the flag has no job left, and with it in a
loser that regressed to the loud exit 3 would read as a success. The shim's own notes also said the loser exits 3.
These teeth READ shim.py (ast for the function, text for the notes), so they run on any OS and start nothing.

    python <this file>
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SHIM = REPO / "cairn" / "tools" / "base" / "shim.py"

PROVES = {
    "ec6dc8002b27": {
        "1": "ensure_ground_loop_does_not_pass_success_exit_status",
        "2": "shim_no_longer_says_the_singleton_loser_exits_3",
    },
}


def ensure_ground_loop_does_not_pass_success_exit_status() -> None:
    source = SHIM.read_text(encoding="utf-8")
    fn = next((n for n in ast.walk(ast.parse(source))
               if isinstance(n, ast.FunctionDef) and n.name == "ensure_ground_loop"), None)
    assert fn is not None, "found no ensure_ground_loop in shim.py: the tooth would pass over nothing"
    body = ast.get_source_segment(source, fn) or ""
    assert "systemd-run" in body, "the function found does not start the ground loop unit"
    assert "SuccessExitStatus" not in body, \
        "ensure_ground_loop still passes -p SuccessExitStatus: a loser that exits the loud 3 would read as a success"


def shim_no_longer_says_the_singleton_loser_exits_3() -> None:
    stale = [(i, line.strip()[:110]) for i, line in enumerate(SHIM.read_text(encoding="utf-8").splitlines(), 1)
             if re.search(r"loser exits 3", line)]
    assert not stale, f"shim.py still says the singleton loser exits 3: {stale}"


TEETH = [ensure_ground_loop_does_not_pass_success_exit_status, shim_no_longer_says_the_singleton_loser_exits_3]


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

"""Proof for ticket 6ba3a921dd8d — bus_client no longer masks exit 3 when it starts the bus.

``_spawn`` in remote.py started the bus unit with ``-p SuccessExitStatus=3`` because the bus loser exited EXIT_HELD=3
and a transient unit that exits NONZERO stays loaded in ``failed`` state, blocking its name (measured 2026-08-18).
Since ac71d984ebda (52ebbc598 on main) a second bus exits 0 quietly (Akien's Q#93 answer, outline 5.3.5.2.1; the bus
is CC's read of it), so the flag has no job left, and with it in a loser that regressed to the loud exit 3 would read
as a success. These teeth READ remote.py (ast for the function, text for the docstring and note), so they run on any
OS and start nothing.

    python <this file>
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
REMOTE = REPO / "cairn" / "tools" / "bus_client" / "remote.py"

PROVES = {
    "6ba3a921dd8d": {
        "1": "spawn_does_not_pass_success_exit_status",
        "2": "remote_no_longer_says_the_second_bus_exits_3",
    },
}


def spawn_does_not_pass_success_exit_status() -> None:
    source = REMOTE.read_text(encoding="utf-8")
    fn = next((n for n in ast.walk(ast.parse(source))
               if isinstance(n, ast.FunctionDef) and n.name == "_spawn"), None)
    assert fn is not None, "found no _spawn in remote.py: the tooth would pass over nothing"
    body = ast.get_source_segment(source, fn) or ""
    assert "systemd-run" in body, "the function found does not start the bus unit"
    # the docstring may name the flag as history; the ARGV must not carry it
    argv_lines = [ln for ln in body.splitlines() if "SuccessExitStatus" in ln and not ln.lstrip().startswith(("#", '"""'))]
    code_hits = [ln.strip() for ln in argv_lines if '"-p"' in ln or "'-p'" in ln]
    assert not code_hits, f"_spawn still passes -p SuccessExitStatus: a bus loser that exits the loud 3 would read as a success: {code_hits}"


def remote_no_longer_says_the_second_bus_exits_3() -> None:
    stale = [(i, line.strip()[:110]) for i, line in enumerate(REMOTE.read_text(encoding="utf-8").splitlines(), 1)
             if re.search(r"loser exits 3|SuccessExitStatus=3", line)]
    assert not stale, f"remote.py still says the bus loser exits 3 or names the flag: {stale}"


TEETH = [spawn_does_not_pass_success_exit_status, remote_no_longer_says_the_second_bus_exits_3]


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

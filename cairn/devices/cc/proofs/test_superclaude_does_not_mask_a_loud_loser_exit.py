"""Proof for ticket 15e64f9fe960 — superclaude no longer masks exit 3 for the ground loop.

The launcher started the ground loop with ``-p SuccessExitStatus=3`` because the singleton loser exited 3 and a
transient unit that exits NONZERO stays loaded in ``failed`` state, blocking its own name (measured 2026-08-18).
Since b38af5fd1852 the loser exits 0 quietly (Akien, Q#93, outline 5.3.5.2.1), a unit that exits ZERO is
garbage-collected, and the flag has no job left; worse, with it in, a loser that regressed to the loud exit 3
would read as a success. The launcher is bash, so these teeth READ ITS TEXT and run on any OS; nothing is
started and nothing is written.

    python <this file>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
LAUNCHER = REPO / "cairn" / "devices" / "cc" / "superclaude"

PROVES = {
    "15e64f9fe960": {
        "1": "the_ground_loop_unit_start_does_not_pass_success_exit_status_3",
        "2": "superclaude_no_longer_says_the_singleton_loser_exits_3",
    },
}


def _text() -> str:
    return LAUNCHER.read_text(encoding="utf-8")


def _loop_start_body(text: str) -> str:
    """The text of ``_sc_loop_start() { ... }``: from its definition to the first line that is only ``}``."""
    m = re.search(r"^_sc_loop_start\(\) \{\n(.*?)^\}\n", text, flags=re.S | re.M)
    assert m, "found no _sc_loop_start function in superclaude: the tooth would pass over nothing"
    return m.group(1)


def the_ground_loop_unit_start_does_not_pass_success_exit_status_3() -> None:
    body = _loop_start_body(_text())
    assert "systemd-run --user" in body, "the function found does not start the ground loop unit"
    assert "SuccessExitStatus" not in body, \
        "_sc_loop_start still passes -p SuccessExitStatus: a loser that exits the loud 3 would read as a success"


def superclaude_no_longer_says_the_singleton_loser_exits_3() -> None:
    text = _text()
    stale = [(i, line.strip()[:120]) for i, line in enumerate(text.splitlines(), 1)
             if re.search(r"loser exits 3|exits 3 at once|loser exits 3 BY DESIGN", line)]
    assert not stale, f"superclaude still says the singleton loser exits 3: {stale}"


TEETH = [the_ground_loop_unit_start_does_not_pass_success_exit_status_3,
         superclaude_no_longer_says_the_singleton_loser_exits_3]


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

"""Proof for ticket d845546b67b9 — proof_coverage reads a NOTRUN marker.

Outline 9.4.8.1 (CC's decision on Q#98, after Akien's Q#90 answer): a tooth that needs what a box lacks reads
not-run, never red, its outcome the sealer's. This is the READER: ``notrun_printed`` lists the teeth a proof printed
on NOTRUN lines, and ``teeth_printed`` never counts such a name green. ``teeth_printed``'s return shape is
unchanged (a third key would break test_proof_coverage.py's exact-dict assertion). Every tooth feeds literal stdout
strings to the reader, imports proof_coverage INSIDE its body (so a reverted proof_coverage.py reds the teeth and
not this file's import), spawns nothing and writes nothing.

    python <this file>
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "d845546b67b9": {
        "1": "notrun_printed_lists_the_notrun_teeth_and_an_all_notrun_run_has_no_green",
        "2": "notrun_never_counts_green_red_still_wins_and_old_output_reads_as_before",
    },
}


def notrun_printed_lists_the_notrun_teeth_and_an_all_notrun_run_has_no_green() -> None:
    from cairn.tools.proof_coverage import notrun_printed, teeth_printed
    out = ("  NOTRUN  test_a_needs_systemd — this box has no systemctl\n"
           "  NOTRUN  test_b_needs_bwrap — no bubblewrap\n"
           "  NOTRUN  test_a_needs_systemd — printed twice\n")
    assert notrun_printed(out) == ["test_a_needs_systemd", "test_b_needs_bwrap"], notrun_printed(out)
    printed = teeth_printed(out)
    assert printed["green"] == [] and printed["red"] == [], f"an all-NOTRUN run must have no green and no red: {printed}"
    assert notrun_printed("  PASS  test_x\n") == [], "output with no NOTRUN line has no notrun teeth"


def notrun_never_counts_green_red_still_wins_and_old_output_reads_as_before() -> None:
    from cairn.tools.proof_coverage import notrun_printed, teeth_printed
    both = "  PASS  test_x\n  NOTRUN  test_x — needs systemd\n  PASS  test_y\n"
    assert teeth_printed(both)["green"] == ["test_y"], f"a name printed NOTRUN must not count green: {teeth_printed(both)}"
    assert notrun_printed(both) == ["test_x"], notrun_printed(both)
    red = "  FAIL  test_z: boom\n  NOTRUN  test_z — needs systemd\n"
    assert teeth_printed(red)["red"] == ["test_z"], teeth_printed(red)
    assert notrun_printed(red) == [], f"red beats notrun: {notrun_printed(red)}"
    old = "  ok   test_a\n  FAIL test_b: boom\n  PASS  test_c\nx/y.py::test_d PASSED\n"
    assert teeth_printed(old) == {"green": ["test_a", "test_c", "test_d"], "red": ["test_b"]}, teeth_printed(old)


TEETH = [notrun_printed_lists_the_notrun_teeth_and_an_all_notrun_run_has_no_green,
         notrun_never_counts_green_red_still_wins_and_old_output_reads_as_before]


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

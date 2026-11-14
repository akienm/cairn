"""Proof for ticket f9ce5ee40b13 — a seal records the platform it was measured on.

Measured 2026-11-13 on akiendell: a validation's evidence.conditions held the interpreter path, isolation,
timeout and env digests, but no platform, so nobody could tell whether a tooth was ever green on Windows.
conditions.measure now carries ``platform`` (sys.platform and the machine); conditions.changed already
compares any key on both sides, so a green over a red from another platform names it with no further edit.

Every tooth imports the tester INSIDE its body, so a reverted conditions.py reds the teeth and does not break
this file's import. Nothing is spawned and nothing berths outside a scratch dir.

    python <this file>
"""

from __future__ import annotations

import platform
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "f9ce5ee40b13": {
        "1": "measure_records_the_platform_it_ran_on",
        "2": "changed_names_platform_when_a_red_and_a_green_were_measured_on_different_boxes",
    },
}


def measure_records_the_platform_it_ran_on() -> None:
    from cairn.devices.tester.conditions import measure
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        proof = Path(d) / "test_x.py"
        proof.write_text("print('x')\n", encoding="utf-8", newline="\n")
        got = measure(proof, iso_name="none", seal_verdict="open", instance_seal_verdict="indeterminate",
                      timeout=1, env={})
    assert "platform" in got, f"measure() records no platform: keys {sorted(got)}"
    assert got["platform"] == f"{sys.platform} {platform.machine()}", got["platform"]


def changed_names_platform_when_a_red_and_a_green_were_measured_on_different_boxes() -> None:
    from unittest import mock
    from cairn.devices.tester.conditions import changed, measure
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        proof = Path(d) / "test_x.py"
        proof.write_text("print('x')\n", encoding="utf-8", newline="\n")
        kw = dict(iso_name="none", seal_verdict="open", instance_seal_verdict="indeterminate", timeout=1, env={})
        with mock.patch.object(sys, "platform", "linux"):
            red = measure(proof, **kw)
        with mock.patch.object(sys, "platform", "win32"):
            green = measure(proof, **kw)
        again = measure(proof, **kw)
    assert changed(red, green) == ["platform"], f"a red and a green measured on different boxes: {changed(red, green)}"
    assert changed(green, dict(green)) == [], "the same platform must not read as a move"
    assert again["platform"] == f"{sys.platform} {platform.machine()}", again
    # a record sealed before this instrument has no platform key: nothing to compare, nothing notified
    older = {k: v for k, v in green.items() if k != "platform"}
    assert changed(older, green) == [], "an older record must not notify by itself"


TEETH = [measure_records_the_platform_it_ran_on,
         changed_names_platform_when_a_red_and_a_green_were_measured_on_different_boxes]


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

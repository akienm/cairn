"""Proof for ticket 9d4b040eb890 — the bus roster finds a device by its name in any case.

Measured by the orchestrator on the Dell 2026-11-14: bounce envelope 38460dafd9f842b8969b827dff502606 came from a
sender written exactly 'CC' while ``cairn/devices`` holds only ``cc``; the roster looked the name up verbatim, found no
shim, and the bounce's own return could not land (54 troubles in one burst). ``Roster.shim_for`` now folds the name
against the fitted device ids (``system_word.canon``). The fitted-id membership test is case-sensitive on every
platform, so this proof is red on Windows too, not only on a case-sensitive filesystem.

    python <this file>
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.bus_client.roster import DeviceRoster  # noqa: E402

PROVES = {
    "9d4b040eb890": {
        "1": "a_name_in_another_case_finds_the_same_shim",
        "2": "a_name_that_is_no_device_in_any_case_still_finds_nothing",
    },
}


class _Bus:
    """The least a shim's constructor may touch; nothing here is sent."""

    def __getattr__(self, name):
        raise AttributeError(name)


def a_name_in_another_case_finds_the_same_shim() -> None:
    roster = DeviceRoster(_Bus(), root=REPO)
    plain = roster.shim_for("cc")
    assert plain is not None, "the cc device has no shim in this tree: the tooth would compare nothing"
    for spelling in ("CC", "Cc"):
        got = roster.shim_for(spelling)
        assert got is not None, f"shim_for({spelling!r}) found nothing: a bounce addressed to it cannot land"
        assert got is plain, f"shim_for({spelling!r}) built a different shim from shim_for('cc'): {got!r} vs {plain!r}"


def a_name_that_is_no_device_in_any_case_still_finds_nothing() -> None:
    roster = DeviceRoster(_Bus(), root=REPO)
    for name in ("nobody", "NOBODY", "ccc"):
        got = roster.shim_for(name)
        assert got is None, f"shim_for({name!r}) found {got!r}: an undeliverable mail would no longer bounce"


TEETH = [a_name_in_another_case_finds_the_same_shim, a_name_that_is_no_device_in_any_case_still_finds_nothing]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:500]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

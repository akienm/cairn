"""Proof for ticket 913bfa09c44e: the orient floor places a top-level bin/ as the cairn device's.

Measured 2026-11-13 (the orchestrator, charting a4f5804c724a; re-measured on akienasus):
floor_packet("x in bin/cmd/proofgate") returned refs ['bin/cmd/proofgate'] and domain None,
because _rung placed only cairn/, skills/ and CairnCommons. Outline 5.4.3.3:
top-level shortcuts are the cairn device's bin/ (open-be3fe60cd353), so bin gets no rung of
its own and no charter is read for the placement.

Teeth bind orient at call time, never at import.

    bin/cairn test <this file>
"""
from __future__ import annotations

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 6))
if REPO not in sys.path:
    sys.path.insert(0, REPO)


def _orient():
    from cairn.devices.codemother.machines.orient import orient
    return orient


def test_a_ref_under_bin_is_held_by_the_cairn_device():
    floor = _orient().floor_packet("x in bin/cmd/proofgate")
    print(f"       refs: {floor['refs']}  domain: {floor['domain']!r}")
    assert floor["domain"], f"the floor placed nothing for a ref under bin/: {floor}"
    assert "bin (bin of device cairn)" in floor["domain"], (
        f"the domain does not name bin as the cairn device's: {floor['domain']!r}")


def test_a_components_bin_places_under_it_and_no_charter_gives_a_rung():
    o = _orient()
    held = o._rung("cairn/devices/testing913bdev/bin/x")
    press = o._rung("press_office/CairnComponentOutline.txt")
    print(f"       component bin: {held!r}  press_office: {press!r}")
    assert held == ("cairn/devices/testing913bdev", "device"), f"a component's bin moved: {held!r}"
    assert press is None, f"a chartered top-level dir got a rung of its own: {press!r}"


PROVES = {
    "913bfa09c44e": {
        "1": "test_a_ref_under_bin_is_held_by_the_cairn_device",
        "2": "test_a_components_bin_places_under_it_and_no_charter_gives_a_rung",
    },
}


if __name__ == "__main__":
    reds = 0
    for name, fn in [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — each tooth's failure is said, verbatim
            reds += 1
            print(f"  RED  {name}: {type(exc).__name__}: {exc}")
    print("\nGREEN" if not reds else f"\nRED ({reds})")
    sys.exit(1 if reds else 0)

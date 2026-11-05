#!/usr/bin/env python3
"""Proof that base's pane and carry proofs ride the live bus, marked as testing (ticket ad7caca4d54c).

Measured 2026-11-05, after d81baa1b5cb8 PROVED: encapsulation_breaches still listed base rows
from three proofs that stood up a private scratch bus by importing the cairn device's bus module
(test_chat_pane.py:19, test_console_pane.py:20, test_probe_carry.py:199). RULE 1: a device's
interface is the bus plus the client tool it publishes (cairn.tools.bus_client). Akien's rule,
2026-09-28 / 10-04 / 10-05: proofs ride the live bus, marked as testing — no scratch or test bus.
Pilot 20a97889646e proved the pattern on system_rackmount's proof.

Teeth, one per falsifier clause (PROVES below):
  (1) encapsulation_breaches lists no row whose file is one of the three;
  (2) each of the three reaches the live bus through bus_client.reach, names the testing mark
      for this ticket, and carries no BusDevice;
  (3) the probe-carry tooth, fired on the live bus, posts there and leaves no testing name held
      in the bus process (RemoteBus.wire_delivery holds the device; a pulsed testing shim must
      decline it).

    PYTHONPATH=. python3 cairn/tools/base/proofs/test_base_proofs_ride_the_live_bus.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_TICKET = "ad7caca4d54c"
_MARK = f"testing-{_TICKET}"
_THREE = ("cairn/tools/base/proofs/test_chat_pane.py",
          "cairn/tools/base/proofs/test_console_pane.py",
          "cairn/tools/base/proofs/test_probe_carry.py")

PROVES = {"ad7caca4d54c": {
    "1": "test_no_breach_from_the_three",
    "2": "test_the_three_reach_the_live_bus_marked",
    "3": "test_the_carry_holds_no_testing_name",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_breach_from_the_three() -> None:
    from cairn.machines.build_inspector import inspector
    rows = [r for r in inspector.encapsulation_breaches(str(_REPO)) if r.get("file") in _THREE]
    check("test_no_breach_from_the_three", not rows,
          "; ".join(f"{r['file']}:{r.get('line')} -> {r.get('module')}" for r in rows))


def test_the_three_reach_the_live_bus_marked() -> None:
    lacks = []
    for rel in _THREE:
        text = (_REPO / rel).read_text(encoding="utf-8")
        if "bus_client.reach" not in text:
            lacks.append(f"{rel}: no bus_client.reach")
        if "testing-" not in text or _TICKET not in text:
            lacks.append(f"{rel}: no testing-{_TICKET} mark")
        if "BusDevice" in text:
            lacks.append(f"{rel}: still names BusDevice")
    check("test_the_three_reach_the_live_bus_marked", not lacks, "; ".join(lacks))


def test_the_carry_holds_no_testing_name() -> None:
    from cairn.tools.bus_client import bus_client
    spec = importlib.util.spec_from_file_location(
        "_carry_under_ad7c", _REPO / "cairn/tools/base/proofs/test_probe_carry.py")
    carry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(carry)
    bus = bus_client.reach()
    before = bus.stats()
    carry.test_the_shim_fires_the_carrier_against_the_pulse_context()
    after = bus.stats()
    held = sorted(n for n in after.get("held", []) if str(n).startswith(_MARK))
    posted = after.get("posted", 0) > before.get("posted", 0)
    check("test_the_carry_holds_no_testing_name", posted and not held,
          f"posted on the live bus: {posted}; testing names held: {held}")


def main() -> int:
    os.chdir(_REPO)
    for tooth in (test_no_breach_from_the_three,
                  test_the_three_reach_the_live_bus_marked,
                  test_the_carry_holds_no_testing_name):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

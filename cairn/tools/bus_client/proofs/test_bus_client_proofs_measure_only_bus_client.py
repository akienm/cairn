#!/usr/bin/env python3
"""Proof that bus_client's proofs reach no device (ticket 38848ed72e19, RULE 1).

Until this ticket the never-beats proof imported codemother, the librarian and
intention_extractor to call their client helpers; each is a one-line reach(), which is
bus_client's own, so the tooth pins reach and the walk holds the clients to it.

Teeth:
  (1) no RULE 1 breach from a file under cairn/tools/bus_client lands on cairn/devices/codemother, cairn/devices/librarian, cairn/devices/intention_extractor;
  (2) the edited files name none of the forbidden modules.

    bin/cairn test cairn/tools/bus_client/proofs/test_bus_client_proofs_measure_only_bus_client.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"38848ed72e19": {"1": "test_no_bus_client_file_reaches_a_device", "2": "test_the_never_beats_proof_names_no_device_module"}}

COMP = "cairn/tools/bus_client"
TARGETS = ('cairn/devices/codemother', 'cairn/devices/librarian', 'cairn/devices/intention_extractor')
FORBID = {'cairn/tools/bus_client/proofs/test_a_client_reaches_and_never_beats.py': ['cairn.devices.codemother', 'cairn.devices.librarian', 'cairn.devices.intention_extractor']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_bus_client_file_reaches_a_device() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        breaches = inspector.encapsulation_breaches(".")
    finally:
        os.chdir(here)
    mine = [b for b in breaches if str(b.get("file", "")).startswith(COMP + "/")
            and str(b.get("target", "")).startswith(TARGETS)]
    # Not blind: the sieve read the tree and found breaches elsewhere. A sieve that returned
    # [] for everything would pass the first half alone.
    check("test_no_bus_client_file_reaches_a_device", not mine and bool(breaches),
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_the_never_beats_proof_names_no_device_module() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_the_never_beats_proof_names_no_device_module", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


TEETH = (test_no_bus_client_file_reaches_a_device, test_the_never_beats_proof_names_no_device_module)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

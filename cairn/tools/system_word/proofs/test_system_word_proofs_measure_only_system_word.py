#!/usr/bin/env python3
"""Proof that system_word's proofs and probes reach devices only as commands (ticket 5dc8f2efcd47, RULE 1).

Until this ticket they imported the ground loop's cli, the librarian, sudo_relay's daemon, the
harbor master and codemother's clearance to drive their folds.

Teeth:
  (1) no RULE 1 breach from a file under cairn/tools/system_word lands on cairn/devices/cairn/machines/ground_loop, cairn/devices/cairn/machines/harbor_master, cairn/devices/librarian, cairn/devices/sudo_relay, cairn/devices/codemother;
  (2) the edited files name none of the forbidden modules.

    bin/cairn test cairn/tools/system_word/proofs/test_system_word_proofs_measure_only_system_word.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"5dc8f2efcd47": {"1": "test_no_system_word_file_reaches_a_device", "2": "test_the_proof_and_probe_name_no_device_module"}}

COMP = "cairn/tools/system_word"
TARGETS = ('cairn/devices/cairn/machines/ground_loop', 'cairn/devices/cairn/machines/harbor_master', 'cairn/devices/librarian', 'cairn/devices/sudo_relay', 'cairn/devices/codemother')
FORBID = {'cairn/tools/system_word/proofs/test_system_word.py': ['cairn.devices.cairn.machines.ground_loop', 'cairn.devices.cairn.machines.harbor_master', 'cairn.devices.librarian', 'cairn.devices.sudo_relay', 'cairn.devices.codemother'], 'cairn/tools/system_word/probes/his_case_never_bites.py': ['cairn.devices.cairn.machines.ground_loop', 'cairn.devices.cairn.machines.harbor_master']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_system_word_file_reaches_a_device() -> None:
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
    check("test_no_system_word_file_reaches_a_device", not mine and bool(breaches),
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_the_proof_and_probe_name_no_device_module() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_the_proof_and_probe_name_no_device_module", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


TEETH = (test_no_system_word_file_reaches_a_device, test_the_proof_and_probe_name_no_device_module)


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

#!/usr/bin/env python3
"""Proof that codemother's proofs find the trouble store through trouble's published tool (RULE 1).

The build inspector's encapsulation_holds filed, 2026-11-11,
cairn/devices/codemother/proofs/test_codemother.py:1087 importing store_root from
cairn.devices.trouble.trouble. Outline 2.3.7.1.3 makes trouble's published store tool the one
direct line, and it exports the same store_root.

Teeth:
  (1) no RULE 1 breach from a file under cairn/devices/codemother lands on cairn/devices/trouble;
  (2) the edited files name none of the forbidden modules.

    bin/cairn test cairn/devices/codemother/proofs/test_codemother_reads_troubles_through_the_store.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"d637eae37668": {"1": "test_no_breach_from_codemother_lands_on_trouble", "2": "test_test_codemother_names_only_the_published_store"}}

COMP = "cairn/devices/codemother"
TARGETS = ('cairn/devices/trouble',)
FORBID = {'cairn/devices/codemother/proofs/test_codemother.py': ['cairn.devices.trouble.trouble', 'cairn.devices.trouble.shim', 'cairn.devices.trouble.device']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_breach_from_codemother_lands_on_trouble() -> None:
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
    check("test_no_breach_from_codemother_lands_on_trouble", not mine and bool(breaches),
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_test_codemother_names_only_the_published_store() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_test_codemother_names_only_the_published_store", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


TEETH = (test_no_breach_from_codemother_lands_on_trouble, test_test_codemother_names_only_the_published_store)


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

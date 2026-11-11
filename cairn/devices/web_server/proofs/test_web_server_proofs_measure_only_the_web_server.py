#!/usr/bin/env python3
"""Proof that web_server's proofs measure only the web server (RULE 1).

The build inspector's encapsulation_holds filed, 2026-11-11, test_web_server_chat.py:45
importing cairn.devices.librarian.shim and test_voyage_pane.py:43 importing
cairn.devices.cairn.machines.harbor_master.voyage. Both now drive the web server with spec devices.

Teeth:
  (1) no RULE 1 breach from a file under cairn/devices/web_server lands on cairn/devices/librarian, cairn/devices/cairn/machines/harbor_master;
  (2) the edited files name none of the forbidden modules.

    bin/cairn test cairn/devices/web_server/proofs/test_web_server_proofs_measure_only_the_web_server.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"3650ce94445b": {"1": "test_no_breach_from_web_server_lands_on_librarian_or_harbor", "2": "test_the_web_server_proofs_name_no_librarian_or_harbor_module"}}

COMP = "cairn/devices/web_server"
TARGETS = ('cairn/devices/librarian', 'cairn/devices/cairn/machines/harbor_master')
FORBID = {'cairn/devices/web_server/proofs/test_web_server_chat.py': ['cairn.devices.librarian', 'cairn.devices.cairn.machines.harbor_master'], 'cairn/devices/web_server/proofs/test_voyage_pane.py': ['cairn.devices.librarian', 'cairn.devices.cairn.machines.harbor_master']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_breach_from_web_server_lands_on_librarian_or_harbor() -> None:
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
    check("test_no_breach_from_web_server_lands_on_librarian_or_harbor", not mine and bool(breaches),
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_the_web_server_proofs_name_no_librarian_or_harbor_module() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_the_web_server_proofs_name_no_librarian_or_harbor_module", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


TEETH = (test_no_breach_from_web_server_lands_on_librarian_or_harbor, test_the_web_server_proofs_name_no_librarian_or_harbor_module)


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

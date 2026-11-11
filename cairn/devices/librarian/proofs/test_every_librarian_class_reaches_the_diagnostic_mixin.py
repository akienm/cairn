#!/usr/bin/env python3
"""Proof that every class with code in the librarian reaches DiagnosticBase, and loses nothing by it.

Akien 2026-10-27 (recorded on 339a45cee6a1): "everybody must inherit it. that's why it's a mixin".
Measured 2026-11-11: inspector.every_class_reaches_the_diagnostic_mixin over cairn/devices/librarian
named one class, ChatSession (chat.py:253), and the PROVED crossing of 8b16f3e77013 was refused on
it. Ticket 8c185173269a converts it, as 668c8d64b4e2 converted the tester's.

Teeth, each importing the code under test at call time:
  (1) the sieve returns no findings for component librarian;
  (2) ChatSession is a DiagnosticBase, a fresh session's page() is its tree and an empty
      transcript, and cairn.devices.librarian.chat imports in a fresh interpreter.

    bin/cairn test cairn/devices/librarian/proofs/test_every_librarian_class_reaches_the_diagnostic_mixin.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"8c185173269a": {"1": "test_the_sieve_reads_the_librarian_green",
                           "2": "test_the_session_reaches_the_mixin_and_keeps_its_behaviour"}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_sieve_reads_the_librarian_green() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        found = inspector.every_class_reaches_the_diagnostic_mixin(
            {"component": "librarian", "dir": "cairn/devices/librarian"}, Path("cairn/devices/librarian"))
    finally:
        os.chdir(here)
    check("test_the_sieve_reads_the_librarian_green", found == [],
          f"{len(found)} finding(s): " + "; ".join(str(f.get("about")) for f in found))


def test_the_session_reaches_the_mixin_and_keeps_its_behaviour() -> None:
    from cairn.devices.librarian.chat import ChatSession
    from cairn.tools.base.diagnostic import DiagnosticBase
    bad = []
    s = ChatSession(resolve=lambda *a, **k: None, tree="t")
    if not isinstance(s, DiagnosticBase):
        bad.append("ChatSession is not a DiagnosticBase")
    if s.page() != {"tree": "t", "turns": []}:
        bad.append(f"page() changed: {s.page()!r}")
    r = subprocess.run([sys.executable, "-c", "import cairn.devices.librarian.chat"],
                       cwd=_REPO, capture_output=True, text=True)
    if r.returncode != 0:
        bad.append("fresh import failed: " + ((r.stderr.strip().splitlines() or [""])[-1]))
    check("test_the_session_reaches_the_mixin_and_keeps_its_behaviour", not bad, "; ".join(bad))


TEETH = (test_the_sieve_reads_the_librarian_green,
         test_the_session_reaches_the_mixin_and_keeps_its_behaviour)


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

#!/usr/bin/env python3
"""Proof that trouble's proofs measure only trouble (ticket edf5835d2e95, RULE 1).

Until this ticket trouble's proofs imported the cairn device's log sweep, the cairn pane, the
cairn pane's probe and web_server's listener. Those teeth berth beside their owners now; what
trouble owes the end-to-end lane is measured here: a raise, poked, folded into the store, and
read back through the tool trouble publishes, inside the 1s budget ticket 9579a6f9cec6 names.

Teeth:
  (1) no RULE 1 breach from a file under cairn/devices/trouble lands on cairn/devices/cairn, cairn/devices/web_server;
  (2) the edited files name none of the forbidden modules;
  (3) a raise poked into trouble's shim is in the published store's live read, OPEN, count 1,
      inside 1s of the raise;
  (4) a second raise of one identity folds into that same row, count 2.

    bin/cairn test cairn/devices/trouble/proofs/test_trouble_proofs_measure_only_trouble.py
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"edf5835d2e95": {"1": "test_no_trouble_proof_reaches_another_device", "2": "test_the_edited_proofs_name_no_other_device", "3": "test_a_raise_reaches_the_published_store_inside_the_budget", "4": "test_a_second_raise_folds_into_the_same_row"}}

COMP = "cairn/devices/trouble"
TARGETS = ('cairn/devices/cairn', 'cairn/devices/web_server')
FORBID = {'cairn/devices/trouble/proofs/test_location_is_liveness.py': ['cairn.devices.cairn', 'cairn.devices.web_server'], 'cairn/devices/trouble/proofs/test_trouble_never_rides_the_bus.py': ['cairn.devices.cairn', 'cairn.devices.web_server']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_trouble_proof_reaches_another_device() -> None:
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
    check("test_no_trouble_proof_reaches_another_device", not mine and bool(breaches),
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_the_edited_proofs_name_no_other_device() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_the_edited_proofs_name_no_other_device", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


def _raised(roots, times: int) -> tuple[list[dict], float, list[str]]:
    """Raise one identity `times` times through a raiser whose notifier is trouble's shim,
    then read the store back through the tool trouble publishes. Returns the live rows, the
    seconds from the first raise to the read, and each raise's poke outcome."""
    from cairn.devices.trouble.shim import TroubleShim
    from cairn.devices.trouble.tools.store import store
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Raiser(DiagnosticBase):
        @property
        def diagnostic_device(self) -> str:
            return "a_fixture_component"

    shim = TroubleShim(roots=roots)
    raiser = _Raiser()
    raiser.set_diagnostic_roots(roots)
    raiser.set_trouble_notifier(shim.receive_raise)
    started = time.monotonic()
    pokes = [raiser.raise_trouble("a-fixture-trouble-for-the-store",
                                  why="trouble must hold a raise nobody put in the store by hand")["poke"]
             for _ in range(times)]
    rows = store.live(roots)
    return rows, time.monotonic() - started, pokes


def test_a_raise_reaches_the_published_store_inside_the_budget() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        roots = {k: Path(tmp) for k in ("repo", "commons", "instance")}
        rows, elapsed, pokes = _raised(roots, 1)
        mine = [r for r in rows if r.get("id") == "a-fixture-trouble-for-the-store"]
        # The poke must be what delivered it: without it this tooth measures the beat.
        ok = (pokes == ["sent"] and len(rows) == 1 and len(mine) == 1
              and mine[0].get("standing") == "OPEN" and mine[0].get("count") == 1 and elapsed < 1.0)
        check("test_a_raise_reaches_the_published_store_inside_the_budget", ok,
              f"pokes={pokes} rows={rows} elapsed={elapsed:.3f}s")


def test_a_second_raise_folds_into_the_same_row() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        roots = {k: Path(tmp) for k in ("repo", "commons", "instance")}
        rows, _, pokes = _raised(roots, 2)
        ok = (pokes == ["sent", "sent"] and len(rows) == 1
              and rows[0].get("id") == "a-fixture-trouble-for-the-store" and rows[0].get("count") == 2)
        check("test_a_second_raise_folds_into_the_same_row", ok, f"pokes={pokes} rows={rows}")


TEETH = (test_no_trouble_proof_reaches_another_device, test_the_edited_proofs_name_no_other_device,
         test_a_raise_reaches_the_published_store_inside_the_budget, test_a_second_raise_folds_into_the_same_row)


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

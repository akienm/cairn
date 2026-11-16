#!/usr/bin/env python3
"""Proof that the cairn device's proofs measure only the cairn device (ticket 6d324d26343d, RULE 1).

Until this ticket the trouble-panel proof imported web_server's render and listener and
trouble's shim. Those teeth berth with their owners; the cairn halves stay in the panel proof.

Teeth:
  (1) no RULE 1 breach from a file under cairn/devices/cairn lands on cairn/devices/web_server, cairn/devices/trouble;
  (2) the edited files name none of the forbidden modules.

    bin/cairn test cairn/devices/cairn/proofs/test_cairn_proofs_measure_only_cairn.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"a99336e5b7e3": {"1": "test_the_sieve_names_a_planted_breach", "2": "test_no_cairn_proof_reaches_web_server_or_trouble"}, "6d324d26343d": {"1": "test_no_cairn_proof_reaches_web_server_or_trouble", "2": "test_the_panel_proof_names_no_other_device"}}

COMP = "cairn/devices/cairn"
TARGETS = ('cairn/devices/web_server', 'cairn/devices/trouble')
FORBID = {'cairn/devices/cairn/proofs/test_trouble_panel.py': ['cairn.devices.web_server', 'cairn.devices.trouble.shim', 'cairn.devices.trouble.trouble', 'cairn.devices.trouble.device']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_sieve_names_a_planted_breach() -> None:
    """Not blind (ticket a99336e5b7e3): over a scratch tree holding one planted import from
    this component into cairn/devices/web_server, the sieve names exactly that row. Until this ticket the live tooth
    proved the sieve could see by requiring a breach somewhere else in the live tree, so it
    went red the day the tree came clean (measured 2026-11-16: 0 breaches at 07:45)."""
    from cairn.tools.inspect_wire.inspect_wire import ask
    from cairn.tools.scratch.scratch import scratch_dir
    root = Path(scratch_dir("testing-a99336e5b7e3-planted-breach-"))
    tgt = "cairn/devices/web_server"
    for comp in (COMP, tgt):
        parts = comp.split("/")
        for i in range(1, len(parts) + 1):
            d = root.joinpath(*parts[:i])
            d.mkdir(exist_ok=True)
            (d / "__init__.py").touch()
        (root / comp / "intention+why.json").write_text("{}\n", encoding="utf-8")
    (root / COMP / "planted.py").write_text("from cairn.devices.web_server import x\n", encoding="utf-8")
    found = [(b["file"], b["line"], b["source"], b["target"])
             for b in ask('encapsulation_breaches', str(root))]
    want = [(COMP + "/planted.py", 1, COMP, tgt)]
    check("test_the_sieve_names_a_planted_breach", found == want, f"found {found!r}")


def test_no_cairn_proof_reaches_web_server_or_trouble() -> None:
    from cairn.tools.inspect_wire.inspect_wire import ask
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        breaches = ask('encapsulation_breaches', ".")
    finally:
        os.chdir(here)
    mine = [b for b in breaches if str(b.get("file", "")).startswith(COMP + "/")
            and str(b.get("target", "")).startswith(TARGETS)]
    # Not blind is test_the_sieve_names_a_planted_breach's job (ticket a99336e5b7e3): a clean live tree is the
    # goal, so this tooth no longer needs a breach elsewhere to pass.
    check("test_no_cairn_proof_reaches_web_server_or_trouble", not mine,
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_the_panel_proof_names_no_other_device() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_the_panel_proof_names_no_other_device", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


TEETH = (test_the_sieve_names_a_planted_breach, test_no_cairn_proof_reaches_web_server_or_trouble, test_the_panel_proof_names_no_other_device)


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

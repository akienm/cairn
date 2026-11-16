#!/usr/bin/env python3
"""Proof that operator_inbox's proofs and probes reach the dashboard and the map only as commands (ticket 96afb3586d2e, RULE 1).

Until this ticket they imported codemother's dashboard and the harbor master's device and register
to render the three reports. The fixture halves berth at their owners (0c6f774d9ad8, cbbb651f4552).

Teeth:
  (1) no RULE 1 breach from a file under cairn/tools/operator_inbox lands on cairn/devices/codemother, cairn/devices/codemother/machines/harbor_master;
  (2) the edited files name none of the forbidden modules.

    bin/cairn test cairn/tools/operator_inbox/proofs/test_operator_inbox_proofs_measure_only_operator_inbox.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"54980b93254f": {"1": "test_the_sieve_names_a_planted_breach", "2": "test_no_operator_inbox_file_reaches_a_device"}, "96afb3586d2e": {"1": "test_no_operator_inbox_file_reaches_a_device", "2": "test_the_proofs_and_probe_name_no_device_module"}}

COMP = "cairn/tools/operator_inbox"
TARGETS = ('cairn/devices/codemother', 'cairn/devices/codemother/machines/harbor_master')
FORBID = {'cairn/tools/operator_inbox/proofs/test_one_status_everywhere.py': ['cairn.devices.codemother', 'cairn.devices.codemother.machines.harbor_master'], 'cairn/tools/operator_inbox/proofs/test_operator_inbox.py': ['cairn.devices.codemother'], 'cairn/tools/operator_inbox/probes/one_status_everywhere.py': ['cairn.devices.codemother', 'cairn.devices.codemother.machines.harbor_master']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_sieve_names_a_planted_breach() -> None:
    """Not blind (ticket 54980b93254f): over a scratch tree holding one planted import from
    this component into cairn/devices/codemother, the sieve names exactly that row. Until this ticket the live tooth
    proved the sieve could see by requiring a breach somewhere else in the live tree, so it
    went red the day the tree came clean (measured 2026-11-16: 0 breaches at 07:45)."""
    from cairn.tools.inspect_wire.inspect_wire import ask
    from cairn.tools.scratch.scratch import scratch_dir
    root = Path(scratch_dir("testing-54980b93254f-planted-breach-"))
    tgt = "cairn/devices/codemother"
    for comp in (COMP, tgt):
        parts = comp.split("/")
        for i in range(1, len(parts) + 1):
            d = root.joinpath(*parts[:i])
            d.mkdir(exist_ok=True)
            (d / "__init__.py").touch()
        (root / comp / "intention+why.json").write_text("{}\n", encoding="utf-8")
    (root / COMP / "planted.py").write_text("from cairn.devices.codemother import x\n", encoding="utf-8")
    found = [(b["file"], b["line"], b["source"], b["target"])
             for b in ask('encapsulation_breaches', str(root))]
    want = [(COMP + "/planted.py", 1, COMP, tgt)]
    check("test_the_sieve_names_a_planted_breach", found == want, f"found {found!r}")


def test_no_operator_inbox_file_reaches_a_device() -> None:
    from cairn.tools.inspect_wire.inspect_wire import ask
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        breaches = ask('encapsulation_breaches', ".")
    finally:
        os.chdir(here)
    mine = [b for b in breaches if str(b.get("file", "")).startswith(COMP + "/")
            and str(b.get("target", "")).startswith(TARGETS)]
    # Not blind is test_the_sieve_names_a_planted_breach's job (ticket 54980b93254f): a clean live tree is the
    # goal, so this tooth no longer needs a breach elsewhere to pass.
    check("test_no_operator_inbox_file_reaches_a_device", not mine,
          f"{len(breaches)} breach(es) in all; these: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def test_the_proofs_and_probe_name_no_device_module() -> None:
    named = {}
    for f, bad in FORBID.items():
        text = (_REPO / f).read_text(encoding="utf-8")
        hits = sorted({m for m in re.findall(r"cairn\.devices(?:\.[A-Za-z_0-9]+)+", text)
                       if m.startswith(tuple(bad))})
        if hits:
            named[f] = hits
    check("test_the_proofs_and_probe_name_no_device_module", not named, "; ".join(f"{f}: {h}" for f, h in named.items()))


TEETH = (test_the_sieve_names_a_planted_breach, test_no_operator_inbox_file_reaches_a_device, test_the_proofs_and_probe_name_no_device_module)


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

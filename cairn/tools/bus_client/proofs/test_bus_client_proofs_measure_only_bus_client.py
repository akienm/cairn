#!/usr/bin/env python3
"""Proof that bus_client's proofs reach no device (ticket 38848ed72e19, RULE 1).

Until this ticket the never-beats proof imported codemother, the librarian and
intention_extractor to call their client helpers; each is a one-line reach(), which is
bus_client's own, so the tooth pins reach and the walk holds the clients to it.

NOT BLIND BY ITS OWN PLANT (ticket 7806309a8018). The first guard asked for at least one
breach anywhere else in the live tree, and the tree went clean: measured 2026-11-12,
``inspector.encapsulation_breaches('.')`` returned 0 and the tooth red with "0 breach(es) in
all". Now the sieve is first run over a scratch tree holding one planted bus_client file that
imports cairn.devices.codemother, and must name exactly that file and line. The never-beats
proof's fixture walk is the pattern.

Teeth:
  (0) the sieve, run over a planted fixture tree, names the planted file and line and nothing else;
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

PROVES = {"38848ed72e19": {"1": "test_no_bus_client_file_reaches_a_device", "2": "test_the_never_beats_proof_names_no_device_module"},
          "7806309a8018": {"1": "test_the_sieve_names_a_planted_breach", "2": "test_no_bus_client_file_reaches_a_device"}}

COMP = "cairn/tools/bus_client"
TARGETS = ('cairn/devices/codemother', 'cairn/devices/librarian', 'cairn/devices/intention_extractor')
FORBID = {'cairn/tools/bus_client/proofs/test_a_client_reaches_and_never_beats.py': ['cairn.devices.codemother', 'cairn.devices.librarian', 'cairn.devices.intention_extractor']}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_the_sieve_names_a_planted_breach() -> None:
    """Not blind: over a scratch tree with one planted breach, the sieve names exactly it."""
    from cairn.machines.build_inspector import inspector
    from cairn.tools.scratch.scratch import scratch_dir
    root = Path(scratch_dir("testing-7806309a8018-planted-breach-"))
    for d in ("cairn", "cairn/devices", "cairn/tools", "cairn/devices/codemother", COMP):
        (root / d).mkdir(parents=True, exist_ok=True)
        (root / d / "__init__.py").touch()
    (root / COMP / "planted.py").write_text("from cairn.devices.codemother import x\n",
                                            encoding="utf-8")
    found = [(b["file"], b["line"], b["target"]) for b in inspector.encapsulation_breaches(str(root))]
    want = [(COMP + "/planted.py", 1, "cairn/devices/codemother")]
    check("test_the_sieve_names_a_planted_breach", found == want, f"found {found!r}")


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
    # Not blind is test_the_sieve_names_a_planted_breach's job (ticket 7806309a8018): a clean
    # live tree is the goal, so this tooth no longer needs a breach elsewhere to pass.
    check("test_no_bus_client_file_reaches_a_device", not mine,
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


TEETH = (test_the_sieve_names_a_planted_breach, test_no_bus_client_file_reaches_a_device, test_the_never_beats_proof_names_no_device_module)


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

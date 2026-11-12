"""Proof for ticket bb20b97a917a — tester's proofs take their bus of their own from scratch_bus.

RULE 1, outline 2.3.7.1.4 (Akien 2026-11-12, Q#86: "works for me"): the cairn device publishes
scratch_bus so a proof can have a bus it controls without reaching into the bus machine. One
tooth per falsifier clause:

  1. No file under cairn/devices/tester imports cairn.devices.cairn.machines.bus
     (encapsulation_breaches carries no tester row into the bus machine).
  2. Every moved proof runs green with its bus taken from scratch_bus.

    bin/cairn test cairn/devices/tester/proofs/test_tester_proofs_ride_the_published_scratch_bus.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 900   # tooth 2 runs each moved proof

PROVES = {"bb20b97a917a": {
    "1": "test_no_tester_file_imports_the_bus_machine",
    "2": "test_every_moved_proof_runs_green_on_scratch_bus",
}}

HERE = Path(__file__).resolve().parent
MOVED = [
    'test_a_hollow_seal_is_announced.py',
    'test_the_seal_announces_itself.py',
    'test_the_tester_takes_its_reply.py',
]


def test_no_tester_file_imports_the_bus_machine():
    from cairn.machines.build_inspector.inspector import encapsulation_breaches
    rows = [r for r in encapsulation_breaches(str(_REPO_ROOT))
            if r["file"].startswith("cairn/devices/tester/")
            and (r["target"] or "").startswith("cairn/devices/cairn/machines/bus")]
    assert not rows, [(r["file"], r["line"], r["module"]) for r in rows]


def test_every_moved_proof_runs_green_on_scratch_bus():
    reds = []
    for name in MOVED:
        src = (HERE / name).read_text(encoding="utf-8")
        assert "cairn.devices.cairn.tools.scratch_bus.scratch_bus import" in src, name
        r = subprocess.run([sys.executable, str(HERE / name)], cwd=_REPO_ROOT, capture_output=True,
                           text=True, timeout=600)
        if r.returncode != 0:
            reds.append((name, r.returncode, (r.stdout + r.stderr)[-600:]))
    assert not reds, reds


def main() -> int:
    teeth = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in teeth:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{len(teeth) - failed}/{len(teeth)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

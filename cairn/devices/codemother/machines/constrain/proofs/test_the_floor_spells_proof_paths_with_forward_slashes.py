"""Proof — constrain's floor spells every discovered instrument with forward slashes on every box.

Measured 2026-11-13 on Windows: discovered_instruments returned
'cairn\\devices\\tester\\proofs\\test_tester_holds.py'. The judge resolves instruments by the
slash spelling (the charters write it so), so a backslash instrument names a proof the door
cannot find.

Teeth, one per claim, over a scratch class-space root with three components:
  1. a claimed floor discovers its owner's proof, spelled with slashes only;
  2. the same berth unclaimed discovers all three, every one spelled with slashes only.

    python3 cairn/devices/codemother/machines/constrain/proofs/test_the_floor_spells_proof_paths_with_forward_slashes.py
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"d37dd96c44a1": {
    "1": "test_a_claimed_floor_spells_with_forward_slashes",
    "2": "test_an_unclaimed_floor_spells_with_forward_slashes",
}}

_TID = "b0e6f17a2c4e"
_HOMES = {"tester": "cairn/devices/tester", "alpha": "cairn/devices/alpha",
          "beta": "cairn/machines/beta"}


def _world():
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir("constrain-slash-floor-")
    for name, home in _HOMES.items():
        (root / home / "proofs").mkdir(parents=True)
        (root / home / "intention+why.json").write_text(json.dumps({"component": name}))
        (root / home / "proofs" / f"test_{name}_holds.py").write_text("raise SystemExit(0)\n")
    tickets = root / "tickets"
    tickets.mkdir()
    (tickets / f"{_TID}-a-fixture.json").write_text(json.dumps(
        {"id": _TID, "title": "a fixture", "owning_intention": "cairn/devices/tester/intention+why.json"}))
    packet = {"intent": "a tester build", "ticket": _TID, "refs": ["tester", "alpha", "beta"]}
    berth = root / "orient-20261113T000000-b0e6b0e6b0e8.json"
    berth.write_text(json.dumps(packet))
    bare = root / "orient-20261113T000001-b0e6b0e6b0e9.json"
    bare.write_text(json.dumps({k: v for k, v in packet.items() if k != "ticket"}))
    return root, tickets, str(berth), str(bare)


def _constrain():
    return importlib.import_module("cairn.devices.codemother.machines.constrain.constrain")


def test_a_claimed_floor_spells_with_forward_slashes():
    root, tickets, berth, _bare = _world()
    got = _constrain().discovered_instruments(berth, root=str(root), tickets_dir=tickets)
    assert got == ["cairn/devices/tester/proofs/test_tester_holds.py"], got


def test_an_unclaimed_floor_spells_with_forward_slashes():
    root, tickets, _berth, bare = _world()
    got = _constrain().discovered_instruments(bare, root=str(root), tickets_dir=tickets)
    assert len(got) == 3 and not any("\\" in p for p in got), got


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

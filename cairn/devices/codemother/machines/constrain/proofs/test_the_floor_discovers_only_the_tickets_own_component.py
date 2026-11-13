"""Proof for ticket b0e608f34ccb — constrain's floor discovers only the ticket's own component's proofs.

Measured 2026-10-05: b312ff041558's constrain stage (a one-file tester build) discovered 70 proofs
across 6 components, because discovery walked every component the orient refs resolve to. RULE 1:
a ticket's proofs measure only its own component. A claimed chart now discovers in the component
whose charter is the ticket's owning_intention; the other refs stay context, contributing none.

The world is a scratch class-space root holding cairn/devices/tester and two other components,
each with one proof, an orient berth claiming a fixture ticket whose refs reach all three, and a
fixture tickets store naming the tester as the owner.

Teeth (the falsifier is one clause, so one composite tooth under "all"):

  - a claimed orient berth whose refs reach tester, alpha and beta discovers the tester's proof
    only, every path under cairn/devices/tester/proofs/;
  - the same berth unclaimed still discovers all three (a claimless chart has no owner to read);
  - a claimed ticket whose owning intention berths outside class-space discovers nothing.

    python3 cairn/devices/codemother/machines/constrain/proofs/test_the_floor_discovers_only_the_tickets_own_component.py
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"b0e608f34ccb": {"all": "test_a_claimed_floor_discovers_only_its_owning_components_proofs"}}

_TID = "b0e6f17a2c4d"
_HOMES = {"tester": "cairn/devices/tester", "alpha": "cairn/devices/alpha",
          "beta": "cairn/machines/beta"}


def _world(owner: str | None):
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir("constrain-owner-floor-")
    for name, home in _HOMES.items():
        (root / home / "proofs").mkdir(parents=True)
        (root / home / f"{name}.py").write_text("x = 1\n")
        (root / home / "intention+why.json").write_text(json.dumps({"component": name}))
        (root / home / "proofs" / f"test_{name}_holds.py").write_text("raise SystemExit(0)\n")
    tickets = root / "tickets"
    tickets.mkdir()
    (tickets / f"{_TID}-a-fixture.json").write_text(json.dumps(
        {"id": _TID, "title": "a fixture", "owning_intention": owner}))
    berth = root / "orient-20261111T000000-b0e6b0e6b0e6.json"
    packet = {"intent": "a one-file tester build", "ticket": _TID,
              "refs": ["tester", "alpha", f"{_HOMES['beta']}/beta.py"]}
    berth.write_text(json.dumps(packet))
    bare = root / "orient-20261111T000001-b0e6b0e6b0e7.json"
    bare.write_text(json.dumps({k: v for k, v in packet.items() if k != "ticket"}))
    return root, tickets, str(berth), str(bare)


def test_a_claimed_floor_discovers_only_its_owning_components_proofs():
    c = importlib.import_module("cairn.devices.codemother.machines.constrain.constrain")
    root, tickets, berth, bare = _world("cairn/devices/tester/intention+why.json")
    got = c.discovered_instruments(berth, root=str(root), tickets_dir=tickets)
    assert got == ["cairn/devices/tester/proofs/test_tester_holds.py"], got
    assert all(p.startswith("cairn/devices/tester/proofs/") for p in got), got

    every = c.discovered_instruments(bare, root=str(root), tickets_dir=tickets)
    assert sorted(every) == sorted(f"{h}/proofs/test_{n}_holds.py" for n, h in _HOMES.items()), every

    root, tickets, berth, _bare = _world("intentions-not-beside-code/_charter+why.json")
    nothing = c.discovered_instruments(berth, root=str(root), tickets_dir=tickets)
    assert nothing == [], nothing


if __name__ == "__main__":
    try:
        test_a_claimed_floor_discovers_only_its_owning_components_proofs()
    except Exception as exc:  # noqa: BLE001
        print(f"  FAIL  test_a_claimed_floor_discovers_only_its_owning_components_proofs: "
              f"{type(exc).__name__}: {exc}", flush=True)
        print("RED — 1 tooth bit")
        raise SystemExit(1)
    print("  PASS  test_a_claimed_floor_discovers_only_its_owning_components_proofs", flush=True)
    print("green — a claimed constrain floor discovers only its owning component's proofs")

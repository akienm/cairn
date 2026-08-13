"""Proof: the FLEET REGISTER (harbor_master child a) queries the real fleet and stays an
INDEX over the boats' own records — never a rival that drifts.

Non-hollow floor (Law 8): the register must show BOTH berths non-empty over the real fleet.
A register that can only ever surface one berth proves nothing about 'query the fleet' — a
green over an empty open-set (or empty in-port-set) would be hollow. So both being real is
itself a tooth, not an incidental.

Index, not a rival record (Law 7): every in-port boat's standing is byte-equal to
`project(that boat's history).cursor` — the register gathers the boats' own answers, it does
not compute a new one that could disagree. Every open boat's standing is read from the
ticket's OWN `state` string (the bracketed [STAGE], or the raw prose state) — not invented.
Drift on either side reds this proof.

Deliberately dependency-light: pure file reads + the projector's pure core + register.py.
Runs bare.

    python3 cairn/devices/harbor_master/proofs/test_harbor_register.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.charter import projector
from cairn.devices.harbor_master import register

_SRC_ROOT = _REPO_ROOT.parent   # ~/dev/src — the root the register's source pointers are relative to


def _abs(source: str) -> Path:
    """Resolve a register source pointer back to a real path (it is relative to the src root)."""
    return _SRC_ROOT / source


def test_fleet_queries_both_berths_nonempty():
    reg = register.register()
    assert reg["open"], ("no OPEN boats — the register cannot answer 'query open tickets'; "
                         "a green here would be hollow (Law 8: the non-hollow floor needs a real open set)")
    assert reg["in_port"], ("no IN-PORT boats — the register cannot show the berthed fleet; "
                            "a green here would be hollow (the split's histories are its whole subject)")
    for b in reg["open"] + reg["in_port"]:
        assert b.get("standing"), f"{b['id']}: a boat with no standing — the register did not read its cursor"
    print(f"    (fleet: {reg['counts']['open']} open, {reg['counts']['in_port']} in port)")


def test_register_is_an_index_not_a_rival_record():
    reg = register.register()
    # IN-PORT: the register's entry is byte-equal to the boat's OWN projected cursor.
    for b in reg["in_port"]:
        history = projector.read_history(str(_abs(b["source"])))
        own = projector.project(history)["cursor"] or {}
        assert b["standing"] == own.get("standing"), (
            f"{b['id']}: register standing diverged from project(history).cursor — a rival record, "
            f"not an index (Law 7)")
        assert b["gate"] == own.get("gate") and b["seq"] == own.get("seq"), (
            f"{b['id']}: register gate/seq diverged from the boat's own cursor (Law 7)")
    # OPEN: the standing is read from the ticket's OWN state — the bracketed [STAGE], or raw prose.
    for b in reg["open"]:
        ticket = json.loads(_abs(b["source"]).read_text(encoding="utf-8"))
        state = ticket["state"]
        assert f"[{b['standing']}]" in state or b["standing"] == state.strip(), (
            f"{b['id']}: register standing '{b['standing']}' is not drawn from the ticket's own "
            f"state string — an invented cursor (Law 7)")
        assert b["id"] == ticket["id"], f"{b['id']}: register id diverged from the ticket's own id"


def test_every_boat_points_back_to_an_existing_source():
    reg = register.register()
    for b in reg["fleet"]:
        assert _abs(b["source"]).exists(), (
            f"{b['id']}: source {b['source']!r} does not exist — the index points at nothing "
            f"(an index references its boat, it does not replace it)")


def test_open_and_in_port_are_exhaustive_and_berth_disjoint():
    reg = register.register()
    assert reg["fleet"] == reg["open"] + reg["in_port"], "fleet is not exactly open ∪ in_port — a boat lost or invented"
    for b in reg["fleet"]:
        assert b["berth"] in ("open", "in_port"), f"{b['id']}: berth {b['berth']!r} is neither vantage"
    assert reg["counts"] == {
        "open": len(reg["open"]), "in_port": len(reg["in_port"]), "fleet": len(reg["fleet"])
    }, "counts disagree with the boats they count"


def test_the_scan_reaches_both_roots():
    """Both-roots (invariant, not a pinned boat): the in-port scan reaches cairn/ — the harbor sees
    its OWN berthed history — and the open scan reaches CairnCommons/tickets/ — there ARE open boats
    and each resolves to a real ticket file there. harbor-master used to sit in BOTH lanes, but once
    it berths beside code it leaves the open lane (2026-07-24); a proof that pinned it as OPEN would
    re-derive a moving value (Law 1). What must always hold: the harbor sees its own berth, and the
    tickets root is really scanned."""
    reg = register.register()
    mine = register.find(reg, "harbor_master")
    assert any(b["berth"] == "in_port" for b in mine), (
        "the harbor does not see its own berthed history — the in-port scan (cairn/) missed it")
    assert reg["open"], (
        "no OPEN boats — the open scan (CairnCommons/tickets/) surfaced nothing; the tickets root is unreached")
    for b in reg["open"]:
        assert "CairnCommons/tickets/" in b["source"] and _abs(b["source"]).exists(), (
            f"{b['id']}: an open boat whose source is not a real CairnCommons/tickets/ file — "
            f"the open scan did not reach the tickets root ({b['source']!r})")


def _main() -> int:
    checks = [
        test_fleet_queries_both_berths_nonempty,
        test_register_is_an_index_not_a_rival_record,
        test_every_boat_points_back_to_an_existing_source,
        test_open_and_in_port_are_exhaustive_and_berth_disjoint,
        test_the_scan_reaches_both_roots,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the fleet register queries both berths of the real fleet (non-hollow), stays an "
          "index over the boats' own records (no drift, Law 7), points every boat back to its source, "
          "and covers the fleet exactly (open ∪ in_port, disjoint) — harbor_master child a")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

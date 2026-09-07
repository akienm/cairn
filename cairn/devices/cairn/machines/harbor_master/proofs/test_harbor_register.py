"""Proof: the FLEET REGISTER (harbor_master child a) queries the real fleet and stays an
INDEX over the boats' own records — never a rival that drifts.

Non-hollow floor (Law 8): the register must show BOTH berths non-empty over the real fleet.
A register that can only ever surface one berth proves nothing about 'query the fleet' — a
green over an empty open-set (or empty in-port-set) would be hollow. So both being real is
itself a tooth, not an incidental.

Index, not a rival record (Law 7): every open boat's standing IS the one label
operator_inbox derives from the ticket's OWN workflow string (ticket 3feb201c84ea — one
status, one reader); every in-port entry berths exactly the open boats whose
``owning_component`` names it, and carries the component's own projected cursor (gate, seq)
unchanged; a history whose last standing is prose rather than a stage token is a FINDING,
never a status. Drift on any side reds this proof.

Deliberately dependency-light: pure file reads + the projector's pure core + register.py.
Runs bare.

    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_harbor_register.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.charter import projector
from cairn.tools.operator_inbox.inbox import cursor_of, is_stage_token, status_label
from cairn.devices.cairn.machines.harbor_master import register

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
    for b in reg["open"]:
        assert b.get("standing"), f"{b['id']}: a boat with no standing — the register did not read its cursor"
    assert any(e["boats"] for e in reg["in_port"]), (
        "no component has a boat berthed at it — the in-port lane is empty of tickets (hollow)")
    print(f"    (fleet: {reg['counts']['open']} open, {reg['counts']['in_port']} in port, "
          f"{reg['counts']['findings']} finding(s))")


def test_register_is_an_index_not_a_rival_record():
    reg = register.register()
    # OPEN: the standing IS the one label the one reader derives from the ticket's OWN string.
    for b in reg["open"]:
        ticket = json.loads(_abs(b["source"]).read_text(encoding="utf-8"))
        own = status_label(cursor_of(ticket["workflow_and_state"]))
        assert b["standing"] == b["label"] == own, (
            f"{b['id']}: register standing '{b['standing']}' is not the ticket's own label "
            f"{own!r} — a second reader (Law 7, ticket 3feb201c84ea)")
        assert b["id"] == ticket["id"], f"{b['id']}: register id diverged from the ticket's own id"
    # IN-PORT: each entry berths exactly the open boats naming it, the SAME dicts; its
    # gate/seq are the component's own projected cursor; a prose standing is a finding.
    open_by_id = {id(b): b for b in reg["open"]}
    for e in reg["in_port"]:
        for b in e["boats"]:
            assert id(b) in open_by_id, f"{e['component']}: berthed boat {b['id']} is a copy, not the open boat"
            assert b["owning_component"] == e["component"], (
                f"{b['id']} berthed at {e['component']} but owned by {b['owning_component']}")
        expected = [b for b in reg["open"] if (b["owning_component"] or "unassigned") == e["component"]]
        assert [b["id"] for b in e["boats"]] == [b["id"] for b in expected], (
            f"{e['component']}: berthed {[b['id'] for b in e['boats']]} != owned {[b['id'] for b in expected]}")
        if e["source"].endswith("history.json"):
            own = projector.project(projector.read_history(str(_abs(e["source"]))))["cursor"] or {}
            assert e["standing"] == own.get("standing") and e["gate"] == own.get("gate") \
                and e["seq"] == own.get("seq"), (
                f"{e['id']}: register cursor diverged from the component's own history (Law 7)")
    for f in reg["findings"]:
        assert not is_stage_token(f["standing"]), f"{f['component']}: a stage token filed as a finding"
        assert any(e["component"] == f["component"] and e["standing"] == f["standing"]
                   for e in reg["in_port"]), f"{f['component']}: finding names no in-port entry"
    for e in reg["in_port"]:
        if e["standing"] is not None and not is_stage_token(e["standing"]):
            assert any(f["component"] == e["component"] for f in reg["findings"]), (
                f"{e['component']}: prose standing {e['standing'][:40]!r} not surfaced as a finding (Law 7)")


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
        "open": len(reg["open"]), "in_port": len(reg["in_port"]), "fleet": len(reg["fleet"]),
        "findings": len(reg["findings"]),
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
          "index over the one reader's labels and the components' own cursors (no drift, Law 7; "
          "prose standings are findings), points every boat back to its source, "
          "and covers the fleet exactly (open ∪ in_port, disjoint) — harbor_master child a")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

#!/usr/bin/env python3
"""Orient's deposit-back into the tree, measured at orient's own address.

These teeth stood in cairn/tools/tree/proofs/test_chart_tree.py, where they reached into
codemother's code from the tree tool (RULE 1; the build inspector's encapsulation_holds filed
cairn/tools/tree/proofs/test_chart_tree.py:50, :225, :364 on 2026-11-11). They measure orient —
deposit_orient and validate_orient — so ticket a692614a4654 moved them beside it, unchanged:

  - GATE BEFORE SEED: a malformed packet never reaches the tree (validate_orient runs at
    the deposit-back door), and a berth path that does not exist on disk refuses BY NAME,
    with the control that the same packet, berthed, is accepted (ticket 9c46e187f2de).
  - DEPOSIT-BACK LANDS HONESTLY: content is the packet's intent, provenance names the
    berth, standing is hypothesis; a duplicate writes nothing (ticket a229f01ed699 (1)).
  - THE ORIENT LEAF IS CODEMOTHER'S SCRATCH (ticket a229f01ed699 (2)).
  - 'tree' IS A LEGAL STRATUM at the packet gate — the seam the ceiling writes through.
  - a692614a4654 (1): the tree tool's proofs import nothing from codemother — the sieve reads [].

Requires the one-time DB provisioning, as the tree tool's proof does. Self-cleaning: the
scratch nexus this run mints is dropped at close.

    bin/cairn test cairn/devices/codemother/machines/orient/proofs/test_orient_deposits_into_the_tree.py
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.codemother.machines.orient.orient import (OrientRefused, deposit_orient)
from cairn.tools.tree.tree import nexus_table, scratch_nexus
from cairn.devices.db_domain.tools.client import store
from cairn.devices.librarian.tools.trees import trees

PROVES = {
    "9c46e187f2de": {"all": "test_gate_before_seed"},
    "a229f01ed699": {"1": "test_deposit_back_lands_and_dedups",
                     "2": "test_the_orient_leaf_is_codemothers_scratch"},
    "a692614a4654": {"1": "test_the_tree_tools_proofs_reach_no_codemother_code",
                "2": "test_tree_is_a_legal_stratum_at_the_packet_gate"},
}

_SCRATCH = contextlib.ExitStack()   # the nexus tables this run mints ride store.scratch(): dropped at close
_HELD: list[tuple[str, str]] = []   # (nexus name, owner) — each forgotten under its own owner at close
_ORIENT: list[str] = []
_CREATED_NODES: list[str] = []

# deposit_orient writes under codemother's owner since 2b3d842bc118, so the teeth that drive it
# deposit into a codemother-owned scratch nexus and read it there (ticket a229f01ed699).
ORIENT_OWNER = "codemother"
_CHART: list[str] = []


def _nexus() -> str:
    """A chart-owned scratch nexus name, for the intent text of the leaf-ownership tooth."""
    if not _CHART:
        name = _SCRATCH.enter_context(scratch_nexus("orient"))
        _HELD.append((name, "chart"))
        _CHART.append(name)
    return _CHART[0]

def _orient_nexus() -> str:
    """This run's codemother-owned scratch nexus, the one deposit_orient's leaf lands in."""
    if not _ORIENT:
        name = _SCRATCH.enter_context(scratch_nexus("orient", owner=ORIENT_OWNER))
        _HELD.append((name, ORIENT_OWNER))
        _ORIENT.append(name)
    return _ORIENT[0]


def _orient_table() -> str:
    return nexus_table(_orient_nexus(), owner=ORIENT_OWNER)


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def _packet(intent="wire the tree stratum into the orient nexus of the chart device",
            **over):
    p = {
        "intent": intent,
        "domain": "chart — the nexus machinery",
        "scope": "IN: the orient nexus's tree. OUT: everything else.",
        # A LIVE ref, and it must stay live: validate_orient refuses an unverifiable
        # ref BEFORE it reaches the berth check, so a fixture naming a component that
        # has stopped existing reds the berth tooth with the wrong reason. "chart"
        # stood here until 2026-08-13, when the decomposition made it a skill and not
        # a component; "tree" is the component this proof is about.
        "refs": ["tree"],
        "unknowns": [],
        "confidence": 0.7,
        # ALL FIVE AUTHORED FIELDS, because this fixture stands for a BERTHED packet.
        # The write door (validate_orient with measure_provenance=True) refuses a
        # sender that declares refs/domain/unknowns and stamps them itself (ticket
        # orient-floor-authors-and-provenance-is-measured, 2026-08-14); the deposit
        # door (measure_provenance=False, since ticket 4c022c44de53) measures nothing
        # and REQUIRES coverage of every authored field — a berthed packet always has
        # it. A fixture carrying only intent/scope was refused with "provenance does
        # not cover: domain, refs, unknowns" one lack BEFORE the berth-existence check,
        # so the berth tooth asserted a refusal the door never reached (ticket
        # 9c46e187f2de). 'cc' is an accepted stratum; the value is not what the tooth
        # measures, the coverage is.
        "provenance": {"intent": "cc", "scope": "cc",
                       "domain": "cc", "refs": "cc", "unknowns": "cc"},
    }
    p.update(over)
    return p


def _berthed_fixture(tmp: str, packet: dict) -> str:
    path = os.path.join(tmp, "orient-20260728T120000-feedfacecafe.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(packet, fh)
    return path


def test_gate_before_seed():
    before = trees.tree_state(_orient_nexus(), table=_orient_table(), owner=ORIENT_OWNER)
    with tempfile.TemporaryDirectory() as tmp:
        berth = _berthed_fixture(tmp, _packet())
        # A malformed packet (missing a required field) never reaches the tree.
        broken = _packet()
        del broken["confidence"]
        _refuses(OrientRefused, deposit_orient, broken, [1.0, 0.0, 0.0], berth_path=berth)
        # A berth that does not exist on disk refuses — provenance may not point at nothing.
        # The refusal must be THAT refusal: it names the missing path, and it is not the
        # coverage refusal that stood in front of it until ticket 9c46e187f2de.
        missing = os.path.join(tmp, "no-such-berth.json")
        msg = _refuses(OrientRefused, deposit_orient, _packet(), [1.0, 0.0, 0.0],
                       berth_path=missing)
        assert "does not exist" in msg, msg
        assert missing in msg, "the refusal must name the berth that is not there: " + msg
        assert "provenance does not cover" not in msg, \
            "the fixture was refused one lack early — the berth check was never reached"
        assert trees.tree_state(_orient_nexus(), table=_orient_table(), owner=ORIENT_OWNER) == before, \
            "a refused deposit-back must leave the tree exactly where it stood"
        # THE CONTROL: the same packet, with the berth that exists, is accepted — so the
        # refusal above was the berth's and not some earlier lack the packet carries.
        control = _packet(intent=f"the gate control packet of the chart tree proof [{_orient_nexus()}]")
        berth = _berthed_fixture(tmp, control)
        r = deposit_orient(control, [1.0, 0.0, 0.0], berth_path=berth, nexus=_orient_nexus())
        _CREATED_NODES.append(r["node_id"])
        assert r["duplicate"] is False, "the control packet must land as a new node"


def test_deposit_back_lands_and_dedups():
    with tempfile.TemporaryDirectory() as tmp:
        packet = _packet(intent=f"wire the tree stratum into the orient nexus [{_orient_nexus()}]")
        berth = _berthed_fixture(tmp, packet)
        r = deposit_orient(packet, [0.9, 0.1, 0.0], berth_path=berth, nexus=_orient_nexus())
        _CREATED_NODES.append(r["node_id"])
        assert r["duplicate"] is False
        node_rows = store.read(trees.NODES_TABLE, where="node_id = %s", params=(r["node_id"],))
        assert node_rows and node_rows[0]["content"] == packet["intent"], \
            "the node's content is the packet's intent"
        assert node_rows[0]["provenance"]["source"] == berth, "provenance names the berth"
        assert node_rows[0]["provenance"]["confidence"] == packet["confidence"]
        assert node_rows[0]["standing"] == "hypothesis", "born a hypothesis (inherited physics)"
        leaf_rows = store.read(_orient_table(), where="node_id = %s", params=(r["node_id"],))
        assert leaf_rows, "a leaf must land in the nexus's table"
        # The same packet again: a duplicate writes nothing (Law 1).
        before = trees.tree_state(_orient_nexus(), table=_orient_table(), owner=ORIENT_OWNER)
        r2 = deposit_orient(packet, [0.9, 0.1, 0.0], berth_path=berth, nexus=_orient_nexus())
        assert r2["duplicate"] is True
        assert trees.tree_state(_orient_nexus(), table=_orient_table(), owner=ORIENT_OWNER) == before


def test_the_orient_leaf_is_codemothers_scratch():
    """deposit_orient writes under codemother's owner (2b3d842bc118), so the leaf this proof
    makes it write must be codemother's AND a registered scratch table — one that cannot
    outlive the run (ticket a229f01ed699; three unregistered ones leaked 2026-11-06)."""
    from cairn.devices.codemother.machines.orient import orient as orient_mod
    with tempfile.TemporaryDirectory() as tmp:
        packet = _packet(intent=f"the orient leaf ownership probe [{_nexus()}]")
        berth = _berthed_fixture(tmp, packet)
        nexus = _orient_nexus()
        r = deposit_orient(packet, [0.7, 0.3, 0.0], berth_path=berth, nexus=nexus)
        _CREATED_NODES.append(r["node_id"])
        leaf = nexus_table(nexus, owner=orient_mod.OWNER)
        assert store.owner_of(leaf) == "codemother", \
            f"deposit_orient's leaf {leaf} must be codemother's, not {store.owner_of(leaf)!r}"
        assert store.is_scratch(leaf), \
            f"deposit_orient's leaf {leaf} is not a registered scratch table — it outlives the run"


def test_tree_is_a_legal_stratum_at_the_packet_gate():
    from cairn.devices.codemother.machines.orient.orient import (validate_orient)
    p = _packet(provenance={"intent": "tree", "domain": "tree", "scope": "tree",
                            "unknowns": "tree"})
    assert validate_orient(p) is p, "the ceiling writes 'tree' through the standing gate"
    # A 'tree' DECLARATION SURVIVES THE FLOOR MEASUREMENT, and this is the clause the
    # 2026-08-14 door had to be careful about: it derives ``floor`` vs ``claude`` and
    # nothing else, so a field the ceiling says came from the TREE keeps saying so. The
    # alternative — overwriting every unreproducible field with ``claude`` — would trade
    # one wrong label for another and erase the only stratum the tree walk can claim.
    assert p["provenance"]["domain"] == "tree", p["provenance"]
    assert p["provenance"]["unknowns"] == "tree", p["provenance"]
    assert p["provenance"]["refs"] == "cc", \
        "an undeclared floor-authored field is derived, and this packet carries no request"


def test_the_tree_tools_proofs_reach_no_codemother_code():
    """The tree tool's proofs import nothing from codemother (RULE 1): the encapsulation sieve
    reads [] for component tree."""
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO_ROOT)
    try:
        found = inspector.encapsulation_holds({"component": "tree", "dir": "cairn/tools/tree"},
                                              Path("cairn/tools/tree"))
    finally:
        os.chdir(here)
    assert found == [], "; ".join(str(f.get("about")) for f in found)


def _main() -> int:
    checks = [
        test_gate_before_seed,
        test_deposit_back_lands_and_dedups,
        test_the_orient_leaf_is_codemothers_scratch,
        test_tree_is_a_legal_stratum_at_the_packet_gate,
        test_the_tree_tools_proofs_reach_no_codemother_code,
    ]
    failed = []
    try:
        for check in checks:     # every tooth runs and reports: a tooth's failure is its verdict
            try:
                check()
                print(f"  PASS  {check.__name__}", flush=True)
            except Exception:    # noqa: BLE001 — loud, named, and counted (Law 7)
                import traceback
                traceback.print_exc()
                print(f"  FAIL  {check.__name__}", flush=True)
                failed.append(check.__name__)
    finally:
        for name, owner in _HELD:     # this run's rows out of the shared tables, then the scratch nexi dropped
            trees.forget_leaf(nexus_table(name, owner=owner))
        _SCRATCH.close()
    if failed:
        print(f"RED — {len(failed)} failure(s): {', '.join(failed)}")
        return 1
    print("green — orient deposits into the tree from its own address: the gate runs before the "
          "seed, deposit-back lands honest and dedups, the leaf is codemother's scratch, 'tree' is "
          "a legal stratum, and the tree tool's proofs reach no codemother code")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

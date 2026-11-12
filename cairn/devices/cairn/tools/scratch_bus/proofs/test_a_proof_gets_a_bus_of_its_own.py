"""Proof for ticket a695aee4d89b — the cairn device publishes a proof's bus of its own.

Measured 2026-11-11: encapsulation_holds redded seven sites in five codemother and tester
proofs importing cairn.devices.cairn.machines.bus.bus/.shim for a scratch bus and its shim.
RULE 1 admits a reach into the cairn device only through a tool it publishes; this is that
tool, and these teeth measure the tool alone.

Teeth, one per falsifier clause:

  1. A post on the yielded bus reads back off its store, stands undelivered with no shim wired
     for its addressee, and flush leaves the ring empty with the post still standing once.
  2. The scratch transit table is registered scratch inside the context and gone after it.
  3. bus_shim builds the bus's own shim, over that bus.
  4. The encapsulation sieve admits an import of this tool from outside the cairn device and
     still reds an import of the bus machine (the charter's published_by_device is read).

    python3 cairn/devices/cairn/tools/scratch_bus/proofs/test_a_proof_gets_a_bus_of_its_own.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"a695aee4d89b": {
    "1": "test_a_post_stands_in_the_scratch_store_undelivered_and_flush_keeps_it",
    "2": "test_the_scratch_table_drops_when_the_context_exits",
    "3": "test_bus_shim_is_the_bus_own_shim_over_that_bus",
    "4": "test_the_sieve_admits_this_tool_and_still_reds_the_bus_machine",
}}

_TO = "testing-a695aee4d89b-nobody"


def _tool():
    from cairn.devices.cairn.tools.scratch_bus import scratch_bus
    return scratch_bus


def test_a_post_stands_in_the_scratch_store_undelivered_and_flush_keeps_it():
    with _tool().scratch_bus("sb_post") as bus:
        bus.post(sender="testing-a695aee4d89b", to=_TO, channel="personal", verb="sealed",
                 why="testing-a695aee4d89b a fixture post", body={"n": 1})
        bus.flush()
        assert not bus._ring, f"{len(bus._ring)} envelope(s) still in the ring after flush"
        read = [e for e in bus.read(to=_TO, channel="personal") if e.get("verb") == "sealed"]
        assert len(read) == 1, f"{len(read)} posts read back, want 1"
        waiting = [e for e in bus.undelivered(to=_TO) if e.get("verb") == "sealed"]
        assert len(waiting) == 1, f"{len(waiting)} undelivered with no shim wired, want 1"


def test_the_scratch_table_drops_when_the_context_exits():
    from cairn.devices.db_domain.tools.client import store
    with _tool().scratch_bus("sb_drop") as bus:
        table = bus._table
        assert store.is_scratch(table), f"{table} is not registered scratch"
        assert store.owner_of(table) is not None, f"{table} has no owner while open"
    assert not store.is_scratch(table), f"{table} is still registered scratch after exit"
    assert store.owner_of(table) is None, f"{table} still owned after exit"


def test_bus_shim_is_the_bus_own_shim_over_that_bus():
    from cairn.devices.cairn.machines.bus.shim import BusShim
    with _tool().scratch_bus("sb_shim") as bus:
        shim = _tool().bus_shim(bus)
        assert type(shim) is BusShim, type(shim)
        assert shim._bus is bus, "the shim is over another bus"


def test_the_sieve_admits_this_tool_and_still_reds_the_bus_machine():
    from cairn.machines.build_inspector import inspector
    root = str(_REPO_ROOT)
    assert inspector._published_tool("cairn/devices/cairn/tools/scratch_bus/scratch_bus.py", root)
    assert not inspector._published_tool("cairn/devices/cairn/machines/bus/bus.py", root)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

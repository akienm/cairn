"""The cairn device's pulse — it fires its own clock probes, ticket 32959e65ec5a.

The heartbeat calls this module's ``on_pulse`` every beat and does nothing else
(bae622881f03). history_integrity and trouble_panel_surfaces_live_troubles are cairn's
clock probes (Akien's group-2 list, 2026-09-30), so they fire here, and only they do: the
other modules in ../probes/ are not in the roster.

The bus is ``reach("trouble")``, built on the first beat: the trouble panel probe asks the
trouble device over the bus, so trouble's shim must be wired on it; reach never beats.
"""
from __future__ import annotations

from pathlib import Path

from cairn.tools.base.beat_probes import BeatProbes

NAMES = ("history_integrity", "trouble_panel_surfaces_live_troubles")


def _bus():
    from cairn.tools.bus_client import reach
    return reach("trouble")


FIRER = BeatProbes("cairn", Path(__file__).resolve().parent.parent, list(NAMES), bus=_bus)


def on_pulse(now, context=None) -> dict:
    return FIRER.on_pulse(now, context)

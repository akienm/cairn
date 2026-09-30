"""The cc device's pulse — it fires its own clock probes, ticket c787b6eea082.

The heartbeat calls this module's ``on_pulse`` every beat and does nothing else
(bae622881f03). memory_curve and is_the_memory_curve_recorded are cc's clock probes
(Akien's group-2 list, 2026-09-30), so they fire here, and only they do: any other module
in ../probes/ is not in the roster.

The bus is ``reach()``, built on the first beat and never at import: no named probe asks
another device over the bus, so no shim is wired on it; reach never beats.
"""
from __future__ import annotations

from pathlib import Path

from cairn.tools.base.beat_probes import BeatProbes

NAMES = ('memory_curve', 'is_the_memory_curve_recorded')


def _bus():
    from cairn.tools.bus_client import reach
    return reach()


FIRER = BeatProbes('cc', Path(__file__).resolve().parent.parent, list(NAMES), bus=_bus)


def on_pulse(now, context=None) -> dict:
    return FIRER.on_pulse(now, context)

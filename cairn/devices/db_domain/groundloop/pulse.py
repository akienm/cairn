"""The db_domain device's pulse — it fires its own clock probes, ticket ca48eeeef86e.

The heartbeat calls this module's ``on_pulse`` every beat and does nothing else
(bae622881f03). scratch_stays_swept is db_domain's clock probe (Akien's group-2 list,
2026-09-30), so it fires here, and only it does: any other module in ../probes/ is not in
the roster.

The bus is ``reach()``, built on the first beat and never at import: no named probe asks
another device over the bus, so no shim is wired on it; reach never beats.
"""
from __future__ import annotations

from pathlib import Path

from cairn.tools.base.beat_probes import BeatProbes

NAMES = ('scratch_stays_swept',)


def _bus():
    from cairn.tools.bus_client import reach
    return reach()


FIRER = BeatProbes('db_domain', Path(__file__).resolve().parent.parent, list(NAMES), bus=_bus)


def on_pulse(now, context=None) -> dict:
    return FIRER.on_pulse(now, context)

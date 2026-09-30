"""The ticket_inspector tool's pulse — it fires its own clock probes, ticket 1904fd89231a.

The heartbeat calls this module's ``on_pulse`` every beat and does nothing else
(bae622881f03). the_corpus_gets_cleaner is ticket_inspector's clock probe (Akien's group-2
list, 2026-09-30), so it fires here, and only it does: any other module in ../probes/ is
not in the roster.

The bus is ``reach()``, built on the first beat and never at import: no named probe asks
another device over the bus, so no shim is wired on it; reach never beats.
"""
from __future__ import annotations

from pathlib import Path

from cairn.tools.base.beat_probes import BeatProbes

NAMES = ('the_corpus_gets_cleaner',)


def _bus():
    from cairn.tools.bus_client import reach
    return reach()


FIRER = BeatProbes('ticket_inspector', Path(__file__).resolve().parent.parent, list(NAMES), bus=_bus)


def on_pulse(now, context=None) -> dict:
    return FIRER.on_pulse(now, context)

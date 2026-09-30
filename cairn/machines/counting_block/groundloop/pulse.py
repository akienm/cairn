"""counting_block/groundloop/pulse.py — the block runs on the beat, and only on the beat.

The ground loop discovers any ``groundloop/pulse.py`` under a component folder and the
shim's pulse service calls ``on_pulse`` after the probes on every beat. That is the whole
wiring: no process, no poller, no registration (falsifier clause 4 of 5a4ec289bf15 —
``ps`` shows nothing; the beat's pulse service IS the poke the ticket's how called the
door's probe poke, a --decide line on the ticket).

The beat is the heartbeat and nothing more (memory ground-loop-is-just-the-heartbeat);
this module is a hook the beat calls, not a feature of the beat. It does one thing:
``block.pulse()`` — recompile the table, raise each new zero-count entry once, write the
table and the probe's acknowledgement. A raising hook is recorded ``refused`` by the pulse
service rather than stopping the beat, so a broken journal is loud on the beat's own
record and never silent.

It also fires the block's one clock probe, raise_rate_falls (ticket a1eca667d227; Akien's
group-2 list, 2026-09-30): the fold first, then the probes, one record. The bus is
``reach()``, built on the first beat and never at import; no named probe asks over it.
"""
from __future__ import annotations

from pathlib import Path

from cairn.machines.counting_block import block
from cairn.tools.base.beat_probes import BeatProbes

NAMES = ("raise_rate_falls",)


def _bus():
    from cairn.tools.bus_client import reach
    return reach()


FIRER = BeatProbes("counting_block", Path(__file__).resolve().parent.parent, list(NAMES), bus=_bus)


def on_pulse(now, context: dict | None = None) -> dict:
    """Called each heartbeat beat. One fold, then the clock probes; returns both."""
    out = block.pulse(now=now)
    d = {"block": block.COMPONENT, "raised": len(out["raised"]),
         "post_appends": out["post_appends"], "compression": out["compression"]}
    d["probes"] = FIRER.on_pulse(now, context)
    return d

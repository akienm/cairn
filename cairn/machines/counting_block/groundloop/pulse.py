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
"""
from __future__ import annotations

from cairn.machines.counting_block import block


def on_pulse(now, context: dict | None = None) -> dict:
    """Called each heartbeat beat. One fold; returns what the fold did."""
    out = block.pulse(now=now)
    return {"block": block.COMPONENT, "raised": len(out["raised"]),
            "post_appends": out["post_appends"], "compression": out["compression"]}

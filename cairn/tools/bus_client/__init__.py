"""cairn.tools.bus_client — reaching the bus, at its own address.

WHY IT IS A TOOL AND NOT A LODGER. It lived in ``cairn/tools/base/`` until 2026-09-09,
and that address made a measurable difference rather than an aesthetic one. ``base`` also
holds ``transitions.py``, the emit chokepoint — which makes the whole component a GATE by
the determinism walk's own derivation (a gate is derived from the import, not from a
charter). This module imports ``inference_domain``. So the directory reached an oracle, and
Akien's ruling of 2026-08-13 is that NO GATES MAY CONSULT ORACLES EVER PERIOD. The reach was
never the gate's; it was the lodger's, counted against the landlord because they shared a
directory. Moving one file is the whole fix, and the verdict on ``base`` changes because the
world changed — not because the instrument was adjusted, which is the plaster CLAUDE.md
forbids and which determinism's own WRONG-SHAPE SIGNAL exists to catch.

IT IS A TOOL BY LAW 6'S TEST, not by placement: it has users, not owners. It gates no writes
at its own address because it holds no state of its own — the bus state berths under the
holder that assembled the client, at ``~/.cairn/devices/<device>/<instance>/``. Anything
called a tool that must gate writes at its own address is a machine; this one need not.

THE THREE FACES, and choosing between them is the contract ticket fc93d8cd5961 settled:
``reach(*devices)`` is the CLIENT's face — it wires a delivery hook per named device and
pays no beat. ``connect_bus`` / ``connect_system`` are the RUNNER's. Since one bus per
instance (ticket 48519f4789b1) neither beats either: ``beat`` is accepted and ignored, and the
ground loop is the only heartbeat (outline 5.5, 19.5.1). When they did beat, a beat
cost ~23.5s against ~0.23s per shim; a client that reaches for the runner's face is still a
measured defect, and ``probes/a_client_reaches_and_never_beats.py`` reds for it.
"""

from cairn.tools.bus_client.bus_client import (
    _load_device_shim,
    _wire,
    connect_bus,
    connect_system,
    harbor_source,
    inference_bus,
    models_stack,
    reach,
)

__all__ = [
    "connect_bus",
    "connect_system",
    "harbor_source",
    "inference_bus",
    "models_stack",
    "reach",
    "_wire",
    "_load_device_shim",
]

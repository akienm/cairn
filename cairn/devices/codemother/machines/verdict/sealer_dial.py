"""The verdict gate's sealer dial — the face that wires the address and the client in.

verdict.py stays inside its import allowlist (the one validator stays tree-free), so it takes
``sealer_home`` and ``exchange`` as injected values and never reads an environment or imports a
client. This face is the caller that supplies them (ticket 86cccb7d30f7, outline 9.4.8.1): a box
that cannot confirm a seal sets ``CAIRN_VERDICT_SEALER_HOME`` to the ``host:port`` of one that can,
and the gate's refused runs are asked of that box's tester over the bus. Unset means no dial.
"""
from __future__ import annotations

import os

from cairn.devices.codemother.machines.verdict import verdict
from cairn.tools.bus_client import remote

ENV = "CAIRN_VERDICT_SEALER_HOME"


def configured(environ=None) -> dict:
    """The injected values the gate takes: ``{sealer_home, exchange}`` when the env names a sealer, else ``{}``."""
    home = (os.environ if environ is None else environ).get(ENV) or None
    return {"sealer_home": home, "exchange": remote.exchange} if home else {}


def write_verdict(artifact: dict, **kwargs) -> str:
    """verdict.write_verdict with the configured sealer dial supplied; an explicit kwarg wins."""
    return verdict.write_verdict(artifact, **{**configured(), **kwargs})

"""host — the tool the system device publishes for "which box, which OS".

The os calls live HERE, in the system device, so a caller asks "which box" and never learns
whether the answer came from ``os.uname`` (absent on Windows) or ``platform.node``. Akien,
2026-11-21: "hostname should come from the system device." RULE 1 admits a reach into
system_rackmount only through a tool it publishes, so the two answers live in this published
module (charter beside it: published_by_device), not in rackmount.py (ticket 5ccc7f05c932).
"""
from __future__ import annotations

import platform   # never socket: nothing here may near the mesh


def host_name() -> str:
    """This box's name as the roster spells it: the short hostname, lowercased, never an IP."""
    return platform.node().split(".")[0].lower()


def os_id() -> str:
    """The OS family id: ``windows``, ``linux``, ``darwin``; the one place that asks the host."""
    return platform.system().lower()

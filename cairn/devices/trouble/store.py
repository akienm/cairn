"""Where the trouble store lives — the one answer, behind a door that imports nothing heavy.

Its own module because its callers stand outside the trouble component (base/transitions.py,
the operator inbox, two base probes) and the inspector's verdict path is one of them: asking
trouble.py for a path imported trouble/shim.py and, through base/shim.py, the bus client's
socket, so a sieve could reach a host (measured 2026-10-13, test_inspector_nexus.py). This
file imports the address door and nothing else, and trouble.py re-exports it, so the root is
spelled once. Declared in the charter's public_interface (RULE 1).
"""
from __future__ import annotations

from pathlib import Path

from cairn.tools.base.address import log_path


def store_root(roots: dict | None = None) -> Path:
    """Where the trouble store lives: ``log_path('cairn', 0, roots)/troubletickets``. Public,
    so every reader of the store asks here instead of naming the path (RULE 1)."""
    return log_path("cairn", 0, roots) / "troubletickets"

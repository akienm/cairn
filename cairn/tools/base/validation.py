"""validation.py — proof discovery and validation reading without cross-device imports.

The tester device owns proof execution and validation sealing. Other devices need
to READ those seals and DISCOVER proofs without importing the tester directly —
that would violate device isolation. This tool surfaces the tester's read-side
functions, the same pattern bus_client uses for bus access.

Tools can import from any device (the device_isolation sieve checks only
``cairn/devices/<X>/`` files importing ``cairn.devices.<Y>``). So the imports
here are legal; the callers in other devices import from this tool instead.
"""
from __future__ import annotations


def discover(targets):
    """Resolve CLI targets to proof files — ``**/proofs/test_*.py`` beneath each."""
    from cairn.devices.tester.cli import discover as _discover
    return _discover(targets)


def standing(proof_path):
    """Is this proof's code in proven-space RIGHT NOW?

    Returns ``{"proven": bool, "why": str, "seal": dict | None}``."""
    from cairn.devices.tester.validation_store import standing as _standing
    return _standing(proof_path)


def source_fingerprint(path):
    """One sha256 over every ``*.py`` under the component root."""
    from cairn.devices.tester.validation_store import source_fingerprint as _fp
    return _fp(path)


def run_proof(path, *, sink="none", caller="unknown"):
    """Run ONE proof and return its record. Persists nothing — the caller decides."""
    from cairn.devices.tester.device import TesterDevice
    return TesterDevice().run_proof(path, sink=sink, caller=caller)

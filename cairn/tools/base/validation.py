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


def source_fingerprint(path, *, closure=None):
    """One sha256 over what a proof proves — its import closure, or its component directory."""
    from cairn.devices.tester.validation_store import source_fingerprint as _fp
    return _fp(path, closure=closure)


def directory_fingerprint(root):
    """One sha256 over every ``*.py`` under ``root`` — the pre-closure recipe, explicit root."""
    from cairn.devices.tester.validation_store import directory_fingerprint as _dir
    return _dir(str(root))


def sealed_fingerprint_now(path, seal):
    """Re-take ``path``'s fingerprint under the recipe THIS seal was taken with.

    The one door for "has the code moved under this seal?". Every reader outside the tester
    comes through here rather than re-deriving the recipe, because the recipe now has two
    forms (closure and directory) and a reader that picks the wrong one reports drift that
    is not there. Which form applies is a property of the SEAL, not of the caller.
    """
    from cairn.devices.tester.validation_store import sealed_fingerprint_now as _now
    return _now(path, seal)


def latest_seal(path, *, artifact=False):
    """The most recent VALIDATION sealed for ``path``, or None if it has never been sealed.

    ``artifact=True`` addresses a thing with no ``proofs/`` directory — a concept-piece
    proved by people reading it — whose seal berths at ``<dir>/validations/<stem>.json``.
    Either way the address is DERIVED from the sealed thing, never chosen by the caller,
    which is what keeps intent and proof at one address (Law 5).
    """
    from cairn.devices.tester.validation_store import (
        read_validations, validations_path_for, validations_path_for_artifact)
    where = validations_path_for_artifact(str(path)) if artifact else validations_path_for(str(path))
    records = read_validations(path=where)
    return records[-1] if records else None


def run_proof(path, *, sink="none", caller="unknown"):
    """Run ONE proof and return its record. Persists nothing — the caller decides."""
    from cairn.devices.tester.device import TesterDevice
    return TesterDevice().run_proof(path, sink=sink, caller=caller)

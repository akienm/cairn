"""WATCHME probe: plaster-is-caught-not-argued.

Fires when the corrosion sieve has been live for 30+ commits touching
constraint-bearing artifacts and has never once fired. Clears when it has
fired at least once on a real weakening AND at least one firing was
dispositioned as a genuine catch.

This is a STUB — the probe is armed at the WATCHME crossing, not at build time.
The module must exist at this path for the emission gate to find it.
"""
from __future__ import annotations

from cairn.tools.base.probe import Probe

PROBE = Probe(
    object="plaster-is-caught-not-argued",
    carry="count of commits touching constraint-bearing artifacts since the sieve went live, count of firings, count of genuine catches",
    enough="at least one firing dispositioned as a genuine catch",
)

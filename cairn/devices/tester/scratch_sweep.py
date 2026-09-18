"""The scratch sweep the tester runs before every seal (ticket 201a37bf1613).

Every proof passes through the tester, so a seal is the one event on which a table that
outlived its process is dropped — no clock, no daemon (memory reaching-for-daemons-is-drift).
``store.sweep_scratch`` drops only what carries a ``cairn_scratch`` row whose minter is dead;
the count and the names ride the seal's evidence so a leaker is named, not counted.

THIS LIVES IN ITS OWN MODULE, NOT IN ``device.py``, BECAUSE THE INSPECTOR'S FIRE PATH REACHES
``device.py``: ``inspector.py -> cairn.tools.base.validation -> cairn.devices.tester.device``,
and nothing on that path may reach a database by import (``test_inspector_nexus``, the
``import_sieve`` over ``inspector._FIRE_PATH``). So the module that touches db_domain sits
one address aside, the two seal writers (``cli.py``, ``reseal.py``) call it and hand the
result to ``run_proof(scratch_sweep=...)``, and ``run_proof`` refuses to seal without one.
db_domain is the one cross-device import the ruling allows.
"""
from __future__ import annotations


def sweep() -> dict:
    """``{"dropped": n, "tables": [...]}``, or ``{"error": ...}`` when the store could not
    be reached — a stated failure, because a seal that says 'swept 0' over a store it never
    opened would be the hollow green Law 8 forbids."""
    try:
        from cairn.devices.db_domain import store
        tables: list[str] = []
        n = store.sweep_scratch(report=tables)
        return {"dropped": n, "tables": tables}
    except Exception as exc:  # noqa: BLE001 — recorded verbatim on the evidence
        return {"error": f"{type(exc).__name__}: {exc}"}

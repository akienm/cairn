"""A tiny PROVEN sensor method — the kind a driver wires. Its whole contract: read a
value and hand back a row. `proof_collect.py` is the proof that admits it to
proven-space; the ground_loop will run it only because that proof passed (Law 8)."""

from __future__ import annotations


def collect() -> dict:
    """Return one reading as a row (the shape db_domain stores). Deterministic so its
    proof can pin it."""
    return {"value": "42"}

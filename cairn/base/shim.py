"""BaseShim — the device-lifecycle base, at its Cairn-honest v0 minimum.

A shim sits between the rack and a device it manages. Every Cairn shim subclasses
this. Right now its whole job is the composition tooth: compose
``CoreValuesMixin`` so every shim carries CP1-CP6 structurally — you cannot be a
shim without the values (Law 2), enforced by proofs/test_composition.py. It also
pins the one thing every shim must answer for: which device it is the shim *of*.

DELIBERATELY NOT CARRIED YET (filed as an open edge, not faked):
  - The lifecycle contract (start / stop / restart / self-test / rollback in UU).
    Cairn's node has no ``RUNNING`` state and no ``block``/``halt`` — it rests in
    PROVED or LEARNING, neither terminal (MAP.md:832). Copying UU's lifecycle verbs
    down here now would reify a state model Cairn has replaced. The Cairn lifecycle
    contract lands with the state-machine physics, below.
  - **The one-loop primitive.** MAP.md:327 files it here, but the newer
    state-machine stone (MAP.md:832, ratified the same day) resolves it: the "one
    loop" is the state machine itself, its two rests are PROVED/LEARNING, and the
    executor is an operational-driver (candidate: ``ground_loop``). That primitive
    **waits on the emit-chokepoint** (MAP.md:884, the base-class spine step;
    ``CairnCommons/tickets/state-machine-physics.json``). Casting a UU-style
    ``ShimLoopThread`` daemon here now would be a hollow build (Law 8) — it would
    pin threading mechanics before Cairn's loop is designed. So the loop primitive
    is a tracked edge on that ticket, not code in this file yet.

Why BaseShim exists at all today, this thin: so the composition tooth has a real
class to bite on — "no shim can lack the values" is a claim about *this* base, and
it is only provable once this base exists (last session's filed open edge). The
lifecycle flesh arrives when the state machine gives it a shape to be honest about.

Kept import-light on purpose: no DB, no logging backend, no daemon threads.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cairn.base.core_values import CoreValuesMixin


class BaseShim(CoreValuesMixin, ABC):
    """Abstract base for every Cairn device shim.

    Composes ``CoreValuesMixin`` — every shim carries CP1-CP6 structurally (Law 2,
    enforced by proofs/test_composition.py). Pins ``device_id``: the device this
    shim is the shim of. The lifecycle contract and the one-loop primitive are
    filed open edges on state-machine-physics (see module docstring), not code
    here yet.
    """

    @property
    @abstractmethod
    def device_id(self) -> str:
        """The id of the device this shim manages — one shim per device."""

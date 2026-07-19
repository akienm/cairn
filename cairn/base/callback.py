"""Callback — the immutable "call X when this trigger is true", made a primitive.

ONE OF TWO SPECIES (converged with Akien 2026-07-18;
``CairnCommons/intentions/I-heartbeat-callbacks-and-bus.md``):

  - **Callback** (here) — *immutable, no workflow.* "Call X when this trigger is true."
    It carries no state of its own; because it is DECLARATION, it lives with the device's
    CODE (class-space — git, greppable, shareable), not in a store. Every recurring
    wake-up — an interval, a wall-clock time, data accumulated, a resource threshold, a
    proof going green — is a callback. One primitive for "call this again / on this
    trigger," used everywhere (even the question-nexus template's loop is a callback).
  - **Ticket** — *a workflow node: mutable, carries a state machine.* A DIFFERENT species,
    living where workflow-state lives (instance-space / the node store), not here. See
    ``CairnCommons/tickets/state-machine-physics.json``. ``LEARNING`` is a STATE; a callback
    is the WORKER a ``LEARNING`` node can SET. Do not mush the two into "a mutable ticket."

A TRIGGER IS ANYTHING THAT EVALUATES TO TRUE (Law 3, and the anti-reification made
structural). There is NO closed enum of trigger kinds — the shipped
``interval/date/quantity/state`` set was the reification this rework deletes. So a trigger
here is not a "kind" you name; it is a PREDICATE you pass: ``trigger(now, context) -> bool``.
A new signal is a new predicate, not a schema change. (The tell that produced the enum: CC
turns an open list of *examples* into a closed typed set — the fix is to keep it a callable.)

EVALUATED WHERE ITS DATA IS OWNED (Law 6 for triggers). A callback reading device-local
data has its predicate CLOSE OVER that device's own data, so the data never leaves — only
the wake-up (the poke) crosses the bus, never the raw value it tested. A callback reading
genuinely shared data (the passage of time) reads it from ``now`` / ``context``. The
primitive does not care which; it just calls the predicate. The ownership lives in how the
owning device BUILDS the closure — which is exactly where Law 6 says it belongs.

FIRING is stateless and fire-and-die: when the trigger is true, the callback's ``to`` /
``channel`` / ``body`` / ``why`` are posted to the bus (the shim does the posting — see
``cairn/base/shim.py``). Because a callback holds no state, its firing can be a separate,
short-lived process that sends the message and terminates (the process model; a filed edge
on the shim). The callback itself is just the immutable declaration of what to send when.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Callback:
    """An immutable "poke ``to`` when ``trigger`` is true." Frozen — it is a declaration, not
    a stateful worker; its fire-history (if any) lives on whatever fires it, never here.

    Fields:
      - ``why``     — the reason this callback exists (CP3 — a callback with no why is a defect).
      - ``trigger`` — the predicate ``(now, context) -> bool``. ANY callable that evaluates to
                      true; NOT a named kind. Closes over device-local data when the data is
                      owned by the firing device (Law 6), so only the poke crosses the bus.
      - ``to``      — the bus address to poke when the trigger fires.
      - ``channel`` — which of the target's channels to poke (default ``personal`` — the inbox
                      where a device is reached).
      - ``body``    — the payload of the poke. Static by design: it says *that* the line was
                      crossed, carrying no owned data it must not leak (Law 6).
    """

    why: str
    trigger: Callable[..., bool]
    to: str
    channel: str = "personal"
    body: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # CP1/CP3, at construction: a callback you cannot fire, or one with no reason, is a
        # defect caught at n=1 — not a resting state discovered when it silently never pokes.
        if not callable(self.trigger):
            raise TypeError("a callback's trigger must be callable — a trigger is anything that "
                            "evaluates to true, passed as a predicate, not named as a kind")
        if not self.why:
            raise ValueError("a callback carries a why (CP3) — the reason it will poke someone")
        if not self.to:
            raise ValueError("a callback carries a 'to' — the bus address it pokes when it fires")

    def fires(self, now, context: dict | None = None) -> bool:
        """Evaluate the trigger against the moment and the observed context. Pure — no side
        effect; the firing (the poke) is the shim's, so the decision stays testable as a table.
        Coerced to bool so a truthy predicate is honest about being a trigger."""
        return bool(self.trigger(now, context or {}))

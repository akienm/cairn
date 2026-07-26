"""Callback — the immutable "call X when this trigger is true", made a primitive.

ONE OF TWO SPECIES (converged with Akien 2026-07-18;
``CairnCommons/intentions-other/I-heartbeat-callbacks-and-bus.md``):

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

WHAT RIDES ALONG IS A CARRIER, NOT A FIXED SHAPE (Akien 2026-07-25). ``body`` alone says
only *that* a line was crossed. But a gate-watching callback usually wants to send the thing
that crossed — and how it must ride depends entirely on what the RECEIVER can process there:
a pointer, a deep copy, or a string rendering of the artifact in motion. Akien's example:
"call dave back with 'ticket detected at {gate} as {ticket}'". And the payload is not always
an artifact at all — something inside the inference proxy may send back a loop count over N.
These are designed to be that flexible.

So carriage gets the SAME treatment as the trigger, one paragraph up: a carrier is a
CALLABLE ``(context) -> dict``, evaluated at fire time — never a named kind, never a closed
enum. ``by_pointer`` / ``by_copy`` / ``by_text`` ship below because they have consumers; a
fourth carriage is a fourth function, not a schema change. (Same shape as the diagnostic
inspector's filters, deliberately — one idea, one spelling.)

LAW 6 STILL BINDS, AND MOVES TO THE AUTHOR. ``by_pointer`` remains the default and the
cheap, safe ride: only the address crosses, owned data stays home. ``by_copy`` and
``by_text`` are the owner's DELIBERATE choice to send owned data across, made where Law 6
says the decision belongs — in the owning device, as it builds the callback, exactly as the
trigger's closure already works. The primitive does not police it; it makes the choice
explicit and greppable instead of implicit.

A POKE PER CROSSING, NOT PER PULSE (Akien 2026-07-25, "so we need an anti-bounce?"). A
trigger is evaluated on every heartbeat pulse, so a condition that STAYS true — a CPU parked
at 91% — would poke on every pulse forever. That is a flood, and floods are how a diagnostic
surface turns into noise (the shrinking-footprint discipline; ``rackmount.py`` filed exactly
this and left it). So the default is: poke once when the trigger CROSSES false -> true, and
not again until it has gone false and crossed back. ``while_true=True`` opts back into
per-pulse poking, for the callback that genuinely means "keep telling me while this holds."

  The DECLARATION is here; the MEMORY is on the shim. A callback is frozen and holds no
  state — "its fire-history lives on whatever fires it, never here" — and that is exactly
  why crossing-detection cannot be implemented in this file. The shim remembers which
  declarations were true last pulse, keyed by ``identity`` below. Same split as the trigger:
  the callback declares, the firer evaluates.

  CROSSING IS NOT CHATTER. A value flapping across the line (89.9 / 90.1 / 89.9) produces a
  genuine crossing each time, so this does not damp it — that wants hysteresis or a hold-down
  window, and it is NOT built: no flapping signal has been measured yet, and damping one
  blind would be guessing at the width. Filed, with its why, on the bus-completion ticket.

FIRING is stateless and fire-and-die: when the trigger is true, the callback's ``to`` /
``channel`` / ``payload(context)`` / ``why`` are posted to the bus (the shim does the
posting — see ``cairn/base/shim.py``). Because a callback holds no state, its firing can be
a separate, short-lived process that sends the message and terminates (the process model; a
filed edge on the shim). The callback itself is just the immutable declaration of what to
send when — and now, in what form.
"""

from __future__ import annotations

import copy as _copy
from collections.abc import Callable
from dataclasses import dataclass, field


# ── the carriers: HOW the thing that crossed rides along ─────────────────────
#
# Each takes the fire-time ``context`` and returns a payload fragment merged over ``body``.
# Three because three have consumers (the three Akien named); a fourth is a fourth function.
# They read ``context`` and never mutate it — a carrier decides what to SEND, not what is.

def by_pointer(key: str = "ticket", *, as_: str = "pointer") -> Callable[[dict], dict]:
    """THE DEFAULT RIDE: only the address crosses; owned data stays home (Law 6). Use this
    unless the receiver genuinely cannot resolve a pointer."""
    def carrier(context: dict) -> dict:
        item = context.get(key)
        pointer = item.get("id") if isinstance(item, dict) else item
        return {as_: pointer}
    return carrier


def by_copy(key: str = "ticket", *, as_: str = "ticket") -> Callable[[dict], dict]:
    """A DEEP COPY of the artifact rides along — for a receiver that cannot come back and
    resolve a pointer. Deep, so the receiver can never reach back and mutate the original;
    the owner's deliberate choice to send owned data across (Law 6, made by the author)."""
    def carrier(context: dict) -> dict:
        return {as_: _copy.deepcopy(context.get(key))}
    return carrier


def by_text(template: str, *, as_: str = "text") -> Callable[[dict], dict]:
    """A STRING RENDERING of the artifact in motion — for a receiver whose only vocabulary is
    text (a human, a log line, a prompt). ``template`` is format-style over the context:
    ``by_text("ticket detected at {gate} as {ticket}")``. A key the context lacks renders as
    ``{missing:key}`` rather than raising — a poke must not be lost to a typo, and a visible
    hole in the text is the loud version (Law 7)."""
    class _Loud(dict):
        def __missing__(self, k):
            return "{missing:" + k + "}"

    def carrier(context: dict) -> dict:
        return {as_: template.format_map(_Loud(context))}
    return carrier


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
      - ``body``    — the STATIC part of the poke, known when the callback is declared.
      - ``carry``   — optional ``(context) -> dict``, evaluated at fire time: what rides
                      along, in the form the receiver can process. ANY callable; NOT a named
                      kind. ``by_pointer`` (the Law 6 default) / ``by_copy`` / ``by_text``
                      ship above. Absent, the poke says only *that* the line was crossed.
      - ``while_true`` — poke on EVERY pulse the trigger holds true. Default ``False``: poke
                      once at the CROSSING (see below). The declaration lives here; the
                      memory that makes it work lives on the shim, where state belongs.
    """

    why: str
    trigger: Callable[..., bool]
    to: str
    channel: str = "personal"
    body: dict = field(default_factory=dict)
    carry: Callable[[dict], dict] | None = None
    while_true: bool = False

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
        if self.carry is not None and not callable(self.carry):
            raise TypeError("a callback's carry must be callable — carriage is a function of the "
                            "fire-time context, not a named kind (see by_pointer/by_copy/by_text)")

    @property
    def identity(self) -> tuple:
        """What makes this the SAME declaration across pulses — so a shim can remember whether
        it was true last time. ``callbacks()`` may rebuild its list every pulse, so object
        identity is not it; the declaration's own content is. Deliberately excludes ``body`` /
        ``carry``: a callback is "poke THIS target for THIS reason", and what rides along does
        not make it a different standing watch."""
        return (self.to, self.channel, self.why)

    def fires(self, now, context: dict | None = None) -> bool:
        """Evaluate the trigger against the moment and the observed context. Pure — no side
        effect; the firing (the poke) is the shim's, so the decision stays testable as a table.
        Coerced to bool so a truthy predicate is honest about being a trigger."""
        return bool(self.trigger(now, context or {}))

    def payload(self, context: dict | None = None) -> dict:
        """What this poke actually sends: the static ``body``, with the carrier's fire-time
        fragment merged OVER it (the moment beats the declaration — a stale static value must
        never mask what was measured at the gate). ``body`` is copied, never mutated: the
        callback is frozen, and a declaration that drifted per firing would stop being one.

        A carrier that RAISES does not silently drop the poke (Law 7, and Akien's rule that
        nothing fails quietly): the payload goes out carrying ``carry_failed`` — the poke
        still lands, and it lands saying it is incomplete."""
        out = dict(self.body)
        if self.carry is None:
            return out
        try:
            fragment = self.carry(context or {})
        except Exception as exc:  # noqa: BLE001 — a broken carrier must not swallow the poke
            return {**out, "carry_failed": f"{type(exc).__name__}: {exc}"}
        if not isinstance(fragment, dict):
            return {**out, "carry_failed": f"carrier returned {type(fragment).__name__}, not a dict"}
        out.update(fragment)
        return out

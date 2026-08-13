"""Probe — the immutable "call X when this trigger is true", made a primitive.

ONE OF TWO SPECIES (converged with Akien 2026-07-18;
``CairnCommons/intentions-not-beside-code/I-heartbeat-probes-and-bus.md``):

  - **Probe** (here) — *immutable, no workflow.* "Call X when this trigger is true."
    It carries no state of its own. Every recurring wake-up — an interval, a wall-clock
    time, data accumulated, a resource threshold, a proof going green — is a probe. One
    primitive for "call this again / on this trigger," used everywhere (even the
    question-nexus template's loop is a probe).
  - **Ticket** — *a workflow node: mutable, carries a state machine.* A DIFFERENT species,
    living where workflow-state lives (instance-space / the node store), not here. See
    ``CairnCommons/tickets/state-machine-physics.json``. A ``WATCHME`` node EMITS a probe;
    the probe is not the node and holds none of its state. Do not mush the two into "a
    mutable ticket."

WHERE A PROBE BERTHS (ruled by Akien 2026-07-30, ticket ``watchme-emits-a-probe``). An
earlier version of this header argued class-space "because it is DECLARATION, it lives with
the device's CODE." That argument is DELETED and recorded as a wrong turn, because a probe
is not the declaration: the DECLARATION is the intent, the intent is on the TICKET, and the
probe is an EXPRESSION of that intent (when this happens, call this, with this).

  THE RULE: A PROBE IS COMPILED INTENT — EXACTLY AS CODE IS COMPILED INTENT — AND IT
  BERTHS WITH WHAT IT WATCHES, NOT WITH THE TICKET IT WAS COMPILED FROM.

So a probe's folder is routinely nowhere near its ticket, and probes CLUSTER BY SUBJECT: a
device's time-related watchers share a folder in that device, as do the watchers over one
piece of code. Three destinations, chosen by the subject:

  (i)   WATCHES THE TOOLS -> IN THE REPO, beside the monitored code, CHECKED IN. Someone
        who installs this repo needs these to have working tools — they are part of what
        the tool IS. (A shipped probe is therefore a HOST-SEAM in shape: it must ARM ITSELF
        on a host it has never seen. Coupled to ticket ``host-seam-installer``, not
        sequential with it.)
  (ii)  WATCHES THIS INSTANCE'S RUNTIME, or is a standing ask from this user ->
        instance-space, e.g. ``~/.cairn/devices/<device>/<n>/<subject>/probes_for_.../``.
  (iii) WATCHES A DOWNSTREAM PROJECT -> that project's own repo, because that project's
        ticket workflow lives there — and ITS user-specific learning points at that user's
        own runtime path, outside both of our roots entirely.

  WORKED, because a rule that cannot place a real probe is prose. (1) THIS MODULE'S OWN
  WATCHER — it watches whether the WATCHME machinery in ``cairn/tools/base`` actually fires, i.e.
  it watches the TOOLS — so it berths at ``cairn/tools/base/probes/``, checked in, nowhere near
  its ticket in the commons. (2) ``system_rackmount`` LOOKS like a counter-example and is
  not: it checks in no probe at all. ``subscribe()`` is a FACTORY that compiles a probe from
  a caller's value at runtime, and the probes it compiles watch THIS host's resources —
  subject (ii) — so they live in this instance's device state and are checked in nowhere.
  The rule places probes; a factory for probes is ordinary code and places by the ordinary
  test. No exception clause was needed for either.

DELIBERATE EXCEPTION TO LAW 5, recorded so it is not "fixed" later: intent, voyage and
proofs share an address, but a probe is none of the three — it is an INSTRUMENT, and an
instrument berths at what it measures. A probe far from its ticket reads as drift and is
not. This EXTENDS the three-roots test rather than breaking it: CLAUDE.md asks "does the
intention have ONE code address?"; for a compiled probe the question becomes "what does it
WATCH, and where does THAT live?" — same question, different subject.

A TRIGGER IS ANYTHING THAT EVALUATES TO TRUE (Law 3, and the anti-reification made
structural). There is NO closed enum of trigger kinds — the shipped
``interval/date/quantity/state`` set was the reification this rework deletes. So a trigger
here is not a "kind" you name; it is a PREDICATE you pass: ``trigger(now, context) -> bool``.
A new signal is a new predicate, not a schema change. (The tell that produced the enum: CC
turns an open list of *examples* into a closed typed set — the fix is to keep it a callable.)

EVALUATED WHERE ITS DATA IS OWNED (Law 6 for triggers). A probe reading device-local
data has its predicate CLOSE OVER that device's own data, so the data never leaves — only
the wake-up (the poke) crosses the bus, never the raw value it tested. A probe reading
genuinely shared data (the passage of time) reads it from ``now`` / ``context``. The
primitive does not care which; it just calls the predicate. The ownership lives in how the
owning device BUILDS the closure — which is exactly where Law 6 says it belongs.

WHAT RIDES ALONG IS A CARRIER, NOT A FIXED SHAPE (Akien 2026-07-25). ``body`` alone says
only *that* a line was crossed. But a gate-watching probe usually wants to send the thing
that crossed — and how it must ride depends entirely on what the RECEIVER can process there:
a pointer, a deep copy, or a string rendering of the artifact in motion. Akien's example:
"call dave back with 'ticket detected at {gate} as {ticket}'". And the payload is not always
an artifact at all — something inside the inference proxy may send back a loop count over N.
These are designed to be that flexible.

So carriage gets the SAME treatment as the trigger, one paragraph up: a carrier is a
CALLABLE ``(context) -> dict``, evaluated at fire time — never a named kind, never a closed
enum. ``by_pointer`` / ``by_copy`` / ``by_text`` ship below; a fourth carriage is a fourth
function, not a schema change. (Same shape as the diagnostic inspector's filters,
deliberately — one idea, one spelling.)

  "BECAUSE THEY HAVE CONSUMERS" WAS A CLAIM, AND IT MEASURED FALSE (2026-08-05, Law 3 on
  this file's own prose). Counted across the corpus: ``by_copy`` had ZERO live consumers,
  and every one of the seven live ``carry=`` closures was hand-rolled — seven private
  functions each shipping a bare ticket id under the same key, which is seven
  re-derivations of one rule (Law 1's defect) and the concrete registry-in-disguise the
  ruling below kills. The three carriers were the design's guess at what would be needed,
  not a count of what was.

AND THE POINTER IS A FILE PATH (Akien, ruled 2026-08-05 —
``CairnCommons/decisions/2026-08-05-the-file-path-is-the-link-rescoped.json``): *"the
carriers are all files. so the file path is the link."* The filesystem is the index and no
receiver resolves anything, so an id — which obliges a receiver to look something up — is
refused as a pointer and rendered as a visible hole. See ``as_a_path``. ``by_copy`` narrows
in the same act to a receiver that genuinely cannot read that filesystem; a copy sent to a
receiver that can is a stale snapshot of a thing still moving.

LAW 6 STILL BINDS, AND MOVES TO THE AUTHOR. ``by_pointer`` remains the default and the
cheap, safe ride: only the address crosses, owned data stays home. ``by_copy`` and
``by_text`` are the owner's DELIBERATE choice to send owned data across, made where Law 6
says the decision belongs — in the owning device, as it builds the probe, exactly as the
trigger's closure already works. The primitive does not police it; it makes the choice
explicit and greppable instead of implicit.

A POKE PER CROSSING, NOT PER PULSE (Akien 2026-07-25, "so we need an anti-bounce?"). A
trigger is evaluated on every heartbeat pulse, so a condition that STAYS true — a CPU parked
at 91% — would poke on every pulse forever. That is a flood, and floods are how a diagnostic
surface turns into noise (the shrinking-footprint discipline; ``rackmount.py`` filed exactly
this and left it). So the default is: poke once when the trigger CROSSES false -> true, and
not again until it has gone false and crossed back. ``while_true=True`` opts back into
per-pulse poking, for the probe that genuinely means "keep telling me while this holds."

  The DECLARATION is here; the MEMORY is on the shim. A probe is frozen and holds no
  state — "its fire-history lives on whatever fires it, never here" — and that is exactly
  why crossing-detection cannot be implemented in this file. The shim remembers which
  declarations were true last pulse, keyed by ``identity`` below. Same split as the trigger:
  the probe declares, the firer evaluates.

  CROSSING IS NOT CHATTER. A value flapping across the line (89.9 / 90.1 / 89.9) produces a
  genuine crossing each time, so this does not damp it — that wants hysteresis or a hold-down
  window, and it is NOT built: no flapping signal has been measured yet, and damping one
  blind would be guessing at the width. Filed, with its why, on the bus-completion ticket.

AND IT CAN SAY WHEN IT HAS GATHERED ENOUGH (ticket ``watchme-emits-a-probe``, 2026-07-30).
A ``WATCHME`` ticket CREATES a probe to gather efficacy data for its own intention, and a
gatherer with no stopping condition is a watcher that runs forever — the standing cost the
shrinking-footprint discipline exists to refuse. So ``enough`` is a THIRD open predicate,
spelled exactly like ``trigger`` and ``carry``: ``enough(context) -> bool``, no enum of
condition kinds. It is asked ONLY AFTER A FIRE, because a probe that has not fired has
gathered nothing; a probe wanting to retire on something other than its own yield is a
different declaration and grows when one is measured.

  CLEARED IS NOT RE-ARMED, and the two must never read alike. RE-ARMED is the anti-bounce
  resting state: the trigger went false, the watch STANDS, and the next crossing pokes.
  CLEARED is terminal: enough was gathered and this declaration is retired — the shim will
  not fire it again even if the trigger crosses. The memory for both lives on the shim
  (this file is frozen and holds no state), and the shim reports them under DIFFERENT
  reasons so a tooth — and an operator reading a pulse record — can tell which happened.

FIRING is stateless and fire-and-die: when the trigger is true, the probe's ``to`` /
``channel`` / ``payload(context)`` / ``why`` are posted to the bus (the shim does the
posting — see ``cairn/tools/base/shim.py``). Because a probe holds no state, its firing can be
a separate, short-lived process that sends the message and terminates (the process model; a
filed edge on the shim). The probe itself is just the immutable declaration of what to
send when — and now, in what form.

  THE ONE DELIBERATE SURVIVAL OF THE OLD WORD. Programmatically, that post IS a **callback**:
  the shim holds a reference and invokes it when the trigger crosses. The word is correct
  for the PLUMBING and is kept here on purpose, once, so a later reader can tell a survivor
  from a straggler. What it stopped being (Akien 2026-07-30) is the NAME OF THE CONCEPT:
  functionally this thing observes a condition and reports what it saw, which is a probe.
  Anywhere else in authored space, "callback" is a straggler from before the rename.
"""

from __future__ import annotations

import copy as _copy
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePath

# Where a staged ticket berths. The three roots are Cairn's physics (CLAUDE.md), so this is
# derived from where THIS file sits rather than configured: cairn/tools/base/probe.py ->
# ~/dev/src/cairn -> its sibling ~/dev/src/CairnCommons. An override rides `owning_ticket`'s
# keyword so a proof can build a corpus without writing into the live commons.
_TICKETS = Path(__file__).resolve().parents[3].parent / "CairnCommons" / "tickets"


# ── the carriers: HOW the thing that crossed rides along ─────────────────────
#
# Each takes the fire-time ``context`` and returns a payload fragment merged over ``body``.
# Three because three have consumers (the three Akien named); a fourth is a fourth function.
# They read ``context`` and never mutate it — a carrier decides what to SEND, not what is.

def as_a_path(item) -> str:
    """The ONE self-resolving rendering of a pointer: a file path (Akien 2026-08-05, ruling
    ``the-file-path-is-the-link``). *"The carriers are all files. So the file path is the
    link."*

    A ``Path`` renders as itself; a ``str`` renders as itself; a dict renders from its
    ``path`` key. A dict carrying only an ``id`` — which is what this carrier shipped until
    today — renders as a VISIBLE HOLE, spelled exactly like ``by_text``'s missing key,
    because that is the failure the ruling names: an id obliges the receiver to resolve it,
    and a resolver over ids is a registry in disguise (``no-enforcer-gated-ownership``).
    Loud rather than fatal: the poke still lands, and it lands saying what it could not
    carry (Law 7)."""
    if isinstance(item, dict):
        for k in ("path", "file", "address"):
            if isinstance(item.get(k), (str, PurePath)) and str(item[k]).strip():
                return str(item[k])
        ident = item.get("id")
        return ("{unresolvable:" + str(ident) + " — a pointer is a FILE PATH (ruled "
                "2026-08-05); an id obliges the receiver to resolve it, and that resolver "
                "is a registry in disguise}")
    if isinstance(item, PurePath):
        return str(item)
    return item


def owning_ticket(name: str, *, tickets_root=None) -> str:
    """THE PATH OF THE TICKET A PROBE WAS COMPILED FROM — the one thing every live probe in
    this corpus wanted to say, said once.

    MEASURED 2026-08-05: all seven live ``carry=`` closures hand-rolled the same line,
    ``"ticket": _TICKET``, over a module constant holding a bare id
    (``intent-becomes-a-learning-block``, ``logger-for-bash``, ``engine-runs-one-block``,
    …). Seven re-derivations of one rule is Law 1's defect, and shipping the id rather than
    the address is exactly what Akien's ruling names: the receiver had to know where tickets
    live before it could open one.

    A MISSING TICKET IS A VISIBLE HOLE NAMING THE PATH IT LOOKED AT, not a silent string.
    A ticket migrates — CLAUDE.md: it stages in the commons and moves beside the code to
    become that component's ``history`` — so a probe outliving its ticket's berth is a
    normal event, and the poke that says *where it looked* is the one an operator can act
    on (Law 7, and the complete-diagnostic rule: everything needed to resolve it, first
    report).

    This is NOT the resolver the ruling refuses. It runs in the SENDER, once, at fire time,
    inside the device that already knows which ticket it was compiled from; what crosses
    the bus is the finished path. A resolver is what a RECEIVER would have to run.
    """
    root = PurePath(tickets_root) if tickets_root is not None else _TICKETS
    path = Path(root) / f"{name}.json"
    if path.exists():
        return str(path)
    return ("{unresolvable:" + str(path) + " — the owning ticket is not at this address; it "
            "has migrated beside its code as history, or the name drifted}")


def by_pointer(key: str = "ticket", *, as_: str = "pointer") -> Callable[[dict], dict]:
    """THE DEFAULT RIDE: only the address crosses; owned data stays home (Law 6). Use this
    unless the receiver genuinely cannot resolve a pointer.

    AND THE ADDRESS IS A FILE PATH — see ``as_a_path``. The filesystem is the index, so the
    receiver opens what it was handed and resolves nothing. This is Law 5 taken literally:
    intent, voyage and proofs share an ADDRESS, and a path is that address said out loud."""
    def carrier(context: dict) -> dict:
        return {as_: as_a_path(context.get(key))}
    return carrier


def by_copy(key: str = "ticket", *, as_: str = "ticket") -> Callable[[dict], dict]:
    """A DEEP COPY of the artifact rides along. Deep, so the receiver can never reach back
    and mutate the original; the owner's deliberate choice to send owned data across (Law 6,
    made by the author).

    NARROWED 2026-08-05 BY THE SAME RULING, and the narrowing is the whole of what is left
    of it: *"by_copy narrows to a receiver that cannot read that filesystem, else it goes."*
    Every carrier in this system rides a file, so a receiver sharing the filesystem already
    has the artifact — the copy buys it nothing and costs it a stale snapshot of something
    that is still moving. MEASURED at the ruling: zero live consumers. It survives for the
    receiver on the other side of a boundary the path cannot cross (another host, a prompt,
    a process with no read access), and a use with a same-filesystem receiver is a defect,
    not a preference."""
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
class Probe:
    """An immutable "poke ``to`` when ``trigger`` is true." Frozen — it is a declaration, not
    a stateful worker; its fire-history (if any) lives on whatever fires it, never here.

    Fields:
      - ``why``     — the reason this probe exists (CP3 — a probe with no why is a defect).
      - ``trigger`` — the predicate ``(now, context) -> bool``. ANY callable that evaluates to
                      true; NOT a named kind. Closes over device-local data when the data is
                      owned by the firing device (Law 6), so only the poke crosses the bus.
      - ``to``      — the bus address to poke when the trigger fires.
      - ``channel`` — which of the target's channels to poke (default ``personal`` — the inbox
                      where a device is reached).
      - ``body``    — the STATIC part of the poke, known when the probe is declared.
      - ``carry``   — optional ``(context) -> dict``, evaluated at fire time: what rides
                      along, in the form the receiver can process. ANY callable; NOT a named
                      kind. ``by_pointer`` (the Law 6 default) / ``by_copy`` / ``by_text``
                      ship above. Absent, the poke says only *that* the line was crossed.
      - ``while_true`` — poke on EVERY pulse the trigger holds true. Default ``False``: poke
                      once at the CROSSING (see below). The declaration lives here; the
                      memory that makes it work lives on the shim, where state belongs.
      - ``enough``  — optional ``(context) -> bool``, asked ONLY AFTER A FIRE: "have I
                      gathered enough?" True retires this declaration for good (CLEARED —
                      not the anti-bounce re-arm; see above). ANY callable; NOT a named
                      kind. Absent, the probe is a standing watch with no end, which is a
                      legitimate declaration and must stay the default so no existing probe
                      acquires a stopping condition it never asked for.
      - ``horizon`` — optional positive int: HOW MANY PULSES THIS WATCH MAY STAND WITHOUT
                      EVER HAVING FIRED before its own silence is a finding. Absent, the
                      probe is a watch with no horizon — legitimate, and the default for
                      exactly the reason ``enough`` defaults to None: no existing probe may
                      acquire a deadline it never declared.

    THE HORIZON, AND WHY IT IS A DECLARATION AND NOT A SWEEP (ticket
    ``watchme-emits-a-probe`` falsifier clause (2), 2026-07-30). The clause: *"A probe is
    armed and never fires, and nothing is loud about it — a watcher emitted into a heartbeat
    nobody runs learns nothing while LOOKING like learning."* That is this design's own way
    of re-committing the forced-and-ungated failure it was built to kill: a summons carried by
    everybody and satisfied by nobody, one level up. So the horizon is the number the shim
    measures silence against, and it is declared HERE beside the trigger — the only place
    that knows what "too long" means for this particular question.

    Counted in PULSES, not seconds, and that is the whole point: a new clock, scheduler or
    registry sweep for probes is bounded OUT (a probe fires where the subject already
    fires). The shim already counts its own pulses, so silence is measured against the beat
    that was going to happen anyway — the same event-not-poll rule the rest of the system
    keeps. A probe held past its horizon surfaces at ``BaseShim.overdue()`` and in every
    pulse-record under its own key; the shim holds the counting, because a Probe is frozen
    and holds no state.
    """

    why: str
    trigger: Callable[..., bool]
    to: str
    channel: str = "personal"
    body: dict = field(default_factory=dict)
    carry: Callable[[dict], dict] | None = None
    while_true: bool = False
    enough: Callable[[dict], bool] | None = None
    horizon: int | None = None

    def __post_init__(self) -> None:
        # CP1/CP3, at construction: a probe you cannot fire, or one with no reason, is a
        # defect caught at n=1 — not a resting state discovered when it silently never pokes.
        if not callable(self.trigger):
            raise TypeError("a probe's trigger must be callable — a trigger is anything that "
                            "evaluates to true, passed as a predicate, not named as a kind")
        if not self.why:
            raise ValueError("a probe carries a why (CP3) — the reason it will poke someone")
        if not self.to:
            raise ValueError("a probe carries a 'to' — the bus address it pokes when it fires")
        if self.carry is not None and not callable(self.carry):
            raise TypeError("a probe's carry must be callable — carriage is a function of the "
                            "fire-time context, not a named kind (see by_pointer/by_copy/by_text)")
        if self.enough is not None and not callable(self.enough):
            raise TypeError("a probe's enough must be callable — an enough-condition is a "
                            "predicate over the fire-time context, not a named kind or a count")
        # A horizon of 0 or a negative one is a probe that is overdue before it is ever
        # evaluated — that reads as loud-about-everything, which is the same as loud about
        # nothing (Law 7 cuts both ways). Refused at n=1 rather than discovered as noise.
        if self.horizon is not None and (not isinstance(self.horizon, int)
                                         or isinstance(self.horizon, bool)
                                         or self.horizon < 1):
            raise ValueError("a probe's horizon is a positive whole number of PULSES it may "
                             "stand without ever firing before its silence is a finding — "
                             "omit it for a watch with no horizon, never 0 or a duration")

    @property
    def identity(self) -> tuple:
        """What makes this the SAME declaration across pulses — so a shim can remember whether
        it was true last time. ``probes()`` may rebuild its list every pulse, so object
        identity is not it; the declaration's own content is. Deliberately excludes ``body`` /
        ``carry``: a probe is "poke THIS target for THIS reason", and what rides along does
        not make it a different standing watch."""
        return (self.to, self.channel, self.why)

    def fires(self, now, context: dict | None = None) -> bool:
        """Evaluate the trigger against the moment and the observed context. Pure — no side
        effect; the firing (the poke) is the shim's, so the decision stays testable as a table.
        Coerced to bool so a truthy predicate is honest about being a trigger."""
        return bool(self.trigger(now, context or {}))

    def gathered_enough(self, context: dict | None = None) -> bool:
        """Has this probe gathered enough to retire? Pure — no side effect; the CLEARING is the
        shim's, so the decision stays testable as a table (same split as ``fires``). No
        ``enough`` declared means a standing watch: the answer is always False, never a
        default stopping condition nobody declared.

        An ``enough`` that RAISES answers False and the raise is the caller's to record: a
        broken stopping condition must leave the watch STANDING rather than silently retiring
        it (Law 7 — the failure that hides is a watcher that quietly stopped watching)."""
        if self.enough is None:
            return False
        return bool(self.enough(context or {}))

    def payload(self, context: dict | None = None) -> dict:
        """What this poke actually sends: the static ``body``, with the carrier's fire-time
        fragment merged OVER it (the moment beats the declaration — a stale static value must
        never mask what was measured at the gate). ``body`` is copied, never mutated: the
        probe is frozen, and a declaration that drifted per firing would stop being one.

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

"""Probe — "when this EVENT happens, send this to that consumer", made a primitive.

THE INTENTION (Akien, 2026-09-30):
  - *"all probes respond to events."* A probe fires where a thing happens — a door
    writing, a ticket crossing a gate, a message arriving. Never on the heartbeat, never on
    a clock. The only clock users in the system are Akien's away windows and sleep (see the
    ground loop charter); a probe is neither.
  - *"if it's not consumed, it's trash."* A probe exists only because a consumer needs its
    data and USES it — code that reads it and acts, not a mailbox or a recorder nobody
    reads. Build the receiver first, then the sender.

A probe is immutable and holds no state; it is a different species from a TICKET (a
mutable workflow node). A ticket's WATCHME creates a probe; the probe carries no authority
and never moves the ticket (Law 6).

It berths WITH WHAT IT WATCHES, not with the ticket that made it (ruled 2026-07-30,
``watchme-emits-a-probe``).

Mechanics this module keeps:
  - a trigger is a predicate ``(now, context) -> bool`` — no closed enum of kinds;
  - a carrier is a callable ``(context) -> dict``; the pointer it carries is a FILE PATH
    (ruled 2026-08-05: *"the carriers are all files. so the file path is the link."*);
  - it is evaluated where its data is owned, so only the poke crosses the bus.

Where code below still speaks of pulses, per-pulse evaluation or crossing memory on the
shim, it is the old clock-driven shape awaiting removal, not the design.
"""

from __future__ import annotations

import copy as _copy
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePath

# Where a staged ticket berths. The three roots are Cairn's physics (CLAUDE.md), so this is
# derived from where THIS file sits rather than configured: cairn/tools/base/probe.py ->
# ~/dev/src/cairn -> its sibling ~/dev/src/CairnCommons. An override rides `owning_ticket`'s
# keyword so a proof can build a corpus without writing into the live commons.
_TICKETS = Path(__file__).resolve().parents[3].parent / "CairnCommons" / "tickets"


def _pulse(context) -> dict:
    """THE CALLER'S CONTEXT, and a fresh one only when there genuinely is none.

    ``fires``, ``payload`` and ``gathered_enough`` each spelled this ``context or {}``, which
    is correct for ``None`` and WRONG FOR AN EMPTY DICT: ``{}`` is falsy, so a shim handing the
    same empty context to all three predicates of one firing probe had each of them silently
    given a DIFFERENT dict. Nothing downstream could tell — the old convention only ever READ
    the context, so three empty dicts and one empty dict answer identically. It surfaced the
    moment ``once`` started writing into it (2026-09-07): the memo went into a dict the next
    predicate never saw, and one firing probe derived its survey three times exactly as before.

    THE POINT IS OWNERSHIP, not thrift. The context belongs to whoever is running the pulse;
    a probe substituting its own is a peer quietly refusing the one that was passed (Law 6),
    and here that made a shared-per-pulse memo unimplementable from the outside."""
    return context if isinstance(context, dict) else {}


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
    # THE ONE LOCATOR (ticket 2516e958a6dd, 2026-09-15). This used to re-derive the lookup
    # with a reversed glob — ``*-<name>.json``, the id on the wrong side — which holed every
    # probe naming its ticket by hex id: 9 of 84 arguments across probes/*.py, 10 disagreements
    # with ``ticket_path``. The import is lazy because chain imports base at module top.
    from cairn.tools.chain.grammar import ticket_path
    found = ticket_path(name, tickets_dir=str(root))
    if found:
        return found
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


_TICKET_ID_SHAPE = re.compile(r"[0-9a-f]{12}")
_NO_FINDING = "the probe reads its ticket's falsifier as failing and its carry names no finding"


def watch_carry(ticket_id: str, carry: Callable[[dict], dict] | None = None, *,
                fails: Callable[[object, dict], bool] | None = None,
                holds: Callable[[dict], bool] | None = None) -> Callable[[dict], dict]:
    """The carry for a probe whose consumer is harbor_master's ``watch`` verb: the probe's own
    carry, plus ``{ticket, holds, finding}`` stated against ITS ticket's falsifier (835b5736bf2b
    D2; the verb and its contract are a88d6a368cfb's). Exactly one predicate says how:

      - ``fails`` — trigger-shaped ``(now, context) -> bool``, TRUE when the falsifier is
        failing. Most probes already have one: their trigger.
      - ``holds`` — ``(context) -> bool``, TRUE when the falsifier holds. For a probe whose
        trigger means "speak", not "something is wrong" — a door that got a caller, a dial that
        moved — inverting the trigger would send a succeeding ticket to FIXME.

    The rule lives here once, not in every carry (Law 1). The address ``owning_ticket`` ships
    (the 2026-08-05 ruling) still rides, as ``ticket_path``: ``ticket`` is the 12-hex id because
    the receiver moves tickets by id. A carry or predicate that raises reads as ``holds False``
    with the raise as the finding — a broken probe is a broken WATCHME, and a raise that
    vanished would be a green nobody measured (Law 7)."""
    if not isinstance(ticket_id, str) or not _TICKET_ID_SHAPE.fullmatch(ticket_id):
        raise ValueError(f"watch_carry needs a ticket's 12-hex id, not {ticket_id!r}")
    if callable(fails) == callable(holds):
        raise TypeError("watch_carry takes exactly one of fails= or holds=")

    def carrier(context: dict) -> dict:
        finding = ""
        try:
            out = dict(carry(context)) if carry else {}
        except Exception as exc:  # noqa: BLE001
            out, broke = {}, f"the probe's carry raised: {type(exc).__name__}: {exc}"
        else:
            broke = ""
        if "ticket" in out:
            out["ticket_path"] = out.pop("ticket")
        if broke:
            held, finding = False, broke
        else:
            try:
                held = (not bool(fails(None, context))) if fails else bool(holds(context))
            except Exception as exc:  # noqa: BLE001
                held = False
                finding = (f"the probe's {'fails' if fails else 'holds'} predicate raised: "
                           f"{type(exc).__name__}: {exc}")
            if not finding:
                said = out.get("finding")
                finding = said if isinstance(said, str) else ""
        if not held and not finding.strip():
            finding = _NO_FINDING
        return {**out, "ticket": ticket_id, "holds": held, "finding": finding}
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
    verb: str = ""
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
        return bool(self.trigger(now, _pulse(context)))

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
        return bool(self.enough(_pulse(context)))

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
            fragment = self.carry(_pulse(context))
        except Exception as exc:  # noqa: BLE001 — a broken carrier must not swallow the poke
            return {**out, "carry_failed": f"{type(exc).__name__}: {exc}"}
        if not isinstance(fragment, dict):
            return {**out, "carry_failed": f"carrier returned {type(fragment).__name__}, not a dict"}
        out.update(fragment)
        return out


# ── ONE SURVEY PER PULSE ─────────────────────────────────────────────────────

def once(context: dict | None, key: str, compute: Callable[[], object]):
    """The probe's survey, computed ONCE for the pulse that is asking.

    THE MEASUREMENT THAT BORE IT (2026-09-07, ticket 9579a6f9cec6). Every probe in the corpus
    is written ``s = context.get("survey") or survey()`` — a convention that reads as though
    the pulse hands the survey down. NOTHING HAS EVER POPULATED THAT CONTEXT: ``beat`` does
    ``context = context or {}`` and ``__main__`` passes none, so all 164 call sites take the
    ``or`` branch on every beat. That alone is Law 1's defect on a 60-second clock, and it is
    tripled by the shim's own shape: a probe that FIRES is asked three times — ``fires``, then
    ``payload`` -> carry, then ``gathered_enough`` -> enough — and each one re-derives the
    whole survey from scratch. 27 of 78 probes fired. Measured beat: 104.8s, of which trigger
    57.5s, carry 24.0s, enough 22.6s, and 0.7s for everything the loop itself does.

    THE WIRING WAS ALREADY THERE, which is why this is a helper and not a rework. ``on_pulse``
    passes ONE context object to ``fires``, ``_fire``/``payload`` and ``gathered_enough`` for
    the same probe, and ``beat`` passes one to every shim — so a memo written into it is
    exactly a per-beat memo, and it dies when the beat does. The gap was never the plumbing;
    it was that the convention only ever READ.

    THE EXPLICIT KEY, AND WHY IT IS NOT DERIVED FROM ``compute``. Hand-injection is a live
    seam — proofs and ``__main__`` blocks pass ``{"survey": <a synthetic one>}`` to drive a
    branch without building the world — so ``key`` names the slot a caller can still fill, and
    an injected value WINS. That makes this a strict superset of the line it replaces: the
    same answers, the same seam, computed once instead of three times. The memo itself berths
    under ``_once`` and is keyed by ``compute``'s module and qualname on top of ``key``, so two
    probes both spelling their slot ``"survey"`` — and there are 24 of them — cannot be served
    each other's world.

    A RAISE IS NOT MEMOIZED, deliberately: a survey that blew up is not an answer, and caching
    one would turn a transient read failure into a pulse-long lie. It propagates to the caller,
    where the shim's per-probe isolation already records it loudly (Law 7)."""
    context = context if isinstance(context, dict) else {}
    injected = context.get(key)
    if injected:
        return injected
    memo = context.setdefault("_once", {})
    slot = (getattr(compute, "__module__", "?"), getattr(compute, "__qualname__", repr(compute)), key)
    if slot not in memo:
        memo[slot] = compute()
    return memo[slot]

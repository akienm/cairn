"""DiagnosticBase — the transition-grade emission mechanism every device inherits.

Cairn's evidence today is OUTCOME-grade: a VALIDATION says what PASSED and why; a journey
says what happened across devices. What was missing is the TRANSITION-grade surface — the
one that would have spoken when ``system_rackmount`` went red 2/5 *silently* (no assertion,
no trace). This is that surface: at a GATE CONTACT — a state transition or a boundary
crossing — a device sends home a microsecond-stamped record of what crossed, so a red
(especially a silent one) has a readable trace to review. Law 3 (nothing known until
measured — the emission IS the measurement) and Law 7 (loud at the diagnostic surface).

WHERE IT LIVES — the base class, inherited by everybody, the way CP1-CP6 are inherited via
``CoreValuesMixin``. ``BaseDevice`` composes this mixin, so every device carries ``emit()``
structurally: you cannot be a device without being able to send diagnostics home. Kept
import-light on purpose — no DB, no loguru, no third-party sink (the boot-order law). UU's
``DiagnosticBase`` loguru/JSON-sink machinery is NOT carried; the one mechanism carried over is
the microsecond stamp (below). The law's WORDING moved on 2026-08-18 and its content did not:
it used to say "stdlib only (``datetime``), no sink backend", and the default home now costs
two in-house imports — ``cairn.tools.base.address`` (measured: ``__future__`` and ``pathlib``,
which is what makes it a legal floor for callers that pin an allowlist) and
``cairn.tools.base.breadcrumb_log`` (``json``, ``pathlib``, and that address). Both are leaves
at this same floor, ``cairn/tools/base/__init__.py`` is empty by that same law, and neither
pulls in a database, a logging framework, or anything outside the repo.

WHERE HOME IS — ``~/.cairn/logs/<device>/<instance>/``, THE DEVICE'S OWN, AND NOBODY HAS TO
WIRE IT (2026-08-18, ticket ``a-device-logs-without-being-wired``; 2026-08-19, ticket
``an-emission-is-one-file-named-by-its-pointer`` — one JSON file per emission, named by its
UTC stamp, source, and gate). A device derives its own component name from its class's module
address and writes there by default.

WHAT THAT REPLACED, AND WHY THE OLD SHAPE WAS RIGHT WHEN IT WAS WRITTEN. This paragraph used to
say home was CC's shim — the diagnostic mailbox — and that the receiver is INJECTED
(``set_diagnostic_receiver``), never imported. That was the correct shape for the home it
described: a mailbox is a LIVE PROCESS, and which process is listening is a deployment fact an
emitting class cannot know, so injection is how you reach it. Then ``BreadcrumbLog`` landed
(2026-08-12) and home became a FILE at an address derived from ``(device, instance)`` — a thing
the device can compute for itself. The plug outlived the socket, and the cost was measured: 17
components hold emit sites, ONE runner ever wired a receiver, so 15 of them wrote to a list in a
process that was about to exit. Akien, 2026-08-18: *"if every class inherits logging, and the
logging is writing to the correct tree, what is the role of a reciever?"*

SO THE RECEIVER IS AN OVERRIDE NOW, NOT THE PATH. It keeps exactly one job, and it is a real
one: diverting a device's stream somewhere else — into a live ``Inspector``, or into a temp
tree so a proof does not seed the world it is about to read. ``set_diagnostic_receiver(None)``
still means HOLD, which is how a temporary instrument is torn down; what changed is that NEVER
CALLING IT no longer means the same thing as calling it with ``None``. Not-wired is the ordinary
case and it writes; held is a thing you ask for.

WHICH DEVICE AM I — derived, never configured, and it is the rung that was actually missing.
``BaseDevice`` had no ``__init__`` and carried no name and no instance, so the only place in the
running system that knew the string ``"ground_loop"`` was the runner that hand-spelled it. The
name now comes from ``type(self).__module__`` through ``address.component_of_module``
(``cairn.devices.cairn.machines.bus.bus`` -> ``bus``), which is house style with a proof behind it — the same
derive-from-your-own-address move as the roots table. The INSTANCE defaults to ``0``, which is
CLAUDE.md's rule rather than a shortcut ("a singleton is instance 0, never an exemption"), and
``set_diagnostic_instance`` is the seam for the day a second instance exists. A class under no
rung at all (a proof's throwaway subclass, ``__main__``) gets no derived name and therefore no
default trail — it HOLDS, exactly as everything did before, because filing records under an
invented device name would be worse than holding them (Law 7: the record of truth would point at
an owner that does not exist).

WHO ISSUES IT — the GATE, not the ticket. The device at the gate calls ``emit`` when something
crosses; it POINTS to the ticket (``pointer`` = the ticket's id / address — the TIE) rather than
copying it. The owned data stays with its owner (Law 6); only the pointer crosses. Keep the
emission THIN — a breadcrumb, not a payload: the gate names itself, points to the ticket, and
stamps the time. We do not enrich the top of it. (A full-value snapshot rides in ``values`` only
for the narrow case where you are watching specific values, not a ticket going by.)

THE TIMESTAMP POINTS TO THE LOGS. The microsecond stamp is not merely an ordering key — it is the
index INTO the fuller logs. Those logs are a separate, CACHE-CLASS tier: json files in
instance-space (``~/.cairn/``) that EVAPORATE after ~30 days — the throwaway history, distinct
from Cairn's durable records (VALIDATIONs, journeys). The breadcrumb (thin, home to CC's mailbox)
and the logs (fat, timestamp-indexed) are two tiers; the emission is the tie between them. v0: the
mailbox is in-memory on the receiver; flushing to the 30-day json tier grows against need — a
filed edge, not faked here.

THE INSPECTOR DOES THE WORK — it CRAWLS. The diagnostic inspector (``diagnostic_inspector``,
built) is where the intelligence lives, not the emission. Reacting to a fired probe it applies
FILTERS (by_pointer, by_gate — conjoined) to the log, gathers the whole transaction (the workflow
item AND its logging), and TRIMS it into the FINDINGS — the coherent json slice whose audience is
CC. The emission stays dumb so the inspector can be smart (Law 1: the diagnostic surface's
inference is compiled once, in the inspector — the same move as ``inference_domain``).

THE DISCIPLINE — targeted and TEMPORARY. You place a gate-contact instrument when you are watching
for something specific, then TAKE IT DOWN. Not standing probes left hanging: a permanent
firehose turns CC's mailbox into noise (the shrinking-footprint principle — instrument on demand,
event not poll). Put one to catch a flake; remove it once caught.

THE 6th PLACE AFTER THE DECIMAL — every record is stamped to the microsecond
(``f"{ts.microsecond:06d}"``), so no two entries collide and none are lost — you can order and
slice the whole diagnostic band precisely. This is the mechanism carried over from UU's sink
(``diagnostic_base/base.py``); the loguru machinery around it is not. ``now`` is passed
explicitly (defaulting to the real UTC clock) so an emission is provable without a clock, the
same way the heartbeat's ``beat`` takes ``now``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from cairn.tools.base.address import component_of_module
from cairn.tools.base.breadcrumb_log import BreadcrumbLog


class _NotWired:
    """The never-touched state, distinct from ``None``.

    ``None`` is a real answer a caller can give (``set_diagnostic_receiver(None)`` = HOLD, the
    teardown of a temporary instrument), so it cannot also mean "nobody has said". Before the
    default existed the two collapsed harmlessly, because both did the same thing; they do
    different things now, and a sentinel is what keeps a device that was deliberately silenced
    from quietly starting to write again."""


NOT_WIRED = _NotWired()


class DiagnosticBase:
    """The send-home mechanism composed onto every device.

    Pure mixin over stdlib. Cooperative ``__init__`` for the normal construction path, but the
    accessors also lazy-init their state via ``__dict__`` so ``emit`` is honest even for a device
    whose ``__init__`` did not chain ``super()`` — an uninitialised diagnostic surface must never
    be the reason a record is silently lost.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._diagnostic_receiver = NOT_WIRED
        self._diagnostic_instance = 0
        self._held_diagnostics: list[dict] = []
        self.debug_sink = self

    @property
    def diagnostic_source(self) -> str:
        """Who is emitting — stamped on every record. Defaults to the class name; a running
        device overrides with its real instance id (filed edge: the id convention firms up with
        instance-space wiring)."""
        return type(self).__name__

    @property
    def diagnostic_device(self) -> str | None:
        """WHICH COMPONENT this is — the name its trail is filed under, or ``None``.

        Derived from the class's own module address, never configured: a class always knows
        ``type(self).__module__``, so this is information the object already had and nobody had
        thought to read. ``None`` is honest and common (a proof's throwaway subclass sits under
        no rung), and it means no default trail rather than a guessed one.

        Distinct from ``diagnostic_source`` above, which stamps the CLASS on each record —
        ``BusDevice`` emitting into ``bus``'s trail. Both are wanted: one says what kind of
        thing spoke, the other says whose logs it belongs in, and a device with two classes in
        it would make the difference visible."""
        return component_of_module(type(self).__module__)

    @property
    def diagnostic_instance(self) -> int:
        """Which instance's trail. ``0`` — CLAUDE.md's rule, not a shortcut: "a singleton is
        instance 0, never an exemption". Settable for the day a second one exists."""
        return getattr(self, "_diagnostic_instance", 0)

    def set_diagnostic_instance(self, instance: int) -> None:
        """Say which instance this object IS. Resets any default trail already computed, so the
        call works after an emission rather than only before one."""
        self._diagnostic_instance = int(instance)
        self.__dict__.pop("_default_diagnostic_receiver", None)

    def set_diagnostic_roots(self, roots) -> None:
        """Point this device's default trail at a different WORLD — the temp-tree seam.

        ``roots`` is ``address``'s three-root table, or ``None`` for the live one, and that is
        the whole vocabulary: this does not choose an address, it chooses which universe the
        address resolves in. It exists because the default trail removed the last reason a
        RUNNER had to name its devices, and a runner is also the one place that hands a device
        the real world — ``ground_loop/__main__`` says so in its own comment, about the clock and
        the discoverer both. Take the naming away and the world-handing has to stay, or a proof
        running the loop against a temp tree would seed the live one it is about to read.

        Distinct from ``set_diagnostic_receiver``, and the difference is worth keeping: a
        receiver replaces WHERE records go (an Inspector, a mailbox, nowhere); this keeps them
        going to this device's own trail and moves the tree the trail is in. A proof that only
        wants isolation should reach for this — it leaves the mechanism under test intact, where
        wiring a hand-built receiver would quietly prove the receiver instead of the default."""
        self._diagnostic_roots = roots
        self.__dict__.pop("_default_diagnostic_receiver", None)

    def diagnostic_trail(self):
        """Where this device's own trail lands — a ``Path``, or ``None`` for a class under no rung.

        A pointer, not a promise about the current stream: it answers "which file would this
        device's crossings be in", which is what a human at a terminal actually needs once the
        crossings stopped being a list they could print. An override (``set_diagnostic_receiver``)
        sends the stream elsewhere and does not move this address — the two questions are
        different, and collapsing them would make the answer wrong exactly when someone is
        debugging a diverted stream.

        Resolves and touches nothing (``address``'s bound, Law 6): asking where a device logs
        must not create a device's log."""
        device = self.diagnostic_device
        if device is None:
            return None
        return BreadcrumbLog(device, self.diagnostic_instance,
                             roots=getattr(self, "_diagnostic_roots", None)).path

    def set_diagnostic_receiver(self, receiver) -> None:
        """OVERRIDE home — divert this device's stream somewhere other than its own trail.

        Not the ordinary path any more, and that is the point of the 2026-08-18 change: an
        un-called device writes to ``~/.cairn/logs/<device>/<instance>/``, so this is for the two
        cases that genuinely need somewhere else. Into a live ``Inspector``, which answers the
        same ``receive_diagnostic(record)`` contract. Or into a ``BreadcrumbLog`` built over a
        temp ``roots`` table, which is how a proof avoids seeding the tree it is about to read.

        ``None`` still means HOLD — records accumulate in memory, retrievable, never sent — which
        is how a temporary instrument is torn down. It is now DIFFERENT from never calling this
        at all, which is why the unwired state is a sentinel and not ``None``: silencing a device
        is a decision, and it must not be undone by the same code path that grants a default."""
        self._diagnostic_receiver = receiver

    def _receiver(self):
        """The receiver in force: an override if one was set, else this device's own trail.

        The default is built ONCE, LAZILY, and only if this class has a component name.
        Lazily because constructing an address must touch no disk (``address``'s own bound,
        and Law 6 — provisioning is a different act with a different owner), and ``BreadcrumbLog``
        keeps that promise: it makes the directory at the first WRITE, not at construction. So a
        device that never emits leaves no directory behind, which is what keeps the logs tree a
        record of what happened rather than a census of what exists."""
        wired = getattr(self, "_diagnostic_receiver", NOT_WIRED)
        if not isinstance(wired, _NotWired):
            return wired
        default = self.__dict__.get("_default_diagnostic_receiver")
        if default is None:
            device = self.diagnostic_device
            if device is None:
                return None
            default = BreadcrumbLog(device, self.diagnostic_instance,
                                    roots=getattr(self, "_diagnostic_roots", None))
            self.__dict__["_default_diagnostic_receiver"] = default
        return default

    def emit(self, gate: str, *, pointer=None, values: dict | None = None, now=None) -> dict:
        """Send one GATE-CONTACT record home, microsecond-stamped.

        ``gate`` names the transition / boundary crossed. ``pointer`` is what is travelling
        through it (a ticket id, an artifact ref) — usually all that goes home. ``values`` is a
        full snapshot, carried ONLY when you are watching specific values. ``now`` is explicit for
        provability (default: the real UTC clock).

        WITH NOBODY WIRED THE RECORD REACHES DISK — this device's own trail in the logs tree, no
        assembly step required. Only two things still HOLD it in memory (retrievable via
        ``held_diagnostics()``, never silently dropped — Law 7): a device deliberately silenced
        with ``set_diagnostic_receiver(None)``, and a class that sits under no rung and so has no
        component name to file under. Returns the record, so a caller (or a test) can read
        exactly what was sent."""
        ts = now or datetime.now(timezone.utc)
        record = {
            "ts": ts.isoformat(),
            "us": f"{ts.microsecond:06d}",   # the 6th place after the decimal — none lost; indexes the logs
            "source": self.diagnostic_source,
            "gate": gate,
            "pointer": pointer,              # the ticket's id/address — the TIE the inspector crawls on
            "values": values or {},          # a fat snapshot ONLY when watching values (norm: thin, empty)
        }
        receiver = self._receiver()
        if receiver is None:
            record["home"] = "held"
            self.__dict__.setdefault("_held_diagnostics", []).append(record)
            return record
        record["home"] = "sent"
        receiver.receive_diagnostic(record)
        return record

    def held_diagnostics(self) -> list[dict]:
        """Records emitted with no home to send to — HELD, not lost (Law 7). A non-empty list
        here is itself a finding, and a SHARPER one since 2026-08-18: it used to mean only that
        nobody had wired a receiver, which was the ordinary state of 15 of the 17 emitting
        components. Now not-wired writes, so a held record means one of two deliberate things —
        a device silenced with ``set_diagnostic_receiver(None)``, or a class under no rung
        emitting where no trail can be addressed."""
        return list(getattr(self, "_held_diagnostics", []))

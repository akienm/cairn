"""BaseShim — the device's always-on front, and its ROUTER for everything it has to route.

THE PATTERN, RULED 2026-08-04 by Akien
(``CairnCommons/decisions/2026-08-04-the-shim-routes-everything-rescoped.json``): *"each
device should own its own everything as much as possible, that's encapsulation... since the
shim knows about the device, it should know exactly how everything should be routed. not
even just messages."*

Read the list below as ONE job, not four. The shim is the single thing that knows both the
bus and the device, so every question of the form "where does this go for that device" is
answered here — mail, predicates, page assembly, and whatever comes next. Routing on a
PREDICATE is the same job as routing on an address; a shim can sort either way precisely
because it knows the device behind it.

This RATIFIES what ``system_rackmount`` already does rather than changing it: a caller
subscribes at the owner's gate, the owner resolves its own predicate, and the OWNER'S SHIM
fires it on the beat. The caller's probe is still the caller's — it chose the line, the
address and the why — and it is still routed by a shim that knows its device. Delegated
access through the owner's gate is Law 6's second clause, not a hole in its first.

The generalization the ruling adds: when a NEW thing needs routing for a device, it goes
here, and a second path around this class is the thing to be suspicious of.

Every Cairn device is its OWN PROCESS, and it does not spin — it sleeps when idle and is
woken on demand (converged with Akien 2026-07-18;
``CairnCommons/intentions-not-beside-code/I-heartbeat-probes-and-bus.md``). The SHIM is the piece that is
always on: one per device, lightweight, and it does three things.

  1. **Fires the device's due probes on each heartbeat pulse.** The ``ground_loop`` is
     ONLY the heartbeat — it beats and pulses shims; the FIRING lives here (this is the
     correction of the goof where the ground_loop was an executor). On ``on_pulse`` the shim
     evaluates each of its device's probes (a probe's trigger is evaluated where its
     data is owned — Law 6) and POKES the target of each one that fires, onto the bus.
  2. **Receives incoming bus messages for its device.**
  3. **Starts the device (the heavier process) on demand** when a message arrives and the
     device isn't running.

So the shim is the device's persistent front and process-manager; the device is the heavier
process the shim wakes. This is the sleep/wake peer model made physical: a device is a
process that WAKES TO A POKE, not a daemon that spins.

RESOLVED: the one-loop primitive. Last session filed "BaseShim's one-loop primitive" as an
open edge (a UU ``ShimLoopThread`` would have been a hollow build before Cairn's loop was
designed). It is now designed and built: the shim's "loop" IS the per-pulse probe-firing,
driven by the ground_loop heartbeat — no bespoke thread, no ``RUNNING`` state. The state
machine (whose one rest is ``PROVED``, since ticket watchme-emits-a-probe dissolved the
second rest on 2026-07-30) is the TICKET species' concern (a different thing from a probe —
see ``cairn/tools/base/probe.py``); the shim fires probes, it does not run workflows.

Still composes ``CoreValuesMixin`` — every shim carries CP1-CP6 structurally (Law 2,
proofs/test_composition.py). Kept import-light: the bus is INJECTED, not imported, so this
module still pulls in no DB and no daemon threads (only the probe primitive, which is
itself import-light).

FILED EDGES (children of this stone, not faked):
  - Each device its own OS PROCESS: ``_start_device`` is the wake hook; today a concrete shim
    may instantiate its device in-process. Spawning a real separate process (and a probe
    firing as a separate short-lived process that posts and terminates) is the process-model
    edge — the SHAPE is here (start-on-demand, fire-and-poke), the OS plumbing grows against
    a real multi-process need, like sudo_relay's daemon is the one unprovable-without-the-OS part.
  - SUBSCRIPTION by a file in the device's own folder tree (how the ground_loop discovers who
    to pulse without in-process references): today a shim is subscribed in-process via
    ``ground_loop.subscribe(shim)``; the file-discovery grows when devices are separate processes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cairn.tools.base.probe import Probe
from cairn.tools.base.core_values import CoreValuesMixin
from cairn.tools.base.diagnostic import DiagnosticBase


class BaseShim(DiagnosticBase, CoreValuesMixin, ABC):
    """Abstract base for every Cairn device shim.

    Composes ``CoreValuesMixin`` (CP1-CP6, Law 2). Pins ``device_id`` (one shim per device).
    Carries the per-pulse probe-firing (``on_pulse``), message receipt (``deliver``), and
    on-demand device start (``_start_device``). The bus is injected so firing has somewhere to
    poke; a shim with no bus records what it *would* have fired (honest, not silent).
    """

    def __init__(self, bus=None) -> None:
        super().__init__()
        self._bus = bus
        self._device = None      # the heavier process, instantiated on demand
        self._running = False
        self._pulses = 0
        self._last_pulse: dict | None = None
        # Which declarations were TRUE at the last pulse — the memory that turns a level into a
        # crossing. Lives here because a Probe is frozen and holds no state (see probe.py):
        # the probe declares, the firer remembers. Keyed by Probe.identity, so a shim that
        # rebuilds its probe list every pulse still recognises the same standing watch.
        self._was_true: set = set()
        # Which declarations have GATHERED ENOUGH and are retired for good. A DIFFERENT memory
        # from ``_was_true`` on purpose: that one is the anti-bounce resting state (the watch
        # stands, the next crossing pokes), this one is terminal (the watch is over). Kept as
        # its own set so the two can never be read for each other — the distinguishability the
        # enough-condition is worthless without. Also keyed by Probe.identity.
        self._cleared: set = set()
        # THE SILENCE MEMORY (ticket watchme-emits-a-probe falsifier clause (2), 2026-07-30).
        # A THIRD memory, and a third one on purpose: ``_was_true`` is the resting state of a
        # standing watch and ``_cleared`` is a watch that ended well, but a watch that has
        # NEVER FIRED is neither — it looks exactly like a healthy resting watch from both of
        # those, which is precisely the silent failure the clause names. ``_first_seen`` is
        # the pulse index a declaration was first evaluated at; ``_ever_fired`` is every
        # identity that has ever poked. Overdue = declared a horizon, never fired, and more
        # pulses than the horizon have passed since it was first seen.
        self._first_seen: dict = {}
        self._ever_fired: set = set()
        # THE PULSE SERVICE (ticket the-pulse-file-is-the-subscription, 2026-08-15): the
        # activated groundloop/pulse.py modules this device carries THIS pass. Handed over
        # whole each reconcile (like the probe list — replaced, never accumulated), fired
        # here because "pulse.py will be our webserver's SHIM's pulse" — the loop only
        # beats, and firing stays in the shim. Empty for every device without one.
        self._pulse_mods: list = []

    @property
    @abstractmethod
    def device_id(self) -> str:
        """The id of the device this shim manages — one shim per device."""

    # --- the device's declared probes ------------------------------------

    def probes(self) -> list[Probe]:
        """The device's probes — the immutable declarations the shim fires on each pulse.

        Default empty: a device with no probes is honest, not broken (it simply is not
        driven by the beat). A concrete shim overrides this to expose its device's probes
        (e.g. the system device's live threshold subscriptions)."""
        return []

    def set_pulse_modules(self, modules: list) -> None:
        """Hand this shim its device's activated pulse modules for the coming pulses.

        Called by the loop's reconcile with whatever the PulseCache holds for this device —
        the whole list, every pass, so a vanished pulse is forgotten by replacement exactly
        like a vanished probe file. The shim never imports; it only fires what it was
        handed (the discovery/firing split the 584aa74 goof record demands)."""
        self._pulse_mods = list(modules)

    def _serve_pulses(self, now, context: dict) -> list[dict]:
        """Fire each carried pulse module's ``on_pulse(now, context)`` hook — batch-safe.

        A module with no callable hook is import-only (its top-level already ran at
        activation; that is a legitimate v0 pulse). A raising hook becomes a loud entry
        and the rest keep firing (CP2, Law 7) — one device's bad pulse is isolated by the
        same physics as one device's bad probe."""
        served: list[dict] = []
        for mod in self._pulse_mods:
            name = getattr(mod, "__name__", repr(mod))
            hook = getattr(mod, "on_pulse", None)
            if not callable(hook):
                served.append({"module": name, "outcome": "import-only"})
                continue
            try:
                returned = hook(now, context)
                served.append({"module": name, "outcome": "ok", "returned": returned})
            except Exception as exc:  # noqa: BLE001 — a bad pulse must not stop the batch
                served.append({"module": name, "outcome": "refused",
                               "error": f"{type(exc).__name__}: {exc}"})
        return served

    def cleared(self) -> set:
        """The identities of probes that GATHERED ENOUGH and are retired — read-only, and
        deliberately a separate surface from the anti-bounce memory. An operator (or a tooth)
        asking "did this watch end, or is it just resting?" gets a different answer from a
        different place, which is the whole point of the split."""
        return set(self._cleared)

    def overdue(self, probes: list[Probe] | None = None) -> list[dict]:
        """THE LOUD SURFACE FOR A WATCH THAT NEVER FIRED — every armed probe that declared a
        ``horizon``, has never poked, and has now stood more pulses than its horizon allows.

        Ticket ``watchme-emits-a-probe`` falsifier clause (2): *"A probe is armed and never
        fires, and nothing is loud about it — a watcher emitted into a heartbeat nobody runs
        learns nothing while LOOKING like learning."* Nothing in ``_was_true`` or
        ``_cleared`` can answer this: a watch resting correctly and a watch that has been
        dead since the day it was armed have byte-identical resting states there. This is the
        third reading, and it is the one that goes loud.

        A READ IS AN EVENT, so this is callable on demand and not only from a pulse — the
        pulse-record carries it too, but a heartbeat that never runs cannot report its own
        absence, so the read-side door is the one that catches the worst case. No clock, no
        sweep, no registry: bounded OUT, and unnecessary — the shim already counts pulses.

        A probe with no ``horizon`` is NEVER overdue. That is the declaration's own choice
        (a standing watch with no deadline is legitimate), not a gap in this check."""
        out = []
        for cb in (self.probes() if probes is None else probes):
            if cb.horizon is None or cb.identity in self._ever_fired:
                continue
            if cb.identity in self._cleared:
                continue          # retired deliberately — an ending, not a silence
            first = self._first_seen.get(cb.identity)
            if first is None:
                continue          # never yet evaluated: no silence to measure against
            stood = self._pulses - first
            if stood > cb.horizon:
                out.append({"why": cb.why, "to": cb.to, "horizon": cb.horizon,
                            "pulses_stood": stood,
                            "finding": "ARMED AND NEVER FIRED past its horizon — this watch "
                                       "has looked like learning for %d pulses and has "
                                       "gathered nothing (Law 7)" % stood})
        return out

    # --- (1) fire due probes on a heartbeat pulse ------------------------

    def on_pulse(self, now, context: dict | None = None) -> dict:
        """One heartbeat pulse reaching this shim. Evaluate every probe (Law 6 — a trigger
        reads its owned data where it lives) and POKE the target of each that fires, onto the
        bus. Returns a PULSE-RECORD — what fired, what held, what kicked back — so a pulse is
        itself evidence — a record, never a silent ``RUNNING``. (Until 2026-07-30 this line
        named a node state as the alternative to silent RUNNING; ticket watchme-emits-a-probe
        dissolved it — what a pulse yields is EVIDENCE, which was always the claim here.)
        A batch drainer must not die on one bad
        probe: a trigger that raises or a poke that is refused becomes a permanent, loud
        entry and the rest keep firing (CP2, Law 7)."""
        context = context or {}
        fired: list[dict] = []
        held: list[dict] = []
        still_true: set = set()
        declared = self.probes()
        for cb in declared:
            try:
                # WHEN THIS WATCH STARTED STANDING — stamped before anything can skip the
                # rest of the body, including the cleared branch and a raising trigger, so a
                # probe that has been broken since birth still has a silence that can be
                # measured (a trigger that always raises is the loudest never-fires there is).
                self._first_seen.setdefault(cb.identity, self._pulses)
                # CLEARED IS TERMINAL and is checked FIRST: a retired declaration is not
                # evaluated at all, so its trigger costs nothing on every later pulse. The
                # reason is its own string — never "trigger false", which is the re-armed
                # resting state and means the opposite (the watch still stands).
                if cb.identity in self._cleared:
                    held.append({"why": cb.why, "to": cb.to,
                                 "reason": "cleared — gathered enough, retired"})
                    continue
                true_now = cb.fires(now, context)
                if true_now:
                    still_true.add(cb.identity)
                    # A POKE PER CROSSING, NOT PER PULSE: a condition that STAYS true pokes once,
                    # when it crosses. ``while_true`` opts back into per-pulse for the probe
                    # that means "keep telling me while this holds."
                    if cb.while_true or cb.identity not in self._was_true:
                        fired.append(self._fire(cb, context))
                        # It has poked at least once, so its silence is over for good — a
                        # watch that fired and then went quiet is a DIFFERENT question
                        # (that is the trigger's resting state), and clause (2) is only
                        # about the watcher that never spoke at all.
                        self._ever_fired.add(cb.identity)
                        # ASKED ONLY AFTER A FIRE: a probe that has not poked has gathered
                        # nothing. A broken enough leaves the watch STANDING (Law 7) and the
                        # kick-back is recorded rather than swallowed — the poke already landed,
                        # so this must not fall into the outer handler and be read as a refusal.
                        try:
                            if cb.gathered_enough(context):
                                self._cleared.add(cb.identity)
                                fired[-1]["cleared"] = "gathered enough — retired"
                        except Exception as exc:  # noqa: BLE001 — a broken stop must not stop the watch
                            fired[-1]["enough_failed"] = f"{type(exc).__name__}: {exc}"
                    else:
                        held.append({"why": cb.why, "to": cb.to, "reason": "still true — "
                                     "already poked at the crossing"})
                else:
                    held.append({"why": cb.why, "to": cb.to, "reason": "trigger false"})
            except Exception as exc:  # noqa: BLE001 — record every kick-back, never abort the batch
                # A trigger that RAISED tells us nothing about the line, so it must not be
                # remembered as either side of it: leaving it out of ``still_true`` means the
                # next true reading is a fresh crossing and pokes. A swallowed error must never
                # ALSO swallow the next real poke (Law 7).
                fired.append({"to": cb.to, "why": cb.why, "outcome": "refused",
                              "error": f"{type(exc).__name__}: {exc}"})
        record = {
            "device": self.device_id,
            "date": str(now),
            "fired": fired,
            "fired_count": sum(1 for f in fired if f.get("outcome") == "ok"),
            "held": held,
        }
        # THE PULSE SERVICE fires after the probes, on the same pulse, additively: the key
        # exists only when this device carries a pulse module, so every pulse-less device's
        # record is byte-identical to what it was before this seam existed.
        if self._pulse_mods:
            record["services"] = self._serve_pulses(now, context)
        # Remember the line's position for the next pulse. Assigned WHOLE, so a declaration that
        # has gone false (or vanished from probes() entirely) is forgotten — and therefore
        # pokes again when it next crosses, instead of being suppressed by a stale memory.
        self._was_true = still_true
        self._pulses += 1
        # Computed AFTER the count advances, so the record answers for the pulse that just
        # happened. Its own key, never folded into ``held``: a watch resting correctly and a
        # watch that has been silent since it was armed must not read the same (Law 7 — loud
        # at a diagnostic surface, and a pulse-record is one).
        record["overdue"] = self.overdue(declared)
        self._last_pulse = record
        return record

    def _fire(self, cb: Probe, context: dict | None = None) -> dict:
        """Fire one probe: POKE its target on the bus (the fire path). With no bus wired, it
        records what it WOULD have posted (honest, not a silent no-op). The fire-and-die
        separate-process spawn is a filed edge — the SHAPE (a poke onto the bus) is here.

        The body is ``cb.payload(context)``, not ``cb.body``: the probe's carrier runs HERE,
        at fire time, against the context the trigger just saw — so what rides along is the
        artifact as it was AT the gate, in whatever form the receiver can process."""
        body = cb.payload(context)
        if self._bus is None:
            return {"to": cb.to, "verb": cb.verb, "channel": cb.channel, "why": cb.why,
                    "outcome": "unwired", "body": body}
        envelope = self._bus.post(sender=self.device_id, to=cb.to, verb=cb.verb,
                                  channel=cb.channel, why=cb.why, body=body)
        return {"to": cb.to, "verb": cb.verb, "channel": cb.channel, "why": cb.why,
                "outcome": "ok", "envelope": envelope["id"]}

    # --- the web presentation surface: assemble the device's ACTIVE page ----

    def device(self):
        """The introspectable device this shim fronts, woken on demand.

        The web server reaches a device's ACTIVE page THROUGH its always-on shim
        (the device may be asleep); querying the page is itself a poke, so it wakes
        the device (wake-to-a-poke). A concrete shim that already holds its device
        directly overrides this to hand it back without the lazy start."""
        self._ensure_device()
        return self._device

    def active_page(self) -> dict:
        """Assemble the device's ACTIVE page as structured DATA — the STANDARD
        machinery, here in the shim and not in each device (Law 6) and not in the web
        server (which only renders). Returns ``{"device", "panes": [...]}`` where each
        pane is ``{kind, label, data}``.

        The STATUS + SETTINGS FLOOR is projected from the device's ``introspect()``
        (Form v0 #2 — STATUS = intention + state, the reported side of the drift
        detector; SETTINGS = settings). The device's ``declared_panes()`` are then
        appended IN ORDER, multiples of a kind allowed. Payload is DATA (dicts / lists
        / scalars), never HTML — the web server renders (Law 7).

        An offered pane whose handler is ``None``, or whose handler RAISES, renders
        ABSENT with a reason and the page still assembles (CP2, Law 7 — loud at this
        diagnostic surface, never a silent drop, never an aborted page).

        FILED EDGE (child b's job, not faked here): STATUS carries only the REPORTED
        intention; flagging drift against the FILED ``intention+why.json`` on disk is
        the web server's render-time comparison (it already reads disk intentions),
        not the shim's — the shim must not couple to charter file paths."""
        dev = self.device()
        surface = dev.introspect()
        panes: list[dict] = [
            {"kind": "status", "label": "Status",
             "data": {"intention": surface["intention"], "state": surface["state"]}},
            {"kind": "settings", "label": "Settings", "data": surface["settings"]},
        ]
        for desc in dev.declared_panes():
            kind = desc.get("kind")
            label = desc.get("label", kind)
            handler = desc.get("handler")
            if handler is None:
                panes.append({"kind": kind, "label": label, "data": None,
                              "absent": "offered but unwired (no handler)"})
                continue
            try:
                data = handler()
            except Exception as exc:  # noqa: BLE001 — a bad pane is loud + absent, never an aborted page
                panes.append({"kind": kind, "label": label, "data": None,
                              "absent": f"handler refused: {type(exc).__name__}: {exc}"})
                continue
            panes.append({"kind": kind, "label": label, "data": data})
        return {"device": self.device_id, "panes": panes}

    # --- the diagnostic mailbox: receive gate-contact breadcrumbs (for now) --

    def receive_diagnostic(self, record: dict) -> None:
        """Receive a gate's diagnostic breadcrumb, sent HOME. In the running system THIS is CC's
        own shim (``cc_0``) — the diagnostic mailbox, *for now* (the honest stopgap until a
        diagnostic device owns it). A device inherits ``emit`` (``cairn/tools/base/diagnostic.py``); its
        gates point breadcrumbs here, each tied to a ticket (``pointer``) and stamped to the
        microsecond (which indexes the fuller 30-day logs). The interpreter crawls this mailbox.
        Records land in arrival order; the µs stamp the emitter applied is what orders them
        precisely, so none collide and none are lost (Law 7)."""
        self.__dict__.setdefault("_diagnostics", []).append(record)

    def diagnostics(self) -> list[dict]:
        """The diagnostic mailbox — breadcrumbs sent home, in arrival order. The log interpreter
        reads this, follows each ``pointer`` + µs stamp, and compiles the slice (the next build)."""
        return list(getattr(self, "_diagnostics", []))

    # --- (2)+(3) receive mail; wake the device on demand --------------------

    def deliver(self, envelope: dict):
        """Receive an incoming bus message for this device. Start the device on demand if it is
        not running (3), then hand the envelope to it (2). This is the wake-to-a-poke: the shim
        is always on and receiving; the device is woken only when there is mail.

        BOUNCES BACK TO SENDER WHEN THERE IS NO HANDLER (ticket
        undeliverable-mail-returns-to-sender, 2026-08-27). The sender owns the decision about
        what to do with returned mail (Law 6); the base class fallback (handle_bounce) emits a
        diagnostic and returns — loud, not silent (Law 7). Devices override handle_bounce when
        they grow capacity. An ``is_bounce`` flag in the body prevents infinite loops: a bounced
        message that itself has no handler raises instead of bouncing again.

        Note the ``_device is None`` check rather than ``_ensure_device`` alone: a shim that is
        always-on (``_running`` true from birth, like a discovered one) never enters the lazy
        start, so asking ``_running`` would answer "yes, running" about a shim holding no
        device at all."""
        if envelope.get("body", {}).get("is_bounce"):
            return self.handle_bounce(envelope)
        self._ensure_device()
        if self._device is None:
            self._device = self._start_device()   # loud by contract; see _start_device
        verb = envelope.get("verb", "")
        if verb:
            verbs = {}
            if hasattr(self._device, "declared_verbs") and callable(self._device.declared_verbs):
                verbs = self._device.declared_verbs()
            if verb not in verbs:
                declared = list(verbs) if verbs else "none"
                reason = (f"{self.device_id} has no verb {verb!r} — declared verbs: "
                          f"{declared}")
                return self._bounce_to_sender(envelope, reason)
            handler = verbs[verb]
            if not callable(handler):
                reason = (f"{self.device_id} declares verb {verb!r} but its handler is "
                          "not callable")
                return self._bounce_to_sender(envelope, reason)
            return handler(envelope)
        receive = getattr(self._device, "receive", None)
        if not callable(receive):
            reason = (f"{self.device_id} was delivered mail but its device declares no "
                      "receive() and the envelope carries no verb")
            return self._bounce_to_sender(envelope, reason)
        return receive(envelope)

    def _bounce_to_sender(self, envelope: dict, reason: str):
        """Post a bounce message back to the sender via the bus. If no bus or no sender,
        raise — the bounce cannot be delivered, so the original error surfaces instead."""
        sender = envelope.get("sender")
        if not sender or not self._bus:
            raise NotImplementedError(
                f"{reason}. Cannot bounce: "
                f"{'no sender on envelope' if not sender else 'no bus on shim'}")
        self._bus.post(
            sender=self.device_id, to=sender, channel="personal",
            why=f"bounced: {reason}",
            body={"is_bounce": True, "reason": reason,
                  "original_verb": envelope.get("verb", ""),
                  "original_addressee": envelope.get("addressee", "")})
        self.emit("bounce_sent", pointer=envelope.get("id"),
                  values={"reason": reason, "to": sender})
        return {"bounced": True, "reason": reason, "to": sender}

    def handle_bounce(self, bounce_envelope: dict):
        """Handle a bounced message that was returned to this device as sender. The default
        emits a diagnostic (permanent in records of truth — Law 7) and returns. Devices
        override this when they grow capacity to deal with returned mail (Law 6)."""
        body = bounce_envelope.get("body", {})
        reason = body.get("reason", "unknown")
        original_verb = body.get("original_verb", "?")
        self.emit("bounced_mail", pointer=bounce_envelope.get("id"),
                  values={"reason": reason, "original_verb": original_verb,
                          "from": bounce_envelope.get("sender", "?")})
        return {"handled": False, "reason": reason}

    @property
    def running(self) -> bool:
        return self._running

    def _ensure_device(self) -> None:
        if not self._running:
            self._device = self._start_device()
            self._running = True

    def _start_device(self):
        """Wake the device (the heavier process) — the shim's process-manager role. A shim that
        receives mail must say how it starts its device; the default refuses loudly rather than
        silently doing nothing (CP1). Concrete shims instantiate (today) or spawn a real process
        (the filed process-model edge)."""
        raise NotImplementedError(
            f"shim for {self.device_id!r} received mail but declares no _start_device — a shim "
            f"that is delivered to must know how to wake its device"
        )

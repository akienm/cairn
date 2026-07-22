"""BaseShim — the device's always-on front: fires its callbacks, receives its mail, wakes it.

Every Cairn device is its OWN PROCESS, and it does not spin — it sleeps when idle and is
woken on demand (converged with Akien 2026-07-18;
``CairnCommons/intentions-other/I-heartbeat-callbacks-and-bus.md``). The SHIM is the piece that is
always on: one per device, lightweight, and it does three things.

  1. **Fires the device's due callbacks on each heartbeat pulse.** The ``ground_loop`` is
     ONLY the heartbeat — it beats and pulses shims; the FIRING lives here (this is the
     correction of the goof where the ground_loop was an executor). On ``on_pulse`` the shim
     evaluates each of its device's callbacks (a callback's trigger is evaluated where its
     data is owned — Law 6) and POKES the target of each one that fires, onto the bus.
  2. **Receives incoming bus messages for its device.**
  3. **Starts the device (the heavier process) on demand** when a message arrives and the
     device isn't running.

So the shim is the device's persistent front and process-manager; the device is the heavier
process the shim wakes. This is the sleep/wake peer model made physical: a device is a
process that WAKES TO A POKE, not a daemon that spins.

RESOLVED: the one-loop primitive. Last session filed "BaseShim's one-loop primitive" as an
open edge (a UU ``ShimLoopThread`` would have been a hollow build before Cairn's loop was
designed). It is now designed and built: the shim's "loop" IS the per-pulse callback-firing,
driven by the ground_loop heartbeat — no bespoke thread, no ``RUNNING`` state. The state
machine (PROVED/LEARNING) is the TICKET species' concern (a different thing from a callback —
see ``cairn/base/callback.py``); the shim fires callbacks, it does not run workflows.

Still composes ``CoreValuesMixin`` — every shim carries CP1-CP6 structurally (Law 2,
proofs/test_composition.py). Kept import-light: the bus is INJECTED, not imported, so this
module still pulls in no DB and no daemon threads (only the callback primitive, which is
itself import-light).

FILED EDGES (children of this stone, not faked):
  - Each device its own OS PROCESS: ``_start_device`` is the wake hook; today a concrete shim
    may instantiate its device in-process. Spawning a real separate process (and a callback
    firing as a separate short-lived process that posts and terminates) is the process-model
    edge — the SHAPE is here (start-on-demand, fire-and-poke), the OS plumbing grows against
    a real multi-process need, like sudo_relay's daemon is the one unprovable-without-the-OS part.
  - SUBSCRIPTION by a file in the device's own folder tree (how the ground_loop discovers who
    to pulse without in-process references): today a shim is subscribed in-process via
    ``ground_loop.subscribe(shim)``; the file-discovery grows when devices are separate processes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from cairn.base.callback import Callback
from cairn.base.core_values import CoreValuesMixin


class BaseShim(CoreValuesMixin, ABC):
    """Abstract base for every Cairn device shim.

    Composes ``CoreValuesMixin`` (CP1-CP6, Law 2). Pins ``device_id`` (one shim per device).
    Carries the per-pulse callback-firing (``on_pulse``), message receipt (``deliver``), and
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

    @property
    @abstractmethod
    def device_id(self) -> str:
        """The id of the device this shim manages — one shim per device."""

    # --- the device's declared callbacks ------------------------------------

    def callbacks(self) -> list[Callback]:
        """The device's callbacks — the immutable declarations the shim fires on each pulse.

        Default empty: a device with no callbacks is honest, not broken (it simply is not
        driven by the beat). A concrete shim overrides this to expose its device's callbacks
        (e.g. the system device's live threshold subscriptions)."""
        return []

    # --- (1) fire due callbacks on a heartbeat pulse ------------------------

    def on_pulse(self, now, context: dict | None = None) -> dict:
        """One heartbeat pulse reaching this shim. Evaluate every callback (Law 6 — a trigger
        reads its owned data where it lives) and POKE the target of each that fires, onto the
        bus. Returns a PULSE-RECORD — what fired, what held, what kicked back — so a pulse is
        itself evidence (LEARNING, not silent RUNNING). A batch drainer must not die on one bad
        callback: a trigger that raises or a poke that is refused becomes a permanent, loud
        entry and the rest keep firing (CP2, Law 7)."""
        context = context or {}
        fired: list[dict] = []
        held: list[dict] = []
        for cb in self.callbacks():
            try:
                if cb.fires(now, context):
                    fired.append(self._fire(cb))
                else:
                    held.append({"why": cb.why, "to": cb.to})
            except Exception as exc:  # noqa: BLE001 — record every kick-back, never abort the batch
                fired.append({"to": cb.to, "why": cb.why, "outcome": "refused",
                              "error": f"{type(exc).__name__}: {exc}"})
        record = {
            "device": self.device_id,
            "date": str(now),
            "fired": fired,
            "fired_count": sum(1 for f in fired if f.get("outcome") == "ok"),
            "held": held,
        }
        self._pulses += 1
        self._last_pulse = record
        return record

    def _fire(self, cb: Callback) -> dict:
        """Fire one callback: POKE its target on the bus (the fire path). With no bus wired, it
        records what it WOULD have posted (honest, not a silent no-op). The fire-and-die
        separate-process spawn is a filed edge — the SHAPE (a poke onto the bus) is here."""
        if self._bus is None:
            return {"to": cb.to, "channel": cb.channel, "why": cb.why, "outcome": "unwired"}
        envelope = self._bus.post(sender=self.device_id, to=cb.to, channel=cb.channel,
                                  why=cb.why, body=cb.body)
        return {"to": cb.to, "channel": cb.channel, "why": cb.why,
                "outcome": "ok", "envelope": envelope["id"]}

    # --- (2)+(3) receive mail; wake the device on demand --------------------

    def deliver(self, envelope: dict):
        """Receive an incoming bus message for this device. Start the device on demand if it is
        not running (3), then hand the envelope to it (2). This is the wake-to-a-poke: the shim
        is always on and receiving; the device is woken only when there is mail."""
        self._ensure_device()
        receive = getattr(self._device, "receive", None)
        return receive(envelope) if callable(receive) else None

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

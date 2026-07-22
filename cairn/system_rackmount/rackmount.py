"""system_rackmount — THE SYSTEM DEVICE: owner of the host's resource predicates.

The one device that stands in for the SYSTEM underneath (converged with Akien 2026-07-18;
``CairnCommons/intentions-other/I-heartbeat-callbacks-and-bus.md``). It OWNS the host-resource data
— CPU, memory, disk — and ADVERTISES the callbacks it can serve against them. It is NOT a
central scheduler (that framing, and the ``interval/date/quantity/state`` trigger enum, were
the goof this rework deletes). Scheduling is the universal heartbeat + shim + callback
mechanism; this device is just the OWNER of one kind of data other devices want triggers on.

THE WORKED EXAMPLE, made physics — "alert me at 80% CPU":
  1. ADVERTISE. The system device publishes a menu: "I accept a ``cpu_threshold`` callback,
     takes a value" — one item in ``advertises()`` (part of its Form v0 #2 surface).
  2. SUBSCRIBE. A caller says "I'll take one of those — value 80, here's my address." It
     never learns the system device's internal method; it names a MENU ITEM, a value, and a
     poke address.
  3. RESOLVE INTERNALLY. The system device builds the predicate ITSELF — a ``Callback`` whose
     trigger closes over ``self._reading()["cpu"] >= 80``. The caller's ``object.object.method``
     ignorance is preserved.
  4. POKE. On each heartbeat pulse, the device's shim evaluates that callback. The reading is
     the system device's OWN data, sampled INSIDE the device (Law 6 — evaluated where its data
     is owned); the caller's raw CPU number NEVER crosses the bus. Only the POKE does — and its
     body says only THAT the caller's line was crossed, never the reading that crossed it.

So the advertise/subscribe/poke protocol + Law-6-local-evaluation are what "abstracts host
services device-independently" actually cashes out to: any device can ask the system device
for a resource trigger, and the host's metrics stay home.

FILED EDGES (children of this stone, not faked):
  - Only ``cpu_threshold`` is advertised (via a dependency-free best-effort load-average
    sampler). ``memory``/``disk`` predicates are the SAME shape — they mount here when a
    consumer asks; privilege (sudo_relay) is a host service in this same family, built
    standalone first, migrating behind this device when a second consumer makes the seam pay.
  - Subscriptions are LEVEL-triggered (a callback pokes while its predicate holds). Edge-
    triggering (poke once on the crossing) and unsubscribe are refinements that wait on a real
    consumer's need.
  - ADVERTISE / SUBSCRIBE are direct calls today; expressing them as bus messages (like the
    poke already is) is a filed edge — the protocol's shape is here, its wire form grows with
    the bus's adapter.
  - The real host sampler (rich per-core CPU, memory, disk) is the OS-specific backing this
    device will own — a thin edge; the PREDICATE physics is proven by injecting a reading.
"""

from __future__ import annotations

import os

from cairn.base.callback import Callback
from cairn.base.device import BaseDevice
from cairn.base.shim import BaseShim


def _default_sampler() -> dict:
    """Best-effort, dependency-free host reading: CPU as the 1-minute load average normalized
    by core count, as a percent. The one part that needs the real host — injected in proofs so
    the predicate physics is provable without it. memory/disk are filed edges (not sampled yet)."""
    try:
        load1 = os.getloadavg()[0]
        cores = os.cpu_count() or 1
        return {"cpu": round(load1 / cores * 100, 1)}
    except (OSError, AttributeError):  # getloadavg is Unix-only — say so, don't fake a number (CP1)
        return {"cpu": None}


class SystemRackmountDevice(BaseDevice):
    """The system device (carries CP1-CP6; reports intention/state/settings). It owns the
    host-resource data and serves threshold callbacks on it: ``advertises`` the menu,
    ``subscribe`` wires a caller's request into a device-local predicate, and the shim pokes
    the subscriber when the predicate holds — the reading never leaving the device (Law 6)."""

    # The menu this device advertises. Each entry names what a caller passes — never an internal
    # method. Minimal today (cpu); memory/disk are the same shape, filed until a consumer asks.
    ADVERTISED: dict[str, dict] = {
        "cpu_threshold": {
            "takes": ["value"],
            "why": "poke you when CPU crosses your line — evaluated here, your value never "
            "leaves as a number (Law 6)",
        },
    }

    def __init__(self, sampler=None, device_id: str = "system_rackmount") -> None:
        super().__init__()
        self._sampler = sampler or _default_sampler
        self._device_id = device_id
        self._subs: dict[str, dict] = {}   # sub_id -> {name, address, value, why, callback}
        self._counter = 0

    @property
    def device_id(self) -> str:
        return self._device_id

    # --- (1) advertise the menu ---------------------------------------------

    def advertises(self) -> list[dict]:
        """The callbacks this device offers — a caller inspects this, then subscribes by menu
        name. Part of the Form v0 #2 surface (inspecting the device shows what it can serve)."""
        return [{"callback": name, **spec} for name, spec in self.ADVERTISED.items()]

    # --- (2)+(3) subscribe; resolve the method internally -------------------

    def subscribe(self, name: str, *, address: str, why: str, value,
                  channel: str = "personal") -> str:
        """Wire a caller's request into a device-local callback and return its subscription id.
        The caller names a MENU ITEM (`name`), a `value`, and a poke `address` — never an
        internal method. The device RESOLVES ITS OWN PREDICATE (`_resolve`) and bakes the
        caller's value into it. An unadvertised name is refused loudly (CP1). The poke body will
        say only THAT the line was crossed, carrying the caller's own value, never the reading."""
        if name not in self.ADVERTISED:
            raise KeyError(f"no advertised callback {name!r}; this device offers "
                           f"{sorted(self.ADVERTISED)} (inspect advertises())")
        trigger = self._resolve(name, value)   # internal — the caller never sees this
        self._counter += 1
        sub_id = f"{name}#{self._counter}"
        callback = Callback(
            why=why,
            trigger=trigger,
            to=address,
            channel=channel,
            body={"alert": name, "crossed": value},  # the caller's line, NOT the owned reading
        )
        self._subs[sub_id] = {"name": name, "address": address, "value": value,
                              "why": why, "callback": callback}
        return sub_id

    def _resolve(self, name: str, value):
        """Map an advertised menu name to the device's OWN predicate, closing over device-local
        data so the reading stays home (Law 6). This is the method-resolution the caller is kept
        ignorant of — it only ever named the menu item."""
        if name == "cpu_threshold":
            return lambda now, context: self._over("cpu", value)
        raise KeyError(name)  # unreachable — subscribe validated the name

    def _over(self, metric: str, value) -> bool:
        """Is the OWNED reading of ``metric`` at/over ``value``? Samples inside the device; a
        None reading (metric unavailable on this host) is honestly NOT-over, never a fake fire."""
        reading = self._reading().get(metric)
        return reading is not None and reading >= value

    def _reading(self) -> dict:
        """The device's own, unexported host data. The sampler is injectable so the predicate
        physics is provable without the real host."""
        return self._sampler()

    def subscription_callbacks(self) -> list[Callback]:
        """The live subscriptions as callbacks — what this device's shim fires on each pulse."""
        return [sub["callback"] for sub in self._subs.values()]

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The system device — owner of the host's resource predicates (CPU, memory, "
            "disk). It advertises the threshold callbacks it can serve, and pokes a subscriber "
            "when their line is crossed — evaluating the predicate locally, so the host's raw "
            "metrics never leave the device.",
            "why": "So any device can get a trigger on a host resource WITHOUT the host's data "
            "being exported and without coupling to the OS (Law 6): the reading stays home, only "
            "the wake-up crosses the bus. This is 'abstract host services device-independently' "
            "made concrete — and it is NOT a central scheduler (that was the goof); scheduling is "
            "the universal heartbeat + shim + callback mechanism.",
        }

    def state(self) -> dict:
        return {
            # Subscriptions WITHOUT the reading — who is waiting on which line, never the metric.
            "subscriptions": [
                {"id": sid, "name": s["name"], "value": s["value"], "to": s["address"]}
                for sid, s in self._subs.items()
            ],
            "advertised": sorted(self.ADVERTISED),
        }

    def settings(self) -> dict:
        return {
            "advertises": self.advertises(),
            "evaluation": "LOCAL — a threshold predicate reads the host metric INSIDE this device "
            "(Law 6); only the poke crosses the bus, never the reading",
            "sampler": "best-effort load-average CPU (dependency-free); the real host sampler and "
            "memory/disk predicates are filed edges — the predicate physics is proven by injection",
            "not": "NOT a central scheduler and NOT a service registry — the interval/date/"
            "quantity/state enum was deleted; a trigger is any predicate (cairn/base/callback.py)",
        }


class SystemRackmountShim(BaseShim):
    """The system device's shim — always on, subscribed to the heartbeat. On each pulse it fires
    the device's live subscription-callbacks (each sampling the device's own reading, Law 6) and
    pokes the subscribers whose line is crossed, onto the bus. This is where the system device's
    'scheduling' actually happens: not in a bespoke scheduler, but in the universal shim-fires-
    callbacks-on-the-beat mechanism every device shares."""

    def __init__(self, device: SystemRackmountDevice, bus) -> None:
        super().__init__(bus=bus)
        self._sysdev = device

    @property
    def device_id(self) -> str:
        return self._sysdev.device_id

    def callbacks(self) -> list[Callback]:
        return self._sysdev.subscription_callbacks()

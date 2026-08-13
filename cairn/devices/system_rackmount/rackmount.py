"""system_rackmount — THE SYSTEM DEVICE: owner of the host's resource predicates.

The one device that stands in for the SYSTEM underneath (converged with Akien 2026-07-18;
``CairnCommons/intentions-not-beside-code/I-heartbeat-probes-and-bus.md``). It OWNS the host-resource data
— CPU, memory, disk — and ADVERTISES the probes it can serve against them. It is NOT a
central scheduler (that framing, and the ``interval/date/quantity/state`` trigger enum, were
the goof this rework deletes). Scheduling is the universal heartbeat + shim + probe
mechanism; this device is just the OWNER of one kind of data other devices want triggers on.

THE WORKED EXAMPLE, made physics — "alert me at 80% CPU":
  1. ADVERTISE. The system device publishes a menu: "I accept a ``cpu_threshold`` probe,
     takes a value" — one item in ``advertises()`` (part of its Form v0 #2 surface).
  2. SUBSCRIBE. A caller says "I'll take one of those — value 80, here's my address." It
     never learns the system device's internal method; it names a MENU ITEM, a value, and a
     poke address.
  3. RESOLVE INTERNALLY. The system device builds the predicate ITSELF — a ``Probe`` whose
     trigger closes over ``self._reading()["cpu"] >= 80``. The caller's ``object.object.method``
     ignorance is preserved.
  4. POKE. On each heartbeat pulse, the device's shim evaluates that probe. The reading is
     the system device's OWN data, sampled INSIDE the device (Law 6 — evaluated where its data
     is owned); the caller's raw CPU number NEVER crosses the bus. Only the POKE does — and its
     body says only THAT the caller's line was crossed, never the reading that crossed it.

So the advertise/subscribe/poke protocol + Law-6-local-evaluation are what "abstracts host
services device-independently" actually cashes out to: any device can ask the system device
for a resource trigger, and the host's metrics stay home.

TWO DOORS, ONE PREDICATE (the second added 2026-08-04, ratified by Akien). The menu above is
the POKE-ME-WHEN door: you subscribe and the shim wakes you. ``ask()`` is the MAY-I door: the
same advertised item, the same device-resolved predicate, pulled instead of pushed. It returns
a VERDICT — "your line is crossed", true or false — never the reading. That is the whole point:
a caller that receives the number receives the METRIC'S SEMANTICS too, and this device could
then never change how it measures without touching every caller. A caller that receives a
verdict is coupled to its own line and nothing else. The raw-number door ("tell me about
yourself" — introspection, for curiosity/self-exploration) is a THIRD shape, named and
deliberately NOT built: it has no customer yet, and unlike these two it exports semantics by
design, which is safe only because no gate would depend on it.

FILED EDGES (children of this stone, not faked):
  - ``disk`` is not sampled — same shape as the two below, mounts when a consumer asks.
    Privilege (sudo_relay) is a host service in this same family, built standalone first,
    migrating behind this device when a second consumer makes the seam pay.
  - Subscriptions are LEVEL-triggered (a probe pokes while its predicate holds). Edge-
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

from cairn.tools.base.probe import Probe
from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim


def _cpu_percent() -> float | None:
    """Host CPU pressure RIGHT NOW: the RUNNABLE count (field 4 of /proc/loadavg, the
    ``running/total`` pair) normalized by core count, as a percent.

    WHY NOT THE LOAD AVERAGE — MEASURED 2026-08-04. This device used to serve
    ``os.getloadavg()[0]``, which the kernel recomputes only every 5s as a ~60s exponentially
    decaying average. Four CPU burners on this 8-core box (truth ~50%) read: 5.5% at t=0, 9.1%
    at t=1s and unchanged through t=5s, 12.4% at t=8s, 15.4% at t=12s. Twelve seconds after the
    box was half-consumed the served metric still said 15%. An admission gate reading that
    number lets every builder in, because the previous builder is still invisible when the next
    one asks. The adjacent field went 2 -> 6 within one second of the same event. The gate needs
    to see a launch before the next asker arrives; only the instantaneous field does that.

    The reading process is itself runnable, so an idle box floors at ``1/cores``, not 0 — an
    honest offset, not a fudge, and small enough that no line worth setting sits under it."""
    try:
        with open("/proc/loadavg") as fh:
            runnable = int(fh.read().split()[3].split("/")[0])
    except (OSError, IndexError, ValueError):
        return None  # not a Linux /proc host — say so, don't fake a number (CP1)
    cores = os.cpu_count() or 1
    return round(runnable / cores * 100, 1)


def _memory_available_mb() -> float | None:
    """Memory a new process could actually claim, in MB — ``MemAvailable`` from /proc/meminfo.

    Instantaneous (no averaging anywhere in its derivation), so it carries none of the lag the
    CPU note above documents. ``MemAvailable``, not ``MemFree``: free memory on a warm box is
    near zero because the kernel holds reclaimable cache, and a gate reading MemFree would
    refuse every build on a perfectly healthy host."""
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return round(int(line.split()[1]) / 1024, 1)
    except (OSError, IndexError, ValueError):
        return None
    return None  # the field is absent on kernels < 3.14 — honestly unavailable, never a guess


def _default_sampler() -> dict:
    """Best-effort, dependency-free host reading. The one part that needs the real host —
    injected in proofs so the predicate physics is provable without it. disk is a filed edge."""
    return {"cpu": _cpu_percent(), "memory_available_mb": _memory_available_mb()}


class SystemRackmountDevice(BaseDevice):
    """The system device (carries CP1-CP6; reports intention/state/settings). It owns the
    host-resource data and serves threshold probes on it: ``advertises`` the menu,
    ``subscribe`` wires a caller's request into a device-local predicate, and the shim pokes
    the subscriber when the predicate holds — the reading never leaving the device (Law 6)."""

    # The menu this device advertises. Each entry names what a caller passes — never an internal
    # method — and which DOORS serve it: "subscribe" (poke me when) and "ask" (may I, right now).
    # Both doors run the SAME device-resolved predicate; disk is the same shape, filed until a
    # consumer asks. memory mounted 2026-08-04 when admission control became its first consumer.
    ADVERTISED: dict[str, dict] = {
        "cpu_threshold": {
            "takes": ["value"],
            "units": "percent of cores runnable",
            "doors": ["subscribe", "ask"],
            "why": "your line is crossed when CPU pressure is AT OR OVER your value — evaluated "
            "here, your value never leaves as a number (Law 6)",
        },
        "memory_floor": {
            "takes": ["value"],
            "units": "MB available",
            "doors": ["subscribe", "ask"],
            "why": "your line is crossed when available memory falls BELOW your value — the "
            "opposite direction from a threshold, which is why it is its own menu item and not "
            "a flag on one (a caller should never have to know which way a metric runs)",
        },
    }

    def __init__(self, sampler=None, device_id: str = "system_rackmount") -> None:
        super().__init__()
        self._sampler = sampler or _default_sampler
        self._device_id = device_id
        self._subs: dict[str, dict] = {}   # sub_id -> {name, address, value, why, probe}
        self._counter = 0

    @property
    def device_id(self) -> str:
        return self._device_id

    # --- (1) advertise the menu ---------------------------------------------

    def advertises(self) -> list[dict]:
        """The probes this device offers — a caller inspects this, then subscribes by menu
        name. Part of the Form v0 #2 surface (inspecting the device shows what it can serve)."""
        return [{"probe": name, **spec} for name, spec in self.ADVERTISED.items()]

    # --- (2)+(3) subscribe; resolve the method internally -------------------

    def subscribe(self, name: str, *, address: str, why: str, value,
                  channel: str = "personal") -> str:
        """Wire a caller's request into a device-local probe and return its subscription id.
        The caller names a MENU ITEM (`name`), a `value`, and a poke `address` — never an
        internal method. The device RESOLVES ITS OWN PREDICATE (`_resolve`) and bakes the
        caller's value into it. An unadvertised name is refused loudly (CP1). The poke body will
        say only THAT the line was crossed, carrying the caller's own value, never the reading."""
        if name not in self.ADVERTISED:
            raise KeyError(f"no advertised probe {name!r}; this device offers "
                           f"{sorted(self.ADVERTISED)} (inspect advertises())")
        trigger = self._resolve(name, value)   # internal — the caller never sees this
        self._counter += 1
        sub_id = f"{name}#{self._counter}"
        probe = Probe(
            why=why,
            trigger=trigger,
            to=address,
            channel=channel,
            body={"alert": name, "crossed": value},  # the caller's line, NOT the owned reading
        )
        self._subs[sub_id] = {"name": name, "address": address, "value": value,
                              "why": why, "probe": probe}
        # GATE CONTACT (DiagnosticBase, cairn/tools/base/diagnostic.py): a predicate was BORN — a rare,
        # low-frequency boundary crossing, worth a standing thin breadcrumb. NOT the per-pulse
        # evaluation (_over/_reading), which would be the firehose the discipline forbids. Thin by
        # design: it points to the subscription (pointer=sub_id) and stamps the time; the value and
        # address live in state() (Law 6 — the breadcrumb carries no owned reading). Held until a
        # receiver is wired (set_diagnostic_receiver), never silently dropped (Law 7). The
        # line-crossing/poke emit is a FILED EDGE, not faked: the poke fires in the shim's _fire
        # (BaseShim is not an emitter) and wants edge-detection — it grows when a real flake needs
        # watching (the targeted-and-temporary instrument discipline).
        self.emit("subscribe", pointer=sub_id)
        return sub_id

    # --- (2') ask: the same predicate, pulled ------------------------------

    def ask(self, name: str, value) -> bool:
        """THE MAY-I DOOR. Is the caller's line crossed RIGHT NOW? Returns the same verdict the
        poke would carry — a bool, never the reading (Law 6).

        No new machinery: it resolves the caller's line into the device's own predicate exactly
        as ``subscribe`` does, and evaluates it once instead of every pulse. That is the whole
        implementation, and it is the argument for the shape — an ask door that returned the
        NUMBER would have needed a second, different thing to exist.

        Deliberately NOT emitting a diagnostic breadcrumb: ``subscribe`` emits because a
        predicate being BORN is rare and low-frequency; an ask fires on every admission check,
        which is the firehose the instrument discipline forbids. It is the answer that matters
        and the caller records what it did with it."""
        if name not in self.ADVERTISED:
            raise KeyError(f"no advertised probe {name!r}; this device offers "
                           f"{sorted(self.ADVERTISED)} (inspect advertises())")
        return bool(self._resolve(name, value)(None, None))

    def _resolve(self, name: str, value):
        """Map an advertised menu name to the device's OWN predicate, closing over device-local
        data so the reading stays home (Law 6). This is the method-resolution the caller is kept
        ignorant of — it only ever named the menu item. Both doors resolve through here, so a
        subscription and an ask on the same item can never drift apart."""
        if name == "cpu_threshold":
            return lambda now, context: self._over("cpu", value)
        if name == "memory_floor":
            return lambda now, context: self._under("memory_available_mb", value)
        raise KeyError(name)  # unreachable — subscribe/ask validated the name

    def _over(self, metric: str, value) -> bool:
        """Is the OWNED reading of ``metric`` at/over ``value``? Samples inside the device; a
        None reading (metric unavailable on this host) is honestly NOT-over, never a fake fire."""
        reading = self._reading().get(metric)
        return reading is not None and reading >= value

    def _under(self, metric: str, value) -> bool:
        """Is the OWNED reading of ``metric`` BELOW ``value``? The floor direction. A None
        reading is honestly NOT-below — same rule as ``_over``: an unavailable metric never
        manufactures a crossing, in either direction."""
        reading = self._reading().get(metric)
        return reading is not None and reading < value

    def _reading(self) -> dict:
        """The device's own, unexported host data. The sampler is injectable so the predicate
        physics is provable without the real host."""
        return self._sampler()

    def subscription_probes(self) -> list[Probe]:
        """The live subscriptions as probes — what this device's shim fires on each pulse."""
        return [sub["probe"] for sub in self._subs.values()]

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The system device — owner of the host's resource predicates (CPU, memory, "
            "disk). It advertises the threshold probes it can serve, and answers on two doors: "
            "it pokes a subscriber when their line is crossed, and it answers an asker whether "
            "their line is crossed right now — evaluating the predicate locally in both cases, "
            "so the host's raw metrics never leave the device.",
            "why": "So any device can get a trigger on a host resource WITHOUT the host's data "
            "being exported and without coupling to the OS (Law 6): the reading stays home, only "
            "the wake-up crosses the bus. This is 'abstract host services device-independently' "
            "made concrete — and it is NOT a central scheduler (that was the goof); scheduling is "
            "the universal heartbeat + shim + probe mechanism.",
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
            "doors": "TWO, one predicate: subscribe (poke me when your line is crossed) and ask "
            "(is my line crossed right now?). Both return a VERDICT; neither returns a reading. "
            "A raw-number introspection door is named and NOT built — no consumer yet",
            "sampler": "dependency-free /proc: CPU as the RUNNABLE count over cores (instantaneous "
            "— the decaying load average it replaced lagged a real load change by ~60s, measured), "
            "memory as MemAvailable. disk is a filed edge — the predicate physics is proven by "
            "injection, not by the host",
            "not": "NOT a central scheduler and NOT a service registry — the interval/date/"
            "quantity/state enum was deleted; a trigger is any predicate (cairn/tools/base/probe.py)",
        }


class SystemRackmountShim(BaseShim):
    """The system device's shim — always on, subscribed to the heartbeat. On each pulse it fires
    the device's live subscription-probes (each sampling the device's own reading, Law 6) and
    pokes the subscribers whose line is crossed, onto the bus. This is where the system device's
    'scheduling' actually happens: not in a bespoke scheduler, but in the universal shim-fires-
    probes-on-the-beat mechanism every device shares."""

    def __init__(self, device: SystemRackmountDevice, bus) -> None:
        super().__init__(bus=bus)
        self._sysdev = device

    @property
    def device_id(self) -> str:
        return self._sysdev.device_id

    def probes(self) -> list[Probe]:
        return self._sysdev.subscription_probes()

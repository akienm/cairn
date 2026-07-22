"""ground_loop — THE HEARTBEAT. One daemon that provides a pulse, and nothing more.

THE MOST BASIC MECHANISM IN CAIRN (converged with Akien 2026-07-18;
``CairnCommons/intentions-other/I-heartbeat-callbacks-and-bus.md``). The ground_loop does NOT
execute, resolve, schedule, route, or write. It BEATS. On each beat it pulses the shim of
every subscribed device; handling the pulse — evaluating callbacks, firing the due ones —
lives in the SHIM (``cairn/base/shim.py``), never here.

THIS FILE CORRECTS A GOOF. The first ground_loop (584aa74) was a generic driver-EXECUTOR
(``run_driver``: resolve a method against a proven-space registry, run it, write through
db_domain). That collapsed three roles — heartbeat + firing + scheduling — into one device
and lost the property that made the design worth having: *a callback is the same unit no
matter what fires it.* The ground_loop is only the heartbeat; a single daemon structure
everyone else hangs their own handlers on. All state stays on disk (via db_domain), reached
by the devices the shim wakes — the heartbeat itself holds none.

WHY SO SMALL: because a rule enforced by a big mechanism is a big mechanism to get wrong.
The heartbeat's whole contract is "pulse the subscribed shims, in order, and leave a legible
beat-record." Everything a device DOES hangs off its own shim's response to the pulse, where
the device's own data and callbacks live (Law 6). The heartbeat carries no device's logic.

``beat`` takes ``now`` (and an optional shared ``context``) EXPLICITLY, so the pulse physics
is provable WITHOUT a wall clock — the same discipline as the tester taking its proof-path
and the shim taking its moment. The OS-specific timer/daemon that calls ``beat`` on a real
cadence is a thin wrapper (like sudo_relay's ``daemon.py``, the one part unprovable without
the OS) — a filed edge, not code here.

FILED EDGES (children of this stone, not faked):
  - SUBSCRIPTION by a file in the device's own folder tree: today a device subscribes its
    shim in-process via ``subscribe(shim)``; discovering subscribers by scanning device code
    trees for a callback-declaration file grows when devices are separate OS processes and the
    heartbeat cannot hold in-process references to them.
  - The wall-clock DAEMON that pulses ``beat`` on a cadence — the OS-specific backing, a thin
    wrapper this stays provable without.
"""

from __future__ import annotations

from cairn.base.device import BaseDevice


class GroundLoopDevice(BaseDevice):
    """The heartbeat as a device (carries CP1-CP6; reports intention/state/settings). Its one
    capability is ``beat`` — pulse every subscribed shim once. It holds no method registry, no
    DB connection, no execution: firing lives in the shims it pulses."""

    def __init__(self, device_id: str = "ground_loop") -> None:
        super().__init__()
        self._device_id = device_id
        self._shims: list = []          # the subscribed shims, pulsed in subscription order
        self._beats = 0
        self._last_beat: dict | None = None

    @property
    def device_id(self) -> str:
        return self._device_id

    # --- subscribe a device's shim to the beat ------------------------------

    def subscribe(self, shim) -> None:
        """Subscribe ``shim`` to the heartbeat. A shim must answer ``device_id`` and ``on_pulse``
        (the handling lives there — CP1: refuse loudly what cannot be pulsed). Idempotent by
        ``device_id`` — subscribing the same device twice does not double-pulse it."""
        if not hasattr(shim, "on_pulse") or not hasattr(shim, "device_id"):
            raise TypeError("only a shim (with device_id + on_pulse) can subscribe to the heartbeat — "
                            "the ground_loop pulses shims; the shim handles the pulse")
        if any(s.device_id == shim.device_id for s in self._shims):
            return
        self._shims.append(shim)

    @property
    def subscribers(self) -> list[str]:
        return [s.device_id for s in self._shims]

    # --- the live roster: the nav across the top (web-server child c) --------

    def roster(self) -> dict:
        """The live heartbeat ROSTER — the devices this heartbeat beats to — published at ALL
        times, as the authoritative nav for the web presentation surface (web-server child c).

        The heartbeat already KNOWS its subscribers: it owns the subscription list (Law 6). This
        is that knowledge published as DATA, no new owner and no new state — the roster IS the
        subscription list, plus each device's live wakefulness (its shim's ``running``) so the
        nav can show who is awake. Available before the first beat too (``beats`` 0, the current
        subscribers): you can navigate to a device the moment it subscribes, not only once it has
        been pulsed. A device ABSENT from the roster cannot appear in the nav — honest by
        construction: you navigate to what the heartbeat beats."""
        return {
            "beats": self._beats,
            "devices": [
                {"device": s.device_id, "awake": bool(getattr(s, "running", False))}
                for s in self._shims
            ],
        }

    # --- the one capability: one beat ---------------------------------------

    def beat(self, now, context: dict | None = None) -> dict:
        """One beat: pulse every subscribed shim once, in order, and return a BEAT-RECORD — what
        was pulsed and what each pulse did. A shim that raises before its own batch-safe firing
        becomes a loud, permanent entry and does NOT stop the beat reaching the others (CP2,
        Law 7). The record is the legibility surface: a beat is evidence (LEARNING, not silent
        RUNNING) — the heartbeat is observable by construction."""
        context = context or {}
        pulses: list[dict] = []
        for shim in self._shims:
            try:
                pulses.append(shim.on_pulse(now, context))
            except Exception as exc:  # noqa: BLE001 — one shim failing cannot stop the heartbeat
                pulses.append({"device": shim.device_id, "outcome": "refused",
                               "error": f"{type(exc).__name__}: {exc}"})
        record = {
            "beat": self._beats + 1,
            "date": str(now),
            "pulsed": self.subscribers,
            "pulses": pulses,
        }
        self._beats += 1
        self._last_beat = record
        return record

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The heartbeat — one daemon that provides a pulse, and nothing more. On each "
            "beat it pulses the shim of every subscribed device; the handling (firing due "
            "callbacks) lives in the shim, not here.",
            "why": "A single daemon structure everyone else hangs their own handlers on. Keeping "
            "the heartbeat to ONLY a pulse means a callback is the same unit no matter what fires "
            "it, and no device's logic rots inside the beat — the goof (an executor here) collapsed "
            "three roles into one and lost that.",
        }

    def state(self) -> dict:
        return {
            "beats": self._beats,
            "subscribers": self.subscribers,
            "last_pulsed_count": len((self._last_beat or {}).get("pulsed", [])),
        }

    def settings(self) -> dict:
        return {
            "does": "pulse subscribed shims, in order; leave a beat-record",
            "does_not": "execute, resolve, schedule, route, or write — firing lives in the shim; "
            "durable state lives in db_domain, reached by the devices the shim wakes",
            "cadence": "none here — beat takes 'now' explicitly, so the pulse is provable without a "
            "clock; the OS timer/daemon that calls beat on a real cadence is a filed thin wrapper",
            "subscription": "in-process via subscribe(shim); file-in-the-device's-tree discovery is "
            "a filed edge for when devices are separate OS processes",
            "roster": "publishes roster() at all times — the devices it beats to, each with live "
            "wakefulness — as the nav for the web presentation surface (web-server child c); no new "
            "owner, it IS the subscription list this device already owns (Law 6)",
        }

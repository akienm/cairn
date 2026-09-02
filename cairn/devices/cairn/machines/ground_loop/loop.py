"""ground_loop — THE HEARTBEAT AND THE DEVICE LIST. Nothing more.

Provides a heartbeat. Provides a list of devices it most recently provided a
heartbeat to. If its code is newer than what this process holds, it restarts
itself. Two flags control behavior: COMMAND_EXIT (stop) and
COMMAND_DO_NOT_RESTART (suppress the drift-triggered exit during development).

IT DOES NOT JUDGE. It does not bench devices, it does not raise trouble tickets,
it does not decide whether a device is broken. A device whose probe fails to
import simply does not get those probes on that beat — the heartbeat keeps
beating, the device stays on the roster, and the import is retried next pass
(gated on mtime, so unchanged files cost one stat). Corrected 2026-09-02 after
three days of Akien saying the same thing (CC-- x3 2026-08-29, then again
2026-08-31, then 2026-09-02): the bench/trouble/staleness-blame machinery was
complexity the heartbeat should never have had.

``beat`` takes ``now`` (and an optional shared ``context``) EXPLICITLY, so the
pulse physics is provable WITHOUT a wall clock.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.device import BaseDevice
from cairn.devices.cairn.machines.ground_loop.discovered import DiscoveredShim
from cairn.devices.cairn.machines.ground_loop.discovery import ProbeCache, PulseCache
from cairn.devices.cairn.machines.ground_loop.liveness import read_liveness, write_liveness
from cairn.devices.cairn.machines.ground_loop import staleness as _staleness


def liveness_pane_data(now, home=None) -> dict:
    """The LIVENESS pane's DATA — the read face's own answer, untouched."""
    return {
        "reports": "the resident singleton's liveness record (instance 0), read from disk "
        "at request time — whatever process serves this page",
        **read_liveness(now, home),
    }


ARBITRATION_THRESHOLD_S = 120.0


def arbitrate_newcomer(now, home) -> dict:
    """Pure decision: should a newcomer that lost the singleton claim kill the
    incumbent or exit? Reads only the liveness record (owned data, Law 6).

    Returns {"action": "takeover"|"exit", "pid": int|None, "age_s": float|None,
             "reason": str}.

    The 120s threshold is two beat cycles at the ruled 60s cadence."""
    found = read_liveness(now, home)
    record = found.get("record") or {}
    age_s = found.get("age_s")
    pid = record.get("pid")

    if age_s is None:
        return {"action": "exit", "pid": pid, "age_s": age_s,
                "reason": found.get("lack", "no liveness record")}

    if age_s > ARBITRATION_THRESHOLD_S:
        return {"action": "takeover", "pid": pid, "age_s": age_s,
                "reason": f"incumbent liveness is {age_s:.1f}s old (>{ARBITRATION_THRESHOLD_S}s)"}

    return {"action": "exit", "pid": pid, "age_s": age_s,
            "reason": f"incumbent is healthy ({age_s:.1f}s old)"}


class GroundLoopDevice(BaseDevice):
    """The heartbeat as a device. Its one capability is ``beat`` — pulse every
    subscribed shim once. It holds no method registry, no DB connection, no
    execution, no bench, no trouble lane: firing lives in the shims it pulses."""

    def __init__(self, device_id: str = "ground_loop", liveness_home=None,
                 discover=None, bus=None, staleness=None,
                 pulse_finder=None) -> None:
        super().__init__()
        self._device_id = device_id
        self._liveness_home = liveness_home
        self._shims: list = []
        self._beats = 0
        self._last_beat: dict | None = None
        self._discover = discover
        self._bus = bus
        self._probe_cache = None
        self._discovered: dict = {}
        self._staleness = staleness or _staleness.module_drift
        self._pulse_finder = pulse_finder
        self._pulse_cache = None
        self._pulse_events: list = []
        self._stale = False

    @property
    def stale(self) -> bool:
        return self._stale

    @property
    def device_id(self) -> str:
        return self._device_id

    # --- subscribe a device's shim to the beat ------------------------------

    def subscribe(self, shim) -> None:
        """Subscribe ``shim`` to the heartbeat. Idempotent by ``device_id``."""
        if not hasattr(shim, "on_pulse") or not hasattr(shim, "device_id"):
            raise TypeError("only a shim (with device_id + on_pulse) can subscribe to the heartbeat — "
                            "the ground_loop pulses shims; the shim handles the pulse")
        if any(s.device_id == shim.device_id for s in self._shims):
            return
        self._shims.append(shim)
        self.emit("subscribe", pointer=shim.device_id)

    @property
    def subscribers(self) -> list[str]:
        return [s.device_id for s in self._shims]

    # --- the live roster: the nav across the top ----------------------------

    def roster(self) -> dict:
        """The devices this heartbeat beats to, published at all times."""
        return {
            "beats": self._beats,
            "devices": [
                {"device": s.device_id, "awake": bool(getattr(s, "running", False))}
                for s in self._shims
            ],
        }

    def shim_for(self, device_id: str):
        """The subscribed shim for ``device_id``, or None."""
        for s in self._shims:
            if s.device_id == device_id:
                return s
        return None

    # --- the disk roster (no bench, no judging) -----------------------------

    def _check_staleness(self) -> None:
        """Set ``self._stale`` if this process's code has drifted from disk.
        The runner reads ``stale`` and exits; that is the only consequence."""
        if self._stale:
            return
        try:
            findings = self._staleness() or []
        except Exception:  # noqa: BLE001
            return
        if any(f.get("evidence") in _staleness.DRIFTED for f in findings):
            self._stale = True

    def _reconcile(self, now=None) -> None:
        """Rebuild the whole roster from DISK, both surfaces, one pass."""
        pulse_active = self._reconcile_pulses(now)
        self._reconcile_probes(pulse_active)
        self._attach_pulses(pulse_active)
        self._check_staleness()

    def _reconcile_pulses(self, now=None) -> dict:
        """Diff found-vs-known over groundloop/pulse.py files."""
        if self._pulse_finder is None:
            return {}
        if self._pulse_cache is None:
            self._pulse_cache = PulseCache()
        try:
            events = self._pulse_cache.reconcile(self._pulse_finder())
        except Exception as exc:  # noqa: BLE001
            self.emit("pulse_discovery_refused", pointer="disk",
                      values={"error": f"{type(exc).__name__}: {exc}"})
            events = []
        for ev in events:
            ev["beat"] = self._beats + 1
            if now is not None:
                ev["at"] = str(now)
            self._pulse_events.append(ev)
            self.emit("pulse_" + ev["event"], pointer=ev["device"], values=dict(ev))
        del self._pulse_events[:-50]
        active: dict[str, list] = {}
        for entry in self._pulse_cache.active():
            active.setdefault(entry["device"], []).append(entry)
        return active

    def _attach_pulses(self, pulse_active: dict) -> None:
        """Hand each device's activated pulse modules to the ONE shim fronting it."""
        if self._pulse_cache is None:
            return
        for device_id, entries in pulse_active.items():
            if self.shim_for(device_id) is None:
                folder = str(Path(entries[0]["path"]).parent)
                shim = DiscoveredShim(device_id, folder, bus=self._bus)
                self._discovered[device_id] = shim
                self._shims.append(shim)
                self.emit("discovered", pointer=device_id,
                          values={"folder": folder, "pulse_files": len(entries)})
        for shim in self._shims:
            if hasattr(shim, "set_pulse_modules"):
                shim.set_pulse_modules(self._pulse_cache.modules_for(shim.device_id))

    def _reconcile_probes(self, pulse_active: dict | None = None) -> None:
        """Rebuild the probe roster from DISK. No bench, no judging — a device
        whose probes fail to import simply doesn't get those probes this beat."""
        pulse_active = pulse_active or {}
        if self._discover is None:
            return
        if self._probe_cache is None:
            self._probe_cache = ProbeCache()
        try:
            found = self._discover(cache=self._probe_cache)
        except Exception as exc:  # noqa: BLE001
            self.emit("discovery_refused", pointer="disk",
                      values={"error": f"{type(exc).__name__}: {exc}"})
            return
        hand_held = {s.device_id for s in self._shims
                     if s.device_id not in self._discovered}
        for device_id, entry in found.items():
            if device_id in hand_held:
                continue
            shim = self._discovered.get(device_id)
            if shim is None:
                shim = DiscoveredShim(device_id, entry["folder"], bus=self._bus)
                self._discovered[device_id] = shim
                self._shims.append(shim)
                self.emit("discovered", pointer=device_id,
                          values={"folder": entry["folder"], "probes": len(entry["probes"])})
            shim.set_probes(entry["probes"], entry["folder"])
        gone = [d for d in self._discovered
                if d not in found and d not in pulse_active]
        for device_id in gone:
            shim = self._discovered.pop(device_id)
            self._shims = [s for s in self._shims if s is not shim]
            self.emit("undiscovered", pointer=device_id,
                      values={"reason": "probes folder no longer on disk"})

    # --- the one capability: one beat ---------------------------------------

    def beat(self, now, context: dict | None = None) -> dict:
        """One beat: pulse every subscribed shim once, in order, and return a
        BEAT-RECORD. A shim that raises does NOT stop the beat reaching the
        others."""
        context = context or {}
        self._reconcile(now)
        pulses: list[dict] = []
        for shim in list(self._shims):
            try:
                pulses.append(shim.on_pulse(now, context))
            except Exception as exc:  # noqa: BLE001
                error = f"{type(exc).__name__}: {exc}"
                pulses.append({"device": shim.device_id, "outcome": "refused", "error": error})
                self.emit("pulse_refused", pointer=shim.device_id,
                          values={"beat": self._beats + 1, "error": error})
        record = {
            "beat": self._beats + 1,
            "date": str(now),
            "pulsed": self.subscribers,
            "pulses": pulses,
        }
        self._beats += 1
        self._last_beat = record
        if self._liveness_home is not None:
            write_liveness(now, self.state(), os.getpid(), self._liveness_home)
        return record

    # --- the declared pane --------------------------------------------------

    def declared_panes(self) -> list[dict]:
        return [{
            "kind": "liveness",
            "label": "Liveness",
            "handler": lambda: liveness_pane_data(datetime.now(timezone.utc).astimezone()),
        }]

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The heartbeat — provides a pulse and a list of devices it beats to. "
            "If its code is newer, it restarts itself. That is all.",
            "why": "A single daemon structure everyone else hangs their own handlers on. Keeping "
            "the heartbeat to ONLY a pulse means a probe is the same unit no matter what fires "
            "it, and no device's logic rots inside the beat.",
        }

    def state(self) -> dict:
        return {
            "beats": self._beats,
            "subscribers": self.subscribers,
            "last_pulsed_count": len((self._last_beat or {}).get("pulsed", [])),
            "pulse_services": self._pulse_cache.active() if self._pulse_cache else [],
            "pulse_refusals": self._pulse_cache.refusals() if self._pulse_cache else [],
            "pulse_events": list(self._pulse_events),
            "stale": self._stale,
        }

    def settings(self) -> dict:
        return {
            "does": "pulse subscribed shims, in order; leave a beat-record; list devices",
            "does_not": "judge, bench, raise trouble tickets, execute, resolve, schedule, "
            "route, or write — firing lives in the shim; durable state lives in db_domain",
            "cadence": "none here — beat takes 'now' explicitly; the wall-clock backing is "
            "__main__.py (python3 -m cairn.devices.cairn.machines.ground_loop)",
        }

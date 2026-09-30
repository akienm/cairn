"""BeatProbes — a device fires its own clock probes from its own groundloop/pulse.py.

Ticket 32959e65ec5a (2026-09-30). Since bae622881f03 the heartbeat calls each
``groundloop/pulse.py`` and nothing else: no probes/ discovery, no shims, no bus. So a
device that owns clock probes fires them itself, on its own pulse, and this is the one
firer every such pulse composes — written once, so the crossing memory, the refusal
isolation and the cleared set are not re-derived per device (Law 1).

IT FIRES THROUGH BaseShim, never beside it. A private ``_Firer`` subclass carries the
shim's ``on_pulse`` whole — poke at the crossing, ``while_true``, ``enough`` retiring a
watch, a raising trigger recorded and the rest still firing, overdue — so a probe fired
from a pulse means exactly what it meant when the loop fired it. The firer never wires
delivery: it posts, it does not receive, so ``_delivery_wired`` is set at birth.

THE BUS IS INJECTED, NEVER IMPORTED. ``cairn/tools/base`` is a gate by the determinism
walk and may not reach an oracle; ``bus_client`` reaches inference_domain. So the pulse
that composes this hands the bus in — an object, or a zero-argument factory resolved on
the first beat (a pulse module is imported by the heartbeat on every change, and building
a bus at import would cost a connection per edit). The bus also rides the pulse context
as ``context['bus']``, because a probe that ASKS over the bus (the trouble panel) needs it.

IT FLUSHES ITS OWN BUS, once per beat. ``BusDevice.post`` only appends to a ring;
``flush()`` is what writes it down. The loop flushed every device's ring until
bae622881f03 took the bus away from it, so a poke that is never flushed is a poke nobody
receives — the silent failure Law 7 forbids. A flush that raises is recorded under
``flush`` as ``{'error': ...}``, never raised: one bad write must not stop the beat.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from cairn.tools.base.probe import Probe
from cairn.tools.base.shim import BaseShim


class _Firer(BaseShim):
    """BaseShim's on_pulse, fed the loaded probes. Posts only; never wired for delivery."""

    def __init__(self, device_id: str) -> None:
        self._id = device_id
        self._loaded: list[Probe] = []
        super().__init__(bus=None)
        self._delivery_wired = True

    @property
    def device_id(self) -> str:
        return self._id

    def probes(self) -> list[Probe]:
        return list(self._loaded)


class BeatProbes:
    """Load ``<folder>/probes/<name>.py`` for each name and fire them on each pulse."""

    def __init__(self, device_id: str, folder, names, bus=None) -> None:
        self._device_id = device_id
        self._folder = Path(folder)
        self._names = tuple(names)
        self._bus_given = bus
        self._bus = None
        self._resolved = False
        self._firer = _Firer(device_id)
        self._held: dict = {}     # name -> (mtime, Probe)

    def roster(self) -> tuple:
        return self._names

    def bind(self, bus) -> None:
        """Replace the bus outright — a proof's stub, or a pulse rebuilding a dead one."""
        self._bus_given = bus
        self._bus = bus
        self._resolved = True
        self._firer._bus = bus

    def _resolve_bus(self):
        if not self._resolved:
            given = self._bus_given
            self._bus = given() if callable(given) and not hasattr(given, "post") else given
            self._resolved = True
            self._firer._bus = self._bus
        return self._bus

    def _load(self) -> list[dict]:
        """Refresh every named probe against its mtime; return the names that did not load."""
        missing: list[dict] = []
        loaded: list[Probe] = []
        for name in self._names:
            path = self._folder / "probes" / f"{name}.py"
            try:
                mtime = path.stat().st_mtime_ns
            except OSError:
                self._held.pop(name, None)
                missing.append({"name": name, "reason": f"no module at {path}"})
                continue
            held = self._held.get(name)
            if held is None or held[0] != mtime:
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"cairn._beat_probe.{self._device_id}.{name}", path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    probe = getattr(mod, "PROBE", None)
                    if not isinstance(probe, Probe):
                        raise TypeError(f"PROBE is {type(probe).__name__}, not a Probe")
                except Exception as exc:  # noqa: BLE001 — one bad module must not stop the beat
                    self._held.pop(name, None)
                    missing.append({"name": name, "reason": f"{type(exc).__name__}: {exc}"})
                    continue
                held = (mtime, probe)
                self._held[name] = held
            loaded.append(held[1])
        self._firer._loaded = loaded
        return missing

    def probes(self) -> list[Probe]:
        """The named probes as they load this instant — a read, not a fire."""
        self._load()
        return self._firer.probes()

    def on_pulse(self, now, context: dict | None = None) -> dict:
        context = context if isinstance(context, dict) else {}
        missing = self._load()
        bus = self._resolve_bus()
        context.setdefault("bus", bus)
        record = self._firer.on_pulse(now, context)
        record["missing"] = missing
        if bus is None:
            record["flush"] = None
        else:
            try:
                record["flush"] = bus.flush()
            except Exception as exc:  # noqa: BLE001 — Law 7: recorded, never raised
                record["flush"] = {"error": f"{type(exc).__name__}: {exc}"}
        return record

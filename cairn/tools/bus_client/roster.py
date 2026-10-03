"""DeviceRoster — the device list on disk, and the shims a client has asked for.

Ticket efb670ff1dd8 (2026-09-30). Until then every client of this tool (``connect_bus``,
``connect_system``, ``reach``) built a private ground loop inside itself to hold its shims and
to answer the web server's nav. That was a second heartbeat in every client. The heartbeat is
the resident one alone (bae622881f03); this object is what a client actually needed from the
private one, and nothing else:

  * ``roster()`` — the nav: every fitted device (``cairn.tools.base.deviceness``), each with
    whether its held shim is awake, plus ``beats`` read from the heartbeat's own liveness
    record. It never counts beats itself; the heartbeat is the only thing that beats.
  * ``shim_for(name)`` — a device's shim, loaded from disk the first time it is asked for: the
    concrete ``<device folder>/shim.py`` when there is one, else a ``DiscoveredShim`` fronting
    the rack device's ``probes/`` folder. Every answer found is held.
  * ``hold(shim)`` / ``pulse(now)`` — the shims a client wires, pulsed once, in the order held.
    A pulse wires each shim's delivery; it is not a heartbeat and it has no cadence.
"""
from __future__ import annotations

from datetime import datetime, timezone


class DeviceRoster:
    """The fitted devices on disk, and the shims held for them."""

    def __init__(self, bus, root=None) -> None:
        from cairn.tools.bus_client import bus_client

        self._bus = bus
        self._root = root if root is not None else bus_client._CLASS_ROOT
        self._held: dict = {}          # device_id -> shim, in the order held

    # --- the held shims -----------------------------------------------------

    def hold(self, shim) -> None:
        """Keep ``shim``. Idempotent by ``device_id`` — the first one held stays."""
        if shim.device_id in self._held:
            return
        self._held[shim.device_id] = shim

    @property
    def held(self) -> list[str]:
        return list(self._held)

    def shim_for(self, name: str):
        """The held shim for ``name``; else its concrete shim from disk; else a
        ``DiscoveredShim`` when ``name`` is a fitted device; else None. Held once found."""
        shim = self._held.get(name)
        if shim is not None:
            return shim
        from cairn.tools.bus_client.bus_client import _load_device_shim

        shim = _load_device_shim(name, self._bus)
        if shim is None:
            shim = self._discovered(name)
        if shim is not None:
            self.hold(shim)
        return shim

    def _discovered(self, name: str):
        """A ``DiscoveredShim`` fronting a rack device's ``probes/`` folder, or None when
        ``name`` is not in the rack (ticket a808e21d646f)."""
        from cairn.tools.base.deviceness import fitted_device_ids

        if name not in fitted_device_ids(self._root):
            return None
        from cairn.devices.cairn.machines.ground_loop.discovered import DiscoveredShim
        from cairn.tools.rack.rack import rack

        for device_id, folder, _shim in rack(self._root):
            if device_id == name:
                return DiscoveredShim(name, str(folder / "probes"), bus=self._bus)
        return None

    # --- the nav ------------------------------------------------------------

    def roster(self) -> dict:
        """``{"beats", "devices": [{"device", "awake"}]}`` — the shape the web server reads."""
        from cairn.tools.base.deviceness import fitted_device_ids

        return {
            "beats": self._beats(),
            "devices": [
                {"device": d, "awake": bool(getattr(self._held.get(d), "running", False))}
                for d in sorted(fitted_device_ids(self._root))
            ],
        }

    @staticmethod
    def _beats() -> int:
        from cairn.tools.liveness.liveness import read_liveness

        record = read_liveness(datetime.now(timezone.utc)).get("record")
        if record is None:
            return 0
        return (record.get("state") or {}).get("beats", 0)

    # --- one pulse of the held shims ----------------------------------------

    def pulse(self, now, context: dict | None = None) -> dict:
        """Pulse every held shim once, in the order held. A shim that raises is recorded
        as refused and the others are still pulsed."""
        from cairn.tools.base.probe import _pulse

        context = _pulse(context)
        pulses: list[dict] = []
        for shim in list(self._held.values()):
            try:
                pulses.append(shim.on_pulse(now, context))
            except Exception as exc:  # noqa: BLE001 — one shim must not stop the others
                pulses.append({"device": shim.device_id, "outcome": "refused",
                               "error": f"{type(exc).__name__}: {exc}"})
        return {"pulsed": list(self._held), "pulses": pulses}

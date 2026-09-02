"""harbor_master/device.py — the fleet register as a device.

The harbor_master's machinery (register.py, voyage.py, clearance.py) predates its
device class. This wraps the existing modules behind a BaseDevice face so the
harbor can be addressed on the bus — which is what 29 probes across the system are
trying to do.

Crossing notifications from emit() are the PRIMARY update path: each notification
patches the cached fleet register in place. A periodic reconciliation scan
(every _RECONCILE_EVERY heartbeat beats, fired by the shim) replaces the cache
from disk — the backstop that catches anything the notifications missed.

Receives mail through two paths:
  - verb "crossing" — patches the cached register from the crossing body
  - verbless receive() — BaseDevice default records to DataRecorder
"""

from __future__ import annotations

from datetime import datetime, timezone

from cairn.tools.base.device import BaseDevice


class HarborMasterDevice(BaseDevice):

    def __init__(self) -> None:
        super().__init__()
        self._device_id = "harbor_master"
        self._fleet_cache: dict | None = None
        self._cache_at: str | None = None
        self._crossings_since_reconcile = 0

    @property
    def device_id(self) -> str:
        return self._device_id

    def declared_verbs(self) -> dict:
        return {"crossing": self._handle_crossing}

    def _handle_crossing(self, envelope: dict) -> dict:
        super().receive(envelope)
        body = envelope.get("body", {})
        self._patch_fleet(body)
        self._crossings_since_reconcile += 1
        return {"accepted": True, "verb": "crossing", "device": self.device_id,
                "patched": True}

    def _patch_fleet(self, crossing: dict) -> None:
        """Patch the cached register from a single crossing notification.

        The body carries component, from, to, direction, ticket. Patching updates
        the standing of the matching boat(s). A boat not yet in the cache (filed
        between reconciliations) is missed here and caught by the next reconcile —
        honest, not silent."""
        if self._fleet_cache is None:
            self.reconcile()
            return
        target = crossing.get("to")
        if not target:
            return
        ticket = crossing.get("ticket")
        component = crossing.get("component", "")
        if ticket:
            for boat in self._fleet_cache.get("open", []):
                if boat["id"] == ticket:
                    boat["standing"] = target
                    break
        comp_name = component.rstrip("/").rsplit("/", 1)[-1] if component else ""
        if comp_name:
            for boat in self._fleet_cache.get("in_port", []):
                if boat["id"] == comp_name:
                    boat["standing"] = target
                    break

    def reconcile(self) -> dict:
        """Full fleet scan — replaces the cache from disk.

        The register walks every ticket and every history — the honest source.
        This is the BACKSTOP; crossing notifications patch between scans."""
        from cairn.devices.cairn.machines.harbor_master.register import register
        self._fleet_cache = register()
        self._cache_at = datetime.now(timezone.utc).isoformat()
        patched = self._crossings_since_reconcile
        self._crossings_since_reconcile = 0
        return {
            "fleet": self._fleet_cache.get("counts", {}),
            "cache_at": self._cache_at,
            "crossings_patched_since_last": patched,
        }

    @property
    def fleet_cache(self) -> dict | None:
        return self._fleet_cache

    def intention(self) -> dict:
        return {
            "what": "Fleet register — compiled index over the boats' own records, "
                    "clearance gate for workflow transitions, voyage view.",
            "why": "The harbor through which workflows voyage. Every boat's standing "
                    "is read from the boat's own record (Law 7 — the register invents "
                    "no truth a boat does not already hold).",
        }

    def state(self) -> dict:
        if self._fleet_cache is not None:
            c = self._fleet_cache.get("counts", {})
            return {
                "total_boats": c.get("fleet", 0),
                "open": c.get("open", 0),
                "in_port": c.get("in_port", 0),
                "cache_at": self._cache_at,
                "crossings_since_reconcile": self._crossings_since_reconcile,
            }
        try:
            from cairn.devices.cairn.machines.harbor_master.register import register
            reg = register()
            return {
                "total_boats": reg["counts"]["fleet"],
                "open": reg["counts"]["open"],
                "in_port": reg["counts"]["in_port"],
            }
        except Exception:
            return {"error": "register unavailable"}

    def settings(self) -> dict:
        return {}

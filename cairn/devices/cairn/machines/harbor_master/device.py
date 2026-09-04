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
from cairn.tools.base.transitions import TERMINAL_STATES


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
        return {**super().declared_verbs(), "crossing": self._handle_crossing}

    def declared_views(self) -> dict:
        return {"map": self._fleet_map}

    def _handle_crossing(self, envelope: dict) -> dict:
        super().receive(envelope)
        body = envelope.get("body", {})
        self._patch_fleet(body)
        self._crossings_since_reconcile += 1
        self.debug_sink.emit("crossing_patched",
                             pointer=body.get("ticket", ""),
                             values={"component": body.get("component", ""),
                                     "to": body.get("to", "")})
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
        self.debug_sink.emit("reconciled",
                             values={"fleet": self._fleet_cache.get("counts", {}),
                                     "crossings_patched": patched})
        return {
            "fleet": self._fleet_cache.get("counts", {}),
            "cache_at": self._cache_at,
            "crossings_patched_since_last": patched,
        }

    def _fleet_map(self) -> dict:
        """The fleet register as data — the view behind ``get map`` and ``show map``."""
        if self._fleet_cache is None:
            self.reconcile()
        return self._fleet_cache

    @classmethod
    def _filter_fleet(cls, fleet: dict, filter_name: str | None) -> dict:
        """Apply a named filter to fleet data. 'open' strips terminal-state boats."""
        if filter_name != "open":
            return fleet
        keep = lambda b: cls._standing_base(b.get("standing", "")) not in TERMINAL_STATES
        open_ = [b for b in fleet.get("open", []) if keep(b)]
        in_port = [b for b in fleet.get("in_port", []) if keep(b)]
        return {
            "open": open_,
            "in_port": in_port,
            "fleet": open_ + in_port,
            "counts": {"open": len(open_), "in_port": len(in_port),
                       "fleet": len(open_) + len(in_port)},
        }

    def _handle_get(self, envelope: dict) -> dict:
        result = super()._handle_get(envelope)
        if result.get("accepted"):
            filt = (envelope.get("body", {}).get("args") or [None])[0]
            result["data"] = self._filter_fleet(result["data"], filt)
        return result

    def _handle_show(self, envelope: dict) -> dict:
        what = envelope.get("body", {}).get("what", "")
        views = self.declared_views()
        view_fn = views.get(what)
        if view_fn is None:
            return {"accepted": False, "verb": "show", "device": self.device_id,
                    "reason": f"no view {what!r}",
                    "available": sorted(views)}
        data = view_fn()
        filt = (envelope.get("body", {}).get("args") or [None])[0]
        data = self._filter_fleet(data, filt)
        text = self._render_view(what, data)
        return {"accepted": True, "verb": "show", "view": what,
                "device": self.device_id, "text": text, "data": data}

    def _render_view(self, name: str, data: dict) -> str:
        if name == "map":
            return self._render_fleet_map(data)
        return super()._render_view(name, data)

    _PRIORITY_ORDER = [
        "THINKME", "TICKETME", "SORTEDME",
        "PROVEME",
        "BUILDME",
        "WATCHME",
        "PROVED", "SUPERSEDED", "RETIRED", "DROPPED", "KILLED", "ABSORBED",
    ]

    @classmethod
    def _standing_short(cls, standing: str) -> str:
        """A display-width standing: WATCHME(probe-name):waiting → WATCHME:waiting,
        prose 'PROVED — long description' → PROVED."""
        if not standing:
            return "?"
        token = standing.split()[0].rstrip(":")
        base = token.split("(")[0].split(":")[0]
        if ":waiting" in token:
            return f"{base}:waiting"
        return base

    @classmethod
    def _standing_base(cls, standing: str) -> str:
        """The root stage only — WATCHME(foo):waiting → WATCHME."""
        return cls._standing_short(standing).split(":")[0]

    @classmethod
    def _standing_sort_key(cls, boat: dict) -> tuple:
        base = cls._standing_base(boat.get("standing", ""))
        is_waiting = ":waiting" in (boat.get("standing") or "")
        try:
            rank = cls._PRIORITY_ORDER.index(base)
        except ValueError:
            rank = len(cls._PRIORITY_ORDER)
        return (rank, is_waiting, boat.get("date", ""), boat.get("id", ""))

    @staticmethod
    def _format_boat(b: dict) -> str:
        date = (b.get("date") or "")[:10]
        standing = HarborMasterDevice._standing_short(b.get("standing", "?"))
        hex_id = b.get("id", "?")[:12]
        title = b.get("title", "")
        return f"  {date:<12s}{standing:<20s}{hex_id:<14s}{title}"

    def _render_fleet_map(self, fleet: dict) -> str:
        counts = fleet.get("counts", {})
        lines = [f"Fleet: {counts.get('fleet', 0)} boats "
                 f"({counts.get('open', 0)} open, {counts.get('in_port', 0)} in port)"]
        all_boats = sorted(
            fleet.get("open", []) + fleet.get("in_port", []),
            key=self._standing_sort_key)
        if not all_boats:
            lines.append("\n  (no boats)")
            return "\n".join(lines)
        current_group = None
        for b in all_boats:
            standing = b.get("standing", "?")
            base = self._standing_base(standing)
            is_waiting = ":waiting" in standing
            group = f"{base}:waiting" if is_waiting else base
            if group != current_group:
                current_group = group
                group_boats = [x for x in all_boats
                               if self._standing_base(x.get("standing", "")) == base
                               and (":waiting" in (x.get("standing") or "")) == is_waiting]
                lines.append(f"\n{group} ({len(group_boats)}):")
            lines.append(self._format_boat(b))
        if self._cache_at:
            lines.append(f"\nCached at: {self._cache_at}")
        return "\n".join(lines)

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

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

import json
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.device import BaseDevice
from cairn.tools.base.transitions import TERMINAL_STATES
from cairn.tools.operator_inbox.inbox import (
    cursor_of,
    format_ticket_row,
    label_sort_key,
    status_label,
)

_SRC_ROOT = Path(__file__).resolve().parents[6]   # ~/dev/src — the root a register source is relative to


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

        The body carries component, from, to, direction, ticket. The ticket's boat
        is RELOADED from its own file through the one reader (cursor_of +
        status_label), never set to the bare target: a crossing to BUILDME leaves
        the ticket at ``[BUILDME:waiting]``, and the label is the ticket's, not the
        notification's (ticket 3feb201c84ea — before, the cache wore the bare
        target while the inbox wore the phase). A boat not in the cache, or a ticket
        that cannot be re-read, triggers a full reconcile — honest, not silent.
        The component's own history standing (its last crossing) is patched to the
        target as before; the map prints it only as a finding when it is prose."""
        if self._fleet_cache is None:
            self.reconcile()
            return
        target = crossing.get("to")
        if not target:
            return
        ticket = crossing.get("ticket")
        component = crossing.get("component", "")
        if ticket:
            boat = next((b for b in self._fleet_cache.get("open", [])
                         if b["id"] == ticket), None)
            reloaded = self._reload_boat(boat) if boat is not None else False
            if not reloaded:
                self.reconcile()
                return
        comp_name = component.rstrip("/").rsplit("/", 1)[-1] if component else ""
        if comp_name:
            for entry in self._fleet_cache.get("in_port", []):
                if entry["id"] == comp_name:
                    entry["standing"] = target
                    break

    @staticmethod
    def _reload_boat(boat: dict) -> bool:
        """Re-read one open boat's ticket file and refresh cursor/label/standing in
        place (the in-port ``boats`` lists hold the same dict). False when the file
        cannot be read — the caller reconciles."""
        src = Path(boat.get("source") or "")
        if not src.is_absolute():
            src = _SRC_ROOT / src
        try:
            doc = json.loads(src.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        cursor = cursor_of(doc.get("workflow_and_state", ""))
        boat["cursor"] = cursor
        boat["label"] = status_label(cursor)
        boat["standing"] = boat["label"]
        return True

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
        """Apply a named filter to fleet data. 'open' strips terminal-state boats —
        from the open lane and from every component's berthed list alike."""
        if filter_name != "open":
            return fleet
        keep = lambda b: (b.get("label") or b.get("standing") or "").split(":")[0] not in TERMINAL_STATES
        open_ = [b for b in fleet.get("open", []) if keep(b)]
        in_port = [{**e, "boats": [b for b in e.get("boats", []) if keep(b)]}
                   for e in fleet.get("in_port", [])]
        findings = list(fleet.get("findings", []))
        return {
            "open": open_,
            "in_port": in_port,
            "findings": findings,
            "fleet": open_ + in_port,
            "counts": {"open": len(open_), "in_port": len(in_port),
                       "fleet": len(open_) + len(in_port), "findings": len(findings)},
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

    def _render_fleet_map(self, fleet: dict) -> str:
        """Two lanes over ONE population. OPEN groups the tickets by their status
        label in priority order; IN PORT groups the same tickets by the component
        they are berthed at. Every row is the standard atom (date, label, id, title)
        from operator_inbox — the same token the inbox and the dashboard print. A
        component whose history's last standing is prose is one FINDING line."""
        counts = fleet.get("counts", {})
        open_ = fleet.get("open", [])
        in_port = fleet.get("in_port", [])
        findings = fleet.get("findings", [])
        lines = [f"Fleet: {counts.get('open', 0)} open boat(s) berthed at "
                 f"{sum(1 for e in in_port if e.get('boats'))} component(s), "
                 f"{counts.get('in_port', 0)} in port"]
        if not open_ and not in_port:
            lines.append("\n  (no boats)")
            return "\n".join(lines)

        lines.append("\nOPEN — by status:")
        by_label: dict[str, list[dict]] = {}
        for b in open_:
            by_label.setdefault(b.get("label") or b.get("standing") or "?", []).append(b)
        for label in sorted(by_label, key=label_sort_key):
            boats = sorted(by_label[label], key=lambda b: (b.get("date", ""), b.get("id", "")))
            lines.append(f"\n{label} ({len(boats)}):")
            for b in boats:
                lines.append(format_ticket_row(b, indent="  "))

        lines.append("\nIN PORT — by component:")
        for entry in in_port:
            boats = entry.get("boats") or []
            if not boats:
                continue
            lines.append(f"\n{entry.get('component', entry.get('id', '?'))} ({len(boats)}):")
            for b in sorted(boats, key=lambda b: (label_sort_key(b.get("label") or ""),
                                                  b.get("date", ""), b.get("id", ""))):
                lines.append(format_ticket_row(b, indent="  "))
        for f in findings:
            lines.append(f"\nFINDING: {f.get('component', '?')} history standing is prose: "
                         f"{str(f.get('standing', ''))[:60]}")
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

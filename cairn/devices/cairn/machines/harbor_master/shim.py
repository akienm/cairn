"""harbor_master/shim.py — the fleet register's always-on front on the heartbeat.

The harbor master is the most-addressed device in the probe fleet: 29 probes send
their findings here. This shim is what makes that delivery path whole — a BaseShim
that wakes a HarborMasterDevice on first delivery.

The periodic reconciliation (every _RECONCILE_EVERY beats) replaces the cached fleet
register from disk — the backstop that catches drift between crossing notifications.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim


class HarborMasterShim(BaseShim):

    _RECONCILE_EVERY = 10

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "harbor_master"

    def _start_device(self):
        from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice
        return HarborMasterDevice()

    def _bare(self) -> dict:
        """A bare ``cairn codemother harbor_master`` answers the fleet's one-line count (outline
        9.4.1.5, ticket f30daa73a599) through the base's one bare hook (59f7456dd9f5)."""
        self._ensure_device()
        c = self._device._fleet_map().get("counts", {})
        return {"exit": 0, "text": f"{c['fleet']} boats ({c['open']} open, {c['in_port']} in port)",
                "data": c, "cached": False}

    def on_pulse(self, now, context=None):
        record = super().on_pulse(now, context)
        if self._device is not None:
            if self._pulses == 1 or self._pulses % self._RECONCILE_EVERY == 0:
                record["reconcile"] = self._device.reconcile()
        return record

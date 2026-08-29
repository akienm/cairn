"""harbor_master/shim.py — the fleet register's always-on front on the heartbeat.

The harbor master is the most-addressed device in the probe fleet: 29 probes send
their findings here. This shim is what makes that delivery path whole — a BaseShim
that wakes a HarborMasterDevice on first delivery.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim


class HarborMasterShim(BaseShim):

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "harbor_master"

    def _start_device(self):
        from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice
        return HarborMasterDevice()

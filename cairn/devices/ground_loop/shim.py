"""ground_loop/shim.py — the heartbeat's own front on itself.

THE CARRIER RULE (Akien, 2026-07-28): there is ONLY EVER ONE WEB SERVER in the whole
system. The ground loop gets a device PAGE the way every device does — a declared pane
the base shim class understands (``declared_panes`` on the device), never a server, a
route, or a port of its own (ticket the-ground-loop-pane-shows-its-state). Subscribe
this shim to the loop it fronts and ground_loop rides the roster like any device: the
nav lists it because the heartbeat beats to it, and the surface reaches its page
through ``active_page()``.

UNLIKE every other shim, this one does not START its device — it FRONTS the chassis it
is subscribed to, HANDED at construction. The heartbeat is already running (it is what
pulses this shim); a shim that lazily built a second GroundLoopDevice would front a
loop nobody beats, and its page would introspect a stranger. Constructor injection is
the honest join: one loop, one shim, the same object on both ends of the subscription.

No probes: the loop is not driven by its own beat — ``on_pulse`` with the base class's
empty ``probes()`` evaluates nothing and fires nothing, so the self-subscription is
inert under the beat (proved in proofs/test_ground_loop.py). It rides its own roster so
the surface can reach it, not so it can wake itself.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim


class GroundLoopShim(BaseShim):
    """The heartbeat's shim: fronts the HANDED loop instance, already running by
    definition — the shim exists to put the loop's own page on the loop's own roster."""

    def __init__(self, loop, bus=None) -> None:
        super().__init__(bus=bus)
        self._device = loop
        self._running = True

    @property
    def device_id(self) -> str:
        return "ground_loop"

    def _start_device(self):
        return self._device

"""web_server/shim.py — the web server's front: a request arrives here and starts the device.

Every shim starts its own device when it is not running (outline 5.7.3.2), and this one is
no different (ticket 0482542c2b7c): listener.py holds the port and hands each request to
``WebServerShim.serve``; the first request wakes a ``WebServerDevice``, and every request
after it is served by that same device. Akien's chain (Q#30, outline 9.6.1): "the http
request arrives at the web server's shim, which launches the web server ... each part is
self initializing."

Who brings the shim up and binds the port is the answer to open-68fe4af67c6d: the ground
loop's pulse (``groundloop/pulse.py``), on the cairn home only (outline 15.3.5, 6.3.7.4).

The roster and the harbor source are injected, as WebServerDevice's are: the listener hands
in the live ones from ``connect_system``; a proof hands in a stub. ``device_factory`` lets a
proof count how many devices were built.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim
from cairn.devices.web_server.server import WebServerDevice


class WebServerShim(BaseShim):
    """The web server's shim: the first ``serve`` starts the device; later ones reuse it."""

    def __init__(self, bus=None, *, roster_source=None, harbor_source=None, port: int = 80,
                 device_factory=None) -> None:
        super().__init__(bus=bus)
        self._roster_source = roster_source
        self._harbor_source = harbor_source
        self._port = port
        self._device_factory = device_factory

    @property
    def device_id(self) -> str:
        return "web_server"

    def _start_device(self) -> WebServerDevice:
        if self._device_factory is not None:
            return self._device_factory()
        return WebServerDevice(self._roster_source, harbor_source=self._harbor_source,
                               port=self._port)

    def serve(self, path: str, method: str = "GET", body: str | None = None):
        """One http request: ``(status, content_type, body)`` from the device, woken if asleep."""
        return self.device().serve(path, method=method, body=body)

"""web_server — a thin presentation surface over the running system (web-server ticket, child b).

The devices on the heartbeat across the top (the roster, child c); the selected device's ACTIVE
page below (its panes, child a). The web server owns NO device state: everything it shows is
pulled live from a device's shim (``active_page``) or the heartbeat (``roster``). It is a dumb
bridge + frame renderer — the intelligence is in the shims, the rendering is pure (``render.py``),
and this device only routes a request to a rendered page.

HOW IT REACHES DEVICES (v0, honest): through the ``ground_loop`` it is given. The heartbeat
already OWNS the roster and holds its subscribers' shims (Law 6); the web server reads the nav
from ``roster()`` and a device's page from that device's shim's ``active_page()``. Devices are
in-process today (the whole spine's shared v0 — ground_loop holds shim references directly), so
the fetch is a direct call. The DESIGNED path is browser ⟷ HTTP ⟷ web_server ⟷ BUS ⟷ shim; the
bus request/reply transport is a FILED EDGE (below), the same separate-process deferral every
device carries — the SHAPE (route → fetch device DATA → render) is here and proven now.

WHAT IS PROVEN HERE vs THE FILED DAEMON: ``serve(path)`` — route a request to (status,
content_type, body) — is pure logic over injected sources, proven green without a socket. The
actual ``http.server`` binding a localhost port lives in ``daemon.py``, the thin OS wrapper the
proof cannot exercise (like ground_loop's wall-clock daemon and sudo_relay's daemon.py).

FILED EDGES (children of this stone, not faked):
  - THE BUS TRANSPORT: fetching a device's active_page over the bus (a request/reply envelope to
    the device's ``personal`` channel, the shim answering) instead of a direct in-process call —
    lands when devices are separate OS processes and the bus carries request/reply.
  - REPORTED-vs-FILED DRIFT on the STATUS pane: comparing a device's reported intention against
    its filed ``intention+why.json`` on disk (child a left the reported side as DATA; this surface
    reads disk intentions). A first cut can live here without coupling the shim to file paths.
  - THE JOURNEY pane (child d, waits on harbor_master) and the SETTINGS circuit-breaker (child e,
    waits on the cgroup-kill sudo script) graft in when those exist.
"""

from __future__ import annotations

from cairn.base.device import BaseDevice
from cairn.web_server import render


class WebServerDevice(BaseDevice):
    """The web presentation surface as a device (carries CP1-CP6; reports intention/state/settings).

    Given a ``roster_source`` (the ground_loop) it routes an HTTP path to a rendered HTML page.
    Owns its listening PORT (a setting; the socket itself is the daemon's, a filed edge). Holds no
    device state — every render pulls live from the roster source and the target device's shim.
    """

    def __init__(self, roster_source, *, port: int = 8787, device_id: str = "web_server") -> None:
        super().__init__()
        self._roster_source = roster_source   # the ground_loop: owns roster() + the shims
        self._port = port
        self._device_id = device_id
        self._served = 0
        self._last_path: str | None = None

    @property
    def device_id(self) -> str:
        return self._device_id

    # --- reaching devices through the heartbeat that owns them --------------

    def _roster(self) -> dict:
        return self._roster_source.roster()

    def _shim_for(self, device: str):
        """The subscribed shim for ``device``, via the heartbeat that holds it (v0 in-process).
        None if no such device is on the heartbeat — you can only view what the heartbeat beats."""
        finder = getattr(self._roster_source, "shim_for", None)
        return finder(device) if callable(finder) else None

    # --- the routing core: a request path -> a rendered page ----------------

    def serve(self, path: str) -> tuple[int, str, str]:
        """Route one request to ``(status, content_type, html)`` — pure over the injected sources,
        no socket. ``/`` is the landing (nav + pick-a-device); ``/device/<id>`` is that device's
        ACTIVE page. An unknown device is a loud, coherent 404 that STILL renders the nav, so you
        can navigate away (Law 7 — a presentation surface collapses the error into a legible shape,
        never a raw crash). Any other path is a 404 the same way."""
        self._served += 1
        self._last_path = path
        roster = self._roster()

        selected = None
        status = 200
        if path in ("/", ""):
            body = render.render_message(
                "Cairn", "Pick a device from the heartbeat above to see its active page.")
        elif path.startswith("/device/"):
            device = path[len("/device/"):].strip("/")
            selected = device
            shim = self._shim_for(device)
            if shim is None:
                status = 404
                body = render.render_message(
                    f"{device}: not on the heartbeat",
                    "No device by that name is beating. Pick one from the nav above.")
                selected = None
            else:
                body = render.render_active_page(shim.active_page())
        else:
            status = 404
            body = render.render_message("Not found", f"No page at {path!r}.")

        nav = render.render_nav(roster, selected=selected)
        title = f"Cairn — {selected}" if selected else "Cairn"
        document = render.render_document(title=title, nav_html=nav, body_html=body)
        return status, "text/html; charset=utf-8", document

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "A thin web presentation surface over the running system — the devices on the "
            "heartbeat across the top, the selected device's ACTIVE page (its panes) below. A dumb "
            "HTTP bridge + frame renderer that owns no device state; everything shown is pulled "
            "live from a device's shim (active_page) or the heartbeat (roster).",
            "why": "Telos 2 — the librarian needs a web interface, and 'a web interface falls out "
            "of the chatbot' only if the surface exists first. Built as a presentation surface "
            "(Law 7): it may render an error into a coherent shape, never a record of truth — which "
            "keeps the intelligence in the shims and the web server trivial (one owner, no state).",
        }

    def state(self) -> dict:
        return {
            "served": self._served,
            "last_path": self._last_path,
            "roster": self._roster(),
        }

    def settings(self) -> dict:
        return {
            "port": self._port,
            "bind": "localhost — single operator (Akien), v0; it exposes device internals and "
            "(later) a kill switch, so it does not listen off-host",
            "owns": "no device state — a pure presentation surface (Law 7); content is each "
            "device's, reached through the heartbeat that holds it",
            "transport": "v0 reaches devices in-process through the ground_loop; the browser ⟷ HTTP "
            "⟷ bus ⟷ shim request/reply transport is a filed edge (separate-process deferral)",
            "daemon": "the http.server binding this port lives in daemon.py — the thin OS wrapper "
            "the proof does not exercise; serve() (route → render) is proven green without a socket",
        }

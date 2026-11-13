"""librarian/shim.py — the librarian's always-on front on the heartbeat.

The shim is the piece that is always on (BaseShim): it receives its device's mail and
STARTS THE DEVICE IF IT IS NOT RUNNING — wake-to-a-poke, the shim's process-manager
role. Waking the librarian means composing the live face: the device over the graph
trees plus the ChatSession over inference_domain's dual seam. Live wiring happens HERE,
at the wake, never at import — trees.py and chat.py stay import-pure and provable.

THE CARRIER RULE (Akien, 2026-07-28): there is ONLY EVER ONE WEB SERVER in the whole
system. The librarian owns a PAGE that the extant web server displays — its chat window
is a pane the base shim class understands (declared_panes) — never a server, a route, or
a port of its own. Subscribe this shim to the ground loop and the librarian rides the
roster like any device: the surface reaches it through ``active_page()``, a POSTed
utterance reaches it through ``deliver()``.

No probes yet: the librarian is not driven by the beat — it wakes to pokes (a walk,
a deposit, a chat turn). It rides the heartbeat so the system can reach it, not so a
clock can spin it (NO DAEMONS).
"""

from __future__ import annotations

import os
import platform
import sys

from cairn.tools.base.shim import BaseShim
from cairn.devices.librarian.device import LibrarianDevice

CHAT_PATH = "/device/librarian"
NO_BROWSER_VAR = "CAIRN_LIBRARIAN_NO_BROWSER"


class LibrarianShim(BaseShim):
    """The librarian's shim: one per device, subscribed to the ground loop.

    ``session_factory(device) -> ChatSession`` is injectable so a proof can wake a
    controlled face; the default composes the LIVE one (dual seam, the library tree)
    at wake time. The wake happens on the first poke — a page query or a delivery —
    and the same woken device serves every poke after it."""

    def __init__(self, bus=None, *, session_factory=None, tree: str = "library") -> None:
        super().__init__(bus=bus)
        self._session_factory = session_factory
        self._tree = tree

    @property
    def device_id(self) -> str:
        return "librarian"

    def _start_device(self) -> LibrarianDevice:
        device = LibrarianDevice()
        factory = self._session_factory
        if factory is None:
            def factory(dev, _tree=self._tree, _bus=self._bus):
                from cairn.devices.librarian.chat import ChatSession
                from cairn.devices.librarian.live import dual_seam
                return ChatSession(resolve=dual_seam(_bus), tree=_tree, dev=dev)
        device.attach_chat(factory(device))
        return device

    def _bare(self) -> dict:
        """A bare call wakes the librarian (ticket d832a24e5144; Q#30, Akien 2026-11-06: "a bare
        call to librarian should 1) launch that device's shim, which 2) parses the request
        (nothing) and so 3) launches the librarian and 4) launches a browser"). The browser is
        the caller's to open — it holds the terminal; this answer prints no URL. A hook on
        BaseShim (ticket 59f7456dd9f5), so the root vocabulary stays inherited whole."""
        self._ensure_device()
        return {"exit": 0, "text": "librarian: awake; its chat opens in your browser",
                "data": {"open": CHAT_PATH}, "cached": False}


def chat_url() -> str:
    """The librarian's chat page on the one web server: the cairn home (CAIRN_HOME_HOST, outline
    15.3.5; this box when unset or when it IS the home) on CAIRN_WEB_SERVER_PORT (80)."""
    host = os.environ.get("CAIRN_HOME_HOST", "").strip()
    if not host or host == platform.node():
        host = "127.0.0.1"
    port = os.environ.get("CAIRN_WEB_SERVER_PORT", "80").strip() or "80"
    return f"http://{host}{'' if port == '80' else ':' + port}{CHAT_PATH}"


def open_chat(opener=None) -> int:
    """A bare `cairn librarian`: the shim wakes the device on the bus, then this process — the
    one holding the terminal — opens the chat page. Skipped when stdout is not a terminal or
    CAIRN_LIBRARIAN_NO_BROWSER is set. Never prints the URL (Q#30)."""
    from cairn.tools.base.shim import cli_main

    rc = cli_main(LibrarianShim, [])
    if rc == 0 and sys.stdout.isatty() and not os.environ.get(NO_BROWSER_VAR):
        if opener is None:
            import webbrowser
            opener = webbrowser.open
        opener(chat_url())
    return rc

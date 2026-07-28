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

No callbacks yet: the librarian is not driven by the beat — it wakes to pokes (a walk,
a deposit, a chat turn). It rides the heartbeat so the system can reach it, not so a
clock can spin it (NO DAEMONS).
"""

from __future__ import annotations

from cairn.base.shim import BaseShim
from cairn.librarian.trees import LibrarianDevice


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
            def factory(dev, _tree=self._tree):
                # Live composition, deferred to the wake: both verbs through
                # inference_domain's one door, the face over the ratified tree.
                from cairn.librarian.chat import ChatSession
                from cairn.librarian.live import dual_seam
                return ChatSession(resolve=dual_seam(), tree=_tree, dev=dev)
        device.attach_chat(factory(device))
        return device

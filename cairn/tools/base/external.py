"""external — a bus participant with no poke path.

An external participant (CC, Akien) has an ADDRESS, a FEED, and VERBS like any
device, but no running device process and no delivery poke. It reads its own
feed at its own arrival moment — CC via a session hook, Akien via the web server.

The adapter gives an external entity its bus identity: a device_id, an announce
menu, and the ability to post and read. It is NOT a shim — a shim carries a device
and receives pokes. This is the bare minimum for a participant who pulls rather
than being pushed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cairn.devices.cairn.machines.bus.bus import BusDevice


class ExternalParticipant:
    """A bus participant with no poke path. Posts, reads, and announces — never poked."""

    def __init__(self, device_id: str, bus: "BusDevice",
                 verbs: list[str] | None = None) -> None:
        self._device_id = device_id
        self._bus = bus
        self._verbs = list(verbs or [])

    @property
    def device_id(self) -> str:
        return self._device_id

    def announce(self) -> dict:
        """Publish the verb menu onto the announce channel. Same shape as a device's
        _announce_menu — compiled, not hand-listed."""
        return self._bus.post(
            sender=self._device_id, to=self._device_id, channel="announce",
            why="external participant menu",
            body={"verbs": sorted(self._verbs)},
        )

    def post(self, *, to: str, channel: str = "personal", why: str,
             verb: str = "", body: dict | None = None,
             reply_to: str | None = None) -> dict:
        """Post as this participant."""
        return self._bus.post(
            sender=self._device_id, to=to, channel=channel, why=why,
            verb=verb, body=body, reply_to=reply_to,
        )

    def read(self, *, channel: str | None = None) -> list[dict]:
        """Read this participant's own feed — the arrival surface."""
        return self._bus.read(to=self._device_id, channel=channel)

    def unread(self) -> list[dict]:
        """Personal-channel mail that has not been delivered (no poke path — these
        wait until the participant reads)."""
        return self._bus.undelivered(to=self._device_id)

    def request(self, *, to: str, channel: str = "personal", why: str,
                verb: str = "", body: dict | None = None,
                timeout: float = 30.0) -> dict:
        """Synchronous exchange as this participant."""
        return self._bus.request(
            sender=self._device_id, to=to, channel=channel, why=why,
            verb=verb, body=body, timeout=timeout,
        )

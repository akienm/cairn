"""cairn/device.py — the cairn system device.

The top-level device. Its machines (ground_loop, harbor_master, bus) are the
system's own infrastructure. BaseDevice.receive() records inbound mail to a
DataRecorder for later evaluation.
"""

from __future__ import annotations

from cairn.tools.base.device import BaseDevice


class CairnDevice(BaseDevice):

    def __init__(self, bus=None, roots=None, roster_root=None) -> None:
        super().__init__()
        self._device_id = "cairn"
        # Where the sleep cycle's standing state and roster are read (ticket bf146e9e3967,
        # D4/D7): None live, a fixture's roots and roster folder under a proof.
        self._roots = roots
        self._roster_root = roster_root
        # INJECTED, never imported (ticket 9579a6f9cec6). This device held a
        # ``TroubleDevice()`` until 2026-09-07 and the isolation sieve was red about it
        # every run: no device may import another device (db_domain is the sole
        # exception). The shim that starts this device is the one thing that knows both
        # it and the bus, so the bus arrives from there — the same place every other
        # routing question for a device is answered (BaseShim's ruling, 2026-08-04).
        self._bus = bus

    @property
    def device_id(self) -> str:
        return self._device_id

    def intention(self) -> dict:
        return {
            "what": "The cairn system device — top-level holder of ground_loop, "
                    "harbor_master, and bus.",
            "why": "Every device has a presence on the bus (Akien, 2026-08-11). "
                    "The system itself is a device and answers its own mail.",
        }

    def state(self) -> dict:
        return {}

    def settings(self) -> dict:
        return {}

    def declared_verbs(self) -> dict:
        """``sleep-token`` is a device's answer to the hand (ticket bf146e9e3967, D2(d));
        ``sleep-cycle`` is the operator's face on the rotation: mint or show."""
        return {**super().declared_verbs(),
                "sleep-token": self._handle_sleep_token,
                "sleep-cycle": self._handle_sleep_cycle}

    def _handle_sleep_token(self, envelope: dict) -> dict:
        from cairn.devices.cairn.machines.sleep_cycle import token
        result = token.receive_answer(self._bus, envelope.get("body") or {}, roots=self._roots)
        if not result.get("accepted"):
            # Loud, not silent (Law 7): a stale or out-of-turn answer is the one thing a
            # rotation can get wrong without anyone noticing.
            self.emit("sleep_token_refused", pointer=str(result.get("device")), values=dict(result))
        return result

    def _handle_sleep_cycle(self, envelope: dict) -> dict:
        from cairn.devices.cairn.machines.sleep_cycle import token
        act = (envelope.get("body") or {}).get("act")
        if act == "mint":
            return {"cycle": token.mint(self._bus, roots=self._roots, roster_root=self._roster_root)}
        if act == "show":
            return {"cycle": token.standing(self._roots)}
        return {"accepted": False, "reason": f"sleep-cycle takes act mint|show, got {act!r}"}

    def declared_panes(self) -> list[dict]:
        return [
            {
                "kind": "trouble",
                "label": "troubles",
                "handler": self._trouble_pane_data,
            },
        ]

    def _trouble_pane_data(self) -> list[dict]:
        """The live troubles, asked for over the bus — trouble's store stays trouble's.

        RAISES rather than returning empty when the bus is missing or the ask is refused,
        and that is the whole point: ``BaseShim.active_page`` renders a raising handler as
        an ABSENT pane carrying the reason, where an empty list would render as the
        NORMAL OPERATING STATE. Those two must never look alike — ``live()`` returning
        nothing is the system working, and a panel that showed 'no troubles' because it
        could not reach the lane would be the silent failure the lane exists to end
        (Law 7, and ``trouble.py``'s own leaning-safe read of ``standing``)."""
        if self._bus is None:
            raise RuntimeError(
                "cairn has no bus, so the trouble lane cannot be asked — an empty panel "
                "here would read as zero troubles, which is the normal operating state "
                "and the opposite of what is true")
        reply = self._bus.request(
            sender=self._device_id, to="trouble", verb="live",
            why="trouble pane render")
        body = reply.get("body") or {}
        if "troubles" not in body:
            raise RuntimeError(
                f"trouble answered `live` without a troubles list: {body!r}")
        return [
            {
                "id": t.get("id", "?"),
                "standing": t.get("standing", "?"),
                "why": t.get("why", ""),
                "count": t.get("count", 0),
                "first_seen": t.get("first_seen", ""),
                "last_seen": t.get("last_seen", ""),
            }
            for t in body["troubles"]
        ]

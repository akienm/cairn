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
        from cairn.devices.cairn.machines.sleep_cycle import idle
        return {"idle_threshold_s": idle.IDLE_THRESHOLD_S,
                "idle_threshold_provenance": idle.IDLE_THRESHOLD_PROVENANCE}

    def declared_verbs(self) -> dict:
        """``sleep-token`` is a device's answer to the hand (ticket bf146e9e3967, D2(d));
        ``sleep-cycle`` is the operator's face on the rotation: mint or show; ``away`` holds
        Akien's declared absence, inside which sleep is due at once (ticket 9b6b392ebcfe)."""
        return {**super().declared_verbs(),
                "sleep-token": self._handle_sleep_token,
                "sleep-cycle": self._handle_sleep_cycle,
                "away": self._handle_away}

    def _handle_away(self, envelope: dict) -> dict:
        from cairn.devices.cairn.machines.sleep_cycle import idle
        body = envelope.get("body") or {}
        act = body.get("act")
        if act == "set":
            try:
                return {"away": idle.set_away(body.get("start"), body.get("end"),
                                              body.get("why") or "", roots=self._roots)}
            except ValueError as exc:
                return {"accepted": False, "reason": str(exc)}
        if act == "show":
            return {"away": idle.read_away(self._roots)}
        if act == "clear":
            return {"cleared": idle.clear_away(self._roots)}
        return {"accepted": False, "reason": f"away takes act set|show|clear, got {act!r}"}

    def _handle_sleep_token(self, envelope: dict) -> dict:
        from cairn.devices.cairn.machines.sleep_cycle import token
        result = token.receive_answer(self._bus, envelope.get("body") or {}, roots=self._roots)
        if not result.get("accepted"):
            # Loud, not silent (Law 7): a stale or out-of-turn answer is the one thing a
            # rotation can get wrong without anyone noticing.
            self.emit("sleep_token_refused", pointer=str(result.get("device")), values=dict(result))
        if result.get("closed"):
            result["logs"] = self._forget_logs()
        return result

    def _handle_sleep_cycle(self, envelope: dict) -> dict:
        from cairn.devices.cairn.machines.sleep_cycle import token
        act = (envelope.get("body") or {}).get("act")
        if act == "mint":
            cycle = token.mint(self._bus, roots=self._roots, roster_root=self._roster_root)
            if cycle.get("closed_at") is None:
                return {"cycle": cycle}
            return {"cycle": cycle, "logs": self._forget_logs()}
        if act == "show":
            return {"cycle": token.standing(self._roots)}
        return {"accepted": False, "reason": f"sleep-cycle takes act mint|show, got {act!r}"}

    def _forget_logs(self) -> dict:
        """The cairn device's own sleep work: forget the logs tree past 30 days (ticket
        ff881672ac57; Akien, open-9d9c0b1ac3a9: "cairn device's sleep cycle should be where that
        cleanup happens"). Run when a rotation this device runs CLOSES — every device on the
        roster has done its own maintenance, or there was none to visit — so the hub sweeps last.
        The counts ride the verb's result and land on this device's own trail."""
        from cairn.devices.cairn.logs_sweep import sweep_logs
        counts = sweep_logs(older_than_days=30, roots=self._roots)
        self.emit("logs_swept", values=counts)
        return counts

    def declared_panes(self) -> list[dict]:
        return [
            {
                "kind": "trouble",
                "label": "troubles",
                "handler": self._trouble_pane_data,
            },
        ]

    def _trouble_pane_data(self) -> list[dict]:
        """The live troubles, read as files through the tool trouble publishes (ticket
        ee04bb869795; Akien 2026-10-18: "TROUBLE TICKETS ARE A FILE ARTIFACT IN THE LOGGING
        TREE"). It asked verb ``live`` over the bus until then, and every reply stood as a bus
        row. Which rows are live is still trouble's: the tool reads the top of its store.

        RAISES rather than returning empty when the store is absent, and that is the whole
        point: ``BaseShim.active_page`` renders a raising handler as an ABSENT pane carrying
        the reason, where an empty list would render as the NORMAL OPERATING STATE. Those two
        must never look alike (Law 7)."""
        from cairn.devices.trouble.tools.store import store
        return [
            {
                "id": t.get("id", "?"),
                "standing": t.get("standing", "?"),
                "why": t.get("why", ""),
                "count": t.get("count", 0),
                "first_seen": t.get("first_seen", ""),
                "last_seen": t.get("last_seen", ""),
            }
            for t in store.live(self._roots)
        ]

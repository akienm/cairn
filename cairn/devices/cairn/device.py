"""cairn/device.py — the cairn system device.

The top-level device. Its machines (ground_loop, harbor_master, bus) are the
system's own infrastructure. BaseDevice.receive() records inbound mail to a
DataRecorder for later evaluation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from cairn.tools.base.device import BaseDevice


def beat_pane_data(home=None, now=None) -> dict:
    """The heartbeat's page: the ground loop's lock (``up``) and its beat record, read at request
    time through the loop's two public faces, ``guard.held`` and ``heartbeat.read_record`` —
    rendered, never derived. The ground loop has no shim and no verbs of its own (outline 5.6.3,
    5.6.5); a machine's panel is reached through its host device (2.3.8.5), so this is the cairn
    device's (ticket 229ee25ff6f0)."""
    from cairn.devices.cairn.machines.ground_loop import guard
    from cairn.devices.cairn.machines.ground_loop.heartbeat import default_home, read_record
    home = home if home is not None else default_home()
    now = now if now is not None else datetime.now(timezone.utc).astimezone()
    return {
        "reports": "the resident singleton's lock and beat record (instance 0), read from disk "
        "at request time — whatever process serves this page",
        "up": guard.held(home),
        **read_record(home, now),
    }


class CairnDevice(BaseDevice):

    def __init__(self, bus=None, roots=None, roster_root=None, metrics_table=None) -> None:
        super().__init__()
        self._device_id = "cairn"
        # Where the sleep cycle's standing state and roster are read (ticket bf146e9e3967,
        # D4/D7): None live, a fixture's roots and roster folder under a proof.
        self._roots = roots
        self._roster_root = roster_root
        # The one metrics table (ticket 3721d82be75c, outline 17.27, 5.3.6): None live, a scratch
        # table under a proof.
        self._metrics_table = metrics_table
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
                    "harbor_master, and bus; it carries the heartbeat's page.",
            "why": "Every device has a presence on the bus (Akien, 2026-08-11). "
                    "The system itself is a device and answers its own mail.",
        }

    def state(self) -> dict:
        return {}

    def settings(self) -> dict:
        from cairn.devices.cairn.machines.sleep_cycle import idle
        return {"idle_threshold_s": idle.IDLE_THRESHOLD_S,
                "idle_threshold_provenance": idle.IDLE_THRESHOLD_PROVENANCE,
                "sleep_clock": f"{idle.CLOCK_HOUR:02d}:00",
                "sleep_clock_provenance": idle.CLOCK_PROVENANCE}

    def declared_verbs(self) -> dict:
        """``sleep-token`` is a device's answer to the hand (ticket bf146e9e3967, D2(d));
        ``sleep-cycle`` is the operator's face on the rotation: mint or show; ``away`` holds
        Akien's declared absence, inside which sleep is due at once (ticket 9b6b392ebcfe)."""
        return {**super().declared_verbs(),
                "sleep-token": self._handle_sleep_token,
                "sleep-cycle": self._handle_sleep_cycle,
                "away": self._handle_away,
                "metrics": self._handle_metrics,
                "beat": self._handle_beat}

    def _handle_beat(self, envelope: dict) -> dict:
        """The heartbeat's page over the bus: a ``beat`` ask answered from the ground loop's lock
        and record (ticket 229ee25ff6f0). The answer leaves a breadcrumb on this device's own
        trail (emit, never the bus)."""
        data = beat_pane_data()
        self.emit("beat_answered", pointer=(envelope or {}).get("id"))
        return data

    def _handle_metrics(self, envelope: dict) -> dict:
        """Fill the metrics table from every holder's recorder, then answer the rows matching
        the body's name / source / since / until (ticket 3721d82be75c, outline 17.27.3); with
        ``totals`` true, answer one count and sum per name instead (ticket f4dbcea5a117)."""
        from cairn.devices.cairn import metrics
        body = envelope.get("body") or {}
        table = self._metrics_table or metrics.TABLE
        kw = {"name": body.get("name"), "source": body.get("source"), "since": body.get("since"),
              "until": body.get("until"), "roots": self._roots}
        if body.get("totals"):   # one count and sum per name (and per info[by]), ticket f4dbcea5a117
            return metrics.totals(table, by=body.get("by"), **kw)
        return metrics.report(table, **kw)

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
        return result

    def _handle_sleep_cycle(self, envelope: dict) -> dict:
        from cairn.devices.cairn.machines.sleep_cycle import token
        act = (envelope.get("body") or {}).get("act")
        if act == "mint":
            # Cairn runs its own sleep first, then hands the token round the rack (outline
            # 5.3.3.1, ticket 4de7baf7e255): the sweep precedes the first hand.
            logs = self._forget_logs()
            cycle = token.mint(self._bus, roots=self._roots, roster_root=self._roster_root)
            return {"cycle": cycle, "logs": logs}
        if act == "show":
            return {"cycle": token.standing(self._roots)}
        return {"accepted": False, "reason": f"sleep-cycle takes act mint|show, got {act!r}"}

    def _forget_logs(self) -> dict:
        """The cairn device's own sleep work: forget the logs tree past 30 days (ticket
        ff881672ac57; Akien, open-9d9c0b1ac3a9: "cairn device's sleep cycle should be where that
        cleanup happens"). Run when this device MINTS a rotation, before token.mint hands to the
        first device: Cairn sleeps first, then hands on (outline 5.3.3.1, ticket 4de7baf7e255).
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
            {
                "kind": "beat",
                "label": "Heartbeat",
                "handler": beat_pane_data,
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

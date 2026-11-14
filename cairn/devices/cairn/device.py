"""cairn/device.py — the cairn system device.

The top-level device. Its machines (ground_loop, harbor_master, bus) are the
system's own infrastructure. BaseDevice.receive() records inbound mail to a
DataRecorder for later evaluation.
"""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timezone

from cairn.tools.base.device import BaseDevice


# THE TESTER'S TIERS, ASKED BY CAIRN (ticket c811a8b1b8c7, outline 9.4.2.3.7.2-.4). Cairn's
# scheduled list fires the first two on the clock (cairn/devices/cairn/0/schedule.json); the
# third is asked from Cairn's own sleep step, before the token is handed on (token.mint).
# Each maps a Cairn verb to the tester verb it asks; the tester runs the tier.
TESTER = "tester"
TIER_ASKS = {
    "ask-tester-reseal-yellow": "reseal-yellow",
    "ask-tester-weekly-run": "weekly-run",
    "ask-tester-run-every-proof": "run-every-proof",
}
# How long an ask waits for the tester's answer before it is raised as unanswered. A tier runs
# proofs, so the bound is the run's, not a chat's: the weekly tier re-hollows every proof.
ASK_TIMEOUT_S = {"reseal-yellow": 3600.0, "weekly-run": 6 * 3600.0, "run-every-proof": 6 * 3600.0}
# How long the sleep step waits to see its ask stand on the bus before it hands the token on.
ASK_POSTED_WITHIN_S = 5.0


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
        # Every tier ask this process made, by its ask id, and its standing: asked, answered or
        # refused. Never "done" on the asking side: done is the tester's answer (ticket
        # c811a8b1b8c7, clause 3).
        self._asks: dict[str, dict] = {}
        self._asks_lock = threading.Lock()

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
                "beat": self._handle_beat,
                **{verb: (lambda env, v=verb: self.ask_tester(TIER_ASKS[v]))
                   for verb in TIER_ASKS},
                "tester-asks": self._handle_tester_asks}

    # --- the tester's tiers, asked over the bus (ticket c811a8b1b8c7) ---------------------

    def _tester_bus(self):
        """The bus the tester is asked over: the shim's own when one was handed in (live, the
        bus process's; under a proof, its scratch bus), else ``bus_client.reach('tester')``.
        Never a dial when a bus is in hand: a fixture's bus must not become the live one."""
        if self._bus is not None:
            return self._bus
        from cairn.tools.bus_client.bus_client import reach
        return reach(TESTER)

    def _ask_refused(self, ask: dict, reason: str) -> None:
        """An ask the tester did not answer, raised loudly (Law 7): a trouble named for the
        tier, so the second unanswered night is the same trouble as the first."""
        with self._asks_lock:
            ask.update(state="refused", reason=reason, at=datetime.now(timezone.utc).isoformat())
            detail = {"ask": dict(ask)}
        self.raise_trouble(f"cairn-tester-ask-{ask['verb']}-unanswered",
                           why=f"cairn asked the tester's {ask['verb']} and it was not answered: "
                               f"{reason}", detail=detail)

    def ask_tester(self, verb: str, *, wait_posted: bool = False) -> dict:
        """Ask the tester's tier ``verb`` over the bus, ASYNCHRONOUSLY: the ask is made on a
        worker, so the pulse or the sleep step that asked is not held while proofs run. The
        answer is the ask's record, state ``asked``; the worker moves it to ``answered`` on
        the tester's reply, or to ``refused`` (and raises a trouble) on a refusal, a bounce,
        an absent tester or no reply in time. With ``wait_posted``, return only once the ask
        stands on the bus (bounded by ASK_POSTED_WITHIN_S), so a caller that must ask BEFORE
        it moves on (the sleep step) has an order it can rely on."""
        ask = {"id": uuid.uuid4().hex, "verb": verb, "to": TESTER, "state": "asked",
               "asked_at": datetime.now(timezone.utc).isoformat()}
        with self._asks_lock:
            self._asks[ask["id"]] = ask
        try:
            bus = self._tester_bus()
        except Exception as exc:  # noqa: BLE001 - an absent tester is loud, never a raise here
            self._ask_refused(ask, f"no bus reaches the tester: {type(exc).__name__}: {exc}")
            return self._ask_view(ask)
        if not callable(getattr(bus, "request", None)):
            self._ask_refused(ask, f"the bus in hand ({type(bus).__name__}) cannot ask")
            return self._ask_view(ask)

        def wait() -> None:
            try:
                reply = bus.request(sender=self.device_id, to=TESTER, verb=verb,
                                    why=f"cairn's {verb} tier (outline 9.4.2.3.7)",
                                    body={"ask_id": ask["id"]},
                                    timeout=ASK_TIMEOUT_S.get(verb, 3600.0))
            except Exception as exc:  # noqa: BLE001 - a timeout or a dead bus: loud
                self._ask_refused(ask, f"{type(exc).__name__}: {exc}")
                return
            body = (reply or {}).get("body") or {}
            if body.get("is_bounce") or body.get("accepted") is False or body.get("refused"):
                self._ask_refused(ask, str(body.get("reason") or body.get("refused") or body))
                return
            with self._asks_lock:
                ask.update(state="answered", at=datetime.now(timezone.utc).isoformat(),
                           answer={k: body[k] for k in ("tier", "proofs", "ticketed", "refusals",
                                                        "not_run") if k in body})
            self.clear_trouble(f"cairn-tester-ask-{verb}-unanswered", by="cairn",
                               what_changed=f"the tester answered {verb} ask {ask['id']}")

        worker = threading.Thread(target=wait, daemon=True,
                                  name=f"cairn-ask-{verb}-{ask['id'][:8]}")
        worker.start()
        if wait_posted:
            deadline = time.monotonic() + ASK_POSTED_WITHIN_S
            while not self._ask_stands(bus, ask["id"]):
                if not worker.is_alive():
                    break
                if time.monotonic() >= deadline:
                    self._ask_refused(ask, f"the ask was not seen on the bus within "
                                           f"{ASK_POSTED_WITHIN_S}s")
                    break
                time.sleep(0.02)
        return self._ask_view(ask)

    def _ask_view(self, ask: dict) -> dict:
        with self._asks_lock:
            return dict(ask)

    @staticmethod
    def _ask_stands(bus, ask_id: str) -> bool:
        try:
            mail = bus.read(to=TESTER, channel="personal", limit=20)
        except Exception:  # noqa: BLE001 - unreadable is "not seen"; the deadline is the loud edge
            return False
        return any((e.get("body") or {}).get("ask_id") == ask_id for e in mail)

    def _handle_tester_asks(self, envelope: dict) -> dict:
        """Every tier ask this process made and where it stands: asked, answered or refused."""
        with self._asks_lock:
            return {"asks": [dict(a) for a in self._asks.values()]}

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
            # The daily tier is Cairn's own sleep work too (ticket c811a8b1b8c7, D3): asked
            # while Cairn still holds the token, before the first hand.
            cycle = token.mint(self._bus, roots=self._roots, roster_root=self._roster_root,
                               ask_first=lambda: self.ask_tester("run-every-proof",
                                                                 wait_posted=True))
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

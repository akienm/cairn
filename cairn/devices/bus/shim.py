"""BusShim — the POSTMAN. The half of the bus that had never been built.

WHAT WAS MEASURED MISSING, 2026-08-11. ``post`` wrote durable envelopes and ``read`` returned
them whole, and ``BaseShim.deliver`` — the method that hands an envelope to a device and wakes
it — stood with **zero callers** since the day it was written. Nothing drained an inbox. So a
device could be sent a question and had no way on earth to receive it, and from the sender's
side that is indistinguishable from a working bus: the post succeeds, the row lands, the read
shows it sitting there. Three envelopes were sitting in transit when this was found, the
oldest addressed to a device that has never once looked.

WHY THE DELIVERER IS THE BUS'S OWN SHIM, and not the heartbeat. The heartbeat's charter is one
sentence long and the ground_loop "does NOT execute, resolve, schedule, ROUTE, or write"
(``ground_loop/loop.py`` — that clause is the 584aa74 goof's headstone). Handing an envelope
to its addressee is routing. It belongs to the device whose whole charter is *the sole path
for inter-device communication* (Law 6: the owner of the traffic delivers it), and it reaches
the addressee's shim through ``heartbeat.shim_for`` — the accessor the heartbeat already
publishes for exactly this, "you can only reach what is on the roster."

ONE QUERY PER BEAT, FOR THE WHOLE SYSTEM. The drain asks ``bus.undelivered()`` once and
dispatches what comes back. A per-device sweep would be a query per device per second — a
poll wearing a heartbeat's clothes, and it would grow with every device added. This is the
shape that shrinks instead: one question, however many devices.

MAIL IS NEVER LOST AND NEVER SILENTLY EATEN. The receipt is written only AFTER the device has
taken the envelope, so a receiver that raises leaves the mail in the inbox for the next beat.
An addressee with no shim on the roster, or a shim that cannot wake a device, is reported —
once per envelope, not once per beat — and its mail waits. That "waits" is honest: it names
the next rung (a device needs a real shim before it can answer) instead of faking an arrival.

FILED EDGE, not faked here: the drain is asked on a cadence because the beat is what exists
today. The event-shaped answer is the store telling the postman a row landed (Postgres
LISTEN/NOTIFY through db_domain's gate), which turns one query per second into zero queries
until there is mail. That waits on a real volume — and on db_domain growing a listen face,
which is its owner's call, not the bus's.
"""

from __future__ import annotations

from cairn.tools.base.shim import BaseShim, ONLINE

# How many envelopes one beat will move. A bound, so a device that was unreachable for an
# hour drains over several beats instead of one enormous transaction — and the oldest mail
# goes first (``bus.undelivered`` orders by arrival), so a backlog cannot starve the message
# that has already waited longest.
DRAIN_LIMIT = 50


class BusShim(BaseShim):
    """The bus's always-on face: it drains the transit table on every pulse and hands each
    envelope to the shim of the device it is addressed to.

    Holds its device directly (the bus is a light object over db_domain's gate, not a heavy
    process to spawn), and holds the heartbeat — not to beat it, but to READ its roster. That
    is a read of something the heartbeat already owns and already publishes (Law 6); the
    postman adds no new registry of who exists, which is the thing that would go stale.
    """

    def __init__(self, bus, heartbeat, limit: int = DRAIN_LIMIT) -> None:
        super().__init__(bus=bus)
        self._heartbeat = heartbeat
        self._limit = limit
        self._device = bus
        self._presence = ONLINE
        # Which envelopes have already been REPORTED undeliverable. The crossing-memory
        # pattern the shim already uses for probes (``_was_true``), applied to the same
        # problem: mail that cannot be delivered stays in the inbox, so without this every
        # beat would re-report the identical finding once a second forever. The finding is
        # about the envelope, so it is remembered by envelope id.
        self._reported: set = set()

    @property
    def device_id(self) -> str:
        return "bus"

    def _start_device(self):
        """The bus is already here — it was handed in at construction. A postman that had to
        spawn its own post office would be a second bus, and there is exactly one."""
        return self._bus

    # --- the drain ----------------------------------------------------------

    def _deliver_one(self, envelope: dict) -> dict:
        """One envelope's journey, isolated. Never raises: the outcome is data, because a
        single undeliverable message must not stop the rest of the round."""
        addressee = envelope.get("addressee")
        outcome = {"envelope": envelope.get("id"), "to": addressee,
                   "channel": envelope.get("channel"), "why": envelope.get("why")}
        shim = self._heartbeat.shim_for(addressee) if addressee else None
        if shim is None:
            return {**outcome, "outcome": "no_shim",
                    "lack": f"nothing on the heartbeat's roster answers to {addressee!r} — the "
                            "mail waits; you can only deliver to what is being beaten"}
        if shim is self:
            return {**outcome, "outcome": "no_shim",
                    "lack": "addressed to the bus itself — the postman is not a destination"}
        try:
            shim.deliver(envelope)
        except NotImplementedError as exc:
            # The shim exists but cannot wake a device. Told apart from a receiver that BROKE,
            # because they call for opposite fixes: this one is a device that has never been
            # given a real shim, not a bug in one that has.
            return {**outcome, "outcome": "no_receiver", "lack": str(exc)}
        except Exception as exc:  # noqa: BLE001 — a broken receiver cannot stop the round
            return {**outcome, "outcome": "refused",
                    "error": f"{type(exc).__name__}: {exc}"}
        # THE RECEIPT COMES LAST, ON PURPOSE. The device has the envelope; only now is it
        # delivered. A receipt written first would mark mail delivered that a raising receiver
        # never saw, and the message would be gone with nothing to show it ever arrived.
        try:
            self._bus.record_delivery(envelope["id"], to=addressee, by=self.device_id)
        except Exception as exc:  # noqa: BLE001
            return {**outcome, "outcome": "unreceipted",
                    "error": f"{type(exc).__name__}: {exc}",
                    "lack": "the device TOOK this envelope but the receipt did not land, so it "
                            "will be delivered again on a later beat — at-least-once, which is "
                            "the right side to fail on"}
        return {**outcome, "outcome": "ok"}

    def drain(self) -> dict:
        """One round of delivery. Never raises — an unreachable store is a reported outcome,
        because the heartbeat must keep beating on a box whose Postgres is down."""
        try:
            waiting = self._bus.undelivered(limit=self._limit)
        except Exception as exc:  # noqa: BLE001 — the substrate being down cannot stop the beat
            return {"outcome": "refused", "error": f"{type(exc).__name__}: {exc}",
                    "lack": "the transit store could not be read, so nothing could be "
                            "delivered this beat; the heartbeat is unaffected"}
        results = [self._deliver_one(env) for env in waiting]
        delivered = [r for r in results if r["outcome"] == "ok"]
        # Only the findings that are NEW are carried out of the drain. The undelivered stay
        # undelivered and come back next beat; reporting them every time would bury a real
        # arrival under a second-by-second repetition of the same stuck envelope.
        fresh = []
        for r in results:
            if r["outcome"] == "ok":
                self._reported.discard(r["envelope"])
                continue
            if r["envelope"] in self._reported:
                continue
            self._reported.add(r["envelope"])
            fresh.append(r)
            # THE BUS EMITS, NOT THE SHIM. ``emit`` is DiagnosticBase's, and a shim is not a
            # device — it RECEIVES breadcrumbs (``receive_diagnostic``) rather than sending
            # them. That is the right ownership anyway: the stuck message is the bus's fact,
            # and ``record_delivery`` already emits the arrival from the same place. Guarded
            # because ``drain`` promises never to raise, and a failed breadcrumb must not
            # cost the substrate its whole round.
            try:
                self._bus.emit("undelivered", pointer=r["envelope"],
                               values={"to": r["to"], "outcome": r["outcome"],
                                       "lack": r.get("lack") or r.get("error")})
            except Exception:  # noqa: BLE001, S110 — the finding is already in the record
                pass
        return {"outcome": "ok", "waiting": len(waiting),
                "delivered": [r["envelope"] for r in delivered], "findings": fresh}

    def on_pulse(self, now, context: dict | None = None) -> dict:
        """The heartbeat's pulse, doing both jobs: the standard probe firing (inherited, so
        the bus can carry watches like any device) and then the drain.

        The drain runs AFTER firing so an envelope a probe posts on this very beat is
        available to the NEXT one — delivering it in the same pass would let one beat cascade
        an unbounded chain of post-and-deliver, which is the heartbeat doing work instead of
        keeping time."""
        record = super().on_pulse(now, context)
        record["postman"] = self.drain()
        return record

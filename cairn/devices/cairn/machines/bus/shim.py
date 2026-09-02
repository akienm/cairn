"""BusShim — the bus's own face on the heartbeat.

THE POSTMAN IS DISSOLVED (2026-08-29). Each device's shim now checks its own inbox on each
pulse (``BaseShim._check_mail``), so the bus no longer drains and dispatches on their behalf.
The old shape — one query for all devices, the BusShim as middleman routing through
``shim_for`` — worked but carried crossing-memory, drain limits, and the no_receiver path
that left 998 messages undelivered for weeks (harbor_master had no real shim). The new shape:
each shim reads its own mail, delivers to itself, records its own receipt. N queries per
minute (N devices, 60s cadence) is trivial at current scale.

WHY THE SHIM STILL EXISTS. The bus is a device (pending absorption into the cairn device —
ticket cairn-device-absorbs-foundational-infrastructure) and has probes in its folder that
the heartbeat fires on each pulse. That firing lives here.

The ``drain()`` and ``_deliver_one()`` methods are kept for callers that need to sweep mail
outside the pulse (e.g. a backlog migration), but they no longer run every beat.

FILED EDGE, not faked: Postgres LISTEN/NOTIFY through db_domain's gate, replacing the
per-device poll with an event — waits on volume and on db_domain growing a listen face.
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
        """The heartbeat's pulse — inherited pulse, then flush the in-memory ring to DB.

        Flush AFTER the pulse so that everything posted during the beat — including
        receipts from mail delivery — lands in one batch transaction. The flush is the
        durable half of the ring buffer; post() and request() run zero-DB on the hot
        path."""
        record = super().on_pulse(now, context)
        try:
            flush_result = self._device.flush()
            if flush_result.get("flushed") or flush_result.get("receipts"):
                record["flush"] = flush_result
        except Exception as exc:  # noqa: BLE001 — a failed flush cannot stop the beat
            self._device.emit("flush_failed", values={
                "error": f"{type(exc).__name__}: {exc}",
            })
        return record

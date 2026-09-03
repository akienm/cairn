"""bus — the ONE common messaging substrate for everything, made a device.

THE SECOND SUBSTRATE (converged with Akien 2026-07-18;
``CairnCommons/intentions-not-beside-code/I-heartbeat-probes-and-bus.md``). Cairn runtime hangs on
exactly two things: the HEARTBEAT (``ground_loop`` — one pulse, nothing more) and the
BUS (here — one messaging substrate, the sole path for inter-device communication). The
symmetry is what makes it load-bearing:

    db_domain : the sole path to durable STATE      :: owner-gated (Law 6), logged
    the bus   : the sole path to inter-device COMMS :: owner-gated (Law 6), logged

Because the bus is the ONLY door for communication — devices never hold references to
each other, never call each other directly, they ``post`` and ``read`` — "inspectable +
logged + common" are not features bolted onto each surface. They are automatic. Physics,
not policy (Law 4). Every surface later (a web feed, an MCP inspector, a debug pane) is a
READ-PROJECTION of this one substrate (Law 1 — nothing re-derived elsewhere).

DURABLE TRANSIT RIDES db_domain (Law 6). The bus opens no Postgres of its own — a message
in transit is an owned write through ``db_domain`` (owner ``"bus"``). That buys logged +
inspectable + one-owner for free, and makes the bus the sole *writer* of traffic, on
behalf of attributed senders. This is the exact mirror of "a device reaches durable state
ONLY through db_domain": a device reaches another device ONLY through ``post``.

CHANNELS, per device (the Murderbot-feeds model, Martha Wells):
  - ``announce`` — the public feed; public conversations, announces-of-fact. RECORD.
  - ``personal`` — the chat inbox; others reach the device here (its pokes land here). RECORD.
  - ``info`` / ``debug`` — the two logging channels. DIAGNOSTIC.
A device's ``introspect()`` can publish onto its ``announce`` feed, so *inspecting a device
is reading its feed* — observability and messaging stop being two systems.

RECORD-OF-TRUTH vs DIAGNOSTIC, as physics (Law 7). A RECORD channel (announce/personal)
never collapses and never expires — it is a record of truth. A DIAGNOSTIC channel
(info/debug) may collapse in a VIEW and expire on a rolling window. The crux: the SUBSTRATE
always stores the full truth; only a ``digest`` VIEW collapses. ``read`` is the record;
``digest`` is the collapsible surface, and it refuses to collapse a record channel.

EVERY ENVELOPE CARRIES WHY + CAUSALITY (Law 5): ``sender``, its ``why`` (CP3 — a message
with no reason is a defect, not a resting state), and ``reply_to`` (the envelope it answers).
So the bus is a REPLAYABLE CAUSAL RECORD, not just traffic — a device woken from sleep
rebuilds its context by reading its own feed history (horizon-of-awareness, made concrete).

FILED EDGES (children of this stone — not faked):
  - The WIRE PROTOCOL is a swappable adapter. The bus's semantics (channels, owned
    envelopes, causality) are Cairn's; MCP is the current lingua franca for agentic comms,
    so it is the adapter to add at the edge — swapped when the ecosystem moves, the way
    ``system_rackmount`` hides an OS service. Not built here; the substrate must not be held
    hostage to a protocol.
  - PER-DEVICE-OWNED channels. Today the bus owns one transit table and is its sole writer,
    attributing each sender in the envelope. Making each device the owner of its own inbound
    channel (so "others post through the owner's gate" is a per-device gate, not the bus's)
    is a refinement that waits on a real multi-owner need.
  - RETENTION / rolling-window expiry of diagnostic channels — the ``digest`` view collapses
    now; a durable expiry policy lands when a real volume pulls it.
  - The HUMAN as a native participant: Akien gets channels like any device, and the web
    server is a view. The channel shape is here; wiring Akien's feeds is the web-server stone.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from cairn.tools.base.device import BaseDevice
from cairn.devices.db_domain import store

# The channels every device has, each classified by Law 7. RECORD channels are records of
# truth (never collapse, never expire); DIAGNOSTIC channels may collapse in a view. The
# classification is DATA the substrate enforces, not a convention each reader remembers.
RECORD = "record"
DIAGNOSTIC = "diagnostic"
CHANNELS: dict[str, str] = {
    "announce": RECORD,      # public feed — public conversation + announces-of-fact
    "personal": RECORD,      # chat inbox — where a device is reached (pokes land here)
    "info": DIAGNOSTIC,      # logging — collapsible in a view
    "debug": DIAGNOSTIC,     # logging — collapsible in a view
}

# Each channel projects onto a visual pane — the pane set IS the channel set, plus two
# structural panes (status, settings) the shim provides from introspect(). Akien 2026-08-31:
# "The pane set is: public feed, personal feed, Status, Settings, INFO, DEBUG."
PANE_CHANNEL_MAP: dict[str, str] = {
    "announce": "public_feed",
    "personal": "personal_feed",
    "info": "info",
    "debug": "debug",
}
STRUCTURAL_PANES: frozenset[str] = frozenset({"status", "settings"})

# The transit table's columns — the envelope, made durable. ``body`` is jsonb so a
# structured payload survives the round-trip intact; everything else is text. ``addressee``
# rather than ``to`` (a SQL-adjacent word) keeps the column name unambiguous.
_TRAFFIC_COLUMNS = {
    "id": "text",
    "sender": "text",
    "addressee": "text",
    "channel": "text",
    "kind": "text",
    "verb": "text NOT NULL DEFAULT ''",
    "why": "text",
    "body": "jsonb",
    "reply_to": "text",
    "date": "text",
}
_BUS_OWNER = "bus"

# THE RECEIPT — delivery as its own append-only fact, NOT a column on the envelope.
#
# ``post`` and ``read`` worked from the day the bus shipped, and nothing ever DELIVERED: no
# drainer read a device's inbox, so ``BaseShim.deliver`` stood with zero callers and no device
# could answer anything sent to it. Sending worked, arriving did not, and the two are
# indistinguishable from the sender's side — which is why "the bus is up" read as true for
# three weeks. This table is the missing half.
#
# WHY A SECOND TABLE RATHER THAN A ``delivered`` COLUMN. An envelope on a RECORD channel is a
# record of truth (Law 7): it does not get rewritten after the fact, and a stamp written back
# into it is exactly that. A receipt is a separate EVENT — *this envelope reached this device
# at this moment* — so it appends, it can carry more than one row per envelope when a message
# is one day delivered to several, and it leaves the causal record bit-unmoved. It also needs
# no migration of a table that already holds live traffic.
_DELIVERY_COLUMNS = {
    "envelope": "text",
    "addressee": "text",
    "by": "text",
    "date": "text",
}


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def sql_missing_receipt(traffic_table: str, delivery_table: str) -> str:
    """The WHERE fragment for 'no receipt exists for this envelope'.

    A raw fragment because ``store.read`` takes a raw ``WHERE`` and a table name cannot be a
    bound parameter. Both names are therefore checked against a plain-identifier pattern
    before they are interpolated: the bus derives them from its own configuration, but a name
    that reaches SQL unchecked is a hole whether or not today's caller could open it (CP6 —
    safety is built, never the resting state).

    The outer reference is QUALIFIED (``traffic.id``, not a bare ``id``) so the correlation
    cannot silently rebind if the receipt table ever grows a column of the same name — that
    would turn the anti-join into a self-comparison and report the entire inbox delivered."""
    for name in (traffic_table, delivery_table):
        if not _IDENTIFIER.match(name or ""):
            raise ValueError(f"refusing {name!r} as a table name — a name that reaches SQL "
                             "uninspected is a hole regardless of who holds it today")
    return (f"NOT EXISTS (SELECT 1 FROM {delivery_table} d "
            f"WHERE d.envelope = {traffic_table}.id)")


class ChannelError(Exception):
    """A post/read against a channel that is not one of the four. Loud, never swallowed (CP1)."""


def _require_channel(channel: str) -> str:
    """Refuse an unknown channel loudly (CP1) before anything is written — a message with no
    valid channel is a defect, not a resting state. Returns the channel's kind (Law 7)."""
    if channel not in CHANNELS:
        raise ChannelError(
            f"unknown channel {channel!r}; the four are {sorted(CHANNELS)} "
            f"(announce/personal are records of truth, info/debug are diagnostic)"
        )
    return CHANNELS[channel]


class BusDevice(BaseDevice):
    """The messaging substrate as a device (carries CP1-CP6; reports intention/state/settings).

    Its capabilities are ``post`` (the sole way to send), ``read`` (the record — full truth),
    and ``digest`` (a collapsible VIEW, for diagnostic channels only). Durable transit rides
    ``db_domain`` under owner ``"bus"``; the bus opens no connection of its own beyond that
    gate. ``table`` is injectable so a proof can run on an ephemeral, self-cleaning table.

    IN-MEMORY RING (ticket 67d7a6783fb3). The hot path (post, request) writes to an in-memory
    ring and fires delivery hooks with zero DB round-trips. The ground loop pulse calls
    ``flush()`` once per beat, batch-writing the ring to Postgres in one transaction. The
    record of truth is still Postgres (Law 7); the ring is the fast path, the flush is the
    durable path. read() merges ring + DB so the full truth is always visible.
    """

    def __init__(self, table: str = "bus_traffic", device_id: str = "bus") -> None:
        super().__init__()
        self._table = table
        self._delivery_table = f"{table}_delivery"
        self._device_id = device_id
        self._ensured = False
        self._posted = 0
        self._delivered = 0
        self._flushed = 0
        self._last_envelope: dict | None = None
        self._delivery_hooks: dict[str, "Callable"] = {}
        self._channel_toggles: dict[str, dict[str, bool]] = {}
        self._ring: list[dict] = []
        self._ring_receipts: list[dict] = []
        self._ring_delivered: set[str] = set()
        self._folder_recorders: dict[str, Any] = {}

    def wire_delivery(self, device_id: str, deliver: "Callable[[dict], Any]") -> None:
        self._delivery_hooks[device_id] = deliver
        if device_id not in self._channel_toggles:
            self._channel_toggles[device_id] = {ch: True for ch in CHANNELS}

    def unwire_delivery(self, device_id: str) -> None:
        self._delivery_hooks.pop(device_id, None)
        self._channel_toggles.pop(device_id, None)

    def _try_folder_delivery(self, addressee: str, envelope: dict) -> bool:
        """Fallback delivery for non-device addressees via folder instanceizer.

        If ``~/.cairn/folders/<addressee>/`` has an instanceizer, load its DataRecorder
        and write the envelope. Returns True if delivered, False if no folder exists."""
        if addressee in self._folder_recorders:
            recorder = self._folder_recorders[addressee]
        else:
            try:
                from cairn.tools.base.address import folder_path
                from cairn.tools.instanceizer.instanceizer import load
                fp = folder_path(addressee)
                recorder = load(fp)
                self._folder_recorders[addressee] = recorder
            except (FileNotFoundError, Exception):
                self._folder_recorders[addressee] = None
                return False
        if recorder is None:
            return False
        try:
            recorder.write({
                "finding": envelope.get("why", "bus message received"),
                "inspector_target": addressee,
                "probe_source": envelope.get("sender", "unknown"),
                "envelope_id": envelope.get("id"),
                "verb": envelope.get("verb", ""),
                "body": envelope.get("body", {}),
            })
            self._ring_delivered.add(envelope["id"])
            self._delivered += 1
            self.emit("delivered", pointer=envelope["id"],
                      values={"addressee": addressee, "by": "folder_instanceizer"})
            return True
        except Exception as exc:  # noqa: BLE001
            self.emit("delivery_failed", pointer=envelope["id"], values={
                "addressee": addressee, "error": f"{type(exc).__name__}: {exc}",
            })
            return False

    def list(self) -> dict:
        """Enumerate registered devices and their per-channel toggle standing."""
        result = {}
        for device_id in self._delivery_hooks:
            toggles = self._channel_toggles.get(device_id, {})
            result[device_id] = {
                "wired": True,
                "channels": {ch: toggles.get(ch, True) for ch in CHANNELS},
            }
        return result

    def toggle(self, device_id: str, channel: str, enabled: bool) -> dict:
        """Enable or disable a device's subscription on one channel."""
        _require_channel(channel)
        if device_id not in self._delivery_hooks:
            raise ValueError(
                f"device {device_id!r} is not wired — toggle requires wire_delivery first"
            )
        self._channel_toggles.setdefault(device_id, {ch: True for ch in CHANNELS})
        self._channel_toggles[device_id][channel] = enabled
        return {"device": device_id, "channel": channel, "enabled": enabled}

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def table(self) -> str:
        return self._table

    @property
    def delivery_table(self) -> str:
        return self._delivery_table

    def _ensure(self) -> None:
        """The transit and receipt tables, owned by the bus — created once, idempotently,
        through db_domain's gate (an ownerless table cannot exist; a different owner is
        refused). Lazy so importing the bus touches no DB (boot-order law)."""
        if not self._ensured:
            store.create_owned_table(self._table, _BUS_OWNER, _TRAFFIC_COLUMNS)
            store.create_owned_table(self._delivery_table, _BUS_OWNER, _DELIVERY_COLUMNS)
            # Migrate: add verb column to an existing transit table that predates it.
            conn = store.connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM information_schema.columns "
                        "WHERE table_schema = 'public' AND table_name = %s "
                        "AND column_name = 'verb'", (self._table,))
                    if cur.fetchone() is None:
                        if not _IDENTIFIER.match(self._table or ""):
                            raise ValueError(
                                f"refusing {self._table!r} as a table name for migration")
                        cur.execute(
                            f'ALTER TABLE "{self._table}" ADD COLUMN '
                            "verb text NOT NULL DEFAULT ''")
            finally:
                conn.close()
            self._ensured = True
            # GATE CONTACT (DiagnosticBase): the transit table came into being — a durable
            # state change, once per instance, never per message. Thin: the pointer is the
            # table; the owner is in settings(). Held until a receiver is wired (Law 7).
            self.emit("transit_table_ensured", pointer=self._table)

    # --- the one way to send ------------------------------------------------

    def post(self, *, sender: str, to: str, channel: str, why: str,
             verb: str = "", body: dict | None = None,
             reply_to: str | None = None) -> dict:
        """Send one message — the SOLE path for inter-device communication. Builds the envelope
        (carrying why + causality, Law 5), appends it to the in-memory ring, and fires the
        delivery hook. Zero DB on the hot path — ``flush()`` batch-writes the ring to Postgres
        on the ground loop pulse. A missing ``why`` is refused (CP3); an unknown channel is
        refused (CP1)."""
        kind = _require_channel(channel)
        if not why:
            raise ValueError("a message carries a why (CP3) — the bus is a causal record, not raw traffic")
        envelope = {
            "id": uuid.uuid4().hex,
            "sender": sender,
            "addressee": to,
            "channel": channel,
            "kind": kind,
            "verb": verb,
            "why": why,
            "body": body or {},
            "reply_to": reply_to,
            "date": datetime.now().isoformat(timespec="seconds"),
        }
        self._ring.append(envelope)
        self._posted += 1
        self._last_envelope = envelope
        self.emit("post", pointer=envelope["id"], values={
            "sender": sender, "addressee": to, "channel": channel,
        })
        if channel == "personal":
            hook = self._delivery_hooks.get(to)
            toggles = self._channel_toggles.get(to, {})
            if hook is not None and toggles.get(channel, True):
                try:
                    hook(envelope)
                except Exception as exc:  # noqa: BLE001
                    self.emit("delivery_failed", pointer=envelope["id"], values={
                        "addressee": to, "error": f"{type(exc).__name__}: {exc}",
                    })
            elif self._try_folder_delivery(to, envelope):
                pass
        return envelope

    # --- the record (full truth) and the view (collapsible) -----------------

    def _ring_matches(self, *, to: str | None = None, channel: str | None = None,
                       reply_to: str | None = None) -> list[dict]:
        """Filter the in-memory ring by the same criteria ``read()`` uses on DB."""
        result = []
        for env in self._ring:
            if to is not None and env.get("addressee") != to:
                continue
            if channel is not None and env.get("channel") != channel:
                continue
            if reply_to is not None and env.get("reply_to") != reply_to:
                continue
            result.append(env)
        return result

    def read(self, *, to: str | None = None, channel: str | None = None,
             reply_to: str | None = None) -> list[dict]:
        """Read the feed — the RECORD, always the full truth (Law 7: the substrate never
        collapses). Merges flushed rows from DB with the in-memory ring, so the full truth
        is visible between flushes. DB rows (older, already flushed) come first; ring rows
        (recent, not yet flushed) come after — insertion order preserved."""
        if channel is not None:
            _require_channel(channel)
        self._ensure()
        clauses, params = [], []
        if to is not None:
            clauses.append("addressee = %s")
            params.append(to)
        if channel is not None:
            clauses.append("channel = %s")
            params.append(channel)
        if reply_to is not None:
            clauses.append("reply_to = %s")
            params.append(reply_to)
        where = (" AND ".join(clauses) + " ORDER BY ctid") if clauses else "TRUE ORDER BY ctid"
        db_rows = store.read(self._table, where=where, params=tuple(params))
        ring_rows = self._ring_matches(to=to, channel=channel, reply_to=reply_to)
        return db_rows + ring_rows

    def request(self, *, sender: str, to: str, channel: str = "personal", why: str,
                verb: str = "", body: dict | None = None,
                timeout: float = 30.0) -> dict:
        """Synchronous exchange: post, then read the correlated reply. ONE DOOR — this is
        post() + a correlated read, not a second path (falsifier 4).

        In the in-process model, the poke chain fires synchronously within post(): the
        target's verb handler posts a reply (with reply_to set to this envelope's id),
        and the reply lands in the ring by the time post() returns. The ring check is
        zero-DB; the timeout falls back to read() (ring + DB) for the multi-process
        future. LOUD on timeout (CP1)."""
        envelope = self.post(sender=sender, to=to, channel=channel, why=why,
                             verb=verb, body=body)
        ring_replies = self._ring_matches(reply_to=envelope["id"])
        if ring_replies:
            return ring_replies[0]
        replies = self.read(reply_to=envelope["id"])
        if replies:
            return replies[0]
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(min(0.1, deadline - time.monotonic()))
            replies = self.read(reply_to=envelope["id"])
            if replies:
                return replies[0]
        raise TimeoutError(
            f"no reply to envelope {envelope['id'][:8]}… from {to} "
            f"within {timeout}s — the target did not reply (CP1: loud, not empty)"
        )

    # --- delivery: the half that was missing --------------------------------

    def undelivered(self, *, to: str | None = None, limit: int = 200) -> list[dict]:
        """Mail that was POSTED to a personal channel and never ARRIVED.

        Merges two sources: DB rows whose receipt hasn't flushed yet (the anti-join), and
        ring rows that haven't been delivered in-memory. DB rows come first (oldest);
        ring rows append. ``_ring_delivered`` tracks in-memory receipts so a flushed
        envelope whose receipt is still in the ring isn't reported as undelivered."""
        self._ensure()
        clauses = [sql_missing_receipt(self._table, self._delivery_table),
                   "channel = 'personal'"]
        params: list = []
        if to is not None:
            clauses.append("addressee = %s")
            params.append(to)
        where = " AND ".join(clauses) + f" ORDER BY ctid LIMIT {int(limit)}"
        db_rows = store.read(self._table, where=where, params=tuple(params))
        db_filtered = [env for env in db_rows
                       if env.get("id") not in self._ring_delivered]
        ring_undelivered = [
            env for env in self._ring
            if env.get("channel") == "personal"
            and (to is None or env.get("addressee") == to)
            and env.get("id") not in self._ring_delivered
        ]
        combined = db_filtered + ring_undelivered
        return combined[:limit]

    def record_delivery(self, envelope_id: str, *, to: str, by: str) -> dict:
        """Write the receipt to the in-memory ring. APPEND, never a rewrite.

        Called by the deliverer AFTER the device has actually taken the envelope — so a
        receiver that raises leaves no receipt and the mail is still there on the next beat.
        The receipt flushes to DB with the next ``flush()`` call."""
        if not envelope_id:
            raise ValueError("a receipt names the envelope it is for — a receipt for nothing "
                             "would silently mark the whole inbox delivered")
        receipt = {"envelope": envelope_id, "addressee": to, "by": by,
                   "date": datetime.now().isoformat(timespec="seconds")}
        self._ring_receipts.append(receipt)
        self._ring_delivered.add(envelope_id)
        self._delivered += 1
        self.emit("delivered", pointer=envelope_id, values={"addressee": to, "by": by})
        return receipt

    def flush(self) -> dict:
        """Batch-write the in-memory ring to Postgres in one transaction.

        Called by the ground loop pulse — the heartbeat IS the flush cadence, no new timer.
        One connection, autocommit off, one commit. A crash between beats loses at most one
        beat's worth of RECORDS — the actions (delivery hooks) already happened."""
        if not self._ring and not self._ring_receipts:
            return {"flushed": 0, "receipts": 0}
        self._ensure()
        to_flush = list(self._ring)
        to_receipt = list(self._ring_receipts)
        self._ring.clear()
        self._ring_receipts.clear()
        self._ring_delivered.clear()
        conn = store.connect()
        conn.autocommit = False
        try:
            for env in to_flush:
                store.write(self._table, _BUS_OWNER, env, conn=conn)
            for rcpt in to_receipt:
                store.write(self._delivery_table, _BUS_OWNER, rcpt, conn=conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        self._flushed += len(to_flush)
        return {"flushed": len(to_flush), "receipts": len(to_receipt)}

    @property
    def ring_depth(self) -> int:
        """How many envelopes are in the ring waiting for flush."""
        return len(self._ring)

    def digest(self, *, to: str, channel: str, keep: int = 3) -> dict:
        """A collapsible VIEW of a channel (Law 7). For a DIAGNOSTIC channel (info/debug) it
        collapses to a count + the last ``keep`` — the surface may summarize. For a RECORD
        channel it REFUSES to collapse: a record of truth is returned whole, because collapsing
        it would be the presentation surface lying about a record (Law 7's hard half). The
        SUBSTRATE is untouched either way — ``read`` still returns the full truth."""
        kind = _require_channel(channel)
        rows = self.read(to=to, channel=channel)
        if kind == RECORD:
            raise ChannelError(
                f"channel {channel!r} is a record of truth — it may not be collapsed into a "
                f"digest (Law 7); read it whole with read(to=..., channel={channel!r})"
            )
        return {
            "channel": channel,
            "kind": kind,
            "count": len(rows),
            "collapsed": max(0, len(rows) - keep),
            "tail": rows[-keep:],
        }

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The one common messaging substrate — the sole path for inter-device "
            "communication (post to send, read to inspect), with per-device channels "
            "(announce/personal records of truth; info/debug diagnostic) and every envelope "
            "carrying its why + causality.",
            "why": "Because comms have exactly one door, 'inspectable + logged + common' are "
            "automatic, not per-surface features (Law 4); durable transit rides db_domain so "
            "one-owner + logged come for free; the bus is a replayable causal record a woken "
            "device rebuilds its context from.",
        }

    def state(self) -> dict:
        return {
            "posted": self._posted,
            "flushed": self._flushed,
            "ring_depth": len(self._ring),
            "last_channel": (self._last_envelope or {}).get("channel"),
            "last_to": (self._last_envelope or {}).get("addressee"),
        }

    def settings(self) -> dict:
        return {
            "channels": {name: kind for name, kind in CHANNELS.items()},
            "transit": f"db_domain — owned table {self._table!r}, owner {_BUS_OWNER!r} (Law 6); "
            "the bus opens no connection of its own",
            "record_vs_diagnostic": "record channels (announce/personal) never collapse (read is "
            "whole truth); diagnostic channels (info/debug) may collapse in a digest VIEW — the "
            "substrate always stores the full truth (Law 7)",
            "wire_protocol": "none yet — the semantics are Cairn's; an MCP adapter at the edge is "
            "a filed edge (swappable, must not hold the design hostage)",
        }

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

import json
import re
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime

from cairn.tools.base.device import BaseDevice
from cairn.devices.db_domain.tools.client import store

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
        # ONE BUS PER INSTANCE (ticket 48519f4789b1 D3). The bus process is the sole writer of
        # transit, so after ONE db read of an addressee's backlog the undelivered mail is known
        # in memory: ``_pending`` holds every personal envelope not yet receipted (post adds,
        # record_delivery removes, flush keeps), ``_loaded`` names the addressees whose backlog
        # has been read (``_loaded_all`` when to=None was asked). A poke then delivers with
        # zero db reads, and a delivery that raised is still offered again on the next poke.
        self._pending: dict[str, dict] = {}
        self._loaded: set[str] = set()
        self._loaded_all = False
        self._db_reads = 0
        # Guards ring/receipt/pending mutation only — microseconds, never a handler — so the
        # bus process's per-connection threads cannot lose a post into a flush (D3, D8).
        self._lock = threading.Lock()

    @classmethod
    @contextmanager
    def scratch(cls, prefix: str = "bus_traffic", device_id: str = "bus"):
        """A bus over a table that cannot outlive this process (ticket 201a37bf1613): the
        transit table is minted through ``store.scratch`` under the bus's owner, its
        ``_delivery`` companion is registered beside it at ``_ensure``, and both drop on
        exit — or on the tester's next sweep if this process is killed first. This is the
        one way a proof gets a bus of its own; a hand-named ``BusDevice(table=...)`` in a
        proof is the leak the ticket measured (2,424 orphan ``_delivery`` tables)."""
        with store.scratch(_BUS_OWNER, prefix, _TRAFFIC_COLUMNS) as table:
            yield cls(table=table, device_id=device_id)

    def wire_delivery(self, device_id: str, deliver: "Callable[[dict], Any]") -> None:
        self._delivery_hooks[device_id] = deliver
        if device_id not in self._channel_toggles:
            self._channel_toggles[device_id] = {ch: True for ch in CHANNELS}

    def unwire_delivery(self, device_id: str) -> None:
        self._delivery_hooks.pop(device_id, None)
        self._channel_toggles.pop(device_id, None)

    @staticmethod
    def _instance_folder(addressee: str):
        """The instance-space folder a non-device addressee names, or None.

        Three spellings, tried in order (ticket 65b34c57ab71 added the last two):
          - a FOLDER, ``~/.cairn/folders/<addressee>/`` — a component with state but no device;
          - a HELD TOOL by full address, ``<device>/<instance>/tools/<tool>``;
          - a HELD TOOL by bare name — ``charter`` finds ``devices/*/*/tools/charter`` under
            whichever holder assembled it, so a tool's own probes need not know their holder.
        A bare name that two holders answer to is ambiguous and resolves to nothing: the bus
        delivers to one addressee or none, never to whichever sorted first.
        """
        from cairn.tools.base import address as _address
        fp = _address.folder_path(addressee)
        if (fp / "instanceizer.json").is_file():
            return fp
        parts = addressee.split("/")
        if len(parts) == 4 and parts[2] == _address.TOOLS and parts[1].isdigit():
            tp = _address.tool_path(parts[0], int(parts[1]), parts[3])
            return tp if (tp / "instanceizer.json").is_file() else None
        if "/" not in addressee:
            held = [p for p in _address.held_tool_paths(addressee)
                    if (p / "instanceizer.json").is_file()]
            if len(held) == 1:
                return held[0]
        return None

    def _try_folder_delivery(self, addressee: str, envelope: dict) -> bool:
        """Fallback delivery for non-device addressees via an instanceizer.

        If the addressee names an instance-space folder (``_instance_folder``: a folder, a
        held tool by address, or a held tool by bare name) that carries an instanceizer, load
        its DataRecorder and write the envelope. Returns True if delivered, False if nothing
        on disk answers to the name."""
        # ONLY A LOADED RECORDER IS CACHED (ticket cff5a197b3c4). A cached None outlived the
        # folder gaining its instanceizer, so the press_office WATCHME and a charter envelope
        # stood undelivered from 2026-09-30 although both names resolved two days later.
        recorder = self._folder_recorders.get(addressee)
        fresh = recorder is None
        if fresh:
            try:
                from cairn.tools.instanceizer.instanceizer import load
                fp = self._instance_folder(addressee)
                recorder = load(fp) if fp is not None else None
            except (FileNotFoundError, Exception):
                return False
            if recorder is None:
                return False
            self._folder_recorders[addressee] = recorder
        if not self._folder_write(recorder, addressee, envelope):
            return False
        if fresh:
            # WHAT STOOD BEFORE THE FOLDER ANSWERED lands now, once per bus life: nothing
            # else ever re-offers a stored envelope to a folder, which has no shim to drain.
            for standing in self.undelivered(to=addressee, limit=10000):
                if standing["id"] != envelope["id"]:
                    self._folder_write(recorder, addressee, standing)
        return True

    def _folder_write(self, recorder, addressee: str, envelope: dict) -> bool:
        """Write one envelope into a folder's recorder and RECEIPT it. A bare
        ``_ring_delivered`` mark is cleared by ``flush()``, after which the envelope read
        undelivered from the store again — the receipt is what makes the taking durable."""
        try:
            recorder.write({
                "finding": envelope.get("why", "bus message received"),
                "inspector_target": addressee,
                "probe_source": envelope.get("sender", "unknown"),
                "envelope_id": envelope.get("id"),
                "verb": envelope.get("verb", ""),
                "body": envelope.get("body", {}),
            })
        except Exception as exc:  # noqa: BLE001
            self.emit("delivery_failed", pointer=envelope["id"], values={
                "addressee": addressee, "error": f"{type(exc).__name__}: {exc}",
            })
            return False
        self.record_delivery(envelope["id"], to=addressee, by="folder_instanceizer")
        return True

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
            # A transit table born through store.scratch() (a proof's) takes its receipt
            # table down with it: register the companion under the parent's pid so the
            # scratch exit and the tester's sweep drop both. Measured 2026-09-06: 2,424
            # `_delivery` tables leaked because the proofs never knew this one existed
            # (ticket 201a37bf1613).
            if store.is_scratch(self._table):
                store.register_scratch_companion(self._table, self._delivery_table)
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
            # JSON-safe at the door (ticket 48519f4789b1): a body that only json.dumps(default=
            # str) could carry — a Decimal cost read from the store, measured 2026-10-03 — would
            # otherwise sit in the ring and fail every flush after it, the shutdown's included.
            # The socket path already crossed this way; an in-process post now matches it.
            "body": json.loads(json.dumps(body or {}, default=str)),
            "reply_to": reply_to,
            "date": datetime.now().isoformat(timespec="seconds"),
        }
        with self._lock:
            self._ring.append(envelope)
            if channel == "personal":
                self._pending[envelope["id"]] = envelope
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
        self._db_reads += 1
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
        future. LOUD on timeout (CP1).

        THE REPLY IT RETURNS IS IN THE REQUESTER'S HAND, so request() writes its receipt
        (ticket 6b1e13704e17; measured 2026-10-02, 2791 trouble->cairn replies stood
        undelivered because nothing receipted them) — unless the poke chain already
        receipted it for a wired requester, which the ``_ring_delivered`` guard reads."""
        envelope = self.post(sender=sender, to=to, channel=channel, why=why,
                             verb=verb, body=body)
        ring_replies = self._ring_matches(reply_to=envelope["id"])
        if ring_replies:
            return self._taken(ring_replies[0], sender)
        replies = self.read(reply_to=envelope["id"])
        if replies:
            return self._taken(replies[0], sender)
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(min(0.1, deadline - time.monotonic()))
            replies = self.read(reply_to=envelope["id"])
            if replies:
                return self._taken(replies[0], sender)
        raise TimeoutError(
            f"no reply to envelope {envelope['id'][:8]}… from {to} "
            f"within {timeout}s — the target did not reply (CP1: loud, not empty)"
        )

    def _taken(self, reply: dict, sender: str) -> dict:
        """Receipt the reply request() hands back, once: a wired requester's hook already
        receipted it inside post()'s poke chain (the reply id is in ``_ring_delivered``)."""
        if reply["id"] not in self._ring_delivered:
            self.record_delivery(reply["id"], to=sender, by=sender)
        return reply

    # --- delivery: the half that was missing --------------------------------

    def undelivered(self, *, to: str | None = None, limit: int = 200) -> list[dict]:
        """Mail that was POSTED to a personal channel and never ARRIVED, oldest first.

        ONE DB READ PER ADDRESSEE, then memory (ticket 48519f4789b1 D3). The first ask for
        ``to`` (or for everyone, ``to=None``) reads the store's anti-join — the backlog from
        before this bus was born — and folds it into ``_pending`` ahead of what this bus has
        posted since. Every later ask answers from ``_pending`` alone: the bus is the sole
        writer of transit, so nothing can land in the table that it did not post. Envelopes
        already receipted in memory (``_ring_delivered``, kept until their receipt is
        committed) are never folded back in."""
        if not (self._loaded_all or (to is not None and to in self._loaded)):
            self._ensure()
            clauses = [sql_missing_receipt(self._table, self._delivery_table),
                       "channel = 'personal'"]
            params: list = []
            if to is not None:
                clauses.append("addressee = %s")
                params.append(to)
            where = " AND ".join(clauses) + " ORDER BY ctid"
            db_rows = store.read(self._table, where=where, params=tuple(params))
            self._db_reads += 1
            with self._lock:
                merged = {env["id"]: env for env in db_rows
                          if env.get("id") not in self._ring_delivered}
                merged.update(self._pending)
                self._pending = merged
                if to is None:
                    self._loaded_all = True
                else:
                    self._loaded.add(to)
        with self._lock:
            waiting = [env for env in self._pending.values()
                       if to is None or env.get("addressee") == to]
        return waiting[:limit]

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
        with self._lock:
            self._ring_receipts.append(receipt)
            self._ring_delivered.add(envelope_id)
            self._pending.pop(envelope_id, None)
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
        # THE SWAP IS ATOMIC (ticket 48519f4789b1 D3): what is posted while this batch is
        # being written lands in the NEXT flush, never cleared unseen. A failed write puts
        # the batch back ahead of anything newer, so a down store loses no record.
        with self._lock:
            to_flush, self._ring = self._ring, []
            to_receipt, self._ring_receipts = self._ring_receipts, []
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
            with self._lock:
                self._ring = to_flush + self._ring
                self._ring_receipts = to_receipt + self._ring_receipts
            raise
        finally:
            conn.close()
        # A receipt is in the store now, so the anti-join excludes its envelope; only now may
        # the in-memory mark go.
        with self._lock:
            self._ring_delivered.difference_update(r["envelope"] for r in to_receipt)
        self._flushed += len(to_flush)
        return {"flushed": len(to_flush), "receipts": len(to_receipt)}

    def spill(self, path) -> dict:
        """Write what the ring still holds to ``path`` as JSON lines and clear it — the bus's
        last act when a flush has failed and the process must still end (ticket 48519f4789b1).
        Appends, so a second failed exit before a restore loses nothing either. Each line is
        ``{"envelope": {...}}`` or ``{"receipt": {...}}``."""
        with self._lock:
            envs, self._ring = self._ring, []
            rcpts, self._ring_receipts = self._ring_receipts, []
        if not envs and not rcpts:
            return {"spilled": 0, "receipts": 0}
        with open(path, "a", encoding="utf-8") as fh:
            for env in envs:
                fh.write(json.dumps({"envelope": env}, default=str) + "\n")
            for rcpt in rcpts:
                fh.write(json.dumps({"receipt": rcpt}, default=str) + "\n")
        return {"spilled": len(envs), "receipts": len(rcpts)}

    def restore(self, path) -> dict:
        """Put a spill back in the ring ahead of anything newer; the next ``flush()`` writes it.
        The file is the caller's to retire once that flush lands."""
        envs, rcpts = [], []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                if "envelope" in row:
                    envs.append(row["envelope"])
                elif "receipt" in row:
                    rcpts.append(row["receipt"])
        with self._lock:
            self._ring = envs + self._ring
            self._ring_receipts = rcpts + self._ring_receipts
            self._ring_delivered.update(r["envelope"] for r in rcpts)
        return {"restored": len(envs), "receipts": len(rcpts)}

    @property
    def db_reads(self) -> int:
        """How many times this bus has read the store — the instrument the one-bus proof
        measures a ring hit with (ticket 48519f4789b1 falsifier 2)."""
        return self._db_reads

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

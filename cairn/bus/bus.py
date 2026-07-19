"""bus — the ONE common messaging substrate for everything, made a device.

THE SECOND SUBSTRATE (converged with Akien 2026-07-18;
``CairnCommons/intentions/I-heartbeat-callbacks-and-bus.md``). Cairn runtime hangs on
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

import uuid
from datetime import datetime

from cairn.base.device import BaseDevice
from cairn.db_domain import store

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

# The transit table's columns — the envelope, made durable. ``body`` is jsonb so a
# structured payload survives the round-trip intact; everything else is text. ``addressee``
# rather than ``to`` (a SQL-adjacent word) keeps the column name unambiguous.
_TRAFFIC_COLUMNS = {
    "id": "text",
    "sender": "text",
    "addressee": "text",
    "channel": "text",
    "kind": "text",
    "why": "text",
    "body": "jsonb",
    "reply_to": "text",
    "date": "text",
}
_BUS_OWNER = "bus"


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
    """

    def __init__(self, table: str = "bus_traffic", device_id: str = "bus") -> None:
        super().__init__()
        self._table = table
        self._device_id = device_id
        self._ensured = False
        self._posted = 0
        self._last_envelope: dict | None = None

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def table(self) -> str:
        return self._table

    def _ensure(self) -> None:
        """The transit table, owned by the bus — created once, idempotently, through db_domain's
        gate (an ownerless table cannot exist; a different owner is refused). Lazy so importing
        the bus touches no DB (boot-order law)."""
        if not self._ensured:
            store.create_owned_table(self._table, _BUS_OWNER, _TRAFFIC_COLUMNS)
            self._ensured = True

    # --- the one way to send ------------------------------------------------

    def post(self, *, sender: str, to: str, channel: str, why: str,
             body: dict | None = None, reply_to: str | None = None) -> dict:
        """Send one message — the SOLE path for inter-device communication. Builds the envelope
        (carrying why + causality, Law 5), writes it as an owned transit row through db_domain
        (owner ``"bus"``, Law 6), and returns it. A missing ``why`` is refused (CP3 — a message
        with no reason is a defect); an unknown channel is refused (CP1)."""
        kind = _require_channel(channel)
        if not why:
            raise ValueError("a message carries a why (CP3) — the bus is a causal record, not raw traffic")
        envelope = {
            "id": uuid.uuid4().hex,
            "sender": sender,
            "addressee": to,
            "channel": channel,
            "kind": kind,
            "why": why,
            "body": body or {},
            "reply_to": reply_to,
            "date": datetime.now().isoformat(timespec="seconds"),
        }
        self._ensure()
        store.write(self._table, _BUS_OWNER, envelope)
        self._posted += 1
        self._last_envelope = envelope
        return envelope

    # --- the record (full truth) and the view (collapsible) -----------------

    def read(self, *, to: str | None = None, channel: str | None = None) -> list[dict]:
        """Read the feed — the RECORD, always the full truth (Law 7: the substrate never
        collapses). Filter by addressee and/or channel. Reading a device's feed IS inspecting
        it. Ordered by insertion (ctid) so causality reads in the order it happened."""
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
        where = (" AND ".join(clauses) + " ORDER BY ctid") if clauses else "TRUE ORDER BY ctid"
        return store.read(self._table, where=where, params=tuple(params))

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

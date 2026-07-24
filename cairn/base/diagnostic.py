"""DiagnosticBase — the transition-grade emission mechanism every device inherits.

Cairn's evidence today is OUTCOME-grade: a VALIDATION says what PASSED and why; a journey
says what happened across devices. What was missing is the TRANSITION-grade surface — the
one that would have spoken when ``system_rackmount`` went red 2/5 *silently* (no assertion,
no trace). This is that surface: at a GATE CONTACT — a state transition or a boundary
crossing — a device sends home a microsecond-stamped record of what crossed, so a red
(especially a silent one) has a readable trace to review. Law 3 (nothing known until
measured — the emission IS the measurement) and Law 7 (loud at the diagnostic surface).

WHERE IT LIVES — the base class, inherited by everybody, the way CP1-CP6 are inherited via
``CoreValuesMixin``. ``BaseDevice`` composes this mixin, so every device carries ``emit()``
structurally: you cannot be a device without being able to send diagnostics home. Kept
import-light on purpose — stdlib only (``datetime``), no DB, no loguru, no sink backend
(the boot-order law). UU's ``DiagnosticBase`` loguru/JSON-sink machinery is NOT carried; the
one mechanism carried over is the microsecond stamp (below).

WHERE HOME IS — CC's own shim (``cc_0`` / ``cc.0``, whichever the instance id is), the
diagnostic mailbox, *for now*. The receiver is INJECTED (``set_diagnostic_receiver``), never
imported — in the running system it is wired to CC's shim; here it is whatever a caller wires.
This is the honest stopgap: a proper diagnostic device owns the mailbox later; the shim is the
receiver today so we have the instrument *now* (the filed edge).

WHO ISSUES IT — the GATE, not the ticket. The device at the gate calls ``emit`` when something
crosses; it POINTS to the ticket (``pointer`` = the ticket's id / address — the TIE) rather than
copying it. The owned data stays with its owner (Law 6); only the pointer crosses. Keep the
emission THIN — a breadcrumb, not a payload: the gate names itself, points to the ticket, and
stamps the time. We do not enrich the top of it. (A full-value snapshot rides in ``values`` only
for the narrow case where you are watching specific values, not a ticket going by.)

THE TIMESTAMP POINTS TO THE LOGS. The microsecond stamp is not merely an ordering key — it is the
index INTO the fuller logs. Those logs are a separate, CACHE-CLASS tier: json files in
instance-space (``~/.cairn/``) that EVAPORATE after ~30 days — the throwaway history, distinct
from Cairn's durable records (VALIDATIONs, journeys). The breadcrumb (thin, home to CC's mailbox)
and the logs (fat, timestamp-indexed) are two tiers; the emission is the tie between them. v0: the
mailbox is in-memory on the receiver; flushing to the 30-day json tier grows against need — a
filed edge, not faked here.

THE INSPECTOR DOES THE WORK — it CRAWLS. The diagnostic inspector (``diagnostic_inspector``,
built) is where the intelligence lives, not the emission. Reacting to a fired callback it applies
FILTERS (by_pointer, by_gate — conjoined) to the log, gathers the whole transaction (the workflow
item AND its logging), and TRIMS it into the FINDINGS — the coherent json slice whose audience is
CC. The emission stays dumb so the inspector can be smart (Law 1: the diagnostic surface's
inference is compiled once, in the inspector — the same move as ``inference_domain``).

THE DISCIPLINE — targeted and TEMPORARY. You place a gate-contact instrument when you are watching
for something specific, then TAKE IT DOWN. Not standing callbacks left hanging: a permanent
firehose turns CC's mailbox into noise (the shrinking-footprint principle — instrument on demand,
event not poll). Put one to catch a flake; remove it once caught.

THE 6th PLACE AFTER THE DECIMAL — every record is stamped to the microsecond
(``f"{ts.microsecond:06d}"``), so no two entries collide and none are lost — you can order and
slice the whole diagnostic band precisely. This is the mechanism carried over from UU's sink
(``diagnostic_base/base.py``); the loguru machinery around it is not. ``now`` is passed
explicitly (defaulting to the real UTC clock) so an emission is provable without a clock, the
same way the heartbeat's ``beat`` takes ``now``.
"""

from __future__ import annotations

from datetime import datetime, timezone


class DiagnosticBase:
    """The send-home mechanism composed onto every device.

    Pure mixin over stdlib. Cooperative ``__init__`` for the normal construction path, but the
    accessors also lazy-init their state via ``__dict__`` so ``emit`` is honest even for a device
    whose ``__init__`` did not chain ``super()`` — an uninitialised diagnostic surface must never
    be the reason a record is silently lost.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._diagnostic_receiver = None
        self._held_diagnostics: list[dict] = []

    @property
    def diagnostic_source(self) -> str:
        """Who is emitting — stamped on every record. Defaults to the class name; a running
        device overrides with its real instance id (filed edge: the id convention firms up with
        instance-space wiring)."""
        return type(self).__name__

    def set_diagnostic_receiver(self, receiver) -> None:
        """Wire HOME. ``receiver`` answers ``receive_diagnostic(record)``. In the running system
        this is CC's shim (``cc_0``) — the diagnostic mailbox, for now. Passing ``None`` unwires
        it (records then HOLD rather than send), which is how a temporary instrument is torn down."""
        self._diagnostic_receiver = receiver

    def emit(self, gate: str, *, pointer=None, values: dict | None = None, now=None) -> dict:
        """Send one GATE-CONTACT record home, microsecond-stamped.

        ``gate`` names the transition / boundary crossed. ``pointer`` is what is travelling
        through it (a ticket id, an artifact ref) — usually all that goes home. ``values`` is a
        full snapshot, carried ONLY when you are watching specific values. ``now`` is explicit for
        provability (default: the real UTC clock).

        With no receiver wired the record is HELD (retrievable via ``held_diagnostics()``), never
        silently dropped — loud at the diagnostic surface even when home is unreachable (Law 7).
        Returns the record, so a caller (or a test) can read exactly what was sent."""
        ts = now or datetime.now(timezone.utc)
        record = {
            "ts": ts.isoformat(),
            "us": f"{ts.microsecond:06d}",   # the 6th place after the decimal — none lost; indexes the logs
            "source": self.diagnostic_source,
            "gate": gate,
            "pointer": pointer,              # the ticket's id/address — the TIE the inspector crawls on
            "values": values or {},          # a fat snapshot ONLY when watching values (norm: thin, empty)
        }
        receiver = getattr(self, "_diagnostic_receiver", None)
        if receiver is None:
            record["home"] = "held"
            self.__dict__.setdefault("_held_diagnostics", []).append(record)
            return record
        record["home"] = "sent"
        receiver.receive_diagnostic(record)
        return record

    def held_diagnostics(self) -> list[dict]:
        """Records emitted while no receiver was wired — HELD, not lost (Law 7). A non-empty list
        here is itself a finding: something was emitting into a torn-down or never-wired home."""
        return list(getattr(self, "_held_diagnostics", []))

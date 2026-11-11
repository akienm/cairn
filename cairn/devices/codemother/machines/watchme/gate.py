"""CodeMother's WATCHME gate — a probe's red finding fails its ticket back to design.

Outline 3.3.4, 3.3.4.1 and 9.4.1.5 (Akien 2026-11-10): the gates are CodeMother's; the harbor's
bus face answers status queries and the crossing notice only. Every WATCHME probe posts its
finding here, as ``machines/watchme/watch`` on codemother's bus face, body
``{ticket, holds, finding}`` (built through ``watch_carry`` in cairn/tools/base/probe.py).

``holds`` is whether the ticket's falsifier still holds under live use. True changes nothing.
False is design work the ticket owns, so the ticket's own instance fails the gate
(``Ticket.failed``): it reaches FIXME with the finding as its one ``watchme`` lack, tells the
harbor, and asks design to queue it — and with no handler it throws a trouble and waits.

THE ACTOR IS THE ENVELOPE'S SENDER (Law 6): the bus stamps it; nothing in the body can claim
a different hand.

THE CROSSING IS JOURNALED AT THE COMPONENT HOLDING THE PROBE: the probe path walked up to its
nearest charter (the harbor's rule, kept: 0 of 90 standing WATCHME tickets named an owning
component, 2026-10-03). A probe under no charter is refused rather than moved unjournaled.

Only a ticket at a rest (PROVED or WATCHME) moves; anything else is left where it stands and the
reply says so. Refusals come back as data (Law 7). Imports no device (RULE 1).
"""

from __future__ import annotations

from pathlib import Path

from cairn.tools.base.diagnostic import DiagnosticBase

HOLDER = "codemother"
VERB = "watch"
RECEIVER = {"what": "codemother watchme gate", "in": "cairn/devices/codemother/machines/watchme"}
_REPO = Path(__file__).resolve().parents[5]
_RESTS = ("PROVED", "WATCHME")


class Voice(DiagnosticBase):
    """The participant a gate hands a Ticket: the holder's bus, with the holder as sender.

    The Ticket asks and tells without naming itself (it has no bus address of its own); this
    stamps ``codemother`` and the personal channel. With no bus it dials ``reach()`` on first
    use, so a device constructed without one still speaks."""

    def __init__(self, bus=None, sender: str = HOLDER) -> None:
        super().__init__()
        self._bus = bus
        self.sender = sender

    def _dial(self):
        if self._bus is None:
            from cairn.tools.bus_client import reach
            self._bus = reach()
        return self._bus

    def request(self, **kw):
        kw.pop("channel", None)
        return self._dial().request(sender=self.sender, channel="personal", **kw)

    def post(self, **kw):
        kw.pop("channel", None)
        return self._dial().post(sender=self.sender, channel="personal", **kw)


class WatchmeGate(DiagnosticBase):
    """The gate a standing WATCHME probe reports to.

    ``roots`` is ``{repo, commons, instance}`` — a proof's scratch world — or None for the live
    one. The device constructs it with none, so a bus caller cannot choose the evidence."""

    def __init__(self, *, participant=None, roots=None) -> None:
        super().__init__()
        self._participant = participant if participant is not None else Voice()
        self._roots = roots
        if roots is not None:
            self.set_diagnostic_roots(roots)

    def declared_verbs(self) -> dict:
        return {VERB: self.watch}

    def _where(self) -> tuple[Path, Path]:
        from cairn.tools.base import ticket_file
        if self._roots is not None:
            return Path(self._roots["commons"]) / "tickets", Path(self._roots["repo"])
        return Path(ticket_file._TICKETS), _REPO

    def watch(self, envelope: dict) -> dict:
        def refuse(reason: str) -> dict:
            return {"accepted": False, "verb": VERB, "device": HOLDER, "reason": reason}

        body = envelope.get("body", {}) or {}
        actor = envelope.get("sender") or ""
        if not actor:
            return refuse("this envelope names no sender, and the sender IS the actor (Law 6)")
        tid = body.get("ticket")
        if not isinstance(tid, str) or not tid:
            return refuse("watch needs a ticket: the id of the ticket whose falsifier was "
                          "measured")
        holds = body.get("holds")
        if not isinstance(holds, bool):
            return refuse(f"holds must be true or false, got {holds!r}")
        finding = body.get("finding")
        if holds is False and (not isinstance(finding, str) or not finding.strip()):
            return refuse("a red watch needs a finding: it becomes the ticket's lack")

        tickets, repo = self._where()
        from cairn.tools.base.ticket_file import find_ticket, read_ticket
        found = find_ticket(tid, tickets)
        if found is None:
            return refuse(f"ticket {tid} resolves to no one plan file under {tickets}")
        try:
            doc = read_ticket(found)
        except (OSError, ValueError) as exc:
            return refuse(f"ticket {tid} does not read: {type(exc).__name__}: {exc}")
        spec = doc.get("watchme")
        probe = spec.get("probe") if isinstance(spec, dict) else None
        if not isinstance(probe, str) or not probe:
            return refuse(f"ticket {tid}'s watchme names no probe, so no component's history "
                          "can take the crossing")
        comp = (repo / probe).parent
        while comp != repo and comp != comp.parent and not (comp / "intention+why.json").is_file():
            comp = comp.parent
        if comp == repo or not (comp / "intention+why.json").is_file():
            return refuse(f"ticket {tid}'s probe {probe} sits under no component charter")

        if holds:
            return {"accepted": True, "verb": VERB, "device": HOLDER, "ticket": tid,
                    "acted": "none", "said": "the falsifier holds; nothing changes"}
        from cairn.tools.operator_inbox.inbox import cursor_of
        workflow = doc.get("workflow_and_state", "")
        token = cursor_of(workflow)   # the one cursor reader (one-status-everywhere)
        if token is None:
            return refuse(f"ticket {tid}'s workflow does not parse: {workflow!r}")
        here = token.split("(")[0].split(":")[0]
        if here not in _RESTS:
            return {"accepted": True, "verb": VERB, "device": HOLDER, "ticket": tid,
                    "acted": "none",
                    "said": f"the ticket stands at {here}, not at a rest; a WATCHME finding "
                            "moves only a PROVED or WATCHME ticket"}

        from cairn.machines.ticket.ticket import Ticket
        out = Ticket.at(found, roots=self._roots).failed(
            [{"kind": "watchme", "why": finding}], participant=self._participant,
            history_path=str(comp / "history.json"), state_path=str(comp / "state.json"),
            actor=actor, why=f"a WATCHME finding: {finding}")
        self.debug_sink.emit("watch_received", pointer=tid,
                             values={"actor": actor, "acted": "fixme",
                                     "queued": out.get("queued")})
        return {"accepted": True, "verb": VERB, "device": HOLDER, "ticket": tid,
                "acted": "fixme", "queued": out.get("queued"), "trouble": out.get("trouble"),
                "workflow": out.get("workflow")}

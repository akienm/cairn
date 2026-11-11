"""CodeMother's CLEARANCE gate on her bus face — a ticket asks it to queue its fileref.

Outline 3.3.4.3 and 9.6 (Akien 2026-11-10, Q#80/Q#81): a ticket crosses a gate by asking that
gate to queue it, sending only its fileref: ``devices/codemother/0/machines/clearance/queueme
<fileref>``. The gate instantiates the ticket on its own side (``Ticket.at``), and that
instance processes the pass. ``cross`` left with the harbor's ``clear`` (9.4.1.5); this is
where the crossing is asked now.

WHAT THE GATE DERIVES, AND FROM WHAT. The fileref is the only input, so everything else is
read off the ticket and the disk, never taken from the asker:

  - the TARGET is the next step of the ticket's workflow after its cursor;
  - PROVEN_BY is, into PROVED, every proof the ticket's crossings named since its latest
    BUILDME (``crossings.proven_by_since_buildme``, the one rule hollow, proof_coverage and
    this gate read); toward any other step, every ``proofs/*.py`` whose ``PROVES`` names the
    ticket (``proof_coverage.declared``) — the proof declares what it proves, so no hand has
    to name it;
  - the JOURNAL is the owning intention's directory (Law 5: intent, state and proofs share
    an address).

THE GATE DECIDES NOTHING. ``clearance.clear`` decides (authority, proven-space, room,
retirement, coverage, rules and truth), and the gate hands it to the ticket as the door its
pass crosses through (``Ticket.passed(cross=...)``), so the crossing is journaled once. The
actor is codemother, the holder; the envelope's sender rides into the journal as
``asked_by``. A refusal comes back as data carrying the exception's class name (Law 7); a
failure after the crossing stood is said as one, never as a refusal, because the boat moved.

Imports no device (RULE 1).
"""

from __future__ import annotations

import functools
import os
from pathlib import Path

from cairn.tools.base.diagnostic import DiagnosticBase

HOLDER = "codemother"
VERB = "queueme"
DOOR = "clearance"
_REPO = Path(__file__).resolve().parents[5]
_COMMONS = _REPO.parent / "CairnCommons"
_SKIP = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def journal_of(ticket, *, roots=None) -> dict:
    """``{history_path, state_path}`` of the component that owns ``ticket``, or ValueError.

    The owning intention resolves under the repo, then the commons, then as an absolute path —
    ``roots`` (``{repo, commons, ...}``) for a proof's scratch world, None for the live one. Read
    by this gate's crossing and by every chart-stage gate's fail (``chart_gate``)."""
    repo, commons = ((Path(roots["repo"]), Path(roots["commons"])) if roots is not None
                     else (_REPO, _COMMONS))
    owning = ticket.doc().get("owning_intention") or ""
    if not owning:
        raise ValueError(f"ticket {ticket.id} names no owning_intention, so the component "
                         "whose journal the crossing writes is unknown")
    comp = next((r / owning for r in (repo, commons) if (r / owning).is_file()), None)
    if comp is None and Path(owning).is_absolute() and Path(owning).is_file():
        comp = Path(owning)
    if comp is None:
        raise ValueError(f"ticket {ticket.id}'s owning_intention {owning!r} resolves under "
                         f"neither {repo} nor {commons}")
    return {"history_path": str(comp.parent / "history.json"),
            "state_path": str(comp.parent / "state.json")}


class ClearanceGate(DiagnosticBase):
    """The gate a ticket's crossing asks.

    ``roots`` is ``{repo, commons, instance}`` — a proof's scratch world — or None for the live
    one. The device constructs it with none, so a bus caller cannot choose the evidence."""

    def __init__(self, *, participant=None, roots=None) -> None:
        super().__init__()
        if participant is None:
            from cairn.devices.codemother.machines.watchme.gate import Voice
            participant = Voice()
        self._participant = participant
        self._roots = roots
        if roots is not None:
            self.set_diagnostic_roots(roots)

    def declared_verbs(self) -> dict:
        return {VERB: self.queueme}

    def _where(self) -> tuple[Path, Path, Path]:
        from cairn.tools.base import ticket_file
        if self._roots is not None:
            commons = Path(self._roots["commons"])
            return commons / "tickets", Path(self._roots["repo"]), commons
        return Path(ticket_file._TICKETS), _REPO, _COMMONS

    # --- what the gate reads off the ticket ---------------------------------

    def crossing_of(self, ticket) -> dict:
        """``{target, proven_by, history_path, state_path}`` for ``ticket``, or ValueError."""
        from cairn.tools.base.workflow_grammar import parse_workflow
        wf = parse_workflow(ticket.workflow)
        if wf.cursor + 1 >= len(wf.path):
            raise ValueError(f"ticket {ticket.id} stands at {wf.here}, the last step of its "
                             "workflow: there is no next step to cross to")
        target = wf.path[wf.cursor + 1]
        return {"target": target, "proven_by": self.proven_by(ticket.id, target),
                **journal_of(ticket, roots=self._roots)}

    def proven_by(self, tid: str, target: str) -> list[str]:
        if target == "PROVED":
            from cairn.tools.base.crossings import proven_by_since_buildme
            from cairn.devices.codemother.machines.clearance import clearance
            # The live gate reads the crossing world the door reads (``clearance._crossing_roots``),
            # so the proofs it hands the door are derived from the journals the door checks.
            roots = self._roots if self._roots is not None else clearance._crossing_roots()
            named = proven_by_since_buildme(tid, roots)
            if named:
                return named
        return self.declaring(tid)

    def declaring(self, tid: str) -> list[str]:
        """Every ``proofs/*.py`` under the repo and the commons whose ``PROVES`` names ``tid``,
        repo-relative where it lies under the repo."""
        from cairn.tools.proof_coverage import declared
        _, repo, commons = self._where()
        out: list[str] = []
        for root in (repo, commons):
            if not root.is_dir():
                continue
            for here, dirs, files in os.walk(root):
                dirs[:] = sorted(d for d in dirs if d not in _SKIP)
                if Path(here).name != "proofs":
                    continue
                for name in sorted(files):
                    if not name.endswith(".py"):
                        continue
                    p = Path(here) / name
                    try:
                        if tid not in p.read_text(encoding="utf-8", errors="replace"):
                            continue
                    except OSError:
                        continue
                    if tid in declared(p):
                        out.append(str(p.relative_to(repo)) if root == repo else str(p))
        return out

    # --- the verb -----------------------------------------------------------

    def queueme(self, envelope: dict) -> dict:
        def answer(accepted: bool, **more) -> dict:
            return {"accepted": accepted, "verb": VERB, "device": HOLDER, "door": DOOR, **more}

        body = envelope.get("body", {}) or {}
        asked_by = envelope.get("sender") or ""
        fileref = body.get("fileref")
        if not isinstance(fileref, str) or not fileref:
            return answer(False, reason="queueme needs a fileref: the ticket's plan path or id, "
                                        "and nothing else (outline 3.3.4.3)")
        tickets, _, _ = self._where()
        from cairn.machines.ticket.ticket import Ticket
        try:
            ticket = Ticket.at(fileref, tickets_dir=tickets, roots=self._roots)
            crossing = self.crossing_of(ticket)
        except (OSError, ValueError) as exc:
            return answer(False, fileref=fileref, reason=f"{type(exc).__name__}: {exc}")
        from cairn.devices.codemother.machines.clearance import clearance
        tid, target, proofs = ticket.id, crossing["target"], crossing["proven_by"]
        crossed: dict = {}

        def door(workflow, to, **kw):
            crossed["workflow"] = clearance.clear(workflow, to, boat_id=tid, proven_by=proofs, **kw)
            return crossed["workflow"]

        said = {"ticket": tid, "fileref": ticket.fileref, "target": target, "proven_by": proofs,
                "asked_by": asked_by}
        try:
            new = ticket.passed(target, participant=self._participant,
                                history_path=crossing["history_path"],
                                state_path=crossing["state_path"], actor=HOLDER,
                                why=f"{tid} queued at clearance by {asked_by or 'an unnamed sender'}",
                                cross=door, asked_by=asked_by)
        except Exception as exc:  # noqa: BLE001 — a refusal IS the answer, said as data
            if "workflow" in crossed:
                return answer(True, **said, workflow=crossed["workflow"],
                              after_crossing=f"{type(exc).__name__}: {exc}")
            return answer(False, **said, refusal=type(exc).__name__, reason=str(exc))
        return answer(True, **said, workflow=new)

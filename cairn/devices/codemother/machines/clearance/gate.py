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
crossing is the ticket's own act (outline 9.6), so its HAND is the asker's: the envelope's sender
crosses whenever the boat's owning intention admits it (``hand_of``), and codemother, the holder,
crosses otherwise (ticket f76d01d3170c — a boat only CC may move could not cross when CC asked).
``clear`` still judges that hand against the owner, so the choice never widens authority. The
sender rides into the journal as ``asked_by`` either way. A refusal comes back as data carrying the exception's class name (Law 7); a
failure after the crossing stood is said as one, never as a refusal, because the boat moved.

A CROSSING ANSWERS LATER, OFF HER REQUEST THREAD (ticket 7c4138f7fa33, as e4714e460e32 did for the
chart stages). The shim holds one lock per device while a verb runs, and a crossing's records
commit under the pre-commit reseal: measured 2026-11-24, b03dce633aa8's PROVEME commit ran 7m56s
inside ``queueme`` while the asker timed out at 120 s and a hollow's ask to codemother at 300 s.
A ``deferred`` gate (the one the shim builds) checks the fileref, queues the envelope on the
gate's one FIFO and returns None, so the shim posts nothing and lets go. One worker per process
runs the crossing (``_run``, the body unchanged) and posts the dict it returns to the asker with
``reply_to`` set to the asking envelope's id, which is the reply the asker's ``request`` is
reading for. One FIFO and one worker per PROCESS, not per gate object, because her device builds
its gates afresh at each lookup: two crossings for one ticket run in the order sent, and two
commits never race for one index. A gate built without ``deferred`` answers in the call, as before.

Imports no device (RULE 1).
"""

from __future__ import annotations

import functools
import os
import queue
import threading
from pathlib import Path

from cairn.tools.base.diagnostic import DiagnosticBase
from cairn.tools.system_word import fold

HOLDER = "codemother"
VERB = "queueme"
DOOR = "clearance"
_REPO = Path(__file__).resolve().parents[5]
_COMMONS = _REPO.parent / "CairnCommons"
_SKIP = {".git", "__pycache__", "node_modules", ".venv", "venv"}

# the gate's one FIFO and the one worker draining it, for this process
_QUEUES: dict[str, queue.Queue] = {}
_WORKERS: dict[str, threading.Thread] = {}
_START = threading.Lock()


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
    one. The device constructs it with none, so a bus caller cannot choose the evidence.
    ``deferred`` queues the crossing on the gate's worker and answers by ``reply_to``; the shim
    builds it so, and a gate built without it answers in the call."""

    def __init__(self, *, participant=None, roots=None, deferred: bool = False) -> None:
        super().__init__()
        if participant is None:
            from cairn.devices.codemother.machines.watchme.gate import Voice
            participant = Voice()
        self._participant = participant
        self._roots = roots
        self._deferred = deferred
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
        proven_by = (self.host_seam_proof(ticket) if fold(wf.node_class) == "host-seam"
                     else self.proven_by(ticket.id, target))
        return {"target": target, "proven_by": proven_by,
                "validation": self.validation_of(wf, proven_by),
                **journal_of(ticket, roots=self._roots)}

    def validation_of(self, wf, proven_by: list[str]) -> str | None:
        """The quorum VALIDATION a human-proved class's crossing out of PROVEME names, or None.

        The chokepoint's quorum seat reads ``emit(..., validation=<path>)`` (transitions.py
        ``_quorum_gate``); the asker sends only a fileref, so the gate derives it the way the
        seal derived it: beside the piece the crossings named (``validations_path_for_artifact``,
        ``<dir>/x.md`` -> ``<dir>/validations/x.json``). Measured 2026-11-12: concept-piece
        0682e51ab011, sealed by quorum, was refused at clearance because "the crossing names no
        validation". The first piece whose seal is on disk is named; the seat still reads the
        file and trusts nothing about it it did not read. Any other class or step: None."""
        if wf.here != "PROVEME":
            return None
        from cairn.tools.base import transitions
        if not transitions._is_human_proved(transitions.load_class_def(wf.node_class)):
            return None
        from cairn.tools.validation_store.validation_store import validations_path_for_artifact
        _, repo, commons = self._where()
        for one in proven_by:
            for piece in ([Path(one)] if Path(one).is_absolute() else [repo / one, commons / one]):
                seal = Path(validations_path_for_artifact(str(piece)))
                if seal.is_file():
                    return str(seal)
        return None

    def host_seam_proof(self, ticket) -> list[str]:
        """A HOST-SEAM'S PROOF IS ITS INTENTION'S VERIFY (ticket b5d439fd6608): the tester seals
        it box-local beside the intention (dfe6c1432fc8), and no ``proofs/*.py`` declares it, so
        ``declaring()`` finds nothing and the crossing named no proof at all. The gate names the
        ticket's owning intention, resolved where ``journal_of`` resolves it; rule 2's
        ``standing()`` reads this box's seal of it."""
        _, repo, commons = self._where()
        owning = ticket.doc().get("owning_intention") or ""
        for root in (repo, commons):
            if owning and (root / owning).is_file():
                return [str(root / owning)]
        return [owning] if owning and Path(owning).is_absolute() else []

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
                        out.append(p.relative_to(repo).as_posix() if root == repo else p.as_posix())  # ticket a4892e762b70
        return out

    def hand_of(self, tid: str, asked_by: str) -> str:
        """The hand the crossing is made with: ``asked_by`` when the boat's owner admits it,
        else the holder. An owner that cannot be read leaves the holder's hand, and ``clear``
        refuses the crossing in its own words."""
        from cairn.devices.codemother.machines.clearance import clearance
        tickets, repo, commons = self._where()
        try:
            owner = clearance.boat_owner_of(tid, tickets_dir=str(tickets), cairn_root=str(repo),
                                            commons_root=str(commons))
        except clearance.OwnerUnresolvable:
            return HOLDER
        return asked_by if asked_by and asked_by in owner.hands else HOLDER

    # --- the verb -----------------------------------------------------------

    def queueme(self, envelope: dict) -> dict | None:
        """Answer ``queueme <fileref>``. A deferred gate returns None once the envelope is queued
        and replies by ``reply_to`` when the crossing (and its records' commit) is done; a fileref
        it cannot read is refused now."""
        fileref = (envelope.get("body", {}) or {}).get("fileref")
        if not self._deferred or not isinstance(fileref, str) or not fileref:
            return self._run(envelope)
        with _START:
            fifo = _QUEUES.setdefault(DOOR, queue.Queue())
            fifo.put((self, envelope))
            worker = _WORKERS.get(DOOR)
            if worker is None or not worker.is_alive():
                worker = _WORKERS[DOOR] = threading.Thread(
                    target=_work, args=(fifo,), daemon=True, name="codemother-clearance-gate")
                worker.start()
        return None

    def _settle(self, envelope: dict) -> None:
        """Run one queued crossing and reply to its asker, whatever the crossing does."""
        try:
            got = self._run(envelope)
        except Exception as exc:  # the asker hears every failure; nothing dies silently
            got = {"accepted": False, "verb": VERB, "device": HOLDER, "door": DOOR,
                   "fileref": (envelope.get("body") or {}).get("fileref"),
                   "refusal": type(exc).__name__, "reason": str(exc)}
        self._reply(envelope, got)

    def _reply(self, envelope: dict, got: dict) -> None:
        sender = envelope.get("sender")
        if not sender or not envelope.get("id"):
            return
        from cairn.tools.base import testing_mark
        mark = testing_mark.mark_of(envelope.get("body") or {})
        if mark is not None and mark["kind"] == testing_mark.PERFORM and testing_mark.FIELD not in got:
            got = {**got, testing_mark.FIELD: mark}
        self._participant.post(to=sender, verb="", body=got, reply_to=envelope["id"],
                               why=f"{VERB} reply: the clearance gate ran {got.get('ticket')}")

    def _run(self, envelope: dict) -> dict:
        """The crossing itself: today's body, unchanged, answering the dict the asker reads."""
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
            if crossing.get("validation"):
                kw["validation"] = crossing["validation"]
            crossed["workflow"] = clearance.clear(workflow, to, boat_id=tid, proven_by=proofs, **kw)
            return crossed["workflow"]

        said = {"ticket": tid, "fileref": ticket.fileref, "target": target, "proven_by": proofs,
                "asked_by": asked_by}
        try:
            new = ticket.passed(target, participant=self._participant,
                                history_path=crossing["history_path"],
                                state_path=crossing["state_path"],
                                actor=self.hand_of(tid, asked_by),
                                why=f"{tid} queued at clearance by {asked_by or 'an unnamed sender'}",
                                cross=door, asked_by=asked_by)
        except Exception as exc:  # noqa: BLE001 — a refusal IS the answer, said as data
            if "workflow" in crossed:
                return answer(True, **said, workflow=crossed["workflow"],
                              after_crossing=f"{type(exc).__name__}: {exc}")
            return answer(False, **said, refusal=type(exc).__name__, reason=str(exc))
        return answer(True, **said, workflow=new)


def _work(fifo: queue.Queue) -> None:
    """The gate's one worker: settle each queued crossing in turn, by the gate that queued it."""
    while True:
        gate, envelope = fifo.get()
        try:
            gate._settle(envelope)
        finally:
            fifo.task_done()


def settled() -> None:
    """Block until every crossing queued at clearance in this process has been answered."""
    fifo = _QUEUES.get(DOOR)
    if fifo is not None:
        fifo.join()

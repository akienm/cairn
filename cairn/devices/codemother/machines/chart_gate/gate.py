"""CodeMother's chart-stage gates — a charting ticket asks each stage to queue its fileref.

Outline 9.6 (Akien 2026-11-10, Q#81): each chart stage (orient through validate) and the verdict
is a gate machine that answers ``queueme <fileref>``, and the ticket class queues itself to each
in turn (``Ticket.chart``). Outline 3.3.4.3: the ticket sends only its fileref; the gate
instantiates it on its own side, and that instance processes the pass or the fail.

WHAT THE GATE READS, AND FROM WHERE. Everything off the ticket and the disk, never off the asker:

  - the DRAFT is the plan's ``chart.<stage>`` (``Ticket.drafted``), authored by the builder;
  - the REF is the earlier stage's berth as the ticket recorded it (``Ticket.berth``), under the
    key that stage's door reads (``intent_ref`` for constrain ... ``validate_ref`` for the
    verdict);
  - the CLAIM is the ticket's own id, so every packet a gate writes is attributed to the ticket
    that asked;
  - orient alone also takes the floor (``orient.floor_packet``): its domain and refs where the
    draft leaves them unset, its unknowns appended.

THE GATE JUDGES NOTHING ITSELF. The stage's own door does (each ``write_<stage>``), and its
refusal is the ticket's lack, carried back to design by ``Ticket.failed``. On a pass the berth is
recorded on the ticket (``Ticket.berthed``) and posted to her ``deposit`` verb, so the stage's tree
learns it.

THE VERDICT'S DISPOSITIONS ARE OBSERVED, NEVER AUTHORED. The gate runs each hypothesis's own
instrument and disposes it from that run: confirmed when it exited 0 inside its bound, killed
otherwise. A disposition in the draft is ignored. The criteria are still run by the verdict door
itself, which refuses any outcome its re-run disagrees with. Before this, verdict_ticket.py wrote
every disposition ``confirmed`` — the builder grading its own build.

A GATE ANSWERS LATER, OFF HER REQUEST THREAD (ticket e4714e460e32; outline 3.3.4.3, the gate queues
the ticket and the ticket goes on by itself; 5.5.3.3, Send is asynchronous). The shim holds one
lock per device while a verb runs, so a stage whose instruments ran 31 minutes in ``queueme``
(measured 2026-11-12: b0e65cf8a77e's constrain, 44 tester proofs run one after another) held every
other box's deposit, chart and verdict behind it. A ``deferred`` gate (what ``gates()`` builds for
the shim) checks the fileref, queues the ticket on its own FIFO and returns None, so the shim posts
nothing and lets go. One worker per gate runs the stage and posts the answer to the asker with
``reply_to`` set to the asking envelope's id, which is the reply the asker's ``request`` is
reading for. One worker, because constrain's floor guard is per process: stages at one gate run
one after another. The FIFO and its worker are the STAGE's, one per stage per process, not one per
gate object: her device builds its gates afresh at each lookup, and a worker per object would run
two tickets at once at one gate. A refusal the gate can give without running the stage still answers at once.
A gate built without ``deferred`` answers in the call, as before.

Imports no device (RULE 1): every import below is CodeMother's own machine or a tool.
"""

from __future__ import annotations

import queue
import threading
from pathlib import Path

from cairn.tools.base.diagnostic import DiagnosticBase

HOLDER = "codemother"
VERB = "queueme"
DEPOSIT = "deposit"
_REPO = Path(__file__).resolve().parents[5]

# stage -> (the machine module, its writer, the ref key its door reads, the stage whose berth fills it)
STAGES = {
    "orient": ("orient", "write_packet", None, None),
    "constrain": ("constrain", "write_constrain", "intent_ref", "orient"),
    "survey": ("survey", "write_survey", "constrain_ref", "constrain"),
    "decompose": ("decompose", "write_decompose", "survey_ref", "survey"),
    "triage": ("triage", "write_triage", "decompose_ref", "decompose"),
    "hypothesize": ("hypothesize", "write_hypothesize", "triage_ref", "triage"),
    "validate": ("validate", "write_validate", "hypothesize_ref", "hypothesize"),
    "verdict": ("verdict", "write_verdict", "validate_ref", "validate"),
}


# stage -> its one FIFO and the one worker draining it, for this process
_QUEUES: dict[str, queue.Queue] = {}
_WORKERS: dict[str, threading.Thread] = {}
_START = threading.Lock()


def _door(stage: str):
    import importlib
    module, writer, _, _ = STAGES[stage]
    return getattr(importlib.import_module(f"cairn.devices.codemother.machines.{module}.{module}"),
                   writer)


class StageGate(DiagnosticBase):
    """The gate for one chart stage.

    ``roots`` is ``{repo, commons, instance}`` (a proof's scratch world) or None for the live one;
    ``packets_dir`` is where the door berths, None for the stage doors' own INSTANCE_DIR;
    ``runner`` is the verdict's instrument runner, None for the door's own (a proof injects one so
    no instrument forks)."""

    def __init__(self, stage: str, *, participant=None, roots=None, packets_dir=None,
                 runner=None, deferred: bool = False) -> None:
        super().__init__()
        if stage not in STAGES:
            raise ValueError(f"{stage!r} is not a chart stage: {', '.join(STAGES)}")
        if participant is None:
            from cairn.devices.codemother.machines.watchme.gate import Voice
            participant = Voice()
        self.stage = stage
        self._participant = participant
        self._roots = roots
        self._packets_dir = packets_dir
        self._runner = runner
        self._deferred = deferred
        if roots is not None:
            self.set_diagnostic_roots(roots)

    def declared_verbs(self) -> dict:
        return {VERB: self.queueme}

    def _tickets(self) -> Path:
        from cairn.tools.base import ticket_file
        if self._roots is not None:
            return Path(self._roots["commons"]) / "tickets"
        return Path(ticket_file._TICKETS)

    # --- what the gate builds from the ticket ------------------------------

    def packet_of(self, ticket) -> tuple[dict | None, list[dict]]:
        """The packet this stage's door is handed, or ``(None, lacks)``."""
        _, _, ref_key, prev = STAGES[self.stage]
        draft = ticket.drafted(self.stage)
        lacks: list[dict] = []
        if not isinstance(draft, dict):
            lacks.append({"kind": self.stage, "why": f"the plan carries no chart.{self.stage} "
                                                    "draft for this stage's gate to write"})
        ref = ticket.berth(prev) if prev else None
        if prev and not ref:
            lacks.append({"kind": self.stage, "why": f"no {prev}_berth is recorded on the ticket, "
                                                    f"so {self.stage} has no {ref_key} to read"})
        if lacks:
            return None, lacks
        packet = dict(draft)
        packet["ticket"] = ticket.id
        if ref_key:
            packet[ref_key] = ref
        if self.stage == "orient":
            from cairn.devices.codemother.machines.orient.orient import floor_packet
            floor = floor_packet(str(packet.get("request") or ""))
            for key in ("domain", "refs"):
                if packet.get(key) is None and floor.get(key) is not None:
                    packet[key] = floor[key]
            packet["unknowns"] = list(floor.get("unknowns") or []) + list(packet.get("unknowns") or [])
        return packet, []

    def _dispose(self, packet: dict) -> dict:
        """The packet carrying the verdict's dispositions, each from a run of its hypothesis's
        OWN instrument (the hypothesize berth, read through the validate berth's
        ``hypothesize_ref``). The door's readings are one per CRITERION, and it refuses a criterion
        whose re-run disagrees, so a disposition read off them could never be a kill on a verdict
        the door would berth: the hypothesis's instrument is run here instead, once per distinct
        command, by the same runner the door is handed."""
        import json
        from cairn.devices.codemother.machines.verdict import verdict as V
        runner = self._runner or V.run_instrument
        validate = json.loads(Path(packet["validate_ref"]).read_text(encoding="utf-8"))
        hyps = json.loads(Path(validate["hypothesize_ref"]).read_text(encoding="utf-8")
                          ).get("hypotheses") or []
        runs: dict[str, dict] = {}
        dispositions, lacks = [], []
        for h in hyps:
            command = V.extract_command(h.get("instrument"), V.CAIRN_ROOT)
            if command is None:
                lacks.append(f"hypothesis {h.get('piece')!r}: its instrument "
                             f"{h.get('instrument')!r} carries no runnable command")
                continue
            if command not in runs:
                runs[command] = runner(command, timeout_s=600, cwd=V.CAIRN_ROOT)
            run = runs[command]
            met = not run.get("timed_out") and run.get("exit") == 0
            dispositions.append({
                "piece": h.get("piece"), "expect": h.get("expect"),
                "disposition": "confirmed" if met else "killed",
                "by": f"{command} exited {run.get('exit')}"
                      + (" (timed out)" if run.get("timed_out") else "")})
        if lacks:
            raise ValueError("; ".join(lacks))
        return dict(packet, dispositions=dispositions)

    # --- the verb -----------------------------------------------------------

    def _answer(self, accepted: bool, **more) -> dict:
        return {"accepted": accepted, "verb": VERB, "device": HOLDER, "door": self.stage,
                "stage": self.stage, **more}

    def queueme(self, envelope: dict) -> dict | None:
        """Answer ``queueme <fileref>``. A deferred gate returns None once the ticket is queued
        and replies by ``reply_to`` when its stage has run; an early refusal is returned now."""
        body = envelope.get("body", {}) or {}
        fileref = body.get("fileref")
        if not isinstance(fileref, str) or not fileref:
            return self._answer(False, reason="queueme needs a fileref: the ticket's plan path or "
                                              "id, and nothing else (outline 3.3.4.3)")
        from cairn.machines.ticket.ticket import Ticket
        try:
            ticket = Ticket.at(fileref, tickets_dir=self._tickets(), roots=self._roots)
        except (OSError, ValueError) as exc:
            return self._answer(False, fileref=fileref, reason=f"{type(exc).__name__}: {exc}")
        if not self._deferred:
            return self._run(envelope, ticket)
        with _START:
            fifo = _QUEUES.setdefault(self.stage, queue.Queue())
            fifo.put((self, envelope, ticket))
            worker = _WORKERS.get(self.stage)
            if worker is None or not worker.is_alive():
                worker = _WORKERS[self.stage] = threading.Thread(
                    target=_work, args=(fifo,), daemon=True, name=f"codemother-{self.stage}-gate")
                worker.start()
        return None

    def _settle(self, envelope: dict, ticket) -> None:
        """Run one queued ticket's stage and reply to its asker, whatever the stage does."""
        try:
            try:
                got = self._run(envelope, ticket)
            except Exception as exc:  # the asker hears every failure; nothing dies silently
                got = self._fail(envelope, ticket,
                                 [{"kind": self.stage, "why": f"{type(exc).__name__}: {exc}"}])
            self._reply(envelope, got)
        except Exception as exc:
            self._reply(envelope, self._answer(
                True, ticket=getattr(ticket, "id", None), passed=False,
                lacks=[{"kind": self.stage, "why": f"{type(exc).__name__}: {exc}"}]))

    def _reply(self, envelope: dict, got: dict) -> None:
        sender = envelope.get("sender")
        if not sender or not envelope.get("id"):
            return
        from cairn.tools.base import testing_mark
        mark = testing_mark.mark_of(envelope.get("body") or {})
        if mark is not None and mark["kind"] == testing_mark.PERFORM and testing_mark.FIELD not in got:
            got = {**got, testing_mark.FIELD: mark}
        self._participant.post(to=sender, verb="", body=got, reply_to=envelope["id"],
                               why=f"{VERB} reply: the {self.stage} gate ran {got.get('ticket')}")

    def _said(self, envelope: dict, ticket) -> dict:
        return {"ticket": ticket.id, "fileref": ticket.fileref,
                "asked_by": envelope.get("sender") or ""}

    def _fail(self, envelope: dict, ticket, lacks: list[dict]) -> dict:
        from cairn.devices.codemother.machines.clearance.gate import journal_of
        journal = journal_of(ticket, roots=self._roots)
        got = ticket.failed(lacks, participant=self._participant, actor=HOLDER,
                            why=f"{ticket.id} failed at the {self.stage} gate", **journal)
        return self._answer(True, **self._said(envelope, ticket), passed=False, lacks=lacks,
                            workflow=got.get("workflow"), trouble=got.get("trouble"))

    def _run(self, envelope: dict, ticket) -> dict:
        """The stage itself: build the packet, hand it to the door, record the pass or the fail."""
        tid = ticket.id
        packet, lacks = self.packet_of(ticket)
        berth = None
        if packet is not None:
            kw = {} if self._packets_dir is None else {"instance_dir": str(self._packets_dir)}
            try:
                if self.stage == "verdict":
                    packet = self._dispose(packet)
                    if self._runner is not None:
                        kw["runner"] = self._runner
                berth = _door(self.stage)(packet, **kw)
            except (RuntimeError, ValueError, OSError, KeyError) as exc:
                lacks = [{"kind": self.stage, "why": f"{type(exc).__name__}: {exc}"}]
        if lacks:
            return self._fail(envelope, ticket, lacks)
        ticket.berthed(self.stage, berth, why=f"{tid}: the {self.stage} gate berthed {berth}")
        self._participant.post(to=HOLDER, verb=DEPOSIT, body={"berth": str(berth)},
                               why=f"{tid}: the {self.stage} gate's berth, for its tree")
        return self._answer(True, **self._said(envelope, ticket), passed=True, berth=str(berth))


def _work(fifo: queue.Queue) -> None:
    """A stage's one worker: settle each queued ticket in turn, by the gate that queued it."""
    while True:
        gate, envelope, ticket = fifo.get()
        try:
            gate._settle(envelope, ticket)
        finally:
            fifo.task_done()


def settled(stage: str) -> None:
    """Block until every ticket queued at ``stage`` in this process has been answered."""
    fifo = _QUEUES.get(stage)
    if fifo is not None:
        fifo.join()


def gates(*, participant=None) -> dict:
    """``{stage: StageGate}`` for every chart stage and the verdict — what the shim registers.
    Each is deferred: it answers by ``reply_to`` from its own worker, never under the shim's lock."""
    return {stage: StageGate(stage, participant=participant, deferred=True) for stage in STAGES}

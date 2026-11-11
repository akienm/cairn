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

Imports no device (RULE 1): every import below is CodeMother's own machine or a tool.
"""

from __future__ import annotations

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
                 runner=None) -> None:
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

    def queueme(self, envelope: dict) -> dict:
        def answer(accepted: bool, **more) -> dict:
            return {"accepted": accepted, "verb": VERB, "device": HOLDER, "door": self.stage,
                    "stage": self.stage, **more}

        body = envelope.get("body", {}) or {}
        asked_by = envelope.get("sender") or ""
        fileref = body.get("fileref")
        if not isinstance(fileref, str) or not fileref:
            return answer(False, reason="queueme needs a fileref: the ticket's plan path or id, "
                                        "and nothing else (outline 3.3.4.3)")
        from cairn.machines.ticket.ticket import Ticket
        try:
            ticket = Ticket.at(fileref, tickets_dir=self._tickets(), roots=self._roots)
        except (OSError, ValueError) as exc:
            return answer(False, fileref=fileref, reason=f"{type(exc).__name__}: {exc}")
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
        said = {"ticket": tid, "fileref": ticket.fileref, "asked_by": asked_by}
        if lacks:
            from cairn.devices.codemother.machines.clearance.gate import journal_of
            journal = journal_of(ticket, roots=self._roots)
            got = ticket.failed(lacks, participant=self._participant, actor=HOLDER,
                                why=f"{tid} failed at the {self.stage} gate", **journal)
            return answer(True, **said, passed=False, lacks=lacks, workflow=got.get("workflow"),
                          design_queued=got.get("queued"))
        ticket.berthed(self.stage, berth, why=f"{tid}: the {self.stage} gate berthed {berth}")
        self._participant.post(to=HOLDER, verb=DEPOSIT, body={"berth": str(berth)},
                               why=f"{tid}: the {self.stage} gate's berth, for its tree")
        return answer(True, **said, passed=True, berth=str(berth))


def gates(*, participant=None) -> dict:
    """``{stage: StageGate}`` for every chart stage and the verdict — what the shim registers."""
    return {stage: StageGate(stage, participant=participant) for stage in STAGES}

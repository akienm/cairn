"""Ticket — the abstract ticket class: a ticket queues itself at a gate (ticket 152d76785229).

Akien, 2026-11-10 (Q#80/Q#81 answers, outline 3.3.1-3.3.4.3 and 9.6): a ticket is a class and
a machine, never a device. To cross a gate it sends its fileref to
``devices/codemother/0/machines/<gate>/queueme``; the gate instantiates the ticket on its own
side, and that instance processes the pass or the fail. On a pass the ticket goes to the next
step and alerts the probes watching the gate. On a fail it waits in the trouble lane CC and Akien
read: one trouble naming the gate and every lack, cleared when that gate later passes it. Design
is CC and Akien until the outline is implemented (outline 3.3.4, Q#85), so nothing posts to a
design verb no machine answers (ticket 794835a34ec9). Self-queuing belongs to the abstract class,
so it is written once, here.

WHAT THE CLASS DOES NOT DO. It does not judge — the gate does (Law 6). It does not dial the bus —
the caller hands it a participant (anything with ``request`` and ``post``), so the ticket has no
bus address of its own (a thing with one would be a device, 3.3.3). It imports no device and not
the harbor's clearance (RULE 1): the FIXME write ``clearance._send_to_fixme`` does is the same
shape here, written through ``ticket_file``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from cairn.tools.base.diagnostic import DiagnosticBase

GATE_HOLDER = "codemother"
HARBOR = "harbor_master"

# The chart stages in the order a ticket queues itself at them (outline 9.6, ticket
# cd8a1de6139c). Each is a CodeMother gate answering ``machines/<stage>/queueme``. The verdict
# is a gate too, but not one of these: it is queued after the build, not as part of the chart.
CHART = ("orient", "constrain", "survey", "decompose", "triage", "hypothesize", "validate")
VERDICT = "verdict"

_CURSOR = re.compile(r"\[([A-Z]+)")


def _before_repair(workflow: str) -> bool:
    """Does ``workflow`` stand before the anchor of its FIXME repair summons, so FIXME cannot be
    entered (``transitions.emit``'s rule, read from the same registered workflow)?"""
    from cairn.tools.base.transitions import load_class_def
    from cairn.tools.base.workflow_grammar import _registered_workflow, parse_workflow
    wf = parse_workflow(workflow)
    anchor = _registered_workflow(load_class_def(wf.node_class), wf.version
                                  ).get("repair_summons", {}).get("FIXME")
    return bool(anchor) and "FIXME" not in wf.path and anchor in wf.path \
        and wf.cursor < wf.path.index(anchor)


def _refused_identity(tid: str, gate: str) -> str:
    """The trouble a refusal at ``gate`` raises on ticket ``tid``, and that gate's pass clears."""
    return f"ticket-refused-{tid}-at-{gate}"


def _step(workflow: str) -> str:
    m = _CURSOR.search(workflow or "")
    return m.group(1) if m else ""


class Ticket(DiagnosticBase):
    """One ticket, read and written through its own three files (plan, state, log).

    It reaches the diagnostic mixin like every class, so the trouble a waiting ticket throws is
    its own (filed under this component, ``ticket``), raised with the base's ``raise_trouble``.
    ``roots`` points that trail at another world — a proof's scratch tree."""

    def __init__(self, plan: str | Path, *, roots=None) -> None:
        super().__init__()
        self._plan = Path(plan)
        if roots is not None:
            self.set_diagnostic_roots(roots)

    @classmethod
    def at(cls, ref: str | Path, *, tickets_dir: str | Path | None = None, roots=None) -> "Ticket":
        """The ticket a fileref names: an existing plan path, or an id the store resolves."""
        p = Path(ref)
        if p.is_file():
            return cls(p, roots=roots)
        from cairn.tools.base.ticket_file import find_ticket
        found = find_ticket(str(ref), Path(tickets_dir) if tickets_dir is not None else None)
        if found is None:
            raise FileNotFoundError(f"no ticket resolves from {str(ref)!r}")
        return cls(found, roots=roots)

    @property
    def fileref(self) -> str:
        return str(self._plan)

    def doc(self) -> dict:
        from cairn.tools.base.ticket_file import read_ticket
        return read_ticket(self._plan)

    @property
    def id(self) -> str:
        return str(self.doc().get("id") or "")

    @property
    def workflow(self) -> str:
        return str(self.doc().get("workflow_and_state") or "")

    def _component(self) -> str:
        owning = self.doc().get("owning_intention") or ""
        return str(Path(owning).parent) if owning else ""

    def _write(self, updates: dict, *, why: str) -> None:
        """Put ``updates`` on the ticket: into its state file when one stands, else its plan."""
        from cairn.tools.base import ticket_file as tf
        sp = tf.state_path(self._plan)
        if sp.is_file():
            state = json.loads(sp.read_text(encoding="utf-8"))
            state.update(updates)
            tf.write_state(self._plan, state, why=why, verb="phase")
            return
        doc = json.loads(self._plan.read_text(encoding="utf-8"))
        doc.update(updates)
        tf.rewrite_ticket(self._plan, doc, why=why, verb="phase")

    # --- the chart, carried on the ticket (outline 3.3.4.3: its life is data) ---------------

    def draft(self, stage: str, packet: dict, *, why: str) -> None:
        """Put ``packet``, the draft of chart stage ``stage``, on the plan under ``chart``.

        The draft is authored, so it lands in the plan; the gate reads it from there, because
        the ticket sends the gate only its fileref. A stage outside CHART and the verdict is
        refused before anything is written."""
        if stage not in CHART + (VERDICT,):
            raise ValueError(f"{stage!r} is not a chart stage: CHART is {', '.join(CHART)}, "
                             f"and {VERDICT} after the build")
        from cairn.tools.base import ticket_file as tf
        doc = json.loads(self._plan.read_text(encoding="utf-8"))
        chart = dict(doc.get("chart") or {})
        chart[stage] = packet
        doc["chart"] = chart
        tf.rewrite_ticket(self._plan, doc, why=why, verb="cast")

    def drafted(self, stage: str):
        """The draft of ``stage`` on the plan, or None."""
        return (self.doc().get("chart") or {}).get(stage)

    def berthed(self, stage: str, berth: str, *, why: str) -> None:
        """Record ``berth``, the packet a stage's gate wrote, as ``<stage>_berth`` in the state's
        ``chart_claim`` — the shape the claim already carries for ``validate_berth`` and
        ``verdict_berth`` — keeping every earlier stage's. A claim still the empty string a cast
        leaves becomes a dict."""
        if stage not in CHART + (VERDICT,):
            raise ValueError(f"{stage!r} is not a chart stage: CHART is {', '.join(CHART)}, "
                             f"and {VERDICT} after the build")
        claim = self.doc().get("chart_claim")
        merged = dict(claim) if isinstance(claim, dict) else {}
        merged[f"{stage}_berth"] = str(berth)
        self._write({"chart_claim": merged}, why=why)

    def berth(self, stage: str):
        """The berth ``stage``'s gate recorded on this ticket, or None."""
        claim = self.doc().get("chart_claim")
        return claim.get(f"{stage}_berth") if isinstance(claim, dict) else None

    def chart(self, *, participant, timeout: float = 30.0, stages=CHART) -> dict:
        """Queue this ticket at each chart stage in turn (outline 9.6), stopping at the first
        stage whose gate does not pass it: one not queued (a trouble is already raised by
        ``queueme``) or one whose reply says ``passed`` is not true (the gate has already
        refused the ticket into the trouble lane)."""
        done: list[dict] = []
        for stage in stages:
            got = self.queueme(stage, participant=participant, timeout=timeout)
            passed = got["queued"] and got["reply"].get("passed") is True
            done.append({"stage": stage, "queued": got["queued"], "passed": passed,
                         "reply": got["reply"]})
            if not passed:
                return {"charted": False, "stopped_at": stage, "stages": done}
        return {"charted": True, "stopped_at": None, "stages": done}

    def queueme(self, gate: str, *, participant, timeout: float = 30.0) -> dict:
        """Ask the gate's holder to queue this ticket at ``gate``; log the exchange.

        A bounce or a timeout means no handler answered: the ticket raises a trouble and waits
        (returns ``queued`` False) — it never retries on its own and never goes quiet."""
        tid = self.id
        verb = f"machines/{gate}/queueme"
        sent = {"fileref": self.fileref}
        try:
            reply = participant.request(to=GATE_HOLDER, verb=verb, body=sent, timeout=timeout,
                                        why=f"ticket {tid} asks to be queued at {gate}")
            body = dict((reply or {}).get("body") or {})
        except TimeoutError as exc:
            body = {"error": str(exc)}
        queued = body.get("accepted") is True and not body.get("is_bounce")
        from cairn.tools.base.ticket_log import append_log
        append_log(self._plan, "gate_dialog",
                   {"gate": gate, "verb": verb, "sent": sent, "reply": body, "queued": queued},
                   actor=tid or "ticket", why=f"{tid} queueme at {gate}: queued={queued}")
        trouble = None
        identity = f"ticket-unqueued-{tid}-at-{gate}"
        if not queued:
            trouble = identity
            self.raise_trouble(
                trouble, why=f"ticket {tid} asked {GATE_HOLDER} to queue it at {gate} and no "
                             "handler took it; the ticket waits",
                detail={"fileref": self.fileref, "gate": gate, "reply": body})
        else:
            if self._stands_raised(identity):
                # The ticket's own raise, cleared by the ticket once the gate takes it
                # (41a5bae3d01b); nothing standing sends nothing, so a taken ask writes no clear.
                self.clear_trouble(identity, by=tid or "ticket",
                                   what_changed=f"queued at {gate}: the gate took it")
            refused = _refused_identity(tid, gate)
            if body.get("passed") is True and self._stands_raised(refused):
                # The refusal this gate made stands until this gate passes the ticket
                # (794835a34ec9); a reply that takes the ticket but does not pass it leaves it.
                self.clear_trouble(refused, by=tid or "ticket",
                                   what_changed=f"passed at {gate}: the refusal is answered")
        return {"queued": queued, "gate": gate, "reply": body, "trouble": trouble}

    def _stands_raised(self, identity: str) -> bool:
        """Does ``identity`` stand raised on this ticket's own trail? The newest raise or clear
        record naming it decides (names sort by time); none is False. Reads only."""
        trail = self.diagnostic_trail()
        if trail is None or not Path(trail).is_dir():
            return False
        names = sorted((n.name for n in Path(trail).iterdir()
                        if n.name.endswith((".raise_trouble.json", ".clear_trouble.json"))),
                       reverse=True)
        for name in names:
            try:
                rec = json.loads((Path(trail) / name).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if rec.get("pointer") == identity:
                return name.endswith(".raise_trouble.json")
        return False

    def _tell_harbor(self, participant, *, frm: str, to: str, direction: str) -> None:
        participant.post(to=HARBOR, verb="crossing",
                         why=f"ticket {self.id} crossed {frm} -> {to}",
                         body={"ticket": self.id, "component": self._component(),
                               "from": frm, "to": to, "direction": direction})

    def passed(self, target: str, *, participant, watchers=(), history_path, state_path,
               actor: str, why: str, cross=None, **journal_extra) -> str:
        """The gate passed this ticket: cross to ``target`` through the chokepoint, write the
        cursor, tell the harbor, and tell each watcher the gate supplies what step is next.
        ``journal_extra`` rides to emit (a gate into a REST carries its witness there).

        ``cross`` is the door the crossing rides, when the gate has one of its own that records
        the crossing itself (the clearance gate's ``clear`` wraps emit, ticket 0be964512fb0):
        the crossing then rides that door exactly once and never a second time through emit,
        and the cursor written is the one the door returned. None is emit."""
        if cross is None:
            from cairn.tools.base.transitions import emit as cross
        old = self.workflow
        new = cross(old, target, history_path=history_path, state_path=state_path,
                    ticket=self.id, actor=actor, why=why, **journal_extra)
        self._write({"workflow_and_state": new}, why=f"{self.id}: passed into {target} — {why}")
        self._tell_harbor(participant, frm=_step(old), to=target, direction="forward")
        for w in watchers:
            participant.post(to=w, verb="next_step", why=f"ticket {self.id} is at {target}",
                             body={"ticket": self.id, "fileref": self.fileref, "step": target})
        return new

    def failed(self, lacks: list[dict], *, participant, history_path, state_path, actor: str,
               why: str, gate: str | None = None) -> dict:
        """The gate failed this ticket: kick back to FIXME carrying every lack and tell the harbor,
        then wait in the trouble lane — one trouble naming ``gate`` (else the first lack's kind)
        and every lack. Nothing is asked of any verb: design is CC and Akien (outline 3.3.4)."""
        from cairn.tools.base.transitions import emit
        old = self.workflow
        missing = [f"[{one['kind']}] {one['why']}" for one in lacks]
        fixme = [{"n": i, "kind": one["kind"], "missing": one["why"]}
                 for i, one in enumerate(lacks, 1)]
        gate = gate or (lacks[0]["kind"] if lacks else "unnamed")
        if _before_repair(old) or _step(old) == "FIXME":
            # A chart stage fails a ticket still at TICKETME, and FIXME is anchored before
            # BUILDME: there is no build to kick back from, so the cursor stands and the lacks land.
            # A ticket already AT FIXME is where the kick would send it: FIXME -> FIXME is no
            # crossing (emit refuses it as a no-op), so the cursor stands there too.
            self._write({"fixme": fixme},
                        why=f"{self.id}: failed at {_step(old)} — {len(lacks)} lack(s): {why}")
            new = old
        else:
            new = emit(old, "FIXME", history_path=history_path, state_path=state_path,
                       write_fixme=False, ticket=self.id, actor=actor, missing=missing, why=why)
            self._write({"workflow_and_state": new, "fixme": fixme},
                        why=f"{self.id}: failed at {_step(old)} — {len(lacks)} lack(s): {why}")
            self._tell_harbor(participant, frm=_step(old), to="FIXME", direction="back")
        identity = _refused_identity(self.id, gate)
        self.raise_trouble(
            identity, why=f"ticket {self.id} was refused at {gate} with {len(lacks)} lack(s): "
                          + "; ".join(missing) + " — it waits for CC and Akien",
            detail={"fileref": self.fileref, "gate": gate, "lacks": lacks, "workflow": new})
        return {"queued": False, "gate": gate, "trouble": identity, "workflow": new}

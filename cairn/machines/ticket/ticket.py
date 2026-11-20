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
import time
from pathlib import Path

from cairn.tools.base.diagnostic import DiagnosticBase

GATE_HOLDER = "codemother"
HARBOR = "harbor_master"

# The chart stages in the order a ticket queues itself at them (outline 9.6, ticket
# cd8a1de6139c). Each is a CodeMother gate answering ``machines/<stage>/queueme``. The verdict
# is a gate too, but not one of these: it is queued after the build, not as part of the chart.
CHART = ("orient", "constrain", "survey", "decompose", "triage", "hypothesize", "validate")
VERDICT = "verdict"

# How long an asker reads its own record for a chart or verdict stage after the gate's reply
# timed out (ticket 0bcb816d6e9c). A deferred gate queues the ticket at once and answers by
# reply_to when the stage ends (e4714e460e32), so a slow stage replies after its asker gave up
# while it still berths. Measured 2026-11-12: one constrain ran 1858 s.
STAGE_BUDGET_S = 3600.0
_SETTLE_POLL_S = 0.2

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


class CrossingCommitError(RuntimeError):
    """A crossing landed but its records could not be committed. Loud, never swallowed (Law 7):
    a crossing left only as dirt on one disk is the defect ticket 79875eb17ac2 closes."""


def commit_crossing_records(history_path, state_path, why: str) -> str | None:
    """Commit the crossed component's ``history.json`` and ``state.json`` and nothing else.

    PUBLISHED (ticket 79875eb17ac2): the ticket machine's one commit step for a crossing, called
    at the end of ``Ticket.passed`` and ``Ticket.failed`` and by the other doors that emit a
    crossing of their own (sail.cross, the clearance refusal). Measured 2026-11-19: five
    crossings sat as uncommitted dirt because only close.sh committed them. Path-limited, so
    another ticket's dirt in the same tree is never staged. It lives here and not in
    ``projector.append_entry``, which scratch proofs call and which stays git-free.

    Returns the new commit's hash, or None when there was nothing to commit or the records sit
    in no git work tree (a scratch path). A failed commit raises ``CrossingCommitError``."""
    import subprocess
    paths = [Path(p) for p in (history_path, state_path) if p and Path(p).exists()]
    if not paths:
        return None

    def git(*args):
        return subprocess.run(["git", "-C", str(paths[0].parent), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace")

    if git("rev-parse", "--show-toplevel").returncode != 0:
        return None
    rel = [str(p.resolve()) for p in paths]
    added = git("add", "--", *rel)
    if added.returncode != 0:
        raise CrossingCommitError(f"git add of {rel} failed: {added.stderr.strip()}")
    if git("diff", "--cached", "--quiet", "--", *rel).returncode == 0:
        return None
    done = git("commit", "-q", "-m", f"crossing records: {why}", "--", *rel)
    if done.returncode != 0:
        raise CrossingCommitError(
            f"git commit of {rel} failed: {(done.stdout + done.stderr).strip()}")
    return git("rev-parse", "HEAD").stdout.strip()


class Ticket(DiagnosticBase):
    """One ticket, read and written through its own three files (plan, state, log).

    It reaches the diagnostic mixin like every class, so the trouble a waiting ticket throws is
    its own (filed under this component, ``ticket``), raised with the base's ``raise_trouble``.
    ``roots`` points that trail at another world — a proof's scratch tree. ``settle`` is how
    long ``queueme`` reads this ticket's own record for a chart or verdict stage once the gate's
    reply timed out (0, the default, reads nothing and the timeout stands as unqueued)."""

    def __init__(self, plan: str | Path, *, roots=None, settle: float = 0.0) -> None:
        super().__init__()
        self._plan = Path(plan)
        self._settle = float(settle)
        if roots is not None:
            self.set_diagnostic_roots(roots)

    @classmethod
    def at(cls, ref: str | Path, *, tickets_dir: str | Path | None = None, roots=None,
           settle: float = 0.0) -> "Ticket":
        """The ticket a fileref names: an existing plan path, or an id the store resolves."""
        p = Path(ref)
        if p.is_file():
            return cls(p, roots=roots, settle=settle)
        from cairn.tools.base.ticket_file import find_ticket
        found = find_ticket(str(ref), Path(tickets_dir) if tickets_dir is not None else None)
        if found is None:
            raise FileNotFoundError(f"no ticket resolves from {str(ref)!r}")
        return cls(found, roots=roots, settle=settle)

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

        A bounce means no handler answered: the ticket raises a trouble and waits (returns
        ``queued`` False) — it never retries on its own and never goes quiet. A holder that
        answers ``accepted`` False raises the same trouble, its why naming the refusal in the same
        words every time and the holder's reason in the detail (ticket 239740d9db04). A timeout at a
        chart or verdict gate is not yet that: a deferred gate takes the ticket and answers when
        the stage ends (e4714e460e32), so the ticket reads its own record for up to ``settle``
        seconds (outline 3.3.4.3, its life is data on disk). The berth the gate writes passes it;
        the refusal the gate raises fails it, carrying the lacks the gate put on the plan; only
        silence through the whole budget is unqueued (ticket 0bcb816d6e9c)."""
        tid = self.id
        verb = f"machines/{gate}/queueme"
        # The id, not this box's path: the gate may sit on another box, which resolves the id
        # from its own commons (ticket 8bb8b4729f17). A doc with no id still sends its path.
        sent = {"fileref": tid or self.fileref}
        settle = self._settle if gate in CHART + (VERDICT,) else 0.0
        before = (self.berth(gate), self._newest_raise(_refused_identity(tid, gate))) \
            if settle > 0 else None
        try:
            reply = participant.request(to=GATE_HOLDER, verb=verb, body=sent, timeout=timeout,
                                        why=f"ticket {tid} asks to be queued at {gate}")
            body = dict((reply or {}).get("body") or {})
        except TimeoutError as exc:
            body = {"error": str(exc)}
            if before is not None:
                body = self._settled(gate, before, settle) or body
        queued = body.get("accepted") is True and not body.get("is_bounce")
        from cairn.tools.base.ticket_log import append_log
        append_log(self._plan, "gate_dialog",
                   {"gate": gate, "verb": verb, "sent": sent, "reply": body, "queued": queued},
                   actor=tid or "ticket", why=f"{tid} queueme at {gate}: queued={queued}")
        trouble = None
        identity = f"ticket-unqueued-{tid}-at-{gate}"
        if not queued:
            trouble = identity
            # A REFUSAL IS NOT A MISSING HANDLER (ticket 239740d9db04). Measured 2026-11-16: all
            # 12 occurrences of ticket-unqueued-*-at-clearance were the gate answering
            # accepted False with its reason, and every one was recorded as "no handler took it"
            # (Law 7). The holder's own answer is said as a refusal; a bounce or silence is still
            # no handler. The why is the same words every time and the reason rides in the
            # detail (outline 3.4.3.2.3). The identity stays, so a later take still clears it
            # (41a5bae3d01b).
            reason = str(body.get("reason") or "").strip()
            answered = (body.get("accepted") is False and not body.get("is_bounce")
                        and "error" not in body and bool(reason))
            said = (f"{GATE_HOLDER} refused it (its reason is in the detail)" if answered
                    else "no handler took it")
            self.raise_trouble(
                trouble, why=f"ticket {tid} asked {GATE_HOLDER} to queue it at {gate} and "
                             f"{said}; the ticket waits",
                detail={"fileref": self.fileref, "gate": gate, "reply": body,
                        **({"reason": reason} if answered else {})})
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

    def _settled(self, gate: str, before: tuple, settle: float) -> dict | None:
        """Read this ticket's record for ``gate`` until it moves past ``before`` (the berth and
        the newest refusal raise noted before asking) or ``settle`` seconds pass. A new berth is
        a passed reply, a new refusal a refused one with the plan's lacks; None is silence."""
        berth0, raise0 = before
        end = time.monotonic() + settle
        while True:
            berth = self.berth(gate)
            if berth and berth != berth0:
                return {"accepted": True, "passed": True, "berth": berth, "ticket": self.id,
                        "stage": gate, "settled_by": "berth"}
            newest = self._newest_raise(_refused_identity(self.id, gate))
            if newest and newest != raise0:
                lacks = [{"kind": one.get("kind"), "why": one.get("missing")}
                         for one in self.doc().get("fixme") or []]
                return {"accepted": True, "passed": False, "lacks": lacks, "ticket": self.id,
                        "stage": gate, "settled_by": "refusal"}
            if time.monotonic() >= end:
                return None
            time.sleep(_SETTLE_POLL_S)

    def _newest_raise(self, identity: str) -> str | None:
        """The trail name of the newest raise record naming ``identity``, or None. Reads only."""
        trail = self.diagnostic_trail()
        if trail is None or not Path(trail).is_dir():
            return None
        for name in sorted((n.name for n in Path(trail).iterdir()
                            if n.name.endswith(".raise_trouble.json")), reverse=True):
            try:
                rec = json.loads((Path(trail) / name).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if rec.get("pointer") == identity:
                return name
        return None

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

    def _commit_commons_state(self, why: str) -> str | None:
        """Commit this ticket's own commons ``.state.json`` and nothing else (ticket db1475029939).

        The crossing rewrites the state file in the commons; ``commit_crossing_records`` commits
        only the component's two files, so this one sat as dirt. Path-limited, so another
        ticket's dirt in the same work tree is never staged. A ticket in no git work tree (a
        scratch commons) returns None; a failed commit raises ``CrossingCommitError``."""
        import subprocess
        from cairn.tools.base import ticket_file as tf
        sp = tf.state_path(self._plan)
        if not sp.is_file():
            return None

        def git(*args):
            return subprocess.run(["git", "-C", str(sp.parent), *args], capture_output=True,
                                  text=True, encoding="utf-8", errors="replace")

        if git("rev-parse", "--show-toplevel").returncode != 0:
            return None
        rel = str(sp.resolve())
        if git("ls-files", "--error-unmatch", "--", rel).returncode != 0:
            return None  # an untracked state is a new ticket's, committed by its cast
        if git("diff", "--quiet", "--", rel).returncode == 0:
            return None
        done = git("commit", "-q", "-m", f"crossing state: {why}", "--only", "--", rel)
        if done.returncode != 0:
            raise CrossingCommitError(
                f"git commit of {rel} failed: {(done.stdout + done.stderr).strip()}")
        return git("rev-parse", "HEAD").stdout.strip()

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
        commit_crossing_records(history_path, state_path, f"{self.id} passed into {target}")
        self._commit_commons_state(f"{self.id} passed into {target}")
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
            commit_crossing_records(history_path, state_path,
                                    f"{self.id} failed at {_step(old)}, sent to FIXME")
            self._commit_commons_state(f"{self.id} failed at {_step(old)}, sent to FIXME")
        identity = _refused_identity(self.id, gate)
        self.raise_trouble(
            identity, why=f"ticket {self.id} was refused at {gate} with {len(lacks)} lack(s): "
                          + "; ".join(missing) + " — it waits for CC and Akien",
            detail={"fileref": self.fileref, "gate": gate, "lacks": lacks, "workflow": new})
        return {"queued": False, "gate": gate, "trouble": identity, "workflow": new}


# A TERMINAL TICKET CLEARS ITS OWN TICKET TROUBLES (ticket c1664a4eb3ad). A ticket's unqueued and
# refused troubles clear when a later ask at the same gate is taken or passed (41a5bae3d01b,
# 794835a34ec9). Measured 2026-11-19: 8c5fdb750b75's two clearance asks timed out at 11:04 and
# 11:06 while the gate still carried it to PROVED, and a terminal ticket asks no gate again, so
# ticket-unqueued-8c5fdb750b75-at-clearance stood with nothing left to clear it. `cairn cleanup`
# hands the live ticket-unqueued-*/ticket-refused-* ids here; each whose ticket now stands at a
# terminal state and whose raise stands on the ticket's own trail is cleared by the ticket.
_TICKET_TROUBLE = re.compile(r"^ticket-(?:unqueued|refused)-(?P<tid>.+)-at-(?P<gate>[a-z_]+)$")


def recheck(ids, *, tickets_dir=None, roots=None) -> dict:
    """Clear each ``ticket-unqueued-*``/``ticket-refused-*`` id in ``ids`` whose ticket stands
    terminal and whose raise stands on that ticket's trail. Returns ``cleared`` / ``standing``
    (a ticket still under way, or nothing raised here) / ``unknown`` (no such ticket, or not a
    ticket trouble)."""
    from cairn.tools.base.workflow_grammar import is_terminal
    out: dict = {"cleared": [], "standing": [], "unknown": []}
    for ident in ids:
        m = _TICKET_TROUBLE.match(ident)
        if not m:
            out["unknown"].append(ident)
            continue
        try:
            t = Ticket.at(m.group("tid"), tickets_dir=tickets_dir, roots=roots)
        except FileNotFoundError:
            out["unknown"].append(ident)
            continue
        state = _step(t.workflow)
        if not (is_terminal(state) and t._stands_raised(ident)):
            out["standing"].append(ident)
            continue
        # BY THE NOTIFIED RECIPIENT, AS THE TESTER'S RECHECK CLEARS (17b087f2483f). The trouble
        # was raised to "cc"; a clear by the ticket's id closes it only under an operator's
        # measured hand, so cleanup run from a gate or a unit left it partially cleared.
        t.clear_trouble(ident, by="cc",
                        what_changed=f"{t.id} stands at {state}, a terminal: it asks "
                                     f"{m.group('gate')} no more")
        out["cleared"].append(ident)
    return out


if __name__ == "__main__":
    import argparse
    import os
    _ap = argparse.ArgumentParser(prog="python3 -m cairn.machines.ticket.ticket")
    _ap.add_argument("--recheck", nargs="*", metavar="TROUBLE_ID", required=True,
                     help="clear the ticket troubles whose ticket stands terminal")
    _ap.add_argument("--tickets-dir", default=os.environ.get("CAIRN_TICKETS_DIR"),
                     help="the ticket store (default $CAIRN_TICKETS_DIR, else the live one)")
    _a = _ap.parse_args()
    # Under `python -m` this file runs as __main__, and a Ticket built here would name its
    # trail after __main__ and read none of the raises; the named module's recheck reads
    # the ticket's own trail (measured 2026-11-19: every id read standing).
    from cairn.machines.ticket.ticket import recheck as _recheck
    print(json.dumps(_recheck(_a.recheck, tickets_dir=_a.tickets_dir), indent=2))

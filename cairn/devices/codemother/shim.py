"""codemother/shim.py — CodeMother's presence on the heartbeat, and her hand at the door.

CodeMother is its own PID, shim-launched on demand via MCP/chat/CLI/skill. The shim
gives CodeMother a rack address so the bus can deliver messages to it and the ground
loop can fire its probes.

TWO THINGS WERE MEASURED DEAD HERE ON 2026-09-09 (ticket 8754ae677af6) and both are
fixed by this file rather than worked around:

  1. ``declared_verbs`` was a TUPLE on the shim. Every reader in the system asks a
     DEVICE for ``declared_verbs()`` and gets a dict of verb → handler
     (``shim.deliver`` at ``tools/base/shim.py``, the announce menu, the contract
     face). A tuple on the shim answered none of them, so the four verbs it named
     were a list nobody could dispatch.
  2. ``deliver()`` was overridden to persist mail and return — it never called
     ``super().deliver()``, so the verb dispatch that bounces an unknown verb and
     replies to the sender never ran, and ``handle_verb`` below it had zero callers.

So codemother's whole verb surface was unreachable over the bus while looking, from
the outside, exactly like a device that had one. The fix is to be an ordinary device:
a real ``CodeMotherDevice`` with a real ``declared_verbs()``, and a ``deliver`` that
hands a VERB-carrying envelope to the base dispatcher and keeps the mail-drop only for
verbless mail (which is what the mail directory was always for — the device process
reads it when woken).

THE CROSS VERB IS THIS TICKET'S POINT. CodeMother owns the care of the code (ruled
2026-09-06), and an owner with no gate is paper: the write she must be able to gate is
a CROSSING. She fires the harbor's clearance door over the bus, as herself, and the
door's own checks run unchanged — so a crossing she admits carries HER name in the
record of truth, and a crossing she should not have admitted is refused by the door
rather than by her manners. She may not import harbor_master (device isolation, ruled
2026-08-31); the bus is the whole seam.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim
from cairn.tools.base.address import instance_path

_INSTANCE_ROOT = instance_path("codemother", 0)
_MAIL_DIR = _INSTANCE_ROOT / "mail"

# The harbor's bus address. A STRING, deliberately: naming the device is not importing
# it, and this is the only thing codemother needs to know about the harbor.
_HARBOR = "harbor_master"

# The commons root, resolved the same way ``_resolve_component_dir`` resolves it below —
# stated once here because the sealed handler reads the ticket corpus to find its boats.
_COMMONS = Path(__file__).resolve().parents[3].parent / "CairnCommons"


def _crossing_roots() -> dict | None:
    """Which world this device derives a boat's CROSSING RECORD from — ``None`` for the live one.

    A READ, NOT A PARAMETER, and the precedent is ``clearance._crossing_roots`` (2026-09-10,
    ticket d2ecdb867bc9). Since the crossings stopped being an array on the ticket, a fixture
    that mints a boat in scratch has nowhere to put that boat's crossing except a journal, and
    the derivation has to be told where to look. Making it an argument on ``_boats_named_on``
    would put the world a device reads its evidence from into the hands of whoever posts the
    message — the shape the clearance charter refuses. It takes no arguments for exactly that
    reason: there is nothing here for a caller to pass.
    """
    return None


def _resolved(path: str) -> str:
    """One spelling for one file. A relative path is read against class-space, which is
    where a repo-relative proof path in a ticket means."""
    p = Path(path)
    if not p.is_absolute():
        p = Path(__file__).resolve().parents[3] / p
    try:
        return str(p.resolve())
    except OSError:
        return str(p)


class CodeMotherDevice(BaseDevice):
    """CodeMother's verb face. Woken by the shim when there is mail with a verb on it."""

    def __init__(self, bus=None) -> None:
        super().__init__()
        self._device_id = "codemother"
        self._bus = bus

    @property
    def device_id(self) -> str:
        return self._device_id

    def declared_verbs(self) -> dict:
        return {
            **super().declared_verbs(),
            "cross": self._handle_cross,
            "sealed": self._handle_sealed,
            "activate": self._handle_activate,
            "commit": self._handle_commit,
            "question": self._handle_question,
        }

    # --- the door she fires -------------------------------------------------

    def _handle_cross(self, envelope: dict) -> dict:
        """Ask the harbor to move a boat, AS CODEMOTHER.

        This handler decides nothing about whether the crossing may happen. It resolves
        the crossing's four coordinates (which boat, to what target, over which history,
        onto which proof), and asks. The harbor reads the actor off the ENVELOPE'S
        SENDER — which is ``codemother``, because this device posted it — so there is no
        field here that could claim a different hand, and none is sent.

        WHAT IT WILL NOT DO IS FALL BACK. If the harbor is not wired on this bus the
        request would sit until ``bus.request`` timed out thirty seconds later and then
        raise something about correlation ids. That is a true error told badly, so it is
        caught before it is made: the bus knows who is wired, and a harbor that is not
        there is said plainly, once, with the fix (CP1).
        """
        body = envelope.get("body", {}) or {}
        ticket = body.get("ticket") or body.get("boat_id") or ""
        target = body.get("target") or ""
        if not ticket or not target:
            return {"accepted": False, "verb": "cross", "device": self.device_id,
                    "reason": "cross needs a ticket and a target — a crossing is a named "
                              "boat moving to a named state"}
        try:
            coords = self._crossing_coordinates(ticket, body)
        except ValueError as exc:
            return {"accepted": False, "verb": "cross", "device": self.device_id,
                    "ticket": ticket, "target": target, "reason": str(exc)}
        if self._bus is None:
            return {"accepted": False, "verb": "cross", "device": self.device_id,
                    "ticket": ticket, "target": target,
                    "reason": "codemother has no bus, and the harbor door is only "
                              "reachable over one — she may not import it (device "
                              "isolation, ruled 2026-08-31)"}
        wired = set(self._bus.list() or {})    # {device_id: {"wired": ..., ...}}
        if wired and _HARBOR not in wired:
            return {"accepted": False, "verb": "cross", "device": self.device_id,
                    "ticket": ticket, "target": target,
                    "reason": f"{_HARBOR!r} is not wired on this bus, so there is no door "
                              f"to knock on. Wired: {sorted(wired)}. Reach it first: "
                              f"reach('codemother', {_HARBOR!r})"}

        # THE BOUNDARY, LOGGED AT BOTH EDGES. This handler is the first thing in this
        # component to inherit BaseDevice, and a device that inherits emit() and never
        # fires it is silent at every crossing (the build inspector's silent_device sieve
        # measured exactly that here on 2026-09-09, and it was right). The ask and the
        # answer are two records on purpose: an ask with no answer beside it is a request
        # that never came back, and that is the shape a reader needs to be able to see.
        self.emit("cross_asked", pointer=ticket,
                  values={"target": target, "door": _HARBOR,
                          "proven_by": coords["proven_by"]})
        reply = self._bus.request(
            sender=self.device_id, to=_HARBOR, verb="clear",
            why=f"codemother clears {ticket} to {target}",
            body={"workflow": coords["workflow"], "target": target,
                  "boat_id": ticket, "proven_by": coords["proven_by"],
                  "history_path": coords["history_path"],
                  "state_path": coords["state_path"],
                  "journal_extra": {"ticket": ticket, **(body.get("journal_extra") or {})}},
            timeout=float(body.get("timeout", 30.0)),
        )
        answer = dict(reply.get("body") or {})
        answer["asked_as"] = self.device_id
        answer["door"] = _HARBOR
        self.emit("cross_answered", pointer=ticket,
                  values={"target": target,
                          "accepted": bool(answer.get("accepted")),
                          "refusal": answer.get("refusal", "")})
        return answer

    @staticmethod
    def _crossing_coordinates(ticket: str, body: dict) -> dict:
        """The four coordinates of a crossing, taken from the body or read off the boat.

        A caller that already knows them (a proof against a fixture history, above all)
        passes them and nothing is read. A caller that knows only the ticket gets them
        derived — from the ticket file, through ``chain.grammar.ticket_path``, which is
        THE one implementation of where a ticket lives, and from the ticket's own
        ``owning_intention``, whose directory is where that component's history berths
        (Law 5: intent, state and proofs share an address).

        ``proven_by`` is never derived. No ticket field carries it (measured 2026-09-09
        across 258 tickets: 0), and inventing one would mean this device choosing which
        proof the harbor leans on — which is the one thing Law 8 asks a hand to state.
        """
        from cairn.tools.chain.grammar import ticket_path

        proven_by = body.get("proven_by")
        if not proven_by:
            raise ValueError(
                "cross needs proven_by — the harbor clears only onto proven code (Law 8) "
                "and the proof is named by the hand asking, never guessed from the ticket")
        workflow = body.get("workflow")
        history_path = body.get("history_path")
        state_path = body.get("state_path")
        if workflow and history_path and state_path:
            return {"workflow": workflow, "history_path": history_path,
                    "state_path": state_path, "proven_by": proven_by}

        path = ticket_path(ticket)
        if path is None:
            raise ValueError(
                f"no ticket on file for {ticket!r}, so its workflow and its component's "
                f"history cannot be read. Pass workflow/history_path/state_path "
                f"explicitly, or cast the ticket first")
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        workflow = workflow or doc.get("workflow_and_state") or ""
        if not workflow:
            raise ValueError(f"ticket {ticket!r} carries no workflow_and_state — there is "
                             f"no cursor to move")
        if not (history_path and state_path):
            charter = doc.get("owning_intention") or ""
            if not charter:
                raise ValueError(
                    f"ticket {ticket!r} names no owning_intention, so the component whose "
                    f"history this crossing writes is unknown. Pass history_path and "
                    f"state_path explicitly")
            comp = _resolve_component_dir(charter)
            if comp is None:
                raise ValueError(
                    f"the owning_intention of {ticket!r} ({charter!r}) resolves under "
                    f"neither class-space nor the commons — nothing to write a history to")
            history_path = history_path or str(comp / "history.json")
            state_path = state_path or str(comp / "state.json")
        return {"workflow": workflow, "history_path": history_path,
                "state_path": state_path, "proven_by": proven_by}

    # --- the seal that crosses its own boat ---------------------------------

    def _handle_sealed(self, envelope: dict) -> dict:
        """A proof sealed. Cross every boat that proof was named on, and no others.

        THE MEASURED DEFECT (2026-09-07, ticket 1accdc1781aa): twelve tickets sat at
        ``PROVEME:waiting`` with a green seal already standing on the proof they named,
        some for three days. Nobody fired the crossing because firing one meant a mind
        remembering to run ``clearance.clear`` after a seal, and minds forget — that pile
        IS the forgetting, written down. A decision with no judgment left in it should
        not wait for a person.

        THIS HANDLER MAKES NO DECISION EITHER, and that is the design rather than a
        limitation. It answers one question — *which boats named this proof?* — by
        reading the ticket corpus, and hands each answer to the door. Whether a boat may
        cross is the harbor's to say, and since this voyage the door's PROVED rung asks
        for full coverage on a matching fingerprint (``clearance.Uncovered``). So a
        hollow green does not become a crossing here; it becomes a refusal there, with a
        trouble raised beside it. The automation can only ever fire a door that was
        already hard — which is why the ticket's build order put the gate first.

        A RED SEAL CROSSES NOTHING. The tester announces every seal, green or red (Law 7
        — a red seals its red), and reading the verdict is this handler's job, not the
        sender's: a tool that only announced its greens would be a tool deciding what the
        owner gets to know.

        CONCEPT-PIECES NEVER ARRIVE HERE, and the reason is worth stating rather than
        assuming: a concept-piece is proved by REVIEW, and a review verdict is not a
        tester seal, so no ``sealed`` message is ever sent about one. Nothing filters
        them out below because nothing needs to — but a reader who finds one in a body
        has found a real defect upstream, not a missing branch here.
        """
        body = envelope.get("body", {}) or {}
        proof = str(body.get("proof") or body.get("proof_path") or "")
        if not proof:
            return {"accepted": False, "verb": "sealed", "device": self.device_id,
                    "reason": "sealed needs the proof it sealed — the boats to cross are "
                              "the ones that named it, and an unnamed proof names none"}
        verdict = str(body.get("verdict") or "")
        if verdict != "green":
            self.emit("sealed_heard", pointer=proof,
                      values={"verdict": verdict, "crossed": 0,
                              "why": "a red seal crosses nothing"})
            return {"accepted": True, "verb": "sealed", "device": self.device_id,
                    "proof": proof, "verdict": verdict, "crossed": [], "refused": [],
                    "reason": "a red seal crosses nothing — the boat stays where it is "
                              "and the red stands beside it (Law 7)"}

        boats = self._boats_named_on(proof)
        self.emit("sealed_heard", pointer=proof,
                  values={"verdict": verdict, "boats": len(boats),
                          "fingerprint": body.get("source_fingerprint", "")})
        crossed, refused = [], []
        for boat in boats:
            # THE CROSSING NAMES WHAT THE BOAT NAMED, NOT WHAT WAS JUST SEALED (2026-09-09).
            # A SEAM HAS ENDS IN MORE THAN ONE COMPONENT, which is why ``proven_by`` is read
            # as one-or-many everywhere else in this path — and passing the single sealed
            # proof here would have thrown that away at the last step: the PROVED rung asks
            # whether every clause of the falsifier is DECLARED by some proof the crossing
            # names, so a three-ended seam would be refused for the two ends it forgot to
            # mention. Measured on this very ticket, whose five clauses live in three files.
            # The boat's own PROVEME crossing is the record of what proves it; the seal is
            # only the event that says now. Every named end must still stand — the harbor
            # checks that, and refusing a seam because one end went stale is correct.
            answer = self._handle_cross({
                "sender": self.device_id,
                "body": {"ticket": boat["ticket"], "target": "PROVED",
                         "proven_by": boat["proven_by"]},
            })
            if answer.get("accepted"):
                crossed.append(boat["ticket"])
            else:
                refused.append({"ticket": boat["ticket"],
                                "reason": answer.get("reason") or answer.get("refusal", "")})
        return {"accepted": True, "verb": "sealed", "device": self.device_id,
                "proof": proof, "verdict": verdict,
                "crossed": crossed, "refused": refused}

    @staticmethod
    def _boats_named_on(proof: str) -> list[dict]:
        """Every cast ticket standing AT PROVEME whose latest crossing names ``proof``.

        Each answer is ``{"ticket": <id>, "proven_by": [<every proof that crossing named>]}``
        — the id alone would not be enough, because what the boat declared as its proof is
        exactly what the crossing forward has to carry (see the caller's note).

        Two conditions and both are necessary. The cursor, because a proof is named on a
        boat's PROVEME crossing and stays named after it moves on — matching on the name
        alone would re-cross a boat every time its proof was resealed. And the cut at the
        latest forward BUILDME (``proof_coverage._proven_by``'s rule), because a boat
        kicked back and re-crossed names a new proof, and the abandoned one must stop
        pulling it forward.

        The paths are compared RESOLVED. The tester announces an absolute path; a ticket
        may have recorded a repo-relative one; the same file under two spellings is one
        file, and a boat left behind by a string compare is exactly the parked boat this
        ticket exists to stop.
        """
        from cairn.tools.base.crossings import proven_by_since_buildme
        from cairn.tools.base.transitions import parse_workflow
        from cairn.tools.proof_coverage import load_tickets

        want = _resolved(proof)
        out = []
        for ticket in load_tickets(_COMMONS):
            wf = ticket.get("workflow_and_state") or ""
            if not wf:
                continue
            try:
                if parse_workflow(wf).here != "PROVEME":
                    continue
            except Exception:      # noqa: BLE001 — a malformed cursor is the ticket
                continue           # inspector's finding, not this handler's
            # EVERY PROOF NAMED SINCE THE BUILD THAT STANDS — derived from the journals
            # since 2026-09-10 (ruling crossings-are-derived-never-written), and asked for
            # by the name of the rule rather than re-implemented. This loop and
            # proof_coverage._proven_by were the same eleven lines written twice, which is
            # how two readers of one key drift into two rules without anyone deciding to.
            # It read the LAST RECORD until later that same day. One crossing act is
            # journaled at every address it touches, so the last record is one component's
            # share of the act and a boat proved at four addresses was surfaced by only one
            # of its four proofs. Measured: 1 of the 42 migrated tickets lost 3 proofs.
            named = proven_by_since_buildme(str(ticket.get("id") or ""), _crossing_roots())
            if named and want in {_resolved(one) for one in named}:
                out.append({"ticket": str(ticket.get("id") or ""), "proven_by": named})
        return [one for one in out if one["ticket"]]

    # --- the watcher face, now actually reachable ---------------------------

    def _handle_activate(self, envelope: dict) -> dict:
        from cairn.devices.codemother.watch import activate
        body = envelope.get("body", {}) or {}
        return activate(body.get("area", ""), body.get("reason", "bus verb"),
                        context=body.get("context"))

    def _handle_commit(self, envelope: dict) -> dict:
        from cairn.devices.codemother.watch import on_commit
        body = envelope.get("body", {}) or {}
        return on_commit(body.get("hash", ""), body.get("files", []),
                         body.get("message", ""))

    def _handle_question(self, envelope: dict) -> dict:
        from cairn.devices.codemother.watch import on_question
        body = envelope.get("body", {}) or {}
        return on_question(body.get("question", ""), area=body.get("area"))

    def intention(self) -> dict:
        return {
            "what": "CodeMother — the owner of the care of the code: the watcher face "
                    "over the codebase, and the hand that clears a boat through the "
                    "harbor door as herself.",
            "why": "An owner with no gate is paper (Law 6). The write an owner of code "
                   "must be able to gate is a CROSSING, so she fires the clearance door "
                   "over the bus and her name lands in the record of truth.",
        }

    def state(self) -> dict:
        return {"mail_dir": str(_MAIL_DIR), "door": _HARBOR}

    def settings(self) -> dict:
        return {}


def _resolve_component_dir(charter: str) -> Path | None:
    """The directory a charter path names, under class-space or the commons.

    Two roots and no third, tried in that order — the same pair
    ``clearance.boat_owner_of`` resolves a charter against, stated here because
    codemother may not import that module to ask.
    """
    cairn_root = Path(__file__).resolve().parents[3]
    commons_root = cairn_root.parent / "CairnCommons"
    for root in (cairn_root, commons_root):
        candidate = root / charter
        if candidate.is_file():
            return candidate.parent
        if candidate.is_dir():
            return candidate
    p = Path(charter)
    if p.is_absolute() and p.is_file():
        return p.parent
    return None


class CodeMotherShim(BaseShim):

    def __init__(self, bus=None) -> None:
        super().__init__(bus=bus)

    @property
    def device_id(self) -> str:
        return "codemother"

    def _start_device(self):
        return CodeMotherDevice(bus=self._bus)

    def declared_contract(self) -> dict:
        """The verb menu, readable without waking the device — COMPILED from the device's
        own ``declared_verbs()`` so adding a handler needs no second edit (Law 1)."""
        return {"verbs": sorted(CodeMotherDevice(bus=self._bus).declared_verbs()),
                "panes": []}

    def deliver(self, envelope: dict):
        """Dispatch a VERB-carrying envelope through the base shim; drop verbless mail
        into the instance mail directory for the device process to read when woken.

        The order matters and it is the fix this file records: base first for anything
        that names a verb, so an unknown verb bounces to its sender and a known one gets
        answered on the bus. Only mail with nothing to dispatch is persisted, which is
        what the mail drop was for."""
        if envelope.get("verb"):
            return super().deliver(envelope)
        return self._persist(envelope)

    @staticmethod
    def _persist(envelope: dict) -> dict:
        """Persist the envelope to the instance mail directory."""
        _MAIL_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        msg_id = f"msg-{now.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
        record = {
            "id": msg_id,
            "received": now.isoformat(),
            "envelope": envelope,
        }
        path = _MAIL_DIR / f"{msg_id}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
        return {"persisted": True, "path": str(path)}

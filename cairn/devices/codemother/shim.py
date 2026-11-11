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

THE CROSSING IS THE TICKET'S OWN ACT (outline 3.3.4.3, 9.6; ticket 0be964512fb0). CodeMother
owns the care of the code (ruled 2026-09-06), and the write she gates is a CROSSING — but she
does not move tickets. She HOLDS the gates a ticket asks: the clearance gate at
``machines/clearance`` answers ``queueme <fileref>``, instantiates the ticket on her side and
lets it process the pass, with ``clearance.clear`` as the door it crosses through, as her. The
``cross`` verb that asked the harbor's ``clear`` over the bus left with it (9.4.1.5).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim
from cairn.tools.base.address import log_path, tool_path

# MAIL SHE CANNOT DISPATCH IS EXHAUST (ticket d10668f76c45): the replies to her own requests, which
# nothing reads, are what HAPPENED to her, so they berth in the logs tree and age out with it.
# Kept in instance space they grew to 3,666 files / 79MB and rode into every tester seal.
_MAIL_DIR = log_path("codemother", 0) / "mail"

# THE CHARTER TOOL'S HELD INSTANCE (ticket 65b34c57ab71) — the first code ownership transfer
# from CC to another device. Charter is a tool and a tool has users, not an owner (Law 6),
# but a tool INSTANCE needs a holder, and the holder is the one whose feedback loop can act
# on it: charter is a building tool, so build-quality feedback belongs to the builder. The
# instance berths at ``devices/codemother/0/tools/charter`` in both roots — class-space
# carries its charter (``cairn/devices/codemother/0/tools/charter/intention+why.json``),
# instance-space carries its life: the data_recorder backpack at ``inbound/`` that collects
# feedback, reached by codemother's own ``charter`` and ``feedback`` verbs. No declaration
# file names it, and the bus never delivers to it: only devices are on the bus (outline
# 19.16, ticket 7778e24dd82e). The instance is ensured on activate and by the ``charter``
# verb; the tool class gains no glue of its own, which is what keeps it a tool.
_CHARTER_TOOL = "charter"
_CHARTER_DATA = "inbound"


def charter_instance(roots: dict | None = None) -> Path:
    """Where codemother holds the charter tool's instance in instance-space."""
    return tool_path("codemother", 0, _CHARTER_TOOL, roots)


def charter_backpack(roots: dict | None = None):
    """The held charter instance's data_recorder backpack, built directly at its inbound/."""
    from cairn.tools.data_recorder.data_recorder import DataRecorder
    return DataRecorder(charter_instance(roots) / _CHARTER_DATA)


def ensure_charter_instance(roots: dict | None = None) -> dict:
    """Ensure the held charter instance exists (its backpack folder) and say what it holds.

    Idempotent: the inbound folder is made once and left alone after. Returns the address,
    the backpack path, and how many feedback records the backpack holds right now."""
    home = charter_instance(roots)
    inbound = home / _CHARTER_DATA
    inbound.mkdir(parents=True, exist_ok=True)
    return {"address": str(home), "backpack": str(inbound),
            "tool_class": "cairn/tools/charter", "records": len(charter_backpack(roots).read())}

# The commons root — stated once here because the sealed handler reads the ticket corpus to find its boats.
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
            "sealed": self._handle_sealed,
            "activate": self._handle_activate,
            "commit": self._handle_commit,
            "question": self._handle_question,
            "charter": self._handle_charter,
            "feedback": self._handle_feedback,
            "deposit": self._handle_deposit,
            "drain": self._handle_drain,
        }

    def declared_machines(self) -> dict:
        """The gates she holds, each answering ``machines/<gate>/<verb>`` (outline 3.3.4.1)."""
        from cairn.devices.codemother.machines.clearance.gate import ClearanceGate
        from cairn.devices.codemother.machines.watchme.gate import Voice, WatchmeGate
        return {"watchme": WatchmeGate(participant=Voice(self._bus)),
                "clearance": ClearanceGate(participant=Voice(self._bus))}

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
                    "awaiting_hollow": [],
                    "reason": "a red seal crosses nothing — the boat stays where it is "
                              "and the red stands beside it (Law 7)"}

        boats = self._boats_named_on(proof)
        self.emit("sealed_heard", pointer=proof,
                  values={"verdict": verdict, "boats": len(boats),
                          "fingerprint": body.get("source_fingerprint", "")})
        from cairn.tools.base.validation import latest_seal
        from cairn.tools.system_word import is_word

        crossed, refused, awaiting_hollow = [], [], []
        for boat in boats:
            # A SEAL WAITS FOR ITS HOLLOW READING (ticket b984567d8c05). The reading can only be
            # taken AFTER a seal stands, so the first seal on a proof always arrives without
            # one — and crossing on it was refused hollow_evidence_absent, which sends the boat
            # to FIXME. Measured n=2 on 2026-10-02 (e8fe361a5b2f, 56d1aff4455e): an unchanged
            # build bounced, both times. An ABSENT reading is a measurement still to come, so
            # the boat waits, listed; the tester announces again when the reading lands
            # (9bdbeeaa1f8b). A PRESENT reading that names a hollow, unreadable or empty file
            # is not waiting for anything, so it crosses and the door refuses it into FIXME,
            # where the real lack belongs (973574dddb77). A proof with NO seal is not waiting
            # either: the harbor already refuses it. Concept-pieces are proved by review and
            # carry no reversion reading at all.
            if not is_word(boat.get("node_class"), "concept-piece"):
                waiting_on = [
                    p for p in boat["proven_by"]
                    if (seal := latest_seal(_resolved(p), artifact=False)) is not None
                    and not isinstance(((seal.get("evidence") or {}).get("hollow") or {})
                                       .get(boat["ticket"]), dict)]
                if waiting_on:
                    awaiting_hollow.append({"ticket": boat["ticket"], "waiting_on": waiting_on})
                    continue
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
            # The boat asks the clearance gate to queue it, fileref only; the gate reads the
            # same proven_by off the boat's crossings (``proven_by_since_buildme``).
            answer = self.declared_machines()["clearance"].queueme(
                {"sender": self.device_id, "body": {"fileref": boat["ticket"]}})
            if answer.get("accepted"):
                crossed.append(boat["ticket"])
            else:
                refused.append({"ticket": boat["ticket"],
                                "reason": answer.get("reason") or answer.get("refusal", "")})
        self.emit("sealed_heard", pointer=proof,
                  values={"crossed": len(crossed), "refused": len(refused),
                          "awaiting_hollow": len(awaiting_hollow)})
        return {"accepted": True, "verb": "sealed", "device": self.device_id,
                "proof": proof, "verdict": verdict,
                "crossed": crossed, "refused": refused, "awaiting_hollow": awaiting_hollow}

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
                out.append({"ticket": str(ticket.get("id") or ""), "proven_by": named,
                            "node_class": str(ticket.get("node_class") or "")})
        return [one for one in out if one["ticket"]]

    # --- the watcher face, now actually reachable ---------------------------

    def _handle_activate(self, envelope: dict) -> dict:
        from cairn.devices.codemother.watch import activate
        body = envelope.get("body", {}) or {}
        out = activate(body.get("area", ""), body.get("reason", "bus verb"),
                       context=body.get("context"))
        # activating codemother ensures what she holds (ticket 65b34c57ab71)
        held = {"charter": ensure_charter_instance()}
        if isinstance(out, dict):
            return {**out, "held": held}
        return {"activated": out, "held": held}

    def _handle_charter(self, envelope: dict) -> dict:
        """The held charter instance, by name: ensure it, write a feedback record into its
        backpack if the body carries one, and answer with what the backpack holds.

        ``body.record`` — a data_recorder record (finding, inspector_target, probe_source);
        ``body.read`` — how many of the newest records to return (default 0)."""
        body = envelope.get("body", {}) or {}
        out = ensure_charter_instance()
        recorder = charter_backpack()
        record = body.get("record")
        if isinstance(record, dict):
            out["written"] = recorder.write({
                "probe_source": envelope.get("sender", "unknown"),
                "inspector_target": "codemother/0/tools/charter", **record})
        want = body.get("read", 0)
        if isinstance(want, int) and want > 0:
            out["read"] = recorder.read()[-want:]
        out["records"] = len(recorder.read())
        return out

    def _handle_feedback(self, envelope: dict) -> dict:
        """A post-build reflection from /sail (ticket 68f563403c8f): ``body.reflection`` is
        the packet ``skills/sail/reflection.py`` shaped, and it lands as ONE record in the
        held charter backpack — the same inbound the ``charter`` verb writes — under
        ``metadata.type == "feedback"`` so ``ingest.ingest_reflections`` picks it up.

        The verb judges only what a receiver must: a dict with an explicit boolean
        ``at_par`` (the sender's door already refused everything else, and a packet that
        skipped that door still cannot land a silent one here). It never re-opens the build
        and never answers the sender with more than the receipt."""
        body = envelope.get("body", {}) or {}
        packet = body.get("reflection")
        if not isinstance(packet, dict):
            return {"accepted": False, "verb": "feedback", "device": self.device_id,
                    "why": "body.reflection is not a dict — a reflection is a packet, not prose"}
        if not isinstance(packet.get("at_par"), bool):
            return {"accepted": False, "verb": "feedback", "device": self.device_id,
                    "why": "reflection.at_par is not an explicit true/false — silence is refused"}
        ensure_charter_instance()
        recorder = charter_backpack()
        flags = sum(1 for f in (packet.get("findings") or []) if isinstance(f, dict) and f.get("kind") == "flag")
        ticket = packet.get("ticket", "?")
        written = recorder.write({
            "probe_source": envelope.get("sender", "unknown"),
            "inspector_target": "codemother/0/tools/charter",
            "finding": f"{ticket}: at par" if packet["at_par"] else f"{ticket}: below par ({flags} flag(s))",
            "metadata": {"type": "feedback"},
            "reflection": packet})
        return {"accepted": True, "verb": "feedback", "device": self.device_id,
                "written": written, "records": len(recorder.read())}

    def _handle_commit(self, envelope: dict) -> dict:
        from cairn.devices.codemother.watch import on_commit
        body = envelope.get("body", {}) or {}
        return on_commit(body.get("hash", ""), body.get("files", []),
                         body.get("message", ""))

    def _handle_question(self, envelope: dict) -> dict:
        from cairn.devices.codemother.watch import on_question
        body = envelope.get("body", {}) or {}
        return on_question(body.get("question", ""), area=body.get("area"))

    def _handle_deposit(self, envelope: dict) -> dict:
        """Land one berthed chart packet in its tree (ticket e8fe361a5b2f). Body
        ``{berth, nexus?}``; a berth that is missing or not on disk is refused."""
        from cairn.devices.codemother.deposit import deposit_berth, embed, embed_metered
        from cairn.tools.bus_client import reach
        body = envelope.get("body", {}) or {}
        berth = body.get("berth")
        if not isinstance(berth, str) or not berth:
            return {"accepted": False, "verb": "deposit", "device": "codemother",
                    "reason": "deposit needs a berth path in body.berth"}
        if not os.path.isfile(os.path.expanduser(berth)):
            return {"accepted": False, "verb": "deposit", "device": "codemother",
                    "reason": "berth %r is not on disk" % berth}
        bus = self._bus or reach("inference_domain")
        try:
            out = deposit_berth(berth, nexus=body.get("nexus"), embed=embed(bus),
                                embed_metered=embed_metered(bus))
        except Exception as e:  # noqa: BLE001 — a refusal rides back named, loud
            return {"accepted": False, "verb": "deposit", "device": "codemother",
                    "reason": "%s: %s" % (type(e).__name__, e)}
        return {"accepted": True, "verb": "deposit", "device": "codemother", **out}

    def _handle_drain(self, envelope: dict) -> dict:
        """Land every verdict the PROVED crossing enqueued and nobody deposited; one
        entry per berth, a failure named and left pending (ticket e8fe361a5b2f)."""
        from cairn.devices.codemother.deposit import drain_pending, embed_metered
        from cairn.tools.bus_client import reach
        bus = self._bus or reach("inference_domain")
        return {"accepted": True, "verb": "drain", "device": "codemother",
                "drained": drain_pending(embed=embed_metered(bus))}

    def intention(self) -> dict:
        return {
            "what": "CodeMother — the owner of the care of the code: the watcher face "
                    "over the codebase, and the holder of the gates a ticket asks to "
                    "queue it (clearance, watchme).",
            "why": "An owner with no gate is paper (Law 6). The write an owner of code "
                   "must be able to gate is a CROSSING, so she holds the clearance gate "
                   "and her name lands in the record of truth.",
        }

    def state(self) -> dict:
        return {"mail_dir": str(_MAIL_DIR), "gates": sorted(self.declared_machines())}

    def settings(self) -> dict:
        return {}


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

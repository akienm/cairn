"""quorum.py — the SEAL DOOR for a node proved by human judgment, not by a tester run.

A code-seam is proved by running its proof: the verdict is an exit code, and the tester is
both the hand that reads it and the hand that seals it. A **concept-piece** cannot work that
way — the prose IS the implementation, so its proof is people reading it and saying whether
the thing is faithful. ``node_classes/concept-piece.json`` names the gate:

    prove_gate: "quorum signature gate — N human reviewers read and sign. Recorded as a
    VALIDATION: method = 'review by N readers', caller = the reviewers, evidence = their
    restated-back understanding."

WHY THIS FILE EXISTS AT ALL (the defect it closes, 2026-07-25). The class definition has said
that since 2026-07-15, and no concept-piece VALIDATION has ever been written. The reason was
purely mechanical and nobody had looked: ``validations_path_for`` derives a seal's address
from a PROOF FILE path (``proofs/x.py`` -> ``validations/x.json``). A concept-piece has no
proof file, so the single write-door could not physically accept one. The gate was therefore
never "awaiting a signature" — it was awaiting an ADDRESS. Every report that it needed a
human's ratify was wrong, and CC made that report repeatedly. A gate with nowhere for its
verdict to land is not a gate; it is prose (Law 4), and this is the physics that retires it.

WHAT IS DELIBERATELY *NOT* NEW HERE. No new artifact type, no second record shape, no rival
door. The class def is explicit — "the same ticket + VALIDATION schema records a human-proved
node" — so a quorum seal is the SAME ratified eight fields, appended through the SAME
``persist_validation``. Only the addressing is new, because only the addressing was missing.

THE ONE THING PHYSICS MUST HOLD HERE (and the reason this is not just a dict literal): for a
code proof, verdict and seal come from one hand and that is fine. For a human-proved node they
are DIFFERENT HANDS — the reviewers give the verdict, the notary records it. A notary who is
also a reviewer is a self-seal, which is the hollow build in its purest form (Law 8). That is
checked below and refused, not asked for politely.

A red is not an error. A reviewer rejecting is a legitimate VERDICT that routes back to the
point of creation exactly like a red build (CP2) — so ``seal`` returns a red record and
persists it. The trail must show the rejection, or the kick-back has no evidence.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from cairn.devices.tester.device import GREEN, RED
from cairn.devices.tester.validation_store import (artifact_fingerprint, persist_validation,
                                           read_validations, validations_path_for_artifact)

# Where a ruling lives when it is a ruling: the intake door (`cairn ruling open`) writes
# nothing anywhere else. Derived from this file's own address, the way the proofs derive
# the commons — not chosen, and not an environment variable someone forgets to set.
_DECISIONS = Path(__file__).resolve().parents[4] / "CairnCommons" / "decisions"


class QuorumRefused(ValueError):
    """The seal door turning away a signature set that could not honestly seal anything.

    Refused BEFORE the record is written: a VALIDATION trail is append-only, so a seal that
    should not have been recorded cannot be taken back out (Law 7).
    """


def _ruling_on_file(ruling_id: str, decisions: Path | None = None) -> dict:
    """A ruling that can stand behind a same-hand seal: on disk, through the intake door,
    and confirmed by his marker. Anything less is a sentence, and the different-hands rule
    is not lifted by a sentence.

    Read from the decisions store, never accepted from the caller: the caller names the
    id, the door reads the packet. The two facts checked are the two the ruling door
    itself stamps — that the file exists under the id (intake wrote it) and that
    ``confirmed`` is true (his RULED marker, or its equivalent, was in the verbatim)."""
    decisions = _DECISIONS if decisions is None else decisions  # read at call, not at def
    ruling_id = (ruling_id or "").strip()
    if not ruling_id:
        raise QuorumRefused("under_ruling is empty — a same-hand seal needs a ruling id, not "
                            "a flag")
    path = decisions / f"{ruling_id}.json"
    if not path.is_file():
        raise QuorumRefused(
            f"no ruling {ruling_id!r} on file at {path} — the different-hands rule is lifted "
            "by a ruling that went through `cairn ruling open`, not by naming one")
    with open(path, encoding="utf-8") as fh:
        packet = json.load(fh)
    if not packet.get("confirmed"):
        raise QuorumRefused(
            f"ruling {ruling_id!r} is on file but not confirmed — an unconfirmed packet is "
            "CC's reading of his words, and CC's reading cannot lift a rule about CC")
    return packet


def _check_signature(sig: dict, i: int) -> tuple[str, str]:
    if not isinstance(sig, dict):
        raise QuorumRefused(f"signature {i} is a {type(sig).__name__}, not a record with a signer")
    signer = (sig.get("signer") or "").strip()
    verdict = (sig.get("verdict") or "").strip()
    restated = (sig.get("restated") or "").strip()
    if not signer:
        raise QuorumRefused(f"signature {i} names no signer — an anonymous seal is not a seal (Law 6)")
    if verdict not in (GREEN, RED):
        raise QuorumRefused(
            f"signature {i} from {signer!r} carries verdict {verdict!r}; a reviewer says "
            f"{GREEN!r} or {RED!r} — silence and 'maybe' are not verdicts (Law 3)")
    if not restated:
        raise QuorumRefused(
            f"signature {i} from {signer!r} carries no `restated` — the class def makes the "
            "reviewer's restated-back understanding the EVIDENCE. A signature with no "
            "restatement is a rubber stamp: it proves someone clicked, not that anyone read "
            "(Law 8 — a hollow build could pass that).")
    return signer, verdict


def seal(
    artifact_path: str,
    *,
    claim: str,
    signatures: list[dict],
    notary: str,
    quorum: int = 1,
    falsifier: str,
    horizon: str,
    now: str | None = None,
    under_ruling: str | None = None,
) -> dict:
    """Run the quorum signature gate over ``artifact_path`` and APPEND the VALIDATION.

    ``signatures`` is a list of ``{"signer", "verdict", "restated"}`` — the reviewers' own
    words, which are the evidence. ``notary`` is the hand that records; it may not be one of
    the signers. Returns the persisted VALIDATION (verdict green or red).

    Refuses, loudly and before writing: an unsigned or unrestated signature, a verdict that is
    neither green nor red, fewer distinct signers than ``quorum``, and a notary who reviewed.

    THE ONE ESCAPE FROM DIFFERENT-HANDS, AND IT IS A RULING, NOT A FLAG. A deterministic
    refusal is fixed or carries a ruling from Akien — never a paragraph (CLAUDE.md, rules
    awaiting physics). ``under_ruling`` names a ruling on file in the decisions store,
    confirmed by his marker, that delegates the reviewer's seat to the recording hand; with
    it the notary MAY be a signer, and the record says so in its method and carries the
    ruling id in its evidence, so a reader sees the lifted rule and who lifted it without
    opening anything. Without it the refusal stands exactly as before. The corrosion
    predicate is satisfied by construction: the constraint stopped constraining, and the
    ruling sits in the same act, in the same record. Born 2026-09-05 from Akien's words
    "you're hereby so delegated for the remainder of this session" — a delegation the door
    could not take, because the only way to spell it was two names for one hand.
    """
    if quorum < 1:
        raise QuorumRefused(f"quorum={quorum} would seal with nobody having read it")
    if not signatures:
        raise QuorumRefused(
            f"no signatures: {artifact_path!r} cannot pass a quorum gate on an empty room")

    checked = [_check_signature(s, i) for i, s in enumerate(signatures)]
    signers = {s for s, _ in checked}
    if len(signers) < quorum:
        raise QuorumRefused(
            f"quorum is {quorum} distinct reviewers; got {len(signers)} ({sorted(signers)}) — "
            f"{len(signatures)} signature(s), so a repeat signer cannot stand in for a second "
            "pair of eyes (that is the whole meaning of a quorum)")

    notary = (notary or "").strip()
    if not notary:
        raise QuorumRefused("a seal with no notary has no accountable hand (Law 6)")
    delegation = None
    if notary in signers:
        if under_ruling is None:
            raise QuorumRefused(
                f"notary {notary!r} is also a reviewer. For a human-proved node the verdict and "
                "the seal are DIFFERENT HANDS (node_classes/concept-piece.json) — one hand doing "
                "both is a self-seal, which is exactly the hollow build Law 8 forbids. A ruling "
                "that delegates the reviewer's seat lifts this: name it in `under_ruling`.")
        ruling = _ruling_on_file(under_ruling)
        delegation = {
            "ruling": under_ruling,
            "ruled_by": ruling.get("ruled_by"),
            "date": ruling.get("date"),
            "now_the_spec_says": ruling.get("now_the_spec_says"),
        }

    rejected = [s for s, v in checked if v == RED]
    verdict = RED if rejected else GREEN

    hands = (f"same hand, under ruling {under_ruling!r}" if delegation
             else "different hands")
    validation = {
        "claim": claim,
        # caller = THE REVIEWERS, per the class def — the seal is theirs, not the notary's.
        "caller": ", ".join(sorted(signers)),
        "date": now or datetime.now().isoformat(timespec="seconds"),
        "method": (
            f"quorum signature gate — review by {len(signers)} reader(s), quorum {quorum}; "
            f"verdict = the reviewers', seal recorded by notary {notary!r} ({hands})"
        ),
        "verdict": verdict,
        "evidence": {
            "signatures": [dict(s) for s in signatures],
            "notary": notary,
            "quorum_required": quorum,
            "distinct_signers": len(signers),
            # THE HORIZON, MADE CHECKABLE — the same field a tester seal carries, over the
            # prose instead of the code: `standing()` expires this seal the moment the piece
            # the readers signed is not the piece on disk. Without it a quorum seal was
            # "green, but UNKNOWABLE" to the clearance gate, so no concept-piece had ever
            # crossed into PROVED through the harbor (2026-09-05).
            "source_fingerprint": artifact_fingerprint(artifact_path),
            **({"rejected_by": sorted(rejected)} if rejected else {}),
            **({"delegation": delegation} if delegation else {}),
        },
        "falsifier": falsifier,
        "horizon": horizon,
    }
    # WHAT COMES BACK IS WHAT LANDED, not what was built. The door owns the record on disk,
    # and handing a caller a second copy assembled here is how a store grows a rival source of
    # truth (the same defect MethodRegistry was). Read it back through the door's own reader.
    # Since 2026-08-16 the file holds exactly one record, so [-1] is that record — the index
    # stays because every reader in the corpus spells it this way and a one-element list is
    # what read_validations returns.
    persist_validation(validation, artifact_path=artifact_path)
    return read_validations(path=validations_path_for_artifact(artifact_path))[-1]

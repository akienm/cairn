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

from datetime import datetime

from cairn.tester.device import GREEN, RED
from cairn.tester.validation_store import (persist_validation, read_validations,
                                           validations_path_for_artifact)


class QuorumRefused(ValueError):
    """The seal door turning away a signature set that could not honestly seal anything.

    Refused BEFORE the record is written: a VALIDATION trail is append-only, so a seal that
    should not have been recorded cannot be taken back out (Law 7).
    """


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
) -> dict:
    """Run the quorum signature gate over ``artifact_path`` and APPEND the VALIDATION.

    ``signatures`` is a list of ``{"signer", "verdict", "restated"}`` — the reviewers' own
    words, which are the evidence. ``notary`` is the hand that records; it may not be one of
    the signers. Returns the persisted VALIDATION (verdict green or red).

    Refuses, loudly and before writing: an unsigned or unrestated signature, a verdict that is
    neither green nor red, fewer distinct signers than ``quorum``, and a notary who reviewed.
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
    if notary in signers:
        raise QuorumRefused(
            f"notary {notary!r} is also a reviewer. For a human-proved node the verdict and the "
            "seal are DIFFERENT HANDS (node_classes/concept-piece.json) — one hand doing both is "
            "a self-seal, which is exactly the hollow build Law 8 forbids.")

    rejected = [s for s, v in checked if v == RED]
    verdict = RED if rejected else GREEN

    validation = {
        "claim": claim,
        # caller = THE REVIEWERS, per the class def — the seal is theirs, not the notary's.
        "caller": ", ".join(sorted(signers)),
        "date": now or datetime.now().isoformat(timespec="seconds"),
        "method": (
            f"quorum signature gate — review by {len(signers)} reader(s), quorum {quorum}; "
            f"verdict = the reviewers', seal recorded by notary {notary!r} (different hands)"
        ),
        "verdict": verdict,
        "evidence": {
            "signatures": [dict(s) for s in signatures],
            "notary": notary,
            "quorum_required": quorum,
            "distinct_signers": len(signers),
            **({"rejected_by": sorted(rejected)} if rejected else {}),
        },
        "falsifier": falsifier,
        "horizon": horizon,
    }
    # WHAT COMES BACK IS WHAT LANDED, not what was built. Since 2026-08-05 the door mints a
    # trail_link into `evidence` as it seals, so the dict assembled above is no longer the
    # record on disk — and handing a caller a second, unlinked copy is how a store grows a
    # rival source of truth (the same defect MethodRegistry was). Read it back through the
    # door's own reader; the trail's newest entry IS the seal.
    persist_validation(validation, artifact_path=artifact_path)
    return read_validations(path=validations_path_for_artifact(artifact_path))[-1]

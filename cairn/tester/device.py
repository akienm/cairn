"""TesterDevice — the first real device on the spine, at its minimal provable stone.

The tester is the system's **notary** and its **proving mechanism** (MAP.md:569):
it runs a proof and attests the result — the verdict comes from a hand the builder
did not guide (Law 8: nothing enters proven-space without a proof a hollow build
couldn't pass). This file is that idea at its smallest honest size.

What it does today (the stone):
  - Subclasses ``BaseDevice`` — so it carries CP1-CP6 structurally (Law 2) and
    reports the Form v0 #2 surface (intention → state → settings). It is the first
    real subject the base's armed composition trap actually bites on.
  - ``run_proof(path)`` runs a proof file as a subprocess and **produces** a
    VALIDATION record: the ratified eight fields (MAP.md:569) — ``claim, caller,
    date, method, verdict, evidence, falsifier, horizon``. ``verdict`` is read from
    the subject's exit code, not granted by the tester (an always-green tester is a
    hollow build; proofs/test_tester.py kills it with a red case).
  - The tester **owns the network** (MAP.md:333): ``run_proof(..., isolation="netns")``
    runs the subject inside a measured seal (``cairn/tester/isolation.py``) and folds
    the seal's verdict into the record's ``method`` + ``evidence`` — no ninth field.
    The seal is measured from inside, never assumed; an unconfirmable seal is
    INDETERMINATE and does not earn a green on the strength of its isolation.

FRESH design, mechanism grafted (like device.py/shim.py were redesigns): UU's tester
(``unseen_university/devices/tester/`` — netpolicy 381 + isolation 183 + sandbox +
seal) is the quarry. The seal's OS plumbing crosses nearly literally (kernel truth);
its design and the programmable Router (fixture/refuse/forward) do not — see
``isolation.py`` for the graft-vs-fresh ruling and the deferred Router.

CLOSED EDGE (2026-07-22): VALIDATIONS are now **persisted**. The durable greppable home is
``cairn/tester/validation_store.py`` — beside-code git-JSON, next to the ``proofs/`` each one
seals (Law 5; ruling in tickets/charter-state-history-split.json child b), NOT a Postgres
row. ``run_proof`` still returns the record and writes nothing itself (class-space stays
state-free by run_proof); a caller — the standing-lesson gate — persists it explicitly, which
keeps run_proof pure and testable as a table. The store refuses a drifted record, so a
non-eight-field validation cannot land and pass for a seal.

OPEN EDGES (filed, not faked — children of this stone):
  - The seal gives **no route** (the closed half of CLAUDE.md's "reached only through
    the domain" rules). The **chosen route** — a Router that serves/refuses/forwards a
    named dependency — is deferred to db_domain (FORWARD) and inference_domain
    (FIXTURE/REFUSE). See ``isolation.py``.
  - The verdict **method** is exit-code (+ seal) only. Quorum / review-by-N-experts
    for concept pieces (MAP.md:752) is a later method the ``method`` field names room
    for.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from cairn.base.device import BaseDevice
from cairn.tester.isolation import OPEN, Seal, get_isolation

GREEN = "green"
RED = "red"

# The ratified VALIDATION record shape (MAP.md:569). Exactly these eight — no more,
# no fewer; proofs/test_tester.py pins the set so a drifted record reds.
VALIDATION_FIELDS = (
    "claim",
    "caller",
    "date",
    "method",
    "verdict",
    "evidence",
    "falsifier",
    "horizon",
)


def _tail(text: str, n: int = 20) -> str:
    """Last ``n`` lines of captured output — enough to see a failure, not a flood."""
    return "\n".join((text or "").splitlines()[-n:])


class TesterDevice(BaseDevice):
    """Runs proofs and attests verdicts — the spine's notary, minimal version.

    Composes the Form (via BaseDevice → CoreValuesMixin): carries CP1-CP6 and
    reports intention → state → settings. Its one capability today is
    ``run_proof``; everything the full tester will own (network ownership, a
    durable VALIDATIONS store, richer verdict methods) is a filed open edge.
    """

    def __init__(self, device_id: str = "tester") -> None:
        super().__init__()
        self._device_id = device_id
        self._proofs_run = 0
        self._last_verdict: str | None = None

    @property
    def device_id(self) -> str:
        return self._device_id

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "Run proofs and attest the result — the system's notary and its proving mechanism.",
            "why": "A build is not done until a proof a hollow build couldn't pass says so (Law 8); "
            "the verdict must come from a hand the builder did not guide.",
        }

    def state(self) -> dict:
        # Honest, live condition — no faked node-state vocabulary (PROVED/LEARNING
        # land with the emit-chokepoint, MAP.md:832; not wired here yet).
        return {
            "proofs_run": self._proofs_run,
            "last_verdict": self._last_verdict,  # None until it has run one
        }

    def settings(self) -> dict:
        return {
            "interpreter": Path(sys.executable).name,
            "isolation": "owned — run_proof takes isolation='netns' to run under a measured "
            "seal (cairn/tester/isolation.py); default 'none' (bare) must be asked for by name. "
            "The chosen-route Router (serve/refuse/forward) is deferred to db/inference domains.",
            "validations_sink": "beside-code git-JSON — validation_store.py persists each "
            "VALIDATION to validations/<stem>.json next to the proofs/ it seals (Law 5); run_proof "
            "returns the record, the standing-lesson gate persists it, so run_proof stays state-free",
        }

    # --- the one capability: prove and attest -------------------------------

    def run_proof(
        self,
        proof_path,
        *,
        caller: str | None = None,
        timeout: int = 120,
        isolation: str = "none",
    ) -> dict:
        """Run ``proof_path`` as a subprocess; produce a VALIDATION of the outcome.

        The verdict is the subject's exit code (0 → green, else red) — read, not
        granted. With ``isolation="netns"`` the subject runs inside a measured network
        seal (``cairn/tester/isolation.py``): the seal is probed from inside and its
        verdict is folded into the record's ``method`` + ``evidence`` — never a ninth
        field. An unconfirmable seal is INDETERMINATE and is reported as such, not
        laundered into a green. Returns the ratified eight-field record; does not
        persist it (the store is a later stone).
        """
        proof_path = Path(proof_path)
        iso = get_isolation(isolation)

        # Measure the seal before trusting it (isolation.py: measured, never assumed).
        # NoIsolation reports OPEN with no subprocess; netns probes from inside.
        available, why = iso.available()
        if iso.seals_network and not available:
            seal = Seal("indeterminate", f"seal '{iso.name}' unavailable: {why}")
        else:
            seal = iso.check_seal(str(proof_path.parent))

        argv = iso.wrap([sys.executable, str(proof_path)], cwd=str(proof_path.parent))
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
            verdict = GREEN if proc.returncode == 0 else RED
            evidence = {
                "returncode": proc.returncode,
                "stdout_tail": _tail(proc.stdout),
                "stderr_tail": _tail(proc.stderr),
                "seal": {"verdict": seal.verdict, "detail": seal.detail},
            }
        except subprocess.TimeoutExpired:
            # A proof that hangs is a red, not a crash of the notary (CP1: say what
            # happened — we measured a timeout, we did not measure a pass).
            verdict = RED
            evidence = {
                "returncode": None,
                "stdout_tail": "",
                "stderr_tail": f"timed out after {timeout}s",
                "seal": {"verdict": seal.verdict, "detail": seal.detail},
            }

        # The method names HOW the verdict was reached AND how trustworthy the seal
        # under it is — so a reader sees seal-backing without opening the evidence.
        seal_note = f"seal={seal.verdict}" if seal.verdict != OPEN else "unsealed (isolation='none')"
        record = self._validation(
            claim=f"proof {proof_path.name} passes under {Path(sys.executable).name}",
            caller=caller or self._device_id,
            method=f"ran the proof as a subprocess ({seal_note}); verdict = exit code (0 → green, else red)",
            verdict=verdict,
            evidence=evidence,
            falsifier="the same proof exits non-zero on re-run, or the code it proves changes underneath it",
            horizon="valid until the proof file or the code it proves changes (Law 3: a VALIDATION expires)",
        )
        self._proofs_run += 1
        self._last_verdict = verdict
        return record

    def _validation(self, *, claim, caller, method, verdict, evidence, falsifier, horizon) -> dict:
        """Assemble the ratified eight-field VALIDATION record (MAP.md:569)."""
        return {
            "claim": claim,
            "caller": caller,
            "date": datetime.now().isoformat(timespec="seconds"),
            "method": method,
            "verdict": verdict,
            "evidence": evidence,
            "falsifier": falsifier,
            "horizon": horizon,
        }

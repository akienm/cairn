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

FRESH, not grafted (a deliberate redesign, like device.py/shim.py): UU's tester
(``unseen_university/devices/tester/`` — ~1226 lines of netpolicy / isolation /
sandbox / seal) is the network-sandbox pillar Cairn will reach as a *later* stone.
Only MAP's ratified VALIDATION schema crosses, and it crosses as a record shape,
not as carried code.

OPEN EDGES (filed, not faked — children of this stone):
  - VALIDATIONS are **produced, not yet persisted**. A durable greppable store is
    db_domain's stone (CLAUDE.md pending rule: durable state goes through the store
    primitives). This tester returns records; it does not write them anywhere yet,
    so class-space stays state-free.
  - The **kernel-owned network + build isolation** (UU's netpolicy/isolation) are
    NOT built. This tester runs local proofs; it does not yet guard a build's
    network. That is the next stone on the same pillar (MAP.md:888).
  - The verdict **method** is exit-code only. Quorum / review-by-N-experts for
    concept pieces (MAP.md:752) is a later method the ``method`` field already
    names room for.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from cairn.base.device import BaseDevice

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
            "isolation": "none — kernel-owned network + build sandbox not yet built "
            "(open edge; UU's netpolicy/isolation are a later stone on this pillar)",
            "validations_sink": "produced-only — the durable VALIDATIONS store is db_domain's "
            "stone (CLAUDE.md pending rule); this tester returns records, it does not persist them yet",
        }

    # --- the one capability: prove and attest -------------------------------

    def run_proof(self, proof_path, *, caller: str | None = None, timeout: int = 120) -> dict:
        """Run ``proof_path`` as a subprocess; produce a VALIDATION of the outcome.

        The verdict is the subject's exit code (0 → green, else red) — read, not
        granted. Returns the ratified eight-field record; does not persist it (the
        store is a later stone).
        """
        proof_path = Path(proof_path)
        try:
            proc = subprocess.run(
                [sys.executable, str(proof_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            verdict = GREEN if proc.returncode == 0 else RED
            evidence = {
                "returncode": proc.returncode,
                "stdout_tail": _tail(proc.stdout),
                "stderr_tail": _tail(proc.stderr),
            }
        except subprocess.TimeoutExpired:
            # A proof that hangs is a red, not a crash of the notary (CP1: say what
            # happened — we measured a timeout, we did not measure a pass).
            verdict = RED
            evidence = {"returncode": None, "stdout_tail": "", "stderr_tail": f"timed out after {timeout}s"}

        record = self._validation(
            claim=f"proof {proof_path.name} passes under {Path(sys.executable).name}",
            caller=caller or self._device_id,
            method="ran the proof as a subprocess; verdict = exit code (0 → green, else red)",
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

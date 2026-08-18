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
    runs the subject inside a measured seal (``cairn/devices/tester/isolation.py``) and folds
    the seal's verdict into the record's ``method`` + ``evidence`` — no ninth field.
    The seal is measured from inside, never assumed; an unconfirmable seal is
    INDETERMINATE and does not earn a green on the strength of its isolation.

FRESH design, mechanism grafted (like device.py/shim.py were redesigns): UU's tester
(``unseen_university/devices/tester/`` — netpolicy 381 + isolation 183 + sandbox +
seal) is the quarry. The seal's OS plumbing crosses nearly literally (kernel truth);
its design and the programmable Router (fixture/refuse/forward) do not — see
``isolation.py`` for the graft-vs-fresh ruling and the deferred Router.

CLOSED EDGE (2026-07-22): VALIDATIONS are now **persisted**. The durable greppable home is
``cairn/devices/tester/validation_store.py`` — beside-code git-JSON, next to the ``proofs/`` each one
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

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from cairn.tools.base.device import BaseDevice
from cairn.devices.tester.isolation import (
    INDETERMINATE, OPEN, Seal, bwrap_available, check_instance_seal, get_isolation,
    snapshot_instance_space,
)

GREEN = "green"
RED = "red"

# WHERE A VALIDATION GOES, named at every call site. Two values, because two are what the
# corpus needs: seal through the store's door, or write nothing. There is deliberately no
# third for artifact addressing — quorum.py composes persist_validation directly for that,
# and build-minimal says a vocabulary grows against a need, not toward a symmetry.
_SINKS = frozenset({"validations", "none"})

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


# How many written paths ride in the record before it is summarised. A proof that writes
# thousands of files has said what it needs to say in the first few dozen, and a VALIDATION
# is read by a mind — but the COUNT is never capped, so the cap can never hide the scale.
_WRITES_LISTED = 40


def _manifest(root: str) -> dict:
    """``{relative path: (size, mtime_ns)}`` for every regular file under ``root``.

    Size+mtime rather than a hash: it is ~200x cheaper across 872 files and this is taken
    twice per proof. The failure mode it cannot see — a rewrite to the identical size within
    the same nanosecond — is not a failure mode that produces a *misleading* answer, because
    a proof that rewrote a file byte-identically seeded nothing.
    """
    out = {}
    base = Path(root)
    for p in base.rglob("*"):
        if p.is_symlink() or not p.is_file():
            continue
        try:
            st = p.stat()
        except OSError:
            continue  # vanished between walk and stat — nothing to compare, and not a write
        out[str(p.relative_to(base))] = (st.st_size, st.st_mtime_ns)
    return out


def _instance_writes(swap: str | None, before: dict | None) -> dict:
    """What the subject wrote into the sealed instance world — the seal's free measurement.

    This is the answer to a question that had no instrument before the seal existed: *does
    this proof write to instance-space, and where?* It costs one directory walk, because the
    swap must be held for the run anyway. An unsealed run answers ``null`` rather than ``[]``
    — CP1: "we did not measure" and "we measured zero" are different facts, and collapsing
    them is how an unsealed run comes to read like a clean one.
    """
    if swap is None or before is None:
        return {"measured": False, "why": "the run was not sealed, so its writes went "
                                          "un-witnessed — this is not a claim that it wrote nothing"}
    after = _manifest(swap)
    changed = sorted(k for k, v in after.items() if before.get(k) != v)
    return {
        "measured": True,
        "count": len(changed),
        "paths": changed[:_WRITES_LISTED],
        "elided": max(0, len(changed) - _WRITES_LISTED),
    }


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
        # Honest, live condition — no faked node-state vocabulary (``PROVED``, the one
        # rest since ticket watchme-emits-a-probe dissolved the second one on 2026-07-30,
        # lands with the emit-chokepoint; not wired here yet).
        return {
            "proofs_run": self._proofs_run,
            "last_verdict": self._last_verdict,  # None until it has run one
        }

    def settings(self) -> dict:
        return {
            "interpreter": Path(sys.executable).name,
            "isolation": "owned — run_proof takes isolation='netns' to run under a measured "
            "seal (cairn/devices/tester/isolation.py); default 'none' (bare) must be asked for by name. "
            "The chosen-route Router (serve/refuse/forward) is deferred to db/inference domains.",
            "validations_sink": "beside-code git-JSON — validation_store.py persists each "
            "VALIDATION to validations/<stem>.json next to the proofs/ it seals (Law 5). "
            "run_proof takes a REQUIRED sink ('validations' | 'none') and, when told to seal, "
            "persists through persist_validation — the store's door, never around it. It was "
            "state-free with no sink at all until 2026-08-16, and that is exactly what made "
            "writing around the door attractive (ticket standing-gates-the-newest-link-and-"
            "run-proof-names-its-sink): every caller had to remember the door on its own, and "
            "six trails' worth of callers did not.",
        }

    # --- the one capability: prove and attest -------------------------------

    def run_proof(
        self,
        proof_path,
        *,
        sink: str,
        caller: str | None = None,
        timeout: int = 120,
        isolation: str = "none",
    ) -> dict:
        """Run ``proof_path`` as a subprocess; produce a VALIDATION of the outcome.

        The verdict is the subject's exit code (0 → green, else red) — read, not
        granted. With ``isolation="netns"`` the subject runs inside a measured network
        seal (``cairn/devices/tester/isolation.py``): the seal is probed from inside and its
        verdict is folded into the record's ``method`` + ``evidence`` — never a ninth
        field. An unconfirmable seal is INDETERMINATE and is reported as such, not
        laundered into a green. Returns the ratified eight-field record.

        ``sink`` IS REQUIRED AND HAS NO DEFAULT, which is the whole point of it (ticket
        standing-gates-the-newest-link-and-run-proof-names-its-sink, 2026-08-16):

          - ``"validations"`` — persist the record through ``persist_validation``, the
            store's single write door, beside the proof it seals.
          - ``"none"`` — write nothing; return the record and let the caller decide.

        Until this existed, run_proof produced the ratified record and DROPPED it, so every
        caller had to independently remember the door — and the callers who forgot are how
        six trails came to hold seven entries that never came through it. A DEFAULTED sink
        would have preserved that exactly: the caller who forgets is the caller who gets the
        default. Requiring it makes the choice appear at the call site, where the reader is.

        run_proof MINTS NOTHING. Sealing is the door's act, and this hands it the same
        eight-field record it hands back to the caller — nothing composed on the way in.
        """
        if sink not in _SINKS:
            raise ValueError(
                f"run_proof: sink={sink!r} is not one of {sorted(_SINKS)} — a sink is named, "
                f"never guessed. Use 'validations' to seal through persist_validation, or "
                f"'none' to run the proof and write nothing.")
        # Resolve to an absolute path BEFORE anything downstream uses proof_path.parent
        # as a cwd. The netns seal runs the subject under `bwrap --chdir <parent>`, and a
        # RELATIVE parent resolves against the namespace root (/), not the host cwd — so a
        # relative call silently breaks the chdir, failing the proof (false RED) and
        # downgrading the seal to INDETERMINATE. The seal must be measured the same way no
        # matter how the caller spelled the path (Law 4: the guarantee is physics, not a
        # "remember to pass an absolute path" convention).
        proof_path = Path(proof_path).resolve()
        iso = get_isolation(isolation)

        # Measure the seal before trusting it (isolation.py: measured, never assumed).
        # NoIsolation reports OPEN with no subprocess; netns probes from inside.
        available, why = iso.available()
        if iso.seals_network and not available:
            seal = Seal("indeterminate", f"seal '{iso.name}' unavailable: {why}")
        else:
            seal = iso.check_seal(str(proof_path.parent))

        # WHAT WAS PROVED, pinned. The record already PROMISES a horizon — "valid until the
        # proof file or the code it proves changes" — and for three weeks nothing could check
        # it, because the record carried no description of the code it was about. This is that
        # description: one sha256 over the component's *.py, taken BEFORE the run so it
        # describes the tree the subject actually executed. It rides inside `evidence`, never
        # as a ninth field (the eight are ratified). Lazy import: validation_store imports this
        # module for VALIDATION_FIELDS, so the dependency only runs one way at import time.
        from cairn.devices.tester.validation_store import source_fingerprint
        fingerprint = source_fingerprint(str(proof_path))

        # THE INSTANCE SEAL — ALWAYS ON, AND DELIBERATELY NOT A PARAMETER (ticket
        # a-proof-cannot-seed-the-tree-it-reads). Every other knob on this method is named at
        # the call site because a reader should see the choice; this one is not a choice. The
        # network seal can honestly be declined — a proof that needs no network loses nothing
        # by running bare. Declining THIS seal has no upside to trade against: it only lets a
        # proof write into the store every later measurement is read from. So there is no
        # `instance=` argument to forget, and no exemption roster to adjudicate at the moment
        # someone is least equipped to (the same reasoning bin/cmd/deletegate carries).
        #
        # The swap is a full copy of the live instance root, so READS answer exactly as they
        # would on the host and only WRITES are discarded — see isolation.py for why an empty
        # room was the wrong shape and which seven proofs measured that.
        swap = probe_swap = None
        before = None
        try:
            available, why = bwrap_available()
            if not available:
                instance_seal = Seal(
                    INDETERMINATE,
                    f"cannot build the instance seal: {why} — this run MAY have written to the "
                    f"live instance root, and the record says so rather than implying it did not")
            else:
                # Two swaps, not one: the probe writes a marker to prove the seal holds, and a
                # marker sitting in the subject's world would show up in `wrote_to_instance`
                # as something the proof did. An instrument that contaminates its own reading
                # is the defect this whole seal exists to remove — at n=1 it would be a
                # footnote, and a footnote is how it survives to n=100.
                probe_swap = snapshot_instance_space()
                instance_seal = check_instance_seal(iso, probe_swap, str(proof_path.parent))
                if instance_seal.sealed:
                    swap = snapshot_instance_space()
                    before = _manifest(swap)

            argv = iso.wrap([sys.executable, str(proof_path)],
                            cwd=str(proof_path.parent), instance_swap=swap)
            base_evidence = {
                "seal": {"verdict": seal.verdict, "detail": seal.detail},
                "source_fingerprint": fingerprint,
            }
            try:
                proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
                verdict = GREEN if proc.returncode == 0 else RED
                evidence = {
                    "returncode": proc.returncode,
                    "stdout_tail": _tail(proc.stdout),
                    "stderr_tail": _tail(proc.stderr),
                    **base_evidence,
                }
            except subprocess.TimeoutExpired:
                # A proof that hangs is a red, not a crash of the notary (CP1: say what
                # happened — we measured a timeout, we did not measure a pass).
                verdict = RED
                evidence = {
                    "returncode": None,
                    "stdout_tail": "",
                    "stderr_tail": f"timed out after {timeout}s",
                    **base_evidence,
                }
            # WHAT THE PROOF WROTE, kept as a measurement rather than thrown away with the
            # swap. Before this, "does this proof write to instance-space?" was a question
            # nobody could answer without instrumenting by hand; now every run answers it for
            # free, because the seal already has to hold the writes somewhere to discard them.
            evidence["instance_seal"] = {
                "verdict": instance_seal.verdict,
                "detail": instance_seal.detail,
                "wrote_to_instance": _instance_writes(swap, before),
            }
        finally:
            for tmp in (swap, probe_swap):
                if tmp:
                    shutil.rmtree(Path(tmp).parent, ignore_errors=True)

        # The method names HOW the verdict was reached AND how trustworthy the seal
        # under it is — so a reader sees seal-backing without opening the evidence.
        seal_note = f"seal={seal.verdict}" if seal.verdict != OPEN else "unsealed (isolation='none')"
        record = self._validation(
            claim=f"proof {proof_path.name} passes under {Path(sys.executable).name}",
            caller=caller or self._device_id,
            method=f"ran the proof as a subprocess ({seal_note}, instance-seal="
                   f"{instance_seal.verdict}); verdict = exit code (0 → green, else red)",
            verdict=verdict,
            evidence=evidence,
            falsifier="the same proof exits non-zero on re-run, or the code it proves changes underneath it",
            horizon="valid until the proof file or the code it proves changes (Law 3: a VALIDATION expires)",
        )
        if sink == "validations":
            # THROUGH THE DOOR, and only through it. persist_validation decides what lands
            # and announces a changed verdict before it does; nothing here writes bytes, which
            # is what keeps the store's "one write door" true while giving run_proof a way to
            # seal at all.
            # Lazy import for the same reason as source_fingerprint above: validation_store
            # imports this module, so the dependency only runs one way at import time.
            from cairn.devices.tester.validation_store import persist_validation
            persist_validation(record, proof_path=str(proof_path))
        self._proofs_run += 1
        self._last_verdict = verdict
        # GATE CONTACT (DiagnosticBase): the notary ACTED — a proof ran and a verdict was
        # attested. One breadcrumb per run (the crossing), red or green alike: a red is not
        # an anomaly of the notary, it is the notary working. Thin: pointer is the proof;
        # values are the two facts a reader wants without opening the eight-field record
        # (which the caller holds and the store persists — the record of truth is not here).
        self.emit("run_proof", pointer=str(proof_path),
                  values={"verdict": verdict, "seal": seal.verdict})
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

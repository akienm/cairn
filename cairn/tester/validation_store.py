"""tester/validation_store.py — a VALIDATION lands as git-JSON BESIDE THE PROOF it seals.

The tester is the one hand that both proves and attests (Law 4). What it attests — the
VALIDATION — is build-provenance, frozen at PROVED: knowledge, not runtime state. So it
belongs beside the code it explains, in git, greppable (Law 5: intent, its voyage, AND
its proofs share an address; ruling in tickets/charter-state-history-split.json child b).
This module is that durable sink — the beside-code home that replaces the Postgres
`validations` table db_domain used to own. The database keeps only the graph trees.

Placement, by construction: a proof at ``.../<component>/proofs/<stem>.py`` seals into
``.../<component>/validations/<stem>.json`` — a ``validations/`` directory that is the peer
of ``proofs/``, one append-only file per proof. So a proof's seal-history sits one directory
over from the proof, and a mind greps ``validations/`` on a hunch rather than re-proving
(Law 1 — the answered proof becomes structure).

APPEND-ONLY (Law 7, the shape history and db_domain's INSERT-only store already carry). A
VALIDATION expires (Law 3: it rides a falsifier + horizon), so re-running a proof does not
overwrite the old seal — it APPENDS a fresh dated one. The file is the seal's whole voyage;
the newest entry is the current verdict. There is no update-in-place and no delete, because
a record of truth has neither. The single write-door is ``persist_validation``.

FIELD-SET IS PHYSICS, not convention (mirrors the Postgres CHECK it replaces): a record that
is not exactly the ratified eight fields is REFUSED here, so a drifted validation cannot land
beside the code and quietly pass for a seal.
"""

from __future__ import annotations

import json
import os
import tempfile

from cairn.tester.device import VALIDATION_FIELDS


def validations_path_for(proof_path: str) -> str:
    """The beside-code validations file for a proof: ``proofs/<stem>.py`` -> ``validations/<stem>.json``.

    Derived purely from the proof's path so the seal always lands beside the thing it seals;
    the caller never picks the location, which is what keeps the co-location honest (Law 5).
    """
    proofs_dir = os.path.dirname(os.path.abspath(proof_path))
    component_dir = os.path.dirname(proofs_dir)  # the component root, one up from proofs/
    stem = os.path.splitext(os.path.basename(proof_path))[0]
    return os.path.join(component_dir, "validations", f"{stem}.json")


def read_validations(proof_path: str | None = None, *, path: str | None = None) -> list[dict]:
    """Grep the seal trail for a proof — the evidence a hunch consults before re-deriving.

    Give either the proof (its validations file is derived) or the file path directly.
    Returns the append-only list, oldest first; an empty list if nothing has sealed yet.
    """
    if path is None:
        if proof_path is None:
            raise ValueError("read_validations needs either proof_path or path")
        path = validations_path_for(proof_path)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _atomic_write(path: str, data) -> None:
    """Write JSON via temp-file + rename, so a reader never sees a half-written trail."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def persist_validation(validation: dict, *, proof_path: str) -> str:
    """The single write-door: APPEND one VALIDATION to the trail beside ``proof_path``.

    Refuses a record that is not exactly the ratified eight fields (drift is not a seal).
    Appends — never overwrites — because the trail is a record of truth (Law 7) and a
    re-run's verdict is a NEW dated entry, not a replacement (Law 3). Returns the file path.
    """
    got = set(validation)
    if got != set(VALIDATION_FIELDS):
        raise ValueError(
            f"a VALIDATION carries exactly the ratified eight fields {sorted(VALIDATION_FIELDS)}; "
            f"got {sorted(got)} — a drifted record is refused, it is not a seal (Law 7)"
        )
    path = validations_path_for(proof_path)
    trail = read_validations(path=path)
    trail.append(dict(validation))
    _atomic_write(path, trail)
    return path

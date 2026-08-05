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

THE READ SIDE (2026-08-05, when MethodRegistry was ripped out). For three weeks this store
had 73 trails on disk and ZERO readers — every seal was written and none was ever consulted,
so "is this proven?" was answered elsewhere, by an in-memory registry holding a second copy.
``standing`` is the reader that makes the copy unnecessary: the proof's own address IS the
key (``validations_path_for`` derives it), so proven-space is a traversal, not a lookup table
someone has to populate and keep (Law 6 — the fact attaches at its endpoint).

And the reader enforces the HORIZON the cache could not. Every VALIDATION already promises
"valid until the proof file or the code it proves changes (Law 3: a VALIDATION expires)" —
a promise nothing checked. ``source_fingerprint`` makes it checkable: one sha256 over every
``*.py`` under the component root, which is exactly the scope the horizon names (the proof
file AND the code it proves). The tester records it at seal time; ``standing`` recomputes it
at read time. A seal whose fingerprint no longer matches is EXPIRED, not green — the code
moved under it, which is the whole content of the horizon.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile

from cairn.tester.device import GREEN, VALIDATION_FIELDS


def validations_path_for(proof_path: str) -> str:
    """The beside-code validations file for a proof: ``proofs/<stem>.py`` -> ``validations/<stem>.json``.

    Derived purely from the proof's path so the seal always lands beside the thing it seals;
    the caller never picks the location, which is what keeps the co-location honest (Law 5).
    """
    proofs_dir = os.path.dirname(os.path.abspath(proof_path))
    component_dir = os.path.dirname(proofs_dir)  # the component root, one up from proofs/
    stem = os.path.splitext(os.path.basename(proof_path))[0]
    return os.path.join(component_dir, "validations", f"{stem}.json")


def validations_path_for_artifact(artifact_path: str) -> str:
    """The validations file for an artifact that has no proof file: ``<dir>/x.md`` ->
    ``<dir>/validations/x.json``.

    A concept-piece is proved by people reading it, so there is no ``proofs/`` directory to
    derive an address from — and until 2026-07-25 that meant the single write-door could not
    accept one at all, which is why no concept-piece had ever been sealed. The address is still
    DERIVED, never chosen by the caller: the seal lands beside the artifact it seals, so intent
    and proof keep one address (Law 5).
    """
    directory = os.path.dirname(os.path.abspath(artifact_path))
    stem = os.path.splitext(os.path.basename(artifact_path))[0]
    return os.path.join(directory, "validations", f"{stem}.json")


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


def component_root_for(proof_path: str) -> str:
    """The component a proof belongs to: ``.../<component>/proofs/<stem>.py`` -> ``.../<component>``.

    The same derivation ``validations_path_for`` uses, named once so the seal's address and the
    seal's SCOPE cannot drift apart — a fingerprint taken over a different tree than the one the
    validation files under would expire for reasons no reader could explain."""
    return os.path.dirname(os.path.dirname(os.path.abspath(proof_path)))


def source_fingerprint(proof_path: str) -> str:
    """One sha256 over every ``*.py`` under the proof's component root — the horizon, made checkable.

    SCOPE IS THE HORIZON'S OWN WORDING: "valid until the proof file OR THE CODE IT PROVES
    changes." Hashing only the proof would miss the likelier drift by far (code edited, proof
    untouched), so the walk covers the whole component — proof included, since it lives there.

    Path AND content go into the digest, so a rename or a deletion moves the number as surely
    as an edit does; a file that vanished cannot be an unnoticed change. Sorted by relative
    path, so the digest is deterministic across filesystems.

    Deliberately NOT git: a seal must expire the moment the working tree diverges, not when
    someone commits. An uncommitted edit is exactly the state where a stale green does harm.
    """
    root = component_root_for(proof_path)
    digest = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            full = os.path.join(dirpath, name)
            digest.update(os.path.relpath(full, root).encode("utf-8"))
            digest.update(b"\0")
            with open(full, "rb") as f:
                digest.update(f.read())
            digest.update(b"\0")
    return digest.hexdigest()


def standing(proof_path: str) -> dict:
    """Is this proof's code in proven-space RIGHT NOW? The reader that replaced MethodRegistry.

    Returns ``{"proven": bool, "why": str, "seal": dict | None}``. ``why`` is a complete
    sentence naming what was looked at and what was found, because the one consumer turns a
    False straight into a refusal a human has to act on
    (I-complete-diagnostic-on-first-pass — no second call to find out which of the four
    reasons it was).

    Four outcomes, and only the first is proven-space:
      - sealed green, fingerprint matches      -> proven
      - never sealed                           -> not proven (the trail does not exist)
      - newest seal is red                     -> not proven (it was measured and it failed)
      - sealed green, fingerprint has moved    -> NOT PROVEN, the horizon closed. This is the
        one an in-memory registry could not reach: it cached a bool with no expiry, so it kept
        answering yes after the code changed underneath it (Law 3 — a VALIDATION expires).

    The NEWEST entry is the verdict; the trail is append-only, so an old green under a newer
    red is history, not standing.
    """
    trail = read_validations(proof_path)
    if not trail:
        return {"proven": False, "seal": None, "why": (
            f"no VALIDATION has ever sealed {proof_path} — the trail at "
            f"{validations_path_for(proof_path)} does not exist. Proven-space is the tester's "
            f"and it has not spoken about this code (Law 8)")}
    seal = trail[-1]
    if seal.get("verdict") != GREEN:
        return {"proven": False, "seal": seal, "why": (
            f"the newest seal on {proof_path} is {seal.get('verdict')!r}, dated "
            f"{seal.get('date')} — the code was measured and it did not pass")}
    recorded = (seal.get("evidence") or {}).get("source_fingerprint")
    if recorded is None:
        return {"proven": False, "seal": seal, "why": (
            f"the newest seal on {proof_path} is green, dated {seal.get('date')}, but records "
            f"no source_fingerprint — so whether the code still matches what was proved is "
            f"UNKNOWABLE from the trail. Unknown is not green (Law 9). Re-run the proof to "
            f"seal a fingerprint")}
    current = source_fingerprint(proof_path)
    if current != recorded:
        return {"proven": False, "seal": seal, "why": (
            f"the newest seal on {proof_path} is green, dated {seal.get('date')} — and its "
            f"HORIZON HAS CLOSED: the component's source fingerprint was "
            f"{recorded[:12]}… when it was sealed and is {current[:12]}… now, so the code moved "
            f"under the proof. Re-run the proof (Law 3: a VALIDATION expires)")}
    return {"proven": True, "seal": seal, "why": (
        f"sealed green {seal.get('date')} by {seal.get('caller')}, and the component's source "
        f"fingerprint still matches what was proved ({recorded[:12]}…)")}


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


def persist_validation(
    validation: dict, *, proof_path: str | None = None, artifact_path: str | None = None
) -> str:
    """The single write-door: APPEND one VALIDATION to the trail beside what it seals.

    Give ``proof_path`` for a node proved by a tester run, or ``artifact_path`` for one proved
    by human judgment (a concept-piece — see ``cairn/tester/quorum.py``). Exactly one: the
    address is always derived, never chosen, and a caller who names both has not decided what
    it is sealing.

    Refuses a record that is not exactly the ratified eight fields (drift is not a seal).
    Appends — never overwrites — because the trail is a record of truth (Law 7) and a
    re-run's verdict is a NEW dated entry, not a replacement (Law 3). Returns the file path.
    """
    if (proof_path is None) == (artifact_path is None):
        raise ValueError(
            "persist_validation seals EITHER a proof (proof_path) or a human-proved artifact "
            f"(artifact_path) — got proof_path={proof_path!r}, artifact_path={artifact_path!r}. "
            "One door, two addressing rules, and the caller picks which by naming one.")
    got = set(validation)
    if got != set(VALIDATION_FIELDS):
        raise ValueError(
            f"a VALIDATION carries exactly the ratified eight fields {sorted(VALIDATION_FIELDS)}; "
            f"got {sorted(got)} — a drifted record is refused, it is not a seal (Law 7)"
        )
    path = (
        validations_path_for(proof_path) if proof_path is not None
        else validations_path_for_artifact(artifact_path)
    )
    trail = read_validations(path=path)
    trail.append(dict(validation))
    _atomic_write(path, trail)
    return path

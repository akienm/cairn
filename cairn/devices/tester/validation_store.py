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

AND THE DOOR IS NOW THE ONLY PATH — BY PHYSICS, IN TWO LAYERS (2026-08-05, ticket
validation-store-door-is-the-only-path, drained from a live trouble). Until today the
door's guarantee rested on everyone remembering to use it: the trail was a plain 0644 JSON
file, so ``json.dump(fresh, open(path, "w"))`` from anywhere destroyed a proof's entire seal
history *silently and permanently*, and the result looked exactly like a fresh seal. Law 7's
worst direction. The two layers answer two different failure modes and neither substitutes
for the other:

  - THE MODE BIT stops the accident. A written trail is dropped to 0444, so the naive
    overwrite raises PermissionError at the ``open`` instead of succeeding. The door still
    writes because ``os.replace`` needs the DIRECTORY, not the file.
  - THE CHAIN makes the deliberate loud and permanent. Every record carries a ``trail_link``
    minted HERE — a sha256 over the whole trail beneath it plus the record itself. Only this
    door mints one, so a record that lacks a link, or whose link no longer matches what is
    under it, did not come through the door and ``standing`` refuses the whole trail rather
    than reading a verdict out of it. A hand-write can no longer pass for a seal, which is the
    exact sentence the trouble used to describe the defect.

  - AND NO SECOND WRITER EXISTS IN THE CORPUS, checked at build time by a proof tooth that
    censuses every module for a write aimed at a ``validations/`` address. The two layers
    above catch a bypass that already ran; this one refuses the bypass being BUILT.

The 73 trails that predated links were ADOPTED (``adopt_chain``) rather than tolerated. The
first draft tolerated an unlinked leading prefix as "prehistory", and its own proof killed
that in one firing: an overwrite that drops every link is then indistinguishable from a legacy
trail — and a total overwrite is exactly the destroy-the-history shape the trouble described.
A tolerance is a forger's costume whenever the forger can produce the thing being tolerated.
What a retro-minted link honestly claims is narrower, and is stated rather than glossed: it
attests the trail's content AS OF ADOPTION, not as of each entry's sealing.

What none of it claims: the bytes are not unwritable to a caller running as the same uid, and
nothing here can un-destroy a trail. That is what git is for — the trail is a committed file,
so a destroyed history is recoverable, and the chain is what tells you to go recover it.

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

from cairn.devices.tester.device import GREEN, VALIDATION_FIELDS

# The one key inside `evidence` that belongs to the DOOR and not to the caller. It rides
# inside evidence rather than becoming a ninth field because the eight are ratified.
TRAIL_LINK = "trail_link"


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
    # THE TRAIL'S OWN INTEGRITY IS CHECKED BEFORE ITS CONTENT. A verdict read out of a
    # trail that was written around the door is not a measurement of anything — and this
    # is the surface where that matters, because harbor_master turns a True here straight
    # into a crossing's clearance. Broken chain, no clearance (Law 8).
    breaks = verify_trail(trail)
    if breaks:
        return {"proven": False, "seal": trail[-1] if trail else None, "why": (
            f"the seal trail at {validations_path_for(proof_path)} DID NOT COME WHOLE THROUGH "
            f"persist_validation — {len(breaks)} break(s): " + "; ".join(breaks) +
            ". A record of truth that was written around its own door proves nothing about the "
            "code; what it proves is that something else has been writing here. Recover the "
            "trail from git and re-run the proof")}
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


def _canonical(obj) -> bytes:
    """One spelling for one value — sorted keys, no incidental whitespace.

    A digest over JSON is only a digest over the VALUE if the encoding is fixed; otherwise
    re-indenting the file would 'break' the chain and a real tamper could hide behind the
    same excuse. This is the fixed encoding, used for nothing else.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def chain_digest(prefix: list) -> str:
    """The digest of everything already on the trail — what the next link commits to."""
    return hashlib.sha256(_canonical(prefix)).hexdigest()


def _link_for(prefix: list, record: dict) -> str:
    """This record's link: sha256(everything before it, then the record itself sans link).

    The record is hashed WITHOUT its own link, because a value cannot contain its own digest.
    """
    body = dict(record)
    body["evidence"] = {k: v for k, v in (body.get("evidence") or {}).items()
                        if k != TRAIL_LINK}
    return hashlib.sha256(
        chain_digest(prefix).encode("ascii") + b"\0" + _canonical(body)).hexdigest()


def verify_trail(trail: list) -> list[str]:
    """Complaints about a trail's chain — empty means EVERY entry still carries a valid link.

    NO PREHISTORY CLAUSE, and that is a decision the first draft got wrong. Tolerating
    unlinked entries as a leading PREFIX seemed like the honest way to carry the 73 trails
    that predated links — but the proof found the hole in one firing: a total overwrite that
    drops every link is then indistinguishable from a legacy trail, and a total overwrite is
    exactly the destroy-the-whole-history shape the trouble described. A tolerance is a
    forger's costume whenever the forger can produce the thing being tolerated.

    So the legacy trails were ADOPTED instead (``adopt_chain``), once, and from then on a
    missing link is a break like any other. What adoption honestly claims is narrower than a
    seal-time link and is written down rather than glossed: a retro-minted link attests the
    trail's content AS OF ADOPTION, not as of the moment each entry was sealed. Nothing can
    attest the latter after the fact, and pretending otherwise would be the same costume.

    Returns complaints rather than raising, because the caller decides the surface: the
    reader turns them into a refusal, a diagnostic prints them (Law 7 — loud where it
    diagnoses, and the record itself is never rewritten to look clean).
    """
    complaints = []
    for i, rec in enumerate(trail):
        if not isinstance(rec, dict):
            complaints.append(f"entry {i} is a {type(rec).__name__}, not a VALIDATION record")
            continue
        link = (rec.get("evidence") or {}).get(TRAIL_LINK)
        if link is None:
            complaints.append(
                f"entry {i} ({rec.get('date')}, {rec.get('verdict')}) carries no {TRAIL_LINK} — "
                f"persist_validation is the only hand that mints one, so a record without a link "
                f"did not come through the door")
            continue
        expected = _link_for(trail[:i], rec)
        if link != expected:
            complaints.append(
                f"entry {i} ({rec.get('date')}, {rec.get('verdict')}) carries link "
                f"{str(link)[:12]}… but the trail beneath it hashes to {expected[:12]}… — either "
                f"this entry or something before it was changed after it was sealed")
    return complaints


def adopt_chain(path: str) -> int:
    """ONE-TIME ADOPTION: mint links over a trail written before links existed. Returns how
    many entries it linked (0 = already fully chained, so it is safe to re-run).

    Not a repair tool and deliberately not usable as one: an entry that ALREADY carries a
    link which no longer verifies makes this refuse the whole file. A break is a finding to
    act on — recover the trail from git — and a migration that quietly re-linked a tampered
    trail would erase precisely the evidence the chain exists to preserve (Law 7).
    """
    trail = read_validations(path=path)
    for i, rec in enumerate(trail):
        link = (rec.get("evidence") or {}).get(TRAIL_LINK) if isinstance(rec, dict) else None
        if link is not None and link != _link_for(trail[:i], rec):
            raise ValueError(
                f"{path} entry {i} carries a link that does not verify — this is a BREAK, not an "
                "unadopted trail. adopt_chain will not overwrite it; recover from git.")
    minted = 0
    for i, rec in enumerate(trail):
        if not isinstance(rec, dict) or not isinstance(rec.get("evidence"), dict):
            raise ValueError(f"{path} entry {i} is not a VALIDATION record with dict evidence")
        if TRAIL_LINK in rec["evidence"]:
            continue
        rec["evidence"][TRAIL_LINK] = _link_for(trail[:i], rec)
        minted += 1
    if minted:
        _atomic_write(path, trail)
    return minted


def _atomic_write(path: str, data) -> None:
    """Write JSON via temp-file + rename, then drop the file to read-only.

    THE MODE BIT IS THE CHEAP HALF OF THE GATE (2026-08-05, ticket
    validation-store-door-is-the-only-path). A record of truth declared append-only was a
    plain 0644 JSON file, so ``json.dump(trail, open(path, "w"))`` from anywhere destroyed a
    proof's whole seal history and looked exactly like a fresh seal. At 0444 that call raises
    PermissionError at the open — the ORDINARY bypass, the one nobody intended, stops being
    possible rather than being detected afterwards.

    It does not stop a deliberate one (same uid can chmod), and it is not meant to: that is
    the chain's job, above. The two halves answer different failure modes — accident and
    forgery — and neither substitutes for the other.

    RESIDUE, stated because git cannot carry it: git tracks only the executable bit, so a
    fresh clone lands these files at 0644 and they are unprotected until the door next
    appends. The mode is a property of the working tree, not of the record. The chain is the
    half that survives a clone.
    """
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.chmod(tmp, 0o444)
        os.replace(tmp, path)  # rename over a read-only file needs the DIRECTORY, not the file
    except BaseException:
        if os.path.exists(tmp):
            os.chmod(tmp, 0o644)
            os.remove(tmp)
        raise


def persist_validation(
    validation: dict, *, proof_path: str | None = None, artifact_path: str | None = None
) -> str:
    """The single write-door: APPEND one VALIDATION to the trail beside what it seals.

    Give ``proof_path`` for a node proved by a tester run, or ``artifact_path`` for one proved
    by human judgment (a concept-piece — see ``cairn/devices/tester/quorum.py``). Exactly one: the
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
    evidence = validation.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError(
            f"a VALIDATION's `evidence` is a structure, not a blob — got {type(evidence).__name__}. "
            "The door mints the trail link INSIDE evidence (the eight fields are ratified and it "
            "may not become a ninth), so a non-dict evidence has nowhere to carry its own seal.")
    if TRAIL_LINK in evidence:
        raise ValueError(
            f"the caller supplied {TRAIL_LINK!r} — the link is MINTED BY THIS DOOR and by nothing "
            "else. A record arriving with one pre-filled is either a replay of an existing entry "
            "or a hand-built forgery; in both cases the door is not the hand that sealed it "
            "(Law 6: the owner alone gates writes).")
    path = (
        validations_path_for(proof_path) if proof_path is not None
        else validations_path_for_artifact(artifact_path)
    )
    trail = read_validations(path=path)
    record = dict(validation)
    # THE LINK COMMITS TO EVERYTHING BENEATH IT — including a prehistory written before links
    # existed. Minted here, at the one door, which is what makes its absence evidence.
    record["evidence"] = dict(evidence, **{TRAIL_LINK: _link_for(trail, record)})
    trail.append(record)
    _atomic_write(path, trail)
    return path

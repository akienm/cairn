"""tester/validation_store.py — a VALIDATION lands as git-JSON BESIDE THE PROOF it seals.

The tester is the one hand that both proves and attests (Law 4). What it attests — the
VALIDATION — is build-provenance, frozen at PROVED: knowledge, not runtime state. So it
belongs beside the code it explains, in git, greppable (Law 5: intent, its voyage, AND
its proofs share an address; ruling in tickets/charter-state-history-split.json child b).
This module is that durable sink — the beside-code home that replaces the Postgres
`validations` table db_domain used to own. The database keeps only the graph trees.

Placement, by construction: a proof at ``.../<component>/proofs/<stem>.py`` seals into
``.../<component>/validations/<stem>.json`` — a ``validations/`` directory that is the peer
of ``proofs/``, one file per proof. So a proof's seal sits one directory over from the proof,
and a mind greps ``validations/`` on a hunch rather than re-proving (Law 1 — the answered
proof becomes structure).

ONE CURRENT RECORD PER PROOF — NOT A TRAIL (2026-08-16, ticket
a-validation-is-one-current-record-not-a-trail). Akien's ruling bore it: *"the validation is
a single record. so is the preceeding one. so a ticket should accumulate them? and all we
need to keep of a proof is enough data to verify it. So do we need it's whole history? no,
in fact it tends to create noise. now where should we draw that line?"* The line he asked for
already existed in this module and had been paid for: ``source_fingerprint``, one sha256 over
every ``*.py`` under the component root. That IS "enough data to verify it" — it says whether
the code still matches what was proved, which is the only question ``standing`` ever asks. A
re-run therefore REPLACES; the file holds exactly one record. What was lost by keeping the
rest is measurable and was measured: of 90 trails, 54 held more than one entry and 52 of
those held nothing but re-runs agreeing with themselves — noise, in his word, and a reader
scrolling past it to reach the entry it would have read anyway.

WHAT REPLACES A RECORD OF TRUTH MUST MAKE THE ERROR LOUDER, NOT QUIETER, and that is the
whole of Law 7's claim on this design. A presentation surface may collapse an error into a
coherent shape; a record of truth may not — and replacing an entry IS collapsing it. So the
collapse ships WITH its door: ``verdict_change`` asks whether the incoming verdict differs
from the standing one, and ``announce_verdict_change`` fires that difference out through
``TroubleDevice`` BEFORE the replace lands. The change is now louder than it was under
append: appended, it sat at an index of a file with three readers, all of which took the last
entry, and in the one measured case it went unread for eight days. Announced, it reaches the
SessionStart banner a human meets before anything else. And the superseded record is not
destroyed — it is one commit back in git, where every one of these files lives.

THE DOOR IS STILL THE ONLY PATH, and what enforces that is now stated honestly rather than
generously (MEASURED 2026-08-16, and the measurement retired a layer):

  - THE MODE BIT stops the accident. A written record is dropped to 0444, so a naive
    ``json.dump(fresh, open(path, "w"))`` raises PermissionError at the ``open`` instead of
    succeeding. The door still writes because ``os.replace`` needs the DIRECTORY, not the file.
  - NO SECOND WRITER EXISTS IN THE CORPUS, checked at build time by a proof tooth that
    censuses every module for a write aimed at a ``validations/`` address. The mode bit
    catches a bypass that already ran; this one refuses the bypass being BUILT.
  - THE SOURCE FINGERPRINT is what a hand-writer cannot fake without doing the work: it must
    match the real working tree, and it expires the moment the code moves.
  - GIT is the layer nothing here can substitute for. Every record is a committed file, so a
    hand-edit is a diff and a destroyed record is recoverable.

  - THE HASH CHAIN IS GONE, AND IT NEVER BOUGHT WHAT ITS DOCSTRING CLAIMED. From 2026-08-05
    every record carried a ``trail_link``, and the module said a hand-write could no longer
    pass for a seal. That was tested against a forger who did not bother: ``_link_for`` was a
    pure function over (trail, record), importable by anyone, so a forger who called it minted
    a trail that verified and stood green — RUN, on 2026-08-16, not reasoned. What the chain
    genuinely bought was append-only-ness: it made a DELETION detectable, and deletion is the
    property this ticket deliberately gives up. So it retires with the thing it protected.

What none of it claims: the bytes are not unwritable to a caller running as the same uid.

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

# THE FIXTURE WORLD, named so persist_validation can stay silent inside it. The predicate is
# "is this under the temp root" rather than "is this under class-space", and the difference is
# not cosmetic: quorum seals human-proved concept-pieces whose addresses live in CairnCommons,
# and a class-space test would have made every one of those changes silent — a hole in the
# half of the store that has no tester to catch it. `gettempdir()` honours TMPDIR, so it is
# exactly the predicate "a fixture wrote this", not a guess at one.


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
      - sealed green, fingerprint matches     -> proven
      - never sealed                          -> not proven (the trail does not exist)
      - the seal is red                       -> not proven (it was measured and it failed)
      - sealed green, fingerprint has moved   -> NOT PROVEN, the horizon closed. This is the
        one an in-memory registry could not reach: it cached a bool with no expiry, so it kept
        answering yes after the code changed underneath it (Law 3 — a VALIDATION expires).

    THERE IS ONE RECORD, so there is no newest to pick (2026-08-16, ticket
    a-validation-is-one-current-record-not-a-trail). This function used to open by asking the
    chain whether the newest entry came whole through the door; that check is gone with the
    chain, and its retirement cost nothing it was actually delivering — MEASURED, not
    reasoned. The link was minted by ``_link_for``, a pure function over (trail, record) that
    any caller could import and call, so a forger who bothered to compute one produced a trail
    that verified and stood green. The tooth that claimed otherwise was measuring a forger who
    did not bother.

    What DOES stand between a hand-write and a false green, and it is what this function now
    rests on entirely: ``source_fingerprint``, which the hand-writer must match against the
    real working tree, and which expires the moment the code moves. Beside it sit the 0444
    mode bit (the accident cannot land at all) and git (every trail is a committed file, so a
    hand-edit is a diff — and unlike the chain, that is not a number the editor can recompute).
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
            f"the seal on {proof_path} is {seal.get('verdict')!r}, dated "
            f"{seal.get('date')} — the code was measured and it did not pass")}
    recorded = (seal.get("evidence") or {}).get("source_fingerprint")
    if recorded is None:
        return {"proven": False, "seal": seal, "why": (
            f"the seal on {proof_path} is green, dated {seal.get('date')}, but records "
            f"no source_fingerprint — so whether the code still matches what was proved is "
            f"UNKNOWABLE from the trail. Unknown is not green (Law 9). Re-run the proof to "
            f"seal a fingerprint")}
    current = source_fingerprint(proof_path)
    if current != recorded:
        return {"proven": False, "seal": seal, "why": (
            f"the seal on {proof_path} is green, dated {seal.get('date')} — and its "
            f"HORIZON HAS CLOSED: the component's source fingerprint was "
            f"{recorded[:12]}… when it was sealed and is {current[:12]}… now, so the code moved "
            f"under the proof. Re-run the proof (Law 3: a VALIDATION expires)")}
    return {"proven": True, "seal": seal, "why": (
        f"sealed green {seal.get('date')} by {seal.get('caller')}, and the component's source "
        f"fingerprint still matches what was proved ({recorded[:12]}…)")}


def verdict_change(standing_trail: list, incoming: dict) -> dict | None:
    """Does this incoming record CHANGE the verdict standing on the trail? ``None`` if not.

    A PURE FUNCTION, kept separate from the announcing so the question can be asked and
    proved without raising anything anywhere. Returns the change as data — both verdicts,
    both dates, both callers — because whoever reads the announcement needs all of it in one
    pass and the record that carried the old half is about to be replaced.

    Fires in BOTH directions, and that is a decision rather than an oversight. A green going
    red is the alarming one, but a red going green destroys the red — and "this was failing on
    <date> and passes now" is the same fact read from the other end. What is NOT reported is a
    re-run that agrees with itself, which is 52 of the 54 multi-entry trails measured in this
    corpus on 2026-08-16: the overwhelmingly common case says nothing and stays silent.
    """
    if not standing_trail:
        return None
    was = standing_trail[-1]
    if not isinstance(was, dict) or was.get("verdict") == incoming.get("verdict"):
        return None
    return {"from": was.get("verdict"), "to": incoming.get("verdict"),
            "was_sealed": was.get("date"), "now_sealed": incoming.get("date"),
            "was_caller": was.get("caller"), "now_caller": incoming.get("caller"),
            "claim": incoming.get("claim")}


def announce_verdict_change(path: str, change: dict, *, device=None) -> dict:
    """Fire a verdict change out of a door, at the moment it happens, BEFORE the replace lands.

    THIS IS WHAT MAKES THE COLLAPSE LEGAL UNDER LAW 7, and the reasoning is worth keeping
    where the code is. Law 7 lets a presentation surface collapse an error into a coherent
    shape and never lets a record of truth do it. Replacing a record IS collapsing it — so the
    only argument that survives is that the error gets LOUDER, not quieter, and "louder" has to
    be a route to a surface rather than a claim. Before this, a verdict change sat at an index
    of a file with three readers, all of which took the last entry; the change itself was read
    by nobody, for eight days in the one measured case. Now it raises a trouble, which lands in
    the SessionStart banner a human meets before anything else.

    THE DAMPING IS TroubleDevice'S AND IS THE REASON IT IS THE RIGHT DOOR rather than a new
    one: ``identity`` names the DEFECT, not the occurrence, so a proof that flaps green/red/green
    for a week raises ONE trouble whose count climbs — "fifty flaps do not make fifty tickets"
    (its own proof's words). A verdict change is precisely the flapping-prone signal that would
    otherwise re-notify forever.

    ``device`` is injectable so a proof can announce into a temporary store. It is not a
    convenience: without it, proving this door would write real troubles into the commons from
    a fixture, and a proof that dirties a record of truth to demonstrate itself is its own
    defect.
    """
    if device is None:
        from cairn.devices.trouble.trouble import TroubleDevice
        device = TroubleDevice()
    return device.raise_trouble(
        f"validation-verdict-changed-{os.path.splitext(os.path.basename(path))[0]}",
        why=(f"the verdict standing at {path} changed from {change['from']!r} (sealed "
             f"{change['was_sealed']} by {change['was_caller']}) to {change['to']!r} (sealed "
             f"{change['now_sealed']} by {change['now_caller']}). The trail holds ONE record "
             f"per proof, so the superseded record is not in the working tree any more — it is "
             f"in git, one commit back from this seal. This report exists because the replace "
             f"may not make the change quieter than the append did (Law 7)."),
        detail=dict(change, trail=path))


def _atomic_write(path: str, data) -> None:
    """Write JSON via temp-file + rename, then drop the file to read-only.

    THE MODE BIT IS THE CHEAP HALF OF THE GATE (2026-08-05, ticket
    validation-store-door-is-the-only-path). A record of truth declared append-only was a
    plain 0644 JSON file, so ``json.dump(trail, open(path, "w"))`` from anywhere destroyed a
    proof's whole seal history and looked exactly like a fresh seal. At 0444 that call raises
    PermissionError at the open — the ORDINARY bypass, the one nobody intended, stops being
    possible rather than being detected afterwards.

    It does not stop a deliberate one (same uid can chmod), and it never did. What it stops
    is the hand that was not trying — and that hand is not hypothetical here: the destroy-the-
    history shape this bit was born against was an ordinary ``open(path, "w")`` in code
    somebody wrote without knowing the file was a record of truth.

    RESIDUE, stated because git cannot carry it: git tracks only the executable bit, so a
    fresh clone lands these files at 0644 and they are unprotected until the door next writes.
    The mode is a property of the working tree, not of the record. What survives a clone is
    git itself — the record is a committed file, so a hand-edit in a fresh clone is a diff.
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
    validation: dict, *, proof_path: str | None = None, artifact_path: str | None = None,
    trouble_device=None,
) -> str:
    """The single write-door: SEAL one VALIDATION as the current record beside what it seals.

    Give ``proof_path`` for a node proved by a tester run, or ``artifact_path`` for one proved
    by human judgment (a concept-piece — see ``cairn/devices/tester/quorum.py``). Exactly one: the
    address is always derived, never chosen, and a caller who names both has not decided what
    it is sealing.

    Refuses a record that is not exactly the ratified eight fields (drift is not a seal).
    REPLACES rather than appends (2026-08-16): a VALIDATION expires (Law 3), so a re-run
    supersedes the seal rather than adding to a pile of them, and what makes the supersession
    verifiable is the ``source_fingerprint`` the record carries — Akien's "enough data to
    verify it". The file holds one record and stays a one-element list, because every reader
    in the corpus takes ``trail[-1]`` and a list is what they already open.

    AND THE CHANGE FIRES BEFORE THE REPLACE LANDS. That order is the design, not an
    implementation detail: announcing after would mean a crash between the two acts loses the
    change AND the old record in one step. Announcing first can at worst report a change that
    then fails to land — a false alarm a human can dismiss, against a silent loss they cannot
    detect. The ordering is chosen in the direction Law 7 points.

    A FAILING DOOR DOES NOT BLOCK THE SEAL, and that is also deliberate. If the trouble store
    is unreachable, refusing the write would throw away the NEW measurement — the freshly
    proved fact — to protect the old one, which is still in git either way. So the
    announcement's failure is swallowed into the record it could not announce... nowhere, and
    that is the honest residue: this door cannot report its own silence. It is why the
    announcement is a trouble (durable, damped, human-facing) rather than a log line.

    ``trouble_device`` is injectable for proofs; see ``announce_verdict_change``.
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
            "The eight fields are ratified, so everything the run measured about ITSELF rides "
            "inside evidence — the seal's verdict, the return code, the source_fingerprint that "
            "expires the record. A blob has nowhere to carry them, and a reader asking 'did the "
            "sandbox hold?' would be left grepping prose for the answer (Law 7).")
    path = (
        validations_path_for(proof_path) if proof_path is not None
        else validations_path_for_artifact(artifact_path)
    )
    record = dict(validation)
    standing_trail = read_validations(path=path)
    change = verdict_change(standing_trail, record)
    # A FIXTURE'S VERDICT CHANGE IS THE FIXTURE DOING ITS JOB, not a defect in the world.
    # Proofs seal into tmpdirs by the dozen and flip verdicts on purpose; announcing those
    # would fill the trouble store with the noise of its own tests — the failure mode a damped
    # door exists to avoid, arriving by a different route.
    if change is not None and not os.path.abspath(path).startswith(
            os.path.realpath(tempfile.gettempdir()) + os.sep):
        try:
            announce_verdict_change(path, change, device=trouble_device)
        except Exception:  # noqa: BLE001 — see the docstring: the new measurement outranks it
            pass
    _atomic_write(path, [record])
    if change is not None and record.get("verdict") == "green":
        identity = f"validation-verdict-changed-{os.path.splitext(os.path.basename(path))[0]}"
        try:
            if trouble_device is None:
                from cairn.devices.trouble.trouble import TroubleDevice
                td = TroubleDevice()
            else:
                td = trouble_device
            td.clear(identity, by="cc",
                     what_changed=f"re-seal round-trip: {change['from']}→green by "
                                  f"{record.get('caller', '?')} ({record.get('date', '?')})")
        except Exception:
            pass
    return path

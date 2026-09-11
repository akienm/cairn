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
from cairn.devices.tester.isolation import BREACHED, INDETERMINATE, OPEN, SEALED

# THE AXIS IS WHETHER ANYONE LOOKED, NOT HOW STRONG THE SEAL IS. isolation.py's own comments
# draw it: `open` is "not asked for; the route is open by construction, said so" — the ONE
# verdict of the four that is the ABSENCE of a measurement. The other three are measurements:
# sealed (confirmed from inside), indeterminate (asked, could not confirm — CP1), breached
# (asked, the route is still there — a measured RED). So the set below is not a strength
# ordering and must never be read as one: it is the answer to "did somebody take a reading
# here?", which is the only question a replace can silently destroy the answer to (Law 3).
_MEASURED_SEALS = frozenset({SEALED, INDETERMINATE, BREACHED})

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


def artifact_fingerprint(artifact_path: str) -> str:
    """One sha256 over a human-proved artifact's bytes — ``source_fingerprint``'s twin for
    prose. A quorum seal carries it so ``standing`` can expire the seal when the piece the
    readers signed is no longer the piece on disk (Law 3: a VALIDATION expires). Over the
    one file only: a concept-piece has no component tree, the artifact IS the thing proved."""
    digest = hashlib.sha256()
    with open(artifact_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))


def directory_fingerprint(root: str) -> str:
    """One sha256 over every ``*.py`` under ``root`` — the older of the two recipes.

    Takes an explicit root rather than deriving one, because it has two kinds of caller: the
    seal recipe below, which derives the component from a proof path, and the readers that
    need to hash a directory they were handed (build_inspector's fixtures, most of all). It
    was copied into build_inspector once for exactly that reason, and the copy is what made
    the two disagree the day the recipe changed. One recipe, one address, an explicit root.

    Path AND content go into the digest, so a rename or a deletion moves the number as surely
    as an edit does; a file that vanished cannot be an unnoticed change. Sorted by relative
    path, so the digest is deterministic across filesystems.
    """
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


def closure_of(seal: dict) -> list[str] | None:
    """The import closure a seal recorded, or ``None`` for a seal taken before closures existed.

    ``None`` is not "empty" and the difference decides which recipe re-takes the fingerprint.
    A pre-2026-09-08 seal was taken over the whole component directory and must be re-taken
    that way or it reads stale for a reason no one can explain; a seal WITH a closure is
    re-taken over exactly the files the proof loaded. Kept as a named reader so the three
    call sites cannot each invent their own way of asking (Law 1)."""
    if not isinstance(seal, dict):
        return None
    closure = (seal.get("evidence") or {}).get("fingerprint_closure")
    return closure if isinstance(closure, list) else None


def sealed_fingerprint_now(proof_path: str, seal: dict) -> str:
    """Re-take ``proof_path``'s fingerprint UNDER THE RECIPE THIS SEAL WAS TAKEN WITH.

    THE ONE DOOR FOR "has the code moved under this seal?", and it exists because that
    question had three independent answers. ``standing`` here, ``component_color`` in
    build_inspector, and ``_fingerprint_stale`` in proof_coverage each re-derived the
    recipe; the day the recipe gained a second form was the day they would have disagreed,
    and a seal reading green in one surface and expired in another is worse than either
    answer alone (Law 7 — a record of truth may not collapse, and two records of truth may
    not contradict). Both remaining call sites now come here.
    """
    closure = closure_of(seal)
    if closure is not None:
        # IS THIS CLOSURE EVEN ABOUT THIS PROOF? ``repo_relative_closure`` unions the proof
        # into every closure it builds, so a real closure ALWAYS names the proof it was taken
        # for. One that does not was copied from somewhere else — and the copy is not
        # hypothetical: it is what a fixture does when it re-points an existing seal's
        # ``source_fingerprint`` at a different component and leaves the closure behind, which
        # is exactly how this check came to be written (the tester's own proofs did it, and
        # the seal silently compared the wrong files). The two halves of the pair must move
        # together; when they have not, the closure is discarded and the directory recipe
        # answers — conservative, and never a comparison against files the proof never loaded.
        mine = repo_relative_closure([], proof_path)
        if not mine or mine[0] not in closure:
            closure = None
    return source_fingerprint(proof_path, closure=closure)


def source_fingerprint(proof_path: str, *, closure: list[str] | None = None) -> str:
    """One sha256 over what the proof actually PROVED — its import closure, or its directory.

    SCOPE IS THE HORIZON'S OWN WORDING: "valid until the proof file OR THE CODE IT PROVES
    changes." The question has always been which files are "the code it proves", and until
    2026-09-08 the answer was every ``*.py`` under the component root — a stand-in for the
    real answer, chosen because nothing could compute the real one.

    WHAT THE STAND-IN COST, MEASURED: 2026-09-05, one edit to ``transitions.py`` expired 60
    of 154 seals at once. 2026-09-07, clearing the inbox meant re-sealing 18 proofs whose
    code had not changed — only a neighbour in the same directory had. 2026-09-08, the seals
    under ``tools/base`` were taken TWICE in one voyage, ~22 minutes each, because a one-line
    edit to ONE proof file expired all 35 — including the 34 that could not load it. The
    lived symptom is a wall of red that says nothing about what broke.

    ``closure`` is the real answer when the runner could capture it: the repo-relative files
    the proof's subprocess actually imported, plus the proof itself. Hashed sorted, path and
    content both, so a rename or a deletion moves the number as surely as an edit does. A
    file in the closure that has since VANISHED digests a sentinel rather than raising — a
    file that is gone is the loudest kind of change, and the seal must expire, not crash.

    ``closure=None`` keeps the directory walk, and that is not a deprecated branch: it is
    what a seal taken before this existed must be re-checked with, and what the runner falls
    back to when the closure could not be captured (a timed-out proof reports nothing). The
    two recipes are never mixed — ``sealed_fingerprint_now`` picks by what the seal carries.

    THE HOLE, STATED RATHER THAN HIDDEN: a closure is what the proof IMPORTED at runtime. A
    file it ``open()``s without importing is invisible to it, and so is a lazy import inside
    a branch that did not run. Both were invisible to the directory walk in a different
    way — it caught them by covering everything, at the price of catching everything else
    too. Narrowing the net is what makes the misses possible; saying so in the record is
    what keeps them findable.

    Deliberately NOT git, in either form: a seal must expire the moment the working tree
    diverges, not when someone commits. An uncommitted edit is exactly the state where a
    stale green does harm.
    """
    if closure is None:
        return directory_fingerprint(component_root_for(proof_path))
    digest = hashlib.sha256()
    for rel in sorted(set(closure)):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        full = os.path.join(_REPO_ROOT, rel)
        try:
            with open(full, "rb") as f:
                digest.update(f.read())
        except OSError:
            # GONE. Digest a sentinel the file's own bytes could never produce, so the seal
            # expires loudly instead of the read raising inside three different callers.
            digest.update(b"\0<absent>\0")
        digest.update(b"\0")
    return digest.hexdigest()


def repo_relative_closure(files, proof_path: str) -> list[str]:
    """Filter a runner's raw ``__file__`` list down to the seal's closure — repo files, sorted.

    Everything outside this repo is dropped: the standard library and site-packages move
    when the interpreter is upgraded, not when this system changes, and a seal that expired
    on a python patch release would teach a reader to ignore expiry. The proof itself is
    unioned in unconditionally — ``runpy`` restores ``sys.modules['__main__']`` before
    ``atexit`` runs, so the one file every closure must contain is the one the raw list is
    most likely to be missing.
    """
    out = set()
    for f in list(files or []) + [proof_path]:
        try:
            full = os.path.realpath(str(f))
        except OSError:
            continue
        if full.endswith(".pyc"):
            full = full[:-1]
        rel = os.path.relpath(full, _REPO_ROOT)
        if rel.startswith(os.pardir) or os.path.isabs(rel):
            continue
        if rel.endswith(".py"):
            out.add(rel)
    return sorted(out)


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
    # TWO KINDS OF PROVEN THING, ONE QUESTION. A proof file lives under proofs/ and its
    # seal is the tester's; anything else handed here is a human-proved ARTIFACT (a
    # concept-piece) whose seal is the quorum's, addressed by the artifact rule and
    # fingerprinted over the artifact itself. Decided by the path's shape, not by a flag,
    # so a caller cannot ask the code question about prose or the prose question about code.
    human_proved = os.path.basename(os.path.dirname(os.path.abspath(proof_path))) != "proofs"
    trail = (read_validations(path=validations_path_for_artifact(proof_path))
             if human_proved else read_validations(proof_path))
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
    # RE-TAKEN UNDER THE SEAL'S OWN RECIPE, never under today's. A seal that recorded an
    # import closure is re-checked over exactly those files; one that predates closures is
    # re-checked over the component directory it was taken across. Asking the new question
    # of an old seal would expire every seal in the corpus at once and call it drift.
    closure = closure_of(seal)
    current = (artifact_fingerprint(proof_path) if human_proved
               else sealed_fingerprint_now(proof_path, seal))
    # WHAT WAS HASHED, NAMED IN THE SENTENCE. Three recipes reach this line and until
    # 2026-09-08 the sentence named none of them, so "the fingerprint moved" left the reader
    # to guess whether it was the artifact, the closure, or a neighbour in the same directory
    # that moved — the difference between a real expiry and a directory-recipe false alarm
    # (Law 7: a diagnostic surface is loud). A human-proved artifact is hashed over ITSELF and
    # must say so; naming it "the component's directory" was both wrong and unfalsifiable.
    scope = ("the artifact" if human_proved else
             f"the {len(closure)} file(s) the proof imports" if closure is not None else
             "the component's directory")
    if current != recorded:
        return {"proven": False, "seal": seal, "why": (
            f"the seal on {proof_path} is green, dated {seal.get('date')} — and its "
            f"HORIZON HAS CLOSED: the fingerprint over {scope} was "
            f"{recorded[:12]}… when it was sealed and is {current[:12]}… now, so the code moved "
            f"under the proof. Re-run the proof (Law 3: a VALIDATION expires)")}
    return {"proven": True, "seal": seal, "why": (
        f"sealed green {seal.get('date')} by {seal.get('caller')}, and the fingerprint over "
        f"{scope} still matches what was proved ({recorded[:12]}…)")}


class SealDowngradeRefused(ValueError):
    """A measurement was about to be replaced by the absence of one, and the door said no."""


class SealConversionRefused(ValueError):
    """A recorded choice NOT to measure was about to be replaced by a measurement, and the door
    said no.

    THE MIRROR OF ITS SIBLING, AND THE ASYMMETRY IT CLOSES IS THE WHOLE FINDING. ``SealDowngradeRefused``
    protects a reading from being retired by the absence of one. This protects the ABSENCE from
    being retired by a reading — and the absence is not nothing: ``open`` means *asked for
    nothing, and said so*, which is a recorded decision about how this proof is run. Measured
    2026-09-10 at HEAD 57bd9cf, on a fixture: a standing ``open``, one ``cairn test --seal
    --netns`` over it, and the record read ``sealed`` with four lines of output, no mention of
    an override, and the ``open`` unrecoverable — because this door REPLACES. 54 of the 219
    standing validations across both roots were convertible by one such sweep.

    Why it is a gate and not a wall: converting IS the right act much of the time — an ``open``
    standing on a proof that should be sealed is exactly what wants fixing. What the door
    refuses is converting SILENTLY. ``converting_because`` is the escape, and the reason rides
    inside the surviving record's evidence, mirroring ``unsealing_because`` in both shape and
    placement. Inside rather than beside, for the same reason as its sibling: the door replaces,
    so there is no superseded record left on disk to carry one.
    """


def _seal_verdict_of(record: dict) -> str | None:
    """The seal verdict recorded INSIDE one VALIDATION's evidence, or ``None`` if it carries none.

    ``None`` is not a fourth verdict — it is "this record says nothing about a seal", which is
    what every pre-seal record in the corpus says (measured 2026-09-09: exactly one of 201).
    Kept separate from the four because collapsing "nobody recorded" into ``open`` ("nobody
    asked") is the same category error this whole module is about, one level down.
    """
    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        return None
    seal = evidence.get("seal")
    if not isinstance(seal, dict):
        return None
    verdict = seal.get("verdict")
    return verdict if isinstance(verdict, str) else None


def standing_seal(proof_path: str | None = None, *, path: str | None = None) -> str | None:
    """What seal is STANDING for this proof right now — one of the four verdicts, or ``None``.

    THE READER THAT DID NOT EXIST. Measured 2026-09-09 with a grep for every ``["seal"]`` and
    ``.get("seal"`` across ``cairn/``, ``bin/`` and ``skills/``: sixteen hits, and not one of
    them opens a standing on-disk validation to ask what seal it carries. Every hit is either a
    proof asserting on a record it just produced, a read of the seal's DATE rather than its
    verdict, or a path being formatted. The seal was written by the door and read by nobody —
    which is exactly how 121 sealed records could be overwritten by an unsealed re-run without
    anything in the system noticing (Law 1: the answer nobody can look up gets re-derived, or
    in this case, thrown away).

    ``None`` means "nothing is standing": no validations file, an empty one, or a record that
    carries no seal at all. It is deliberately NOT ``open``. A file that does not exist and a
    record saying "no seal was requested" are different facts, and the second one is a
    measurement — treating absence as ``open`` would let the guard below wave through the very
    first replace of a record it never read.
    """
    trail = read_validations(proof_path, path=path)
    if not trail:
        return None
    return _seal_verdict_of(trail[-1])


def isolation_for_seal(verdict: str | None) -> str | None:
    """The isolation that would REPRODUCE a standing seal verdict — ``None`` if it says nothing.

    Three of the four verdicts mean the seal was ASKED FOR (sealed, indeterminate, breached),
    so reproducing them means asking again: ``netns``. ``open`` means nobody asked, so
    reproducing it means not asking: ``none``. ``None`` in means ``None`` out — there is no
    standing record to reproduce, and the caller's own default is the honest answer, not a
    guess dressed as one.

    This lives here rather than in the runner because it is the seal vocabulary's own
    knowledge, and a provider does not know its consumers: the CLI, a re-seal sweep and the
    probe all ask the same question and must not each spell the mapping their own way.
    """
    if verdict is None:
        return None
    return "none" if verdict == OPEN else "netns"


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

    THE DOOR IS NOW AN EMISSION, NOT A HELD DEVICE (ticket 9579a6f9cec6, 2026-09-07). The
    damping above is unchanged and still the reason this is the right door — it just happens
    in the hand that OWNS the store instead of in ours. The tester raises a breadcrumb under
    its own log home; the trouble device folds it by identity. What the tester is responsible
    for is the half it can be responsible for: a STABLE IDENTITY, so fifty flaps present as
    one defect to fold. Whether the fold then counts correctly is trouble's property and is
    proved at trouble's address (Law 6 — the store's owner gates writes to it, and until this
    ticket the tester was writing that store from inside a seal).

    ``device`` is injectable so a proof can announce into a temporary log root. It is not a
    convenience: without it, proving this door would write real troubles into the commons from
    a fixture, and a proof that dirties a record of truth to demonstrate itself is its own
    defect.
    """
    if device is None:
        from cairn.tools.base.diagnostic import ModuleRaiser
        device = ModuleRaiser("tester")
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
    trouble_device=None, unsealing_because: str | None = None,
    converting_because: str | None = None,
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

    AND A MEASUREMENT IS NEVER REPLACED BY THE ABSENCE OF ONE (2026-09-09, ticket
    4431cf2bc625). Because the door REPLACES, a re-run that did not ask for the network seal
    used to overwrite a record that HAD measured it — 44 validations went that way in one
    afternoon and nothing refused, which was caught by diffing a file by hand. The guard below
    refuses a record carrying seal ``open`` over a standing ``sealed``/``indeterminate``/
    ``breached``, because those three are readings and ``open`` is the absence of one. It
    deliberately does NOT refuse the other directions: ``sealed -> breached`` is a measured
    failure and Law 7 says it must land loudly, and ``sealed -> indeterminate`` is CP1 saying
    "I could not confirm" — both are readings, and a guard that blocked them would be
    protecting an old green from a new red, which is the opposite of the job.

    ``unsealing_because`` is the escape, and the escape is what keeps this a gate rather than a
    wall: a caller who genuinely means to drop the seal says why, and the reason lands
    PERMANENTLY inside the new record's evidence. Inside, not beside — the eight fields are
    ratified (Akien's half of this device's ownership) and everything a run measured about
    itself already rides in evidence. A ruling id is a legal thing to write there; the field
    takes prose so that the cheaper case does not have to mint a ruling to get past a bug.

    AND THE ABSENCE OF A MEASUREMENT IS NEVER REPLACED BY ONE SILENTLY (2026-09-10, ticket
    299d4f72ae40). The mirror of the guard above, and it was left open by it: a standing
    ``open`` is not an empty slot, it is a recorded choice not to ask, and until this build one
    ``cairn test --seal --netns`` converted it to ``sealed`` with nothing said and nothing left
    behind. The same store refused to retire a MEASUREMENT without a written reason while
    letting a deliberate NON-measurement be retired without one — that asymmetry is what this
    closes. ``converting_because`` is its escape and behaves exactly like ``unsealing_because``:
    the reason rides permanently in the landed record's evidence.

    NEITHER GUARD FIRES WHEN NOTHING IS STANDING. A first seal — ``None`` -> anything — is the
    ordinary way a proof enters proven-space, and ``None`` is not ``open``: it is "no record",
    where ``open`` is "a record saying nobody asked". ``_seal_verdict_of`` keeps them apart on
    purpose, and the guards read it, so a proof being sealed for the first time meets no door.

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

    # THE GUARD, AND IT FIRES BEFORE ANYTHING ELSE HAPPENS — before the announce, before the
    # write. A refusal that had already announced would have reported a change that never
    # landed; a refusal after the write would not be a refusal at all.
    was = _seal_verdict_of(standing_trail[-1]) if standing_trail else None
    now = _seal_verdict_of(record)
    if was in _MEASURED_SEALS and now == OPEN:
        if not (isinstance(unsealing_because, str) and unsealing_because.strip()):
            raise SealDowngradeRefused(
                f"{os.path.relpath(path)} carries a seal that was ASKED FOR ({was!r}) and this "
                f"record carries {OPEN!r} — which is not a weaker reading, it is the ABSENCE of "
                "one. Because this door REPLACES, landing it would retire the measurement with "
                "nothing left on disk to say a measurement was ever taken (Law 3). Two ways "
                "forward: re-run at the isolation the standing seal was taken at (`cairn test "
                "--seal` now does this per proof, so the ordinary path never reaches here), or "
                "pass unsealing_because='<why>' and the reason rides permanently in the "
                "record's evidence.")
        record["evidence"] = {**evidence, "unsealing_because": unsealing_because}

    # THE MIRROR, AND IT SITS HERE RATHER THAN IN THE CLI FOR THE REASON A PROVIDER DOES NOT
    # KNOW ITS CONSUMERS. The observed conversion came through `cairn test --seal --netns`, but
    # `cairn/tools/base/validation.py`'s public `run_proof` also persists and never forwards
    # isolation at all, so it lands `open` or a measured verdict depending only on what its
    # caller's environment did — and a guard bolted to the flag would not see it. One door, one
    # guard, every persisting caller covered.
    #
    # `was is not None` is load-bearing and is NOT the same test as `was != OPEN`: a first seal
    # has no standing record, and refusing it would wall off the ordinary entrance to
    # proven-space.
    if was == OPEN and now in _MEASURED_SEALS:
        if not (isinstance(converting_because, str) and converting_because.strip()):
            raise SealConversionRefused(
                f"{os.path.relpath(path)} carries a seal of {OPEN!r} — which is not an empty "
                f"slot, it is a RECORDED CHOICE not to measure ('asked for nothing, and said "
                f"so') — and this record carries {now!r}. Because this door REPLACES, landing "
                "it would retire that choice with nothing left on disk to say it was ever "
                "made, and the reading that replaced it would look like it had always been "
                "there (Law 3). Two ways forward: run the proof at the isolation its standing "
                "record was taken at (`cairn test --seal` reproduces it per proof, so the "
                "ordinary path never reaches here), or pass converting_because='<why>' and the "
                "reason rides permanently in the record's evidence.")
        record["evidence"] = {**evidence, "converting_because": converting_because}

    # AND A HOLLOW READING SURVIVES A RE-SEAL OF THE SAME CODE (2026-09-09, uncovered by the
    # 1accdc1781aa voyage). Same shape as the guard above, one level in: because the door
    # REPLACES, ``evidence.hollow`` — the reading ``record_hollow`` lands, and the one thing a
    # PROVED gate can ask to tell a real green from a green a hollow build could also earn —
    # had a lifetime of ONE COMMIT. Measured before the fix: the fc93d8cd5961 run reported
    # "hollow evidence landed on 1 of 1 standing validation(s)", and a corpus-wide read found
    # ZERO records anywhere carrying the key, because the pre-commit reseal ladder runs on
    # every commit and each reseal dropped it.
    #
    # THE CARRY IS FINGERPRINT-BOUND, WHICH IS THE WHOLE POINT. A hollow reading is a
    # measurement about a specific tree: revert THESE files, and no declared tooth reds. Change
    # the code and that reading is about a tree that no longer exists, so it must expire (Law
    # 3) — and it does, because the fingerprints stop matching and the key is not carried. An
    # unchanged re-seal is the case this fixes: the same code, measured again, and a reading
    # nobody re-took is not a reading nobody ever took.
    #
    # A NEW RECORD THAT CARRIES ITS OWN ``hollow`` WINS, always: ``record_hollow`` writes
    # through this same door, so the carry must never overwrite the act that is landing.
    _prior_ev = (standing_trail[-1].get("evidence") or {}) if standing_trail else {}
    if isinstance(_prior_ev, dict):
        _prior_hollow = _prior_ev.get("hollow")
        _new_ev = record.get("evidence") or {}
        _fp = _prior_ev.get("source_fingerprint")
        if (isinstance(_prior_hollow, dict) and _prior_hollow
                and "hollow" not in _new_ev
                and _fp and _fp == _new_ev.get("source_fingerprint")):
            record["evidence"] = {**_new_ev, "hollow": _prior_hollow}

    change = verdict_change(standing_trail, record)
    # A FIXTURE'S VERDICT CHANGE IS THE FIXTURE DOING ITS JOB, not a defect in the world.
    # Proofs seal into tmpdirs by the dozen and flip verdicts on purpose; announcing those
    # would fill the trouble store with the noise of its own tests — the failure mode a damped
    # door exists to avoid, arriving by a different route.
    #
    # ONE PREDICATE, BOTH HALVES (2026-09-07, ticket 9579a6f9cec6). The guard used to cover
    # only the announce, and the clear below ran for every fixture re-seal in the corpus. That
    # was invisible while clearing meant constructing a device and finding no such trouble —
    # a cheap no-op nobody paid for. It stopped being invisible the moment clearing became a
    # bus request: the same fixture traffic that was a no-op now dials a lane, per seal. The
    # cost exposed the defect, but the defect was always there — the reasoning in the
    # paragraph above never distinguished the two halves, and the code did.
    fixture_address = os.path.abspath(path).startswith(
        os.path.realpath(tempfile.gettempdir()) + os.sep)
    if change is not None and not fixture_address:
        try:
            announce_verdict_change(path, change, device=trouble_device)
        except Exception:  # noqa: BLE001 — see the docstring: the new measurement outranks it
            pass
    _atomic_write(path, [record])
    if change is not None and record.get("verdict") == "green" and not fixture_address:
        identity = f"validation-verdict-changed-{os.path.splitext(os.path.basename(path))[0]}"
        what_changed = (f"re-seal round-trip: {change['from']}→green by "
                        f"{record.get('caller', '?')} ({record.get('date', '?')})")
        try:
            if trouble_device is not None:
                # THE OWNER ITSELF, injected by a proof that holds the store under a temp
                # root. It can write directly because it IS the one hand; nobody else can.
                trouble_device.clear(identity, by="cc", what_changed=what_changed)
            else:
                # AN EMISSION, LIKE THE RAISE ABOVE (ticket 9579a6f9cec6, completed
                # 2026-09-08). This was a bus request, on the reasoning that a clear is a
                # read-modify-write and so belongs to the hand that owns the store. The
                # reasoning holds; the bus was the wrong way to reach that hand. Dialing it
                # pulls in ``bus_client``, which imports ``inference_domain`` and reaches
                # ``db_domain`` through the bus device — and this module sits on the build
                # inspector's own import path (``transitions -> validation_store``), so the
                # tester's clear was half of why the inspector could statically reach a
                # database. Now the ask is a breadcrumb and the fold is trouble's, which is
                # where the read-modify-write was always supposed to happen.
                from cairn.tools.base.diagnostic import ModuleRaiser
                ModuleRaiser("tester").clear_trouble(
                    identity, by="cc", what_changed=what_changed)
        except Exception:
            pass
    return path


def record_hollow(proof_path: str, ticket: str, measured: dict, *, trouble_device=None) -> bool:
    """Land a hollow reading on this proof's STANDING validation as ``evidence.hollow[ticket]``.

    Returns True when a record was rewritten, False when there is no standing validation to
    write on — which is not an error: `--hollow` may name a ticket whose proof has run but was
    never sealed, and inventing a seal to hang the reading off would mint a measurement of the
    proof's OUTCOME that nobody took.

    WHY IT RIDES `evidence` AND NOT A NINTH FIELD. The eight are ratified (Akien's half of this
    device's ownership) and `evidence` is exactly where a run's self-measurements already live —
    the seal, the fingerprint closure, the teeth. A hollow reading is one more thing measured
    about this proof, so it belongs beside them; a ninth field would be this ticket quietly
    renegotiating the record's shape to hold its own output.

    KEYED BY TICKET, DELIBERATELY, because one proof holds teeth for several tickets and a bare
    `evidence.hollow` would let the next ticket's reading silently overwrite this one's — the
    same replace-without-noticing shape that 4431cf2bc625 was cast to close, one level in.

    THE SEAL AND THE VERDICT COME THROUGH UNTOUCHED: this reads the standing record, adds one
    key inside evidence, and hands the same eight fields back to the door. A hollow run's
    proofs execute against reverted code, so nothing it observed about pass-or-fail may be
    sealed as standing — and nothing here is.
    """
    trail = read_validations(proof_path)
    if not trail:
        return False
    record = json.loads(json.dumps(trail[-1]))  # a copy: the door replaces, and the standing
    evidence = record.get("evidence")           # record must not be mutated before it lands
    if not isinstance(evidence, dict):
        return False
    hollow = evidence.get("hollow")
    # ``list(t)`` ON A NON-LIST WOULD LAUNDER IT. A file's reading is normally a list of the
    # teeth that redded, and the coercion made that concrete. Since 2026-09-09 a file whose
    # reversion broke the proof's IMPORT instead of failing a tooth is sealed as
    # ``{"unreadable": [proofs]}`` — a dict, deliberately, so the gate cannot mistake it for
    # a reading — and ``list()`` over that dict yields ``["unreadable"]``: a NON-EMPTY tooth
    # list, which reads at the gate as a file covered by a tooth named "unreadable". The
    # narrowest possible hollow green, manufactured by a defensive cast. Lists are still
    # normalised; anything else rides through as itself.
    evidence["hollow"] = {**(hollow if isinstance(hollow, dict) else {}),
                          str(ticket): {str(f): (list(t) if isinstance(t, (list, tuple, set))
                                                 else t)
                                        for f, t in measured.items()}}
    persist_validation(record, proof_path=proof_path, trouble_device=trouble_device)
    return True

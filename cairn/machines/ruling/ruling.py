"""cairn/machines/ruling/ruling.py — THE RULING INTAKE GATE. Akien rules; before any code moves,
his ruling becomes a small schema-gated artifact he can red-pen in thirty seconds.

WHY THIS EXISTS, measured 2026-07-31 (the day that produced it): four times in one
session, Akien's stated intent and the code's shape disagreed, and the code won. Two
hours went to one of them — the intentions folder — because his ruling ("``_model.json``
is retired") existed only as conversation while the compiler that wrote the file existed
as source with green proofs. When drift comes, WRITTEN BEATS SPOKEN. There was nothing
written on his side of the room.

That is the whole mechanism, and it is not a discipline problem — it is a missing
artifact. A ruling with no address is a ruling the next reader reconstructs from the
code, which is exactly the direction authority does not flow: code and its proofs are
evidence of what was BUILT, never of what is INTENDED, and a green proof means conformance
to a spec — the very thing a ruling is changing.

THE THREE LINES (Akien approved this shape 2026-07-31): what the spec now says, what
dies, what conforms. Plus his own words, verbatim, above my reading of them — so the gap
between what he said and what I heard is visible on one screen instead of surfacing at
hour two as a regenerated file.

WHAT IS PHYSICS HERE AND WHAT IS NOT. Honest line, because the difference is the whole
value of the thing:

  - PHYSICS: the shape refusals below, the disk checks at intake, and ``verify``'s check
    that a thing ruled dead STAYED dead. None of these can be talked around.
  - NOT PHYSICS: whether I heard him correctly in the first place. No deterministic step
    can do that. What the gate buys is that my misreading surfaces as three wrong lines at
    minute one, red-pennable, instead of as an hour of code built on it. The cost of being
    wrong drops by two orders of magnitude; the rate of being wrong is untouched.

THE INTAKE DOOR COMPUTES WHAT IT CAN, so I cannot author it: ``conforms_fingerprint`` is
a sha256 taken by the door at intake, never a field I fill. That is what lets ``verify``
say "this file has not moved since the ruling" without trusting a word I wrote.

CONFIRMATION IS A SEPARATE ACT. ``open`` may not write ``confirmed: true``; it refuses.
Until Akien confirms, ``verify`` is red no matter how clean the tree is — an unconfirmed
reading is an unverified reading, and work sealed against it is work sealed against my
guess. Kin: the trouble lane, where a live trouble stays in the inbox until cleared.

WHERE IT BERTHS. ``CairnCommons/decisions/`` — the store that already exists, whose one
prior entry was written AFTER a ruling got lost and had to be reconstructed. This is that
store's intake door, not a second store (Law 1). Records carry ``kind: "ruling"``; the
older narrative ``kind: "decision"`` entries are not touched and not scanned.

WHICH PREBUILD STEP THIS IS. ``I-prebuild-cognition-compiles`` step 1, ORIENT — parse the
request, ground it in what is actually being asked. Not step 3, SURVEY, which grounds it
in the existing code and is already built as ``cairn/tools/orient/``. The intention names them
as distinct steps with one module each, and names Survey as the one that gets skipped;
today measured that Orient is the one that gets OVERWRITTEN — by Survey's own output.

SUPERSESSION IS THE RETIREMENT DOOR (grown 2026-08-02, against the first superseded
ruling, exactly as filed edge (d) predicted). A misfiled packet cannot be edited in
place — it carries Akien's ``confirmed: true`` and his verbatim confirmation, and
rewriting a confirmed record erases his act (Law 7). And it cannot just sit red: a
permanent red the hook prints every turn is noise, and noise gets trained away while
still LOOKING like coverage. So retirement is an act through the door, like confirm:
``supersede`` stamps the SUPERSEDING packet — never the retired one — with what it
retires and the evidence for retiring it. The retired packet stays on disk, byte-
identical, forever; it simply stops being OPEN, because a confirmed successor answers
for it. ``list`` still shows it, marked, so the history is visible rather than silent.

``as_of`` — THE GATE COULD ONLY EXPRESS FUTURE WORK (grown 2026-08-06). ``what_conforms``
went green when a file's bytes changed SINCE INTAKE, which silently assumed the packet is
opened before the work. Both 2026-08-05 packets were opened around or after it, and the
board showed the result honestly and uselessly: five ``UNTOUCHED`` lines on a ruling whose
corrections were already made, and nine live files parked under ``what_dies`` because that
was the only field left that could ever go green. A ruling is a record of what Akien said,
and he says it whenever he says it — the gate does not get to require that the paperwork
come first. So the baseline is measurable rather than assumed: ``as_of`` maps each root to
a commit-ish, git renders the file as it stood when he ruled, and the door fingerprints
THAT. Keyed per root because the two roots are separate repos. verify is untouched by this
— it still asks one question, "have the bytes moved off the baseline?", and now the
baseline can be the truth instead of the filing date.

ONE SUCCESSOR RETIRES MANY (grown 2026-08-06, measured not predicted). ``supersedes``
was a single slot, so a second supersession by the same successor OVERWROTE the first —
retiring old-b silently un-retired old-a and erased its evidence, with no error anywhere.
The field is a LIST and the act APPENDS. This is not an exotic case: a successor must be
CONFIRMED before it can retire anything, so a packet rescoped before Akien signs the
original leaves BOTH open, and one corrected reading is the only thing that can retire
the pair. That is exactly how ``2026-08-05-the-file-path-is-the-link`` and its
``-rescoped`` twin came to sit on the board together. Legacy records written in the
single-slot shape are NOT rewritten — they are confirmed records carrying his act, and
``_supersessions`` is the one reader that knows both shapes.

    cairn ruling open <packet.json>      # intake: refuse or write
    cairn ruling list                    # what is open or red
    cairn ruling verify <id>             # the mechanical verdict
    cairn ruling confirm <id>            # Akien's act, not mine
    cairn ruling supersede <old> <new>   # retire a misfiled packet, evidence required
    python3 cairn/machines/ruling/proofs/test_ruling.py    # exit 0 = green
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess

from cairn.tools.gate import gate
from cairn.tools.import_sieve import sieve

# ── the shape ─────────────────────────────────────────────────────────────────

KIND = "ruling"

# The three lines, plus the identity and his own words. Every one is required and every
# one is refused empty — a gate with an optional field is a gate with a way around it.
REQUIRED = (
    "id",
    "kind",
    "date",
    "ruled_by",
    "the_ruling_verbatim",
    "now_the_spec_says",
    "what_dies",
    "what_conforms",
)

# Padding physics. A reading that needs more than this is not a reading — it is a design,
# and a design is what the ruling is supposed to GATE, not what it is supposed to contain.
SPEC_MAX = 280

# HIS MARKER. Akien, 2026-08-13: "I will start saying RULED after every goddamned one" /
# "if i don't use that word, it'd not confimed and i'll live with learning to do that."
#
# WHY A MARKER RATHER THAN A SECOND ASK, which is what this component did until today. The
# confirm door was CIRCULAR: it asked for his words to authorize his words. If
# `the_ruling_verbatim` could be trusted the packet was already confirmed, and if it could
# not, a second quote typed by the same hand fixed nothing — I would be fabricating both
# halves. What the second ask was really guarding is narrower and real: the packets where
# **I** decided something was a ruling and he never said so. He named the mechanism that
# separates those without asking him twice — he marks the ones he means.
#
# UPPERCASE, WORD-BOUNDED, DELIBERATE. Lowercase "ruled" is ordinary English and appears in
# sentences ABOUT rulings ("he ruled that…"); matching it would confirm packets on my own
# prose. The marker is a thing he TYPES, and its absence is not a defect in the packet —
# see `verify`, where unmarked is a separate fact from red and never stops the work.
RULED = re.compile(r"\bRULED\b")

_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_STORE = os.path.join("CairnCommons", "decisions")


def _roots_parent() -> str:
    """The directory holding BOTH roots (``cairn/`` and ``CairnCommons/``).

    Every path in a packet is relative to here, because a ruling routinely spans the two
    trees — the compiler lives in one and the folder it writes lives in the other. A
    packet whose paths were relative to one repo could not name the other's files at all,
    which is precisely the ruling that cost two hours.

    ``CAIRN_ROOTS_PARENT`` overrides it, so the proof can exercise the real doors against
    a temp world instead of the live store — the same seam ``CAIRN_CMD_DIR`` gives the
    dispatcher's proof.
    """
    override = os.environ.get("CAIRN_ROOTS_PARENT")
    if override:
        return override
    package_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # <repo>/cairn
    repo_root = os.path.dirname(package_dir)                                   # <repo>
    return os.path.dirname(repo_root)


def store_dir(roots_parent: str | None = None) -> str:
    return os.path.join(roots_parent or _roots_parent(), _STORE)


def fingerprint(abs_path: str) -> str:
    """sha256 of a file's bytes. The door's own measurement, never an authored field."""
    h = hashlib.sha256()
    with open(abs_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _split_root(rel: str) -> tuple[str, str]:
    """``"cairn/cairn/tools/base/probe.py"`` -> ``("cairn", "cairn/tools/base/probe.py")``.

    Paths are relative to the roots PARENT, so the first segment names which repo the
    rest of the path lives in. ``as_of`` is keyed by that segment because the two roots
    are separate git repos and one commit-ish cannot address both.
    """
    head, _, tail = rel.replace(os.sep, "/").partition("/")
    return head, tail


def fingerprint_at(roots_parent: str, rel: str, commit: str) -> str:
    """sha256 of a file's bytes AS THEY STOOD AT ``commit``. Still the door's own
    measurement — git is the instrument, the packet's author never types a hash.

    Raises ``OSError`` if the commit or the path-at-that-commit does not resolve, which
    the intake door turns into a refusal: a ruling cannot conform a file that did not
    exist when it was ruled.
    """
    root, inner = _split_root(rel)
    proc = subprocess.run(["git", "-C", os.path.join(roots_parent, root),
                           "show", f"{commit}:{inner}"],
                          capture_output=True)
    if proc.returncode != 0:
        raise OSError(proc.stderr.decode("utf-8", "replace").strip()
                      or f"git could not read {inner!r} at {commit!r}")
    return hashlib.sha256(proc.stdout).hexdigest()


# ── refusals: the pure half ───────────────────────────────────────────────────


def refusals_shape(packet: dict) -> list[str]:
    """Everything refusable without touching disk. Returns ALL of them, never the first.

    A gate that reports one refusal per run makes the author play twenty questions with
    it, which is the incomplete-diagnostic defect wearing a validator's clothes: the
    standing method is that the first report carries every datum needed to resolve.
    """
    out: list[str] = []

    for field in REQUIRED:
        if field not in packet:
            out.append(f"missing required field: {field!r}")
    if out:
        return out                      # shape checks below would only echo these

    if packet["kind"] != KIND:
        out.append(f"kind must be {KIND!r}, got {packet['kind']!r}")

    if not _DATE.match(str(packet["date"])):
        out.append(f"date must be YYYY-MM-DD, got {packet['date']!r}")
    if not _ID.match(str(packet["id"])):
        out.append(f"id must be <YYYY-MM-DD>-<kebab-slug>, got {packet['id']!r}")
    elif not str(packet["id"]).startswith(str(packet["date"])):
        out.append(f"id {packet['id']!r} does not carry its own date {packet['date']!r}")

    if not str(packet["ruled_by"]).strip():
        out.append("ruled_by is empty — a ruling has an author or it is not a ruling")

    verbatim = packet["the_ruling_verbatim"]
    if not isinstance(verbatim, list) or not verbatim:
        out.append("the_ruling_verbatim must be a non-empty list of his actual words — "
                   "this is the field my reading is checked AGAINST, so a packet without "
                   "it is a packet that only contains my reading")
    elif any(not isinstance(v, str) or not v.strip() for v in verbatim):
        out.append("the_ruling_verbatim holds an empty or non-string entry")

    spec = packet["now_the_spec_says"]
    if not isinstance(spec, str) or not spec.strip():
        out.append("now_the_spec_says is empty")
    else:
        if "\n" in spec:
            out.append("now_the_spec_says must be ONE line — a multi-line reading is a "
                       "design, and a design is what this gates, not what it holds")
        if len(spec) > SPEC_MAX:
            out.append(f"now_the_spec_says is {len(spec)} chars, cap is {SPEC_MAX}")

    dies, conforms = packet["what_dies"], packet["what_conforms"]
    for name, val in (("what_dies", dies), ("what_conforms", conforms)):
        if not isinstance(val, list):
            out.append(f"{name} must be a list of paths relative to the roots parent")
        elif any(not isinstance(p, str) or not p.strip() for p in val):
            out.append(f"{name} holds an empty or non-string path")
        elif any(os.path.isabs(p) for p in val if isinstance(p, str)):
            out.append(f"{name} holds an absolute path — paths are relative to the roots "
                       f"parent so the packet survives a clone to another machine")

    if isinstance(dies, list) and isinstance(conforms, list):
        if not dies and not conforms:
            out.append("what_dies and what_conforms are BOTH empty — a ruling that moves "
                       "nothing on disk has nothing for this gate to verify; it belongs "
                       "in the narrative decision record, not here")
        both = sorted(set(dies) & set(conforms))
        if both:
            out.append(f"a path cannot both die and conform: {both}")

    as_of = packet.get("as_of")
    if as_of is not None:
        if not isinstance(as_of, dict) or not as_of:
            out.append("as_of must be a non-empty {root: commit-ish} map — the two roots "
                       "are separate git repos, so one commit cannot address both")
        elif any(not isinstance(k, str) or not k.strip() or
                 not isinstance(v, str) or not v.strip() for k, v in as_of.items()):
            out.append("as_of holds an empty or non-string root or commit")
        elif isinstance(conforms, list) and not conforms:
            out.append("as_of on a packet with no what_conforms — as_of only changes "
                       "WHEN the conformers are measured; with none, it measures nothing")

    # THE CONFIRMATION FIELDS ARE THE DOOR'S TO WRITE, never the packet's. Until 2026-08-13
    # this refused `confirmed: true` outright, because confirmation was a separate act of
    # his and a self-confirming recorder had removed the only reader. Confirmation is now
    # DERIVED from `the_ruling_verbatim` at intake (asking him twice was the error), so the
    # refusal moved rather than vanished: the packet may not AUTHOR any of it. That keeps
    # the actual guard — the confirmation must be traceable to his words in this packet and
    # to nothing a recorder typed — while removing the second ask.
    authored = [f for f in ("confirmed", "confirmed_by", "confirmation_verbatim",
                            "confirmation_source", "reaffirmations") if f in packet]
    if authored:
        out.append(f"the packet authors {authored} — the confirmation fields are stamped "
                   "by the door from `the_ruling_verbatim`, so a recorder cannot write "
                   "its own sign-off in any of them")

    return out


def _refusals_what_dies_is_still_imported(packet: dict, roots_parent: str) -> list[str]:
    """The gate troubles/what-dies-sentences-files-the-corpus-still-imports was owed.

    ``what_dies`` means LITERAL DELETION — verify's tooth prints 'STILL ALIVE: <path> was
    ruled dead and is on disk'. On 2026-08-05 two packets sentenced cairn/tools/base/probe.py,
    the Probe primitive, while eight live modules imported it. Both were caught by hand,
    which is exactly the wrong mechanism: the lived symptom was Akien about to run
    ``cairn ruling confirm`` on a packet whose reading he agreed with, making 'delete the
    file eight modules import' a green instruction, with nothing on screen to show him the
    kill list was wrong.

    So the door asks the corpus instead of asking the author. A .py file with importers is
    not a file that dies; it is a file that CHANGES, and what_conforms is the field that
    already means that. The refusal names the importers, because 'this is wrong' without
    the eight paths is a second lookup the reader should not have to do (Law 7 — loud, and
    complete on the first pass).

    Scoped to Python under the ``cairn/`` root: that is where importing exists. A JSON or
    prose file is not covered and this does not pretend otherwise.
    """
    dying = [r for r in packet.get("what_dies", [])
             if isinstance(r, str) and r.endswith(".py") and r.startswith("cairn" + os.sep)]
    if not dying:
        return []
    repo = os.path.join(roots_parent, "cairn")
    try:
        graph = sieve.import_graph(repo)
    except OSError:
        return []                       # no tree to ask; do not invent a refusal
    if len(graph) < 20:
        return []                       # a hollow graph cannot clear anything (Law 8)
    out = []
    for rel in dying:
        inner = rel.split(os.sep, 1)[1]
        importers = sieve.importers_of(graph, inner)
        if importers:
            shown = ", ".join(importers[:8]) + (" …" if len(importers) > 8 else "")
            out.append(
                f"what_dies: {rel!r} is imported by {len(importers)} live module(s) — "
                f"{shown}. what_dies means DELETION and the verify tooth enforces it; a "
                "file the corpus still imports does not die, it CHANGES, and what_conforms "
                "is the field that means that")
    return out


def refusals_on_disk(packet: dict, roots_parent: str) -> list[str]:
    """The intake-time disk checks. Both directions catch me inventing the target.

    A ``what_dies`` path that does not exist is either already dead (nothing to rule) or
    a file I made up; a ``what_conforms`` path that does not exist is not a conformance at
    all but a new build. Either way the packet is describing a world that is not this one.
    """
    out: list[str] = []
    for name in ("what_dies", "what_conforms"):
        for rel in packet.get(name, []):
            if not isinstance(rel, str):
                continue
            if not os.path.exists(os.path.join(roots_parent, rel)):
                out.append(f"{name}: {rel!r} does not exist at intake — "
                           + ("already dead, or invented" if name == "what_dies"
                              else "nothing to conform; that is a new build, not a ruling"))

    out += _refusals_what_dies_is_still_imported(packet, roots_parent)

    as_of = packet.get("as_of")
    if isinstance(as_of, dict):
        for rel in packet.get("what_conforms", []):
            if not isinstance(rel, str):
                continue
            commit = as_of.get(_split_root(rel)[0])
            if not isinstance(commit, str):
                continue                        # no as_of for this root: the working tree
            try:
                fingerprint_at(roots_parent, rel, commit)
            except OSError as exc:
                out.append(f"as_of: {rel!r} does not resolve at {commit!r} — {exc}. A "
                           "ruling cannot conform a file that did not exist when it was "
                           "ruled; that is a new build, not a conformance")
    return out


def refusals(packet: dict, roots_parent: str | None = None) -> list[str]:
    shape = refusals_shape(packet)
    if shape:
        return shape                    # disk checks read fields the shape just refused
    return refusals_on_disk(packet, roots_parent or _roots_parent())


# ── the doors ─────────────────────────────────────────────────────────────────


def open_ruling(packet: dict, roots_parent: str | None = None) -> str:
    """THE INTAKE DOOR: refuse, or write the packet and return its path.

    Raises ``ValueError`` carrying EVERY refusal. On success the door stamps the fields it
    measures itself — the conforms fingerprints and ``confirmed`` — so neither can be
    authored by the thing being gated.

    THE RULING IS THE CONFIRMATION, and asking a second time is an ERROR (Akien,
    2026-08-13: "why you keep asking me to say yes to the thing i got so pissed off on and
    said THIS IS HOW ITS SUPPOSED TO WORK. THAT'S THE DAMN CONFIRMATION." / "ASKING ME
    REPEATEDLY IS AN ERROR."). This door used to stamp ``confirmed: false`` and send him to
    a second command, and the second command was CIRCULAR: it asked for his words to
    authorize his words. ``the_ruling_verbatim`` is already what he said, already required,
    already refused empty. If that field can be trusted then the packet is confirmed the
    moment it is written; if it cannot, then neither can a second quote typed by the same
    hand — I would be fabricating both halves. The door measured nothing and cost him a
    keystroke per ruling, which is Law 1's defect exactly: re-deriving the settled.

    WHAT IS NOT CLAIMED, because collapsing it into the above would be the check that goes
    green for the wrong reason: his words being HIS is now derived; his words matching MY
    READING of them (``now_the_spec_says``) is not, and never was — the old door did not
    measure that either. See filed edge (h) at this component's charter.

    THE WORD "RULED" IS NOT A SCHEMA FIELD. He offered it as his own habit ("I will start
    saying RULED after every goddamned one"), and requiring it would refuse a ruling for
    lacking a token — the same ask in a new costume, and this component's whole job is to
    stop asking twice.
    """
    rp = roots_parent or _roots_parent()
    bad = refusals(packet, rp)
    if bad:
        raise ValueError("ruling refused (" + str(len(bad)) + "):\n  - " + "\n  - ".join(bad))

    record = dict(packet)
    # DERIVED FROM HIS MARKER, never asked for a second time. RULED in his verbatim words
    # confirms the packet at intake; its absence leaves the packet as MY READING awaiting
    # his word — which is not a defect and does not stop the work (see `verify`).
    marked = ruled_marks(record)
    record["confirmed"] = bool(marked)
    if marked:
        record["confirmed_by"] = record.get("ruled_by", "Akien")
        record["confirmation_verbatim"] = marked
        record["confirmation_source"] = (
            "his RULED marker, inline in the ruling itself (Akien, 2026-08-13: \"I will "
            "start saying RULED after every goddamned one\")")
    as_of = record.get("as_of") if isinstance(record.get("as_of"), dict) else {}
    record["conforms_fingerprint"] = {
        rel: (fingerprint_at(rp, rel, as_of[_split_root(rel)[0]])
              if _split_root(rel)[0] in as_of
              else fingerprint(os.path.join(rp, rel)))
        for rel in sorted(record["what_conforms"])
    }

    d = store_dir(rp)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{record['id']}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def confirm(ruling_id: str, evidence: str, roots_parent: str | None = None) -> str:
    """A LATER RE-AFFIRMATION. Records additional words of his against a ruling already
    confirmed by the ruling it carries.

    NO LONGER A REQUIRED STEP, and that is the point (Akien, 2026-08-13: "ASKING ME
    REPEATEDLY IS AN ERROR"). Confirmation is derived at intake from
    ``the_ruling_verbatim`` — see ``open_ruling``. Nothing is UNCONFIRMED waiting on this
    verb, nothing prints an instruction to run it, and ``verify`` no longer reds for its
    absence. What survives is a door for the case that still has content: he says more
    about a ruling later, and those words are worth keeping beside it.

    ``evidence`` is required and refused empty, unchanged — a re-affirmation with no
    written source is reconstructible only from whoever ran the command. Recorded
    2026-07-31, the first time the verb was used for real: Akien typed the confirm command
    into the session rather than a shell, so the act was genuinely his but the hand on the
    keyboard was mine, and nothing in the record could tell the difference. That is why the
    instruction and the mediator are separate fields, and why the fix for the circularity
    was to derive confirmation rather than to trust a second quote from the same hand.

    APPENDS, NEVER OVERWRITES (Law 7): the confirmation the intake derived stays in the
    record, and later words land beside it in ``reaffirmations``.
    """
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError(
            "confirm requires the EVIDENCE of Akien's confirmation, verbatim — a "
            "confirmation with no written source is the defect this gate exists to fix, "
            "one layer up (`cairn ruling confirm <id> \"<his words>\"`)")

    rp = roots_parent or _roots_parent()
    path = os.path.join(store_dir(rp), f"{ruling_id}.json")
    if not os.path.exists(path):
        raise ValueError(f"no such ruling: {ruling_id}")
    with open(path, encoding="utf-8") as fh:
        record = json.load(fh)
    record["confirmed"] = True
    record["confirmed_by"] = record.get("ruled_by", "Akien")
    # APPEND. A record written before 2026-08-13 carries its confirmation here and this
    # verb was the only way it got one, so overwriting would erase the act; a record
    # written since carries the derived confirmation, and overwriting would replace HIS
    # RULING with a later aside. Neither is acceptable — Law 7, a record of truth.
    if not record.get("confirmation_verbatim"):
        record["confirmation_verbatim"] = evidence.strip()
    else:
        record.setdefault("reaffirmations", []).append(evidence.strip())
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def supersede(old_id: str, new_id: str, evidence: str,
              roots_parent: str | None = None) -> str:
    """THE RETIREMENT DOOR: retire ``old_id`` by stamping ``new_id`` as its successor.

    Writes ONLY to the superseding record — the retired packet is never touched, so
    Akien's confirmation on it survives byte-identical. Refuses with EVERY reason at
    once, matching the intake door:

      - evidence is required and refused empty, same rule as ``confirm`` and for the
        same reason: an unsourced retirement is reconstructible only from whoever ran
        the command;
      - both packets must exist in the store, and a packet cannot supersede itself;
      - the successor must be CONFIRMED — an unconfirmed reading cannot retire a
        confirmed act; that would be my guess outvoting his signature;
      - the successor must not itself be retired — a retired ruling answers for
        nothing;
      - the old packet must not already be retired — a second supersession of the same
        id would silently overwrite the first act's evidence.

    The act APPENDS to the successor's ``supersedes`` list. It used to assign to a single
    slot, which meant retiring a second packet by the same successor deleted the first
    retirement outright — measured 2026-08-06, not caught by the same-id guard above,
    because the guard watches the OLD id while the overwrite happens on the NEW one.
    """
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError(
            "supersede requires the EVIDENCE for the retirement, verbatim — an "
            "unsourced retirement is the confirm defect one layer up "
            "(`cairn ruling supersede <old> <new> \"<why, in his words>\"`)")

    rp = roots_parent or _roots_parent()
    records = load_all(rp)
    by_id = {r.get("id"): r for r in records}
    retired = retired_ids(records)

    out: list[str] = []
    if old_id not in by_id:
        out.append(f"no such ruling to retire: {old_id!r}")
    if new_id not in by_id:
        out.append(f"no such superseding ruling: {new_id!r}")
    if old_id == new_id:
        out.append("a ruling cannot supersede itself")
    new = by_id.get(new_id)
    if new is not None:
        # WAS "is it confirmed", which since 2026-08-13 is derived at intake and would
        # therefore pass for every door-written packet — a check going green for the
        # wrong reason, which is worse than no check. Re-pointed at what confirmation is
        # now DERIVED FROM. It can still fire, on exactly one path: a record hand-edited
        # after intake. Narrow, and honestly narrow, rather than vacuous and reassuring.
        if not _verbatim_of(new):
            out.append(f"{new_id} carries no ruling verbatim — nothing in it is his, so "
                       "it cannot retire an act that is")
        if new_id in retired:
            out.append(f"{new_id} is itself retired — a retired ruling answers for "
                       "nothing")
    if old_id in retired:
        out.append(f"{old_id} is already retired — a second supersession would "
                   "silently overwrite the first act's evidence")
    if out:
        raise ValueError("supersede refused (" + str(len(out)) + "):\n  - "
                         + "\n  - ".join(out))

    record = dict(new)
    record["supersedes"] = _supersessions(new) + [{"id": old_id,
                                                   "evidence": evidence.strip()}]
    path = os.path.join(store_dir(rp), f"{new_id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def _supersessions(record: dict) -> list[dict]:
    """THE ONE READER THAT KNOWS BOTH SHAPES — ``[{id, evidence}, …]``, oldest act first.

    The field was a single ``{id, evidence}`` dict until 2026-08-06 and two CONFIRMED
    records on disk still carry that shape. They are not migrated: rewriting a confirmed
    record to change a field's type is an in-place edit of his act, which is the thing
    this whole module refuses to do. Normalising on READ costs one function; normalising
    by rewrite costs the record. Anything unrecognisable reads as no supersession at all
    — a malformed field must never silently retire a live packet.
    """
    sup = record.get("supersedes")
    entries = [sup] if isinstance(sup, dict) else sup if isinstance(sup, list) else []
    return [e for e in entries if isinstance(e, dict) and isinstance(e.get("id"), str)]


def retired_ids(records: list[dict]) -> set[str]:
    """Every id retired by a CONFIRMED successor. A store-level fact, deliberately not
    part of ``verify`` — the mechanical verdict stays record-local, and whether anyone
    still has to ACT on that verdict is a property of the whole store."""
    out: set[str] = set()
    for r in records:
        if r.get("confirmed"):
            out.update(e["id"] for e in _supersessions(r))
    return out


def ruled_marks(record: dict) -> list[str]:
    """The lines of his verbatim in which he actually typed RULED, or an empty list.

    Returns the LINES rather than a bool so the confirmation records exactly which of his
    sentences carried the marker — a confirmation whose source cannot be pointed at is the
    defect this component was built for, one layer up.
    """
    return [s for s in _verbatim_of(record) if RULED.search(s)]


def _verbatim_of(record: dict) -> list[str]:
    """His actual words in a record, or an empty list — the whole basis of confirmation.

    Read the same way the intake refuses on it, so the door and the verdict cannot disagree
    about what counts as a ruling being present.
    """
    v = record.get("the_ruling_verbatim")
    if not isinstance(v, list):
        return []
    return [s for s in v if isinstance(s, str) and s.strip()]


def verify(record: dict, roots_parent: str | None = None) -> dict:
    """The mechanical verdict. ``{"id":…, "green": bool, "failures": [...]}``.

    Three things it can actually see, and it claims nothing beyond them:
      - the packet is CONFIRMED (an unconfirmed reading is my guess, and work sealed
        against a guess is unsealed work);
      - every ``what_dies`` path is GONE — this is the tooth that catches a file coming
        back, which is exactly what happened to ``_model.json``;
      - every ``what_conforms`` path still exists, carries a baseline fingerprint, and its
        bytes have CHANGED since that baseline — intake by default, or the commit named in
        ``as_of`` when the packet was written after its own work landed.

    It does NOT claim the change was the right change. That is not mechanical and saying
    so here would be a check that goes green for the wrong reason.
    """
    rp = roots_parent or _roots_parent()
    record_of_checks = inspect(record, rp)
    failures = [f for e in record_of_checks if not gate.passed(e)
                for f in e["values"]["failures"]]

    # `green` is about THE WORK. `ruled` is about whether he has spoken. Two facts, two
    # fields — the same shape the gate primitive was rebuilt on this morning: state both,
    # never collapse one into the other.
    return {"id": record.get("id"), "green": not failures, "failures": failures,
            "ruled": bool(record.get("confirmed")), "record": record_of_checks}


def _checked(identity: str, *, expected, actual, location: str,
             failures: list[str], **values) -> dict:
    """One entry of this gate's proof record, in the seed's shape.

    ``failures`` rides as a LIST and the refusal sentence is joined from it, never split
    back out of one — a failure legitimately contains the separator, and re-splitting a
    string you just joined is a parser guessing at its own output.
    """
    return gate.proved(identity=identity, expected=expected, actual=actual,
                       location=location, code="ruling.py:%s" % identity,
                       source="ruling.inspect", failures=list(failures),
                       lack="; ".join(failures), **values)


def inspect(record: dict, roots_parent: str | None = None) -> list[dict]:
    """THE PROOF RECORD ``verify`` opens on: one entry per check that RAN, EXPECTED
    beside ACTUAL, passes included (Akien, 2026-08-13: "EVERYTHING ALWAYS PROVED AND
    LISTING WHAT IT PROVED ... SAME PATTERN EVERYWHERE").

    What it retires, and it is the defect the ruling names: ``verify`` returned only
    ``failures``, so a packet reading GREEN said the same thing whether every path was
    measured and moved, or ``what_conforms`` was empty, or the walk never ran. `cairn
    ruling list` printed 42 greens over a list of nothing. Each lane now states what it
    EXPECTED and what it ACTUALLY found, so a lane that stops running makes the record
    SHORTER rather than cleaner.

    A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED: the baseline lane covers only the
    conformers that EXIST, and the change lane only those that carry a baseline, because
    a vanished file has no bytes to fingerprint and a fingerprint that was never taken
    has nothing to differ from. Each is one fault, reported once, by the lane above.
    """
    rp = roots_parent or _roots_parent()
    out: list[dict] = []
    verbatim = _verbatim_of(record)
    out.append(_checked(
        "the_packet_carries_a_ruling",
        expected="the_ruling_verbatim carries his words",
        actual=("the_ruling_verbatim carries his words" if verbatim
                else "the_ruling_verbatim is empty or missing"),
        location="the_ruling_verbatim",
        lines=len(verbatim) if isinstance(verbatim, list) else (1 if verbatim else 0),
        failures=[] if verbatim else [
            "NO RULING IN THE PACKET — `the_ruling_verbatim` is empty or missing, so "
            "nothing here is his. The intake refuses this, so a record in this state was "
            "edited after it was written."]))

    dies = list(record.get("what_dies", []))
    alive = [rel for rel in dies if os.path.exists(os.path.join(rp, rel))]
    out.append(_checked(
        "every_ruled_dead_path_is_gone",
        expected=[], actual=sorted(alive),
        location="what_dies",
        failures=["STILL ALIVE: %s was ruled dead and is on disk" % rel
                  for rel in sorted(alive)],
        sentenced=len(dies)))

    conforms = list(record.get("what_conforms", []))
    prints = record.get("conforms_fingerprint", {})
    baseline = "the ruling" if record.get("as_of") else "intake"

    present = [rel for rel in conforms if os.path.exists(os.path.join(rp, rel))]
    out.append(_checked(
        "every_conformer_still_exists",
        expected=sorted(conforms), actual=sorted(present),
        location="what_conforms",
        failures=["VANISHED: %s was to conform, not to die" % rel
                  for rel in sorted(set(conforms) - set(present))]))

    # GUARDED: a path that is gone cannot be fingerprinted. Asking anyway would report
    # the same single fault twice, in two different vocabularies.
    if present:
        measured = [rel for rel in present if rel in prints]
        out.append(_checked(
            "every_conformer_carries_a_baseline",
            expected=sorted(present), actual=sorted(measured),
            location="conforms_fingerprint",
            # Unreachable through the door, which stamps every conformer. Reachable by a
            # hand-edit that moves a path into what_conforms — and a missing baseline used
            # to read as PASSED, so the weakest possible check wore the strongest verdict.
            failures=["UNMEASURED: %s carries no baseline fingerprint — its conformance "
                      "was never measured, which is not the same as measured and green"
                      % rel for rel in sorted(set(present) - set(measured))]))

        if measured:
            moved = [rel for rel in measured
                     if prints[rel] != fingerprint(os.path.join(rp, rel))]
            out.append(_checked(
                "every_conformer_changed_since_its_baseline",
                expected=sorted(measured), actual=sorted(moved),
                location="what_conforms",
                failures=["UNTOUCHED: %s is byte-identical to %s" % (rel, baseline)
                          for rel in sorted(set(measured) - set(moved))],
                baseline=baseline))
    return out


def load_all(roots_parent: str | None = None) -> list[dict]:
    """Every ``kind: "ruling"`` record in the store, oldest id first.

    The store's older narrative ``kind: "decision"`` entries are skipped, not migrated —
    they are a different artifact with a different job, and rewriting them to fit this
    gate would be the gate inventing history it was not present for.
    """
    d = store_dir(roots_parent)
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, name), encoding="utf-8") as fh:
                record = json.load(fh)
        except Exception:
            continue                    # a store this gate did not write is not its business
        if isinstance(record, dict) and record.get("kind") == KIND:
            out.append(record)
    return out


def open_rulings(roots_parent: str | None = None) -> list[dict]:
    """Every ruling whose verdict is red AND still anyone's to act on — unconfirmed,
    or contradicted on disk, and not retired by a confirmed successor. A superseded
    packet stays on disk and stays red under ``verify``; it is simply no longer OPEN,
    because its successor answers for it."""
    rp = roots_parent or _roots_parent()
    records = load_all(rp)
    retired = retired_ids(records)
    return [v for v in (verify(r, rp) for r in records if r.get("id") not in retired)
            if not v["green"]]

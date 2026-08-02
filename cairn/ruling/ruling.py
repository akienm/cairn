"""cairn/ruling/ruling.py — THE RULING INTAKE GATE. Akien rules; before any code moves,
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
in the existing code and is already built as ``cairn/orient/``. The intention names them
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

    cairn ruling open <packet.json>      # intake: refuse or write
    cairn ruling list                    # what is open or red
    cairn ruling verify <id>             # the mechanical verdict
    cairn ruling confirm <id>            # Akien's act, not mine
    cairn ruling supersede <old> <new>   # retire a misfiled packet, evidence required
    python3 cairn/ruling/proofs/test_ruling.py    # exit 0 = green
"""

from __future__ import annotations

import hashlib
import json
import os
import re

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
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # <repo>/cairn
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

    if packet.get("confirmed") is True:
        out.append("confirmed cannot be true at intake — confirmation is Akien's separate "
                   "act (`cairn ruling confirm`), and a recorder that self-confirms has "
                   "removed the only reader the gate exists for")

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
    measures itself — ``confirmed: false`` and the conforms fingerprints — so neither can
    be authored by the thing being gated.
    """
    rp = roots_parent or _roots_parent()
    bad = refusals(packet, rp)
    if bad:
        raise ValueError("ruling refused (" + str(len(bad)) + "):\n  - " + "\n  - ".join(bad))

    record = dict(packet)
    record["confirmed"] = False
    record["conforms_fingerprint"] = {
        rel: fingerprint(os.path.join(rp, rel)) for rel in sorted(record["what_conforms"])
    }

    d = store_dir(rp)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{record['id']}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def confirm(ruling_id: str, evidence: str, roots_parent: str | None = None) -> str:
    """Akien's act. Flips ``confirmed`` and records WHO SAID SO, verbatim.

    ``evidence`` is required and refused empty. A bare ``confirmed: true`` would be the
    same defect this whole component exists to fix, one layer up: a confirmation with no
    written source, which the next reader can only reconstruct from whoever ran the
    command. Recorded 2026-07-31, the first time the verb was used for real — Akien typed
    the confirm command into the session rather than a shell, so the act was genuinely his
    but the hand on the keyboard was mine, and nothing in the record could tell the
    difference. Now the record carries his instruction and the mediator, and the two are
    separate fields because they are separate facts.
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
    record["confirmation_verbatim"] = evidence.strip()
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
        if not new.get("confirmed"):
            out.append(f"{new_id} is UNCONFIRMED — an unconfirmed reading cannot "
                       "retire a confirmed act")
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
    record["supersedes"] = {"id": old_id, "evidence": evidence.strip()}
    path = os.path.join(store_dir(rp), f"{new_id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def retired_ids(records: list[dict]) -> set[str]:
    """Every id retired by a CONFIRMED successor. A store-level fact, deliberately not
    part of ``verify`` — the mechanical verdict stays record-local, and whether anyone
    still has to ACT on that verdict is a property of the whole store."""
    out: set[str] = set()
    for r in records:
        sup = r.get("supersedes")
        if r.get("confirmed") and isinstance(sup, dict) and isinstance(sup.get("id"), str):
            out.add(sup["id"])
    return out


def verify(record: dict, roots_parent: str | None = None) -> dict:
    """The mechanical verdict. ``{"id":…, "green": bool, "failures": [...]}``.

    Three things it can actually see, and it claims nothing beyond them:
      - the packet is CONFIRMED (an unconfirmed reading is my guess, and work sealed
        against a guess is unsealed work);
      - every ``what_dies`` path is GONE — this is the tooth that catches a file coming
        back, which is exactly what happened to ``_model.json``;
      - every ``what_conforms`` path still exists and its bytes have CHANGED since intake.

    It does NOT claim the change was the right change. That is not mechanical and saying
    so here would be a check that goes green for the wrong reason.
    """
    rp = roots_parent or _roots_parent()
    failures: list[str] = []

    if not record.get("confirmed"):
        failures.append("UNCONFIRMED — Akien has not signed this reading off "
                        f"(`cairn ruling confirm {record.get('id')}`)")

    for rel in record.get("what_dies", []):
        if os.path.exists(os.path.join(rp, rel)):
            failures.append(f"STILL ALIVE: {rel} was ruled dead and is on disk")

    prints = record.get("conforms_fingerprint", {})
    for rel in record.get("what_conforms", []):
        abs_path = os.path.join(rp, rel)
        if not os.path.exists(abs_path):
            failures.append(f"VANISHED: {rel} was to conform, not to die")
        elif prints.get(rel) == fingerprint(abs_path):
            failures.append(f"UNTOUCHED: {rel} is byte-identical to intake")

    return {"id": record.get("id"), "green": not failures, "failures": failures}


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

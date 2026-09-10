"""A ticket's crossings, DERIVED from the journals — never read off the ticket.

Ticket:  CairnCommons/tickets/d2ecdb867bc9-a-crossing-is-derived-from-the-journal-never-stored-on-the-ticket.json
Ruling:  CairnCommons/decisions/2026-09-10-crossings-are-derived-never-written.json

WHY THIS EXISTS. A gate must not write its own input. ``crossings`` was a hand-written array
on the ticket that five non-proof read sites treated as gate evidence — the clearance gate,
proof_coverage, hollow and codemother's shim all decided things by reading it — and NOTHING
WROTE IT. Measured 2026-09-10 over the live corpus: 271 tickets, 42 carrying a crossings LIST
(99 dict entries) and 1 carrying PROSE where readers parse a list of dicts; **zero writers**.
Every one of those 99 entries got there by a hand. Meanwhile ``emit`` — the chokepoint every
crossing already rides — journals the same crossing into the component's own history.json as
the record of truth (Law 7). So the evidence existed twice: once written by physics, once by a
hand, and the readers were reading the hand.

THE DERIVATION RULE, AND IT WAS SETTLED BY MEASUREMENT RATHER THAN BY ARGUMENT. Three candidate
rules were run against all 42 tickets carrying a stored list:

  * latest-crossing-naming-any     → 40 agree, 2 disagree
  * union over every crossing      → 35 agree, 7 disagree (1 LOSS)
  * union since the latest BUILDME → 36 identical, 6 derived-superset, **0 loss**

The third is what ``proven_by_since_buildme`` implements. It is also exactly the rule
``proof_coverage._proven_by``'s docstring argues for when it says "latest, not first": a ticket
kicked back to BUILDME and re-crossed must not be checked against the proof it abandoned.
Cutting at the latest BUILDME says that, and keeps every proof of the build that STANDS.

``also_proven_by`` IS READ, AND THAT ONE KEY IS WHAT MAKES THE DERIVATION LOSSLESS. One journal
entry of 677 carries it (trouble's PROVEME crossing for ticket 9579a6f9cec6), and it is exactly
the entry that the stored/derived comparison flagged at risk: the stored crossing named three
proofs, the journal's ``proven_by`` named one, and the other two sat in ``also_proven_by``.
Read one key and that ticket loses ``cairn/tools/base/proofs/test_raise_trouble.py`` from
hollow's instrument set. Read both and the derived set is byte-identical to the stored one.
n=1 is the whole population of that key today, which is why it is read by name and not by guess.

TWO READING VERBS, NOT ONE, and their difference is deliberate. ``proven_by_latest`` answers
"which proof does THIS crossing stand on" (proof_coverage's gate, codemother's shim);
``proven_by_since_buildme`` answers "which instruments can measure this build at all" (hollow).
Bending one reader to serve both questions is the defect recorded at ticket
proven-by-answers-two-questions-and-one-reader-serves-both — so there are two verbs with their
reasons written down, over one derivation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.address import ROOTS

__all__ = [
    "journals", "crossings_for", "has_crossings",
    "proven_by_latest", "proven_by_since_buildme", "buildme_crossing",
]


def _roots(roots: dict[str, Path] | None = None) -> dict[str, Path]:
    return dict(ROOTS) if roots is None else dict(roots)


def journals(roots: dict[str, Path] | None = None) -> list[Path]:
    """Every history.json in class-space and in the commons, sorted.

    BOTH roots, and the commons half is not optional: a concept-piece ticket journals to
    ``intentions-not-beside-code/history.json`` or ``intentions-congruency-lab/history.json``
    and to nowhere in class-space. A first scan of class-space alone left 3 stored entries
    with no journal match; adding the two commons journals dropped that to 2.
    """
    r = _roots(roots)
    out: list[Path] = []
    for key in ("repo", "commons"):
        base = r.get(key)
        if base and Path(base).is_dir():
            out.extend(sorted(Path(base).rglob("history.json")))
    return out


_CACHE: dict[tuple, dict[str, list[dict]]] = {}


def _index(roots: dict[str, Path] | None = None) -> dict[str, list[dict]]:
    """{ticket_id: [journal entry, ...]} over both roots, in ``at`` order.

    Cached on the (path, mtime, size) of every journal, so a call that follows a crossing
    sees it. The invalidation is a stat of ~50 files rather than a watcher — the reader IS
    the event, which is the same shape the intentions model compiler's gate uses.
    """
    files = journals(roots)
    key = tuple((str(f), *(lambda s: (s.st_mtime_ns, s.st_size))(f.stat())) for f in files)
    hit = _CACHE.get(key)
    if hit is not None:
        return hit
    idx: dict[str, list[dict]] = {}
    for f in files:
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        entries = doc.get("entries") if isinstance(doc, dict) else doc
        if not isinstance(entries, list):
            continue
        rel = _rel(f, roots)
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            tid = entry.get("ticket")
            if not tid:
                continue
            one = dict(entry)
            one["journal"] = rel
            idx.setdefault(str(tid), []).append(one)
    for tid in idx:
        idx[tid].sort(key=lambda e: str(e.get("at") or ""))
    _CACHE.clear()          # one live index; the old one can only be staler
    _CACHE[key] = idx
    return idx


def _rel(path: Path, roots: dict[str, Path] | None = None) -> str:
    """Repo-relative where the path is under the repo, commons-parent-relative otherwise.

    The stored arrays wrote journals repo-relative (``cairn/devices/trouble/history.json``)
    and the commons ones with the CairnCommons prefix, so both shapes are reproduced rather
    than normalised to one — a consumer that joins on this string joins on what it always saw.
    """
    r = _roots(roots)
    p = Path(path).resolve()
    repo = Path(r["repo"]).resolve()
    try:
        return str(p.relative_to(repo))
    except ValueError:
        pass
    try:
        return str(p.relative_to(repo.parent))
    except ValueError:
        return str(p)


def _norm_proof(one: str, roots: dict[str, Path] | None = None) -> str:
    """A proof path as the repo sees it. The journals carry both absolute and relative forms
    for the same file; a set comparison over the raw strings reports a difference that is only
    a prefix (measured: 1 of the 2 disagreements under the latest-crossing rule was exactly this)."""
    r = _roots(roots)
    s = str(one).strip()
    if not s:
        return s
    repo = str(Path(r["repo"]).resolve())
    if s.startswith(repo + os.sep):
        return s[len(repo) + 1:]
    return s


def _named(entry: dict, roots: dict[str, Path] | None = None) -> list[str]:
    """Every proof this ONE crossing names — ``proven_by`` and ``also_proven_by`` both, deduped
    in first-seen order. Read as one-or-many because a seam has more than one end."""
    out: list[str] = []
    for key in ("proven_by", "also_proven_by"):
        raw = entry.get(key)
        if not raw:
            continue
        many = [raw] if isinstance(raw, str) else [str(x) for x in raw if x]
        for one in many:
            got = _norm_proof(one, roots)
            if got and got not in out:
                out.append(got)
    return out


def crossings_for(ticket_id: str, roots: dict[str, Path] | None = None) -> list[dict]:
    """This ticket's crossings, oldest first, derived from every journal in both roots.

    The returned records carry the fields the stored arrays carried and the readers read —
    ``to``, ``from``, ``direction``, ``journal``, ``proven_by`` — plus the ``at`` the stored
    ones never had. ``date`` is derived from ``at`` so a consumer written against the stored
    shape does not have to change to keep working; a consumer that wants the second reads ``at``.
    """
    if not ticket_id:
        return []
    out: list[dict] = []
    for entry in _index(roots).get(str(ticket_id), []):
        at = str(entry.get("at") or "")
        named = _named(entry, roots)
        out.append({
            "at": at,
            "date": at.split("T")[0] if at else "",
            "from": entry.get("from"),
            "to": entry.get("to"),
            "direction": entry.get("direction"),
            "journal": entry.get("journal"),
            "by": entry.get("actor") or entry.get("cleared_by"),
            "proven_by": named[0] if len(named) == 1 else named,
            "proofs": named,
            "seq": entry.get("seq"),
        })
    return out


def has_crossings(ticket_id: str, roots: dict[str, Path] | None = None) -> bool:
    """Whether ANY journal in either root records a crossing for this ticket.

    The distinction proof_coverage draws between ``crossing_record_absent`` and ``proof_named``
    is worth keeping and is not the same question as "does it name a proof": a ticket that
    never crossed anything is archaeology, one that crossed and named nothing is actionable.
    """
    return bool(_index(roots).get(str(ticket_id)))


def proven_by_latest(ticket_id: str, roots: dict[str, Path] | None = None) -> list[str]:
    """The proofs named by the LATEST crossing that names any — and only it.

    THE GATE'S RULE, and the reason is a kick-back: a ticket sent back to BUILDME and re-crossed
    must not be checked against the proof it abandoned. Consumers: ``proof_coverage._proven_by``
    and ``codemother/shim.py``'s proofs_pending read, which already implemented this rule
    separately and identically.
    """
    for entry in reversed(crossings_for(ticket_id, roots)):
        if entry["proofs"]:
            return list(entry["proofs"])
    return []


def buildme_crossing(ticket_id: str, roots: dict[str, Path] | None = None) -> dict | None:
    """The LATEST FORWARD crossing into BUILDME — the start of the build that STANDS.

    ``direction`` is checked here where the stored-array reader could not: a stored entry
    carried no direction at all, so a kick-back INTO BUILDME and a disposition looked the same
    as a forward crossing. Returns None when the ticket never crossed BUILDME; the caller
    decides whether that is unmeasurable or merely empty.
    """
    for entry in reversed(crossings_for(ticket_id, roots)):
        if entry.get("to") == "BUILDME" and entry.get("direction") == "forward":
            return entry
    return None


def proven_by_since_buildme(ticket_id: str, roots: dict[str, Path] | None = None) -> list[str]:
    """Every proof named at or after the latest forward BUILDME crossing — the UNION.

    HOLLOW'S RULE, and it is deliberately not ``proven_by_latest``. Measured 2026-09-09: read
    latest-only, hollow reported FIVE of eight ``writes_to`` files hollow on 9579a6f9cec6; read
    as the union, none. A seam is proved by several proofs at several addresses, and the reading
    that asks "could ANY instrument have caught this file" needs all of them.

    The cut at BUILDME is what keeps that union from also picking up the abandoned proof of a
    build that was kicked back — the same reason ``proven_by_latest`` takes the latest. Measured
    over all 42 tickets that carried a stored array: 36 identical, 6 derived-superset, 0 loss.
    """
    entries = crossings_for(ticket_id, roots)
    start = 0
    for i, entry in enumerate(entries):
        if entry.get("to") == "BUILDME" and entry.get("direction") == "forward":
            start = i
    out: list[str] = []
    for entry in entries[start:]:
        for one in entry["proofs"]:
            if one not in out:
                out.append(one)
    return out


# --------------------------------------------------------------------------------------
# THE ONE-SHOT MIGRATION. Kept beside the derivation on purpose: what it removes and what
# replaces it are one act, and a migration living somewhere else is a script that outlives
# its reason with nobody able to see what it undid.
# --------------------------------------------------------------------------------------

def _prose_note(text: str) -> str:
    return ("2026-09-10 — this text stood in the ticket's ``crossings`` field, where four "
            "gate-reading sites parsed a list of dicts. It is prose, not a crossing record, "
            "and it is kept because it establishes what is going on with this ticket right "
            "now (Law 5), not merely what happened. Moved here whole by the migration under "
            "ruling 2026-09-10-crossings-are-derived-never-written. Verbatim:\n\n" + text)


def _carried_note(entry: dict, journalled: bool) -> str:
    where = ("the journal records this crossing; the note did not ride it"
             if journalled else
             "NO JOURNAL IN EITHER ROOT RECORDS THIS CROSSING — this note was its only record")
    return (f"2026-09-10 crossing note carried out of the ticket's ``crossings`` field "
            f"({entry.get('date') or entry.get('at') or 'undated'} → {entry.get('to')}, "
            f"by {entry.get('by') or 'unrecorded'}, door {entry.get('door') or 'unrecorded'}; "
            f"{where}). Kept under Law 5 — the array was a second copy of the journal, but "
            f"these words were not: measured 2026-09-10, 66 of 79 stored notes appeared "
            f"nowhere else in either root, and they carry Akien's verbatim approvals, "
            f"back-edge reasons and ruling citations. Verbatim: " + str(entry.get("note")))


def _note_is_elsewhere(note: str, derived: list[dict], ticket_id: str,
                       roots: dict[str, Path] | None = None) -> bool:
    """Whether a journal entry for this ticket already carries these words.

    A 60-character probe rather than an equality test: the journal wrapped the same sentence
    differently in places, and an equality test would have called 13 duplicates unique and
    carried them twice."""
    probe = note.strip()[:60]
    if not probe:
        return True
    blob = json.dumps(_index(roots).get(str(ticket_id), []), ensure_ascii=False)
    return probe in blob


def drop_stored_crossings(roots: dict[str, Path] | None = None, *, apply: bool = False) -> dict:
    """Remove the ``crossings`` key from every commons ticket that carries one.

    NOT A DELETE OF EVIDENCE — a delete of a SECOND COPY of evidence that no writer wrote.
    The journals hold every one of these crossings as the record of truth (Law 7), and this
    voyage measured the derived reading against the stored one over all 42 list-carriers
    before removing anything: 36 identical, 6 derived-superset, 0 loss. The comparison had
    to happen first because after this verb runs it cannot be taken again.

    WHAT IS NOT A SECOND COPY IS CARRIED OUT, NOT DROPPED — and finding that out is why this
    verb is longer than a ``del``. Measured 2026-09-10 before anything was written:

      * 79 stored entries carry a ``note``, and **66 of them appear nowhere else in either
        root**. They hold Akien's verbatim approvals ("passes review all the way to buildme"),
        back-edge reasons, and ruling citations. The array was duplicative; these words were
        not, and Law 5 is explicit that history moved out is kept and greppable, never
        destroyed. They land in ``notes`` with the crossing they annotated named around them.
      * THREE stored entries have no journal twin at all, and two of them
        (``0682e51ab011`` and ``6bc43453ca64``) claim ``door: transitions.emit`` while no
        journal in either root records the crossing. The door did not fire; a hand wrote a
        record saying it had. That is the exact defect this ruling exists to end, and the
        migration does not paper over it: those tickets derive to zero crossings afterward,
        their cursors read BUILDME with nothing journalled behind them, and proof_coverage
        will say ``crossing_record_absent`` — which is true, and was true before, and was
        invisible while a hand-written array said otherwise.
      * ONE ticket (``326f1c2c99c4``) stored a PARAGRAPH where the readers parsed dicts — a
        census that iterated it yielded 817 single-character "entries". It records a gate
        refusal, why the gate was right, and what the next session's first move is: history
        still under way, so Law 5 puts it beside the thing.

    Default is a DRY RUN. ``apply=True`` writes through ``transitions._write_ticket`` — the
    atomic writer that reproduces each file's measured serialisation — because a git-tracked
    record of truth must not be half-written, and because re-implementing the writer here is
    how two spellings of one file appear in ``git status``.
    """
    from cairn.tools.base.transitions import _write_ticket

    r = _roots(roots)
    tickets = Path(r["commons"]) / "tickets"
    report: dict = {"applied": bool(apply), "removed": [], "prose_moved": [], "empty": [],
                    "notes_carried": 0, "unjournalled": [], "unreadable": []}
    if not tickets.is_dir():
        return report
    for path in sorted(tickets.glob("*.json")):
        try:
            raw = path.read_bytes()
            doc = json.loads(raw.decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            report["unreadable"].append({"ticket": path.name, "why": str(exc)})
            continue
        if not isinstance(doc, dict) or "crossings" not in doc:
            continue
        # THE SHAPE IS READ BEFORE THE MUTATION, and that ordering is the contract:
        # ``_ticket_shape`` discovers which (ensure_ascii, newline) pair reproduces ``raw``
        # from the doc AS IT STANDS ON DISK. Handing it the edited doc asks it to reproduce
        # the old bytes from the new content, which no pair can do — it refuses, correctly,
        # and the migration dies on its first file with nothing written.
        from cairn.tools.base.transitions import _ticket_shape as _shape_of
        ensure_ascii, newline = _shape_of(raw, doc)
        value = doc["crossings"]
        tid = str(doc.get("id") or path.stem.split("-")[0])
        notes = doc.get("notes")
        notes = list(notes) if isinstance(notes, list) else ([notes] if notes else [])
        carried = 0

        if isinstance(value, str) and value.strip():
            notes.append(_prose_note(value))
            report["prose_moved"].append({"ticket": tid, "chars": len(value)})
        elif isinstance(value, list) and value:
            derived = crossings_for(tid, roots)
            seen_pairs = {(e.get("to"), e.get("date")) for e in derived}
            for entry in value:
                if not isinstance(entry, dict):
                    continue
                journalled = (entry.get("to"), entry.get("date")) in seen_pairs
                if not journalled and entry.get("to") not in {e.get("to") for e in derived}:
                    report["unjournalled"].append(
                        {"ticket": tid, "to": entry.get("to"), "date": entry.get("date"),
                         "claimed_door": entry.get("door")})
                note = str(entry.get("note") or "").strip()
                if note and not _note_is_elsewhere(note, derived, tid, roots):
                    notes.append(_carried_note(entry, journalled))
                    carried += 1
            report["removed"].append({"ticket": tid, "entries": len(value),
                                      "derived": len(derived), "notes_carried": carried})
            report["notes_carried"] += carried
        else:
            report["empty"].append({"ticket": tid})

        del doc["crossings"]
        if notes:
            doc["notes"] = notes
        if apply:
            _write_ticket(path, doc, ensure_ascii, newline)
    return report


if __name__ == "__main__":
    import sys
    print(json.dumps(drop_stored_crossings(apply="--apply" in sys.argv[1:]), indent=2))

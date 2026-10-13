"""aider_shim_edit_survival — did the APPRENTICE's work survive, or did the hand rewrite it?

THE TICKET'S WATCHME, COMPILED. The spec (CairnCommons/tickets/aider-builds-a-piece.json)
names this exact path, and the emission gate resolves ARMED from it, so this module is what
stands between the WATCHME crossing and a refusal. Its fields are that spec's, kept in the
spec's own words where they are the answer:

  trigger  — "each driven piece reaches a disposition — the driver's own result write is the
             event that already fires, and the comparison is read at the ticket's PROVED
             crossing. No poll"
  enough   — "five driven pieces with survival recorded — the same five the offload probe
             waits for, deliberately, so the two watches answer their different questions
             over ONE population rather than each demanding its own five real tickets"
  carrier  — per driven piece: the edit as the apprentice applied it, versus the same files
             as they stand at the ticket's PROVED commit, dispositioned
             survived | rewritten | discarded
  nexus    — the hypothesize tree, the same one aider_shim_offload_yield deposits to
  consumer — Akien at triage (offload-more vs pull-back is his call)

WHY THIS IS NOT THE OFFLOAD PROBE'S QUESTION, in the spec's own words: "a ticket can pass
its physics green while every line the apprentice wrote was thrown away and rewritten by CC
— the offload buying nothing while reporting success." That is a hollow green (Law 8) and
nothing else in the system would say so. The pair is the point: one watch asks whether the
build PASSED, this one asks WHO EARNED IT.

THE VOCABULARY IS THE DRIVER'S, TRANSLATED ONCE AND VISIBLY. ``driver.survival`` answers in
four words and the spec asks for three, and the mismatch is real rather than sloppy:

  survived      -> survived      the file is still what the drive left
  changed_again -> rewritten     somebody moved it since; neither image matches
  reverted      -> discarded     back to exactly what it was before the drive
  untouched     -> not-applied   the drive changed nothing HERE — not a disposition of an
                                 edit, because there was no edit. Collapsing it into
                                 `discarded` would report a drive that did nothing as a
                                 drive whose work was thrown away, which is the difference
                                 between "the apprentice is being overruled" and "the
                                 apprentice is not producing", and those call for opposite
                                 decisions from the consumer.

THE ROLL-UP DOES NOT COLLAPSE A MIXTURE (Law 7). A drive that edits four files and has two
survive and two rewritten is reported as `mixed`, with the per-file dispositions carried
whole. A presentation surface may collapse; this is a record of truth on its way to a
triage decision, and "mostly survived" is exactly the shape that would make an offload look
better than it is.

WHAT IS COMPARED AGAINST WHAT, AND THE HOLE IN IT. The spec says "as they stand at the
ticket's PROVED commit". This reads the WORKING TREE, because ``driver.survival`` does —
composing the primitive the device already owns beats minting a second, git-shaped one that
could disagree with it. At the PROVED crossing those are the same state, which is when the
trigger says to read. Fired later they are not, so the carrier records the HEAD the
comparison was taken against: a receiver can then see for itself whether the reading was
taken at the moment the spec meant. Naming the drift beats pretending it is not there, and
beats a second implementation that would have to be kept honest against the first.

A PROBE CARRIES NO AUTHORITY (Law 6). This reads ``drives.jsonl`` and the working tree, and
writes nothing anywhere. It deposits and pokes; re-opening a node whose intention did not
work is the owner's act.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from cairn.tools.base.probe import Probe

TICKET = "aider-builds-a-piece"

#: The spec's three words, plus the honest fourth. Read by `_disposition`; never re-spelled
#: at a call site, so a change here cannot leave one reader on the old vocabulary.
_SPEAK = {
    "survived": "survived",
    "changed_again": "rewritten",
    "reverted": "discarded",
    "untouched": "not-applied",
}


def _head(root) -> str | None:
    """The commit the working tree is sitting on, or None if that cannot be read.

    Carried so the receiver can tell whether the comparison was taken where the spec meant
    it (at PROVED) or somewhere downstream. A probe that cannot answer this says None rather
    than guessing — an unmeasured claim is a hypothesis (Law 3), and a wrong sha here would
    make a stale reading look authoritative.
    """
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def _roll_up(per_file: dict) -> str:
    """One word for the drive, and `mixed` whenever one word would be a lie."""
    spoken = {v for v in per_file.values()}
    real = spoken - {"not-applied"}
    if not per_file:
        return "nothing-recorded"
    if not real:
        return "not-applied"
    if len(real) == 1:
        return real.pop()
    return "mixed"


def _identity(rec: dict) -> tuple:
    """A drive's own identity, minted by the driver at drive time.

    ONE DRIVE APPENDED TWICE IS STILL ONE DRIVE, and `enough` is a count — a store that
    gained a row by accident would retire this watch early, having learned four fifths of
    what it asked for. Observed at n=1 on the day this was built: the live-fire caller
    called `driver.record` on a result `drive_brief` had already recorded, and the real
    store carried two rows per drive with byte-identical `at`. The log is append-only and
    its rows are true — both writes really happened — so the collapse belongs to the
    reader, not to the record. `at` is an isoformat timestamp with microseconds taken once
    per drive, so two genuinely separate drives cannot collide on it.
    """
    return (rec.get("ticket"), rec.get("piece_index"), rec.get("at"))


def dispositions(*, drives_path=None, root=None) -> list[dict]:
    """One row per driven piece, oldest first, in the spec's vocabulary.

    Composed from the driver's own reader and its own survival answer — this module owns no
    second opinion about what a drive record means, which is what keeps the two from
    drifting apart the way `criteria`/`verdicts` did on the sibling probe.
    """
    from cairn.devices.aider_shim import driver  # noqa: PLC0415

    root = Path(root) if root is not None else driver.REPO
    rows = []
    seen = set()
    for rec in driver.drives(drives_path if drives_path is not None else driver.DEFAULT_DRIVES):
        ident = _identity(rec)
        if ident in seen:
            continue
        seen.add(ident)
        raw = driver.survival(rec, root=root)
        per_file = {rel: _SPEAK.get(word, word) for rel, word in raw.items()}
        rows.append({
            "ticket": rec.get("ticket"),
            "piece_index": rec.get("piece_index"),
            "at": rec.get("at"),
            "model": rec.get("model"),
            "applied": rec.get("aider_reported_edited") or [],
            "hashes_moved": [rel for rel, was in (rec.get("before") or {}).items()
                             if (rec.get("after") or {}).get(rel) != was],
            "per_file": per_file,
            "disposition": _roll_up(per_file),
            "error": rec.get("error") or "",
        })
    return rows


def _recorded(rows: list[dict]) -> list[dict]:
    """The rows that actually carry a survival reading.

    A drive that applied nothing has no edit whose survival could be asked about, so it does
    NOT count toward `enough` — five drives that all failed to produce an edit would retire
    this watch having learned nothing about survival, which is the same hollow-stop the
    sibling probe's `enough` was written to refuse.
    """
    return [r for r in rows if r["disposition"] not in ("not-applied", "nothing-recorded")]


def _trigger(now=None, context=None) -> bool:
    """True when a driven piece carries a disposition it did not carry before.

    NOT A POLL. The driver's record write is the event that already fires; this asks whether
    that event has left something new behind. The count rides `context` because a Probe is
    frozen and holds no state, and the anti-bounce default means a standing population pokes
    once, at the crossing.
    """
    context = context or {}
    rows = _recorded(dispositions(drives_path=context.get("drives_path"),
                                  root=context.get("root")))
    return len(rows) > int(context.get("seen", 0))


def _carry(context=None) -> dict:
    context = context or {}
    from cairn.devices.aider_shim import driver  # noqa: PLC0415

    root = context.get("root") or driver.REPO
    rows = dispositions(drives_path=context.get("drives_path"), root=root)
    recorded = _recorded(rows)
    counts = {}
    for r in recorded:
        counts[r["disposition"]] = counts.get(r["disposition"], 0) + 1
    return {
        "ticket": TICKET,
        "drives": len(rows),
        "with_survival": len(recorded),
        "counts": counts,
        "rows": rows,
        "compared_against": {
            "root": str(root),
            "head": _head(root),
            "hole": "the comparison is the WORKING TREE, not a git read of the PROVED "
                    "commit — the same state at the crossing the trigger names, and not "
                    "the same state if this fires later. The head above is what it was "
                    "actually taken against.",
        },
        "reads": "`survived` means the apprentice earned it; `rewritten` and `discarded` "
                 "mean the hand did. `not-applied` is neither — the drive produced no "
                 "edit, which is a different finding and a different decision.",
    }


def _enough(context=None) -> bool:
    """Five driven pieces with survival recorded — the spec's words, unlowered."""
    context = context or {}
    rows = _recorded(dispositions(drives_path=context.get("drives_path"),
                                  root=context.get("root")))
    return len(rows) >= 5


#: Honest as a placeholder, dishonest as a measurement — the same tracked debt every sibling
#: probe carries: nothing pulses this shim yet, so loudness rides BaseShim.overdue() alone.
_HORIZON = 1000

PROBE = Probe(
    why="a ticket can pass its physics green while every line the apprentice wrote was "
        "thrown away and rewritten by CC — the offload buying nothing while reporting "
        "success. That is a hollow green (Law 8), and the offload probe cannot see it: it "
        "reads whether the build PASSED, never who earned the pass. This watch reads the "
        "edit the apprentice applied against the files as they stand, and tells Akien at "
        "triage whether the green came from the apprentice or from the hand cleaning up "
        "after it.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "edit-survival", "ticket": TICKET,
          "consumer": "Akien at triage — offload-more vs pull-back is his call"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

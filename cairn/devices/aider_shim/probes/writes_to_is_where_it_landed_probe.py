"""aider_shim_writes_to_is_where_it_landed — is the declared output address where the work
actually went, or is the field decorative?

THE TICKET'S WATCHME, COMPILED. The spec
(CairnCommons/tickets/a-piece-names-where-its-output-lands.json) names this exact path, and
the emission gate resolves ARMED from it, so this module is what stands between the WATCHME
crossing and a refusal. Its fields are that spec's, kept in the spec's own words where they
are the answer:

  object   — piece_output_address
  trigger  — "every drive_brief that runs against a piece carrying `writes_to` — the drive
             record already carries `aider_reported_edited` and the before/after images, so
             the comparison costs nothing at the moment the drive lands"
  enough   — "when 10 drives have been recorded and each one's reported edits fall inside
             the piece's declared `writes_to`, or at the FIRST drive whose edits all land
             outside it — that one is the finding and stops the watch immediately, because
             it means the declared address is not where the work actually goes and the
             field is decorative"
  carrier  — per drive: the piece's `writes_to`, aider's `aider_reported_edited`, and the
             disposition of each path
  nexus    — the aider_shim drive record (drives.jsonl), the same surface
             edit_survival_probe already reads
  consumer — whoever next charts a ticket for the apprentice to build; today CC, deciding
             at decompose time whether a piece's output address is knowable

THE ASYMMETRIC STOP IS THE WHOLE DESIGN, and it is not a convenience. Ten agreeing drives
buy one weak confirmation; ONE drive whose edits all land elsewhere is a strong
falsification, because it says the field the door now REQUIRES is not describing the world.
So `enough` is satisfied by either, and the fast arm is the one that matters — this watch
is built to die early on bad news rather than late on good.

WHY THIS IS NOT edit_survival_probe's QUESTION, and the two are deliberately over one
store. That probe asks WHO EARNED the green — did the apprentice's edit survive the hand.
This one asks WHETHER THE CHART KNEW WHERE THE EDIT WOULD GO. A drive can score `survived`
on every file and still be a total failure of this watch: the apprentice writes something
that lasts, at an address nobody declared, and the chart's claim to know its own output was
fiction. The measured n=1 that bore the ticket is exactly that shape — declared
`venv.py`, edited `driver.py`, and nothing in the system said a word.

WHAT IS COMPARED AGAINST WHAT, AND THE HOLE IN IT — NAMED, NOT PAPERED OVER (Law 7). The
declaration lives in the decompose berth, and the berth that STANDS is not necessarily the
berth the drive read: a re-chart between the two would compare an old drive against a new
declaration and report a disagreement that is really just time passing. So this does not
guess. It composes ``translate._files`` over the standing berth's `writes_to` — the same
function, so the two cannot resolve an address differently — and then checks that result
against the ``files`` the drive record ITSELF carries. Those agree only if the declaration
the drive was handed is the declaration standing now, and that agreement is a fact on disk
rather than a clock comparison (the berth stamps are local time and the drive stamps are
UTC; a timestamp comparison across the two would be wrong in a way nothing would notice).
Disagreement is `unknowable`, not a finding.

  AND `unknowable` IS WHAT MAKES THE PRE-FIELD DRIVES HONEST. Every drive recorded before
  2026-08-17 was handed an editable list sourced from `uses`, so its `files` cannot match a
  `writes_to` resolution and the row falls out on its own — with no date constant anywhere
  in this module, and no drive silently counted as evidence about a field that did not
  exist when it ran. Measured at arming (2026-08-17): 8 rows on the store, 6 drives after
  the duplicate collapse, 6 unknowable, 0 countable — so this watch starts at zero and has
  to earn every row it counts.

A PROBE CARRIES NO AUTHORITY (Law 6). This reads drives.jsonl and the standing berths, and
writes nothing anywhere. It deposits and pokes; re-opening a node whose intention did not
work is the owner's act.
"""

from __future__ import annotations

from pathlib import Path

from cairn.tools.base.probe import Probe

TICKET = "a-piece-names-where-its-output-lands"

#: The dispositions, and there is no sixth. `no-edit` is kept apart from `landed-outside`
#: for the same reason edit_survival_probe keeps `not-applied` apart from `discarded`: a
#: drive that produced nothing says the apprentice is not producing, and a drive that
#: produced something elsewhere says the CHART was wrong. Those call for opposite moves,
#: and collapsing them would make the second invisible inside the first.
UNKNOWABLE = "unknowable"
NO_EDIT = "no-edit"
INSIDE = "landed-inside"
OUTSIDE = "landed-outside"
MIXED = "mixed"


def _declared(ticket: str, piece_index: int, *, berths_root=None):
    """``(relative writes_to paths, berth path)`` for a ranked piece — or ``(None, why)``.

    Composed from the two functions that already own these answers: ``chain_for_ticket``
    resolves the standing berth, and ``translate._files`` resolves an output address the
    way the brief does. Re-spelling either here is how the watch and the thing it watches
    come to disagree about what a declaration means.
    """
    from cairn.devices.aider_shim import translate  # noqa: PLC0415
    from cairn.tools.chain.chain import chain_for_ticket  # noqa: PLC0415

    chain = chain_for_ticket(ticket, berths_root=berths_root)
    d, t = chain.get("decompose"), chain.get("triage")
    if not d or not t:
        return None, "no standing decompose+triage berth for this ticket"
    order = translate._lookup(t, "order") or []
    if not 0 <= piece_index < len(order):
        return None, "piece %d is outside the standing triage order" % piece_index
    what = order[piece_index].get("what")
    pieces = translate._lookup(d, "sub_problems") or []
    matches = [p for p in pieces if p.get("what") == what]
    if len(matches) != 1:
        return None, "the ranked piece matches %d entries in the standing split" % len(matches)
    writes_to = matches[0].get("writes_to") or []
    if not writes_to:
        return None, "the standing berth's piece carries no `writes_to` (it predates the field)"
    editable, _read_only, _skipped = translate._files([], writes_to, [])
    return editable, d


def _rel(paths, root: Path) -> set:
    out = set()
    for p in paths:
        q = Path(p)
        try:
            out.add(str(q.relative_to(root)) if q.is_absolute() else str(q))
        except ValueError:
            out.add(str(q))
    return out


def _inside(edited: str, declared: set) -> bool:
    """An edit is inside iff it IS a declared address.

    NOT a prefix test. A declared file's directory is not a licence to write its siblings,
    and the measured failure was a sibling in the same folder — `venv.py` declared,
    `driver.py` edited. A containment rule generous enough to call that inside would have
    reported the founding defect as a pass.
    """
    return edited in declared


def readings(*, drives_path=None, berths_root=None, root=None) -> list[dict]:
    """One row per recorded drive, oldest first. Reads; never writes."""
    from cairn.devices.aider_shim import driver  # noqa: PLC0415

    root = Path(root) if root is not None else driver.REPO
    rows, seen = [], set()
    for rec in driver.drives(drives_path if drives_path is not None else driver.DEFAULT_DRIVES):
        # One drive appended twice is still one drive — the same collapse, and the same
        # measured reason, as edit_survival_probe._identity carries.
        ident = (rec.get("ticket"), rec.get("piece_index"), rec.get("at"))
        if ident in seen:
            continue
        seen.add(ident)

        declared, where = _declared(rec.get("ticket") or "", rec.get("piece_index") or 0,
                                    berths_root=berths_root)
        row = {
            "ticket": rec.get("ticket"),
            "piece_index": rec.get("piece_index"),
            "at": rec.get("at"),
            "declared": sorted(_rel(declared or [], root)),
            "handed_to_the_drive": sorted(rec.get("files") or []),
            "edited": sorted(rec.get("aider_reported_edited") or []),
            "berth": where if declared is not None else None,
            "why_unknowable": "" if declared is not None else where,
            "per_path": {},
        }
        if declared is None:
            row["disposition"] = UNKNOWABLE
            rows.append(row)
            continue

        want = _rel(declared, root)
        if want != set(row["handed_to_the_drive"]):
            row["disposition"] = UNKNOWABLE
            row["why_unknowable"] = (
                "the standing berth's `writes_to` resolves to %s, and the drive was handed "
                "%s — the declaration standing now is not the one this drive read, so what "
                "it was told to write cannot be recovered" % (sorted(want),
                                                              row["handed_to_the_drive"]))
            rows.append(row)
            continue

        edited = _rel(row["edited"], root)
        row["per_path"] = {e: (INSIDE if _inside(e, want) else OUTSIDE) for e in sorted(edited)}
        if not edited:
            row["disposition"] = NO_EDIT
        elif all(v == INSIDE for v in row["per_path"].values()):
            row["disposition"] = INSIDE
        elif all(v == OUTSIDE for v in row["per_path"].values()):
            row["disposition"] = OUTSIDE
        else:
            row["disposition"] = MIXED
        rows.append(row)
    return rows


def _countable(rows: list[dict]) -> list[dict]:
    """The rows that actually say something about the declaration.

    `unknowable` says the comparison could not be made and `no-edit` says there was nothing
    to compare — neither is evidence about whether `writes_to` describes the world, and
    counting either toward ten would retire this watch having learned less than it asked
    for. Same refusal as the sibling probe's: a stop reached on hollow rows is a hollow
    green (Law 8).
    """
    return [r for r in rows if r["disposition"] in (INSIDE, OUTSIDE, MIXED)]


def _trigger(now=None, context=None) -> bool:
    """True when a drive carries a comparison it did not carry before.

    NOT A POLL. ``drive_brief``'s own record write is the event that already fires; this
    asks whether it left a new comparable row behind. The count rides `context` because a
    Probe is frozen and holds no state.
    """
    context = context or {}
    rows = _countable(readings(drives_path=context.get("drives_path"),
                               berths_root=context.get("berths_root"),
                               root=context.get("root")))
    return len(rows) > int(context.get("seen", 0))


def _carry(context=None) -> dict:
    context = context or {}
    rows = readings(drives_path=context.get("drives_path"),
                    berths_root=context.get("berths_root"),
                    root=context.get("root"))
    countable = _countable(rows)
    counts = {}
    for r in rows:
        counts[r["disposition"]] = counts.get(r["disposition"], 0) + 1
    return {
        "ticket": TICKET,
        "object": "piece_output_address",
        "drives": len(rows),
        "countable": len(countable),
        "counts": counts,
        "rows": rows,
        "reads": "`landed-inside` says the chart knew where the work would go. "
                 "`landed-outside` is THE FINDING — the declared address is not where the "
                 "work actually goes and the field is decorative. `mixed` is carried whole "
                 "rather than rounded, because a piece that half-obeys its declaration is "
                 "a different problem from one that ignores it. `unknowable` and `no-edit` "
                 "are not evidence either way and are counted separately for that reason.",
        "hole": "the declaration compared against is the STANDING berth's, confirmed to be "
                "the drive's own by matching the resolved `writes_to` against the `files` "
                "the record carries. A drive whose berth has since been re-charted reads "
                "`unknowable` rather than being compared against a declaration it never "
                "saw — the honest answer, and the reason this watch may need more real "
                "tickets than ten drives to reach ten countable rows.",
    }


def _enough(context=None) -> bool:
    """Ten agreeing drives, or the FIRST drive whose edits all land outside. The spec's
    words, unlowered — and the asymmetry is deliberate (see the module header)."""
    context = context or {}
    rows = _countable(readings(drives_path=context.get("drives_path"),
                               berths_root=context.get("berths_root"),
                               root=context.get("root")))
    if any(r["disposition"] == OUTSIDE for r in rows):
        return True
    return len(rows) >= 10 and all(r["disposition"] == INSIDE for r in rows)


#: Honest as a placeholder, dishonest as a measurement — the same tracked debt every sibling
#: probe carries: nothing pulses this shim yet, so loudness rides BaseShim.overdue() alone.
_HORIZON = 1000

PROBE = Probe(
    why="the decompose door now REQUIRES every piece to name where its output lands, and a "
        "required field that does not describe the world is worse than an absent one — it "
        "reads as knowledge. The measured n=1 that bore the ticket is the shape: a piece "
        "declared `venv.py`, the apprentice edited `driver.py`, and the only trace was "
        "aider's own edit list. This watch reads every drive's reported edits against the "
        "declaration it was handed, and tells the next mind charting a ticket whether a "
        "piece's output address is actually knowable at decompose time.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "decompose", "kind": "piece-output-address", "ticket": TICKET,
          "consumer": "whoever next charts a ticket for the apprentice to build — today "
                      "CC, deciding at decompose time whether a piece's output address is "
                      "knowable"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

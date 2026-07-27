"""base/needs.py — a STAGE declares what it needs, and LOOKING is what keeps the record honest.

Akien's shape, verbatim (2026-07-26, tickets/stage-needs.json):

    'the workflow is the stages, but dependencies can be outside influences. so we can't
    represent dependencies directly by just saying workflow. each workflow step should list
    it's dependenices. so BUILD might be gated on BUS DEVICE and EMBEDDINGS GENERATOR... and
    just be listed like: [ ] BUILD - Needs: - BUS DEVICE - EMBEDDINGS GENERATOR etc. then
    whenever we look at the state of the things, if there's an update we mark it: [ ] BUILD -
    Needs: [DONE] BUS DEVICE - EMBEDDINGS GENERATOR — even if we don't pick up the ticket!
    the fact that we went and looked gets compiled into the ticket.'

Two failures, one fix. `waits_on` was hand-authored prose in no schema, read by nothing, and
DROPPED at berthing — so finishing the work destroyed the dependency record. And the record kept
disagreeing with the world ('awaiting Akien's signature' when there was nowhere to sign; 'no
inference host' with ollama serving on :11434 for four days). Needs are declared PER STAGE
(intrinsic to the stage, true regardless of which goal we aim at — the goal-relative ORDER stays
derived at ask time, which is why this is storable at all), and the OBSERVATION compiles in even
when nobody picks the ticket up.

THE MARK IS AN OBSERVATION, NOT A CHECKBOX — {status, when, how_measured}, the same three fields a
VALIDATION carries and the same reason a host-seam carries a re-runnable verify whose seal expires.
A bare [DONE] is an unmeasured claim wearing a checkmark (Law 3), and it goes stale INVISIBLY, which
is the exact defect this node exists to close. So the door REFUSES a mark missing when or
how_measured (Law 4 — physics, not a reminder to be diligent).

Marks are APPEND-ONLY (Law 7): ``append_mark`` returns a new list and never touches a prior mark.
The current mark is a COMPILED VIEW (``project_needs``) — latest observation per need, plus its AGE,
so 'this DONE is 21 days old' is a fact on the surface rather than an invisible assumption.

WHERE MARKS LIVE — and a DIVERGENCE from this node's own recorded distinction, argued rather than
assumed. The ticket filed 'it rides the projector's append door'. It does not, and cannot yet: that
door writes a COMPONENT's history.json/state.json pair, and a staged ticket has neither — a ticket's
voyage freezes into history when it PROVES OUT (CLAUDE.md), so routing marks there would mint a
history file per staged ticket before the ticket has one, inverting that design. Instead the mark
lands in the ticket record itself, through this one function, reusing the projector's pure core
discipline (append-only, atomic write). One door, one owner (Law 6: the tickets store owns the
ticket). And because the mark rides INSIDE the ticket, it MIGRATES when the ticket berths beside its
code — which is precisely the destroyed-at-berthing failure, fixed.

    python3 cairn/base/proofs/test_needs.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime

from cairn.base import transitions

# The two writable statuses. A need with NO marks is the third condition — never looked at — and it
# is represented by the ABSENCE of a mark, not by a status, because 'nobody has measured this' is
# not an observation and must not be writable as one.
#
# DONE is Akien's word, kept from his sketch. MISSING IS CC'S COINAGE AND IS FLAGGED FOR RATIFY
# (memory terms-drift-flag-coinages): it names the case his sketch does not — we went and looked and
# the thing is NOT there. That case is the whole point of 'even if we don't pick up the ticket', so
# it needs a status; the word is derivable in the native domain (a dependency that is not there is
# missing) but it is mine, not his, until he rules.
STATUSES = ("DONE", "MISSING")

# What an observation must carry to be admitted. `need` addresses it; the other three ARE the
# observation. `at` is stamped by the door, so it is not asked of the caller (the same split the
# append door makes: the door writes what the door knows).
REQUIRED_MARK_FIELDS = ("need", "status", "when", "how_measured")

# A how_measured that says nothing is a bare [DONE] with extra words. The floor is deliberately
# LOW (a length, not a grammar) because the falsifier is 'a reader can re-run this', which no
# regex can decide — but 'ok' and '' can be refused outright, and are.
_MIN_HOW_MEASURED = 12


class NeedRefused(ValueError):
    """The needs door turning away a malformed declaration or an unmeasured mark. Loud, and BEFORE
    the write — a record of truth is permanent, so the only place to stop a bad one is on the way in
    (Law 7). The report is complete on this one pass (I-complete-diagnostic-on-first-pass): what was
    refused, what was required, what was carried, and why the field is load-bearing."""


# ── the pure core: declaration, observation, projection ──────────────────────


def declared_path(node: dict) -> tuple[str, ...]:
    """The stage vocabulary this node's own workflow string claims, via the emit-chokepoint's
    parser. Needs are validated against THIS, not against a list kept here — so the stages a node
    can declare needs for are exactly the stages it actually has (Law 1: the class definition
    already answered 'what stages exist'; a second copy here would be the re-derivation)."""
    wf = transitions.parse_workflow(node["state"])
    return wf.path


def validate_needs(node: dict, *, node_class_root=transitions._NODE_CLASSES) -> None:
    """Refuse a malformed ``stage_needs`` block. Absent is fine — a node with no declared needs is
    not a defect (most nodes need nothing external); a MISSHAPEN one is."""
    block = node.get("stage_needs")
    if block is None:
        return
    if not isinstance(block, dict):
        raise NeedRefused(
            f"stage_needs must map STAGE -> [need, ...]; carried {type(block).__name__}. "
            "The whole point of the shape is that a need attaches to the stage that needs it "
            "(Akien, 2026-07-26: 'each workflow step should list it's dependenices')."
        )
    path = declared_path(node)
    # The class definition is loaded so an unknown class is refused here too, rather than letting a
    # need attach to a stage of a class that has no physics (Law 8).
    transitions.load_class_def(
        transitions.parse_workflow(node["state"]).node_class, root=node_class_root
    )
    for stage, needs in block.items():
        if stage not in path:
            raise NeedRefused(
                f"stage {stage!r} is not in this node's workflow vocabulary {list(path)} — "
                f"a need cannot attach to a stage the node does not have. "
                f"(node {node.get('id')!r}, state {node['state'].split('(')[0].strip()!r})"
            )
        if not isinstance(needs, list) or not needs:
            raise NeedRefused(
                f"stage {stage!r} declares {needs!r} — expected a NON-EMPTY list of needs. "
                "An empty list asserts 'this stage needs nothing', which is what OMITTING the "
                "stage already says; two ways to say one thing is how they drift apart."
            )
        for entry in needs:
            _validate_need_entry(stage, entry, node)


def _validate_need_entry(stage: str, entry, node: dict) -> None:
    if not isinstance(entry, dict):
        raise NeedRefused(
            f"stage {stage!r} carries need {entry!r} ({type(entry).__name__}) — expected "
            "{'need': <what>, 'marks': [...]}. A bare string cannot hold an observation, and a "
            "need that cannot hold an observation is the checkbox this shape replaces."
        )
    what = entry.get("need")
    if not isinstance(what, str) or not what.strip():
        raise NeedRefused(
            f"stage {stage!r} carries a need with no 'need' text (carried {sorted(entry)}) — "
            "a need nobody can identify cannot be looked for, so it can never be marked."
        )
    marks = entry.get("marks", [])
    if not isinstance(marks, list):
        raise NeedRefused(
            f"need {what!r} in stage {stage!r} has marks={marks!r} — expected a list. "
            "Marks are APPEND-ONLY history (Law 7); a non-list has nowhere to append."
        )
    for mark_record in marks:
        validate_mark(mark_record, context=f"need {what!r} in stage {stage!r}")


def validate_mark(mark_record, *, context: str = "mark") -> None:
    """Refuse an observation that no reader could trust. THE FALSIFIER OF THIS WHOLE NODE: a mark
    lacking WHEN or HOW MEASURED must be refused — a bare [DONE] cannot be written."""
    if not isinstance(mark_record, dict):
        raise NeedRefused(f"{context}: mark {mark_record!r} is not a record")
    missing = [k for k in REQUIRED_MARK_FIELDS if not str(mark_record.get(k) or "").strip()]
    if missing:
        raise NeedRefused(
            f"{context}: mark refused, missing {missing} — required {list(REQUIRED_MARK_FIELDS)}, "
            f"carried {sorted(mark_record)}. 'when' and 'how_measured' are what make this an "
            "OBSERVATION rather than an assertion: without them the mark cannot be aged and cannot "
            "be re-run, so it is read as current forever and goes stale invisibly. That is the "
            "defect this shape exists to close (Law 3), and it is permanent once written (Law 7)."
        )
    status = mark_record["status"]
    if status not in STATUSES:
        raise NeedRefused(
            f"{context}: status {status!r} is not one of {list(STATUSES)}. A need with NO marks is "
            "how 'never looked at' is said — it is the absence of an observation, never a status."
        )
    when = str(mark_record["when"]).strip()
    try:
        _parse_when(when)
    except ValueError:
        raise NeedRefused(
            f"{context}: when={when!r} is not an ISO date (YYYY-MM-DD, or a full timestamp). "
            "It must be machine-comparable because the AGE of the mark is the point — a date only "
            "a human can read cannot be turned red by a staleness query."
        ) from None
    how = str(mark_record["how_measured"]).strip()
    if len(how) < _MIN_HOW_MEASURED:
        raise NeedRefused(
            f"{context}: how_measured={how!r} is {len(how)} chars, floor is {_MIN_HOW_MEASURED}. "
            "The test is whether the next reader can RE-RUN it ('curl :11434/api/tags — three "
            "models present' passes; 'checked' does not). A token value here is a bare [DONE] "
            "wearing a field name."
        )


def _parse_when(when: str) -> date:
    """ISO date or full timestamp -> date. Strict on purpose: the age is the product."""
    return datetime.fromisoformat(when).date() if len(when) > 10 else date.fromisoformat(when)


def append_mark(marks: list[dict], mark_record: dict, *, at: str | None = None) -> list[dict]:
    """Return marks with the observation appended — the ONLY mutation marks admit (Law 7).

    Pure: a new list, prior marks untouched. Validates BEFORE appending, so a refused mark leaves
    the record exactly as it was.
    """
    validate_mark(mark_record)
    stamped = {
        **mark_record,
        "at": at or datetime.now().isoformat(timespec="seconds"),
        "seq": (marks[-1]["seq"] + 1) if marks else 0,
    }
    return [*marks, stamped]


def project_needs(node: dict, *, today: date) -> dict:
    """Compile the CURRENT view: per stage, per need, the latest observation and its AGE IN DAYS.

    ``today`` is injected, never read from the clock here — a projection that reaches for the clock
    cannot be proved without the proof going stale (memory proof-over-live-data-assert-invariants:
    a proof that pins a legitimately-moving value turns a normal day into a spurious red).

    Deterministic: same node + same day in, same view out. So this view can never drift from the
    marks it is derived from — it is not a second copy anyone maintains (Law 1).
    """
    validate_needs(node)
    out: dict[str, list[dict]] = {}
    for stage, needs in (node.get("stage_needs") or {}).items():
        rows = []
        for entry in needs:
            marks = entry.get("marks") or []
            latest = marks[-1] if marks else None
            rows.append(
                {
                    "need": entry["need"],
                    "status": latest["status"] if latest else None,   # None = never looked at
                    "when": latest["when"] if latest else None,
                    "how_measured": latest["how_measured"] if latest else None,
                    "age_days": (today - _parse_when(latest["when"])).days if latest else None,
                    "observations": len(marks),
                }
            )
        out[stage] = rows
    return out


def unmeasured(node: dict, *, today: date) -> list[dict]:
    """The needs NOBODY HAS LOOKED AT — the category every one of 2026-07-26's stumbles lived in.

    Not 'blocked on work' and not 'ready': blocked on a MEASUREMENT NOBODY HAS TAKEN. It was
    invisible before this shape existed, which is why it gets its own function rather than being
    left for a reader to filter out.
    """
    return [
        {"stage": stage, **row}
        for stage, rows in project_needs(node, today=today).items()
        for row in rows
        if row["status"] is None
    ]


def render_needs(node: dict, *, today: date) -> str:
    """Akien's sketch, rendered — his shape IS the specification of the surface, so it is built
    here rather than described. The age is shown because a mark with no age is the invisible-stale
    failure; 'never looked' is shown as an empty box because that is the honest third condition."""
    view = project_needs(node, today=today)
    path = declared_path(node)
    lines = []
    for stage in path:                       # workflow order, not dict order
        if stage not in view:
            continue
        lines.append(f"[ ] {stage} — Needs:")
        for row in view[stage]:
            if row["status"] is None:
                lines.append(f"      [ ]        {row['need']}   — never looked")
                continue
            lines.append(
                f"      [{row['status']}]{' ' * max(1, 8 - len(row['status']))}{row['need']}   "
                f"— {row['when']} ({row['age_days']}d ago): {row['how_measured']}"
            )
    return "\n".join(lines)


# ── the today-shape: the one door that writes a mark into a ticket record ────


def _atomic_write(path: str, data) -> None:
    """Temp file + rename, so a reader never sees a half-written record (the projector's rule)."""
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def mark(
    node_path: str,
    stage: str,
    need: str,
    *,
    status: str,
    when: str,
    how_measured: str,
    at: str | None = None,
) -> dict:
    """THE DOOR: record that we went and looked. Refuses before it writes.

    'even if we don't pick up the ticket! the fact that we went and looked gets compiled into the
    ticket.' — so this is callable on a node nobody is working, which is the point: looking is
    cheap, and the finding must survive the looking.

    Refuses: an unknown stage, an unknown need (matched on its text — a mark for a need that was
    never declared would be an observation of nothing), and any mark missing when/how_measured.
    """
    with open(node_path, encoding="utf-8") as f:
        node = json.load(f)
    validate_needs(node)
    block = node.get("stage_needs") or {}
    if stage not in block:
        raise NeedRefused(
            f"{node_path}: stage {stage!r} declares no needs (declared: {sorted(block)}) — "
            "declare the need before marking it, so the ticket says WHAT it is waiting on even "
            "before anyone has looked."
        )
    for entry in block[stage]:
        if entry["need"] == need:
            entry["marks"] = append_mark(entry.get("marks") or [], {
                "need": need, "status": status, "when": when, "how_measured": how_measured,
            }, at=at)
            break
    else:
        raise NeedRefused(
            f"{node_path}: stage {stage!r} has no need {need!r} "
            f"(declared: {[e['need'] for e in block[stage]]}) — a mark must land ON a declared "
            "need; an observation with nothing to attach to would be lost."
        )
    node["stage_needs"] = block
    _atomic_write(node_path, node)
    return node

"""verdict_contract — the chart chain's verdict contract: what a verdict owes, and the ledger
of verdicts owed to the tree.

MOVED DOWN A RUNG 2026-10-02 (ticket d8e8a2dc1176, RULE 1) from
cairn/devices/codemother/machines/verdict/verdict.py, unchanged but for its address. The
coverage reader (``unanswered``, the falsifier reader under it) is what the PROVED exit gate
composes, and the ledger is chart's ("Law 6: chart owns the ledger"); codemother's verdict
machine held both, so the build inspector and the PROVED crossing reached into a device to read
them. They are the chain's contract, so they live beside the chain reader in this tool, and the
verdict machine binds the very same objects from here (write_verdict and its instrument runner
stay in codemother).

TREE-FREE AND FILE-ONLY, as before: a netns-sealed crossing enqueues identically to a live one.
"""
from __future__ import annotations

import json
import os
import re
import time

from cairn.tools.chain.grammar import CAIRN_ROOT, INSTANCE_DIR, ticket_path
from cairn.tools.chain.chain import BERTHS_ROOT, latest_claiming_artifact  # noqa: F401  (BERTHS_ROOT: a fixture seam)

# THE SECOND PROVENANCE FORM (ticket watchme-emits-a-probe piece (d), 2026-07-30).
# A verdict's obligations came from exactly one place until now: a berthed chart
# validate packet. But a WATCHME probe fires long after the voyage that built the
# node has closed and its chart chain has gone cold — the question it answers is
# "did the intention WORK?", and the artifact that states that in falsifiable form
# is the ticket's own ``falsifier``, not an acceptance packet. So ``validate_ref``
# admits ``falsifier@<ticket-id>`` and the criteria are derived from the ticket.
#
# ONE CONTRACT, NOT TWO (the ticket's own falsifier clause (6): "a verdict written
# by a probe cannot pass validate_verdict, or needs a second schema to do so — one
# contract or the design failed"). Everything above this line is untouched: the
# shape gate does not know this form exists, the ticket claim is required exactly
# as before, and coverage is still "every obligation answered and passing". Only
# WHERE the obligations are read from forks — which is why the fork lives in
# ``_read_chain`` and nowhere else.
FALSIFIER_REF = "falsifier@"

# A falsifier states its RED conditions as numbered clauses: "RED on any of: (1) …
# (2) …". Consecutive numbering from 1 is REQUIRED, not assumed — a falsifier this
# reader cannot segment refuses rather than silently mis-segmenting, because a
# mis-segmented obligation is an obligation quietly dropped (Law 8).
_CLAUSE_RE = re.compile(r"\((\d+)\)\s*")


class VerdictRefused(RuntimeError):
    """The loud refusal — an artifact this door cannot honestly berth."""


def falsifier_criteria(ticket_id: str, root: str = CAIRN_ROOT) -> tuple[list, str | None]:
    """Derive a criteria list from a filed ticket's ``falsifier``, one criterion per
    numbered RED clause. Returns (criteria, error).

    PUBLIC ON PURPOSE — the same reason ``verdict_error`` is: the door that READS
    the obligations and the probe that WRITES the answers must derive the claims
    by one implementation, or the claim strings drift apart and every falsifier
    verdict is refused as unanswered while looking word-for-word correct. The
    writer calls this to learn what it owes; the door calls it to check.

    A criterion's ``instrument`` is deliberately NOT synthesised here. The falsifier
    states the observation that would kill the claim; naming the measure that was
    actually run is the writer's act, and the shape gate already refuses a verdict
    that omits it. Inventing one would be this module putting words in the
    voyage's mouth."""
    path = ticket_path(ticket_id, root)
    if path is None:
        return [], ("validate_ref %s%s names no ticket on file in "
                    "CairnCommons/tickets/ — an obligation read from nowhere is "
                    "fabricated attribution" % (FALSIFIER_REF, ticket_id))
    try:
        with open(path, encoding="utf-8") as fh:
            ticket = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        return [], ("ticket %r cannot be read (%s: %s) — an unreadable obligation "
                    "refuses, it does not vanish" % (ticket_id, type(e).__name__, e))
    raw = ticket.get("falsifier")
    text = raw.get("proves_red", "") if isinstance(raw, dict) else raw
    if not isinstance(text, str) or not text.strip():
        return [], ("ticket %r carries no falsifier — there is nothing for a "
                    "falsifier-sourced verdict to answer, and an empty obligation "
                    "would pass everything" % (ticket_id,))
    marks = list(_CLAUSE_RE.finditer(text))
    if not marks:
        return [], ("ticket %r's falsifier states no numbered clauses — this form "
                    "answers clause by clause, and one undivided paragraph cannot "
                    "be answered clause by clause" % (ticket_id,))
    if [int(m.group(1)) for m in marks] != list(range(1, len(marks) + 1)):
        return [], ("ticket %r's falsifier numbers its clauses %s, not 1..%d — a "
                    "falsifier this reader cannot segment refuses rather than "
                    "silently mis-segmenting"
                    % (ticket_id, [m.group(1) for m in marks], len(marks)))
    criteria = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        clause = text[m.end():end].strip()
        if not clause:
            return [], ("ticket %r's falsifier clause (%d) is empty — a RED "
                        "condition that says nothing cannot be answered"
                        % (ticket_id, i + 1))
        criteria.append({"claim": clause,
                         "source": "%s%s clause (%d)" % (FALSIFIER_REF, ticket_id, i + 1)})
    return criteria, None


def _read_falsifier_chain(artifact, root: str) -> tuple[list, list, str | None]:
    """The second reader. Criteria come from the ticket's falsifier; there are NO
    hypotheses, because this provenance has no hypothesize berth to disposition
    against — the chart chain it would have come from is cold, which is the whole
    reason this form exists.

    THE VACUOUS HALF IS NAMED, NOT HIDDEN. An empty hypotheses list makes the
    dispositions obligation trivially satisfied, and a gate that inspects nothing
    passes everything (Law 8). What keeps this honest is the other half: the
    criteria obligation refuses outright unless the ticket yields at least one
    numbered clause, and EVERY clause must be answered and passing. The falsifier
    is the whole RED set; answering half of it is answering none of it, because
    the unanswered half is exactly where the failure hides.

    A verdict may not read one ticket's falsifier while claiming another's voyage —
    that is laundered provenance, and it refuses here rather than at no point."""
    ticket_id = artifact["validate_ref"][len(FALSIFIER_REF):].strip()
    claim = artifact.get("ticket")
    if ticket_id != claim:
        return [], [], ("validate_ref %r reads the falsifier of %r while the verdict "
                        "claims ticket %r — a verdict answers its own ticket's "
                        "falsifier or it is answering somebody else's question"
                        % (artifact["validate_ref"], ticket_id, claim))
    criteria, err = falsifier_criteria(ticket_id, root)
    if err:
        return [], [], err
    return criteria, [], None


def _read_chain(artifact, root: str = CAIRN_ROOT) -> tuple[list, list, str | None]:
    """Read what must be answered: the claiming validate berth's criteria and its
    hypothesize berth's hypotheses. Returns (criteria, hypotheses, error) — a
    chain that cannot be read is an error, never an empty obligation (a gate that
    silently inspects nothing passes everything, Law 8).

    THE FORK, and the only one in this module: a ``validate_ref`` of the form
    ``falsifier@<ticket-id>`` reads the ticket instead of a berth (see above)."""
    ref = artifact.get("validate_ref")
    if isinstance(ref, str) and ref.startswith(FALSIFIER_REF):
        return _read_falsifier_chain(artifact, root)
    try:
        with open(os.path.expanduser(artifact["validate_ref"]), encoding="utf-8") as fh:
            vpacket = json.load(fh)
        criteria = vpacket["criteria"]
        with open(os.path.expanduser(vpacket["hypothesize_ref"]), encoding="utf-8") as fh:
            hpacket = json.load(fh)
        hypotheses = hpacket["hypotheses"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
        return [], [], ("the claiming chain cannot be read from validate_ref %r "
                        "(%s: %s) — an unreadable obligation refuses, it does not "
                        "vanish" % (artifact.get("validate_ref"), type(e).__name__, e))
    return criteria, hypotheses, None


def unanswered(artifact, root: str = CAIRN_ROOT) -> list[str]:
    """Coverage: every criterion answered (and PASSING — an answered-and-failed
    criterion is a kick-back, not a crossing), every hypothesis dispositioned.
    Returns one line per unanswered item, complete on the first pass.

    ``root`` reaches only the falsifier form (a berth ref is an absolute path and
    needs no root), and it is the LAST positional this door will ever grow — the
    inspector composes this function by identity, so its arity is a shared surface."""
    criteria, hypotheses, err = _read_chain(artifact, root)
    if err:
        return [err]
    items = []
    answered = {v["claim"]: v for v in artifact.get("verdicts", ())
                if isinstance(v, dict) and isinstance(v.get("claim"), str)}
    for c in criteria:
        verdict = answered.get(c.get("claim"))
        if verdict is None:
            items.append("criterion unanswered: %r — its instrument (%s) was never "
                         "run against the build" % (c.get("claim"), c.get("instrument")))
        elif verdict.get("outcome") != "pass":
            items.append("criterion answered and FAILED: %r — evidence: %s. PROVED "
                         "asserts done; a failed criterion is a kick-back, not a "
                         "crossing" % (c.get("claim"), verdict.get("evidence")))
    disposed = {(d.get("piece"), d.get("expect")) for d in artifact.get("dispositions", ())
                if isinstance(d, dict)}
    for h in hypotheses:
        if (h.get("piece"), h.get("expect")) not in disposed:
            items.append("hypothesis undispositioned: piece %r expected %r — "
                         "confirmed or killed, but answered; silence is neither"
                         % (h.get("piece"), h.get("expect")))
    return items


# ── THE PENDING LEDGER (ticket the-deposit-rides-the-read, 2026-07-29) ───────
# An append-only JSONL in chart's instance-space, FOUR RECORD KINDS and no fifth
# motion: ``enqueued`` (a crossing named a verdict berth that owes the tree a
# deposit), ``deposited`` (the door landed it, with the node it became), since
# 2026-10-10 (ticket 2b34b52f80f3) ``failed`` (one deposit attempt was refused,
# with the stderr line it was reported with and its result code), and since the
# same day (ticket a76447d28af9) ``superseded`` (an owed berth was replaced by a
# later verdict berth already owed for the same ticket — see mark_superseded).
# PENDING IS DERIVED BY READ — enqueued minus answered (deposited or superseded) —
# never by editing or removing a line: a record of truth is never changed in place
# (Law 7), so a failed deposit leaves its enqueued line standing and loud instead of
# vanishing. A ``failed`` record answers nothing: pending() keys on ``deposited``
# and ``superseded`` alone, so a failed berth stays owed however many times it fails.
#
# Law 6: chart owns the ledger. Every writer (the chokepoint's enqueue, the
# drain's deposited-mark and failed-mark, the supersede) appends through THIS module; nothing
# else touches the file. Tree-free by construction, like everything else here — the crossing
# side of the deposit may never reach the db or the embed host, which is the
# whole reason the deposit is split in two.

LEDGER_PATH = os.path.join(os.path.dirname(INSTANCE_DIR), "verdict-deposits.jsonl")


def _stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _append(record: dict, ledger_path: str) -> dict:
    """The ONE write: open in append mode, one JSON object per line. Nothing on
    disk is read, rewritten, or truncated by a write — the file only grows."""
    parent = os.path.dirname(ledger_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def read_ledger(*, ledger_path: str | None = None) -> list[dict]:
    """Every record on the ledger, in append order. A missing ledger is an honest
    empty list (nothing has ever been enqueued). A line that cannot be parsed is
    NEVER dropped silently — it rides back as ``{"kind": "unreadable", ...}`` so a
    reader can name it, and the line itself stays exactly where it is."""
    path = os.path.expanduser(ledger_path if ledger_path is not None else LEDGER_PATH)
    if not os.path.isfile(path):
        return []
    records = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                records.append({"kind": "unreadable", "line": n, "raw": line.rstrip("\n"),
                                "why": "%s: %s" % (type(e).__name__, e)})
                continue
            records.append(record if isinstance(record, dict)
                           else {"kind": "unreadable", "line": n, "raw": line.rstrip("\n"),
                                 "why": "a ledger line must be a JSON object"})
    return records


def pending(*, ledger_path: str | None = None) -> list[dict]:
    """The enqueued records no ``deposited`` or ``superseded`` record answers, in
    enqueue order, one per berth — DERIVED BY READ, which is why nothing ever has to
    be edited."""
    records = read_ledger(ledger_path=ledger_path)
    landed = {r.get("berth") for r in records
              if r.get("kind") in ("deposited", "superseded")}
    out, seen = [], set()
    for r in records:
        berth = r.get("berth")
        if r.get("kind") != "enqueued" or not isinstance(berth, str):
            continue
        if berth in landed or berth in seen:
            continue
        seen.add(berth)
        out.append(r)
    return out


def enqueue_verdict(ticket: str, *, berths_root=None,
                    ledger_path: str | None = None) -> str | None:
    """Append ONE ``enqueued`` record naming the verdict artifact that answers
    ``ticket``. Returns the berth enqueued, or ``None`` when nothing claims the
    ticket — and that ``None`` is the load-bearing case: the exit gate is CLEAN
    both when a chart was answered and when no chart claims the ticket at all, so
    an enqueue keyed on the clean note would file a pending deposit for an
    artifact that does not exist. The key is the ARTIFACT.

    File-only by construction: a netns-sealed crossing enqueues identically to a
    live one, which is the constraint that split this deposit in two."""
    found = latest_claiming_artifact(ticket, berths_root=berths_root)
    if found is None:
        return None
    berth = found[0]
    _append({"kind": "enqueued", "berth": berth, "ticket": ticket, "at": _stamp()},
            os.path.expanduser(ledger_path if ledger_path is not None else LEDGER_PATH))
    return berth


def mark_deposited(berth: str, node_ids, *,
                   ledger_path: str | None = None) -> dict:
    """Append the SECOND record kind after the tree door landed the verdict. The
    enqueued line is never touched — 'drained' is a record appended by the
    depositor, so the ledger reads as the whole story of every deposit (whole
    since ticket 2b34b52f80f3, when a refused attempt became a ``failed`` record
    instead of a stderr print — see mark_failed).

    MANY NODES PER BERTH since 2026-07-29 (ticket a-node-holds-one-claim): a verdict
    now lands as its PARTS, so the record names every node the berth became. This
    record is what makes pending() stop returning the berth, so it may only be
    written when EVERY part landed — a single-id shape left a partial landing with
    nowhere honest to sit: mark it and the ledger lies about a verdict that is only
    half in the tree, or never mark it and the berth re-deposits forever.

    An empty landing is refused rather than recorded: 'deposited nothing' would
    close a berth that never reached the tree, which is the silent lapse the ledger
    exists to end. A lone string is accepted and wrapped — the old call shape stays
    honest rather than becoming a list of characters.

    Records written before this change carry ``node_id`` (singular) and are read
    correctly forever: pending() has only ever keyed on ``kind`` and ``berth``, and
    an append-only file is never rewritten to make an old line look new (Law 7)."""
    ids = [node_ids] if isinstance(node_ids, str) else list(node_ids)
    if not ids or not all(isinstance(n, str) and n.strip() for n in ids):
        raise VerdictRefused(
            "mark_deposited: berth %r landed no node ids (%r) — a 'deposited' record "
            "is what closes a berth, so recording an empty landing would close a "
            "verdict that never reached the tree" % (berth, node_ids))
    return _append({"kind": "deposited", "berth": berth, "node_ids": ids,
                    "at": _stamp()},
                   os.path.expanduser(ledger_path if ledger_path is not None
                                      else LEDGER_PATH))


def mark_failed(berth: str, *, stderr: str, result_code: str, ticket: str | None = None,
                ledger_path: str | None = None) -> dict:
    """Append the THIRD record kind: one deposit attempt on ``berth`` was refused
    (ticket 2b34b52f80f3). Akien, 2026-10-10: "we need to make the queue record
    stderr. and the result code for heavens sake." Until this record existed a
    refused drain left nothing on the ledger but the enqueued line it could not
    close, and the only trace of each refusal was a print on stderr.

    ``stderr`` is the line the failure was reported with, verbatim; ``result_code``
    is the failure's class name (e.g. 'VerdictRefused') — a string, not a process
    exit integer, because the drain runs inside a bus verb where no process exits.
    Both must be non-empty strings, else ValueError and NOTHING is appended: an
    empty failure record is the silent lapse again, wearing a record's shape.

    ``ticket`` defaults to the ticket on the berth's enqueued record, when the
    ledger holds one. One record per attempt, never de-duplicated — growth is
    measured after it runs. pending() ignores this kind, so the berth stays owed."""
    for name, value in (("stderr", stderr), ("result_code", result_code)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                "mark_failed: berth %r carries %s=%r — a 'failed' record exists to say "
                "what went wrong, and an empty one is the silent lapse again"
                % (berth, name, value))
    path = os.path.expanduser(ledger_path if ledger_path is not None else LEDGER_PATH)
    if ticket is None:
        for r in read_ledger(ledger_path=path):
            if r.get("kind") == "enqueued" and r.get("berth") == berth:
                ticket = r.get("ticket")
    return _append({"kind": "failed", "berth": berth, "ticket": ticket, "at": _stamp(),
                    "stderr": stderr, "result_code": result_code}, path)


def mark_superseded(berth: str, *, by: str, why: str,
                    ledger_path: str | None = None) -> dict:
    """Append the FOURTH record kind: the owed ``berth`` is replaced by the later
    verdict berth ``by`` (ticket a76447d28af9). Akien, 2026-10-10: "go ahead and cast
    the b577 repair ticket". A berth written before a rule it now fails (measured:
    verdict-20260815T141125-dd35ea1c8f7b, refused on every drain since f8f8ff9d made
    discriminating_observation required) can never be deposited as it stands; a new
    verdict alone leaves it owed forever, because pending() is keyed by berth.

    A new kind, never a reuse of ``deposited``: marking the old berth deposited would
    claim nodes it never became (mark_deposited's own docstring names that lie).

    ``by`` must already be owed for the SAME ticket, so a supersede never retires an
    obligation without another one standing in its place. Every refusal is a
    ValueError raised before anything is appended: an empty ``why``; ``berth`` with no
    enqueued record; ``berth`` already answered by a deposited or superseded record;
    ``by == berth``; ``by`` with no enqueued record; ``by`` enqueued for another
    ticket. ``failed`` records on ``berth`` do not stand in the way — they answer
    nothing."""
    if not isinstance(why, str) or not why.strip():
        raise ValueError("mark_superseded: berth %r carries why=%r — a supersede says "
                         "why the old verdict is replaced" % (berth, why))
    path = os.path.expanduser(ledger_path if ledger_path is not None else LEDGER_PATH)
    records = read_ledger(ledger_path=path)
    enqueued = {}
    for r in records:
        if r.get("kind") == "enqueued" and isinstance(r.get("berth"), str):
            enqueued.setdefault(r["berth"], r.get("ticket"))
    if berth not in enqueued:
        raise ValueError("mark_superseded: berth %r was never enqueued — there is no "
                         "owed deposit to supersede" % (berth,))
    answered = [r.get("kind") for r in records
                if r.get("berth") == berth and r.get("kind") in ("deposited", "superseded")]
    if answered:
        raise ValueError("mark_superseded: berth %r is already answered (%s) — it is "
                         "not owed" % (berth, answered[0]))
    if by == berth:
        raise ValueError("mark_superseded: berth %r cannot supersede itself" % (berth,))
    if by not in enqueued:
        raise ValueError("mark_superseded: by=%r is not enqueued — the replacement must "
                         "already be owed, or the obligation is retired with nothing in "
                         "its place" % (by,))
    if enqueued[by] != enqueued[berth]:
        raise ValueError("mark_superseded: by=%r is owed for ticket %r, berth %r for "
                         "ticket %r — a supersede stays within one ticket"
                         % (by, enqueued[by], berth, enqueued[berth]))
    return _append({"kind": "superseded", "berth": berth, "by": by,
                    "ticket": enqueued[berth], "why": why, "at": _stamp()}, path)

"""verdict — the answer a voyage owes its chart (ticket proved-answers-the-chart).

The chart chain ends at validate: what DONE means, measured. This module is the
other side of that promise — the v0 VERDICT ARTIFACT a voyage writes after
running those criteria, and the ONE validator both consumers compose:

  - the EXIT GATE (build_inspector.proved_answers_the_chart, called from the emit
    chokepoint's PROVED entry) shape-checks the artifact before a claimed ticket
    may close;
  - the DEPOSIT FACE (skills.chart.live's verdict- branch) re-validates the same
    artifact before its dispositions become the hypothesize tree's memory of
    what killed which.

One implementation, two mouths — a door and a gate that disagreed on a single
artifact would be the two-mouths defect measured on the first crossing.

TREE-FREE BY CONSTRUCTION: like cairn.devices.codemother.machines.orient.orient (the wire's standing
condition, pinned transitively by the inspector-nexus proof), this module
imports no tree machinery — the fire path from the chokepoint through the
inspector into here can never reach the trees or the db. A verdict is always
hardware. The deposit face therefore lives on the tree side (live.py), not here.

The artifact (verdict-<stamp>-<digest>.json, berthed beside the stage packets):

  ticket        — the cast ticket this verdict answers (REQUIRED here, unlike
                  the stages where a claim is optional: an unattributed verdict
                  answers nobody)
  validate_ref  — WHERE THE OBLIGATIONS COME FROM, in one of two forms: the
                  claiming validate berth whose criteria were run, or
                  ``falsifier@<ticket-id>`` — the ticket's own falsifier, clause
                  by clause, for a verdict written long after the chart chain
                  went cold (a WATCHME probe's answer to "did the intention
                  WORK?"). ONE contract either way; see FALSIFIER_REF below
  nexus         — OPTIONAL: which tree this verdict teaches, default
                  ``hypothesize``. Unconstrained to any roster on purpose — a
                  consumer outside this toolchain has no reason to own a tree by
                  one of our names
  verdicts      — [{claim, instrument, outcome: pass|fail, evidence}] — claim
                  verbatim from the berth's criteria; instrument what was RUN;
                  evidence what was OBSERVED (a verdict without both is
                  narration, the exact place done may not live — the 2026-07-24
                  correction as schema at the close)
  dispositions  — [{piece, expect, disposition: confirmed|killed, by}] — piece +
                  expect verbatim from the chain's hypothesize berth; ``by`` is
                  the observation that decided it (a kill nobody can point at is
                  a narrated kill)

THE PENDING LEDGER (2026-07-29, ticket the-deposit-rides-the-read) berths at the
bottom of this file: the crossing side of the deposit split. The exit gate
shape-checks the artifact on disk, but the DEPOSIT of it into the hypothesize
tree used to be a sail step a builder remembered — and coupling the chokepoint to
the db/embed hosts would break netns sealing (build_inspector edge (l)). So the
crossing writes the cheap durable half (one appended line in a FILE) and the tree
side pays the db cost at its own door, on its own next read.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

from cairn.tools.gate import gate
from cairn.tools.chain.grammar import (CAIRN_ROOT, INSTANCE_DIR, inspected, lacks_of, ticket_claim_error, ticket_path)
from cairn.tools.chain.chain import (
    BERTHS_ROOT, CHAIN_STAGES, DISPOSITIONS, OUTCOMES,
    _DISPOSITION_FIELDS, _VERDICT_FIELDS,
    chain_for_ticket, claiming_packets, latest_claiming_artifact, verdict_error,
)

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
DEFAULT_NEXUS = "hypothesize"

# A falsifier states its RED conditions as numbered clauses: "RED on any of: (1) …
# (2) …". Consecutive numbering from 1 is REQUIRED, not assumed — a falsifier this
# reader cannot segment refuses rather than silently mis-segmenting, because a
# mis-segmented obligation is an obligation quietly dropped (Law 8).
_CLAUSE_RE = re.compile(r"\((\d+)\)\s*")


class VerdictRefused(RuntimeError):
    """The loud refusal — an artifact this door cannot honestly berth."""


def verdict_nexus(artifact: dict) -> str:
    """WHICH TREE THIS VERDICT TEACHES. Named by the artifact, defaulting to
    ``hypothesize`` — the tree a chart-sourced verdict has always taught, so an
    artifact that says nothing lands exactly where it landed before this field
    existed (ticket watchme-emits-a-probe piece (d): "nexus becomes a specified
    parameter rather than the hardwired hypothesize").

    DELIBERATELY UNCONSTRAINED to any roster. The same ticket's falsifier clause
    (8) makes that a RED: a nexus that can only name one of our own devices would
    mean the design works for the toolchain watching itself and nowhere else. The
    value is a name the consumer resolves, and this door does not adjudicate it."""
    named = artifact.get("nexus")
    return named.strip() if isinstance(named, str) and named.strip() else DEFAULT_NEXUS


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


def inspect_verdict(artifact, root: str = CAIRN_ROOT) -> list:
    """VERDICT'S OWN INSPECTOR — the proof record for the artifact it berths.

    Every question this stage asks, EXPECTED beside ACTUAL, passes included. Akien,
    2026-08-13, ruling every-machine-carries-its-own-inspector-and-gate: "we can backtrack
    and see exactly where something went awry even if it's not something we're
    specifically looking for yet." Stage 8 hands its artifact to no ninth stage, and the
    ruling still lands here — the reader downstream of a verdict is a HUMAN reading the
    chain later, and an unrecorded pass is exactly as mysterious to them.

    A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED. The three checks after the shape one
    read fields whose shape is not yet established, so they only run once it holds: on a
    malformed artifact the record is SHORTER and the gate is already closed. That
    sequencing is the door's own, unchanged — what is new is that it is visible in the
    record rather than implied by the order of four raises.
    """
    err = verdict_error(artifact)
    record = [inspected("shape_is_well_formed", stage="verdict",
                        expected="well-formed", actual="well-formed" if not err else "malformed",
                        lack=err or "")]
    if err:
        return record

    hollow = []
    for i, v in enumerate(artifact.get("verdicts") or []):
        if isinstance(v, dict):
            obs = v.get("discriminating_observation")
            if not isinstance(obs, str) or not obs.strip():
                hollow.append("verdicts[%d]" % i)
    record.append(inspected(
        "every_criterion_carries_a_discriminating_observation", stage="verdict",
        expected=[], actual=hollow,
        lack=("verdict artifact refused — %s: discriminating_observation must be "
              "a non-empty string (a criterion whose instrument was never shown "
              "capable of failing is a hollow green — Law 8)"
              % ", ".join(hollow)) if hollow else ""))
    if hollow:
        return record

    claimed = "ticket" in artifact
    record.append(inspected(
        "verdict_claims_its_ticket", stage="verdict",
        expected="claimed", actual="claimed" if claimed else "unattributed",
        lack="verdict artifact refused — a verdict must claim its ticket"))

    claim_error = ticket_claim_error(artifact, root)
    record.append(inspected(
        "ticket_claim_is_consistent", stage="verdict",
        expected="consistent", actual="consistent" if not claim_error else "inconsistent",
        lack="verdict artifact refused — " + (claim_error or "")))

    items = unanswered(artifact, root)
    record.append(inspected(
        "every_falsifier_clause_is_answered", stage="verdict",
        expected=[], actual=items,
        lack="verdict artifact refused — the chart is not yet answered:\n  "
             + "\n  ".join(items)))
    return record


def validate_verdict(artifact, root: str = CAIRN_ROOT) -> dict:
    """VERDICT'S OWN GATE — an == compare over ``inspect_verdict``'s record.

    The whole door: shape, then the REQUIRED ticket claim (an unattributed verdict answers
    nobody), then coverage. Opens only when every entry's expected equals its actual, per
    entry, no oracle anywhere near it (ruling a-gate-opens-on-an-equality-compare-and-
    never-on-an-oracle). The refusal is the FIRST mismatch's own sentence rather than all
    of them joined, which is this door's long-standing behaviour and is kept deliberately:
    its four checks are sequentially dependent — a malformed artifact cannot be asked
    about its claim, and an artifact with no claim cannot be asked whether the claim is
    consistent — so a joined refusal here would name derived failures as if they were
    independent findings. The record still holds every check that RAN, which is what makes
    the sequencing readable instead of merely obeyed.
    """
    record = inspect_verdict(artifact, root=root)
    if gate.verdict(record)["opens"]:
        return artifact
    raise VerdictRefused(lacks_of(record)[0])


def write_verdict(artifact: dict, *, instance_dir: str = INSTANCE_DIR,
                  root: str = CAIRN_ROOT) -> str:
    """The berth: gate at the door, then land beside the stage packets. Returns
    the path. The artifact is a NEW record — no berthed packet is ever touched."""
    validate_verdict(artifact, root=root)
    os.makedirs(instance_dir, exist_ok=True)
    digest = hashlib.sha256(
        json.dumps(artifact, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = os.path.join(instance_dir, "verdict-%s-%s.json" % (stamp, digest))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(artifact, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def _criterion_part(v: dict) -> str:
    return "%s -> %s [by %s: %s]" % (v["claim"], v["outcome"],
                                     v["instrument"], v["evidence"])


def _disposition_part(d: dict) -> str:
    return "%s: %s — decided by: %s" % (d["disposition"].upper(), d["piece"], d["by"])


def verdict_node_parts(artifact: dict) -> list[tuple[str, str]]:
    """A NODE HOLDS ONE CLAIM (ticket a-node-holds-one-claim, 2026-07-29): the
    verdict rendered as its PARTS — one entry per criterion run verdict, one per
    hypothesis disposition — so each lands as its own node with its own honest
    vector. Returns ``[(kind, content), ...]`` with kind in criterion|disposition.

    WHY PARTS AND NOT ONE NODE. Measured: an eight-claim verdict rendered whole is
    11283 chars and the embed host refuses it outright (nomic-embed-text carries
    context_length 2048; a binary search over that exact content accepted 7403 and
    refused at 7447), while its largest single part is 2113 — every part clears
    with ~3.5x headroom. But size was the messenger, not the defect: ONE vector
    over eight distinct claims is a centroid pointing nowhere in particular, so
    eight vectors each pointing at one claim is MORE ACCURATE, not merely smaller.

    THE PARTS ARE BARE ON PURPOSE — no ticket, no berth, no framing prose. Two
    reasons, and the second is the load-bearing one. (1) The whole rendering below
    is a pure JOIN over these exact strings, so the two renderings are one function
    and cannot drift into the two-mouths defect. (2) node_id_for is a content hash,
    so attribution baked into content would make every part unique BY
    CONSTRUCTION — which is exactly the property that makes a monolith undedupable
    and is the thing this stone exists to end. A recurring disposition shape must
    be able to land on an existing node and corroborate it. Attribution therefore
    rides the node's PROVENANCE, which is where it belongs and where the deposit
    door already gates it."""
    return ([("criterion", _criterion_part(v)) for v in artifact["verdicts"]]
            + [("disposition", _disposition_part(d)) for d in artifact["dispositions"]])


def verdict_node_content(artifact: dict) -> str:
    """The whole-verdict rendering — what killed which, with the deciding
    observation VERBATIM beside each disposition, so a future counsel hit reads the
    kill and its evidence, not a summary of one.

    DERIVED FROM THE PARTS since 2026-07-29, not built beside them: this is a join
    over verdict_node_parts, so there is exactly one place that formats a criterion
    and one that formats a disposition. Kept because the exit gate and the human
    record still want the whole; it is NOT what the tree stores (nothing anywhere
    reassembles a verdict from tree nodes — measured at this stone's survey, which
    is why the composition half was never built)."""
    parts = verdict_node_parts(artifact)
    ran = "; ".join(c for kind, c in parts if kind == "criterion") or "nothing"
    fates = "; ".join(c for kind, c in parts if kind == "disposition") or "none"
    return ("VERDICT for ticket %s — the chart answered at PROVED. CRITERIA: %s. "
            "HYPOTHESES: %s" % (artifact["ticket"], ran, fates))


# ── WHICH BERTH CLAIMS THIS TICKET — THE ONE LATEST-CLAIMER RULE ─────────────
# Factored to cairn/tools/chain/chain.py (2026-09-02, device isolation): the
# chain reader belongs at the chain level, not inside the builder device.
# claiming_packets, latest_claiming_artifact, chain_for_ticket, CHAIN_STAGES,
# and BERTHS_ROOT are now imported from cairn.tools.chain.chain above.


# ── THE PENDING LEDGER (ticket the-deposit-rides-the-read, 2026-07-29) ───────
# An append-only JSONL in chart's instance-space, TWO RECORD KINDS and no third
# motion: ``enqueued`` (a crossing named a verdict berth that owes the tree a
# deposit) and ``deposited`` (the door landed it, with the node it became).
# PENDING IS DERIVED BY READ — enqueued minus deposited — never by editing or
# removing a line: a record of truth is never changed in place (Law 7), so a
# failed deposit leaves its enqueued line standing and loud instead of vanishing.
#
# Law 6: chart owns the ledger. Both writers (the chokepoint's enqueue and the
# live door's deposited-mark) append through THIS module; nothing else touches
# the file. Tree-free by construction, like everything else here — the crossing
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
    """The enqueued records no ``deposited`` record answers, in enqueue order, one
    per berth — DERIVED BY READ, which is why nothing ever has to be edited."""
    records = read_ledger(ledger_path=ledger_path)
    landed = {r.get("berth") for r in records if r.get("kind") == "deposited"}
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
    depositor, so the ledger reads as the whole story of every deposit.

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

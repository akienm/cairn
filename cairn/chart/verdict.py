"""verdict — the answer a voyage owes its chart (ticket proved-answers-the-chart).

The chart chain ends at validate: what DONE means, measured. This module is the
other side of that promise — the v0 VERDICT ARTIFACT a voyage writes after
running those criteria, and the ONE validator both consumers compose:

  - the EXIT GATE (build_inspector.proved_answers_the_chart, called from the emit
    chokepoint's PROVED entry) shape-checks the artifact before a claimed ticket
    may close;
  - the DEPOSIT FACE (cairn.chart.live's verdict- branch) re-validates the same
    artifact before its dispositions become the hypothesize tree's memory of
    what killed which.

One implementation, two mouths — a door and a gate that disagreed on a single
artifact would be the two-mouths defect measured on the first crossing.

TREE-FREE BY CONSTRUCTION: like cairn.chart.orient (the wire's standing
condition, pinned transitively by the inspector-nexus proof), this module
imports no tree machinery — the fire path from the chokepoint through the
inspector into here can never reach the trees or the db. A verdict is always
hardware. The deposit face therefore lives on the tree side (live.py), not here.

The artifact (verdict-<stamp>-<digest>.json, berthed beside the stage packets):

  ticket        — the cast ticket this verdict answers (REQUIRED here, unlike
                  the stages where a claim is optional: an unattributed verdict
                  answers nobody)
  validate_ref  — the claiming validate berth whose criteria were run
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

import glob
import hashlib
import json
import os
import time

from cairn.chart.orient import CAIRN_ROOT, INSTANCE_DIR, ticket_claim_error

OUTCOMES = ("pass", "fail")
DISPOSITIONS = ("confirmed", "killed")

_VERDICT_FIELDS = ("claim", "instrument", "outcome", "evidence")
_DISPOSITION_FIELDS = ("piece", "expect", "disposition", "by")


class VerdictRefused(RuntimeError):
    """The loud refusal — an artifact this door cannot honestly berth."""


def verdict_error(artifact) -> str | None:
    """Shape only: is this a well-formed verdict artifact? Returns the refusal
    text or None. Coverage against the chain is ``unanswered`` below — shape and
    coverage are separate questions so the gate can name which one failed."""
    if not isinstance(artifact, dict):
        return "verdict artifact must be a dict, got %s" % type(artifact).__name__
    for field in ("ticket", "validate_ref"):
        if not isinstance(artifact.get(field), str) or not artifact[field].strip():
            return "verdict artifact refused — %s must be a non-empty string" % field
    for field, entry_fields, vocab, vocab_field in (
            ("verdicts", _VERDICT_FIELDS, OUTCOMES, "outcome"),
            ("dispositions", _DISPOSITION_FIELDS, DISPOSITIONS, "disposition")):
        entries = artifact.get(field)
        if not isinstance(entries, list):
            return "verdict artifact refused — %s must be a list" % field
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                return "verdict artifact refused — %s[%d] must be a dict" % (field, i)
            for k in entry_fields:
                if not isinstance(entry.get(k), str) or not entry[k].strip():
                    return ("verdict artifact refused — %s[%d].%s must be a non-empty "
                            "string (a verdict without its instrument and evidence is "
                            "narration)" % (field, i, k))
            if entry[vocab_field] not in vocab:
                return ("verdict artifact refused — %s[%d].%s must be one of %s, got %r"
                        % (field, i, vocab_field, "|".join(vocab), entry[vocab_field]))
    return None


def _read_chain(artifact) -> tuple[list, list, str | None]:
    """Read what must be answered: the claiming validate berth's criteria and its
    hypothesize berth's hypotheses. Returns (criteria, hypotheses, error) — a
    chain that cannot be read is an error, never an empty obligation (a gate that
    silently inspects nothing passes everything, Law 8)."""
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


def unanswered(artifact) -> list[str]:
    """Coverage: every criterion answered (and PASSING — an answered-and-failed
    criterion is a kick-back, not a crossing), every hypothesis dispositioned.
    Returns one line per unanswered item, complete on the first pass."""
    criteria, hypotheses, err = _read_chain(artifact)
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


def validate_verdict(artifact, root: str = CAIRN_ROOT) -> dict:
    """The whole door: shape, then the REQUIRED ticket claim (an unattributed
    verdict answers nobody), then coverage. Loud and complete on first pass."""
    err = verdict_error(artifact)
    if err:
        raise VerdictRefused(err)
    if "ticket" not in artifact:
        raise VerdictRefused("verdict artifact refused — a verdict must claim its ticket")
    claim_error = ticket_claim_error(artifact, root)
    if claim_error:
        raise VerdictRefused("verdict artifact refused — " + claim_error)
    items = unanswered(artifact)
    if items:
        raise VerdictRefused(
            "verdict artifact refused — the chart is not yet answered:\n  "
            + "\n  ".join(items))
    return artifact


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
# Factored here 2026-07-29 (ticket the-deposit-rides-the-read) out of the exit
# gate, which owned the only copy: the gate globs berthed packets for a ticket
# claim and takes the LAST as the answer that stands. The enqueue below needs
# the identical rule — so it is composed by import, never mirrored. A gate and
# an enqueue that disagreed about WHICH artifact answered would deposit one
# verdict while the gate judged another (the two-mouths defect, in a place
# nobody would look for it).
#
# ~/.cairn/devices/chart — the chart device's berths, one directory per instance
# (INSTANCE_DIR is instance 0's packets/ child; a singleton is instance 0, not a
# special case).
BERTHS_ROOT = os.path.dirname(os.path.dirname(INSTANCE_DIR))


def claiming_packets(ticket: str, stage: str, *, berths_root=None) -> list[tuple]:
    """Every readable berthed ``<stage>-*.json`` packet whose ``ticket`` field names
    ``ticket``, OLDEST FIRST — the stamp rides the filename, so sorted order is
    chronological and the LAST entry is the one that stands.

    An unreadable berth names no claim and is skipped here (the berth owner's own
    sweep carries that finding — a gate must not invent a claim it cannot read).
    Returns ``[(path, packet), ...]`` with paths as strings."""
    root = os.path.expanduser(str(berths_root if berths_root is not None else BERTHS_ROOT))
    found = []
    for path in sorted(glob.glob(os.path.join(root, "*", "packets", "%s-*.json" % stage))):
        try:
            with open(path, encoding="utf-8") as fh:
                packet = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(packet, dict) and packet.get("ticket") == ticket:
            found.append((path, packet))
    return found


def latest_claiming_artifact(ticket: str, *, berths_root=None):
    """The verdict artifact that STANDS for ``ticket`` — ``(path, artifact)`` or
    ``None`` when nothing claims it. The latest answer is the one that stands
    (verdict multiplicity beyond latest-wins is the exit ticket's filed edge (b))."""
    found = claiming_packets(ticket, "verdict", berths_root=berths_root)
    return found[-1] if found else None


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

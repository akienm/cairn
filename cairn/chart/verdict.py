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
"""
from __future__ import annotations

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


def verdict_node_content(artifact: dict) -> str:
    """The ONE rendering of a verdict as a tree node's content — what killed
    which, with the deciding observation VERBATIM beside each disposition, so a
    future counsel hit reads the kill and its evidence, not a summary of one."""
    ran = "; ".join("%s -> %s [by %s: %s]" % (v["claim"], v["outcome"],
                                              v["instrument"], v["evidence"])
                    for v in artifact["verdicts"]) or "nothing"
    fates = "; ".join("%s: %s — decided by: %s" % (d["disposition"].upper(),
                                                   d["piece"], d["by"])
                      for d in artifact["dispositions"]) or "none"
    return ("VERDICT for ticket %s — the chart answered at PROVED. CRITERIA: %s. "
            "HYPOTHESES: %s" % (artifact["ticket"], ran, fates))

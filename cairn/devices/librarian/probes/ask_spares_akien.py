"""PROBE — ask_spares_akien

Berth for the WATCHME that ticket ``cd8096f9eeca`` carries. Berthed beside the librarian
because that is where the answers tree lives and where `cairn librarian ask` writes: every
ask leaves one learning-block state log (block ``librarian-ask``, event ``engine_run``) in
the same act as its judgement, so the reading needs no instrument of its own — it reads
those records and the question corpus they escalate into.

THE QUESTION: over live use, does the ask spare Akien the settled? A resolved run is one
question that did not reach him; an escalated run did. For each escalation the probe
follows the question it opened (matched by its words and source ``librarian ask``) to his
answer, and asks whether a later re-ask RESOLVED to that record by walk. Two readings are
breaches, carried the moment they appear (Law 7, complete diagnostic on the first report):
his answer to an escalated question reads "already answered" (the tree let a settled
question through), or a later ask of the same words resolved to a DIFFERENT record than the
one his answer made (the tree held it all along). Enough is 30 live asks. Runs marked
``testing`` in their input are a proof's, never use, and are not counted.

    python3 cairn/devices/librarian/probes/ask_spares_akien.py
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket, once

_OWNING_TICKET = "cd8096f9eeca"
_BLOCK = "librarian-ask"
ENOUGH_RUNS = 30
_QID = re.compile(r"question:(open-[0-9a-f]{12})")
_ALREADY = re.compile(r"already\s+answered", re.IGNORECASE)


def _winner_qid(run: dict) -> str | None:
    w = (run.get("data") or {}).get("winner")
    m = _QID.search((w or {}).get("why") or "")
    return m.group(1) if m else None


def survey(*, trace_root: Path | None = None, questions_root: Path | None = None) -> dict:
    from cairn.machines.learning_block.engine import RUN_EVENT
    from cairn.machines.learning_block.learning_block import read_trace
    from cairn.tools.question import question as Q

    runs = [r for r in read_trace(_BLOCK, root=trace_root)
            if r.get("event") == RUN_EVENT
            and not ((r.get("data") or {}).get("input") or {}).get("testing")]
    qdir = Path(questions_root) if questions_root is not None else Q.QUESTIONS_DIR
    opened: dict[str, list[dict]] = {}
    for p in sorted(qdir.glob(f"{Q.PREFIX}*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if str(rec.get("source") or "") == "librarian ask":      # live only; a proof's carries "(testing: ...)"
            opened.setdefault(str(rec.get("question") or ""), []).append(rec)

    resolved = [r for r in runs if (r.get("data") or {}).get("winner")]
    zero_inference = [r for r in resolved
                      if not ((r["data"].get("input") or {}).get("backfills") or 0)]
    escalations, breaches = [], []
    for i, r in enumerate(runs):
        if (r.get("data") or {}).get("winner"):
            continue
        words = ((r.get("data") or {}).get("input") or {}).get("question") or ""
        recs = opened.get(words, [])
        answered = [q for q in recs if q.get("resolved") and q.get("answer")]
        later = runs[i + 1:]
        closed_by = None
        for q in answered:
            for lr in later:
                if _winner_qid(lr) == q.get("id"):
                    closed_by = lr.get("id")
                    break
            if _ALREADY.search(str(q.get("answer"))):
                breaches.append({"kind": "answered 'already answered'", "run": r.get("id"),
                                 "question": words, "record": q.get("id"),
                                 "answer": q.get("answer")})
            for lr in later:
                lw = ((lr.get("data") or {}).get("input") or {}).get("question")
                wq = _winner_qid(lr)
                if lw == words and wq and wq != q.get("id"):
                    breaches.append({"kind": "re-ask resolved to a different record",
                                     "run": lr.get("id"), "question": words,
                                     "his_record": q.get("id"), "resolved_to": wq})
        escalations.append({"run": r.get("id"), "when": r.get("when"), "question": words,
                            "opened": [q.get("id") for q in recs],
                            "answered": [q.get("id") for q in answered],
                            "reask_resolved_by_walk": closed_by})
    return {
        "runs": len(runs),
        "resolved_by_walk": len(resolved),
        "resolved_with_zero_inference": len(zero_inference),
        "escalated": len(escalations),
        "escalations": escalations,
        "breaches": breaches,
        "holds": not breaches,
        "surveyed_at": datetime.now(timezone.utc).isoformat(),
    }


def _trigger(now, context: dict) -> bool:
    s = once(context, "survey", survey)
    return bool(s["breaches"]) or s["runs"] >= ENOUGH_RUNS


def _enough(context: dict) -> bool:
    s = once(context, "survey", survey)
    return bool(s["breaches"]) or s["runs"] >= ENOUGH_RUNS


def _carry(context: dict) -> dict:
    s = once(context, "survey", survey)
    closed = sum(1 for e in s["escalations"] if e["reask_resolved_by_walk"])
    if s["holds"]:
        finding = (f"SPARES — {s['runs']} live ask(s): {s['resolved_by_walk']} resolved by walk "
                   f"({s['resolved_with_zero_inference']} with zero inference), {s['escalated']} "
                   f"escalated, {closed} of those answered and then resolved by walk on a re-ask")
    else:
        finding = (f"LETS THROUGH — {len(s['breaches'])} breach(es) over {s['runs']} live ask(s): "
                   + "; ".join(f"{b['kind']}: {b['question']!r}" for b in s["breaches"]))
    return {"finding": finding, "survey": s, "ticket": owning_ticket(_OWNING_TICKET)}


PROBE = Probe(
    why="his review bandwidth is what everything runs on, and a question he already answered "
        "spends it on the settled (Law 1); this probe watches, over 30 live asks, whether the "
        "answers tree catches equivalent questions or lets them through to him",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "ask_spares_akien"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)


if __name__ == "__main__":
    s = survey()
    print(json.dumps({
        "survey": s,
        "would_trigger": _trigger(None, {"survey": s}),
        "enough": _enough({"survey": s}),
        "carry": _carry({"survey": s}),
    }, indent=2, default=str))

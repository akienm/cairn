"""codemother/adjudicate.py — a red ticket is adjudicated against both whys and CP1-CP6 (ticket aa2d42b15886).

Outline 17.11.6 and 9.4.2.3.7: when a proof reds, either the CODE is wrong (it no longer does
what its component is for) or the TOOTH is wrong (the check no longer measures what it was
written to measure). There is no third outcome. A tooth change needs a decision behind it
(CLAUDE.md, a deterministic red carries a decision — never a paragraph), and since ticket
9adc6fddf185 a decision is an answered question. So the verdict lands as one question bound to
the red ticket, answered with ``--measured`` citing the proof it read; the reseal door's rung
4 accepts that question's id (a resolved ``open-`` question lifts it, whoever answered).

What the reader is given, and nothing else:
  - the red ticket's ``fixes`` entry — the proof — and its source;
  - the TOOTH'S WHY: the proof's docstring and its PROVES map;
  - the COMPONENT'S WHY: the ``why`` of the charter the ticket names as ``owning_intention``;
  - CairnCommons/intentions-not-beside-code/core-values.md (CP1-CP6);
  - the run record named in the ticket's ``measured``, when it is a file.

The reader is an LLM asked over the bus (``inference``'s ``infer`` verb — the ask codemother's
watch.py already makes); this module never imports the inference device (RULE 1). Its answer
must be JSON ``{"verdict": "code-wrong"|"tooth-wrong", "reasons": [...]}`` with every reason
naming the why or CP it rests on. Anything else is refused loudly, and nothing is written
(Law 7): an unreadable verdict recorded as a verdict is the collapse a record of truth may
never make.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from cairn.tools.base.address import ROOTS

OUTCOMES = ("code-wrong", "tooth-wrong")
_GROUNDS = re.compile(r"\b(CP[1-6]|component'?s? why|tooth'?s? why)\b", re.IGNORECASE)
_RECORD = re.compile(r"record (\S+?);")


class AdjudicationRefused(RuntimeError):
    """The verdict could not be reached or read. The message names why; nothing was written."""


# --- what the reader is given ------------------------------------------------------------

def tooth_why(proof_source: str) -> str:
    """The proof's docstring and its PROVES map, as written."""
    tree = ast.parse(proof_source)
    doc = ast.get_docstring(tree) or ""
    proves = ""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PROVES" for t in node.targets):
            proves = ast.get_source_segment(proof_source, node) or ""
    return (doc + ("\n\n" + proves if proves else "")).strip()


def gather(ticket: dict, *, repo: Path | None = None, commons: Path | None = None) -> dict:
    """Everything the reader reads, keyed; raises AdjudicationRefused naming a missing piece."""
    repo = Path(repo or ROOTS["repo"])
    commons = Path(commons or ROOTS["commons"])
    fixes = ticket.get("fixes") or []
    if not fixes or not isinstance(fixes[0], str):
        raise AdjudicationRefused(f"ticket {ticket.get('id')}: no `fixes` entry names the red proof")
    proof = Path(fixes[0]) if Path(fixes[0]).is_absolute() else repo / fixes[0]
    if not proof.is_file():
        raise AdjudicationRefused(f"ticket {ticket.get('id')}: the proof {proof} is not a file")
    source = proof.read_text(encoding="utf-8")
    charter_rel = ticket.get("owning_intention") or ""
    charter = repo / charter_rel
    if not (charter_rel and charter.is_file()):
        raise AdjudicationRefused(f"ticket {ticket.get('id')}: owning_intention {charter_rel!r} is not a charter on disk")
    component_why = json.loads(charter.read_text(encoding="utf-8")).get("why") or ""
    if not component_why:
        raise AdjudicationRefused(f"{charter}: the charter carries no why")
    cv = commons / "intentions-not-beside-code" / "core-values.md"
    if not cv.is_file():
        raise AdjudicationRefused(f"{cv}: CP1-CP6 are not on disk")
    run = ""
    for m in ticket.get("measured") or []:
        hit = _RECORD.search(str((m or {}).get("how", "")) + ";")
        if hit and Path(hit.group(1)).is_file() and Path(hit.group(1)) != proof:
            run = Path(hit.group(1)).read_text(encoding="utf-8")[-8000:]
    return {"ticket": ticket.get("id"), "proof": str(proof), "proof_source": source,
            "tooth_why": tooth_why(source), "component_why": component_why,
            "core_values": cv.read_text(encoding="utf-8"), "run_record": run,
            "saw": "; ".join(str((m or {}).get("saw", "")) for m in ticket.get("measured") or [])}


def prompt(g: dict) -> str:
    return (
        "A proof ran red. Decide whether the CODE is wrong (it no longer serves the component's "
        "why) or the TOOTH is wrong (the check no longer measures what its why says it "
        "measures). There is no third outcome.\n\n"
        f"COMPONENT'S WHY:\n{g['component_why']}\n\n"
        f"TOOTH'S WHY (the proof's docstring and PROVES):\n{g['tooth_why']}\n\n"
        f"CORE VALUES CP1-CP6:\n{g['core_values']}\n\n"
        f"WHAT THE TESTER SAW:\n{g['saw']}\n\n"
        f"RUN RECORD:\n{g['run_record'] or '(none on disk)'}\n\n"
        f"PROOF SOURCE ({g['proof']}):\n{g['proof_source']}\n\n"
        'Answer with JSON only: {"verdict": "code-wrong" or "tooth-wrong", "reasons": '
        '["...", ...]}. Every reason names what it rests on: the component\'s why, the '
        "tooth's why, or a CP by number (CP1..CP6)."
    )


# --- reading the answer ------------------------------------------------------------------

def read_verdict(text: str) -> dict:
    """``{"verdict", "reasons"}`` from the reader's text, or AdjudicationRefused naming why."""
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not m:
        raise AdjudicationRefused(f"the reader's answer carries no JSON verdict: {(text or '')[:300]!r}")
    try:
        doc = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise AdjudicationRefused(f"the reader's verdict is not JSON ({exc}): {m.group(0)[:300]!r}") from exc
    verdict = doc.get("verdict")
    if verdict not in OUTCOMES:
        raise AdjudicationRefused(f"the reader answered {verdict!r}, which is neither {' nor '.join(OUTCOMES)} "
                                  "(17.11.6: there is no third outcome)")
    reasons = doc.get("reasons")
    if not (isinstance(reasons, list) and reasons and all(isinstance(r, str) and r.strip() for r in reasons)):
        raise AdjudicationRefused(f"the reader's {verdict} carries no reasons: {reasons!r}")
    ungrounded = [r for r in reasons if not _GROUNDS.search(r)]
    if ungrounded:
        raise AdjudicationRefused(f"a reason names no why and no CP: {ungrounded[0]!r}")
    return {"verdict": verdict, "reasons": [r.strip() for r in reasons]}


def ask_inference(bus, text: str) -> str:
    """One ``infer`` ask of the inference device over the bus; a refusal raises, naming it."""
    reply = bus.request(sender="codemother", to="inference", channel="personal", verb="infer",
                        why="adjudicate a red ticket: code-wrong or tooth-wrong (ticket aa2d42b15886)",
                        body={"kind": "generate", "prompt": text, "domain": "coding"}, timeout=300.0)
    body = (reply or {}).get("body") or {}
    if body.get("outcome") == "refused" or body.get("answer") is None:
        raise AdjudicationRefused(f"inference refused ({body.get('refused')}): {body.get('detail')}")
    answer = body["answer"]
    return answer.get("text", "") if isinstance(answer, dict) else str(answer)


# --- the act -----------------------------------------------------------------------------

def adjudicate(ticket: dict, *, ask, repo: Path | None = None, commons: Path | None = None,
               question_root: Path | None = None) -> dict:
    """Read, ask, and record. ``ask(prompt) -> text`` is the reader. The verdict is read and
    checked BEFORE anything is written, so a refused verdict leaves no question behind."""
    from cairn.tools.question import question as q

    g = gather(ticket, repo=repo, commons=commons)
    v = read_verdict(ask(prompt(g)))
    tid = ticket.get("id")
    opened = q.open_question(
        tid, f"Is the red on {Path(g['proof']).name} code-wrong or tooth-wrong?",
        "a tooth change needs a decision behind it; this verdict is that decision (ticket aa2d42b15886)",
        source="codemother adjudicate", root=question_root)
    words = f"{v['verdict']}: " + " | ".join(v["reasons"])
    q.answer(opened["id"], words, spawned=[], measured=g["proof"], root=question_root)
    return {"ticket": tid, "question": opened["id"], **v}


def find_ticket(tid: str, commons: Path | None = None) -> dict:
    tickets = Path(commons or ROOTS["commons"]) / "tickets"
    hits = [p for p in tickets.glob(f"{tid}-*.json") if not p.name.endswith(".state.json")]
    if len(hits) != 1:
        raise AdjudicationRefused(f"ticket {tid!r}: {len(hits)} ticket files under {tickets}")
    return json.loads(hits[0].read_text(encoding="utf-8"))

"""librarian/ask.py — `cairn librarian ask "<question>"`: the one path CC takes to a question
(ticket cd8096f9eeca).

THE LIVED SYMPTOM (Akien, 2026-09-29): three of one morning's questions had already been
answered and cast, and he had noticed — "i've developed a confidence that i really am giving
you the same answers each time, even if i do it with different words." His review bandwidth
is what everything runs on, and a re-asked question spends it on the settled (Law 1).

THE SHAPE, his words: the librarian answers from what the system already holds, "the graph
trees ... will help us get equivalent questions answered with the same answer", failing over
to "llm node deposit", and only then to his inbox — "and if something not clear enough, then
you can ask follow on questions, and the system keeps learning."

    fold     answered question records -> the 'answers' tree (its own leaf table), by sha,
             at read — no daemon; an unchanged corpus costs nothing (D1, D4)
    walk     resolve_query over that tree, exactly as the loop runs everywhere: graph first,
             the host supplies NODES on a miss, a same-crossing mint never counts (D5)
    block    the walk's nodes become the learning block's candidates in walk order; the
             constraints admit only his answer — unrefuted, over the floor, from an answered
             record (D6, ask_block.json); run_block writes the state log. A mint is killed by
             source, not by the walk's evidence label: his answers never decay (D7, loop.py)
    escalate what survives nothing goes to `cairn question operator` — bound to a ticket, or
             handed back as the ready command when there is none (D9); once he answers, the
             next ask folds it and the equivalent re-ask resolves by walk (D10)

The content of an answers node is the question AND the answer ("yes B" alone reads as
nothing); its vector is the QUESTION's, because a re-ask lands by what it asks.

    cairn librarian ask "<question?>" [--ticket <id> --why "<what it blocks>"] [--json]
      exit 0  resolved — his answer, the record id, the similarity
      exit 3  escalated — opened (with --ticket) or the operator command to run
      exit 2  the ask could not run (inference host down, door refusal) — never an escalation
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path

from cairn.devices.librarian.loop import RESOLUTION_FLOOR, resolve_query
from cairn.devices.librarian.trees import LibrarianDevice
from cairn.machines.learning_block.engine import run_block
from cairn.tools.base.address import instance_path
from cairn.tools.question import question as Q

# The answers tree is its own leaf table — in the three-table design the leaf IS the tree,
# so a shared leaf would let commons nodes walk as answers.
ANSWERS = "librarian_answers"
TREE = "answers"
SPEC = Path(__file__).resolve().parent / "ask_block.json"
SOURCE = "librarian ask"
ANSWERED = "answered_question"


def ledger_default() -> Path:
    return instance_path("librarian", 0) / "tools" / "ask" / "learned.json"


def node_content(question: str, answer: str) -> str:
    return f"Q: {question.strip()}\nA: {answer.strip()}"


def _load_ledger(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def fold(*, resolve, table: str = ANSWERS, questions_root=None, ledger_path=None,
         testing: str | None = None, dev: LibrarianDevice | None = None, conn=None) -> dict:
    """Fold every answered question record new or changed since the last fold into the
    answers tree. Returns {deposited, attested, unchanged, skipped}."""
    qdir = Path(questions_root) if questions_root is not None else Q.QUESTIONS_DIR
    ledger_path = Path(ledger_path) if ledger_path is not None else ledger_default()
    ledger = _load_ledger(ledger_path)
    dev = dev or LibrarianDevice()
    out = {"deposited": 0, "attested": 0, "unchanged": 0, "skipped": 0}
    for p in sorted(qdir.glob(f"{Q.PREFIX}*.json")):
        raw = p.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if ledger.get(p.stem) == sha:
            out["unchanged"] += 1
            continue
        try:
            rec = json.loads(raw)
        except ValueError:
            out["skipped"] += 1
            continue
        answer = rec.get("answer")
        if not (rec.get("resolved") and isinstance(answer, str) and answer.strip()
                and isinstance(rec.get("question"), str)):
            out["skipped"] += 1      # not ledgered: an open question folds once it is answered
            continue
        if answer.lstrip().upper().startswith("VOID"):
            # the corpus's withdrawal convention ("VOID — not Akien's words ... re-asked whole
            # as the spawned follow-up", open-ee4a67728294): the field says it is not his
            # answer, so it never becomes one (D13)
            out["skipped"] += 1
            continue
        provenance = {"source": f"question:{rec.get('id') or p.stem}",
                      "question": rec["question"],
                      "answered_by": rec.get("answered_by"),
                      "answered_at": rec.get("answered_at"), "sha256": sha}
        if testing:
            provenance["testing"] = testing
        vector = resolve({"kind": "embed", "prompt": rec["question"]})["answer"]["vector"]
        r = dev.deposit(node_content(rec["question"], answer), vector, provenance,
                        tree=TREE, table=table, conn=conn)
        out["attested" if r.get("duplicate") else "deposited"] += 1
        ledger[p.stem] = sha
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return out


def _candidate(rank: int, node: dict, floor: float) -> dict:
    prov = node.get("provenance") or {}
    src = str(prov.get("source") or "")
    kind = ANSWERED if src.startswith("question:") else (src or "unknown")
    return {"name": f"{rank}:{node['node_id'][:12]}",
            "why": f"{src or 'no source'} at similarity {node['similarity']:.4f}",
            "provides": {"not_refuted": node.get("standing") != "refuted",
                         "clears_floor": node["similarity"] >= floor,
                         "source_kind": kind}}


def operator_command(question: str, ticket: str | None = None) -> str:
    return ("cairn question operator " + shlex.quote(question)
            + " --ticket " + (shlex.quote(ticket) if ticket else "<ticket-id>")
            + " --why " + shlex.quote("<what the build cannot settle without it>"))


def ask(question: str, *, resolve, table: str = ANSWERS, questions_root=None,
        ledger_path=None, trace_root=None, ticket: str | None = None, why: str | None = None,
        testing: str | None = None, floor: float = RESOLUTION_FLOOR,
        dev: LibrarianDevice | None = None, conn=None) -> dict:
    """One ask: fold, walk, judge, and either answer or escalate. Never a guess."""
    dev = dev or LibrarianDevice()
    folded = fold(resolve=resolve, table=table, questions_root=questions_root,
                  ledger_path=ledger_path, testing=testing, dev=dev, conn=conn)
    verdict = resolve_query(question, resolve=resolve, tree=TREE, table=table, floor=floor,
                            dev=dev, conn=conn)
    walk = verdict.get("nodes") or []

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    spec["candidates"] = ([_candidate(i, n, floor) for i, n in enumerate(walk)]
                          + spec["candidates"])
    payload = {"question": question, "floor": floor, "tree": table,
               "verdict": verdict.get("verdict"), "reason": verdict.get("reason"),
               "backfills": verdict.get("backfills")}
    if testing:
        payload["testing"] = testing
    trace = run_block(spec, payload, root=Path(trace_root) if trace_root else None)

    walk_view = [{k: n.get(k) for k in ("node_id", "content", "similarity", "evidence",
                                        "evidence_why", "standing", "provenance")}
                 for n in walk]
    out = {"asked": question, "outcome": None, "qid": None, "question": None, "answer": None,
           "answered_by": None,
           "similarity": None, "opened": None, "operator_command": None, "folded": folded,
           "verdict": verdict.get("verdict"), "reason": verdict.get("reason"),
           "walk": walk_view, "trace": trace}

    winner = (trace.get("data") or {}).get("winner")
    if winner:
        node = walk[int(winner["name"].split(":", 1)[0])]
        prov = node.get("provenance") or {}
        q, _, a = node["content"].partition("\nA: ")
        out.update(outcome="resolved", qid=prov["source"].split(":", 1)[1],
                   question=q[len("Q: "):] if q.startswith("Q: ") else q, answer=a,
                   answered_by=prov.get("answered_by"),
                   similarity=node["similarity"])
        return out

    out["outcome"] = "escalated"
    out["operator_command"] = operator_command(question, ticket)
    if ticket and why:
        rec = Q.operator(ticket, question, why,
                         source=SOURCE + (f" (testing: {testing})" if testing else ""),
                         root=questions_root)
        out["opened"] = rec["id"]
    return out


def _render(r: dict) -> str:
    if r["outcome"] == "resolved":
        return (f"answered: {r['qid']}  (similarity {r['similarity']:.3f})\n"
                f"  asked:    {r['asked']}\n  on record: {r['question']}\n"
                f"  answer:   {r['answer']}\n"
                f"  by:       {r['answered_by']}")
    lines = [f"not on record — escalate: {r['asked']}"]
    if r["opened"]:
        lines.append(f"  opened {r['opened']} in the operator inbox")
    else:
        lines.append("  no --ticket given; to put it in the operator inbox run:")
        lines.append(f"  {r['operator_command']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cairn librarian ask",
                                description="answer a question from what Akien already said; "
                                            "escalate to the operator inbox when nothing covers it")
    p.add_argument("question")
    p.add_argument("--ticket", help="the ticket the question is bound to (needed to open it)")
    p.add_argument("--why", help="what the build cannot settle without the answer")
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args(argv)
    try:
        from cairn.devices.librarian.live import _wire_bus, dual_seam
        resolve = dual_seam(_wire_bus())
        r = ask(args.question, resolve=resolve, ticket=args.ticket, why=args.why)
    except Exception as e:  # a down host or a refusing door is loud, never an escalation (Law 7)
        print(f"cairn librarian ask: could not run — {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if args.as_json:
        slim = {k: v for k, v in r.items() if k not in ("walk", "trace")}
        slim["trace_id"] = (r.get("trace") or {}).get("id")
        print(json.dumps(slim, indent=1, default=str))
    else:
        print(_render(r))
    return 0 if r["outcome"] == "resolved" else 3


if __name__ == "__main__":
    sys.exit(main())

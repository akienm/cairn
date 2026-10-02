"""Proof for librarian/ask.py — `cairn librarian ask "<question>"`, the one path CC takes to
a question (ticket cd8096f9eeca). Written and run RED before any of the build landed (D12,
Akien 2026-09-29: "prove THEN work THEN prove the final state").

Teeth a hollow ask could not pass:

  - A PARAPHRASE LANDS ON THE ANSWER: a question worded differently from one Akien answered
    resolves by walk to THAT record's id, his words verbatim, with no generate call.
  - THE FOLD IS INCREMENTAL: a second fold of an unchanged corpus deposits 0 and embeds 0;
    a changed record re-folds.
  - AN UNCOVERED QUESTION REACHES HIM ONCE: it escalates, and with a ticket opens exactly
    one question record through the question door; without one it opens nothing and hands
    back the ready-to-run `cairn question operator` command.
  - THE LOOP CLOSES: once that question is answered, an equivalent re-ask resolves to it
    without reaching him.
  - STRUCTURE THAT ISN'T HIS ANSWER NEVER WINS: an LLM-minted node that clears the floor on
    a later crossing is killed by the block (source_kind), and a refuted answer is killed
    (not_refuted) — both escalate.
  - HIS ANSWER DOES NOT DECAY: with the decay horizon forced past, an answered record still
    resolves with no generate — decay is for mints, and a faded answer would re-ask him.
  - THE RUN IS A STATE LOG: every ask's trace answers the learning block's five questions.
  - TEST OUTPUT CARRIES THE TESTING MARK (Akien 2026-09-28, ticket 71d1bbfa98b0): every node
    this proof folds and every question it opens says it came from testing.
  - THE VERBS RESOLVE: `cairn librarian ask --help` and `cairn question operator` answer.

The store is the LIVE database through db_domain on a scratch leaf (dropped at exit, its
nodes forgotten); the inference seam is a deterministic fake; questions, traces and the
fold ledger live in a tmp world under diagnostic artifact roots.

    python3 cairn/devices/librarian/proofs/test_librarian_ask.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

TICKET = "cd8096f9eeca"
PROVES = {TICKET: {"all": "test_the_librarian_answers_before_akien_is_asked"}}
MARK = "proofs/test_librarian_ask.py"
TID = "0badc0ffee01"
FAILURES: list[str] = []

# A five-axis fake embedding space. Answered questions sit on their own axes; everything
# the fake does not know lands on the junk axis — valid direction, poor cosine to all.
Q_SEAL = "Should CC sign and seal concept-pieces itself from now on?"
A_SEAL = "a) Yes: CC signs and seals concept-pieces from now on."
Q_HEX = "Does anything besides inference run on Hex?"
A_HEX = "NOTHING runs on hex except inference."
PARA_SEAL = "May CC put its own seal on a concept-piece?"
PARA_HEX = "Can the bus live on the Hex box?"
UNCOVERED = "What colour is the operator's bike shed?"
UNCOVERED_AGAIN = "Which colour did Akien pick for the bike shed?"
A_SHED = "Green, obviously."
MINTQ = "When does the away verb's clearance end?"
MINT = "The away verb clears CC to use everything until 06:00 local time."
REFUTER = "Akien 2026-09-29: the Hex answer on record was recorded against the wrong question."
JUNK = "This junk fixture node explains nothing about the request at all."
# a withdrawn record, in the corpus's own convention (open-ee4a67728294, open-bcca3badf4ae):
# the answer field says it is NOT his words, so it is never an answer
Q_VOID = "Is the  breakage fixed inside this voyage?"
A_VOID = ("VOID — not Akien's words: CC's shell expanded the backticked command name before "
          "the door saw the text. Re-asked whole as the spawned follow-up.")

VEC = {
    Q_SEAL: [1, 0, 0, 0, 0], PARA_SEAL: [0.97, 0.2, 0, 0, 0],
    Q_HEX: [0, 1, 0, 0, 0], PARA_HEX: [0.05, 0.99, 0, 0, 0],
    UNCOVERED: [0, 0, 1, 0, 0], UNCOVERED_AGAIN: [0, 0.1, 0.99, 0, 0],
    MINTQ: [0, 0, 0, 1, 0], MINT: [0, 0, 0.05, 0.99, 0],
}
FAR = [0, 0, 0, 0, 1]
# what the fake host drafts per request — the mint question gets a node that lands beside it
DRAFTS = {MINTQ: [MINT]}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def fake_seam():
    calls = {"embed": [], "generate": []}

    def resolve(request):
        if request["kind"] == "embed":
            calls["embed"].append(request["prompt"])
            return {"answer": {"vector": [float(x) for x in VEC.get(request["prompt"], FAR)]},
                    "hit": False}
        calls["generate"].append(request["prompt"])
        req = request["prompt"].split("REQUEST: ", 1)[-1].split("\n", 1)[0]
        return {"answer": {"text": json.dumps({"nodes": DRAFTS.get(req, [JUNK])})}, "hit": False}

    resolve.calls = calls
    return resolve


def _answered(qdir: Path, qid: str, question: str, words: str) -> None:
    """A fixture answered record in the scratch world — the shape the question door writes."""
    rec = {"id": qid, "date": "2026-09-29", "ticket": TID, "question": question,
           "why_it_blocks": "fixture", "raised_by": "cc (proof)", "born_of": None,
           "source": f"testing: {MARK}", "resolved": True, "answer": words,
           "answered_by": "akien (fixture)", "answered_at": "2026-09-29T12:00:00-07:00",
           "spawned": []}
    (qdir / f"{qid}.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")


def test_the_librarian_answers_before_akien_is_asked() -> None:
    from cairn.tools.artifact import artifact as A
    from cairn.devices.librarian.tools.trees.trees import NODES_TABLE, forget_leaf, node_id_for, refute, scratch_leaf
    from cairn.devices.librarian.device import LibrarianDevice
    from cairn.devices.db_domain.tools.client import store
    from cairn.machines.learning_block.engine import answers_five_questions
    from cairn.devices.librarian import ask as ASK
    from cairn.tools.question import question as Q

    with tempfile.TemporaryDirectory(prefix="proof-librarian-ask-") as td, \
            scratch_leaf("ask_answers") as table:
        tmp = Path(td)
        commons = tmp / "CairnCommons"
        qdir = commons / "questions"
        qdir.mkdir(parents=True)
        (commons / "tickets").mkdir()
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn",
                                "parked": tmp / "parked"})
        _answered(qdir, "open-000000000a01", Q_SEAL, A_SEAL)
        _answered(qdir, "open-000000000a02", Q_HEX, A_HEX)
        _answered(qdir, "open-000000000a0f", Q_VOID, A_VOID)
        dev = LibrarianDevice()
        dev.set_diagnostic_receiver(None)
        kw = dict(table=table, questions_root=qdir, ledger_path=tmp / "learned.json",
                  trace_root=tmp / "traces", testing=MARK, dev=dev)
        try:
            seam = fake_seam()

            # --- the fold -----------------------------------------------------------
            f1 = ASK.fold(resolve=seam, table=table, questions_root=qdir,
                          ledger_path=tmp / "learned.json", testing=MARK)
            check("the first fold deposits every answered record, and never a VOID one",
                  f1.get("deposited") == 2 and f1.get("skipped") == 1, f"fold 1 = {f1}")
            before = len(seam.calls["embed"])
            f2 = ASK.fold(resolve=seam, table=table, questions_root=qdir,
                          ledger_path=tmp / "learned.json", testing=MARK)
            check("a second fold of an unchanged corpus deposits 0 and embeds 0",
                  f2.get("deposited") == 0 and len(seam.calls["embed"]) == before,
                  f"fold 2 = {f2}, embeds spent = {len(seam.calls['embed']) - before}")

            # --- a paraphrase lands on his answer -----------------------------------
            gen0 = len(seam.calls["generate"])
            r = ASK.ask(PARA_SEAL, resolve=seam, **kw)
            check("a paraphrase resolves to the answered record's id",
                  r.get("outcome") == "resolved" and r.get("qid") == "open-000000000a01",
                  f"outcome={r.get('outcome')} qid={r.get('qid')}")
            check("his words come back verbatim", r.get("answer") == A_SEAL, repr(r.get("answer")))
            check("who answered comes back verbatim — a measurement is never labelled as him",
                  r.get("answered_by") == "akien (fixture)"
                  and "akien (fixture)" in ASK._render(r), repr(r.get("answered_by")))
            check("the resolved ask spent no generate",
                  len(seam.calls["generate"]) == gen0,
                  f"{len(seam.calls['generate']) - gen0} generate call(s)")
            traces = [r.get("trace") or {}]

            # --- his answer does not decay: with the horizon forced past, it still resolves
            import cairn.devices.librarian.loop as L
            from datetime import timedelta
            horizon, L.DECAY_HORIZON = L.DECAY_HORIZON, timedelta(seconds=-1)
            try:
                # the Hex answer: nothing has walked to it yet, so no attestation exempts it
                r = ASK.ask(PARA_HEX, resolve=seam, **kw)
            finally:
                L.DECAY_HORIZON = horizon
            traces.append(r.get("trace") or {})
            check("an answer past the decay horizon still resolves — his words are not a hypothesis",
                  r.get("outcome") == "resolved" and r.get("qid") == "open-000000000a02"
                  and len(seam.calls["generate"]) == gen0,
                  f"outcome={r.get('outcome')} generate={len(seam.calls['generate']) - gen0}")

            # --- an uncovered question, without a ticket: nothing opened, command handed back
            n_before = len(list(qdir.glob("open-*.json")))
            r = ASK.ask(UNCOVERED, resolve=seam, **kw)
            traces.append(r.get("trace") or {})
            check("an uncovered question escalates",
                  r.get("outcome") == "escalated", f"outcome={r.get('outcome')}")
            check("with no ticket it opens nothing and hands back the operator command",
                  r.get("opened") is None
                  and len(list(qdir.glob("open-*.json"))) == n_before
                  and shlex.split(r.get("operator_command") or "x")[:4]
                  == ["cairn", "question", "operator", UNCOVERED],
                  f"opened={r.get('opened')} cmd={r.get('operator_command')!r}")

            # --- with a ticket: exactly one record, through the door, test-marked ----
            r = ASK.ask(UNCOVERED, resolve=seam, ticket=TID, why="the proof's uncovered question", **kw)
            traces.append(r.get("trace") or {})
            opened = r.get("opened")
            after = sorted(p.stem for p in qdir.glob("open-*.json"))
            check("with a ticket it opens exactly one question record",
                  bool(opened) and len(after) == n_before + 1 and opened in after,
                  f"opened={opened} records {n_before}->{len(after)}")
            rec = json.loads((qdir / f"{opened}.json").read_text()) if opened and (qdir / f"{opened}.json").exists() else {}
            check("the opened record names librarian ask and carries the testing mark",
                  "librarian ask" in str(rec.get("source")) and MARK in str(rec.get("source")),
                  f"source={rec.get('source')!r}")

            # --- the loop closes ---------------------------------------------------
            if opened:
                Q.answer(opened, A_SHED, spawned=[], root=qdir)
            r = ASK.ask(UNCOVERED_AGAIN, resolve=seam, **kw)
            traces.append(r.get("trace") or {})
            check("once answered, an equivalent re-ask resolves to that record without reaching him",
                  r.get("outcome") == "resolved" and r.get("qid") == opened and r.get("answer") == A_SHED,
                  f"outcome={r.get('outcome')} qid={r.get('qid')} answer={r.get('answer')!r}")

            # --- an LLM mint never wins, even on a later crossing where it counts ------
            r1 = ASK.ask(MINTQ, resolve=seam, **kw)
            r2 = ASK.ask(MINTQ, resolve=seam, **kw)
            traces += [r1.get("trace") or {}, r2.get("trace") or {}]
            walked_mint = any(n.get("content") == MINT and n.get("evidence")
                              for n in (r2.get("walk") or []))
            check("the mint is standing evidence on the second crossing (the tooth has teeth)",
                  walked_mint, "the mint must clear the walk for the kill to mean anything")
            check("an LLM-minted node above the floor never wins",
                  r1.get("outcome") == "escalated" and r2.get("outcome") == "escalated"
                  and MINT not in (r1.get("answer"), r2.get("answer")),
                  f"outcomes={r1.get('outcome')},{r2.get('outcome')}")

            # --- a refuted answer never wins -----------------------------------------
            dev.deposit(REFUTER, FAR, {"source": MARK, "testing": MARK}, tree="answers", table=table)
            hex_node = node_id_for(ASK.node_content(Q_HEX, A_HEX))
            refute(hex_node, node_id_for(REFUTER), "proof: retire the Hex answer", table=table)
            r = ASK.ask(PARA_HEX, resolve=seam, **kw)
            traces.append(r.get("trace") or {})
            check("a refuted answer never wins",
                  r.get("outcome") == "escalated" and r.get("answer") != A_HEX,
                  f"outcome={r.get('outcome')} answer={r.get('answer')!r}")

            # --- every run is a state log ------------------------------------------
            bad = [(i, answers_five_questions(t)) for i, t in enumerate(traces)
                   if not t or answers_five_questions(t)]
            check("every ask's trace answers the block's five questions",
                  not bad and len(traces) == 8, f"{len(traces)} traces, failing: {bad}")

            # --- the testing mark on every node this proof folded ---------------------
            nids = sorted({row["node_id"] for row in store.read(table)})
            rows = store.read(NODES_TABLE, where="node_id = ANY(%s)", params=(nids,)) if nids else []
            folded = [x for x in rows if str((x["provenance"] or {}).get("source", "")).startswith("question:")]
            unmarked = [x["node_id"] for x in folded if (x["provenance"] or {}).get("testing") != MARK]
            check("every node the proof folded carries the testing mark",
                  len(folded) >= 3 and not unmarked, f"folded={len(folded)} unmarked={unmarked}")
        finally:
            A.set_diagnostic_roots(None)
            forget_leaf(table)


def test_the_verbs_resolve() -> None:
    r = subprocess.run(["cairn", "librarian", "ask", "--help"], capture_output=True, text=True,
                       timeout=60, cwd=REPO)
    check("`cairn librarian ask --help` answers", r.returncode == 0 and "--ticket" in r.stdout,
          f"exit={r.returncode} {(r.stdout + r.stderr)[-300:]!r}")
    with tempfile.TemporaryDirectory(prefix="proof-librarian-ask-cli-") as td:
        commons = Path(td) / "CairnCommons"
        (commons / "questions").mkdir(parents=True)
        (commons / "tickets").mkdir()
        env = dict(os.environ, PYTHONPATH=str(REPO), CAIRN_QUESTIONS_DIR=str(commons / "questions"),
                   CAIRN_ARTIFACT_ROOTS=json.dumps({"CairnCommons": str(commons),
                                                    "cairn": str(Path(td) / "cairn")}))
        r = subprocess.run([sys.executable, "-m", "cairn.tools.question", "operator",
                            "Is this the proof's operator question?", "--ticket", TID,
                            "--why", f"testing: {MARK}"],
                           capture_output=True, text=True, timeout=60, cwd=REPO, env=env)
        recs = [json.loads(p.read_text()) for p in (commons / "questions").glob("open-*.json")]
        check("`cairn question operator` opens one record stamped librarian ask",
              r.returncode == 0 and len(recs) == 1 and "librarian ask" in str(recs[0].get("source")),
              f"exit={r.returncode} records={len(recs)} {(r.stdout + r.stderr)[-300:]!r}")


def main() -> int:
    for fn in (test_the_librarian_answers_before_akien_is_asked, test_the_verbs_resolve):
        print(fn.__name__)
        try:
            fn()
        except Exception as e:  # a tooth that cannot run is a red, loud (Law 7)
            check(f"{fn.__name__} ran", False, f"{type(e).__name__}: {e}")
            traceback.print_exc()
    print(f"\n{'RED' if FAILURES else 'GREEN'} — {len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

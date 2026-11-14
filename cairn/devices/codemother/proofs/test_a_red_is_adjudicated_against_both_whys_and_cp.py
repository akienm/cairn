"""A red ticket is adjudicated against both whys and CP1-CP6 (ticket aa2d42b15886).

Outline 17.11.6 and 9.4.2.3.7: a red proof means the CODE is wrong or the TOOTH is wrong, with
no third outcome, and a tooth change needs a decision behind it. Measured 2026-11-13: nothing
in the system reached that verdict. A red ticket was cast and stood until a mind read it by
hand, and CodeMother answered no `adjudicate` verb.

Teeth a hollow build could not pass. Everything is scratch: a scratch repo holding one proof
and one charter, a scratch commons holding core-values.md, a scratch question root, a fixture
ticket id that no live ticket carries, and a stub inference device wired onto a scratch bus
(the cairn device's published scratch_bus) that answers `infer` with a canned text.
  1. adjudicate on a red ticket opens ONE question bound to the ticket and answers it with
     exactly one of code-wrong | tooth-wrong, every reason naming a why or a CP; CodeMother
     declares the `adjudicate` verb.
  2. An inference answer that is neither outcome is refused loudly, and no question is
     written.
  3. The answered question reads back resolved and bound to the ticket, which is the predicate
     the reseal door's rung 4 reads (a resolved `open-` question lifts it). The tester's
     reseal is not imported here: codemother may not import cairn.devices.tester (RULE 1).

    bin/cairn test cairn/devices/codemother/proofs/test_a_red_is_adjudicated_against_both_whys_and_cp.py
"""
from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"aa2d42b15886": {
    "1": "test_adjudicate_opens_one_bound_question_answered_with_one_outcome",
    "2": "test_a_third_outcome_is_refused_and_nothing_is_written",
    "3": "test_the_answered_question_reads_resolved_and_bound",
}}

_TID = "fa1e0adj0d2d"          # a fixture ticket id; no live ticket carries it
_PROOF_REL = "cairn/tools/fixture_widget/proofs/test_the_widget_counts.py"
_CHARTER_REL = "cairn/tools/fixture_widget/intention+why.json"
_GOOD = json.dumps({"verdict": "tooth-wrong", "reasons": [
    "the tooth's why says it counts widgets, and it now counts bytes",
    "CP1: the red names a measurement the component's why never promised"]})
_SCRATCH = contextlib.ExitStack()
_LAST: dict = {}


def _world(answer: str) -> dict:
    """A scratch repo, commons and question root, and a bus whose `inference` answers ``answer``."""
    from cairn.tools.scratch.scratch import scratch_dir
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import scratch_bus

    d = scratch_dir("adjudicate_aa2d")
    repo, commons, qroot = d / "repo", d / "commons", d / "questions"
    (repo / _PROOF_REL).parent.mkdir(parents=True)
    (repo / _PROOF_REL).write_text(
        '"""The widget counts widgets: one tooth, the count of three widgets is three."""\n'
        'PROVES = {"%s": {"1": "test_three"}}\n\n'
        "def test_three():\n    assert len(b'abc') == 3\n" % _TID, encoding="utf-8")
    (repo / _CHARTER_REL).write_text(json.dumps({"why": "a widget count tells the operator how many widgets stand"}),
                                     encoding="utf-8")
    (commons / "intentions-not-beside-code").mkdir(parents=True)
    (commons / "intentions-not-beside-code" / "core-values.md").write_text(
        "CP1 truth over coherence. CP2 kill is a win. CP3 force the why. CP4 serve us. "
        "CP5 cheapest first. CP6 the world is not safe.\n", encoding="utf-8")
    qroot.mkdir()
    bus = _SCRATCH.enter_context(scratch_bus("adjudicate_aa2d"))
    asked: list[dict] = []

    def _inference(env: dict):
        if env.get("verb") != "infer" or env.get("reply_to"):
            return None
        asked.append(env)
        bus.post(sender="inference", to=env["sender"], channel=env.get("channel", "personal"),
                 why="stub inference answer (proof aa2d42b15886)", verb="infer",
                 body={"outcome": "ok", "answer": {"text": answer}}, reply_to=env["id"])

    bus.wire_delivery("inference", _inference)
    ticket = {"id": _TID, "fixes": [_PROOF_REL], "owning_intention": _CHARTER_REL,
              "measured": [{"when": "2026-11-13", "saw": f"{_PROOF_REL} ran red",
                            "how": "the tester's run, record (none); keys 1"}]}
    return {"repo": repo, "commons": commons, "qroot": qroot, "bus": bus, "asked": asked, "ticket": ticket}


def _adjudicate(w: dict) -> dict:
    from cairn.devices.codemother import adjudicate as adj
    return adj.adjudicate(w["ticket"], ask=lambda text: adj.ask_inference(w["bus"], text),
                          repo=w["repo"], commons=w["commons"], question_root=w["qroot"])


def _question_files(qroot: Path) -> list[Path]:
    return sorted(p for p in qroot.rglob("*.json"))


def test_adjudicate_opens_one_bound_question_answered_with_one_outcome():
    from cairn.devices.codemother.shim import CodeMotherDevice
    from cairn.tools.question import question as q

    assert "adjudicate" in CodeMotherDevice().declared_verbs(), "codemother declares no adjudicate verb"
    w = _world(_GOOD)
    out = _adjudicate(w)
    assert len(w["asked"]) == 1, f"inference was asked {len(w['asked'])} times over the bus"
    prompt = w["asked"][0]["body"]["prompt"]
    for piece in ("a widget count tells the operator", "counts widgets", "CP6"):
        assert piece in prompt, f"the reader was not given {piece!r}"
    files = _question_files(w["qroot"])
    assert len(files) == 1, f"expected one question, found {[p.name for p in files]}"
    doc = q.read(out["question"], root=w["qroot"])
    assert doc.get("ticket") == _TID, f"the question is not bound to the ticket: {doc.get('ticket')!r}"
    words = doc.get("answer") if isinstance(doc.get("answer"), str) else json.dumps(doc.get("answer"))
    hits = [o for o in ("code-wrong", "tooth-wrong") if o in words]
    assert hits == ["tooth-wrong"], f"the answer carries {hits}, not exactly one outcome: {words!r}"
    assert out["verdict"] == "tooth-wrong" and len(out["reasons"]) == 2, out
    _LAST.update(question=out["question"], qroot=w["qroot"])
    print("ok test_adjudicate_opens_one_bound_question_answered_with_one_outcome")


def test_a_third_outcome_is_refused_and_nothing_is_written():
    from cairn.devices.codemother import adjudicate as adj

    for text in ('{"verdict": "maybe", "reasons": ["CP1: unsure"]}',
                 '{"verdict": "code-wrong", "reasons": ["it feels wrong"]}',
                 "I think the code is wrong."):
        w = _world(text)
        try:
            _adjudicate(w)
        except adj.AdjudicationRefused as exc:
            assert str(exc), "the refusal names nothing"
        else:
            raise AssertionError(f"an unreadable verdict was accepted: {text!r}")
        assert len(w["asked"]) == 1, "the reader was not asked"
        assert _question_files(w["qroot"]) == [], f"a refused verdict wrote a question: {text!r}"
    print("ok test_a_third_outcome_is_refused_and_nothing_is_written")


def test_the_answered_question_reads_resolved_and_bound():
    from cairn.tools.question import question as q

    if not _LAST:
        test_adjudicate_opens_one_bound_question_answered_with_one_outcome()
    qid = _LAST["question"]
    assert qid.startswith("open-"), f"rung 4 lifts on an open- question id, got {qid!r}"
    doc = q.read(qid, root=_LAST["qroot"])
    assert doc.get("resolved") is True, f"the answered question does not read resolved: {doc}"
    assert doc.get("ticket") == _TID, doc.get("ticket")
    print("ok test_the_answered_question_reads_resolved_and_bound")


if __name__ == "__main__":
    try:
        test_adjudicate_opens_one_bound_question_answered_with_one_outcome()
        test_a_third_outcome_is_refused_and_nothing_is_written()
        test_the_answered_question_reads_resolved_and_bound()
    finally:
        _SCRATCH.close()

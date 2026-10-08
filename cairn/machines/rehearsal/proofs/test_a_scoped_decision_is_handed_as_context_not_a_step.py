"""Proof for ticket eb05adbe0a0f — a scoped decision is handed to the reader as context, not a step.

Measured 2026-10-08: 41202d4c8d3b ran 12 passes with gaps 2 -> 6 -> 8 as prose scope lines were
added, and b4d39f3610f3 read D6/D7 gaps while its reader's own would_settle said 'This ticket's
build scope ends at D5 (per D9)'. A line saying 'D6 is out of scope' is one more decision the
reader must judge; scope() is the door that marks it instead.

Every tooth runs over its own SCRATCH commons holding one ticket (testing-marked, removed at
exit); none reads the live corpus or calls a reader.

  1. A SCOPED DECISION IS CONTEXT, NOT A STEP. After scope(t, [2]) the reader_view of the
     ticket carries no decision with n 2 and a top-level 'context' list whose one entry's text
     begins 'D2'; the file keeps D2's text with context.by/at/because. An empty because refuses
     and writes nothing.
  2. THE VOCABULARY OMITS IT. decision_ids_of the scoped ticket omits 2, so validate passes a
     reading that names every other decision and not D2, and refuses one that names D2.
  3. THE CLI NEEDS A REASON. cairn rehearse --scope without --because exits non-zero and never
     reaches scope(); with --because it exits 0 and reaches scope() once with D2.

    bin/cairn test cairn/machines/rehearsal/proofs/test_a_scoped_decision_is_handed_as_context_not_a_step.py
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"eb05adbe0a0f": {"1": "a_scoped_decision_is_context_not_a_step",
                           "2": "the_vocabulary_omits_a_scoped_decision",
                           "3": "the_cli_scope_needs_a_reason"}}

TID = "eb05f00dfeed"
STEM = f"{TID}-testing-eb05adbe0a0f-scoped-decision-is-context"
VOYAGE = "the voyage pushes both repos before PROVED"


def _ticket(decisions):
    return {"id": TID, "title": "testing-eb05adbe0a0f-scoped-decision-is-context",
            "intention": "testing: a fixture ticket for the eb05adbe0a0f proof",
            "decisions": decisions}


BASE = [
    {"n": 1, "text": "add def f to the module", "by": "cc"},
    {"n": 2, "text": VOYAGE, "by": "cc"},
    {"n": 3, "text": "add def g beside f", "by": "cc"},
]

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


class World:
    def __init__(self, decisions):
        from cairn.tools.scratch.scratch import scratch_dir
        self.dir = Path(scratch_dir("testing-eb05adbe0a0f-scoped-"))
        self.commons = self.dir / "CairnCommons"
        (self.commons / "tickets").mkdir(parents=True)
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.ticket.write_text(json.dumps(_ticket(decisions), indent=2) + "\n", encoding="utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def doc(self):
        return json.loads(self.ticket.read_text(encoding="utf-8"))


def _node(step):
    return {"step": step, "state": "builds_as_written", "assumption": "", "would_settle": "",
            "confidence": 0.9}


def a_scoped_decision_is_context_not_a_step():
    from cairn.machines.rehearsal import rehearsal as R
    with World(BASE) as w:
        before = w.ticket.read_bytes()
        try:
            R.scope(TID, [2], by="cc", because="", root=w.commons)
        except R.Refused:
            pass
        else:
            raise AssertionError("scope with an empty because did not refuse")
        assert w.ticket.read_bytes() == before, "a refused scope wrote the ticket"
        R.scope(TID, [2], by="cc", because="describes the voyage, not the build", root=w.commons)
        view = json.loads(R.reader_view(w.ticket.read_bytes()))
        ns = [d.get("n") for d in view.get("decisions") or []]
        assert 2 not in ns and ns == [1, 3], f"the scoped line is still handed as a step: {ns}"
        ctx = view.get("context")
        assert isinstance(ctx, list) and len(ctx) == 1, f"no one-entry top-level context list: {ctx!r}"
        assert str(ctx[0].get("text", "")).startswith("D2"), f"the context entry is not labeled D2: {ctx[0]}"
        assert VOYAGE in ctx[0]["text"], f"the context entry lost D2's words: {ctx[0]}"
        d2 = {d["n"]: d for d in w.doc()["decisions"]}[2]
        assert d2["text"] == VOYAGE, "the file lost D2's text"
        c = d2.get("context")
        assert isinstance(c, dict) and c.get("by") == "cc" and c.get("at") and c.get("because"), \
            f"D2 lacks its context stamp: {c}"


def the_vocabulary_omits_a_scoped_decision():
    from cairn.machines.rehearsal import rehearsal as R
    with World(BASE) as w:
        R.scope(TID, [2], by="cc", because="describes the voyage, not the build", root=w.commons)
        ids = R.decision_ids_of(w.doc())
        assert ids == {1, 3}, f"the vocabulary still owes the scoped id: {ids}"
        skips = {"nodes": [_node("D1"), _node("D3")]}
        assert R.validate(skips, ids) == [], f"a reading that skips D2 was refused: {R.validate(skips, ids)}"
        names = {"nodes": [_node("D1"), _node("D2"), _node("D3")]}
        lacks = R.validate(names, ids)
        assert any("D2" in x for x in lacks), f"a reading naming D2 as a step passed: {lacks}"


def the_cli_scope_needs_a_reason():
    from cairn.machines.rehearsal import rehearsal as R
    from cairn.machines.rehearsal.__main__ import main
    calls = []

    def stub(ticket, ns, *, by, because, root=None):
        calls.append((ticket, list(ns), by, because))
        return [{"n": n, "text": f"D{n} {VOYAGE}", "context": {"by": by, "because": because}} for n in ns]

    real = getattr(R, "scope", None)
    R.scope = stub
    try:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = main([TID, "--scope", "D2", "--by", "cc"])
            except SystemExit as exc:
                rc = exc.code
        assert rc not in (0, None), f"--scope without --because exited {rc!r}"
        assert calls == [], f"--scope without --because reached scope(): {calls}"
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = main([TID, "--scope", "D2", "--by", "cc", "--because", "describes the voyage"])
            except SystemExit as exc:
                rc = exc.code
        assert rc == 0, f"--scope with --because exited {rc!r}: {err.getvalue().strip()}"
        assert calls == [(TID, [2], "cc", "describes the voyage")], f"scope() was not reached once with D2: {calls}"
    finally:
        if real is None:
            del R.scope
        else:
            R.scope = real


TEETH = [a_scoped_decision_is_context_not_a_step, the_vocabulary_omits_a_scoped_decision,
         the_cli_scope_needs_a_reason]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

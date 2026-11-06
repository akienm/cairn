#!/usr/bin/env python3
"""Proof that a decide line on a shaped plan carries writes_to and reads (ticket 70f91244f3c0).

Measured 2026-11-05: rehearsal.decide writes an entry {n, text, by, step, source, at} with no
paths, and `cairn rehearse` takes --decide STEP LINE and --by only. The parent e4f02a1ceef5
makes a ticket's plan JSON at the cast door (Akien: "should be json"); the amendment entrance
must not become the prose leak the cast door closed.

  (1) on a scratch ticket with a clauses falsifier, decide without paths is refused (and with
      one list but not the other, refused naming the missing one) and the ticket bytes are
      unchanged;
  (2) with --writes-to and --reads (or --no-writes / --no-reads for an explicit empty) the
      line lands carrying both lists;
  (3) on a scratch ticket with a string falsifier, decide without paths lands as at HEAD:
      the keys {n, text, by, step, source, at}, no writes_to, no reads.

Every ticket lives in a scratch commons (testing-marked, removed at exit); the CLI is pointed
at it through CAIRN_ARTIFACT_ROOTS, the door's own seam. Nothing reads the live corpus.

    PYTHONPATH=. python3 cairn/machines/rehearsal/proofs/test_a_decide_line_on_a_shaped_plan_carries_its_paths.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

PROVES = {"70f91244f3c0": {
    "1": "test_clause_1_a_pathless_line_on_a_shaped_plan_is_refused",
    "2": "test_clause_2_the_cli_lands_a_line_carrying_both_lists",
    "3": "test_clause_3_a_string_falsifier_lands_as_at_head",
}}

FAILURES: list[str] = []

TID = "70f9f00dfeed"
STEM = f"{TID}-testing-70f91244f3c0-decide-carries-paths"
CLAUSES = {"clauses": [{"n": 1, "claim": "a"}, {"n": 2, "claim": "b"}]}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


class World:
    def __init__(self, falsifier):
        from cairn.tools.scratch.scratch import scratch_dir
        self.dir = Path(scratch_dir("testing-70f91244f3c0-decide-paths-"))
        self.commons = self.dir / "CairnCommons"
        tickets = self.commons / "tickets"
        tickets.mkdir(parents=True)
        # ticket_log reads the declared log kinds beside the plan; a hollow worktree has no
        # live commons beside it to fall back on
        (tickets / "_charter+why.json").write_text(json.dumps({
            "plan_fields": ["id", "title", "intention", "falsifier", "decisions"],
            "log_kinds": {"field": {}, "phase_write": {}, "rehearsal": {}, "decision_retired": {}}}) + "\n")
        self.ticket = tickets / f"{STEM}.json"
        self.ticket.write_text(json.dumps({
            "id": TID, "title": "testing-70f91244f3c0-decide-carries-paths",
            "intention": "testing: a fixture ticket for the 70f91244f3c0 proof",
            "falsifier": falsifier,
            "decisions": [{"n": 1, "text": "build it", "by": "cc",
                           "writes_to": ["x.py"], "reads": ["x.py"]}]}, indent=2) + "\n",
            encoding="utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def doc(self):
        return json.loads(self.ticket.read_text(encoding="utf-8"))

    def cli(self, *argv) -> tuple[int, str]:
        """`cairn rehearse` in-process, the door pointed at this scratch commons."""
        from cairn.machines.rehearsal.__main__ import main
        old = os.environ.get("CAIRN_ARTIFACT_ROOTS")
        os.environ["CAIRN_ARTIFACT_ROOTS"] = json.dumps({"cairn": str(_REPO), "CairnCommons": str(self.commons)})
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                try:
                    rc = main([TID, *argv])
                except SystemExit as e:
                    rc = e.code if isinstance(e.code, int) else 2
        finally:
            if old is None:
                os.environ.pop("CAIRN_ARTIFACT_ROOTS", None)
            else:
                os.environ["CAIRN_ARTIFACT_ROOTS"] = old
        return rc, out.getvalue()


def test_clause_1_a_pathless_line_on_a_shaped_plan_is_refused() -> None:
    from cairn.machines.rehearsal import rehearsal as R
    bad = []
    with World(CLAUSES) as w:
        before = w.ticket.read_bytes()
        for label, kw, names in (("no paths", {}, ("writes_to", "reads")),
                                 ("writes_to only", {"writes_to": ["y.py"]}, ("reads",)),
                                 ("reads only", {"reads": ["y.py"]}, ("writes_to",)),
                                 ("an in-place rewrite of D1", {"step": "D1"}, ("writes_to", "reads"))):
            step = kw.pop("step", "unlisted: polish")
            try:
                entry = R.decide(TID, step, "polish it", by="cc", root=w.commons, **kw)
                bad.append(f"{label}: landed {entry}")
            except R.Refused as e:
                if not all(n in str(e) for n in names):
                    bad.append(f"{label}: refusal names not {names}: {e}")
            if w.ticket.read_bytes() != before:
                bad.append(f"{label}: the ticket bytes changed")
                before = w.ticket.read_bytes()
        rc, out = w.cli("--decide", "unlisted: polish", "polish it", "--by", "cc")
        if rc == 0 or w.ticket.read_bytes() != before:
            bad.append(f"the CLI without paths: rc {rc}, bytes changed {w.ticket.read_bytes() != before}: {out[-200:]}")
    check("test_clause_1_a_pathless_line_on_a_shaped_plan_is_refused", not bad,
          "each pathless line refused, bytes unchanged" + (f"; failing {bad}" if bad else ""))


def test_clause_2_the_cli_lands_a_line_carrying_both_lists() -> None:
    bad = []
    with World(CLAUSES) as w:
        rc, out = w.cli("--decide", "unlisted: polish", "polish it", "--by", "cc",
                        "--writes-to", "a.py", "--writes-to", "b.py", "--reads", "c.py")
        new = [d for d in w.doc()["decisions"] if d.get("text") == "polish it"]
        if rc != 0 or len(new) != 1 or new[0].get("writes_to") != ["a.py", "b.py"] or new[0].get("reads") != ["c.py"]:
            bad.append(f"--writes-to/--reads: rc {rc}, lines {new}: {out[-200:]}")
        rc, out = w.cli("--decide", "unlisted: run it", "run it", "--by", "cc", "--no-writes", "--reads", "c.py")
        new = [d for d in w.doc()["decisions"] if d.get("text") == "run it"]
        if rc != 0 or len(new) != 1 or new[0].get("writes_to") != [] or new[0].get("reads") != ["c.py"]:
            bad.append(f"--no-writes: rc {rc}, lines {new}: {out[-200:]}")
        rc, out = w.cli("--decide", "D1", "build it better", "--by", "cc", "--writes-to", "z.py", "--no-reads")
        d1 = [d for d in w.doc()["decisions"] if d.get("n") == 1]
        if rc != 0 or not d1 or d1[0].get("text") != "build it better" or d1[0].get("writes_to") != ["z.py"] \
                or d1[0].get("reads") != []:
            bad.append(f"D1 rewritten: rc {rc}, line {d1}: {out[-200:]}")
    check("test_clause_2_the_cli_lands_a_line_carrying_both_lists", not bad,
          "new, explicit-empty and rewritten lines carry both lists" + (f"; failing {bad}" if bad else ""))


def test_clause_3_a_string_falsifier_lands_as_at_head() -> None:
    from cairn.machines.rehearsal import rehearsal as R
    with World("(1) a (2) b") as w:
        entry = R.decide(TID, "unlisted: polish", "polish it", by="cc", root=w.commons)
        on_disk = [d for d in w.doc()["decisions"] if d.get("text") == "polish it"]
        ok = (set(entry) == {"n", "text", "by", "step", "source", "at"}
              and len(on_disk) == 1 and set(on_disk[0]) == set(entry))
    check("test_clause_3_a_string_falsifier_lands_as_at_head", ok, f"entry keys {sorted(entry)}")


def main() -> int:
    for fn in (test_clause_1_a_pathless_line_on_a_shaped_plan_is_refused,
               test_clause_2_the_cli_lands_a_line_carrying_both_lists,
               test_clause_3_a_string_falsifier_lands_as_at_head):
        try:
            fn()
        except Exception as e:  # a crash in a tooth is a red for that tooth
            check(fn.__name__, False, f"{type(e).__name__}: {e}")
    print(f"{'FAIL' if FAILURES else 'PASS'}: {len(FAILURES)} failing")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

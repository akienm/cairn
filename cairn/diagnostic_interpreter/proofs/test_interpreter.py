"""Proof for diagnostic_interpreter — the complete first-pass report + the learning-loop.

Instantiates I-complete-diagnostic-on-first-pass. Teeth a hollow interpreter could not pass:

  THE REPORT
  - GATHERS ONE POINTER'S TRANSACTION, ORDERED. Real DiagnosticBase emissions for pointer A
    (across gates, out of insertion order) plus noise for pointer B land in a Mailbox;
    assemble(A) returns exactly A's records, ordered by the 6th-decimal stamp, carrying every
    emitted value — and B never bleeds in (Law 6, owned data stays home).
  - READS, NEVER MUTATES. The slice is a copy; the source records are untouched.

  THE LEARNING-LOOP (the special-class falsifier)
  - A FIRST MISS IS LEARNED AND FOLDED FORWARD. record_miss → "learned"; the next report for
    that gate now REQUIRES the datum (Law 1 — the answered question became structure).
  - A LEARNED GAP THAT RECURS IS LOUD. A report for a gate missing an already-learned key is
    complete=False with the key named in `recurrences` — the terminal falsifier, never silent
    (Law 7).
  - A COMPLETE REPORT IS CLEAN. Carry every learned-required key → complete=True, no recurrences.
  - THE SIGNAL IS DISTINGUISHED FROM THE RE-DERIVATION. record_miss on an already-learned
    key → "recurred", not "learned".
  - LEARNED COMPLETENESS PERSISTS. save→load round-trips the registry (the loop's memory survives).

Pure over stdlib (+ DiagnosticBase, stdlib-only). No DB, no network.

    python3 cairn/diagnostic_interpreter/proofs/test_interpreter.py     # exit 0 = green
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.diagnostic import DiagnosticBase
from cairn.diagnostic_interpreter import CompletenessRegistry, Mailbox, assemble


class _Dev(DiagnosticBase):
    """A minimal device that carries the emit mechanism — the real breadcrumb source."""


def _t(us: int):
    """A UTC instant at a chosen microsecond — lets the proof control (and scramble) order."""
    return datetime(2026, 7, 23, 12, 0, 0, us, tzinfo=timezone.utc)


def test_the_report_gathers_one_pointers_transaction_ordered_and_isolated():
    box = Mailbox()
    dev = _Dev()
    dev.set_diagnostic_receiver(box)

    # Pointer A emits across three gates, OUT of chronological order (stamps 300, 100, 200).
    dev.emit("verify", pointer="ticket/A", values={"expected": "2", "actual": "123"}, now=_t(300))
    dev.emit("enter", pointer="ticket/A", values={"arg": "x"}, now=_t(100))
    dev.emit("branch", pointer="ticket/A", values={"took": "left"}, now=_t(200))
    # Pointer B is unrelated noise that must NOT bleed into A's report.
    dev.emit("enter", pointer="ticket/B", values={"other": "y"}, now=_t(150))

    report = assemble(box.records(), "ticket/A")

    assert report["pointer"] == "ticket/A"
    assert report["gates"] == ["enter", "branch", "verify"], "ordered by the 6th-decimal stamp"
    assert len(report["steps"]) == 3, "exactly A's records — B did not bleed in (Law 6)"
    assert all(s["pointer"] == "ticket/A" for s in report["steps"])
    # every emitted value is carried — a resolver reading only the slice has what it needs
    assert report["steps"][2]["values"] == {"expected": "2", "actual": "123"}


def test_the_interpreter_reads_it_does_not_mutate():
    box = Mailbox()
    dev = _Dev()
    dev.set_diagnostic_receiver(box)
    dev.emit("enter", pointer="ticket/A", values={"arg": "x"}, now=_t(100))
    before = box.records()
    snapshot = before[0]["values"].copy()

    report = assemble(before, "ticket/A")
    report["steps"][0]["values"]["arg"] = "MUTATED"

    assert box.records()[0]["values"] == snapshot, "the slice is a copy; the source is untouched"


def test_a_first_miss_is_learned_and_folded_forward():
    reg = CompletenessRegistry()
    # The resolver hit a gap: the "verify" report should have carried "actual". Fold it in.
    assert reg.record_miss("verify", "actual") == "learned", "first miss is a feed-forward signal"
    assert reg.required("verify") == {"actual"}

    # The NEXT report for a "verify" that lacks "actual" now knows it is required (Law 1).
    records = [{"pointer": "ticket/Z", "gate": "verify", "values": {"expected": "2"},
                "ts": _t(1).isoformat(), "us": "000001"}]
    report = assemble(records, "ticket/Z", registry=reg)
    assert report["completeness"]["per_gate"]["verify"]["required"] == ["actual"]


def test_a_learned_gap_that_recurs_is_loud():
    reg = CompletenessRegistry({"verify": ["actual"]})   # "actual" already learned
    records = [{"pointer": "ticket/Z", "gate": "verify", "values": {"expected": "2"},
                "ts": _t(1).isoformat(), "us": "000001"}]   # ...but the report lacks it → recurrence

    report = assemble(records, "ticket/Z", registry=reg)
    comp = report["completeness"]
    assert comp["complete"] is False, "a learned gap that recurs makes the report incomplete"
    assert {"gate": "verify", "key": "actual"} in comp["recurrences"], "and it is named LOUD (Law 7)"


def test_a_complete_report_is_clean():
    reg = CompletenessRegistry({"verify": ["actual", "expected"]})
    records = [{"pointer": "ticket/Z", "gate": "verify",
                "values": {"expected": "2", "actual": "123"},
                "ts": _t(1).isoformat(), "us": "000001"}]

    report = assemble(records, "ticket/Z", registry=reg)
    assert report["completeness"]["complete"] is True
    assert report["completeness"]["recurrences"] == []


def test_the_signal_is_distinguished_from_the_re_derivation():
    reg = CompletenessRegistry()
    assert reg.record_miss("verify", "actual") == "learned", "first time — a learning signal"
    assert reg.record_miss("verify", "actual") == "recurred", "second time — the re-derivation"


def test_learned_completeness_persists():
    reg = CompletenessRegistry()
    reg.record_miss("verify", "actual")
    reg.record_miss("branch", "took")
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "completeness.json"
        reg.save(path)
        back = CompletenessRegistry.load(path)
    assert back.required("verify") == {"actual"}
    assert back.required("branch") == {"took"}
    # a missing file is an empty registry, not an error (the loop starts blank and grows)
    assert CompletenessRegistry.load(Path("/nonexistent/nowhere.json")).required("verify") == set()


def _main() -> int:
    checks = [
        test_the_report_gathers_one_pointers_transaction_ordered_and_isolated,
        test_the_interpreter_reads_it_does_not_mutate,
        test_a_first_miss_is_learned_and_folded_forward,
        test_a_learned_gap_that_recurs_is_loud,
        test_a_complete_report_is_clean,
        test_the_signal_is_distinguished_from_the_re_derivation,
        test_learned_completeness_persists,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — diagnostic_interpreter: assembles one pointer's transaction into an ordered, "
          "isolated first-pass report, and the learning-loop folds a first miss forward (Law 1) "
          "while surfacing an already-learned recurrence LOUD (Law 7) — the special-class falsifier.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

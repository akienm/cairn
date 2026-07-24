"""Proof for diagnostic_inspector — filters a log into findings, and gets better over time.

THE REMIT under test (charter): the inspector saves CC tokens exploring an issue — a
resolver reading only the findings needs NO second exploration — and it gets better over
time (a learned gap never costs a second exploration again). Teeth a hollow inspector could
not pass:

  THE FINDINGS (the token-saving slice)
  - FILTER ONE ITEM'S TRANSACTION, ORDERED, ISOLATED. Real DiagnosticBase emissions for
    pointer A (across gates, out of order) plus noise for pointer B land in a log;
    inspect(log, by_pointer(A)) returns exactly A's records, ordered by the 6th-decimal
    stamp, carrying every emitted value — B never bleeds in (Law 6). A resolver reading only
    this has what it needs (no second crawl — the tokens saved).
  - FILTERS COMPOSE (the plural). by_pointer(A) AND by_gate("verify") narrows to A's verify
    contacts only — the conjunction, so 'filters' is not a single hardcoded pointer-match.
  - READS, NEVER MUTATES. The slice is a deep copy; the source records are untouched.

  GETS BETTER OVER TIME (the learning-loop, carried BY the inspector)
  - A FIRST MISS IS LEARNED AND FOLDED FORWARD. inspector.record_miss → "learned"; the
    inspector's NEXT findings for that gate now REQUIRE the datum (Law 1 — the answered
    question became structure). Proven on the Inspector, not a loose registry: the inspector
    is what gets better.
  - A LEARNED GAP THAT RECURS IS LOUD. Findings for a gate missing an already-learned key are
    complete=False with the key named in `recurrences` — the terminal falsifier (the surface
    failed to save the tokens it already learned to save), never silent (Law 7).
  - A COMPLETE FINDINGS IS CLEAN. Carry every learned-required key → complete=True.
  - THE SIGNAL IS DISTINGUISHED FROM THE RE-DERIVATION. record_miss on an already-learned
    key → "recurred", not "learned".
  - LEARNED COMPLETENESS PERSISTS. save→load round-trips the memory (it survives a restart).

Pure over stdlib (+ DiagnosticBase, stdlib-only). No DB, no network.

    python3 cairn/diagnostic_inspector/proofs/test_inspector.py     # exit 0 = green
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
from cairn.diagnostic_inspector import (
    CompletenessRegistry,
    Inspector,
    Mailbox,
    by_gate,
    by_pointer,
)


class _Dev(DiagnosticBase):
    """A minimal device that carries the emit mechanism — the real breadcrumb source."""


def _t(us: int):
    """A UTC instant at a chosen microsecond — lets the proof control (and scramble) order."""
    return datetime(2026, 7, 23, 12, 0, 0, us, tzinfo=timezone.utc)


def test_findings_filter_one_items_transaction_ordered_and_isolated():
    box = Mailbox()
    dev = _Dev()
    dev.set_diagnostic_receiver(box)

    # Pointer A emits across three gates, OUT of chronological order (stamps 300, 100, 200).
    dev.emit("verify", pointer="ticket/A", values={"expected": "2", "actual": "123"}, now=_t(300))
    dev.emit("enter", pointer="ticket/A", values={"arg": "x"}, now=_t(100))
    dev.emit("branch", pointer="ticket/A", values={"took": "left"}, now=_t(200))
    # Pointer B is unrelated noise that must NOT bleed into A's findings.
    dev.emit("enter", pointer="ticket/B", values={"other": "y"}, now=_t(150))

    findings = Inspector().inspect(box.records(), by_pointer("ticket/A"))

    assert findings["scope"] == ["pointer='ticket/A'"], "the findings echo their own filter scope"
    assert findings["gates"] == ["enter", "branch", "verify"], "ordered by the 6th-decimal stamp"
    assert len(findings["steps"]) == 3, "exactly A's records — B did not bleed in (Law 6)"
    assert all(s["pointer"] == "ticket/A" for s in findings["steps"])
    # every emitted value is carried — a resolver reading only the slice has what it needs (the tokens saved)
    assert findings["steps"][2]["values"] == {"expected": "2", "actual": "123"}


def test_filters_compose_pointer_and_gate():
    box = Mailbox()
    dev = _Dev()
    dev.set_diagnostic_receiver(box)
    dev.emit("verify", pointer="ticket/A", values={"actual": "123"}, now=_t(300))
    dev.emit("enter", pointer="ticket/A", values={"arg": "x"}, now=_t(100))
    dev.emit("verify", pointer="ticket/B", values={"actual": "9"}, now=_t(200))   # noise: right gate, wrong item

    findings = Inspector().inspect(box.records(), by_pointer("ticket/A"), by_gate("verify"))

    assert findings["scope"] == ["pointer='ticket/A'", "gate='verify'"]
    assert findings["gates"] == ["verify"], "the conjunction narrowed to A's verify contact only"
    assert len(findings["steps"]) == 1 and findings["steps"][0]["values"] == {"actual": "123"}


def test_the_inspector_reads_it_does_not_mutate():
    box = Mailbox()
    dev = _Dev()
    dev.set_diagnostic_receiver(box)
    dev.emit("enter", pointer="ticket/A", values={"arg": "x"}, now=_t(100))
    before = box.records()
    snapshot = before[0]["values"].copy()

    findings = Inspector().inspect(before, by_pointer("ticket/A"))
    findings["steps"][0]["values"]["arg"] = "MUTATED"

    assert box.records()[0]["values"] == snapshot, "the slice is a copy; the source is untouched"


def test_a_first_miss_is_learned_and_folded_forward():
    insp = Inspector()
    # The resolver hit a gap: the "verify" findings should have carried "actual". Fold it in.
    assert insp.record_miss("verify", "actual") == "learned", "first miss is a feed-forward signal"
    assert insp.registry.required("verify") == {"actual"}

    # The inspector's NEXT findings for a "verify" that lacks "actual" now require it (Law 1).
    records = [{"pointer": "ticket/Z", "gate": "verify", "values": {"expected": "2"},
                "ts": _t(1).isoformat(), "us": "000001"}]
    findings = insp.inspect(records, by_pointer("ticket/Z"))
    assert findings["completeness"]["per_gate"]["verify"]["required"] == ["actual"]


def test_a_learned_gap_that_recurs_is_loud():
    insp = Inspector(CompletenessRegistry({"verify": ["actual"]}))   # "actual" already learned
    records = [{"pointer": "ticket/Z", "gate": "verify", "values": {"expected": "2"},
                "ts": _t(1).isoformat(), "us": "000001"}]   # ...but the findings lack it → recurrence

    comp = insp.inspect(records, by_pointer("ticket/Z"))["completeness"]
    assert comp["complete"] is False, "a learned gap that recurs makes the findings incomplete"
    assert {"gate": "verify", "key": "actual"} in comp["recurrences"], "and it is named LOUD (Law 7)"


def test_a_complete_findings_is_clean():
    insp = Inspector(CompletenessRegistry({"verify": ["actual", "expected"]}))
    records = [{"pointer": "ticket/Z", "gate": "verify",
                "values": {"expected": "2", "actual": "123"},
                "ts": _t(1).isoformat(), "us": "000001"}]

    comp = insp.inspect(records, by_pointer("ticket/Z"))["completeness"]
    assert comp["complete"] is True
    assert comp["recurrences"] == []


def test_the_signal_is_distinguished_from_the_re_derivation():
    insp = Inspector()
    assert insp.record_miss("verify", "actual") == "learned", "first time — a learning signal"
    assert insp.record_miss("verify", "actual") == "recurred", "second time — the re-derivation"


def test_learned_completeness_persists():
    insp = Inspector()
    insp.record_miss("verify", "actual")
    insp.record_miss("branch", "took")
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "completeness.json"
        insp.registry.save(path)
        back = CompletenessRegistry.load(path)
    assert back.required("verify") == {"actual"}
    assert back.required("branch") == {"took"}
    # a missing file is an empty registry, not an error (the loop starts blank and grows)
    assert CompletenessRegistry.load(Path("/nonexistent/nowhere.json")).required("verify") == set()


def _main() -> int:
    checks = [
        test_findings_filter_one_items_transaction_ordered_and_isolated,
        test_filters_compose_pointer_and_gate,
        test_the_inspector_reads_it_does_not_mutate,
        test_a_first_miss_is_learned_and_folded_forward,
        test_a_learned_gap_that_recurs_is_loud,
        test_a_complete_findings_is_clean,
        test_the_signal_is_distinguished_from_the_re_derivation,
        test_learned_completeness_persists,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — diagnostic_inspector: filters a log into an ordered, isolated findings slice "
          "(the tokens saved — no second exploration), filters compose, and the inspector gets "
          "better over time — a first miss is folded forward (Law 1), a learned recurrence is LOUD "
          "(Law 7, the terminal falsifier).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

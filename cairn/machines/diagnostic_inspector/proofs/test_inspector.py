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

    python3 cairn/machines/diagnostic_inspector/proofs/test_inspector.py     # exit 0 = green
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.diagnostic import DiagnosticBase
from cairn.machines.diagnostic_inspector import (
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


# ── THE EVERY-VALUE CLAUSE (2026-08-06) ──────────────────────────────────────────────
# Akien, naming what the report must tell its consumer: "what variables were in play and
# important. what things is it operating on there... so that you have a complete picture
# of exactly what happened millisecond to millisecond leading up to the failure, and
# everything that was involved." Measured against the corpus that day: not one emit() site
# carries a SEED key, and a record that carries no values at all witnesses that a thing
# crossed and nothing about what it held. These teeth pin that the report SAYS SO.


def test_a_valueless_record_is_named_loud_with_its_count():
    box, dev = Mailbox(), _Dev()
    dev.set_diagnostic_receiver(box)
    # Two thin breadcrumbs and one fat record at the SAME gate — the count is the diagnosis.
    dev.emit("post", pointer="ticket/A", now=_t(100))
    dev.emit("post", pointer="ticket/A", now=_t(200))
    dev.emit("post", pointer="ticket/A", values={"envelope": "e1"}, now=_t(300))

    found = Inspector().inspect(box.records(), by_pointer("ticket/A"))
    loud = found["completeness"]["values_at_the_fault"]
    assert len(loud) == 1, f"one gate carried valueless records; reported {loud}"
    assert loud[0]["gate"] == "post"
    assert loud[0]["records"] == 3 and loud[0]["valueless"] == 2, (
        f"2 of 3 records at 'post' were thin; report said {loud[0]}")
    assert "placed too thin" in loud[0]["why_it_matters"].lower(), (
        "the finding must tell its consumer what to DO — re-place the instrument with the "
        "values needed. A bare flag makes the reader re-derive the next move, which is the "
        "second exploration this whole surface exists to abolish")
    # and per_gate carries the same measurement, so the reader never re-counts
    assert found["completeness"]["per_gate"]["post"]["valueless"] == 2


def test_every_record_carrying_values_reports_nothing_loud():
    """DEFECT-FIRST: a check that always fires is not a check."""
    box, dev = Mailbox(), _Dev()
    dev.set_diagnostic_receiver(box)
    dev.emit("post", pointer="ticket/A", values={"envelope": "e1"}, now=_t(100))
    dev.emit("verify", pointer="ticket/A", values={"expected": "2", "actual": "2"}, now=_t(200))

    found = Inspector().inspect(box.records(), by_pointer("ticket/A"))
    assert found["completeness"]["values_at_the_fault"] == [], (
        "a slice whose every record carries values must report NOTHING here")


def test_the_every_value_clause_is_not_folded_into_complete():
    """The two answer different questions and a record of truth may not collapse them
    (Law 7): `complete` = did a LEARNED gap come back; `values_at_the_fault` = was there
    anything to learn from at all. A thin record must not read as a recurrence."""
    box, dev = Mailbox(), _Dev()
    dev.set_diagnostic_receiver(box)
    dev.emit("post", pointer="ticket/A", now=_t(100))   # thin — nothing learned is missing

    found = Inspector().inspect(box.records(), by_pointer("ticket/A"))["completeness"]
    assert found["complete"] is True, (
        "no learned key was missing, so complete must stay True — folding the thinness in "
        "here would make a design gap indistinguishable from the terminal falsifier")
    assert found["recurrences"] == []
    assert found["values_at_the_fault"], "...while the thinness is still reported, loudly"


def test_the_seed_matches_the_intention_it_claims_to_carry():
    """The translation loss that started this: SEED said it carried the intention's list
    and had dropped `source` and the every-value clause. This tooth reds if the seed drifts
    from the intention's own sentence again — the words are quoted from
    CairnCommons/intentions-not-beside-code/I-complete-diagnostic-on-first-pass.md."""
    from cairn.machines.diagnostic_inspector import inspector as _insp
    named = ("identity", "location", "code", "expected", "actual", "fatality", "source", "trace")
    assert set(_insp.SEED) == set(named), (
        f"SEED drifted from the intention's named list; missing={set(named) - set(_insp.SEED)}, "
        f"extra={set(_insp.SEED) - set(named)}")
    # and the every-value clause is honoured by a CHECK, not by a key the registry could
    # never satisfy — requiring the literal "values" key would be missing by construction
    assert "values" not in _insp.SEED, (
        "'values' as a seed key is red-forever: _completeness scans INTO values and excludes "
        "the wrapper, so it can never appear in `present`")
    seeded = CompletenessRegistry.seeded()
    assert "source" in seeded.required("any-gate"), "a seeded registry must demand source"


def test_source_is_demanded_and_the_envelope_answers_it():
    """`source` reads green because emit() always stamps it. That is the point — the seed's
    job is to MATCH THE INTENTION, not to be interestingly unmet. This tooth is what makes
    the green non-vacuous: it reds if the envelope stops carrying it."""
    box, dev = Mailbox(), _Dev()
    dev.set_diagnostic_receiver(box)
    dev.emit("post", pointer="ticket/A", values={"envelope": "e1"}, now=_t(100))

    found = Inspector(CompletenessRegistry.seeded()).inspect(box.records(), by_pointer("ticket/A"))
    per_gate = found["completeness"]["per_gate"]["post"]
    assert "source" in per_gate["present"], "emit() stamps source; the report must see it"
    assert "source" not in per_gate["missing"]
    # ...and the rest of the seed IS unmet, which is the corpus's real state today
    assert {"code", "expected", "actual", "trace"} <= set(per_gate["missing"]), (
        "measured 2026-08-06: no emit site in the corpus carries these; if this tooth ever "
        "goes green on its own, the supply side finally landed and this message is the note")


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
        test_a_valueless_record_is_named_loud_with_its_count,
        test_every_record_carrying_values_reports_nothing_loud,
        test_the_every_value_clause_is_not_folded_into_complete,
        test_the_seed_matches_the_intention_it_claims_to_carry,
        test_source_is_demanded_and_the_envelope_answers_it,
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

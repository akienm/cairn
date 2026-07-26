"""The append door is INSTRUMENTED — a gate progression emits a seeded-complete findings.

WHAT THIS PROVES (Akien, 2026-07-25: "just attach it to a gate, and then we do something
that will naturally cause a gate progression, and we will get a proof instantly"):

  - THE PROGRESSION IS THE EVENT. Nobody scans, nobody polls, no daemon runs. Calling the
    single write-door emits one gate-contact record — so instrumenting this one function
    instruments every voyage advance in Cairn at once.
  - THE SEED IS THE FLOOR. A registry from ``CompletenessRegistry.seeded()`` demands
    I-complete-diagnostic-on-first-pass's named list from the very first report, instead of
    re-learning it one forced second-run at a time (Law 1 — the settled is not re-derived).
  - THE EXPECTED-VS-ACTUAL IS REAL. The caller asks to stand at a gate; the door reports
    what the compiled state actually came to rest on. Equal on the happy path — and the
    place a dropped move would show.
  - A HOLLOW PASS IS IMPOSSIBLE (Law 8). ``trace`` is in the seed and this door genuinely
    cannot supply it on a success path, so the findings come back INCOMPLETE and say so
    out loud. A green here would mean the completeness check had been faked.
  - UNATTACHED, NOTHING IS LOST. With no receiver the record HOLDS (Law 7).

    python3 cairn/charter/proofs/test_append_door_instrument.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cairn.charter import projector
from cairn.diagnostic_inspector.inspector import (
    CompletenessRegistry,
    Inspector,
    Mailbox,
    SEED,
    by_gate,
    by_pointer,
)


def _advance(tmp, box, gate="PROVEME", ident="widget"):
    """Cause one real gate progression through the single write-door."""
    h, s = str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")
    projector.set_diagnostic_receiver(box)
    try:
        record = {"id": ident, "gate": gate, "standing": f"{gate} — advance", "what": "advance"}
        state = projector.append_entry(h, s, record)
    finally:
        projector.set_diagnostic_receiver(None)   # targeted and TEMPORARY — take it down
    return state


def test_a_gate_progression_emits_one_contact():
    box = Mailbox()
    with tempfile.TemporaryDirectory() as tmp:
        _advance(tmp, box)
    records = box.records()
    assert len(records) == 1, f"one progression, one contact — got {len(records)}"
    r = records[0]
    assert r["gate"] == "append_entry"
    assert r["source"] == "charter.projector.append_entry"
    assert r["pointer"] == "widget", "the contact POINTS at the travelling thing (Law 6)"
    assert r["home"] == "sent"


def test_the_expected_vs_actual_is_the_real_transition():
    box = Mailbox()
    with tempfile.TemporaryDirectory() as tmp:
        state = _advance(tmp, box, gate="PROVEME")
    v = box.records()[0]["values"]
    assert v["expected"] == "PROVEME", "what the caller asked to stand at"
    assert v["actual"] == "PROVEME", "what the compiled state came to rest on"
    assert v["actual"] == state["cursor"]["gate"], "the report agrees with the state on disk"
    assert v["seq"] == 0, "the seq append() assigned, not the one the caller didn't send"
    assert v["from"] is None, "no prior history — nothing to come from"


def test_the_second_advance_carries_where_it_came_from():
    box = Mailbox()
    with tempfile.TemporaryDirectory() as tmp:
        h, s = str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")
        projector.set_diagnostic_receiver(box)
        try:
            projector.append_entry(h, s, {"id": "widget", "gate": "BUILDME", "standing": "BUILDME"})
            projector.append_entry(h, s, {"id": "widget", "gate": "PROVEME", "standing": "PROVEME"})
        finally:
            projector.set_diagnostic_receiver(None)
    second = box.records()[1]["values"]
    assert second["from"] == "BUILDME" and second["expected"] == "PROVEME", \
        "the contact carries the whole transition, not just its destination"
    assert second["seq"] == 1 and second["entries"] == 2


def test_the_seed_is_the_floor_not_the_horizon():
    """Every seeded datum is demanded of a gate that has learned nothing at all."""
    fresh = CompletenessRegistry.seeded()
    assert fresh.required("append_entry") == set(SEED), \
        "the settled list arrives as structure, not as N forced second-runs"
    assert CompletenessRegistry().required("append_entry") == set(), \
        "a BARE registry stays empty — the learning half is still provable in isolation"
    fresh.record_miss("append_entry", "held_for")
    assert fresh.required("append_entry") == set(SEED) | {"held_for"}, "learning grows ABOVE the seed"
    assert fresh.record_miss("append_entry", "trace") == "recurred", \
        "a seeded key that goes missing was TOLD ONCE, at the seed — never re-learned"


def test_the_findings_are_honestly_incomplete():
    """Law 8: the door cannot supply ``trace`` on a success path, and the report says so."""
    box = Mailbox()
    with tempfile.TemporaryDirectory() as tmp:
        _advance(tmp, box)
    comp = Inspector(CompletenessRegistry.seeded()).inspect(
        box.records(), by_pointer("widget"), by_gate("append_entry")
    )["completeness"]
    per = comp["per_gate"]["append_entry"]
    assert set(per["required"]) == set(SEED)
    assert per["missing"] == ["trace"], f"one honest gap, named — got {per['missing']}"
    assert comp["complete"] is False, "a hollow green would mean the check was faked"
    assert comp["recurrences"] == [{"gate": "append_entry", "key": "trace"}], "LOUD (Law 7)"


def test_a_carried_datum_is_never_reported_missing():
    """``source`` rides on the envelope, not in values — measuring only values would
    manufacture a FALSE miss, and a false miss folded into the registry corrupts the loop."""
    box = Mailbox()
    with tempfile.TemporaryDirectory() as tmp:
        _advance(tmp, box)
    reg = CompletenessRegistry.seeded()
    reg.record_miss("append_entry", "source")
    comp = Inspector(reg).inspect(box.records(), by_pointer("widget"))["completeness"]
    assert "source" not in comp["per_gate"]["append_entry"]["missing"], \
        "the envelope carries it; demanding a duplicate in values would be a phantom gap"


def test_unattached_the_record_holds_and_is_not_lost():
    projector.set_diagnostic_receiver(None)
    before = len(projector.held_diagnostics())
    with tempfile.TemporaryDirectory() as tmp:
        h, s = str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")
        projector.append_entry(h, s, {"id": "orphan", "gate": "THINKME", "standing": "THINKME"})
    held = projector.held_diagnostics()
    assert len(held) == before + 1, "no receiver is not a licence to drop it (Law 7)"
    assert held[-1]["home"] == "held" and held[-1]["pointer"] == "orphan"


def test_the_instrument_does_not_disturb_the_door():
    """The state written to disk is exactly what it was before the door was instrumented."""
    with tempfile.TemporaryDirectory() as tmp:
        h, s = str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")
        projector.set_diagnostic_receiver(Mailbox())
        try:
            state = projector.append_entry(h, s, {"id": "widget", "gate": "PROVEME", "standing": "PROVEME"})
        finally:
            projector.set_diagnostic_receiver(None)
        on_disk = json.loads(Path(s).read_text())
        history = json.loads(Path(h).read_text())
    assert state == on_disk, "the returned state is the state on disk"
    assert len(history) == 1 and history[0]["seq"] == 0
    assert "trace" not in history[0], "the instrument writes NOTHING into the record of truth"



# ── THE SHAPE GATE (ratified by Akien 2026-07-25: universal floor, `standing` only) ──

def test_a_record_without_standing_is_refused_before_the_write():
    """The whole point: history is append-only, so the ONLY place a bad record can be stopped
    is on the way in. Nothing may be written, not even partially."""
    with tempfile.TemporaryDirectory() as tmp:
        h, s = str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")
        try:
            projector.append_entry(h, s, {"id": "widget", "gate": "PROVEME", "what": "advance"})
        except projector.RecordRefused as e:
            msg = str(e)
        else:
            raise AssertionError("the exact 2026-07-25 fault must now be refused, not accepted")
        assert not Path(h).exists() and not Path(s).exists(), \
            "REFUSED BEFORE THE WRITE — a half-written record of truth is worse than none"
    for owed in ("standing", "harbor_master", "65/66", "append-door-has-no-schema-gate"):
        assert owed in msg, f"the refusal must resolve itself on the first pass; missing {owed!r}"


def test_an_empty_standing_is_refused_too():
    with tempfile.TemporaryDirectory() as tmp:
        h, s = str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")
        for bad in ("", None):
            try:
                projector.append_entry(h, s, {"gate": "PROVEME", "standing": bad})
            except projector.RecordRefused:
                pass
            else:
                raise AssertionError(f"standing={bad!r} is absence wearing a key, and must fail")


def test_the_floor_is_exactly_one_field_and_the_rest_stay_free():
    """`gate` is carried by only 80% of real records — requiring it would retroactively
    invalidate 13 legitimate ones. The floor is what was MEASURED, not what looks tidy."""
    assert projector.UNIVERSAL_REQUIRED == ("standing",)
    with tempfile.TemporaryDirectory() as tmp:
        h, s = str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")
        state = projector.append_entry(h, s, {"standing": "PROVED — bare but honest"})
    assert state["cursor"]["standing"].startswith("PROVED"), \
        "a record carrying only the floor is VALID — no gate, no proof, no validation needed"


def test_every_real_history_on_disk_would_pass_the_gate():
    """The gate is retroactively honest: it refuses nothing that is already legitimately here.
    Reads the live histories — asserts CONFORMANCE, never a count that legitimately moves."""
    root = Path(__file__).resolve().parents[2]
    offenders = []
    for hist in sorted(root.glob("*/history.json")):
        for rec in json.loads(hist.read_text()):
            if not all(rec.get(k) for k in projector.UNIVERSAL_REQUIRED):
                offenders.append((hist.parent.name, rec.get("seq"), sorted(rec)))
    assert offenders == [("diagnostic_inspector", 4, ["at", "gate", "id", "seq", "what", "why"])], \
        f"the ONLY record that fails the floor must be the permanent one this gate exists " \
        f"to have prevented — got {offenders}"

TESTS = [
    test_a_gate_progression_emits_one_contact,
    test_the_expected_vs_actual_is_the_real_transition,
    test_the_second_advance_carries_where_it_came_from,
    test_the_seed_is_the_floor_not_the_horizon,
    test_the_findings_are_honestly_incomplete,
    test_a_carried_datum_is_never_reported_missing,
    test_unattached_the_record_holds_and_is_not_lost,
    test_the_instrument_does_not_disturb_the_door,
    test_a_record_without_standing_is_refused_before_the_write,
    test_an_empty_standing_is_refused_too,
    test_the_floor_is_exactly_one_field_and_the_rest_stay_free,
    test_every_real_history_on_disk_would_pass_the_gate,
]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)

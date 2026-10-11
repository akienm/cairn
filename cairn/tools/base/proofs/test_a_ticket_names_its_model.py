"""Proof for ticket 2cee2c5e8478 — a ticket names the model its work runs on.

Every cast tooth runs over a SCRATCH commons the proof owns (``artifact.set_diagnostic_roots``),
restored in ``finally``; the scratch store's charter declares the live charter's plan_fields,
so a live charter without 'model' reds the tooth that keeps one.

1. a cast without 'model' is written with model 'opus';
2. a cast with model 'fable' keeps it (and 'FABLE' folds to it);
3. a cast with model 'gpt' is refused with a lack naming 'model' and the value 'gpt' (a
   charter refusing the key outright is not this lack), and nothing is written;
4. ticket_model({}) == 'opus' and ticket_model({'model': 'haiku'}) == 'haiku'.

THE SUBJECT IS BOUND AT CALL TIME: ``transitions`` is imported inside each tooth, so the
hollow reading reds the declared teeth by name instead of failing at import.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_ticket_names_its_model.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "2cee2c5e8478": {
        "1": "a_cast_without_model_is_written_with_opus",
        "2": "a_cast_with_fable_keeps_it",
        "3": "a_cast_with_gpt_is_refused_naming_model",
        "4": "ticket_model_reads_opus_when_absent",
    },
}

LIVE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"
WORKFLOW = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _doc(tmp: Path, tid: str, **over) -> dict:
    """A complete cast over scratch berths (the sorted berth agrees with the doc)."""
    sorted_berth = tmp / f"sorted-{tid}.json"
    sorted_berth.write_text(json.dumps({"skill": "sorted", "answers": {
        "workflow": WORKFLOW, "node_class": "code-seam"}}), encoding="utf-8")
    doc = {
        "id": tid, "title": "model proof " + tid, "date": "2026-10-11",
        "owner": "codemother", "owning_intention": "skills/sorted/intention+why.json",
        "intention": "a ticket names its model", "why": "proof", "traces_to": "Law 4",
        "how": "cast_ticket", "falsifier": "DONE when the model is stamped",
        "node_class": "code-seam", "workflow_and_state": WORKFLOW,
        "watchme": "none, because cairn/tools/base/transitions.py",
        "sorted_berth": str(sorted_berth),
        "intent_berth": "none, because cairn/tools/base/transitions.py",
    }
    doc.update(over)
    return doc


def _cast(tmp: Path, tickets: Path, tid: str, **over):
    from cairn.tools.base import transitions
    path = transitions.cast_ticket(_doc(tmp, tid, **over), actor="proof", tickets_dir=tickets)
    return json.loads(path.read_text(encoding="utf-8"))


def test_1(tmp: Path, tickets: Path) -> None:
    try:
        written = _cast(tmp, tickets, "aaaaaaaaaaa1")
        check(PROVES["2cee2c5e8478"]["1"], written.get("model") == "opus", repr(written.get("model")))
    except Exception as exc:  # noqa: BLE001
        check(PROVES["2cee2c5e8478"]["1"], False, f"{type(exc).__name__}: {exc}")


def test_2(tmp: Path, tickets: Path) -> None:
    try:
        kept = _cast(tmp, tickets, "aaaaaaaaaaa2", model="fable")
        folded = _cast(tmp, tickets, "aaaaaaaaaaa3", model="FABLE")
        check(PROVES["2cee2c5e8478"]["2"],
              kept.get("model") == "fable" and folded.get("model") == "fable",
              f"{kept.get('model')!r}, {folded.get('model')!r}")
    except Exception as exc:  # noqa: BLE001
        check(PROVES["2cee2c5e8478"]["2"], False, f"{type(exc).__name__}: {exc}")


def test_3(tmp: Path, tickets: Path) -> None:
    from cairn.tools.base import transitions
    try:
        _cast(tmp, tickets, "aaaaaaaaaaa4", model="gpt")
        check(PROVES["2cee2c5e8478"]["3"], False, "the cast was admitted")
    except transitions.CastRefused as exc:
        written = list(tickets.glob("aaaaaaaaaaa4*.json"))
        check(PROVES["2cee2c5e8478"]["3"],
              any("model" in lack and "gpt" in lack for lack in exc.lacks) and not written,
              f"lacks={exc.lacks}, written={written}")
    except Exception as exc:  # noqa: BLE001
        check(PROVES["2cee2c5e8478"]["3"], False, f"{type(exc).__name__}: {exc}")


def test_4() -> None:
    try:
        from cairn.tools.base import transitions
        got = (transitions.ticket_model({}), transitions.ticket_model({"model": "haiku"}))
        check(PROVES["2cee2c5e8478"]["4"], got == ("opus", "haiku"), repr(got))
    except Exception as exc:  # noqa: BLE001
        check(PROVES["2cee2c5e8478"]["4"], False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    live = A.journal_path(A.roots()["CairnCommons"])
    live_before = live.read_bytes() if live.exists() else b""
    with tempfile.TemporaryDirectory(prefix="cairn-ticket-model-proof-") as d:
        tmp = Path(d)
        commons = tmp / "CairnCommons"
        tickets = commons / "tickets"
        tickets.mkdir(parents=True)
        fields = json.loads(LIVE_CHARTER.read_text(encoding="utf-8"))["plan_fields"]
        (tickets / "_charter+why.json").write_text(json.dumps({"plan_fields": fields}) + "\n")
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
        try:
            test_1(tmp, tickets)
            test_2(tmp, tickets)
            test_3(tmp, tickets)
        finally:
            A.set_diagnostic_roots(None)
    test_4()
    live_after = live.read_bytes() if live.exists() else b""
    check("the live journal never moved", live_before == live_after)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

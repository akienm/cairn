"""Proof for ticket c1c3c0300d5c — the build gate judges every component a ticket writes, not
only its owner.

Measured 2026-11-18: dda0e72b9c67, owned by cairn/tools/scratch, wrote a cross-device import
into bin/proofs/ (a path in its bounds.in); the PROVEME build gate inspected scratch alone,
encapsulation_holds reds a breach only on the row holding it or the row it lands on, and dda0
crossed green. The red surfaced at the next bin-owned crossing.

1. clause_1_a_breach_written_outside_the_owner_reds_the_crossing: a PROVEME exit for a ticket
   owned by component a whose bounds.in holds a file in component b carrying an import of
   cairn.devices.x is refused, a finding naming b's encapsulation_holds, and nothing journaled;
2. clause_2_the_clean_crossing_names_every_component: the same ticket with the import removed
   crosses, and the journal's build_gate note names both a and b.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_the_build_gate_judges_every_written_component.py
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
    "c1c3c0300d5c": {
        "1": "clause_1_a_breach_written_outside_the_owner_reds_the_crossing",
        "2": "clause_2_the_clean_crossing_names_every_component",
    },
}

_TID = "c0ffee000001"
_AT_PROVE = "code-seam@v1: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> LEARNME -> PROVED"
_BREACH = "from cairn.devices.x import y\n"


def _component(root: Path, name: str, extra: dict[str, str] | None = None) -> Path:
    """A census-visible, green component at <root>/cairn/<name> (the shape test_transitions'
    fixture uses, so the repo the sieve reads is <root>), sealed over its own source."""
    d = root / "cairn" / name
    (d / "proofs").mkdir(parents=True)
    (d / "proofs" / "test_x.py").write_text("assert True\n")
    (d / "lib.py").write_text("def helper():\n    return 1\n")
    for rel, text in (extra or {}).items():
        (d / rel).write_text(text)
    (d / "intention+why.json").write_text(json.dumps(
        {"component": name, "runtime_role": "tool",
         "how_it_learns": "fixture component — does not learn", "gated_by": ["CC"],
         "claim_provenance": {"role": "test", "what": "test", "why": "test"}}))
    from cairn.tools.inspect_wire.inspect_wire import ask
    fp = ask("_source_fingerprint", d)
    (d / "validations").mkdir()
    (d / "validations" / "test_x.json").write_text(json.dumps([{
        "claim": "fixture", "caller": "test", "date": "2026-01-01T00:00:00",
        "method": "fixture", "verdict": "green",
        "evidence": {"source_fingerprint": fp, "teeth_green": ["test_the_fixture"]},
        "falsifier": "test", "horizon": "test"}]))
    return d


def _world(root: Path, *, breach: bool) -> tuple[Path, Path, Path]:
    """Owner a, written component b (with or without the breach), device x it would reach,
    and a ticket store holding a plan whose bounds.in names a file in b."""
    dev = root / "cairn" / "devices" / "x"
    dev.mkdir(parents=True)
    (dev / "__init__.py").write_text("")
    (dev / "y.py").write_text("Y = 1\n")
    a = _component(root, "a")
    b = _component(root, "b", {"breach.py": _BREACH} if breach else None)
    tickets = root / "commons" / "tickets"
    tickets.mkdir(parents=True)
    (tickets / f"{_TID}-fixture.json").write_text(json.dumps({
        "id": _TID, "title": "fixture",
        "bounds": {"in": ["cairn/a/lib.py", "cairn/b/breach.py"], "out": []}}))
    return a, b, tickets


def _patched(root: Path, tickets: Path):
    from cairn.tools.base import ticket_file, transitions
    saved = (transitions._REPO_ROOT, ticket_file._TICKETS)
    transitions._REPO_ROOT, ticket_file._TICKETS = root, tickets
    return saved


def _restore(saved) -> None:
    from cairn.tools.base import ticket_file, transitions
    transitions._REPO_ROOT, ticket_file._TICKETS = saved


def clause_1_a_breach_written_outside_the_owner_reds_the_crossing() -> None:
    from cairn.tools.base import transitions
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        a, b, tickets = _world(root, breach=True)
        hist = a / "history.json"
        saved = _patched(root, tickets)
        try:
            transitions._build_gate(str(hist), ticket=_TID)
        except transitions.BuildGateRed as e:
            enc = [f for f in e.findings if f.get("method") == "encapsulation_holds"]
            assert enc, f"the breach in b must red encapsulation_holds: {e.findings}"
            assert all(f.get("component") == "b" for f in enc), \
                f"the finding must name the component holding the breach, b: {enc}"
            assert "'b'" in str(e) and "breach.py" in str(e), \
                f"the refusal must name b and the file: {e}"
        else:
            raise AssertionError("a ticket owned by a crossed while the b it writes reds "
                                 "encapsulation_holds — the gate judged the owner alone")
        finally:
            _restore(saved)
        assert not hist.exists(), "a refused crossing must journal nothing"
        # The same breach under a ticket that writes only a: the owner's row is clean, so
        # the narrow gate's verdict stands — the widening comes from bounds.in, not a sieve.
        (tickets / f"{_TID}-fixture.json").write_text(json.dumps({
            "id": _TID, "title": "fixture", "bounds": {"in": ["cairn/a/lib.py"], "out": []}}))
        saved = _patched(root, tickets)
        try:
            note, record = transitions._build_gate(str(hist), ticket=_TID)
        finally:
            _restore(saved)
        assert "sieves over a, and" in note, \
            f"a ticket writing only its owner inspects only its owner: {note}"


def clause_2_the_clean_crossing_names_every_component() -> None:
    from cairn.tools.base import transitions
    from cairn.tools.charter import projector
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        a, b, tickets = _world(root, breach=False)
        hist, state = a / "history.json", a / "state.json"
        saved = _patched(root, tickets)
        try:
            note, record = transitions._build_gate(str(hist), ticket=_TID)
            assert "over a, b (the owner and every component" in note, \
                f"the clean note must name every component inspected: {note}"
            guards = [e for e in record if e["identity"] == "the_census_can_measure_the_component"]
            assert {(e.get("values") or {}).get("component") for e in guards} == {"a", "b"}, \
                f"the record must carry a census lane for a and for b: {guards}"
            new = transitions.emit(_AT_PROVE, "LEARNME", history_path=str(hist),
                                   state_path=str(state))
        finally:
            _restore(saved)
        assert "[LEARNME:waiting]" in new
        assert projector.read_history(str(hist))[0]["build_gate"].startswith("clean — build_inspector")


FAILURES: list[str] = []


def main() -> int:
    for name, fn in [(k, v) for k, v in globals().items() if k.startswith("clause_")]:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides another
            FAILURES.append(name)
            print(f"  FAIL  {name}")
            print(f"        {type(exc).__name__}: {exc}"[-1200:])
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


def test_clause_1_a_breach_written_outside_the_owner_reds_the_crossing():
    clause_1_a_breach_written_outside_the_owner_reds_the_crossing()


def test_clause_2_the_clean_crossing_names_every_component():
    clause_2_the_clean_crossing_names_every_component()


if __name__ == "__main__":
    sys.exit(main())

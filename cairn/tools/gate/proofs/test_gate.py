"""Proof for gate — the == compare, and the ways a proof record decays back into silence.

THE FAILURE MODE THIS COMPONENT HAS, and it is not "the compare is wrong". Nobody writes a
broken ==. What happens is that the RECORD gets thinner: it starts listing only failures
(because that is what everyone means by a report), then an empty one starts reading as
success, and at that point the gate's green is a green about SILENCE — indistinguishable
from no check running, the subject not being found, or the walk crashing early.

So the teeth are aimed at the thinning, not at equality:

  (c) an EMPTY record raises — a gate that proved nothing has not proved everything
  (d) a record that lists only failures cannot be told from one where nothing ran, which
      is why the passes are IN the record and counted
  (e) an entry missing expected or actual raises rather than being skipped — a skipped
      entry means the gate opened on fewer checks than it claims
  (h) key order in a structured value cannot decide a verdict

    python3 cairn/tools/gate/proofs/test_gate.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.gate import gate

OK = gate.proved(identity="charter_on_disk", location="devices/cairn/machines/bus",
                 code="inspector.py:charter_on_disk", expected=1.0, actual=1.0,
                 source="build_inspector")
BAD = gate.proved(identity="proofs_exist", location="devices/builder",
                  code="inspector.py:proofs_exist", expected=1.0, actual=0.0,
                  source="build_inspector")


def test_a_every_check_proved_opens_the_gate():
    v = gate.verdict([OK, OK])
    assert v["opens"] and v["verdict"] == gate.OPEN, v
    assert v["checks"] == 2 and v["passed"] == 2 and v["failed"] == 0, v


def test_b_one_mismatch_closes_it_and_names_which():
    v = gate.verdict([OK, BAD])
    assert not v["opens"], v
    assert v["mismatches"] == [BAD], v
    assert v["passed"] == 1 and v["failed"] == 1, v


def test_c_an_empty_record_raises_it_does_not_pass():
    """NO EMPTY ANYWHERE (Akien, 2026-08-13). A gate that proved nothing has not proved
    everything — an empty list is the vacuous green (Law 8), and `all([])` is True, which
    is exactly how this defect ships without anyone noticing."""
    try:
        gate.verdict([])
    except gate.NoProof:
        return
    raise AssertionError("an empty proof record produced a verdict instead of raising")


def test_d_the_record_lists_what_passed_not_only_what_failed():
    """THE WHOLE POINT (Akien: "The build inspector must list EVERY TEST THAT HAS PASSED").
    A findings report throws the passes away, so an empty one means "everything passed"
    AND "nothing ran" AND "the subject wasn't found" — a gate on that is a gate on silence.
    Here twenty checks that pass and zero that pass are different records."""
    v = gate.verdict([OK, OK, BAD])
    assert v["proved"] == ["charter_on_disk @ devices/cairn/machines/bus"] * 2, v["proved"]
    assert v["checks"] == 3, "the record must count every check that RAN, not just failures"


def test_e_an_entry_without_expected_or_actual_raises():
    """A skipped entry means the gate opened on fewer checks than it says it did, and the
    verdict cannot report a check it silently dropped."""
    for broken in ({"identity": "x", "expected": 1}, {"identity": "x", "actual": 1},
                   {"expected": 1, "actual": 1}):
        try:
            gate.verdict([OK, broken])
        except gate.NoProof:
            continue
        raise AssertionError(f"an unusable entry was skipped instead of refused: {broken}")


def test_f_proved_builds_the_seed_shape_so_every_gate_emits_the_same_one():
    """SAME PATTERN EVERYWHERE (Akien, 2026-08-13). The shape is diagnostic_inspector's
    SEED — Akien's 2007 list — so a reader who has read one proof record has read all."""
    for field in gate.SEED:
        assert field in OK, f"gate.proved() dropped a seed field: {field}"


def test_g_fatality_is_derived_not_asked_for():
    """A caller who has to remember to say 'this one is fatal' will forget, and a gate that
    reads a caller's opinion of severity is a gate consulting something other than ==."""
    assert gate.proved(identity="x", expected=1, actual=0)["fatality"] == "closes the gate"
    assert gate.proved(identity="x", expected=1, actual=1)["fatality"] == "none"


def test_h_key_order_in_a_value_cannot_decide_a_verdict():
    """Otherwise the gate measures how its caller happened to construct a literal."""
    assert gate.passed(gate.proved(identity="x", expected={"a": 1, "b": 2},
                                   actual={"b": 2, "a": 1}))


def test_i_an_unserializable_value_does_not_crash_the_gate():
    """A gate that raises on an odd value FAILS OPEN in every caller that wraps it."""
    v = gate.verdict([gate.proved(identity="x", expected=Path("/a"), actual=Path("/b"))])
    assert not v["opens"], v


def test_j_the_gate_holds_no_state_between_calls():
    """Law 6: a tool has users, not an owner — because it holds nothing to gate."""
    gate.verdict([OK, BAD])
    assert gate.opens([OK]), "a prior call changed a later verdict"


def test_k_the_real_inspector_emits_a_record_that_is_not_silent():
    """Against the live corpus, BY INVARIANT: the gate's floor is that the record is
    non-empty and that passes outnumber nothing — a record carrying only failures would
    satisfy a naive == check and still be the silence this exists to end."""
    from cairn.machines.build_inspector import inspector
    report = inspector.inspect(component="bus")
    record = report["proof_record"]
    assert record, "the live inspector emitted an empty proof record"
    assert any(gate.passed(e) for e in record), \
        "the live record lists no PASSES — it is a findings report wearing the seed shape"
    for e in record:
        assert all(k in e for k in gate.REQUIRED), e
    assert report["gate"]["checks"] == len(record), report["gate"]


def _run() -> int:
    fails = []
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — the proof reports, it does not propagate
            fails.append((name, exc))
            print(f"  RED  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{'RED' if fails else 'green'}: {len(fails)} failing")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_run())

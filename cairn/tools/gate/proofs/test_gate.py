"""Proof for gate — the == compare, and the ways an == compare gets quietly loosened.

THE FAILURE MODE THIS COMPONENT HAS, and it is not "the compare is wrong". Nobody writes a
broken ==. What happens is that the compare gets HELPFUL: it starts ignoring order, then it
starts ignoring duplicates, then it starts allowing a subset "because nothing unexpected
fired", and each step is one small reasonable-looking commit. At the end the gate opens on
a findings report that does not match what it allows, which is the one thing Akien said it
may never do.

So the teeth are aimed at the loosenings, not at equality:

  (b) sorting is the ONLY normalization — pinned by requiring it to survive shuffling
  (c) duplicates are NOT collapsed — a scanner that double-fires must close the gate
  (d) a subset does NOT open it — the permission-slip reading, refused
  (e) a MISSING allowed finding closes it too — the stale-in-the-safe-direction case,
      which is the whole reason the compare is identity and not containment
  (j) an ABSENT baseline is an ERROR — the loosening that hides inside a strict-looking
      default, since "missing file means allow nothing" still closes the gate and still
      invents a declaration nobody made

    python3 cairn/tools/gate/proofs/test_gate.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.scratch import scratch_dir
from cairn.tools.gate import gate

F1 = {"sieve": "charter_on_disk", "component": "bus", "finding": "no charter"}
F2 = {"sieve": "proofs_exist", "component": "builder", "finding": "no proofs"}


def test_a_identical_opens_and_says_so():
    v = gate.verdict([F1, F2], [F1, F2])
    assert v["opens"] and v["verdict"] == gate.OPEN, v
    assert not v["unexpected"] and not v["missing"], v


def test_b_scan_order_cannot_decide_a_verdict():
    """Without sorting, this gate measures the scanner's iteration order. A dict rebuild
    or a filesystem walk in a different order would close a gate that found exactly what
    it was supposed to find."""
    assert gate.opens([F1, F2], [F2, F1]), "the compare was order-sensitive"


def test_c_duplicates_are_not_collapsed():
    """Two identical findings are two findings. Collapsing them lets a scanner that starts
    double-firing look correct — the compare is a multiset compare, not a set compare."""
    v = gate.verdict([F1, F1], [F1])
    assert not v["opens"], "a duplicate finding was deduplicated into looking correct"
    assert v["unexpected"] == [F1], v


def test_d_a_subset_does_not_open_the_gate():
    """THE PERMISSION-SLIP READING, REFUSED. 'Nothing unexpected fired' is the compare
    everyone reaches for first, and it can only ever be too generous."""
    assert not gate.opens([F1], [F1, F2]), "a subset opened the gate"


def test_e_a_missing_allowed_finding_closes_it_too():
    """Stale in the direction that LOOKS safe: a finding stopped firing and nobody learned
    that the world changed. Identity is what makes that as loud as a new finding."""
    v = gate.verdict([F1], [F1, F2])
    assert v["missing"] == [F2], v
    assert not v["unexpected"], "a missing entry was misreported as an unexpected one"


def test_f_an_empty_allowlist_closes_on_any_finding():
    """The degenerate gate — and the one build_inspector runs today, honestly closed."""
    assert not gate.opens([F1], [])
    assert gate.opens([], []), "a clean report against an empty allowlist must OPEN"


def test_g_the_verdict_carries_the_whole_diagnostic():
    """A closed gate that says only 'closed' makes the next mind re-run it to find out
    what happened (I-complete-diagnostic-on-first-pass)."""
    v = gate.verdict([F1, F2], [F2])
    assert v["unexpected"] == [F1] and v["missing"] == [], v
    assert "unexpected" in v["why"] and str(v["compared"]) == "2", v


def test_h_an_unserializable_finding_does_not_crash_the_gate():
    """A gate that raises on an odd finding FAILS OPEN in every caller that wraps it in a
    try. The shape of a finding is the caller's business, not this tool's."""
    v = gate.verdict([{"path": Path("/tmp/x"), "n": 1}], [])
    assert not v["opens"], v


def test_j_an_absent_baseline_is_an_error_not_an_empty_one():
    """AKIEN, 2026-08-13: "an absent allowed.json is an ERROR." The first cut read a
    missing file as `[]`, which sounds strict — it closes the gate — and still decides on
    the operator's behalf, then reports a verdict as though somebody had declared it. An
    unconfigured gate must not produce a verdict at all."""
    d = scratch_dir("gate-baseline-")
    try:
        gate.allowed_from(d)
    except gate.NoBaseline as exc:
        assert "[]" in str(exc), "the error must say how to fix it, not just that it failed"
        return
    raise AssertionError("an absent baseline was silently read as an empty allowlist")


def test_k_an_authored_empty_baseline_is_legal_and_means_allows_nothing():
    """The pair to (j), and the reason (j) can be strict: declaring 'this gate allows
    nothing' costs one line. Without this, `absent is an error` would have no legal way to
    express the strictest gate."""
    d = scratch_dir("gate-baseline-empty-")
    (d / gate.BASELINE).write_text("[]")
    assert gate.allowed_from(d) == []
    assert not gate.opens([F1], gate.allowed_from(d))
    assert gate.opens([], gate.allowed_from(d))


def test_l_a_baseline_file_may_be_named_directly():
    d = scratch_dir("gate-baseline-direct-")
    p = d / "other-name.json"
    p.write_text('[{"sieve":"x"}]')
    assert gate.allowed_from(p) == [{"sieve": "x"}]


def test_i_the_gate_holds_no_state_between_calls():
    """Law 6: a tool has users, not an owner — because it holds nothing to gate. If a call
    could change a later call's answer, this would be a machine and would need one."""
    gate.verdict([F1, F2], [F1])
    assert gate.opens([F1], [F1]), "a prior call changed a later verdict"


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

"""Proof for ticket eb27604ab267 — the tester seals nothing for a run whose every tooth printed NOTRUN.

Outline 9.4.2.3.3.1 (Akien, Q#90): one sealer, on cairn's home, Linux. 9.4.8.1 (CC's decision on Q#98): a box that
cannot run a proof asks for the sealer's run and does not run it itself; a tooth that needs what the box lacks reads
not-run, never red. Before this the tester read an exit-0 run with no green tooth as RED ('zero teeth printed'), so a
proof that could not run on a box had no honest outcome. The reader is proof_coverage.notrun_printed (d845546b67b9).

Every tooth drives the real run_proof over a one-file fixture proof in a scratch component, with the store's
persist_validation replaced by a recorder, so "wrote nothing" is a measurement and not a hope. Nothing is sealed.

    python <this file>
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "eb27604ab267": {
        "1": "an_all_notrun_run_is_not_red_and_writes_no_validation",
        "2": "a_mixed_run_seals_its_green_teeth_and_an_empty_run_is_still_red",
    },
}

_SWEEP = {"skipped": "proof fixture: a scratch component, nothing to sweep"}

_ALL_NOTRUN = '''import sys
print("  NOTRUN  test_a_needs_systemd — this box has no systemctl")
print("  NOTRUN  test_b_needs_bwrap — no bubblewrap")
sys.exit(0)
'''
_MIXED = '''import sys
print("  PASS  test_a_runs_anywhere")
print("  NOTRUN  test_b_needs_systemd — this box has no systemctl")
sys.exit(0)
'''
_EMPTY = '''import sys
print("this proof names no tooth at all")
sys.exit(0)
'''


def _component(prefix: str, body: str) -> Path:
    root = scratch_dir(prefix) / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    proof = root / "proofs" / "test_fixture.py"
    proof.write_text(body, encoding="utf-8", newline="\n")
    return proof


@contextlib.contextmanager
def _recording_store():
    """persist_validation records instead of writing; read_validations answers nothing standing."""
    import cairn.tools.validation_store.validation_store as vs
    persisted: list = []
    saved = (vs.read_validations, vs.persist_validation)
    vs.read_validations = lambda proof_path=None, **kw: []
    vs.persist_validation = lambda record, **kw: persisted.append(record) or "recorded"
    try:
        yield persisted
    finally:
        vs.read_validations, vs.persist_validation = saved


def _run(proof: Path, *, sink: str) -> dict:
    from cairn.devices.tester.device import TesterDevice
    kw = {"scratch_sweep": dict(_SWEEP)} if sink == "validations" else {}
    return TesterDevice().run_proof(proof, sink=sink, caller="proof-fixture", timeout=60, isolation="none", **kw)


def an_all_notrun_run_is_not_red_and_writes_no_validation() -> None:
    from cairn.devices.tester.device import NOTRUN, RED
    proof = _component("testing-eb27-allnotrun-", _ALL_NOTRUN)
    with _recording_store() as persisted:
        record = _run(proof, sink="validations")
    assert record["verdict"] == NOTRUN, f"an all-NOTRUN run must read not-run, got {record['verdict']!r}"
    assert record["verdict"] != RED, "an all-NOTRUN run must not be RED"
    assert persisted == [], f"an all-NOTRUN run wrote a validation: {persisted}"
    ev = record["evidence"]
    assert ev["teeth_green"] == [] and ev["teeth_red"] == [], ev
    assert ev["teeth_notrun"] == ["test_a_needs_systemd", "test_b_needs_bwrap"], ev.get("teeth_notrun")
    assert "Linux sealer" in ev["stderr_tail"], f"the run must say it asks for the sealer: {ev['stderr_tail']!r}"


def a_mixed_run_seals_its_green_teeth_and_an_empty_run_is_still_red() -> None:
    from cairn.devices.tester.device import GREEN, RED
    mixed = _component("testing-eb27-mixed-", _MIXED)
    with _recording_store() as persisted:
        record = _run(mixed, sink="validations")
    assert record["verdict"] == GREEN, f"green and NOTRUN teeth seal as green, got {record['verdict']!r}"
    assert record["evidence"]["teeth_green"] == ["test_a_runs_anywhere"], record["evidence"]["teeth_green"]
    assert record["evidence"]["teeth_notrun"] == ["test_b_needs_systemd"], record["evidence"].get("teeth_notrun")
    assert len(persisted) == 1, f"a mixed run must still seal its green teeth: {persisted}"
    empty = _component("testing-eb27-empty-", _EMPTY)
    with _recording_store() as persisted:
        record = _run(empty, sink="none")
    assert record["verdict"] == RED, f"a run that names no tooth at all stays RED, got {record['verdict']!r}"
    assert "zero teeth printed" in record["evidence"]["stderr_tail"], record["evidence"]["stderr_tail"]


TEETH = [an_all_notrun_run_is_not_red_and_writes_no_validation,
         a_mixed_run_seals_its_green_teeth_and_an_empty_run_is_still_red]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

"""Proof for ticket 2b34b52f80f3 — the verdict-deposit ledger records a failed deposit attempt.

Akien, 2026-10-10: "we need to make the queue record stderr. and the result code for heavens
sake." Measured that day: the live ledger held one ``enqueued`` line for
verdict-20260815T141125-dd35ea1c8f7b and nothing else, although every drain since had refused
it — the only trace of each refusal was a stderr print. A record of truth that keeps no failure
is the silent lapse the ledger exists to end (Law 7).

One tooth per numbered falsifier clause, each over a fresh ledger in a tmp directory (never the
live one):

  1. A FAILED ATTEMPT IS A RECORD. After enqueue + mark_failed, read_ledger's last record has
     kind 'failed' and carries berth, ticket (taken from the enqueued record), at, stderr and
     result_code byte-equal to what was passed.
  2. A FAILED BERTH STAYS OWED. pending() still returns the berth after any number of failed
     records, and stops returning it only after mark_deposited.
  3. AN EMPTY FAILURE IS REFUSED. mark_failed with an empty stderr or an empty result_code raises
     ValueError and appends nothing (the ledger is byte-identical).

    python3 cairn/tools/chain/proofs/test_the_ledger_records_a_failed_deposit.py   # exit 0 = green
"""
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"2b34b52f80f3": {"1": "a_failed_attempt_is_a_record",
                           "2": "a_failed_berth_stays_owed",
                           "3": "an_empty_failure_is_refused"}}

BERTH = "/fixture/2b34b52f80f3/packets/verdict-failed-deposit-fixture.json"
TICKET = "fixture2b34b5"
STDERR = ("DEPOSIT FAILED — %s STANDS PENDING on the ledger: VerdictRefused: verdict artifact "
          "refused — verdicts[0]: discriminating_observation must be a non-empty string" % BERTH)
RESULT_CODE = "VerdictRefused"


def _contract():
    """Bound at CALL time, so a hollow build that takes the subject away reds the teeth rather
    than crashing an import before the first one runs."""
    from cairn.tools.chain import verdict_contract
    return verdict_contract


def _enqueued_ledger(tmp: str) -> str:
    """A tmp ledger holding one enqueued record, written in the shape enqueue_verdict writes."""
    path = os.path.join(tmp, "verdict-deposits.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "enqueued", "berth": BERTH, "ticket": TICKET,
                             "at": "2026-10-10T00:00:00"}, sort_keys=True) + "\n")
    return path


def a_failed_attempt_is_a_record(tmp: str) -> None:
    vc = _contract()
    ledger = _enqueued_ledger(tmp)
    vc.mark_failed(BERTH, stderr=STDERR, result_code=RESULT_CODE, ledger_path=ledger)
    records = vc.read_ledger(ledger_path=ledger)
    assert len(records) == 2, records
    last = records[-1]
    assert last.get("kind") == "failed", last
    assert last.get("berth") == BERTH, last
    assert last.get("ticket") == TICKET, ("the ticket comes from the enqueued record", last)
    assert last.get("stderr") == STDERR, last
    assert last.get("result_code") == RESULT_CODE, last
    assert isinstance(last.get("at"), str) and last["at"].strip(), last


def a_failed_berth_stays_owed(tmp: str) -> None:
    vc = _contract()
    ledger = _enqueued_ledger(tmp)
    for n in range(3):
        vc.mark_failed(BERTH, stderr="%s (attempt %d)" % (STDERR, n), result_code=RESULT_CODE,
                       ledger_path=ledger)
        owed = [r.get("berth") for r in vc.pending(ledger_path=ledger)]
        assert owed == [BERTH], ("a failed berth stays owed after %d failed record(s)" % (n + 1),
                                 owed)
    kinds = [r.get("kind") for r in vc.read_ledger(ledger_path=ledger)]
    assert kinds == ["enqueued", "failed", "failed", "failed"], kinds
    vc.mark_deposited(BERTH, ["fixture-node-a"], ledger_path=ledger)
    assert vc.pending(ledger_path=ledger) == [], "only a deposited record closes the berth"


def an_empty_failure_is_refused(tmp: str) -> None:
    vc = _contract()
    ledger = _enqueued_ledger(tmp)
    before = Path(ledger).read_bytes()
    for stderr, result_code in (("", RESULT_CODE), ("   ", RESULT_CODE),
                                (STDERR, ""), (STDERR, "  "), (None, RESULT_CODE),
                                (STDERR, 3)):
        try:
            vc.mark_failed(BERTH, stderr=stderr, result_code=result_code, ledger_path=ledger)
        except ValueError:
            pass
        else:
            raise AssertionError("mark_failed accepted stderr=%r result_code=%r"
                                 % (stderr, result_code))
        assert Path(ledger).read_bytes() == before, (
            "a refused failure appended to the ledger (stderr=%r result_code=%r)"
            % (stderr, result_code))


TEETH = (a_failed_attempt_is_a_record, a_failed_berth_stays_owed, an_empty_failure_is_refused)


def main() -> int:
    failed = 0
    from cairn.tools.scratch.scratch import scratch_dir
    for tooth in TEETH:
        tmp = str(scratch_dir("cairn-chain-failed-deposit-"))
        try:
            tooth(tmp)
            print("  green %s" % tooth.__name__)
        except Exception as e:  # noqa: BLE001 — a tooth's every failure is a red, named
            failed += 1
            print("  RED   %s — %s: %s" % (tooth.__name__, type(e).__name__, e))
    print("%d passed, %d failed out of %d" % (len(TEETH) - failed, failed, len(TEETH)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

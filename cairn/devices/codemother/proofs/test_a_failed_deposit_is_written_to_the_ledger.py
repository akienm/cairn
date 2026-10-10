"""Proof for ticket 637d206be821 — codemother's drain writes each failed deposit to the ledger.

Akien, 2026-10-10: "we need to make the queue record stderr. and the result code for heavens
sake." Measured that day: every drain had refused verdict-20260815T141125-dd35ea1c8f7b and the
ledger held nothing but its enqueued line — the only trace was a stderr print in
skills/chart/live.py. The drain now renders that line ONCE, writes it to the ledger through the
chain tool's mark_failed, and carries it back in the drained entry for the printer.

One tooth per numbered falsifier clause, each over a fresh world (fixtures copied from
test_deposit.py's test_a_failed_deposit_stands_pending_and_is_named, not imported — a proof does
not reach into another proof):

  1. A FAILED DEPOSIT IS A RECORD. A drain over one enqueued berth whose deposit raises appends
     exactly one 'failed' record whose stderr starts 'DEPOSIT FAILED — <berth> STANDS PENDING on
     the ledger: ' and whose result_code is the raised class name; a second drain appends a second.
  2. THE ENTRY CARRIES WHAT WAS WRITTEN. The drained entry's stderr and result_code equal the
     record's.
  3. A LANDING WRITES NO FAILURE. A successful drain appends no 'failed' record.

DB tooth 3 needs the one-time provisioning (as test_deposit.py). Self-cleaning.

    python3 cairn/devices/codemother/proofs/test_a_failed_deposit_is_written_to_the_ledger.py
"""
from __future__ import annotations

import contextlib
import json
import os
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"637d206be821": {"1": "a_failed_deposit_is_a_record",
                           "2": "the_entry_carries_what_was_written",
                           "3": "a_landing_writes_no_failure"}}

PREFIX = "DEPOSIT FAILED — %s STANDS PENDING on the ledger: "

_SCRATCH = contextlib.ExitStack()
_HELD: list[str] = []


def _nexus() -> str:
    """This run's own nexus, minted on first use through tree.scratch_nexus()."""
    if not _HELD:
        from cairn.tools.tree.tree import scratch_nexus
        _HELD.append(_SCRATCH.enter_context(scratch_nexus("verdict")))
    return _HELD[0]


def make_root(tmp: str):
    """A synthetic world, as test_deposit.py's: a filed ticket, a claiming chain
    (hypothesize <- validate), two real instruments."""
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    os.makedirs(os.path.join(root, "proofs"))
    for name, body in (("splitter.sh", "echo 'splitter: 2 runs, 0 red'\nexit 0\n"),
                       ("phantom.sh", "echo 'phantom ref refused'\nexit 7\n")):
        with open(os.path.join(root, "proofs", name), "w") as fh:
            fh.write(body)
    tickets = os.path.join(tmp, "CairnCommons", "tickets")
    os.makedirs(tickets)
    with open(os.path.join(tickets, "sworn.json"), "w") as fh:
        fh.write("{}")
    berths = os.path.join(tmp, "berths")
    packets = os.path.join(berths, "0", "packets")
    os.makedirs(packets)
    hyp = os.path.join(packets, "hypothesize-20260729T000000-feedfeedfeed.json")
    with open(hyp, "w") as fh:
        json.dump({"hypotheses": [
            {"piece": "build the alpha splitter",
             "expect": "the splitter's teeth pass twice",
             "falsifier": "any tooth red on either run",
             "instrument": "python3 proofs/test_splitter.py, twice"},
            {"piece": "compose the settled machinery",
             "expect": "the composed door refuses a phantom ref",
             "falsifier": "a phantom ref berths",
             "instrument": "the door's own gate, fixture ref"}]}, fh)
    val = os.path.join(packets, "validate-20260729T000001-cafecafecafe.json")
    with open(val, "w") as fh:
        json.dump({"ticket": "sworn", "hypothesize_ref": hyp,
                   "criteria": [
                       {"claim": "the splitter is green twice",
                        "instrument": "the splitter's teeth, twice: `bash proofs/splitter.sh`",
                        "expect_exit": 0,
                        "covers": ["build the alpha splitter"]},
                       {"claim": "the door refuses the phantom",
                        "instrument": "bash proofs/phantom.sh",
                        "expect_exit": 7,
                        "covers": ["compose the settled machinery"]}]}, fh)
    return root, berths, val


def good_artifact(val):
    return {
        "ticket": "sworn",
        "validate_ref": val,
        "verdicts": [
            {"claim": "the splitter is green twice",
             "instrument": "the splitter's teeth, twice: `bash proofs/splitter.sh`",
             "outcome": "pass", "evidence": "exit 0 on both runs",
             "discriminating_observation": "reverted the fix; the same instrument exits 1"},
            {"claim": "the door refuses the phantom",
             "instrument": "bash proofs/phantom.sh",
             "outcome": "pass", "evidence": "VerdictRefused raised, tree untouched",
             "discriminating_observation": "removed the ref check; the phantom berths"},
        ],
        "dispositions": [
            {"piece": "build the alpha splitter",
             "expect": "the splitter's teeth pass twice",
             "disposition": "confirmed", "by": "exit 0 on both runs"},
            {"piece": "compose the settled machinery",
             "expect": "the composed door refuses a phantom ref",
             "disposition": "killed", "by": "the phantom berthed on run one"},
        ],
    }


def _berth_a_verdict(berths, artifact, stamp):
    path = os.path.join(berths, "0", "packets", "verdict-%s-feedfeedfeed.json" % stamp)
    with open(path, "w") as fh:
        json.dump(artifact, fh)
    return path


def _failing_world(tmp: str):
    """One enqueued berth whose deposit raises (an undispositioned verdict)."""
    from cairn.devices.codemother.machines.verdict.verdict import enqueue_verdict
    root, berths, val = make_root(tmp)
    ledger = os.path.join(tmp, "instance", "verdict-deposits.jsonl")
    bad = _berth_a_verdict(berths, dict(good_artifact(val), dispositions=[]), "20260729T050000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == bad
    return root, ledger, bad


def _drain(root, ledger, embed):
    from cairn.devices.codemother.deposit import drain_pending
    return drain_pending(root=root, nexus=_nexus(), embed=embed, ledger_path=ledger)


def _failed_records(ledger):
    from cairn.tools.chain.verdict_contract import read_ledger
    return [r for r in read_ledger(ledger_path=ledger) if r.get("kind") == "failed"]


def a_failed_deposit_is_a_record(tmp: str) -> None:
    root, ledger, bad = _failing_world(tmp)
    _drain(root, ledger, lambda text: [0.0, 0.0, 1.0])
    failed = _failed_records(ledger)
    assert len(failed) == 1, ("one drain, one failed record", failed)
    rec = failed[0]
    assert rec.get("berth") == bad, rec
    assert rec.get("ticket") == "sworn", rec
    assert isinstance(rec.get("stderr"), str) and rec["stderr"].startswith(PREFIX % bad), rec
    assert "undispositioned" in rec["stderr"], rec
    assert rec.get("result_code") == "VerdictRefused", rec
    _drain(root, ledger, lambda text: [0.0, 0.0, 1.0])
    assert len(_failed_records(ledger)) == 2, "a second drain is a second attempt, a second record"


def the_entry_carries_what_was_written(tmp: str) -> None:
    root, ledger, bad = _failing_world(tmp)
    drained = _drain(root, ledger, lambda text: [0.0, 0.0, 1.0])
    assert len(drained) == 1 and drained[0].get("still_pending") is True, drained
    rec = _failed_records(ledger)[-1]
    entry = drained[0]
    assert entry.get("stderr") == rec["stderr"], (entry, rec)
    assert entry.get("result_code") == rec["result_code"], (entry, rec)
    assert entry.get("stderr") == (PREFIX % bad) + entry["failed"], \
        ("the carried line is the one the printer prints today", entry)


def a_landing_writes_no_failure(tmp: str) -> None:
    from cairn.devices.codemother.machines.verdict.verdict import enqueue_verdict, pending
    root, berths, val = make_root(tmp)
    ledger = os.path.join(tmp, "instance", "verdict-deposits.jsonl")
    a = dict(good_artifact(val))
    a["verdicts"] = [dict(v, evidence=v["evidence"] + f" — landing [{_nexus()}]")
                     for v in a["verdicts"]]
    a["dispositions"] = [dict(d, by=d["by"] + f" — landing [{_nexus()}]")
                         for d in a["dispositions"]]
    art = _berth_a_verdict(berths, a, "20260729T060000")
    assert enqueue_verdict("sworn", berths_root=berths, ledger_path=ledger) == art
    drained = _drain(root, ledger, lambda text: [0.0, 1.0, 0.0])
    assert len(drained) == 1 and "deposited" in drained[0], drained
    assert "stderr" not in drained[0] and "result_code" not in drained[0], drained
    assert pending(ledger_path=ledger) == [], "the landing closed the berth"
    assert _failed_records(ledger) == [], "a landing writes no failure"


TEETH = (a_failed_deposit_is_a_record, the_entry_carries_what_was_written,
         a_landing_writes_no_failure)


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    failed = 0
    tmps = []
    try:
        for tooth in TEETH:
            tmp = str(scratch_dir("cairn-codemother-failed-deposit-"))
            tmps.append(tmp)
            try:
                tooth(tmp)
                print("  green %s" % tooth.__name__)
            except Exception as e:  # noqa: BLE001 — a tooth's every failure is a red, named
                failed += 1
                print("  RED   %s — %s: %s" % (tooth.__name__, type(e).__name__, e))
    finally:
        _SCRATCH.close()
        for tmp in tmps:
            shutil.rmtree(tmp, ignore_errors=True)
    print("%d passed, %d failed out of %d" % (len(TEETH) - failed, failed, len(TEETH)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

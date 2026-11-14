"""Proof for ticket 535ca407cc73 — the verdict-deposit ledger closes a berth on librarian node addresses.

Measured 2026-11-14 on the 06db stack: under 06db (outline 4.3.1.5.1.1) a librarian node id is
an int address, and mark_deposited refused a full landing of four int ids as "landed no node
ids" because it accepted only strings. The berth stood pending forever, and codemother's
test_deposit went red.

One tooth per numbered falsifier clause, each over a fresh ledger in a scratch directory:

  1. INT ADDRESSES CLOSE THE BERTH. mark_deposited with positive int addresses (a list, and a
     lone int) records them as given, and pending() stops returning the berth.
  2. A NON-ID IS STILL REFUSED. An empty list, 0, a negative int, True and a blank string each
     raise VerdictRefused and append nothing; a legacy non-blank string id still closes.

    python3 cairn/tools/chain/proofs/test_a_deposit_closes_on_node_addresses.py   # exit 0 = green
"""
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"535ca407cc73": {"1": "int_addresses_close_the_berth",
                           "2": "a_non_id_is_still_refused"}}

BERTH = "/fixture/535ca407cc73/packets/verdict-node-address-fixture.json"
ADDRS = [281474976710664, 281474976710665]  # the shape 06db mints: nodes tag 1 over a row


def _contract():
    """Bound at CALL time, so a hollow build that takes the subject away reds the teeth."""
    from cairn.tools.chain import verdict_contract
    return verdict_contract


def _enqueued_ledger(tmp: str) -> str:
    path = os.path.join(tmp, "verdict-deposits.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "enqueued", "berth": BERTH, "ticket": "fixture535ca407cc73",
                             "at": "2026-11-14T00:00:00"}, sort_keys=True) + "\n")
    return path


def int_addresses_close_the_berth(tmp: str) -> None:
    vc = _contract()
    ledger = _enqueued_ledger(tmp)
    rec = vc.mark_deposited(BERTH, ADDRS, ledger_path=ledger)
    assert rec["node_ids"] == ADDRS, rec
    assert vc.pending(ledger_path=ledger) == [], "a landing of int addresses closes the berth"
    other = os.path.join(tmp, "solo")
    os.makedirs(other)
    ledger2 = _enqueued_ledger(other)
    assert vc.mark_deposited(BERTH, ADDRS[0], ledger_path=ledger2)["node_ids"] == [ADDRS[0]]
    assert vc.pending(ledger_path=ledger2) == []


def a_non_id_is_still_refused(tmp: str) -> None:
    vc = _contract()
    ledger = _enqueued_ledger(tmp)
    before = Path(ledger).read_bytes()
    for bad in ([], [0], [-5], [True], [ADDRS[0], "  "], 0, True):
        try:
            vc.mark_deposited(BERTH, bad, ledger_path=ledger)
        except vc.VerdictRefused:
            pass
        else:
            raise AssertionError("mark_deposited accepted %r" % (bad,))
        assert Path(ledger).read_bytes() == before, "a refused landing appended (%r)" % (bad,)
    assert vc.mark_deposited(BERTH, ["legacy-node"], ledger_path=ledger)["node_ids"] == \
        ["legacy-node"], "a legacy string id still closes"


TEETH = (int_addresses_close_the_berth, a_non_id_is_still_refused)


def main() -> int:
    failed = 0
    from cairn.tools.scratch.scratch import scratch_dir
    for tooth in TEETH:
        tmp = str(scratch_dir("cairn-chain-node-address-"))
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

"""Proof for ticket a76447d28af9 — a deposit-ledger berth can be superseded by a later verdict.

Akien, 2026-10-10: "go ahead and cast the b577 repair ticket". Measured that day: the berth
verdict-20260815T141125-dd35ea1c8f7b predates the rule that made discriminating_observation
required (f8f8ff9d), so every drain refuses it, and pending() is keyed by berth — a new verdict
alone would leave the old berth owed forever. The ledger gains a fourth kind, ``superseded``,
naming the owed berth, the later berth that replaces it, and why; pending() reads it as an
answer. The replacing berth must already be owed for the same ticket, so a supersede never
retires an obligation without another one standing in its place.

One tooth per numbered falsifier clause, each over a fresh ledger in a tmp directory (never the
live one):

  1. A SUPERSEDE ANSWERS THE OLD BERTH. Enqueue old and new for ticket T, then
     mark_superseded(old, by=new, why='w'): the last record is kind 'superseded' carrying berth,
     by, ticket T, why 'w' and at; pending() returns [new] only.
  2. EVERY REFUSAL APPENDS NOTHING. Empty why; old not enqueued; old already deposited; old
     already superseded; by == old; by not enqueued; by enqueued for another ticket — each raises
     ValueError and leaves the ledger byte-identical.
  3. A FAILED BERTH CAN STILL BE SUPERSEDED. mark_failed records on old do not stop it being
     superseded, and pending() ignores the failed records either way.

    python3 cairn/tools/chain/proofs/test_a_berth_can_be_superseded.py   # exit 0 = green
"""
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"a76447d28af9": {"1": "a_supersede_answers_the_old_berth",
                           "2": "every_refusal_appends_nothing",
                           "3": "a_failed_berth_can_still_be_superseded"}}

OLD = "/fixture/a76447d28af9/packets/verdict-old-fixture.json"
NEW = "/fixture/a76447d28af9/packets/verdict-new-fixture.json"
OTHER = "/fixture/a76447d28af9/packets/verdict-other-ticket-fixture.json"
STRAY = "/fixture/a76447d28af9/packets/verdict-never-enqueued-fixture.json"
TICKET = "fixturea76447"
OTHER_TICKET = "fixtureother"
WHY = "w"


def _contract():
    """Bound at CALL time, so a hollow build that takes the subject away reds the teeth rather
    than crashing an import before the first one runs."""
    from cairn.tools.chain import verdict_contract
    return verdict_contract


def _ledger(tmp: str, *records: dict) -> str:
    """A tmp ledger holding ``records``, written in the shape the ledger's writers write."""
    path = os.path.join(tmp, "verdict-deposits.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(dict(r, at="2026-10-10T00:00:00"), sort_keys=True) + "\n")
    return path


def _enqueued(berth: str, ticket: str = TICKET) -> dict:
    return {"kind": "enqueued", "berth": berth, "ticket": ticket}


def a_supersede_answers_the_old_berth(tmp: str) -> None:
    vc = _contract()
    ledger = _ledger(tmp, _enqueued(OLD), _enqueued(NEW))
    vc.mark_superseded(OLD, by=NEW, why=WHY, ledger_path=ledger)
    records = vc.read_ledger(ledger_path=ledger)
    assert len(records) == 3, records
    last = records[-1]
    assert last.get("kind") == "superseded", last
    assert last.get("berth") == OLD and last.get("by") == NEW, last
    assert last.get("ticket") == TICKET, ("the ticket comes from the enqueued record", last)
    assert last.get("why") == WHY, last
    assert isinstance(last.get("at"), str) and last["at"].strip(), last
    owed = [r.get("berth") for r in vc.pending(ledger_path=ledger)]
    assert owed == [NEW], ("the superseded berth stops being owed; its replacement is", owed)


def every_refusal_appends_nothing(tmp: str) -> None:
    vc = _contract()
    cases = (
        ("empty why", (_enqueued(OLD), _enqueued(NEW)), OLD, NEW, "  "),
        ("old not enqueued", (_enqueued(NEW),), STRAY, NEW, WHY),
        ("old already deposited", (_enqueued(OLD), _enqueued(NEW),
                                   {"kind": "deposited", "berth": OLD, "node_ids": ["n0"]}),
         OLD, NEW, WHY),
        ("old already superseded", (_enqueued(OLD), _enqueued(NEW), _enqueued(OTHER),
                                    {"kind": "superseded", "berth": OLD, "by": OTHER,
                                     "ticket": TICKET, "why": WHY}),
         OLD, NEW, WHY),
        ("by == old", (_enqueued(OLD),), OLD, OLD, WHY),
        ("by not enqueued", (_enqueued(OLD),), OLD, STRAY, WHY),
        ("by enqueued for another ticket", (_enqueued(OLD), _enqueued(OTHER, OTHER_TICKET)),
         OLD, OTHER, WHY),
    )
    for i, (name, records, berth, by, why) in enumerate(cases):
        case_dir = os.path.join(tmp, "case%d" % i)
        os.makedirs(case_dir)
        ledger = _ledger(case_dir, *records)
        before = Path(ledger).read_bytes()
        try:
            vc.mark_superseded(berth, by=by, why=why, ledger_path=ledger)
        except ValueError:
            pass
        else:
            raise AssertionError("mark_superseded accepted the case: %s" % name)
        assert Path(ledger).read_bytes() == before, (
            "a refused supersede appended to the ledger: %s" % name)


def a_failed_berth_can_still_be_superseded(tmp: str) -> None:
    vc = _contract()
    ledger = _ledger(tmp, _enqueued(OLD), _enqueued(NEW))
    for n in range(2):
        vc.mark_failed(OLD, stderr="DEPOSIT FAILED — attempt %d" % n,
                       result_code="VerdictRefused", ledger_path=ledger)
    owed = [r.get("berth") for r in vc.pending(ledger_path=ledger)]
    assert owed == [OLD, NEW], ("failed records answer nothing", owed)
    vc.mark_superseded(OLD, by=NEW, why=WHY, ledger_path=ledger)
    owed = [r.get("berth") for r in vc.pending(ledger_path=ledger)]
    assert owed == [NEW], ("a failed berth is superseded like any other", owed)


TEETH = (a_supersede_answers_the_old_berth, every_refusal_appends_nothing,
         a_failed_berth_can_still_be_superseded)


def main() -> int:
    failed = 0
    from cairn.tools.scratch.scratch import scratch_dir
    for tooth in TEETH:
        tmp = str(scratch_dir("cairn-chain-superseded-berth-"))
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

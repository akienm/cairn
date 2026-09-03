"""Proof: THE DEPOSIT STANDS DOWNSTREAM OF A MOVE — and the berth door does not.

``judge_survey`` has three mouths and until 2026-08-17 only two were counted. The
BERTH DOOR keeps a flat address rule on purpose (at berth time every holding
resolves by definition, so a tolerance there would let a packet be berthed naming
an address that was already gone). ``inspector.survey_holdings_resolve`` disposes,
on the stated ground that it "alone stands downstream of a move". It does not:
``deposit_survey`` runs minutes to hours later, on the far side of the build the
packet was charted for, and it was re-running the door's flat rule.

Teeth a hollow build could not pass — and the first two are the ticket's falsifier,
BOTH HALVES, because half (a) alone is satisfied by deleting the judge:

  - (a) A holding whose address has a recorded successor DEPOSITS. The world is
    moved under a packet the real ``write_survey`` already admitted, so the fixture
    is one the WRITER produced and not one described from the reader's side.
  - (b) A holding that resolves to nothing and carries NO forwarding record is
    STILL REFUSED, in the original sentence. Same packet, same moved world, the
    forwarding order taken away — so the tooth isolates the tolerance itself.
  - THE BERTH DOOR IS UNCHANGED: in that same moved world ``validate_survey`` and
    ``write_survey`` still refuse. This is the tooth that goes red if the fix is
    applied one level too deep, and nothing else in the corpus would notice.
  - THE TOLERANCE IS NARROW: an empty ``sought`` beside a moved address still
    refuses. Only the holdings-resolve ADDRESS finding is downstream of anything.
  - THE PUBLIC NAME IS THE SAME ORDER: ``resolves_to`` and ``_resolves_to`` agree
    on every charted address in the live corpus — one body, two spellings.
  - THE LIVE CORPUS INVARIANT, asserted rather than snapshotted: no berth is
    refused at the deposit for an address that HAS a successor. The count of
    rescued berths is recorded as evidence and never asserted — it moves whenever
    somebody charts.

No database: the deposit's gate is proved directly, and ``deposit_survey`` is
proved to have passed it by watching it reach the NEXT check (the berth-exists
one) instead of the gate.

    python3 cairn/devices/codemother/machines/survey/proofs/test_deposit_survives_a_move.py
"""
from __future__ import annotations

import glob
import json
import os
import pytest
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import cairn.machines.build_inspector.inspector as inspector_mod
from cairn.machines.build_inspector.inspector import judge_survey, resolves_to
from cairn.devices.codemother.machines.survey.survey import (
    SurveyRefused, deposit_survey, validate_survey, validate_survey_at_deposit,
    write_survey,
)
from cairn.devices.tester.scratch import scratch_dir

TICKET = "a-deposit-stands-downstream-of-a-move"
CONSTRAIN_BERTH = ("/home/akien/.cairn/devices/chart/0/packets/"
                   "constrain-20260817T212124-e0bc2bbadd77.json")
# A live address that this voyage will not move, and its stand-in successor.
MOVES_FROM = "cairn/devices/codemother/machines/survey/survey.py"
MOVES_TO = "cairn/machines/build_inspector/inspector.py"
BERTHS = os.path.expanduser("~/.cairn/devices/chart/0/packets")


def base_packet():
    """A packet the REAL berth door admits — everything below moves the world out
    from under this, never the packet out from under the door."""
    return {
        "constrain_ref": CONSTRAIN_BERTH,
        "ticket": TICKET,
        "sought": ["the seat the deposit's gate takes"],
        "holdings": [{"what": "the deposit path itself", "address": MOVES_FROM}],
        "absences": [{"what": "a deposit-time tolerance anywhere in the six stages",
                      "measure": "grep over cairn/devices/codemother/machines/ "
                                 "--include=*.py for the successor order: 0 hits"}],
        "unknowns": [],
        "confidence": 0.8,
        "provenance": {"constrain_ref": "floor", "sought": "cc",
                       "holdings": "cc", "absences": "cc",
                       "unknowns": "cc"},
    }


class MovedWorld:
    """MOVES_FROM stops existing; optionally a ticket's forwarding order records
    where it went. Patches the inspector's own predicates, so the judge and the
    successor door see one consistent world — and restores them, because a proof
    that leaks a patched global poisons every test after it."""

    def __init__(self, tmp, *, forwarded: bool):
        self.tmp, self.forwarded = tmp, forwarded

    def __enter__(self):
        self._exists = inspector_mod.ref_exists
        self._default = inspector_mod._default_exists
        self._tickets = inspector_mod._TICKETS_ROOT
        real = self._exists

        def hidden(addr, *a, **k):
            return False if addr == MOVES_FROM else real(addr, *a, **k)

        inspector_mod.ref_exists = hidden
        inspector_mod._default_exists = hidden
        root = os.path.join(self.tmp, "repo")
        tickets = os.path.join(self.tmp, "CairnCommons", "tickets")
        os.makedirs(tickets, exist_ok=True)
        order = ({MOVES_FROM: {"to": MOVES_TO, "why": "fixture: the build moved it"}}
                 if self.forwarded else {})
        with open(os.path.join(tickets, TICKET + ".json"), "w") as fh:
            json.dump({"id": TICKET, "forwarding": order}, fh)
        inspector_mod._TICKETS_ROOT = root
        return self

    def __exit__(self, *exc):
        inspector_mod.ref_exists = self._exists
        inspector_mod._default_exists = self._default
        inspector_mod._TICKETS_ROOT = self._tickets
        return False


def expect_refusal(fn, needle):
    try:
        fn()
    except SurveyRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return str(err)
    raise AssertionError("expected a refusal naming %r, got none" % (needle,))


@pytest.fixture
def tmp():
    return str(scratch_dir("deposit_move_proof_"))


def test_the_fixture_is_one_the_writer_admits(tmp):
    """Before anything moves, the real door accepts it — so every tooth below is
    about the WORLD changing, never about a packet the writer would have refused."""
    berth = write_survey(base_packet(), instance_dir=os.path.join(tmp, "berths"))
    assert os.path.isfile(berth)
    assert validate_survey(base_packet()) is not None


def test_the_berth_door_keeps_the_flat_rule(tmp):
    """The asymmetry, stated as a decision on 2026-07-30 and preserved here: with a
    successor ON RECORD, the door still refuses. If this goes green the fix landed
    one level too deep and a packet can be berthed naming an address already gone."""
    with MovedWorld(tmp, forwarded=True):
        expect_refusal(lambda: validate_survey(base_packet()),
                       "names an address that does not resolve")
        expect_refusal(lambda: write_survey(base_packet(),
                                            instance_dir=os.path.join(tmp, "b2")),
                       "names an address that does not resolve")
        assert resolves_to(MOVES_FROM, TICKET) == MOVES_TO, \
            "the fixture's own premise: the successor IS on record"


def test_half_a_the_deposit_stands_downstream_of_a_move(tmp):
    """The moved holding deposits. Proved twice over: the gate returns the packet,
    and deposit_survey reaches its NEXT check instead of the gate's refusal."""
    with MovedWorld(tmp, forwarded=True):
        assert validate_survey_at_deposit(base_packet()) is not None
        # Past the gate is proved by the refusal that comes AFTER it.
        expect_refusal(lambda: deposit_survey(base_packet(), [1.0, 0.0, 0.0],
                                              berth_path=os.path.join(tmp, "no.json")),
                       "does not exist")


def test_half_b_a_dead_holding_with_no_forwarding_still_refuses(tmp):
    """Same packet, same moved world, no forwarding record — the original refusal,
    unchanged. Deleting the judge satisfies half (a) and fails here."""
    with MovedWorld(tmp, forwarded=False):
        assert resolves_to(MOVES_FROM, TICKET) is None
        expect_refusal(lambda: validate_survey_at_deposit(base_packet()),
                       "names an address that does not resolve")
        expect_refusal(lambda: deposit_survey(base_packet(), [1.0, 0.0, 0.0],
                                              berth_path=os.path.join(tmp, "no.json")),
                       "names an address that does not resolve")


def test_the_tolerance_is_only_the_address_finding(tmp):
    """A moved address beside an empty sought still refuses: an empty sweep is not
    downstream of anything, and the disposition must not launder the rest."""
    with MovedWorld(tmp, forwarded=True):
        packet = base_packet()
        packet["sought"] = []
        err = expect_refusal(lambda: validate_survey_at_deposit(packet), "sought")
        assert "does not resolve" not in err, \
            "the moved address was disposed; only the coverage lack should stand"
        packet = base_packet()
        packet["absences"] = [{"what": "no measure here", "measure": ""}]
        expect_refusal(lambda: validate_survey_at_deposit(packet), "measure")


def test_the_public_name_is_the_same_order():
    """One body, two spellings — over every charted address in the live corpus."""
    asked = 0
    for path in sorted(glob.glob(os.path.join(BERTHS, "survey-*.json"))):
        packet = json.load(open(path))
        tid = packet.get("ticket")
        for att in judge_survey(packet):
            for frag in att["findings"]:
                address = (frag.get("evidence") or {}).get("address")
                if not isinstance(address, str):
                    continue
                asked += 1
                assert resolves_to(address, tid) == inspector_mod._resolves_to(address, tid), \
                    "the public name answers differently for %r" % (address,)
    assert asked, "the corpus asked nothing — this tooth measured no addresses"


def test_the_live_corpus_carries_no_moved_refusal():
    """THE INVARIANT, not the count: after the build, no berth is refused at the
    deposit FOR A FINDING whose address has a successor on record.

    Asserted per FINDING and not per berth, and that is a correction the corpus
    made to this tooth's first draft (2026-08-17). ``survey-20260803T112015``
    carries six dead holdings; five have successors, the sixth is
    ``cairn/chart/proofs``, which has none — the berth claims no ticket, so there
    is no hand-authored forwarding order to read, and git recorded no rename for
    a directory. So the berth is BOTH partly rescued and still refused, and a
    per-berth assertion calls that a defect. It is the disposition working: the
    five are gone from the refusal, the sixth still bites.

    The rescued/refused counts are printed as evidence and never asserted — they
    move whenever anybody charts, and a proof that asserts a snapshot goes red at
    the moment its own condition is satisfied."""
    paths = sorted(glob.glob(os.path.join(BERTHS, "survey-*.json")))
    assert paths, "no berthed survey packets — the corpus tooth measured nothing"
    still_refused, rescued, disposed = [], 0, 0
    for path in paths:
        packet = json.load(open(path))
        tid = packet.get("ticket")
        moved = [f["finding"] for att in judge_survey(packet)
                 for f in att["findings"]
                 if f["judge"] == "survey_holdings_resolve"
                 and resolves_to((f.get("evidence") or {}).get("address"), tid)]
        if moved:
            rescued += 1
            disposed += len(moved)
        try:
            validate_survey_at_deposit(packet)
        except SurveyRefused as err:
            still_refused.append((os.path.basename(path), str(err)))
            for finding in moved:
                assert finding not in str(err), (
                    "%s is still refused naming %r, whose address HAS a successor"
                    % (os.path.basename(path), finding))
    print("      evidence: %d berths, %d carried a moved address (%d findings "
          "disposed), %d still refused"
          % (len(paths), rescued, disposed, len(still_refused)))
    for name, err in still_refused:
        print("      still refused: %s — %s" % (name, err.splitlines()[-1].strip()[:100]))


def _main() -> int:
    tmp = str(scratch_dir("deposit_move_proof_"))
    checks = [
        (test_the_fixture_is_one_the_writer_admits, True),
        (test_the_berth_door_keeps_the_flat_rule, True),
        (test_half_a_the_deposit_stands_downstream_of_a_move, True),
        (test_half_b_a_dead_holding_with_no_forwarding_still_refuses, True),
        (test_the_tolerance_is_only_the_address_finding, True),
        (test_the_public_name_is_the_same_order, False),
        (test_the_live_corpus_carries_no_moved_refusal, False),
    ]
    try:
        for check, needs_tmp in checks:
            check(tmp) if needs_tmp else check()
            print(f"  PASS  {check.__name__}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("green — the deposit stands downstream of a move: a holding with a "
          "recorded successor deposits, a holding with none is still refused, the "
          "berth door keeps its flat rule, the tolerance reaches only the address "
          "finding, and the public successor name is the same order as the private")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

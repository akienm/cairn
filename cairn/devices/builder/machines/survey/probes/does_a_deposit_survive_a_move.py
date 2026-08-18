"""PROBE — does a survey deposit still survive a move, and is the disposition still WIRED?

Berth for the ``WATCHME(the_deposit_survives_a_move)`` that ticket
``a-deposit-stands-downstream-of-a-move`` carries. Berthed HERE, beside
``cairn/devices/builder/machines/survey/``, because that component owns the door
and the deposit this probe reads — a probe berths with what it watches, never with
the ticket it was compiled from (``cairn/tools/base/probe.py``).

THE EFFICACY QUESTION. ``judge_survey`` has three mouths. The berth door keeps a flat
address rule deliberately; the promotion sieve disposes through the successor order;
and the DEPOSIT — counted only on 2026-08-17 — runs on the far side of the build the
packet was charted for, so it stands downstream of a move too. The fix gives it the
sieve's tolerance and nothing more. Two ways that goes wrong later, and the watch is
ASYMMETRIC across them because they are not the same failure:

  - **The fix is present and did not take** — a berth the forwarding order FULLY
    rescues, still refused at the deposit. ONE is strong falsification.
  - **The door came loose** — a berth carrying an unrescuable dead holding that the
    deposit ACCEPTS. ONE is strong falsification of the bound, and it is the thing
    this ticket is fenced against: the tolerance may reach the address finding of the
    holdings judge and nothing else.

AND THE READING A COUNT CANNOT GIVE. Over a clean corpus a live fix and a reverted one
print the same two zeros, forever, looking healthy — the carrier-shaped hole the ticket
named at cast. So the probe also asks the question behaviorally: it builds a packet from
a real berth's own chain, points one holding at an address git RECORDS AS MOVED, and
checks that the berth door refuses it while the deposit's gate does not — then that
``deposit_survey`` itself reaches its next check instead of the door's refusal. No world
is patched and nothing is written: the berth path handed to ``deposit_survey`` does not
exist, which is the refusal the wiring is read from.

**A vacuous reading is a red, not a pass.** ``berths_read == 0`` clears nothing and is
reported as its own finding — the corpus this watch is denominated in going missing is
itself the news.

AUTHORITY: none, by construction. This probe deposits and pokes; re-opening the node is
the owner's act (Law 6).
"""

from __future__ import annotations

import glob
import json
import os

from cairn.tools.base.address import instance_path
from cairn.tools.base.probe import Probe, owning_ticket
from cairn.machines.build_inspector.inspector import judge_survey, resolves_to
from cairn.devices.builder.machines.survey.survey import (
    SurveyRefused, deposit_survey, validate_survey, validate_survey_at_deposit,
)

_TICKET = owning_ticket("a-deposit-stands-downstream-of-a-move")

# The berth corpus, resolved PER CALL through the one rung — a probe that froze the
# path at import would keep reading a root the instance had already left.
_BERTH_ENV = "CAIRN_CHART_BERTHS"

# An address git records as moved, used ONLY by the wiring check. Chosen because the
# rename is in the repo's own history rather than in any ticket's hand-authored map, so
# the check needs no ticket, no patching, and no writes.
_MOVED = "cairn/chart/constrain.py"

_NEEDLE = "names an address that does not resolve"


def _berths() -> list[str]:
    root = os.environ.get(_BERTH_ENV) or str(instance_path("chart", 0) / "packets")
    return sorted(glob.glob(os.path.join(root, "survey-*.json")))


def read_the_corpus() -> dict:
    """The two counts, per berth, over the live corpus. Unreadable packets are skipped
    and counted apart — a claim resting on a parse failure is worse than a smaller n."""
    refused_but_rescuable, dead_holding_accepted, unreadable = [], [], 0
    read = 0
    for path in _berths():
        try:
            packet = json.loads(open(path, encoding="utf-8").read())
        except (OSError, json.JSONDecodeError):
            unreadable += 1
            continue
        read += 1
        ticket = packet.get("ticket") if isinstance(packet, dict) else None
        findings = [f for f in judge_survey(packet)
                    if f.get("judge") == "survey_holdings_resolve"
                    and _NEEDLE in (f.get("finding") or "")]
        moved = [f for f in findings
                 if resolves_to((f.get("evidence") or {}).get("address"), ticket)]
        stuck = [f for f in findings if f not in moved]
        try:
            validate_survey_at_deposit(packet)
        except SurveyRefused as err:
            for finding in moved:
                if finding["finding"] in str(err):
                    refused_but_rescuable.append(
                        {"berth": os.path.basename(path),
                         "finding": finding["finding"],
                         "address": (finding.get("evidence") or {}).get("address")})
            continue
        for finding in stuck:
            dead_holding_accepted.append(
                {"berth": os.path.basename(path),
                 "finding": finding["finding"],
                 "address": (finding.get("evidence") or {}).get("address")})
    return {"berths_read": read, "unreadable": unreadable,
            "refused_but_rescuable": refused_but_rescuable,
            "dead_holding_accepted": dead_holding_accepted}


def read_the_wiring() -> dict:
    """Is the disposition still in the deposit's path? Asked of BEHAVIOUR, because the
    two counts above cannot tell a live fix from a reverted one over a clean corpus.

    Borrows a real berth's own chain so the packet is one the writer's chain admits, and
    points a single holding at an address git records as moved. Then three readings, all
    of which must hold: the berth door still refuses it (the asymmetry is intact), the
    deposit's gate does not (the tolerance is present), and ``deposit_survey`` reaches
    its NEXT check (the gate it calls is the deposit's, not the door's).

    THE TEMPLATE IS CHOSEN BY THE DOOR, not by shape. The first draft took the first
    berth carrying a ``constrain_ref`` and got ``survey-20260728T170650``, which the door
    refuses for a request-identity mismatch its chain has carried since 2026-08-03 — so
    ``door_refuses`` read False for a reason that had nothing to do with the address, and
    the wire read broken while it was fine. A fixture that agrees with the reader instead
    of the writer says nothing about the world: the template must be one the writer's own
    door ACCEPTS as it stands, so the moved address is the single lack introduced. Newest
    first, because a recent berth is likelier to satisfy the doors as they are today."""
    template = None
    for path in reversed(_berths()):
        try:
            packet = json.loads(open(path, encoding="utf-8").read())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(packet, dict):
            continue
        try:
            validate_survey(packet)
        except SurveyRefused:
            continue
        template = packet
        break
    if template is None:
        return {"wired": None,
                "why": "no berth the door accepts as it stands — nothing to borrow a "
                       "chain from, and the wire went unasked rather than read wrong"}
    probe_packet = dict(template)
    probe_packet["holdings"] = [{"what": "the wiring check's moved address",
                                 "address": _MOVED}]
    if resolves_to(_MOVED, probe_packet.get("ticket")) is None:
        return {"wired": None,
                "why": "the wiring check's own premise failed: git no longer records "
                       "%s as moved — pick another address" % _MOVED}
    readings = {}
    try:
        validate_survey(probe_packet)
        readings["door_refuses"] = False
    except SurveyRefused as err:
        readings["door_refuses"] = _NEEDLE in str(err)
    try:
        validate_survey_at_deposit(probe_packet)
        readings["deposit_gate_passes"] = True
    except SurveyRefused as err:
        readings["deposit_gate_passes"] = _NEEDLE not in str(err)
    try:
        deposit_survey(probe_packet, [1.0, 0.0, 0.0], berth_path=os.devnull + ".absent")
        readings["deposit_reaches_its_next_check"] = True
    except SurveyRefused as err:
        readings["deposit_reaches_its_next_check"] = _NEEDLE not in str(err)
    except Exception as err:  # noqa: BLE001 — an unexpected raise is a reading, not a crash
        readings["deposit_reaches_its_next_check"] = None
        readings["unexpected"] = "%s: %s" % (type(err).__name__, err)
    return {"wired": all(readings.get(k) is True for k in
                         ("door_refuses", "deposit_gate_passes",
                          "deposit_reaches_its_next_check")),
            "readings": readings}


def _survey(context: dict) -> dict:
    reading = context.get("deposit_move")
    if reading is None:
        reading = {"corpus": read_the_corpus(), "wiring": read_the_wiring()}
        context["deposit_move"] = reading
    return reading


def _trigger(now, context: dict) -> bool:
    """TRUE on any finding worth a poke: either falsification half, a broken wire, or a
    VACUOUS reading — a corpus that has gone to zero clears nothing and is itself news."""
    reading = _survey(context)
    corpus = reading["corpus"]
    return bool(corpus["refused_but_rescuable"]
                or corpus["dead_holding_accepted"]
                or reading["wiring"].get("wired") is not True
                or corpus["berths_read"] == 0)


def _enough(context: dict) -> bool:
    """CLEARED only by the WEAK-confirmation arm, and never by silence: a non-vacuous
    reading with both counts at zero AND the wire demonstrably live. The ticket asks for
    three consecutive such readings, at least one after a voyage that retired an address
    — the consecutiveness is the shim's to count across firings, so what this predicate
    can honestly answer is whether THIS reading is one of the three."""
    reading = _survey(context)
    corpus = reading["corpus"]
    return (corpus["berths_read"] > 0
            and not corpus["refused_but_rescuable"]
            and not corpus["dead_holding_accepted"]
            and reading["wiring"].get("wired") is True)


def _carry(context: dict) -> dict:
    """The verdict artifact's raw material, against THIS ticket's falsifier — the four
    readings the ticket's carrier names, the fourth being the one a count cannot give."""
    reading = _survey(context)
    return {"ticket": _TICKET,
            "corpus": reading["corpus"],
            "wiring": reading["wiring"],
            "against_falsifier":
                "(a) a berth whose holdings-resolve findings are all rescued by the "
                "successor order deposits without refusal; (b) a berth with a holding "
                "that resolves to nothing and carries no forwarding record is STILL "
                "refused. One counterexample to either half is strong falsification.",
            "vacuity": "berths_read == 0 is a RED, not a pass — it counts toward "
                       "neither arm and is reported as its own finding"}


# Honest as a placeholder, dishonest as a measurement — the same tracked debt every
# probe in the corpus carries: nothing pulses this shim yet, so loudness rides
# BaseShim.overdue() alone. Re-tune when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="the deposit was the third mouth of judge_survey and nobody counted it for "
        "eighteen days. Two ways the fix stops holding — present-but-not-taking, and "
        "the door coming loose — and over a clean corpus BOTH read as zero whether the "
        "disposition is wired or reverted. So this watch reports the two counts and "
        "asks the wire the question directly.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "survey", "kind": "efficacy", "ticket": _TICKET},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

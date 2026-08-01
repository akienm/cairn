"""PROBE — does /intent's door ever actually RED?

Berth for the WATCHME that ticket ``intent-becomes-a-learning-block`` carries. Berthed
here, beside ``skills/intent/``, because that is WHAT IT WATCHES; the ticket it was
compiled from lives in CairnCommons and this probe deliberately does not follow it there
(the rule in ``cairn/base/probe.py``: a probe berths with its subject).

THE EFFICACY QUESTION, and why it is this one. The migration's claim is that /intent
stopped being prose and became a gate. A gate that never refuses is not a gate — it is a
ceremony with an exit code, and it looks exactly like a working gate from the outside.
That is the coin-toss-green shape: green for the wrong reason, indistinguishable from
green for the right one. This is the ticket's falsifier (4), and it is the ONE clause the
build cannot answer about itself — proofs show the door CAN refuse; only live firings
show whether it EVER DOES while inputs are demonstrably imperfect.

WHY THIS IS MEASURABLE HERE AND WAS NOT AT THE EMISSION GATE. The sibling probe
``cairn/base/probes/does_optional_mean_never_carried.py`` had to swap its question
because a refusal at the chokepoint raises BEFORE anything is journaled — refusals leave
no trace a probe can read there. The Learning Block anatomy inverts exactly that: the
door TRACES ITS OWN SEND-BACK (falsifier (2) of the primitive), so a refusal is a durable
record. The denominator exists, which is the whole reason this question is askable.

TWO EDGES, NOT ONE. The watch is not cleared by refusals alone. The second edge is the
KILL — a firing that reached ``routed_out`` because nothing traced to the Telos. That
exit is the one that has been vanishing into conversation for the whole life of the
skill, and a migration that records only the greens and the refusals would have moved
the wrong half. Until both edges are demonstrated live, the migration is unfalsified,
not proven.

THE CORPUS IS THE LIVE TRACE ONLY, and that is enforced upstream rather than filtered
here: ``skills/intent/proofs/test_intent_skill.py`` and the seam's own proof fire against
INJECTED roots, and the seam's proof carries a tooth asserting the live trace is
byte-identical across a proof run. Without that, every proof run would deposit a refusal
into the exact counter this probe reads — the author's own test-fixtures answering the
author's own question, which is the home-field advantage the librarian measured and this
probe's sibling was bitten by.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that
re-opens a node whose intention did not work is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.base.probe import Probe

# Read the live roots the way the components themselves do — env first, default second —
# so an instance that moved its roots is measured where it actually lives, not where this
# file guessed. Resolved per call, never captured at import: a probe that froze the path
# at import time would keep reading a root the system had already left.
_TRACE_ENV = "CAIRN_LB_TRACE_ROOT"
_BERTH_ENV = "CAIRN_SKILL_BERTHS"
_TRACE_DEFAULT = Path.home() / ".cairn/devices/learning_block/0/traces"
_BERTH_DEFAULT = Path.home() / ".cairn/devices/skill_block/0/berths"

# The sample size below which "the door has never refused" says nothing. Three firings
# with no refusal is a plausible run of well-formed packets; twenty is a pattern — and
# twenty firings of the work loop's entry point is weeks of real work, not a sprint.
_ENOUGH = 20

_TICKET = "intent-becomes-a-learning-block"


def survey_the_firings() -> dict:
    """Count, over /intent's LIVE trace and berths: firings (the denominator), refusals,
    and kill exits. Reads instance-space files only — no device, no bus, no network — so
    the probe stays cheap enough to sit on a pulse.

    A corpus this probe cannot read is not a finding: an unreadable line is skipped
    rather than counted as evidence in either direction. The counts a probe reports are
    a claim (Law 3), and a claim resting on a parse failure is worse than a smaller n.
    """
    traces = Path(os.environ.get(_TRACE_ENV) or _TRACE_DEFAULT)
    berths = Path(os.environ.get(_BERTH_ENV) or _BERTH_DEFAULT)

    passes = refusals = findings = 0
    path = traces / "skill:intent.jsonl"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            event = rec.get("event")
            if event == "door_pass":
                passes += 1
            elif event == "send_back":
                refusals += 1
            elif event == "finding":
                findings += 1

    kills = 0
    for p in sorted((berths / "intent").glob("*.json")) if (berths / "intent").is_dir() else []:
        try:
            if json.loads(p.read_text(encoding="utf-8")).get("exit") == "routed_out":
                kills += 1
        except (OSError, json.JSONDecodeError):
            continue

    return {"firings": passes + refusals, "passes": passes, "refusals": refusals,
            "findings": findings, "kills": kills}


def _trigger(now, context: dict) -> bool:
    """TRUE when there have been enough firings to judge AND the door has never once
    refused. Both clauses are load-bearing: firing on a small corpus pokes the owner
    about noise, and firing while refusals exist pokes about a working gate."""
    s = context.get("firings") or survey_the_firings()
    return s["firings"] >= _ENOUGH and s["refusals"] == 0


def _enough(context: dict) -> bool:
    """CLEARED once BOTH edges are demonstrated live: the door has refused at least once,
    and at least one node has been killed at /intent with its finding recorded. At that
    moment the question is answered — the gate bites and the kill leaves a record — and a
    standing watch on a settled question is the re-derivation Law 1 refuses.

    NO SAMPLE-SIZE FLOOR HERE, deliberately, and the asymmetry against ``_trigger`` is the
    opposite of the sibling probe's bug rather than a repeat of it. That one could clear at
    n=1 while needing n=12 to fire, so it was guaranteed to retire before it could bite —
    because its clear was a claim ABOUT A POPULATION ('some author carries a watch'), which
    n=1 cannot support. This clear is a claim about an EXISTENCE ('this door has refused'),
    and one witnessed refusal settles an existence claim completely. A floor on an
    existence claim would not add rigor; it would just keep a watch armed after its
    question was answered.
    """
    s = context.get("firings") or survey_the_firings()
    return s["refusals"] >= 1 and s["kills"] >= 1


def _carry(context: dict) -> dict:
    """The datum that rides back: the counts against the ticket's own falsifier, and a
    POINTER to the ticket rather than a copy of it (Law 6 — the ticket is the commons')."""
    s = context.get("firings") or survey_the_firings()
    return {"finding": "/intent's door has never refused a firing",
            "counts": s,
            "ticket": _TICKET,
            "against_falsifier": "(4) the door never REDS across the first measurement "
                                 "window while inputs are demonstrably imperfect — a gate "
                                 "that cannot refuse is vacuous",
            "suggests": "back-edge intent-becomes-a-learning-block and ask which half is "
                        "true: either the contract is too loose to ever bite (fix the "
                        "charter's input_contract), or the firings are being assembled to "
                        "fit the door before they are fired, which is the skate the "
                        "migration was built to close, one layer up"}


# THE HORIZON, and the residual it does NOT cover. Same tracked debt as the sibling's: the
# unit is PULSES because the shim counts pulses, but nothing pulses this shim yet (the
# wall-clock backing that would call `beat` on a cadence is a filed edge in
# cairn/ground_loop/loop.py, not built), so today the loudness rides the READ-SIDE door
# (`BaseShim.overdue()`) alone. 1000 is honest as a placeholder and dishonest as a
# measurement, and MUST be re-tuned when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="does /intent's door ever actually RED? — a gate that cannot refuse is a ceremony "
        "with an exit code, and it is indistinguishable from a working gate until someone "
        "counts. Cleared only when BOTH edges are live: a refusal, and a recorded kill.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

"""PROBE — did making the watch OPTIONAL make it never carried?

Berth for the WATCHME that ticket ``watchme-emits-a-probe`` carries. Berthed here, beside
``cairn/base``, because that is WHAT IT WATCHES; the ticket it was compiled from lives in
CairnCommons and the probe deliberately does not follow it there.

THE EFFICACY QUESTION, and why it is this one. v1 measured a real failure: ``LEARNME`` sat in
the backbone, MANDATORY for every node, and carried NO GATE — so every voyage crossed it and
no voyage satisfied it. The fix inverts both halves: optional to carry, gated once carried.
That fix has an obvious way to fail, and it is the exact mirror of what it replaced — if
nobody ever CARRIES a watch, the gate never fires, and the system has traded a summons
satisfied by nobody for a summons carried by nobody. Same silence, opposite mechanism.

WHY NOT "does the emission gate fire in anger?" — the question this berth was first drafted
for, and the swap is a finding worth keeping. IT IS NOT MEASURABLE FROM THE RECORD, by the
gate's own correct design: a refusal raises BEFORE anything is journaled, so refusals leave
no trace anywhere a probe can read. Only passes are journaled. A probe aimed at "has it ever
bitten?" would answer from the half of the evidence that cannot contain a bite — precisely
the confident-hollow shape Law 3 refuses. The question below subsumes it anyway: if no v2
node carries a watch, the gate never fires at all, in anger or otherwise.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that re-opens
a node whose intention did not work is the OWNER's act at the register (Law 6).

OPEN AND NAMED, not glossed: whether any shim currently serves the ``harbor_master`` address
is UNMEASURED. A poke to an address nothing serves is recorded ``unwired`` by the shim rather
than lost, which is loud enough to find but is not the same as delivered. Wiring it is not
this ticket's rung; saying so out loud is.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.base.probe import Probe

_TICKETS = Path(__file__).resolve().parents[3].parent / "CairnCommons" / "tickets"

# The sample size below which the question cannot be answered at all. Four v2 tickets that all
# say "none, because X" is a plausible run of honest answers; twelve is a pattern.
_ENOUGH = 12

# The node this probe was compiled from. Excluded from its own corpus — see survey_the_corpus.
_OWNING_TICKET = "watchme-emits-a-probe"


def survey_the_corpus() -> dict:
    """Count, over tickets claiming a version whose vocabulary can carry a watch: how many
    CARRY one, and how many recorded "none, because X". Reads class-space files only — no
    device, no bus, no network, so the probe stays cheap enough to sit on a pulse.

    THE OWNING TICKET IS EXCLUDED, and that exclusion is the whole honesty of the count.
    Caught by this node's own live fire, 2026-07-30: the first pulse reported
    ``{carried: 1, eligible: 1}`` — and the one was ``watchme-emits-a-probe`` itself, the
    node that INVENTED the mechanism, counting its own participation as evidence that
    authors participate. That is home-field advantage as a measurement: the maximally
    motivated author is the one sample. The question is about OTHER authors, so the
    author is not in the corpus.
    """
    from cairn.base.watchme_spec import workflow_objects

    carried = declined = 0
    for p in sorted(_TICKETS.glob("*.json")):
        if p.name.startswith("_") or p.stem == _OWNING_TICKET:
            continue
        try:
            t = json.loads(p.read_text(encoding="utf-8"))
            state = t.get("state")
            if not isinstance(state, str) or "@v1:" in state:
                continue
            if workflow_objects(state):
                carried += 1
            elif isinstance(t.get("watchme"), str):
                declined += 1
        except Exception:  # noqa: BLE001 — a corpus this probe cannot read is not a finding
            continue
    return {"carried": carried, "declined": declined, "eligible": carried + declined}


def _trigger(now, context: dict) -> bool:
    """TRUE when the corpus is big enough to judge AND not one node has carried a watch. The
    two clauses are both load-bearing: firing on a small corpus would poke the owner about
    noise, and firing on "some carried" would poke about a working mechanism."""
    s = context.get("corpus") or survey_the_corpus()
    return s["eligible"] >= _ENOUGH and s["carried"] == 0


def _enough(context: dict) -> bool:
    """CLEARED once the corpus is big enough to judge AND some other node has carried a watch.
    At that moment the question is answered — optional does not mean never — and a standing
    watch on a settled question is the re-derivation Law 1 refuses. If the answer later goes
    bad again, that is a NEW watch a node carries deliberately, not this one silently resuming.

    THE CORPUS FLOOR IS ON BOTH CLAUSES SINCE 2026-07-30, and it was not before. This read
    ``return s["carried"] > 0`` — no floor at all — while ``_trigger`` next door required
    ``eligible >= _ENOUGH``. The asymmetry was fatal in the quiet direction: the watch could
    CLEAR at n=1 but could not FIRE until n=12, so it was guaranteed to retire before it
    could ever bite. This node's live fire proved it — ``enough`` returned True on the very
    first pulse, against a corpus of exactly one ticket, which was this one.

    Two independent bugs met at that line and either alone would have been enough: the
    corpus counted the owning ticket (fixed in ``survey_the_corpus``), and the clear had no
    sample-size floor (fixed here). A watch that clears before it can fire is the v1 failure
    wearing this node's own clothes — a summons crossed by everybody and satisfied by
    nobody — which is precisely what this probe exists to detect.
    """
    s = context.get("corpus") or survey_the_corpus()
    return s["eligible"] >= _ENOUGH and s["carried"] > 0


def _carry(context: dict) -> dict:
    """The datum that rides back: the counts, and the ticket the finding is against. A pointer
    to the ticket rather than a copy of it (Law 6 — the ticket is the commons', not ours)."""
    s = context.get("corpus") or survey_the_corpus()
    return {"finding": "no v2 node has carried a WATCHME",
            "counts": s,
            "ticket": "watchme-emits-a-probe",
            "against_falsifier": "optional to carry became never carried — the mirror of the "
                                 "v1 failure this node replaced",
            "suggests": "back-edge watchme-emits-a-probe to WATCHME and re-open the design: "
                        "either the default is not defaulting, or the spec is too expensive "
                        "to write"}


# THE HORIZON, and the residual it does NOT cover (falsifier clause (2), added 2026-07-30 at
# this node's own validate step). This watch cannot answer until the corpus reaches 12
# eligible v2 tickets — many voyages away — so it is exactly the shape clause (2) warns
# about: armed, correct, and silent for a long time. Without a declared horizon its silence
# would be indistinguishable from health forever, so it declares one.
#
# WHY A ROUND NUMBER AND NOT A DERIVED ONE: the unit is PULSES because the shim counts pulses
# and a clock is bounded OUT — but the wall-clock backing that would call ``beat`` on a
# cadence is a FILED EDGE, not built (cairn/ground_loop/loop.py header). So today nothing
# pulses this shim at all, no pulse-record is ever produced, and the loudness rides the
# READ-SIDE door (``BaseShim.overdue()``) alone. 1000 is "clearly a long standing" against
# any beat rate we would plausibly pick; it is honest as a placeholder and dishonest as a
# measurement, and it MUST be re-tuned when the beat becomes a real number. That re-tune is
# the tracked debt this comment exists to carry.
_HORIZON = 1000

PROBE = Probe(
    why="did making the watch OPTIONAL make it never carried? — the mirror failure of the "
        "LEARNME shape this node replaced, and the one way this design fails silently",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

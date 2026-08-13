"""PROBE — does /sorted's cast door ever actually RED, and does a refused cast recover?

Berth for the WATCHME that ticket ``sorted-becomes-a-learning-block`` carries. Berthed
here, beside ``skills/sorted/``, because that is WHAT IT WATCHES (the rule in
``cairn/tools/base/probe.py``: a probe berths with its subject).

THE EFFICACY QUESTION, two edges. The migration's claim is that casting stopped being
prose and became a gate. Edge one is the sibling's (``skills/intent/probes/``): a gate
that never refuses is a ceremony with an exit code — the vacuity question, falsifier
(2)'s hollow pass measured from the outside. Edge two is THIS ticket's own: the door
exists so a weaker model recovers by fix-and-refire — so a refusal that is never
followed by a berthed cast means the door bites but does not help, which is worse than
prose (all cost, no rescue). Until both edges are demonstrated live, the migration is
unfalsified, not proven.

RECOVERY IS MEASURED COARSELY AND SAYS SO: a ``send_back`` with any LATER ``door_pass``
in the same live trace. The trace does not carry a cast identity linking the refusal to
its refire (that would be the berth's job, and a refused firing has no berth by
construction), so this is an EXISTENCE floor, not a per-cast rate — labeled in the
carry, per Law 3.

THE CORPUS IS THE LIVE TRACE ONLY, enforced upstream: the door's own proof
(``skills/sorted/proofs/test_sorted_door.py``) fires against injected roots and carries
a tooth asserting the live trace is byte-identical across a proof run.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that
re-opens a node whose intention did not work is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

# Live roots read the way the components read them — env first, default second,
# resolved per call, never captured at import (the sibling's rule).
_TRACE_ENV = "CAIRN_LB_TRACE_ROOT"
_TRACE_DEFAULT = Path.home() / ".cairn/devices/learning_block/0/traces"

# The judgment floor for the vacuity edge. Casts are rarer than /intent firings —
# a dozen real casts is weeks of resolution pivots, enough to call "never refused"
# a pattern rather than a run of well-formed packets.
_ENOUGH = 12

_TICKET = owning_ticket("sorted-becomes-a-learning-block")


def survey_the_firings() -> dict:
    """Count, over /sorted's LIVE trace: firings (the denominator), refusals, passes,
    and whether any refusal was followed by a later pass (the recovery existence floor).
    Unreadable lines are skipped, never counted as evidence in either direction."""
    traces = Path(os.environ.get(_TRACE_ENV) or _TRACE_DEFAULT)
    passes = refusals = 0
    recovery = False
    path = traces / "skill:sorted.jsonl"
    if path.exists():
        seen_refusal = False
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
                if seen_refusal:
                    recovery = True
            elif event == "send_back":
                refusals += 1
                seen_refusal = True
    return {"firings": passes + refusals, "passes": passes,
            "refusals": refusals, "recovery_observed": recovery}


def _trigger(now, context: dict) -> bool:
    """TRUE when there have been enough casts to judge AND the door has never once
    refused — the vacuity poke. Both clauses load-bearing, as in the sibling."""
    s = context.get("firings") or survey_the_firings()
    return s["firings"] >= _ENOUGH and s["refusals"] == 0


def _enough(context: dict) -> bool:
    """CLEARED once BOTH edges are live: the door has refused at least once, and at
    least one later cast passed (fix-and-refire works). Existence claims, settled by
    one witness each — no sample-size floor, the sibling's reasoning verbatim."""
    s = context.get("firings") or survey_the_firings()
    return s["refusals"] >= 1 and s["recovery_observed"]


def _carry(context: dict) -> dict:
    s = context.get("firings") or survey_the_firings()
    return {"finding": "/sorted's cast door has never refused a firing",
            "counts": s,
            "counts_caveat": "recovery_observed is an existence floor (a send_back with "
                             "any later door_pass), not a per-cast rate — the trace "
                             "carries no cast identity by construction",
            "ticket": _TICKET,
            "against_falsifier": "(2)/(4) of the ticket: a door that cannot tell a "
                                 "reason from a sentence, or that never reds while casts "
                                 "are demonstrably imperfect, is the hollow pass rank 3 "
                                 "measured",
            "suggests": "back-edge sorted-becomes-a-learning-block and ask which half is "
                        "true: either the contract + judges are too loose to bite (tighten "
                        "the charter's input_contract or door.py's judges), or packets are "
                        "being assembled to fit the door before firing — the skate, one "
                        "layer up"}


# Same tracked debt as the siblings: nothing pulses the shim yet, so loudness rides
# BaseShim.overdue() alone; 1000 is a placeholder to re-tune when the beat is real.
_HORIZON = 1000

PROBE = Probe(
    why="does /sorted's cast door ever actually RED — and does a refused cast come back "
        "as a berthed one? A gate that cannot refuse is ceremony; a gate that refuses "
        "without rescue is worse than prose. Cleared only when both edges are live.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "sorted", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

"""PROBE — does the slate door ever actually RED, and does a refused close recover?

Berth for the WATCHME that ticket ``slate-compiles-from-the-world`` carries. Berthed
beside ``skills/saveslate/`` because that is what it watches.

THE EFFICACY QUESTION. The migration's claim is that the slate stopped being
unassisted synthesis: the heads check bites when a writer never looked at the world,
the ceiling bites when a slate grows past its measured line. A door whose checks
never fire on real closes is ceremony (the coin-toss-green shape); a door that
refuses without a later successful write bites without rescuing. Both edges must be
live before the migration is proven — the sibling probes' reasoning verbatim
(``skills/intent/probes/``, ``skills/sorted/probes/``).

RECOVERY IS AN EXISTENCE FLOOR, labeled: a ``send_back`` with any LATER
``door_pass`` in the live trace — the trace carries no close identity.

THE CORPUS IS THE LIVE TRACE ONLY, enforced upstream by the proofs' injected roots
and pinned by the proof's live-trace byte-compare tooth.

AUTHORITY: none. Deposits and pokes; the back-edge is the owner's act (Law 6).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_TRACE_ENV = "CAIRN_LB_TRACE_ROOT"
_TRACE_DEFAULT = Path.home() / ".cairn/devices/learning_block/0/traces"

# Slates are written roughly once a session — a dozen firings is weeks of closes,
# enough to call "never refused" a pattern.
_ENOUGH = 12

_TICKET = owning_ticket("slate-compiles-from-the-world")


def survey_the_firings() -> dict:
    traces = Path(os.environ.get(_TRACE_ENV) or _TRACE_DEFAULT)
    passes = refusals = 0
    recovery = False
    path = traces / "skill:saveslate.jsonl"
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
    s = context.get("firings") or survey_the_firings()
    return s["firings"] >= _ENOUGH and s["refusals"] == 0


def _enough(context: dict) -> bool:
    s = context.get("firings") or survey_the_firings()
    return s["refusals"] >= 1 and s["recovery_observed"]


def _carry(context: dict) -> dict:
    s = context.get("firings") or survey_the_firings()
    return {"finding": "/saveslate's door has never refused a close",
            "counts": s,
            "counts_caveat": "recovery_observed is an existence floor (a send_back with "
                             "any later door_pass), not a per-close rate",
            "ticket": _TICKET,
            "against_falsifier": "a heads check and a ceiling that never bite while real "
                                 "closes happen are ceremony — the vacuity question",
            "suggests": "back-edge slate-compiles-from-the-world: either the ceiling and "
                        "heads checks are set where nothing real ever lands (re-measure "
                        "the corpus), or packets are assembled to fit the door before "
                        "firing — the skate, one layer up"}


# Same tracked debt as the siblings: nothing pulses the shim; re-tune when the beat is real.
_HORIZON = 1000

PROBE = Probe(
    why="does the slate door ever actually RED — and does a refused close come back as "
        "a written slate? Cleared only when both edges are live.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "saveslate", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

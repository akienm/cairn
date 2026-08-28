"""PROBE — do the exit-gate fields actually fire, or is the contract hollow?

Berth for the WATCHME that ticket ``design-step-gains-gated-exits`` carries. Berthed
here, beside ``skills/design/``, because that is WHAT IT WATCHES; the ticket it was
compiled from lives in CairnCommons and this probe deliberately does not follow it
there (the rule in ``cairn/tools/base/probe.py``: a probe berths with its subject).

THE EFFICACY QUESTION. The charter added ``intentions_cleared`` and ``tickets_reviewed``
to the design door's input_contract, and the door enforces them. But a contract that
is enforced and never satisfied is a contract nobody sees — the field exists, the
door checks it, and every real design session either supplies the exemption ("none
checked" / "none reviewed") or supplies real names. The probe watches which: a berth
carrying only the exemption form on every firing is a gate that fires without gating,
and the sibling probe (``design_return_trip.py``) already tells you whether return
trips arrive at all.

TRIGGER AND CLEAR: the trigger fires when enough design berths exist to judge AND
none of them carry a REAL list (not an exemption) in either gate field — the gate
was added but has never done its actual work. Cleared once one berth carries a real
list in both fields on a return trip (entering_from: sorted:*), proving the gate
fires on the path it was built for.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_BERTH_ENV = "CAIRN_SKILL_BERTHS"
_BERTH_DEFAULT = Path.home() / ".cairn/devices/skill_block/0/berths"

_FLOOR = 6


def survey_gate_fields() -> dict:
    """Count, over /design's live berths: total openings, how many carry a real list
    (not the exemption string) in intentions_cleared, same for tickets_reviewed, and
    how many carry both on a return trip (entering_from: sorted:*)."""
    root = Path(os.environ.get(_BERTH_ENV) or _BERTH_DEFAULT)

    openings = 0
    real_intentions = 0
    real_tickets = 0
    both_on_return = 0

    for p in sorted((root / "design").glob("*.json")) if (root / "design").is_dir() else []:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        answers = rec.get("answers") or {}
        openings += 1

        ic = answers.get("intentions_cleared")
        has_real_ic = isinstance(ic, list) and len(ic) > 0

        tr = answers.get("tickets_reviewed")
        has_real_tr = isinstance(tr, list) and len(tr) > 0

        if has_real_ic:
            real_intentions += 1
        if has_real_tr:
            real_tickets += 1

        is_return = str(answers.get("entering_from", "")).strip().lower().startswith("sorted:")
        if has_real_ic and has_real_tr and is_return:
            both_on_return += 1

    return {"openings": openings, "real_intentions": real_intentions,
            "real_tickets": real_tickets, "both_on_return": both_on_return}


def _trigger(now, context: dict) -> bool:
    s = context.get("gate_fields") or survey_gate_fields()
    return s["openings"] >= _FLOOR and s["real_intentions"] == 0 and s["real_tickets"] == 0


def _enough(context: dict) -> bool:
    s = context.get("gate_fields") or survey_gate_fields()
    return s["both_on_return"] >= 1


def _carry(context: dict) -> dict:
    s = context.get("gate_fields") or survey_gate_fields()
    return {"finding": "the exit-gate fields (intentions_cleared, tickets_reviewed) have "
                       "never carried a real list in any design berth",
            "counts": s,
            "ticket": _TICKET,
            "against_falsifier": "a ticket routed back from /sorted goes through /design, "
                                 "both exit gates check, and the gate-evidence fields are "
                                 "visible in the berth with distinct values — unfalsified "
                                 "until one return trip carries them",
            "suggests": "if openings > 0 and real_intentions == 0, every session used the "
                        "exemption 'none checked' — the lab sweep is being skipped, not "
                        "enforced. Same for real_tickets == 0 with 'none reviewed'. The "
                        "gate fires but gates nothing."}


_TICKET = owning_ticket("design-step-gains-gated-exits")

_HORIZON = 1000

PROBE = Probe(
    why="do the exit-gate fields (intentions_cleared, tickets_reviewed) actually fire "
        "with real content, or does every design session use the exemption? — the door "
        "enforces the fields but enforcement is not efficacy; a gate that always passes "
        "the exemption is a gate that fires without gating.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)

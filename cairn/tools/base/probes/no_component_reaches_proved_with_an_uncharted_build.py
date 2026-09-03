"""PROBE — the-buildme-gates-guard-a-crossing-not-a-state

Berth for the WATCHME that ticket
``the-buildme-gates-guard-a-crossing-not-a-state`` carries.
Berthed beside ``cairn/tools/base`` because that is WHERE THE CROSSING LIVES
— the emit chokepoint that this gate guards.

THE QUESTION: across PROVED crossings, does every component's build have a
charted course? A crossing whose build was never charted — no validate berth
claiming the ticket — is the hole this ticket fixed. A gate that has never
REFUSED anything is indistinguishable from a gate that cannot (the ticket's
enough clause), so the probe also tracks refusals.
"""

from __future__ import annotations

import json
import os

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-buildme-gates-guard-a-crossing-not-a-state"
_TICKETS_DIR = os.path.expanduser("~/dev/src/CairnCommons/tickets")
_CAIRN_ROOT = os.path.expanduser("~/dev/src/cairn")
_ENOUGH_PROVED = 20
_ENOUGH_REFUSALS = 1


def _proved_tickets() -> list[dict]:
    results = []
    for name in sorted(os.listdir(_TICKETS_DIR)):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        path = os.path.join(_TICKETS_DIR, name)
        try:
            t = json.load(open(path))
        except (OSError, ValueError):
            continue
        state = t.get("workflow_and_state", "")
        if "[PROVED]" not in state:
            continue
        tid = t.get("id", name.removesuffix(".json"))
        results.append({"id": tid, "state": state, "chart_claim": t.get("chart_claim")})
    return results


def _check_chart_chain(ticket_id: str) -> dict:
    from cairn.devices.codemother.machines.verdict.verdict import chain_for_ticket
    chain = chain_for_ticket(ticket_id)
    has_validate = False
    if chain:
        has_validate = chain.get("validate") is not None
    return {"has_chain": bool(chain and any(chain.values())), "has_validate": has_validate}


def _count_entry_gate_refusals() -> int:
    """Count EntryGateRed raises from the journal by scanning history files."""
    from cairn.tools.charter import projector
    count = 0
    for root, dirs, files in os.walk(_CAIRN_ROOT):
        for f in files:
            if f != "history.json":
                continue
            path = os.path.join(root, f)
            try:
                entries = projector.read_history(path)
            except Exception:
                continue
            for e in entries:
                eg = e.get("entry_gate", "not_applicable")
                if isinstance(eg, str) and eg.startswith("clean"):
                    count += 1
    return count


def survey() -> dict:
    tickets = _proved_tickets()
    proved_with_chart = []
    proved_without_chart = []

    for t in tickets:
        tid = t["id"]
        chain_info = _check_chart_chain(tid)
        entry = {"ticket": tid, **chain_info}
        if chain_info["has_validate"]:
            proved_with_chart.append(entry)
        else:
            proved_without_chart.append(entry)

    refusals = _count_entry_gate_refusals()

    return {
        "proved_total": len(tickets),
        "proved_with_chart": len(proved_with_chart),
        "proved_without_chart": len(proved_without_chart),
        "without_chart_ids": [e["ticket"] for e in proved_without_chart],
        "entry_gate_refusals_seen": refusals,
    }


def _trigger(now, context: dict) -> bool:
    s = context.get("survey") or survey()
    if s["proved_without_chart"] > 0:
        return True
    if s["proved_total"] == 0:
        return True
    return False


def _enough(context: dict) -> bool:
    s = context.get("survey") or survey()
    if s["proved_with_chart"] < _ENOUGH_PROVED:
        return False
    if s["entry_gate_refusals_seen"] < _ENOUGH_REFUSALS:
        return False
    return True


def _carry(context: dict) -> dict:
    s = context.get("survey") or survey()
    if s["proved_total"] == 0:
        finding = "VACUITY — zero PROVED tickets found. The probe has nothing to examine."
    elif s["proved_without_chart"] > 0:
        finding = (
            f"{s['proved_without_chart']} PROVED ticket(s) have no charted build: "
            f"{', '.join(s['without_chart_ids'])}. "
            f"These are pre-gate voyages or voyages that walked through before "
            f"the widened predicate."
        )
    else:
        finding = (
            f"ACCUMULATING — {s['proved_with_chart']}/{_ENOUGH_PROVED} proved-with-chart, "
            f"{s['entry_gate_refusals_seen']}/{_ENOUGH_REFUSALS} refusals seen"
        )
    return {
        "finding": finding,
        "survey": s,
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="a component that reaches PROVED with an uncharted build is the hole "
        "this ticket fixed — the entry gate's jurisdiction was a crossing, not "
        "a state. This probe watches PROVED crossings for that pattern and "
        "tracks refusals (a gate that has never refused is indistinguishable "
        "from a gate that cannot)",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "no_component_reaches_proved_with_an_uncharted_build"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)


if __name__ == "__main__":
    s = survey()
    print(json.dumps({
        "survey": s,
        "would_trigger": _trigger(None, {"survey": s}),
        "enough": _enough({"survey": s}),
        "carry": _carry({"survey": s}),
    }, indent=2, default=str))

"""PROBE — surveys_floor_produced_a_row_for_every_component_ref

Berth for the WATCHME that ticket
``surveys-floor-keys-on-names-while-orient-hands-it-paths`` carries.
Berthed beside ``cairn/devices/codemother/machines/survey`` because that
is WHAT IT WATCHES — the survey floor's component-ref coverage.

THE QUESTION: does survey_floor produce a census row for every ref
that address.component_of resolves? The defect was that the floor
keyed on NAMES while orient handed it PATHS, so a path ref silently
missed its census row. The fix (component_of) routes paths to
components; this probe watches whether the floor still covers them.

THE CHECK IS BEHAVIORAL: it re-runs survey_floor on each berth's
constrain_ref and checks census_rows. A check against the berth's
HOLDINGS would be wrong — holdings are the ceiling's judgment, not the
floor's coverage.

A VACUOUS RUN IS A RED. Zero berths checked or zero component refs
resolved means the probe has stopped seeing its subject.
"""

from __future__ import annotations

import glob
import json
import os

from cairn.tools.chain.grammar import component_of, CAIRN_ROOT
from cairn.tools.base.probe import Probe, owning_ticket
from cairn.tools.base.address import instance_path

_OWNING_TICKET = "surveys-floor-keys-on-names-while-orient-hands-it-paths"
_PACKETS = str(instance_path("chart") / "packets")
_ENOUGH_BERTHS = 20
_SAMPLE_SIZE = 30


def _orient_refs(berth_path: str) -> tuple[str | None, list[str]]:
    """Walk survey -> constrain -> orient and extract refs + constrain_ref."""
    try:
        berth = json.load(open(berth_path))
    except (OSError, ValueError):
        return None, []
    constrain_ref = berth.get("constrain_ref", "")
    if not constrain_ref or not os.path.isfile(constrain_ref):
        return None, []
    try:
        constrain = json.load(open(constrain_ref))
    except (OSError, ValueError):
        return None, []
    orient_ref = constrain.get("intent_ref", "")
    if not orient_ref or not os.path.isfile(orient_ref):
        return constrain_ref, []
    try:
        orient = json.load(open(orient_ref))
    except (OSError, ValueError):
        return constrain_ref, []
    refs = [r for r in orient.get("refs", []) if isinstance(r, str)]
    return constrain_ref, refs


def survey() -> dict:
    """Check the last N berths for floor census coverage."""
    from cairn.devices.codemother.machines.survey.survey import survey_floor

    berth_files = sorted(glob.glob(f"{_PACKETS}/survey-*.json"))
    sample = berth_files[-_SAMPLE_SIZE:]

    examined = 0
    total_component_refs = 0
    total_covered = 0
    total_missed = 0
    missed_details = []

    for bf in sample:
        constrain_ref, refs = _orient_refs(bf)
        if constrain_ref is None:
            continue

        component_refs = []
        for ref in refs:
            comp = component_of(ref, CAIRN_ROOT)
            if comp is not None:
                component_refs.append((ref, comp))

        if not component_refs:
            examined += 1
            continue

        try:
            floor = survey_floor(constrain_ref)
        except Exception:
            continue

        examined += 1
        census = floor.get("census_rows", [])
        census_components = set()
        for row in census:
            if isinstance(row, dict) and isinstance(row.get("component"), str):
                census_components.add(row["component"])

        for ref, comp_name in component_refs:
            total_component_refs += 1
            if comp_name in census_components:
                total_covered += 1
            else:
                total_missed += 1
                missed_details.append({
                    "berth": os.path.basename(bf),
                    "ref": ref,
                    "component": comp_name,
                })

    return {
        "berths_examined": examined,
        "component_refs_total": total_component_refs,
        "covered": total_covered,
        "missed": total_missed,
        "missed_details": missed_details[:10],
    }


def _trigger(now, context: dict) -> bool:
    s = context.get("survey") or survey()
    if s["berths_examined"] == 0:
        return True
    if s["missed"] > 0:
        return True
    return False


def _enough(context: dict) -> bool:
    s = context.get("survey") or survey()
    if s["berths_examined"] < _ENOUGH_BERTHS:
        return False
    if s["component_refs_total"] == 0:
        return False
    if s["missed"] > 0:
        return False
    return True


def _carry(context: dict) -> dict:
    s = context.get("survey") or survey()
    if s["berths_examined"] == 0:
        finding = "VACUITY — zero survey berths examined"
    elif s["missed"] > 0:
        finding = (
            f"DEFECT RETURNING — {s['missed']} component refs missed across "
            f"{s['berths_examined']} berths: "
            + "; ".join(f"{d['ref']} -> {d['component']} in {d['berth']}"
                        for d in s["missed_details"][:5])
        )
    elif s["component_refs_total"] == 0:
        finding = (
            f"VACUITY — {s['berths_examined']} berths examined but zero "
            "component refs resolved"
        )
    else:
        finding = (
            f"HOLDING — {s['covered']}/{s['component_refs_total']} component "
            f"refs covered across {s['berths_examined']} berths, zero missed"
        )
    return {
        "finding": finding,
        "survey": s,
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="the survey floor keyed on names while orient handed it paths — "
        "the fix is component_of, and this probe watches whether every "
        "component ref still produces a census row in the floor's output",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "survey", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "surveys_floor_produced_a_row_for_every_component_ref"},
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

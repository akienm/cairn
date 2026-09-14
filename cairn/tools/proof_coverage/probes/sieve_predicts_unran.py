"""WATCHME probe: a_proof_that_binds_an_added_name_at_import_never_reaches_hollow.

The binding sieve (``proof_binds_its_subject_at_call_time``, ticket c5b6b128a376) claims to
red, at PROVEME and by line, every proof the hollow reading would otherwise report UNRAN for
a module-level import of something the build added. This probe measures the two instruments
AGAINST EACH OTHER in the wild: every hollow reading sealed on a standing validation since
the sieve was built (``evidence.hollow[ticket][file] == {"unreadable": [proofs]}`` is hollow's
UNRAN marker) is compared with what the sieve predicts for the same ticket today.

FIRES on the first UNRAN the sieve did not predict — the ticket's WRONG-INTENT clause: the
static walk missed a binding hollow caught, and the instrument belongs inside hollow as a
pre-flight import against the reverted world. ENOUGH once 20 hollow readings after the build
carry no unpredicted UNRAN: the sieve is then measured as hollow's front door, not assumed.
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.probe import Probe

SIEVE_BORN = "2026-09-14T15:00:00"
ENOUGH_READINGS = 20
_REPO = Path(__file__).resolve().parents[4]
_COMMONS = _REPO.parent / "CairnCommons"


def _hollow_readings() -> dict:
    """{ticket: {file: {"proofs": [...], "unran": [...]}}} from every standing validation's
    ``evidence.hollow`` — the reading ``cairn test --hollow --seal`` lands."""
    out: dict = {}
    for v in _REPO.rglob("validations/*.json"):
        if "__pycache__" in v.parts or ".git" in v.parts:
            continue
        try:
            doc = json.loads(v.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        records = doc if isinstance(doc, list) else [doc]
        for rec in records:
            if not isinstance(rec, dict):
                continue
            hollow = (rec.get("evidence") or {}).get("hollow") or {}
            for tid, reading in hollow.items():
                if not isinstance(reading, dict):
                    continue
                slot = out.setdefault(str(tid), {})
                for f, val in reading.items():
                    one = slot.setdefault(str(f), {"unran": set(), "sealed_on": set()})
                    one["sealed_on"].add(str(v.relative_to(_REPO)))
                    if isinstance(val, dict) and "unreadable" in val:
                        one["unran"].update(str(p) for p in (val.get("unreadable") or []))
    return out


def _measure(context: dict) -> dict:
    # Bound at call time: the sieve is this probe's subject, and a probe that crashed on
    # import when its subject was taken away would be the defect the sieve reds.
    from cairn.tools.base.crossings import buildme_crossing
    from cairn.tools.proof_coverage.proof_coverage import (
        load_tickets, proof_binds_its_subject_at_call_time)

    readings = _hollow_readings()
    tickets = {t["id"]: t for t in load_tickets(_COMMONS)}
    since, unpredicted, predicted_total = 0, [], 0
    for tid, files in readings.items():
        crossing = buildme_crossing(tid) or {}
        if (crossing.get("at") or "") < SIEVE_BORN:
            continue  # a build the sieve never saw: hollow was its only instrument
        since += 1
        ticket = tickets.get(tid)
        lacks = (proof_binds_its_subject_at_call_time(ticket, repo_root=_REPO) if ticket else [])
        predicted = {l["values"].get("file") or l["values"].get("in") for l in lacks}
        predicted_total += len(predicted)
        for f, one in files.items():
            if one["unran"] and f not in predicted:
                unpredicted.append({"ticket": tid, "file": f, "proofs": sorted(one["unran"]),
                                    "sealed_on": sorted(one["sealed_on"]),
                                    "sieve_predicted": sorted(p for p in predicted if p)})
    context.update({"readings_since_build": since, "readings_total": len(readings),
                    "predicted": predicted_total, "unpredicted": unpredicted})
    return context


def _trigger(now, context: dict) -> bool:
    _measure(context)
    return bool(context["unpredicted"])


def _carry(context: dict) -> dict:
    if "readings_since_build" not in context:
        _measure(context)
    n = len(context["unpredicted"])
    return {
        "readings_since_build": context["readings_since_build"],
        "readings_total": context["readings_total"],
        "sieve_predicted": context["predicted"],
        "unpredicted": context["unpredicted"][:20],
        "finding": (
            "%d hollow UNRAN reading(s) the binding sieve did not predict — the static walk "
            "missed a binding hollow caught; the WRONG-INTENT clause of ticket c5b6b128a376: "
            "the instrument moves into hollow as a pre-flight import against the reverted "
            "world" % n
        ) if n else (
            "every UNRAN in %d hollow reading(s) since the sieve was built was predicted by "
            "the sieve (%d binding(s) predicted in all)" % (context["readings_since_build"],
                                                             context["predicted"])
        ),
    }


def _enough(context: dict) -> bool:
    if "readings_since_build" not in context:
        _measure(context)
    return not context["unpredicted"] and context["readings_since_build"] >= ENOUGH_READINGS


PROBE = Probe(
    why="the binding sieve claims to be hollow's front door — every module-level binding "
        "of a build-added name red at PROVEME before hollow spends its budget to say UNRAN; "
        "a claim about what one instrument catches before another is measured by running "
        "both and counting what only the second saw.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)

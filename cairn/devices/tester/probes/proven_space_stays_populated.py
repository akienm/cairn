"""PROBE — does the proven-space fraction stay at what the settled rule predicts?

Berth for the WATCHME that ticket ``the-corpus-is-out-of-proven-space`` carries. Berthed
beside ``cairn/devices/tester`` because that is WHAT IT WATCHES: the validation_store's
``standing()`` reader, which the tester owns, over the census of every proof in class-space.

THE MEASUREMENT. Census every proof file under ``cairn/**/proofs/test_*.py``, call
``standing()`` on each, and report the fraction in proven-space. The census is the full
population — no sampling, no head/tail. Each not-proven proof carries its own why, which
``standing()`` itself writes: never sealed, fingerprint moved, no fingerprint recorded, or
red seal.

THREE TRIGGER CONDITIONS from the ticket spec, and only the first is measurable today:

  (a) A proof's seal TRAIL fails integrity — a Law 7 record-of-truth failure, reported
      separately, never folded into the staleness count. THIS ONE FIRES.

  (b) The standing fraction falls below what the settled rule predicts. THE RULE HAS NOT
      BEEN SETTLED YET — child (a) of the owning ticket (``what-proven-space-is-for``) is
      the design question, and until it is answered there is no threshold to compare
      against. When the rule IS written, the probe reads it from where it lives — never
      from a constant hardcoded here (the ticket says so explicitly).

  (c) A crossing was REFUSED for an unproven ``proven_by`` — the horizon condition, and the
      only evidence that the state has an actual cost. No refusal record for this probe to
      read exists yet.

WHAT ``enough`` CAN AND CANNOT MEASURE. The ticket says: "when at least one crossing has
been refused for an unproven proven_by AND the standing fraction has held at or above the
settled rule's prediction across that refusal." Both halves are gated on things that do not
exist yet. This probe says False honestly, names what it lacks, and will clear when both
arrive. This is not a failure — it is a probe armed before its ticket's design question was
answered, measuring what CAN be measured (the census) while the answer arrives.

AUTHORITY: none. This probe deposits and pokes; settling what proven-space IS for is
Akien's ruling and the ticket's child (a) (Law 6).

FILES ONLY — no device, no bus, no network, so it stays cheap enough to sit on a pulse.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_CLASS_SPACE = Path(__file__).resolve().parents[4]

_OWNING_TICKET = "the-corpus-is-out-of-proven-space"


def survey_the_corpus() -> dict:
    """Census every proof in class-space through standing().

    THE CENSUS IS THE FULL POPULATION, and the trail integrity check runs alongside it so a
    finding about integrity is never separated from the census that saw it. A file this probe
    cannot parse is skipped and reported — a probe that quietly treats an unreadable file as
    clean is the vacuous green its own subject matter is about.
    """
    from cairn.devices.tester.validation_store import standing, validations_path_for

    proofs = sorted(_CLASS_SPACE.glob("**/proofs/test_*.py"))
    proofs = [p for p in proofs if "__pycache__" not in str(p)]

    total = 0
    in_proven = 0
    not_proven: list[dict] = []
    trail_integrity: list[dict] = []
    unreadable: list[str] = []

    for p in proofs:
        rel = os.path.relpath(p, _CLASS_SPACE)
        total += 1

        vpath = validations_path_for(str(p))
        if os.path.exists(vpath):
            try:
                data = json.loads(Path(vpath).read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    trail_integrity.append({
                        "proof": rel,
                        "trail": os.path.relpath(vpath, _CLASS_SPACE),
                        "failure": "validations file is not a list",
                    })
            except Exception as err:  # noqa: BLE001
                trail_integrity.append({
                    "proof": rel,
                    "trail": os.path.relpath(vpath, _CLASS_SPACE),
                    "failure": str(err),
                })
                unreadable.append(rel)
                continue

        s = standing(str(p))
        if s.get("proven"):
            in_proven += 1
        else:
            why = s.get("why", "?")
            if "does not exist" in why:
                cat = "never_sealed"
            elif "fingerprint" in why.lower() and ("moved" in why.lower()
                                                    or "unknowable" in why.lower()):
                cat = "fingerprint_stale"
            elif "not pass" in why:
                cat = "red_seal"
            else:
                cat = "other"
            not_proven.append({"proof": rel, "category": cat, "why": why})

    fraction = in_proven / total if total else 0.0
    by_category: dict[str, int] = {}
    for entry in not_proven:
        by_category[entry["category"]] = by_category.get(entry["category"], 0) + 1

    return {
        "total": total,
        "in_proven": in_proven,
        "fraction": fraction,
        "not_proven": not_proven,
        "not_proven_by_category": by_category,
        "trail_integrity_failures": trail_integrity,
        "unreadable": unreadable,
    }


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE when any trail fails integrity (condition a).

    Conditions (b) and (c) are gated on the settled rule and a refusal record, neither of
    which exists yet. This probe triggers on the one condition it can measure TODAY: a
    validation trail that does not parse or carries a non-dict entry is a Law 7
    record-of-truth failure.
    """
    s = _corpus(context)
    return bool(s["trail_integrity_failures"])


def _enough(context: dict) -> bool:
    """CANNOT CLEAR YET — both halves of the enough clause are gated.

    The ticket says: "when at least one crossing has been refused for an unproven proven_by
    AND the standing fraction has held at or above the settled rule's prediction." The rule
    does not exist (ticket child (a): what-proven-space-is-for) and no refusal record exists
    for this probe to read. This probe clears when both arrive and the conditions are met.
    """
    return False


def _carry(context: dict) -> dict:
    s = _corpus(context)
    parts = []
    if s["trail_integrity_failures"]:
        parts.append(f"{len(s['trail_integrity_failures'])} trail(s) fail integrity — "
                     f"Law 7 record-of-truth failure")
    parts.append(f"{s['in_proven']}/{s['total']} in proven-space "
                 f"({s['fraction'] * 100:.1f}%)")
    for cat, count in sorted(s["not_proven_by_category"].items(), key=lambda x: -x[1]):
        parts.append(f"{count}x {cat.replace('_', ' ')}")

    return {
        "finding": "; ".join(parts),
        "total_proofs": s["total"],
        "in_proven_space": s["in_proven"],
        "fraction": s["fraction"],
        "not_proven_by_category": s["not_proven_by_category"],
        "trail_integrity_failures": s["trail_integrity_failures"],
        "rule_settled": False,
        "refusal_observed": False,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "clause (2): the number raised by weakening standing() — "
                             "this census runs the real standing() over every proof, so a "
                             "weakened reader would show up as a fraction that moved without "
                             "a code change behind it; clause (3): broken trails re-sealed "
                             "rather than diagnosed — the trail-integrity section names them "
                             "separately so the consumer sees what would be overwritten",
        "suggests": "settle what proven-space is for (ticket child (a)) — until the rule "
                    "exists this probe measures the census but cannot compare it against a "
                    "threshold and enough cannot clear; the trail-integrity failures "
                    "(ticket child (b)) are the louder and independent defect",
    }


_HORIZON = 1000

PROBE = Probe(
    why="the corpus has most of its proofs outside proven-space and no rule says what the "
        "number should be — the census is measured but the question of what it means is "
        "this ticket's own open design question (child (a): what-proven-space-is-for)",
    trigger=_trigger,
    to="tester",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_corpus()
    print(json.dumps({
        "census": {
            "total": s["total"],
            "in_proven": s["in_proven"],
            "fraction": s["fraction"],
            "not_proven_by_category": s["not_proven_by_category"],
            "trail_integrity_failures": s["trail_integrity_failures"],
        },
        "would_trigger": _trigger(None, {"corpus": s}),
        "enough": _enough({"corpus": s}),
    }, indent=2, default=str))

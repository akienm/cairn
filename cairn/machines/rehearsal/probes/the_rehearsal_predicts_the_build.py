"""WATCHME probe: the_rehearsal_predicts_the_build.

Ticket cf80bdb57205's claim is that a clean rehearsal — three cold reads by the cheapest
reader agreeing on a build tree with zero gaps — PREDICTS the build: the proof that lands at
PROVED has a tooth for each step the tree named, and no tooth the tree did not foresee. The
machine writes that diff onto the clean record after PROVED (``cairn rehearse <ticket>
--proved <proofs>`` → ``divergence`` on the record). This probe counts those records over
the live commons: it never calls the reader and never runs a proof.

FIRES (WRONG-INTENT) once ten rehearsed tickets have reached PROVED with a divergence written
and FEWER than eight of them are empty both ways — the rehearsal did not predict the build
and the gate is holding crossings on a measurement that does not measure. ENOUGH once ten
have reached PROVED and at least eight are empty — the gate is trusted, and the learning
child over recurring gaps (D16) has its ten records. Nexus: the machine's own state.json
beside the code, per the ticket's watchme spec.
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.artifact import artifact as door
from cairn.tools.base.probe import Probe

ENOUGH_PROVED = 10
ENOUGH_CLEAN = 8
_REPO = Path(__file__).resolve().parents[4]


def _proved_records(commons: Path | None = None) -> list[dict]:
    """Every rehearsal record carrying a divergence — one per ticket that reached PROVED,
    the latest per ticket."""
    commons = commons or door.roots()["CairnCommons"]
    d = commons / "rehearsals"
    latest: dict[str, dict] = {}
    for p in sorted(d.glob("*.json")) if d.is_dir() else []:
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        dv = rec.get("divergence")
        if isinstance(dv, dict) and rec.get("ticket"):
            latest[rec["ticket"]] = {
                "ticket": rec["ticket"], "record": p.name,
                "steps_unproved": len(dv.get("steps_unproved") or []),
                "teeth_unforeseen": len(dv.get("teeth_unforeseen") or []),
                "matched": len(dv.get("matched") or []),
            }
    return list(latest.values())


def _measure(context: dict, commons: Path | None = None) -> dict:
    recs = _proved_records(commons)
    empty = [r for r in recs if not r["steps_unproved"] and not r["teeth_unforeseen"]]
    context.update({"proved": len(recs), "empty": len(empty), "records": recs})
    return context


def _trigger(now, context: dict) -> bool:
    _measure(context)
    return context["proved"] >= ENOUGH_PROVED and context["empty"] < ENOUGH_CLEAN


def _carry(context: dict) -> dict:
    if "proved" not in context:
        _measure(context)
    n, e = context["proved"], context["empty"]
    return {
        "proved": n, "empty_divergence": e, "records": context["records"][:20],
        "finding": (
            "%d of %d rehearsed tickets reached PROVED with a build the rehearsal predicted "
            "(fewer than %d) — the WRONG-INTENT clause of ticket cf80bdb57205: the gate holds "
            "crossings on a measurement that does not measure" % (e, n, ENOUGH_CLEAN)
        ) if n >= ENOUGH_PROVED and e < ENOUGH_CLEAN else (
            "%d rehearsed ticket(s) reached PROVED, %d with an empty divergence both ways" % (n, e)
        ),
    }


def _enough(context: dict) -> bool:
    if "proved" not in context:
        _measure(context)
    return context["proved"] >= ENOUGH_PROVED and context["empty"] >= ENOUGH_CLEAN


PROBE = Probe(
    why="a rehearsal that reads clean but does not predict the proof that lands is a gate "
        "holding crossings on noise; this counts, over the live records, how often the "
        "converged tree's steps and the built proof's teeth diverged, so the gate is trusted "
        "by measurement or found wrong by it.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "cairn/machines/rehearsal/state.json", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)

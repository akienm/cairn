"""PROBE — does yield_report account for every verdict value the store actually carries?

Berth for the WATCHME that ticket ``yield-report-names-its-refusals`` carries. Berthed beside
``cairn/devices/inference_domain`` because that is WHAT IT WATCHES: ``domain.yield_report`` is
the meter six live print sites read, and the one way this design fails silently is a new verdict
value appearing in ``inference_calls`` that the meter does not count — the identity
``calls == hits + misses + refused`` breaks quietly and a reader sees numbers that no longer sum.

THE EFFICACY QUESTION: does yield_report survive the next verdict value? The build proved the
identity holds over the three values that exist today. Whether it holds over a fourth is a fact
about the fourth, and the ticket's own falsifier names it: "the next verdict value added to
inference_calls SHOULD RED this tooth rather than pass it — an identity that survives a fourth
value is an identity that stopped checking anything."

TWO INVARIANTS:

  (a) THE IDENTITY HOLDS: calls == hits + misses + refused, read through yield_report's own
      numbers. A nonzero difference is the finding — the exact gap and the unaccounted verdicts
      name the shape of the failure.

  (b) EVERY VERDICT IS ACCOUNTED FOR: the distinct verdict values in the store past the era
      are a subset of {hit, miss, refused}. A new value is the finding, and it fires BEFORE
      the identity breaks — a value that hasn't reached the identity yet is a value that is
      being silently folded into `calls` and out of the sum.

FILES AND ONE STORE READ — the store through its one door. A DB this probe cannot reach raises
rather than reporting a clean zero.

AUTHORITY: none. This probe deposits and pokes; fixing the meter is the owner's act (Law 6).
"""

from __future__ import annotations

import json
from datetime import datetime

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "yield-report-names-its-refusals"

_ERA = datetime.fromisoformat("2026-08-18T01:25:01-06:00")

_ACCOUNTED_VERDICTS = {"hit", "miss", "refused"}

_ENOUGH_PER_VERDICT = 1


def _post_era(row: dict) -> bool:
    created = row.get("created")
    if not isinstance(created, datetime) or created.tzinfo is None:
        return False
    return created >= _ERA


def judge(rows: list[dict], meter: dict) -> dict:
    """The pure judgement: the identity, and the vocabulary.

    Separable from both reads so the proof can feed it fixtures.
    """
    post = [r for r in rows if _post_era(r)]
    verdict_counts: dict[str, int] = {}
    for r in post:
        v = r.get("verdict")
        if v is not None:
            verdict_counts[v] = verdict_counts.get(v, 0) + 1

    unaccounted = sorted(set(verdict_counts) - _ACCOUNTED_VERDICTS)
    accounted_sum = meter.get("hits", 0) + meter.get("misses", 0) + meter.get("refused", 0)
    calls = meter.get("calls", 0)
    difference = calls - accounted_sum

    return {
        "era": _ERA.isoformat(),
        "post_era_rows": len(post),
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "unaccounted_verdicts": unaccounted,
        "meter": {"calls": calls, "hits": meter.get("hits", 0),
                  "misses": meter.get("misses", 0),
                  "refused": meter.get("refused", 0)},
        "identity_difference": difference,
        "identity_holds": difference == 0,
    }


def survey_the_corpus() -> dict:
    """The live read — the store and the meter through their own doors."""
    from cairn.devices.db_domain import store
    from cairn.devices.inference_domain.domain import yield_report
    rows = store.read("inference_calls")
    meter = yield_report()
    return judge(rows, meter)


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE when the identity breaks OR an unaccounted verdict appears.

    The second fires before the first: a new verdict value is silently folded into
    `calls` and out of the sum, so the identity breaks one row later. Catching the
    vocabulary is how the probe sees it coming.
    """
    s = _corpus(context)
    return not s["identity_holds"] or bool(s["unaccounted_verdicts"])


def _enough(context: dict) -> bool:
    """CLEARED when the store carries all three accounted verdicts past the era, the identity
    holds, and no unaccounted verdict has appeared.

    The per-verdict floor is the non-vacuity tooth: an identity that holds over zero rows
    proves nothing, and an identity that holds with zero of one kind is holding by absence.
    """
    s = _corpus(context)
    if not s["identity_holds"]:
        return False
    if s["unaccounted_verdicts"]:
        return False
    for v in _ACCOUNTED_VERDICTS:
        if s["verdict_counts"].get(v, 0) < _ENOUGH_PER_VERDICT:
            return False
    return True


def _carry(context: dict) -> dict:
    s = _corpus(context)
    parts = []
    if not s["identity_holds"]:
        parts.append(f"calls ({s['meter']['calls']}) != hits ({s['meter']['hits']}) + "
                     f"misses ({s['meter']['misses']}) + refused ({s['meter']['refused']}) "
                     f"— difference is {s['identity_difference']}")
    if s["unaccounted_verdicts"]:
        parts.append(f"unaccounted verdict value(s) in the store: "
                     f"{', '.join(repr(v) for v in s['unaccounted_verdicts'])}")

    return {
        "finding": "; ".join(parts) or "the meter accounts for every verdict — identity holds",
        "meter": s["meter"],
        "identity_holds": s["identity_holds"],
        "identity_difference": s["identity_difference"],
        "verdict_counts": s["verdict_counts"],
        "unaccounted_verdicts": s["unaccounted_verdicts"],
        "window": {"era": s["era"], "post_era_rows": s["post_era_rows"]},
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's falsifier reds on (1) a reader computing hits + "
                             "misses and silently missing refusals, and on the horizon clause: "
                             "the next verdict value added should RED this, not pass it — an "
                             "identity that survives a fourth value stopped checking anything",
        "suggests": "read yield_report() in domain.py: a new verdict value needs its own "
                    "counter in the return dict and its own term in the identity, or the "
                    "meter collapses the new outcome into the total",
    }


_HORIZON = 1000

PROBE = Probe(
    why="yield_report accounts for hit, miss, and refused — the identity calls == hits + "
        "misses + refused is the thing that must hold, and the next verdict value is the "
        "thing that could break it",
    trigger=_trigger,
    to="inference_domain",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    s = survey_the_corpus()
    print(json.dumps({"corpus": s,
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2, default=str))

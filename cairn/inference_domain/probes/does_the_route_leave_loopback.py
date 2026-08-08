"""PROBE — the route is ruled to NEVER land a generate on loopback; does it hold live?

Berth for the WATCHME that ticket ``the-inference-proxy-is-a-rules-stack`` carries.
Berthed beside ``cairn/inference_domain`` because that is WHAT IT WATCHES: the ruling
(2026-08-08) says "the lowest cost answer is NEVER 127.0.0.1", route.py's never_routed
sieve enforces it at the shake, and the proofs enforce it on fixtures — but the one
place the rule can still fail is LIVE: a caller that pins an endpoint by hand, a code
path the routed default missed, a future edit that quietly re-teaches a literal. The
proxy's own cache (``inference_calls``, read through db_domain — the one door) records
every miss with its provenance, so the record of truth already carries the answer;
this probe reads it instead of instrumenting anything new (Law 1).

THE EFFICACY QUESTION: the ruled rule is NEVER, so the trigger floor is ONE — a single
post-era generate miss whose provenance.host names loopback is the finding, not a
trend to accumulate. The clear runs the other way and needs a denominator: zero
loopback rows across >= 12 post-era generate misses is the route demonstrably leaving
loopback under real traffic; zero-of-two is a young berth, not evidence.

THE ERA FLOOR — misses recorded before the routed resolver went LIVE were CORRECTLY
loopback (it was the only host the code in memory knew); counting them would fire the
probe at its own birth about a world that no longer exists. Live means the SERVING
process, not the disk: the first live fire of this voyage caught exactly that gap — a
web server started 15:07 held pre-route host.py for two hours after the code landed,
and its 17:19 generate landed on loopback. The floor is the restart that put the
routed default in the serving process, 2026-08-08T17:22:52-06:00. A date is
provenance here (when the build went live — a measured fact), not a tunable.

GENERATE ONLY, by the ruling's own words: the lived symptom was the ~100s CPU
generate; an embed miss on loopback is outside this watch's question (and nomic's
duty bound is the models stack's row, not this probe's).

AUTHORITY: none. This probe deposits and pokes; disabling a caller, fixing a rung, or
back-edging the ticket is the owner's act at the register (Law 6).
"""

from __future__ import annotations

import json
from datetime import datetime

from cairn.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-inference-proxy-is-a-rules-stack"

_ERA = datetime.fromisoformat("2026-08-08T17:22:52-06:00")

# The clear's denominator floor: below it, zero loopback rows is silence, not health.
# A hand-set constant is a learns-its-gates IOU, named at the owning ticket's horizon.
_ENOUGH = 12

_LOOPBACK_MARKS = ("127.0.0.1", "localhost")


def _is_post_era_generate_miss(row: dict) -> bool:
    created = row.get("created")
    if not isinstance(created, datetime) or created.tzinfo is None:
        return False            # a dateless row cannot be placed against the era
    if created < _ERA:
        return False
    try:
        return json.loads(row.get("canonical") or "{}").get("kind") == "generate"
    except ValueError:
        return False


def _on_loopback(row: dict) -> bool:
    host = ((row.get("provenance") or {}).get("host") or "")
    return any(mark in host for mark in _LOOPBACK_MARKS)


def judge_rows(rows: list[dict]) -> dict:
    """The pure judgement, separable from the read so the proof can feed it fixture rows:
    the post-era generate misses, and which of them landed on loopback (offenders carry
    canonical + created + provenance verbatim — the complete first report)."""
    misses = [r for r in rows
              if r.get("verdict", "miss") == "miss" and _is_post_era_generate_miss(r)]
    offenders = [{"canonical": r.get("canonical"),
                  "created": str(r.get("created")),
                  "provenance": r.get("provenance")}
                 for r in misses if _on_loopback(r)]
    return {"post_era_generate_misses": len(misses), "loopback_offenders": offenders}


def survey_the_corpus() -> dict:
    """The live read, THROUGH the one door (db_domain.store). A DB this probe cannot
    reach raises rather than reporting a clean zero — a silent 0/0 would read as both
    'no finding' and 'not yet enough', which is the quiet the watch exists to end."""
    from cairn.db_domain import store  # late: the probe module imports clean without a DB
    rows = store.read("inference_calls", where="verdict = 'miss'", params=())
    return judge_rows(rows)


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE on the FIRST offender — the ruled rule is NEVER, so one is the finding."""
    return bool(_corpus(context)["loopback_offenders"])


def _enough(context: dict) -> bool:
    """CLEARED when zero loopback rows stand across >= _ENOUGH post-era generate misses.
    The pair shares the one variable (offenders empty vs not) plus a denominator floor
    that makes the zero meaningful — mutually exclusive by construction."""
    s = _corpus(context)
    return not s["loopback_offenders"] and s["post_era_generate_misses"] >= _ENOUGH


def _carry(context: dict) -> dict:
    s = _corpus(context)
    # "which sieve let it out": re-shake the nest for each offender's request TODAY, so
    # the finding carries the current trace beside the historical row — the reader gets
    # the route's own explanation, not a re-run chore (complete on first pass).
    traces = []
    for off in s["loopback_offenders"]:
        try:
            req = json.loads(off["canonical"] or "{}")
        except ValueError:
            req = {}
        try:
            from cairn.inference_domain import route
            plan = route.route("generate", req.get("model"))
            traces.append({"canonical": off["canonical"],
                           "survivors": plan["survivors"], "trace": plan["findings"]})
        except Exception as e:  # noqa: BLE001 — the trace is best-effort context, the row is the finding
            traces.append({"canonical": off["canonical"], "trace_unavailable": str(e)})
    return {"finding": "a post-era generate miss landed on loopback — the ruled NEVER "
                       "(2026-08-08: 'the lowest cost answer is NEVER 127.0.0.1') was "
                       "crossed live while the proofs stayed green",
            "counts": {"post_era_generate_misses": s["post_era_generate_misses"],
                       "loopback_offenders": len(s["loopback_offenders"])},
            "offenders": s["loopback_offenders"],
            "todays_shake": traces,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket reds on 'a generate miss lands with "
                                 "provenance.host = 127.0.0.1 while hex.local answers' — "
                                 "this row is that observation",
            "suggests": "find the caller that pinned the endpoint (the provenance names "
                        "the host and, if routed, the provider and walk) — a bare "
                        "resolver build takes the routed default, so an offender almost "
                        "certainly passed endpoint= by hand or predates a healed call site"}


# Same placeholder horizon, same tracked debt, as the probes at cairn/base: the beat
# rate is not yet a real number; 1000 pulses is "clearly a long standing" until it is.
_HORIZON = 1000

PROBE = Probe(
    why="the ruling says a generate NEVER routes to 127.0.0.1; the proxy's own cache "
        "records where every miss actually landed — one post-era loopback generate is "
        "the rule failing live, and zero across enough traffic is it proven holding",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the live counts and what the pair would do with them now.
    s = survey_the_corpus()
    print(json.dumps({"corpus": {"post_era_generate_misses": s["post_era_generate_misses"],
                                 "loopback_offenders": s["loopback_offenders"]},
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2, default=str))

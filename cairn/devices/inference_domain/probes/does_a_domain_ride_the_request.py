"""PROBE — every request crossing the sole path is ruled to carry its domain; does it hold live?

Berth for the WATCHME that ticket ``the-domain-carries-the-inference-side`` carries.
Berthed beside ``cairn/devices/inference_domain`` because that is WHAT IT WATCHES: the domains
build says every resolved row's provenance carries a domain marker (the default row riding
silently for bare callers), and the seam's proofs enforce it on fixtures — but the one
place it can still fail is LIVE: a code path that bypasses the dressing, a future edit
that writes provenance without the stamp, a consumer reaching the cache some other way.
The proxy's own cache (``inference_calls``, read through db_domain — the one door) records
every call with its provenance, so the record of truth already carries the answer; this
probe reads it instead of instrumenting anything new (Law 1).

THE EFFICACY QUESTION, both ways. The trigger floor is ONE — a single post-era row whose
provenance lacks the domain marker means a request crossed the sole path undomained. The
clear runs the other way and needs TWO clauses: >= 12 post-era rows all carrying a marker,
AND at least one row carrying a NON-default domain named by a real caller (the librarian's
research stamp). The second clause is the non-vacuity tooth: default-stamping every row
cannot clear this watch — only a real consumer naming a real vertical can, because that is
the only way a non-default marker can appear (the seam never invents one). Without it,
"the verticals are real" (falsifier tells 5 and 6) would be cleared by machinery alone.

THE ERA FLOOR — rows recorded before the domained seam went LIVE correctly carry no
marker; counting them would fire the probe at its own birth about a world that no longer
exists. Live means the SERVING process, not the disk (the 2026-08-08 stale-process lesson:
a web server held pre-route host.py for two hours after the code was right on disk). The
floor is the restart that put the domain seam in the serving process,
2026-08-08T20:19:58-06:00 (ps lstart of the relaunched listener) — a measured
fact, not a tunable.

ALL VERBS, unlike the loopback probe: the marker must ride embeds and generates alike
(the seam stamps provenance on both paths, hit and miss), so every post-era row is in
this watch's jurisdiction.

AUTHORITY: none. This probe deposits and pokes; fixing a bypassing caller or back-edging
the ticket is the owner's act at the register (Law 6).
"""

from __future__ import annotations

import json
from datetime import datetime

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "the-domain-carries-the-inference-side"

_ERA = datetime.fromisoformat("2026-08-08T20:19:58-06:00")

# The clear's denominator floor: below it, all-marked is silence, not health.
# A hand-set constant is a learns-its-gates IOU, named at the owning ticket's horizon.
_ENOUGH = 12


def _default_domain() -> str:
    """The default row's name, read from the domains stack itself — the stack owns which
    row is default; a literal here would drift the day the stack changes."""
    from cairn.devices.inference_domain import route
    return route.domain_rows()["default"]


def _post_era(row: dict) -> bool:
    created = row.get("created")
    if not isinstance(created, datetime) or created.tzinfo is None:
        return False            # a dateless row cannot be placed against the era
    return created >= _ERA


def judge_rows(rows: list[dict], *, default_name: str | None = None) -> dict:
    """The pure judgement, separable from the read so the proof can feed it fixture rows:
    the post-era rows, which of them crossed undomained (offenders carry canonical +
    created + provenance verbatim — the complete first report), and which domains were
    observed riding (the clear's non-vacuity evidence)."""
    default = default_name if default_name is not None else _default_domain()
    post = [r for r in rows if _post_era(r)]
    offenders = [{"canonical": r.get("canonical"),
                  "created": str(r.get("created")),
                  "verdict": r.get("verdict"),
                  "provenance": r.get("provenance")}
                 for r in post if not (r.get("provenance") or {}).get("domain")]
    riding = sorted({d for r in post
                     if (d := (r.get("provenance") or {}).get("domain"))})
    return {"post_era_rows": len(post),
            "undomained": offenders,
            "domains_riding": riding,
            "non_default_riding": [d for d in riding if d != default]}


def survey_the_corpus() -> dict:
    """The live read, THROUGH the one door (db_domain.store). A DB this probe cannot
    reach raises rather than reporting a clean zero — a silent 0/0 would read as both
    'no finding' and 'not yet enough', which is the quiet the watch exists to end."""
    from cairn.devices.db_domain import store  # late: the probe module imports clean without a DB
    rows = store.read("inference_calls")
    return judge_rows(rows)


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE on the FIRST undomained post-era row — the rule is EVERY row, so one is the
    finding."""
    return bool(_corpus(context)["undomained"])


def _enough(context: dict) -> bool:
    """CLEARED when >= _ENOUGH post-era rows all carry the marker AND a non-default
    vertical has been seen riding — the two clauses of the ticket's own enough: the
    denominator makes the zero meaningful, the non-default makes it non-vacuous."""
    s = _corpus(context)
    return (not s["undomained"]
            and s["post_era_rows"] >= _ENOUGH
            and bool(s["non_default_riding"]))


def _carry(context: dict) -> dict:
    s = _corpus(context)
    return {"finding": "a post-era row crossed the sole path with no domain marker in its "
                       "provenance — the domains seam was bypassed or unwound while the "
                       "proofs stayed green",
            "counts": {"post_era_rows": s["post_era_rows"],
                       "undomained": len(s["undomained"])},
            "undomained": s["undomained"],
            "domains_riding": s["domains_riding"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket reds on 'a caller names a domain and the "
                                 "request arrives without it applied' and on the vertical "
                                 "not being real — an unmarked row is the seam not riding",
            "suggests": "the provenance names the host and path; find the writer that "
                        "reached inference_calls without domain.resolve's dressing — the "
                        "seam stamps every path it owns, so an unmarked row means a "
                        "second door"}


# Same placeholder horizon, same tracked debt, as the probes at cairn/tools/base: the beat
# rate is not yet a real number; 1000 pulses is "clearly a long standing" until it is.
_HORIZON = 1000

PROBE = Probe(
    why="the domains build says every request crosses the sole path carrying its vertical "
        "(the default riding silently); the proxy's own cache records what actually rode — "
        "one unmarked post-era row is the seam failing live, and enough marked traffic "
        "with a real non-default vertical is the domains proven real",
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
    print(json.dumps({"corpus": s,
                      "would_trigger": _trigger(None, {"corpus": s}),
                      "enough": _enough({"corpus": s})}, indent=2, default=str))

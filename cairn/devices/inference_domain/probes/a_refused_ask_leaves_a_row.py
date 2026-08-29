"""PROBE — a refused ask is supposed to leave a row now; does the write path ever actually fire?

Berth for the WATCHME that ticket ``a-refused-ask-leaves-a-row`` carries. Berthed beside
``cairn/devices/inference_domain`` because that is WHAT IT WATCHES: as of 2026-08-18 a raise
escaping ``resolver(request)`` inside ``domain.resolve()`` lands a ``verdict='refused'`` row
before it propagates, so the refusal rate of the system's only inference door is readable by
the same read that counts answers. The proofs enforce that on fixtures. The one place it can
still fail is LIVE, and it can fail in two opposite directions — which is why this watch has
teeth on both.

THE FINDING (trigger), three shapes, any one of which is one row:

  1. A post-era ``hit`` whose provenance carries a ``refused`` marker. A refusal replayed as
     an answer. This is the ticket's own red (3) and the worst outcome available here: it
     converts a loud error into a permanent quiet wrong answer, which is strictly worse than
     the defect being fixed. The read path selects ``verdict = 'miss'`` today, so this cannot
     happen — and that is exactly why it is watched: it holds by a WHERE clause nobody
     declared was load-bearing, and the next edit to the read path deletes it silently.
  2. A post-era ``refused`` row that does not name what refused it. The row exists and is
     useless; ticket red (2), a record of truth carrying an error quietly (Law 7).
  3. A post-era ``refused`` row carrying a non-zero cost, or an answer. A refusal that spends
     is a refusal being metered as work; ticket red (4), the fix breaking the path it was
     grafted beside.

THE CLEAR (enough), and its non-vacuity clause. Both halves come from the ticket verbatim:
at least one post-era row records a REFUSED ask, AND the post-era answered rows are all still
carrying real content and non-zero cost. The first half is what makes the clear mean anything
— **a refusal-recording path that has never recorded a refusal is exactly as unproven as the
guard this ticket descends from**, and a probe that cleared on zero refusals would be the
vacuous green this whole line of work exists to stop. The second half proves the graft did not
damage its neighbour.

THE ERA FLOOR — every one of the 2520 rows written before this build recorded only answers,
because refusals left no trace at all; counting them would fire the probe at its own birth
about a world that no longer exists. The floor is when the write path landed on disk,
2026-08-18T01:25:01-06:00.

THIS DOCSTRING CARRIED A FALSE CAVEAT UNTIL 2026-08-18, and the correction is left standing
here because the false version is the more plausible-sounding one. It claimed the ground loop
(pid 973171) was a long-running process making inference calls with a pre-build copy of
``resolve``, so a standing zero on clause one would be ambiguous between "nothing refused" and
"the busy caller runs yesterday's code", disambiguated only by a restart. THE GROUND LOOP MAKES
NO INFERENCE CALLS. Measured: ``grep -rn inference cairn/devices/cairn/machines/ground_loop/`` returns one hit
and it is prose in a provenance note — no code path — and no armed probe calls ``resolve``
either; probes READ rows, they do not ask. The caveat was reasoned from a stale-process lesson
cited in a neighbouring probe and never checked against the store that would have killed it.

WHAT ACTUALLY WRITES THESE ROWS, measured the same day over the last 400: 205 ``/api/embed``
calls to ``nomic-embed-text`` at ``domain: "research"`` — the graph-tree embedding in
``cairn/tools/tree/tree.py``, fired by ``chart counsel`` and ``chart learn`` and by the
librarian. Those run as short-lived ``python3 -m`` invocations that load fresh code every time,
so THERE IS NO STALE-CODE ERA PROBLEM ON THIS PATH AT ALL and nothing about this probe's clear
waits on any process being restarted. The 2026-08-08 stale-process lesson is real; it simply
does not reach this seam, and saying it did put a demand in front of the owner for nothing.

AND WHAT COUNTS FOR CLAUSE ONE, said plainly so a later reader of the clear is not misled.
The build's own live fire ARRANGED a refusal (a dial to 127.0.0.1:1) and it landed the first
refused row this system has ever recorded, at 2026-08-18T01:28:54-06:00, naming HostUnreachable.
That is a genuine measurement — the host genuinely refused — and it genuinely proves the write
path fires outside the fixture world, which is all clause one asks. It is NOT evidence that
organic traffic refuses at any rate; nothing here claims it is, and the refused_by_type counts
in the carry are what a reader should look at to tell arranged from organic.

AUTHORITY: none. This probe deposits and pokes; fixing a degraded write path or back-edging the
ticket is the owner's act at the register (Law 6).
"""

from __future__ import annotations

import json
from datetime import datetime

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "a-refused-ask-leaves-a-row"

_ERA = datetime.fromisoformat("2026-08-18T01:25:01-06:00")

# The clear's denominator floor for the answered half: below it, "all answers healthy" is
# silence, not health. A hand-set constant is a learns-its-gates IOU, named at the ticket's
# horizon — the same debt every probe in this folder carries.
_ENOUGH_ANSWERED = 12


def _post_era(row: dict) -> bool:
    created = row.get("created")
    if not isinstance(created, datetime) or created.tzinfo is None:
        return False            # a dateless row cannot be placed against the era
    return created >= _ERA


def _has_content(row: dict) -> bool:
    """Real content, judged the way the sibling non-final watch judges it: an answer that is
    there and is not empty. A row whose answer is ``{}`` or ``""`` counts as no content."""
    answer = row.get("answer")
    if answer in (None, "", {}, []):
        return False
    if isinstance(answer, dict):
        return any(v not in (None, "", {}, []) for v in answer.values())
    return True


def judge_rows(rows: list[dict]) -> dict:
    """The pure judgement, separable from the read so the proof can feed it fixture rows.

    Offenders carry canonical + created + provenance verbatim — the complete first report, so
    a reader never has to re-run this to find out which rows it meant.
    """
    post = [r for r in rows if _post_era(r)]
    refused = [r for r in post if r.get("verdict") == "refused"]
    answered = [r for r in post if r.get("verdict") in ("miss", "hit")]

    def _report(r, finding):
        return {"canonical": r.get("canonical"), "created": str(r.get("created")),
                "verdict": r.get("verdict"), "cost": r.get("cost"),
                "provenance": r.get("provenance"), "finding": finding}

    offenders = []
    offenders += [_report(r, "a refusal was served back as a cache hit")
                  for r in post
                  if r.get("verdict") == "hit" and (r.get("provenance") or {}).get("refused")]
    offenders += [_report(r, "a refused row does not name what refused it")
                  for r in refused if not (r.get("provenance") or {}).get("refused")]
    offenders += [_report(r, "a refused row was metered as work (cost, or an answer)")
                  for r in refused if float(r.get("cost") or 0) != 0.0 or _has_content(r)]

    hollow_answers = [_report(r, "an answered row carries no content or no cost — the graft "
                                 "damaged the path it was grafted beside")
                      for r in answered if not _has_content(r) or float(r.get("cost") or 0) == 0.0]

    by_type: dict[str, int] = {}
    for r in refused:
        name = (r.get("provenance") or {}).get("refused") or "(unnamed)"
        by_type[name] = by_type.get(name, 0) + 1

    return {"post_era_rows": len(post),
            "refused": len(refused),
            "refused_by_type": dict(sorted(by_type.items())),
            "answered": len(answered),
            "offenders": offenders,
            "hollow_answers": hollow_answers}


def survey_the_corpus() -> dict:
    """The live read, THROUGH the one door (db_domain.store). A DB this probe cannot reach
    raises rather than reporting a clean zero — a silent 0/0 would read as both 'no finding'
    and 'not yet enough', which is the quiet the watch exists to end."""
    from cairn.devices.db_domain import store  # late: the probe module imports clean without a DB
    return judge_rows(store.read("inference_calls"))


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE on the FIRST offending row. Each of the three shapes is a rule about EVERY row,
    so one is the finding — there is no rate here to be patient about."""
    s = _corpus(context)
    return bool(s["offenders"]) or bool(s["hollow_answers"])


def _enough(context: dict) -> bool:
    """CLEARED when the write path has actually FIRED at least once post-era, the answered
    rows beside it are still healthy at a meaningful denominator, and nothing is offending.
    The first clause is the non-vacuity tooth: zero refusals is not a pass."""
    s = _corpus(context)
    return (not s["offenders"]
            and not s["hollow_answers"]
            and s["refused"] >= 1
            and s["answered"] >= _ENOUGH_ANSWERED)


def _carry(context: dict) -> dict:
    s = _corpus(context)
    return {"finding": "the refusal-recording path is not holding live — either a refusal was "
                       "replayed as an answer, or a refused row cannot say what refused it, or "
                       "the graft damaged the answered path beside it",
            "counts": {"post_era_rows": s["post_era_rows"],
                       "refused": s["refused"],
                       "answered": s["answered"],
                       "offending": len(s["offenders"]),
                       "hollow_answers": len(s["hollow_answers"])},
            "refused_by_type": s["refused_by_type"],
            "offenders": s["offenders"],
            "hollow_answers": s["hollow_answers"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket reds on (2) a refused row indistinguishable from "
                                 "an answered one, (3) a refusal served back as a cache hit, "
                                 "and (4) the write changing what a successful ask stores — "
                                 "each offender shape above is one of those, live",
            "suggests": "read domain.resolve()'s except clause and _latest_valid_answer's WHERE. "
                        "A replayed refusal means the read path stopped selecting verdict='miss'; "
                        "an unnamed refusal means the provenance dict lost its 'refused' key; a "
                        "hollow answer means the try: block swallowed something it should not"}


# Same placeholder horizon, same tracked debt, as the sibling probes in this folder: the beat
# rate is not yet a real number; 1000 pulses is "clearly a long standing" until it is.
_HORIZON = 1000

PROBE = Probe(
    why="a raise inside resolver() now lands a row before it propagates, so the refusal rate "
        "of the system's only inference door is readable — one replayed refusal, one nameless "
        "refused row, or one damaged answer is the build failing live, and one real recorded "
        "refusal beside healthy answered traffic is it proven real",
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

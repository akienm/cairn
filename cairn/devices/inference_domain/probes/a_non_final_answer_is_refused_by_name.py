"""PROBE — the non-final frame is refused at the door; does anything ever get PAST it live?

Berth for the WATCHME that ticket ``a-non-final-answer-is-refused-by-name`` carries. Berthed
beside ``cairn/devices/inference_domain`` because that is WHAT IT WATCHES.

WHAT THE GUARD IS. ollama answers a NON-STREAMING ask with a frame from the STREAMING grammar
while a model is loading: HTTP 200, 96 bytes, empty role, empty content, ``done: false``, no
counters. Measured on hex 2026-08-18, and measured again live through this very code path the
same day — four asks during a load, four refusals; eight asks once the model was up, eight
answers. ``_post`` now refuses that frame by name (``HostNonFinal``) instead of letting it walk
three more checks and die at ``metered_cost`` complaining about token counters.

WHAT THIS PROBE ACTUALLY MEASURES, AND WHAT IT CANNOT — say the second part first, because it
is the honest half. **A REFUSAL LEAVES NO ROW.** ``domain.resolve`` writes to
``inference_calls`` only after ``resolver(request)`` returns; a raise means no write. So the
ticket's own ``enough`` — "the refusal has fired at least once on live traffic AND no successful
ask was ever refused by it" — is not readable from the ask log, and pretending otherwise would
be a watch that cannot bite dressed as one that can.

  - Clause one was satisfied AT BIRTH, by measurement rather than by this probe: four live
    refusals against a real cold hex, recorded in this voyage's verdict artifact. A probe that
    re-measured it would have to dial the host on a schedule, which is a poller wearing a
    watch's clothes.
  - Clause two is not measurable from this store at all, and the gap is a filed defect in the
    ticket's own watchme spec rather than something to paper over here (ticket owed: a refusal
    is invisible to the ask log).

So this probe watches THE FAULT RETURNING, which is what a standing watch is for: not "did the
guard fire" but "did anything the guard exists to stop ever get through anyway". A non-final
frame that got past ``_post`` would be CACHED — an answer with no text and a cost of zero,
stored under a canonical key and served to every future asker of the same question until its
horizon expires. That is strictly worse than the misdiagnosis this ticket started from, it is
recorded in a store this probe can read, and one is the finding.

THE ERA FLOOR. Rows recorded before the predicate landed cannot testify about it. The floor is
the netns seal that pinned the predicate, 2026-08-18T00:50:47-06:00. NOTE THE CAVEAT, because
it bit this system before (2026-08-08: a web server held pre-route host.py for two hours after
the code was right on disk): a process started before the floor still holds the old module.
That does not weaken the watch — a contentless zero-cost row is a fault under the old code and
the new one alike — but it does mean an offender may name a stale process rather than a hole in
the predicate, and the carry says so to whoever reads it.

CHAT ONLY, deliberately, and this is the same bound the fix itself was built under: the frame
was reproduced on ``/api/chat``. The predicate sits at ``_post`` and therefore covers all three
verbs by construction, but covering is not measuring, and a probe that claimed jurisdiction over
``/api/generate`` and ``/api/embed`` would be reporting on traffic whose failure shape nobody
has ever observed. An embed answer is a vector and has no ``text`` at all — judging it by this
rule would fire on every healthy row in the store.

AUTHORITY: none. This probe deposits and pokes; fixing a hole or back-edging the ticket is the
owner's act (Law 6).
"""

from __future__ import annotations

import json
from datetime import datetime

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "a-non-final-answer-is-refused-by-name"

# The netns seal that pinned the predicate — the moment before which no row can testify.
_ERA = datetime.fromisoformat("2026-08-18T00:50:47-06:00")

# The clear's denominator floor: below it, zero-offenders is silence rather than health. A
# hand-set constant is a learns-its-gates IOU, named at the owning ticket's horizon.
_ENOUGH = 20

_CHAT_PATH = "/api/chat"


def _post_era(row: dict) -> bool:
    created = row.get("created")
    if not isinstance(created, datetime) or created.tzinfo is None:
        return False            # a dateless row cannot be placed against the era
    return created >= _ERA


def _is_chat(row: dict) -> bool:
    return (row.get("provenance") or {}).get("path") == _CHAT_PATH


def _got_through(row: dict) -> bool:
    """THE SIGNATURE OF THE FRAME, and it is deliberately narrow — BOTH clauses, never either.

    The non-final frame carries an empty content AND no counters, so a row born of one has no
    text and a cost of zero. A model that genuinely replies with an empty string still spends
    tokens and lands a non-zero cost; a cheap-but-real answer still carries its text. Only the
    conjunction is the fault, and widening it to either half would fire this watch on healthy
    traffic — which is the failure mode the guard's own proofs are built against.
    """
    answer = row.get("answer")
    text = answer.get("text") if isinstance(answer, dict) else None
    cost = row.get("cost")
    return (not text) and (cost in (0, None))


def judge_rows(rows: list[dict]) -> dict:
    """The pure judgement, separable from the read so the proof can feed it fixture rows."""
    post = [r for r in rows if _post_era(r) and _is_chat(r)]
    offenders = [{"canonical": r.get("canonical"),
                  "created": str(r.get("created")),
                  "verdict": r.get("verdict"),
                  "cost": r.get("cost"),
                  "answer": r.get("answer"),
                  "provenance": r.get("provenance")}
                 for r in post if _got_through(r)]
    return {"post_era_chat_rows": len(post),
            "got_through": offenders,
            "clean": len(post) - len(offenders)}


def survey_the_corpus() -> dict:
    """The live read, THROUGH the one door (db_domain.store). A DB this probe cannot reach
    raises rather than reporting a clean zero — a silent 0/0 reads as both 'no finding' and
    'not yet enough', which is exactly the quiet a watch exists to end."""
    from cairn.devices.db_domain import store  # late: the module imports clean without a DB
    return judge_rows(store.read("inference_calls"))


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_corpus()


def _trigger(now, context: dict) -> bool:
    """TRUE on the FIRST cached contentless zero-cost chat answer — one is the finding, because
    one is already being served to every future asker of that question."""
    return bool(_corpus(context)["got_through"])


def _enough(context: dict) -> bool:
    """CLEARED when >= _ENOUGH post-era chat rows stand and NONE of them is contentless.

    The denominator is what makes the zero mean something: a guard over no traffic is unproven,
    not proven. The other half of the ticket's enough — that the refusal has bitten live — was
    settled by measurement at birth and is not re-derivable from this store; see the header.
    """
    s = _corpus(context)
    return not s["got_through"] and s["post_era_chat_rows"] >= _ENOUGH


def _carry(context: dict) -> dict:
    s = _corpus(context)
    return {"finding": "a chat answer with no text and no cost is STORED in inference_calls — a "
                       "non-final frame got past the _post guard and has been cached, which "
                       "means every future asker of that canonical question is served an empty "
                       "answer until its horizon expires",
            "counts": {"post_era_chat_rows": s["post_era_chat_rows"],
                       "got_through": len(s["got_through"]),
                       "clean": s["clean"]},
            "got_through": s["got_through"],
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket reds on a non-final frame reaching a caller as "
                                 "anything other than its own named error; a CACHED one is the "
                                 "worst shape of that — it stops being an error at all",
            "suggests": "two candidates, and they are told apart by the row's own timestamp "
                        "against the era: a process started before 2026-08-18T00:50:47-06:00 "
                        "still holding the pre-predicate host.py (check ps lstart of whatever "
                        "wrote it), or a real hole — a path into inference_calls that does not "
                        "cross _post. The provenance names the host and path; start there."}


# Same placeholder horizon, same tracked debt, as the probes beside it: the beat rate is not yet
# a real number; 1000 pulses is "clearly a long standing" until it is.
_HORIZON = 1000

PROBE = Probe(
    why="the predicate refuses ollama's non-final frame at the door, proved on fixtures and "
        "measured live (4 refusals cold, 8 answers warm, 2026-08-18); what a standing watch can "
        "still catch is the fault RETURNING — one contentless zero-cost chat row in the cache is "
        "a frame that got through and is now being served",
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

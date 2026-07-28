"""build_inspector/nexus.py — the GRAFT: the gate's learning path in the question-nexus shape.

Ticket: CairnCommons/tickets/build-inspector-nexus-graft.json (cast 2026-07-28 by
Akien's redefinition of the learning event — 'building ANYTHING should be the learning
event for the orient/inspector tickets'; charter filed edge (e)).

THE FIRE-PATH DOES NOT MOVE. The verdict is always HARDWARE (the 2026-07-28 ruling):
the FILTERS registry is replayable and changes only by installation; inspector.py never
imports this module, so the tree CANNOT be consulted at verdict-time — and the
emit-chokepoint wiring (transitions.py's build gate) is untouched, its own proof the
falsifier. What grafts is the GROWTH:

  deposit_failure(...)      — a failure into the inspector's own corpus tree
                              (``build_inspector_failures_nodes``, owner
                              ``build_inspector``, through chart's nexus verbs → the
                              librarian's tools → db_domain's one gate). The door demands
                              a DATED provenance: an undated failure could never become a
                              filter's Provenance (tooth 10 refuses a filter nobody was
                              taught by), so it may not take up residence pretending it
                              could.
  counsel_failures(...)     — the walk: prior failures and standing questions nearest a
                              new one, floor visible and labeled (inherited fences).
  propose_filter(...)       — the nexus loop's handoff: corpus walked, the draft left to
                              the ceiling, the ADMISSION gate named in the artifact —
                              tooth 10 + Akien's ratification + a new version of
                              inspector.py. Nothing here writes the registry (a gate
                              that could learn its own leniency is the measured
                              home-field risk; admission stays Akien's).
  seed_founding(embed)      — edge (a): the corpus's first residents are the CANDIDATE
                              FILTER QUESTIONS already filed — seeded but unbuilt is
                              exactly what a question nexus holds well. Idempotent.

Vectors arrive as DATA; the embed call is the caller's, through inference_domain (this
module never opens the host).
"""
from __future__ import annotations

from cairn.chart.tree import counsel, deposit_learning, propose

OWNER = "build_inspector"
CORPUS = "failures"

ADMISSION = (
    "installation only: the filter lands in inspector.py's FILTERS carrying Provenance "
    "naming the failure that taught it (tooth 10 refuses a filter nobody was taught by), "
    "joins the teeth, and is ratified by Akien — the verdict is always hardware, the "
    "registry never changes mid-fire, and the tree is never consulted at verdict-time.")

# Edge (a): the founding residents — the candidate filters already filed as questions.
# Each names the filter it would become; the proof pins that none is in FILTERS yet
# (seeded-but-unbuilt — when one lands by installation, its entry here records that).
FOUNDING_QUESTIONS = [
    {
        "content": "A transient absence written into a comment as intent ('on purpose') "
                   "outlives the absence and reads as design. What checkable shape "
                   "catches a stale 'on purpose' comment — a claim of intent whose "
                   "referent has since arrived?",
        "candidate_filter": "stale_on_purpose",
        "provenance": {"source": "cairn/build_inspector/intention+why.json filed edge "
                                 "(c) — device.py:36's transient-absence-written-as-intent",
                       "date": "2026-07-27"},
    },
    {
        "content": "A host-seam's implementation lives where git cannot see it, so its "
                   "seal EXPIRES — the host drifts with nothing in git changing. What "
                   "shape reds a host-seam whose re-runnable verify has not been "
                   "re-proven inside its horizon?",
        "candidate_filter": "host_seam_seal_expiry",
        "provenance": {"source": "cairn/build_inspector/intention+why.json filed edge "
                                 "(c) — CLAUDE.md's host-seam contract",
                       "date": "2026-07-27"},
    },
    {
        "content": "Every component's charter must answer 'how does this component "
                   "learn?' — 'it doesn't, because X' is valid; silence is not. What "
                   "shape reds a charter whose how_it_learns is absent or empty?",
        "candidate_filter": "charter_answers_learning",
        "provenance": {"source": "cairn/build_inspector/intention+why.json filed edge "
                                 "(c) — the learning-as-a-pattern IOU (CLAUDE.md rules "
                                 "awaiting physics)",
                       "date": "2026-07-27"},
    },
    {
        "content": "A nexus whose floor+tree fraction is not growing over N crossings is "
                   "not compiling — the ceiling is doing the floor's job forever, which "
                   "is the puppet. The dial reads the fraction; what N and what shape "
                   "make 'not growing' a checkable filter rather than a judgment?",
        "candidate_filter": "dial_trend_not_growing",
        "provenance": {"source": "CairnCommons/tickets/chart-tree.json filed edge (c) — "
                                 "the hardware ruling's falsifier, arriving at the gate "
                                 "through the gate's own admission door",
                       "date": "2026-07-28"},
    },
]


class GraftRefused(RuntimeError):
    """A growth-path ask this graft cannot honestly serve — refused loudly (Law 7)."""


def deposit_failure(content: str, vector, provenance: dict, *, conn=None) -> dict:
    """One failure (or standing question) into the corpus — dated at the door."""
    if not isinstance(provenance, dict) or not str(provenance.get("date", "")).strip():
        raise GraftRefused(
            f"deposit_failure: provenance {provenance!r} names no date — an undated "
            "failure can never become a filter's Provenance (tooth 10 demands the dated "
            "failure that taught it), so it may not join the corpus; nothing landed.")
    return deposit_learning(CORPUS, content, vector, provenance, owner=OWNER, conn=conn)


def counsel_failures(vector, *, k: int = 3, conn=None) -> dict:
    """The walk over prior failures and standing questions — floor visible, labeled."""
    return counsel(vector, nexus=CORPUS, owner=OWNER, k=k, conn=conn)


def propose_filter(failure: str, vector, *, conn=None) -> dict:
    """The loop's handoff for a failure that would seed a filter: corpus walked, draft
    left to the ceiling, admission gate carried in the artifact. Writes nothing."""
    return propose(failure, vector, nexus=CORPUS, owner=OWNER,
                   kind="filter", admission=ADMISSION, conn=conn)


def seed_founding(embed, *, conn=None) -> list[dict]:
    """Edge (a): the candidate questions take residence. ``embed`` is the injected seam
    (text → vector through inference_domain); reseeding dedups to no-ops."""
    return [
        deposit_failure(q["content"], embed(q["content"]),
                        {**q["provenance"], "candidate_filter": q["candidate_filter"]},
                        conn=conn)
        for q in FOUNDING_QUESTIONS
    ]

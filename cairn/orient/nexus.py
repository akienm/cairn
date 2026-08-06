"""orient/nexus.py — the GRAFT: orient's learning path in the question-nexus shape.

Ticket: CairnCommons/tickets/orient-nexus-graft.json (cast 2026-07-28 by Akien's
redefinition of the learning event — 'building ANYTHING should be the learning event
for the orient/inspector tickets'; charter filed edge (f)).

THE FIRE-PATH DOES NOT MOVE. Scans are HARDWARE (the 2026-07-28 ruling,
held-nexi-everywhere): deterministic, replayable, changed only by installation — and
orient.py never imports this module, so the tree CANNOT be consulted at measure-time
(the proof pins both directions by AST allowlist). What grafts is the GROWTH:

  deposit_correction(...)   — a correction into orient's own corpus tree
                              (``orient_corrections_nodes``, owner ``orient``, through
                              chart's nexus verbs → the librarian's tools → db_domain's
                              one gate). The door demands a DATED provenance: an undated
                              correction could never become a scan's provenance, so it
                              may not take up residence pretending it could (tooth 12's
                              requirement, honored one layer early).
  counsel_corrections(...)  — the walk: prior corrections nearest a new one, floor
                              visible and labeled (inherited fences, all of them).
  propose_scan(...)         — the nexus loop's handoff: corpus walked, the draft left
                              to the ceiling, the ADMISSION gate named in the artifact —
                              tooth 12 + Akien's ratification + a new version of
                              orient.py. Nothing here writes the registry.
  seed_founding(embed)      — edge (a): the corpus's first residents are the founding
                              corrections — the scars that built the instrument.
                              Idempotent (the deposit door dedups).

Vectors arrive as DATA; the embed call is the caller's, through inference_domain (the
same seam shape as ``deepen(resolve=...)`` — this module never opens the host).
"""
from __future__ import annotations

from cairn.chart.tree import counsel, deposit_learning, propose

OWNER = "orient"
CORPUS = "corrections"

ADMISSION = (
    "installation only: the scan lands in orient.py's SCANS carrying provenance that "
    "names this dated correction (tooth 12 refuses a scan nobody was taught by), joins "
    "the teeth, and is ratified by Akien — the registry is HARDWARE, it never changes "
    "mid-fire, and the tree is never consulted at measure-time.")

# Edge (a): the founding corrections — one per scar that built the instrument. Each is
# already a scan's provenance in orient.py; here it becomes WALKABLE, so the next
# correction's proposal starts from its nearest kin instead of from nothing (Law 1).
FOUNDING_CORRECTIONS = [
    {
        "content": "CC grepped for the word 'logging', found stdlib-shaped strings, and "
                   "reported '0 of 13 components have logging' of a tree with a composed "
                   "emission base and 7 live emit() call sites. Prose about a capability "
                   "cannot fire it; only a call site can — capability, not mention.",
        "provenance": {"source": "cairn/orient/orient.py call_sites (its Provenance)",
                       "date": "2026-07-27", "scan": "call_sites"},
    },
    {
        "content": "System state was reported from records (a filed edge, the map, a "
                   "docstring) three times in two days and was wrong about the world "
                   "each time. A census row is built only from things a filesystem call "
                   "returned — world, not record.",
        "provenance": {"source": "cairn/orient/orient.py device_census (its Provenance)",
                       "date": "2026-07-27", "scan": "device_census"},
    },
    {
        "content": "An echo label welded to && attested a push that never happened, and "
                   "git status clean confirmed the wrong thing. Only a command that "
                   "reads the THING (rev-parse, rev-list, porcelain) counts — thing, "
                   "not narration.",
        "provenance": {"source": "cairn/orient/orient.py repo_truth (its Provenance)",
                       "date": "2026-07-26", "scan": "repo_truth"},
    },
    {
        "content": "The census's generic emit-by-name count admitted two homonyms (a "
                   "module-level audit function; the workflow chokepoint) and let two "
                   "components pass the silent_device sieve on a word. The measure now "
                   "checks the RECEIVER is self — the word is not the capability, even "
                   "inside the instrument built to say so.",
        "provenance": {"source": "cairn/orient/orient.py device_census (sharpened "
                                 "same-day; history.json seq 3)",
                       "date": "2026-07-27", "scan": "device_census"},
    },
]


class GraftRefused(RuntimeError):
    """A growth-path ask this graft cannot honestly serve — refused loudly (Law 7)."""


def deposit_correction(content: str, vector, provenance: dict, *, conn=None) -> dict:
    """One correction into the corpus — dated at the door, or turned away."""
    if not isinstance(provenance, dict) or not str(provenance.get("date", "")).strip():
        raise GraftRefused(
            f"deposit_correction: provenance {provenance!r} names no date — an undated "
            "correction can never become a scan's provenance (tooth 12 demands the dated "
            "correction that taught it), so it may not join the corpus; nothing landed.")
    return deposit_learning(CORPUS, content, vector, provenance, owner=OWNER, conn=conn)


def counsel_corrections(vector, *, k: int = 3, conn=None) -> dict:
    """The walk over prior corrections — floor visible and labeled, fences inherited."""
    return counsel(vector, nexus=CORPUS, owner=OWNER, k=k, conn=conn)


def propose_scan(correction: str, vector, *, conn=None) -> dict:
    """The loop's handoff for a correction that would grow a scan: corpus walked, draft
    left to the ceiling, admission gate carried in the artifact. Writes nothing."""
    return propose(correction, vector, nexus=CORPUS, owner=OWNER,
                   kind="scan", admission=ADMISSION, conn=conn)


def seed_founding(embed, *, conn=None) -> list[dict]:
    """Edge (a): the founding corrections take residence. ``embed`` is the injected
    seam (text → vector through inference_domain); reseeding dedups to no-ops."""
    return [
        deposit_correction(c["content"], embed(c["content"]), c["provenance"], conn=conn)
        for c in FOUNDING_CORRECTIONS
    ]

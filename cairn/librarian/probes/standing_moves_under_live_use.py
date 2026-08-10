"""PROBE — does standing MOVE under live use, or does the tenure loop stand decorative?

Berth for the WATCHME that ticket ``the-tenure-loop`` carries. Berthed beside
``cairn/librarian`` because that is WHAT IT WATCHES: the tenure behaviors live in
``loop.py`` + ``trees.py``, and the one way this design fails silently is a tree where
nothing ever changes standing — every node minted hypothesis and still hypothesis weeks
later, promotion never firing, decay never fading a shard. The proofs pin that the
MECHANISM works (a staged node rises to earned, a back-dated shard fades); this probe asks
the efficacy question the proofs cannot: does it happen under LIVE use, at live rates,
with live questions? The charter's "weeks into live use the tree is all hypothesis" clause,
made a measure (the ticket's falsifier clause 2).

THE CORPUS IS THE LIBRARIAN'S OWN TREE — its component, its read (Law 6: the predicate
closes over data the librarian owns; only the poke crosses). One honest undercount, stated
rather than hidden: a resolve crossing that deposits nothing and touches no standing row
leaves no trace in the store, so store-evidenced crossings (birth questions + attestation
questions stamped after the loop landed) UNDERCOUNT true crossings. An undercount makes
the trigger fire LATER, never spuriously — the right error direction for a poke.

THE DIALS ARE THE LOOP'S OWN, imported, never restated: ``PROMOTION_THRESHOLD`` and
``DECAY_HORIZON`` live once, in ``loop.py`` (Law 1) — a probe that re-derived them would
drift the moment the loop learned better values.

AUTHORITY: none. This probe deposits and pokes; re-opening the tenure design (thresholds
wrong, promotion hollow, decay too eager) is the owner's act at the register (Law 6).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cairn.base.probe import Probe, owning_ticket
from cairn.db_domain import store
from cairn.librarian.loop import DECAY_HORIZON, PROMOTION_THRESHOLD
from cairn.librarian.trees import NODES

_OWNING_TICKET = "the-tenure-loop"

# The live tree this probe watches — NAMED AGAINST A MEASUREMENT, never copied from a
# neighbouring module's default. Measured 2026-08-10 (ticket a-probe-reads-the-tree-the-
# face-writes): librarian_nodes holds 88 rows distributed {'library': 84, 'founding': 4},
# and 'library' is what the live face composes its session with (LibrarianShim.__init__'s
# own default, shim.py). All four RATIFIED rows — the 3 earned and the 1 refuted, which are
# precisely the tenure outcomes this probe exists to watch — sit in 'library'.
#
# It read 'commons' from arming until 2026-08-10, and 'commons' is an ABSENT KEY in that
# distribution, not a small count: no row has ever existed there. So the instrument was
# armed against an address the running system has never written to, and it reported neither
# health nor decoration — it reported nothing, which at a watch is indistinguishable from
# health. That is how the-tenure-loop's WATCHME crossed PROVED with a dead eye.
#
# It is still not a proof nonce table, and must not become one: a proof table would be
# home-field advantage as a measurement (the sibling base probe measured exactly that
# failure live, 2026-07-30). The seam is pinned by
# proofs/test_the_probe_reads_the_tree_the_face_writes.py, which reads the face's tree from
# LibrarianShim's signature rather than from a literal — so if either end moves, the tooth
# reds on the DISAGREEMENT rather than on a string it carries a copy of.
_TREE = "library"

# When the loop LANDED (commit b599d34, 2026-08-09) — crossings before it predate the
# behaviors being watched and are not evidence about them.
_LANDED = datetime(2026, 8, 9, tzinfo=timezone.utc)

# The sample size below which a frozen standing distribution cannot be judged. A handful
# of crossings with no promotion is a young tree; twenty crossings and not one node earned
# is the charter's all-hypothesis clause standing live. The ticket's watchme names this
# number; it is a first guess and re-tunes when live crossing rates are measured.
_ENOUGH_CROSSINGS = 20


def _tz(dt):
    """A timestamp made comparable: naive rows read as UTC (the store writes UTC)."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _at(stamp: str | None):
    try:
        return _tz(datetime.fromisoformat(stamp)) if stamp else None
    except ValueError:
        return None


def _distinct_corroborations(prov: dict) -> set:
    """The questions that corroborated a node, EXCLUDING its birth question — the same
    cross-question rule the loop's promotion and decay both run on: an echo of the birth
    question is a touch, never independent reach."""
    birth = prov.get("question")
    return {a.get("question") for a in (prov.get("attestations") or [])
            if a.get("question") != birth}


def survey_the_tree() -> dict:
    """The standing distribution and crossing evidence, read from the live tree. Returns,
    besides the counts, the WITNESSES the carry ships: which nodes are earned (with their
    corroboration spans) and which uncorroborated shards have aged past walk reach — so
    the finding that rides back names the rows, not just the totals (complete diagnostic,
    first report). A store this probe cannot reach is not a finding: the survey says so
    and both predicates stand down."""
    try:
        rows = store.read(NODES, where="tree = %s", params=(_TREE,))
    except Exception as e:  # noqa: BLE001 — an unreachable store is a shim concern, not efficacy data
        return {"unreadable": str(e)}
    now = datetime.now(timezone.utc)
    standing: dict[str, int] = {}
    crossings: set[str] = set()
    earned: list[dict] = []
    faded: list[str] = []
    for r in rows:
        prov = r.get("provenance") or {}
        s = r.get("standing") or "?"
        standing[s] = standing.get(s, 0) + 1
        created = _tz(r.get("created"))
        if created and created >= _LANDED and prov.get("question"):
            crossings.add(prov["question"])
        for a in (prov.get("attestations") or []):
            stamped = _at(a.get("at"))
            if stamped and stamped >= _LANDED and a.get("question"):
                crossings.add(a["question"])
        distinct = _distinct_corroborations(prov)
        if s == "earned":
            earned.append({"node_id": r["node_id"], "corroborating_questions": len(distinct)})
        elif not distinct and created and (now - created) > DECAY_HORIZON:
            faded.append(r["node_id"])
    return {"standing_distribution": standing,
            "crossings_since_landing": len(crossings),
            "earned": earned,
            "faded_shards": faded}


def _trigger(now, context: dict) -> bool:
    """TRUE when the tree has been used and standing has not moved: >= _ENOUGH_CROSSINGS
    store-evidenced crossings since landing with ZERO earned nodes — or earned nodes exist
    but every one spans fewer distinct questions than PROMOTION_THRESHOLD (promotion gone
    hollow: standing moved without the cross-crossing reach that is its whole meaning)."""
    s = context.get("survey") or survey_the_tree()
    if "unreadable" in s:
        return False
    if s["crossings_since_landing"] < _ENOUGH_CROSSINGS:
        return False
    if not s["earned"]:
        return True
    return all(e["corroborating_questions"] < PROMOTION_THRESHOLD for e in s["earned"])


def _enough(context: dict) -> bool:
    """CLEARED by one witnessed instance of EACH half of the loop coexisting: an earned
    node whose corroborations span >= PROMOTION_THRESHOLD distinct questions (promotion,
    for real) AND an uncorroborated shard aged past walk reach (decay, for real).
    Existence claims both — one instance each settles them. Mutually exclusive with the
    trigger by construction: a genuinely-corroborated earned node is exactly what both
    trigger clauses assert the absence of."""
    s = context.get("survey") or survey_the_tree()
    if "unreadable" in s:
        return False
    promoted = any(e["corroborating_questions"] >= PROMOTION_THRESHOLD for e in s["earned"])
    return promoted and len(s["faded_shards"]) >= 1


def _carry(context: dict) -> dict:
    s = context.get("survey") or survey_the_tree()
    return {"finding": "the tree is being crossed and standing does not move — the tenure "
                       "loop stands decorative under live use",
            "survey": s,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "falsifier clause 2: standing never moves under live use "
                                 "— the charter's weeks-of-hypothesis clause, measured met",
            "suggests": "back-edge the-tenure-loop to WATCHME and re-open the dials: either "
                        "live questions never re-approach old ground (PROMOTION_THRESHOLD "
                        "unreachable at real crossing rates), or the similarity floor keeps "
                        "corroboration from ever firing — the dials are in loop.py, learned "
                        "values stranded as constants until this data moves them"}


# Same placeholder horizon, same tracked debt, as the base probes: the librarian shim's
# beat rate is not yet a real number, so 1000 pulses is "clearly a long standing" and
# MUST be re-tuned when it becomes one.
_HORIZON = 1000

PROBE = Probe(
    why="does standing MOVE under live use? — the proofs pin that promotion and decay CAN "
        "fire; twenty live crossings with an all-hypothesis tree (or hollow promotions) is "
        "the tenure loop standing decorative, which is the ticket's own falsifier clause 2",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    # The smoke-fire surface: the survey, and what the pair would do with it right now.
    s = survey_the_tree()
    print(json.dumps({"survey": s,
                      "would_trigger": _trigger(None, {"survey": s}),
                      "enough": _enough({"survey": s})}, indent=2, default=str))

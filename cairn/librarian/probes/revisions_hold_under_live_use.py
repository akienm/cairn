"""PROBE — do REVISIONS hold under live use, or does the retirement door stand decorative
(or, the other way, storm)?

Berth for the WATCHME that ticket ``revision-with-receipts`` carries. Berthed beside
``cairn/librarian`` because that is WHAT IT WATCHES: the fifth tenure behaviour —
refutation — lives in ``trees.refute``, its read-time half in ``loop._label_evidence``,
its entry affordance in ``chat.correction_turn``. The proofs pin that the MECHANISM works
(a stated correction retires a node, the walk returns it present-labelled-uncounted, the
standing gate stops a guess and passes a signature). This probe asks the efficacy question
the proofs cannot: does anyone ever USE it, and when they do, does the corpus stay sane?

THREE WAYS THIS DESIGN FAILS, and the probe watches all three (the ticket's three trigger
conditions, quoted into ``_trigger``):

  (a) A refutation LANDS and nobody ever says whether the refutation was itself right.
      A retirement is a claim like any other (Law 3), and the only instrument that can
      judge it is Akien. So an un-adjudicated refutation is a standing question, and the
      probe's whole job is to put it where he already looks.
  (b) THE DECORATIVE TELL — the tree gets crossed twenty times and not one refutation
      lands. Built, proved, sealed, and never once exercised: the behaviour is a museum
      piece and the ticket's own falsifier is met.
  (c) THE STORM TELL — refutations run past a tenth of the tree, or one crossing retires
      more than one node. That is the standing gate not holding: retirement should be a
      rare, deliberate, attributed act, and a corpus that retires itself in bulk has a
      door letting hypotheses shoot at each other.

THE CORPUS IS THE TREE THE LIVE FACE ACTUALLY WRITES — ``library``, not ``commons``.
MEASURED 2026-08-10 against the live store: 87 rows, of which ``library`` holds 83 and
``commons`` holds ZERO. The librarian's shim composes its live session on the ``library``
tree (``cairn/librarian/shim.py``, ``tree: str = "library"``), so a probe pointed at
``commons`` would survey an empty substrate and report a serene, meaningless green
forever. The armed sibling ``standing_moves_under_live_use.py`` is pointed at ``commons``
and does exactly that; its repair is its own ticket. Naming the live tree here is a
decision made against a measurement, not a copy of the neighbour.

THE ERA FLOOR IS MEASURED, AND THE MEASUREMENT SAYS SOMETHING UNEXPECTED. The rule
(2026-08-08 stale-process lesson, ``inference_domain/probes/does_a_domain_ride_the_
request.py``) is that "live" means the SERVING process, not the disk — a web server held
pre-route code for two hours after the disk was right. Applied here at arming time, the
measurement came back: THERE IS NO LONG-LIVED LIBRARIAN SERVING PROCESS. ``ss -ltnp``
shows no librarian listener, and ``systemctl --user status ground_loop.service`` reports
``activating (auto-restart)`` with ``ExecStart`` exiting 1 — the shim the librarian
subscribes to never gets to wake it. Every crossing on this box today therefore runs in a
short-lived process that imports ``trees.py`` fresh, so for this component the disk IS the
serving face and there is no staleness gap to fear. ``_ERA`` is consequently the arming
moment itself, and this is the condition under which that becomes WRONG: **if a long-lived
librarian listener is ever started, this floor must be re-measured as its ``ps lstart``,**
because from that moment a process can hold code older than the disk again.

AUTHORITY: none. This probe surveys and pokes. Deciding that a refutation was itself
wrong — and re-opening the node it retired — is the owner's act (Law 6), which is exactly
why ``adjudicated`` below is a thing the probe READS and never writes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from cairn.base.probe import Probe, owning_ticket
from cairn.db_domain import store
from cairn.librarian.trees import NODES

_OWNING_TICKET = "revision-with-receipts"

# The live tree — see the header's measurement. NOT the sibling's "commons".
_TREE = "library"

# The era floor: the arming moment, measured (see the header for why this is not a
# `ps lstart` — there is no long-lived listener to take one from). Crossings and
# refutations older than this predate the behaviour and are not evidence about it.
_ERA = datetime.fromisoformat("2026-08-10T14:24:30-06:00")

# The sample size below which "no refutations yet" is a young tree rather than a
# decorative behaviour. The ticket's watchme names this number; it is a first guess and
# re-tunes when live crossing rates are measured (a hand-set constant in a gate is a
# learned value stranded in a human's head — I-learns-its-gates).
_ENOUGH_CROSSINGS = 20

# The storm line: refutations past this fraction of the tree's nodes. Same status as
# above — a first guess, stated so it can be argued with.
_STORM_FRACTION = 0.10

# How Akien's verdict on a refutation is RECORDED: another attestation on the retired
# node, source "adjudication". Nothing in the corpus writes one today, and that is not an
# oversight — adjudication is the owner's act (Law 6), so the probe reads for it and never
# manufactures it. Until one exists every landed refutation reads un-adjudicated, which is
# TRUE and is precisely what condition (a) is for.
_ADJUDICATION = "adjudication"

# How many adjudications settle the human half of `enough` — the ticket's number.
_ENOUGH_ADJUDICATIONS = 3


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


def survey_the_tree() -> dict:
    """The refutation census, read from the live tree — the counts AND the rows, because
    the finding that rides back has to name each retirement with its evidence, its refuter
    and the node it retired (complete diagnostic, first report: the question 'was this
    refutation itself wrong?' is unanswerable from a total).

    Returns ``total_nodes``, ``standing_distribution``, ``crossings_since_era``,
    ``refutations`` (one entry per retired node), ``unadjudicated``, ``per_crossing_max``
    (the most retirements any single refuter landed — one correction mints one refuter
    node, so a refuter appearing twice IS one crossing retiring two nodes), and
    ``witnessed_later_walk``. A store this probe cannot reach is not a finding: the survey
    says so and both predicates stand down."""
    try:
        rows = store.read(NODES, where="tree = %s", params=(_TREE,))
    except Exception as e:  # noqa: BLE001 — an unreachable store is a shim concern, not efficacy data
        return {"unreadable": str(e)}

    standing: dict[str, int] = {}
    crossings: set[str] = set()
    latest_crossing = None
    refutations: list[dict] = []
    by_refuter: dict[str, int] = {}

    for r in rows:
        prov = r.get("provenance") or {}
        s = r.get("standing") or "?"
        standing[s] = standing.get(s, 0) + 1

        created = _tz(r.get("created"))
        if created and created >= _ERA and prov.get("question"):
            crossings.add(prov["question"])
            if latest_crossing is None or created > latest_crossing:
                latest_crossing = created

        adjudications: list[dict] = []
        retirement = None
        for a in (prov.get("attestations") or []):
            stamped = _at(a.get("at"))
            if stamped and stamped >= _ERA and a.get("question"):
                crossings.add(a["question"])
                if latest_crossing is None or stamped > latest_crossing:
                    latest_crossing = stamped
            if a.get("source") == "refutation":
                retirement = a          # the LAST refutation attestation is the live one
            elif a.get("source") == _ADJUDICATION:
                adjudications.append(a)

        if s == "refuted" and retirement is not None:
            at = _at(retirement.get("at"))
            if at is None or at >= _ERA:
                refuter = retirement.get("refuter")
                by_refuter[refuter] = by_refuter.get(refuter, 0) + 1
                refutations.append({
                    "retired_node": r["node_id"],
                    "refuter": refuter,
                    "evidence": retirement.get("evidence"),
                    "at": retirement.get("at"),
                    "adjudicated": bool(adjudications),
                    "adjudications": adjudications,
                })

    # The mechanism half of `enough`, derived rather than observed: a refutation older
    # than the most recent crossing means the tree WAS walked after that node was retired.
    # `loop._label_evidence` labels every refuted node present-and-uncounted on every walk
    # (proved, test_librarian_loop), so a later crossing IS a later walk that returned it
    # labelled and uncounted. The derivation rests on a proved property, not on a hope.
    witnessed = False
    if latest_crossing is not None:
        for ref in refutations:
            at = _at(ref["at"])
            if at is not None and at < latest_crossing:
                witnessed = True
                break

    return {"total_nodes": len(rows),
            "standing_distribution": standing,
            "crossings_since_era": len(crossings),
            "refutations": refutations,
            "unadjudicated": [r for r in refutations if not r["adjudicated"]],
            "per_crossing_max": max(by_refuter.values()) if by_refuter else 0,
            "witnessed_later_walk": witnessed}


def _reasons(s: dict) -> list[str]:
    """The trigger's three conditions, evaluated together so the poke can say WHICH fired
    (a probe that says only 'true' hands its reader a second investigation)."""
    out: list[str] = []
    if s["unadjudicated"]:
        out.append(f"(a) {len(s['unadjudicated'])} refutation(s) stand un-adjudicated — "
                   "a retirement is a claim, and only Akien can say whether it was itself wrong")
    if s["crossings_since_era"] >= _ENOUGH_CROSSINGS and not s["refutations"]:
        out.append(f"(b) DECORATIVE: {s['crossings_since_era']} crossings since the era "
                   "floor and not one refutation — built, proved, never exercised")
    if s["refutations"]:
        if s["total_nodes"] and len(s["refutations"]) > _STORM_FRACTION * s["total_nodes"]:
            out.append(f"(c) STORM: {len(s['refutations'])} refutations over "
                       f"{s['total_nodes']} nodes exceeds {_STORM_FRACTION:.0%} — the "
                       "standing gate is not holding")
        if s["per_crossing_max"] > 1:
            out.append(f"(c) STORM: one refuter retired {s['per_crossing_max']} nodes — a "
                       "single crossing landing more than one retirement")
    return out


def _trigger(now, context: dict) -> bool:
    """TRUE on any of the ticket's three conditions — see ``_reasons``."""
    s = context.get("survey") or survey_the_tree()
    if "unreadable" in s:
        return False
    return bool(_reasons(s))


def _enough(context: dict) -> bool:
    """CLEARED by BOTH halves witnessed: the MECHANISM half — at least one refuted node
    returned by a later walk, present-labelled-uncounted (derived in the survey from a
    proved property) — AND the HUMAN half, >= _ENOUGH_ADJUDICATIONS landed refutations
    that Akien has actually judged. The second half is the one no code here can settle,
    and it is deliberately the gate: a probe that retired itself on mechanism alone would
    be declaring the design worked on the evidence that it ran."""
    s = context.get("survey") or survey_the_tree()
    if "unreadable" in s:
        return False
    adjudicated = [r for r in s["refutations"] if r["adjudicated"]]
    return s["witnessed_later_walk"] and len(adjudicated) >= _ENOUGH_ADJUDICATIONS


def _carry(context: dict) -> dict:
    s = context.get("survey") or survey_the_tree()
    return {"finding": "; ".join(_reasons(s)) or "revisions census",
            "survey": s,
            "ticket": owning_ticket(_OWNING_TICKET),
            "against_falsifier": "the ticket's falsifier: refutation lands as a behaviour "
                                 "nobody exercises (decorative), or one that retires the "
                                 "corpus faster than the corpus earns it (storm) — and "
                                 "either way, retirements nobody ever adjudicates",
            "suggests": "read each un-adjudicated refutation's evidence against the node it "
                        "retired and say whether the retirement was right. A wrong one is a "
                        "back-edge on this ticket AND a re-open of the retired node (the "
                        "owner's act — the probe cannot do it). A decorative reading re-opens "
                        "the ENTRY question instead: 'correct: <node_id> <why>' may be a shape "
                        "nobody reaches for. A storm reading re-opens _REFUTER_AUTHORITIES in "
                        "trees.py — a hand-set allowlist standing in for a learned gate"}


# Same placeholder horizon, same tracked debt, as the sibling and the base probes: the
# librarian shim's beat rate is not yet a real number, so 1000 pulses is "clearly a long
# standing" and MUST be re-tuned when it becomes one.
_HORIZON = 1000

PROBE = Probe(
    why="do revisions hold under live use? — the proofs pin that a retirement CAN land, be "
        "labelled and stay uncounted; a tree crossed twenty times with zero refutations is "
        "the behaviour standing decorative, a tree retiring itself past a tenth is the "
        "standing gate not holding, and a refutation nobody adjudicates is a claim nobody "
        "checked — the ticket's own falsifier, all three ways",
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
                      "reasons": _reasons(s) if "unreadable" not in s else None,
                      "would_trigger": _trigger(None, {"survey": s}),
                      "enough": _enough({"survey": s})}, indent=2, default=str))

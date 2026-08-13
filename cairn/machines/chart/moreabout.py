"""chart/moreabout.py — the LEARNING DOOR: a scoped expansion from deposited state, and
the invocation written back as the training signal.

Stone 3 of the chart device (ticket: CairnCommons/tickets/moreabout.json), the skill
pair's other half — the ratifying intent's own words: "/chart <something> --- learning
from /moreabout <something>". When a field is too compressed, the answer is a WALK over
the upstream nexus's already-deposited tree, never a re-run of the pass that compressed
it (the charter's falsifier 4). And the ask itself is the datum: every invocation
deposits a dated ``moreabout_signal`` node back into that tree — "this, at this
compression, wasn't enough for this class" — so the parsimony threshold tunes on
evidence, not vibes.

The verbs:

  expand(vector)          — the scoped walk: counsel over the tenant's tree (floor
                            visible and labeled, inherited), with each walked node's
                            BERTHED STATE attached when its provenance names a file on
                            disk (a berthed packet is deposited state — reading it is
                            the walk continuing, not a re-run). Three honest shapes:
                            a file attaches parsed, a non-file source passes through
                            untouched, an unreadable file is named loudly. UNDER-FLOOR
                            HONESTY: a walk whose every node sits under the floor still
                            returns the ranked nodes, flagged — ranking was measured
                            right (correct node first) at 0.5775 < 0.65 the day this
                            was built; silence would launder "under floor" into
                            "nothing known".
  signal(ask, vector)     — the write-back: the ask lands as a node in the same
                            tenant's tree, provenance dated (undated evidence cannot
                            tune anything — the tooth-12 discipline one layer up). A
                            repeat identical ask returns duplicate:true — frequency
                            made readable at invoke time, not lost.

The door serves every tenant of the generalized verbs — chart's nexi, orient's
corrections, the inspector's failures — through the same mouth. Its only cairn import
is cairn.machines.chart.tree: the floor/ceiling machinery is structurally out of reach, so a
re-run is impossible by import physics, not discouraged by prose (the proof pins it).
Vectors arrive as data; the embed is the caller's (live.py), one per crossing serving
both the walk and the write-back.
"""
from __future__ import annotations

import json
import os

from cairn.machines.chart.tree import counsel, deposit_learning

OWNER = "chart"


class MoreaboutRefused(RuntimeError):
    """An ask this door cannot honestly serve — refused loudly (Law 7)."""


def expand(vector, *, nexus: str = "orient", owner: str = OWNER, k: int = 3,
           conn=None) -> dict:
    """The scoped walk over deposited state — counsel plus the berthed packets the
    walked nodes' provenance names. Never a re-run: this module cannot reach the
    machinery that would run one."""
    got = counsel(vector, nexus=nexus, owner=owner, k=k, conn=conn)
    expansions = []
    for node in got["walk"]:
        entry = {"similarity": node["similarity"], "content": node["content"],
                 "standing": node.get("standing"), "provenance": node.get("provenance")}
        source = (node.get("provenance") or {}).get("source")
        if isinstance(source, str):
            path = os.path.expanduser(source)
            if os.path.isfile(path):
                try:
                    with open(path, encoding="utf-8") as fh:
                        entry["berthed"] = json.load(fh)
                except (OSError, ValueError) as e:
                    entry["berthed_unreadable"] = f"{type(e).__name__}: {e}"
        expansions.append(entry)
    under_floor = bool(got["walk"]) and not got["above_floor"]
    return {
        "nexus": nexus,
        "owner": owner,
        "floor": got["floor"],
        "floor_is": got["floor_is"],
        "expansions": expansions,
        "above_floor": len(got["above_floor"]),
        "under_floor": under_floor,
        "under_floor_note": (
            f"every walked node sits under the floor (top "
            f"{got['walk'][0]['similarity']:.4f} < {got['floor']}) — the ranked nodes "
            "are shown anyway: ranking has been measured right under the floor "
            "(correct node first at 0.5775, 2026-07-28); the reader decides what "
            "applies, and 'under floor' is not 'nothing known'"
        ) if under_floor else None,
    }


def signal(ask: str, vector, *, date: str, nexus: str = "orient", owner: str = OWNER,
           about: str | None = None, field: str | None = None, conn=None) -> dict:
    """The invocation written back — the ask as a dated moreabout_signal node in the
    tenant's own tree. Refusals leave the tree exactly where it stood."""
    if not isinstance(ask, str) or not ask.strip():
        raise MoreaboutRefused(
            "signal: an empty ask cannot be a training signal — nothing deposited")
    if not isinstance(date, str) or not date.strip():
        raise MoreaboutRefused(
            "signal: a signal without a date cannot tune anything — parsimony "
            "evidence is dated or it is noise; nothing deposited")
    provenance = {"source": f"/moreabout over {owner}/{nexus}",
                  "kind": "moreabout_signal", "date": date.strip()}
    if about:
        provenance["about"] = about
    if field:
        provenance["field"] = field
    return deposit_learning(nexus, ask.strip(), vector, provenance,
                            owner=owner, conn=conn)

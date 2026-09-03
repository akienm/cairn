"""chart/tree.py — the TREE STRATUM: the orient nexus's own graph tree, between floor and ceiling.

Stone 2 of the chart device (ticket: CairnCommons/tickets/chart-tree.json). The ladder
ruling (held-nexi-everywhere, 2026-07-28) made this stone load-bearing: a nexus's Claude
CEILING may only stand above a TREE, because the tree is the deposit path that makes
inference temporary. This module is that rung for chart's nexi.

THE TOOLS ARE THE LIBRARIAN'S — the ratified unification ("we'll use the same tools with
the librarian"), landed as an owner parameter, not a fork: chart reaches ITS OWN table
(``chart_<nexus>_nodes``, owner ``chart``) through cairn.devices.librarian.trees, whose deposit
door and walks are the only door here. This module never touches db_domain or the network
directly (the composition lesson from stone 1, applied one layer up; the proof pins it by
AST allowlist).

AND THIS MODULE GENERALIZES THE SAME WAY (the graft tickets, 2026-07-28): every verb
takes an ``owner`` (default: chart), so a grafted nexus — orient's correction corpus,
the build_inspector's failure corpus — reaches ITS OWN table (``<owner>_<nexus>_nodes``)
through these same verbs and db_domain's same gate. One nexus shape, many tenants; the
same move trees.py made, one rung up. Chart's defaults are untouched and this proof
staying green is what says so.

The verbs:

  counsel(vector)          — the walk between floor and ceiling: the nexus's nearest
                             prior learnings, with the resolution floor VISIBLE and
                             LABELED (imported from the librarian's loop — 0.65, an n=1
                             guess, never laundered as settled). Counsel is COUNSEL:
                             the tree surfaces candidates; the ceiling decides what
                             applies (the what-exists/what-applies discipline, extended
                             to the tree). A field the ceiling takes from a walked node
                             is marked provenance "tree" in the packet.
  (orient's own deposit_orient lives in cairn/devices/codemonkey/machines/orient — see the note below)
  the deposit-back after the berth: the packet's ``intent``
                             lands as one node whose provenance names the berth path, so
                             the same class of request next time is a walk, not a
                             re-assembly (Law 1 as the nexus's own runtime). The packet
                             is re-validated at this door — a malformed packet must not
                             become a permanent resident — and the berth must exist on
                             disk (a provenance pointing at nothing is fabricated
                             attribution one layer up).
  propose(content, vector)   — the nexus loop's GROWTH HANDOFF: corpus walked, the draft
                             left to the ceiling, the admission gate named in the artifact
                             itself. It assembles; it never writes a registry — admission
                             is installation, and installation is the owner's gate.

Vectors arrive as DATA (the embed call is the caller's, through inference_domain — live
wiring in ``live.py``, never here). Home-field fences, pre-tenure: nodes are born
``hypothesis`` (inherited physics), counsel never fills a field silently, and nothing in
this module scores the nexus by its own tree's similarity (the charter's falsifier 6 —
manufactured resolution was measured at 0.8295 on the librarian).
"""
from __future__ import annotations

import os
import re

import cairn.devices.librarian.trees as trees
from cairn.devices.librarian.loop import RESOLUTION_FLOOR

OWNER = "chart"

_FLOOR_LABEL = ("a labeled guess (the librarian's RESOLUTION_FLOOR, n=1) — moves only by "
                "installation against real counsel evidence, per the hardware ruling")

_NEXUS_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class TreeRefused(RuntimeError):
    """A tree-stratum ask this module cannot honestly serve — refused loudly (Law 7)."""


def nexus_table(nexus: str, *, owner: str = OWNER) -> str:
    """The nexus's own table — per-tenant, per-nexus grain, literal to the charter ('its
    own table through db_domain'). A name outside the class is refused, not sanitized: a
    table name is identity, and silently rewriting identity is a different fact."""
    for role, name in (("nexus", nexus), ("owner", owner)):
        if not isinstance(name, str) or not _NEXUS_RE.match(name):
            raise TreeRefused(
                f"nexus_table: {role} {name!r} is not a legal name ([a-z][a-z0-9_]*) — "
                "refusing to mint a table for a name that cannot be one")
    return f"{owner}_{nexus}_nodes"


def deposit_learning(nexus: str, content: str, vector, provenance: dict, *,
                     owner: str = OWNER, conn=None) -> dict:
    """One learning into the nexus's tree, through the librarian's deposit door — its
    refusals (untraceable, under-floor, wrong-dimension, zero-vector) all inherited."""
    return trees.deposit(content, vector, provenance, tree=nexus,
                         table=nexus_table(nexus, owner=owner), owner=owner, conn=conn)


def counsel(vector, *, nexus: str = "orient", owner: str = OWNER, k: int = 3,
            floor: float = RESOLUTION_FLOOR, conn=None) -> dict:
    """The walk between floor and ceiling: prior learnings nearest the request, the
    resolution floor visible and labeled in every answer. An empty tree is an honest
    empty counsel — the nexus has simply never been here before."""
    walk = trees.nearest(vector, k=k, tree=nexus,
                         table=nexus_table(nexus, owner=owner), owner=owner, conn=conn)
    return {
        "nexus": nexus,
        "floor": floor,
        "floor_is": _FLOOR_LABEL,
        "walk": walk,
        "above_floor": [n for n in walk if n["similarity"] >= floor],
    }


def propose(content: str, vector, *, nexus: str, kind: str, admission: str,
            owner: str = OWNER, k: int = 3, conn=None) -> dict:
    """The nexus loop's GROWTH HANDOFF — the shape the graft tickets name: 'corpus
    walked, ceiling drafting, admission through the unchanged gate.'

    This function ASSEMBLES the proposal; it drafts nothing and admits nothing. The
    draft is the ceiling's (Claude works from the content and the counsel), and the
    admission is an INSTALLATION through the owning device's unchanged gate — named in
    the artifact itself so the proposal cannot travel without its gate. Nothing here
    can touch a registry: a registry is hardware, and hardware changes only by
    installation, never mid-fire (the hardware ruling's sharpest line)."""
    return {
        "proposal_for": kind,
        "nexus": nexus,
        "owner": owner,
        "content": content,
        "counsel": counsel(vector, nexus=nexus, owner=owner, k=k, conn=conn),
        "draft_is": "the ceiling's — drafted from the content and the counsel above; "
                    "nothing in this module writes code or a registry",
        "admission": admission,
    }

"""cairn/tools/tree/tree.py — the one graph-tree tool every learning block uses: the nexus's
graph tree, between floor and ceiling.

ONE TOOL, NOT CHART'S (outline 19.29, Q#54, Akien 2026-11-05: "it's stated as belonging to the
chart because that was the first time we defined it at that level, but it's the same tool
everywhere. if learning blocks need a special adaptation of it in some way, then it'd be a
subclass"). It was first defined at this level for chart's nexi (ticket chart-tree.json), and
the wording stayed chart's after the tool stopped being; every learning block — chart's stages,
codemother's machines, the build_inspector's failure corpus, the orient instrument — works the
trees the librarian delegates to it through these same verbs. A tool has users, not an owner
(Law 6): ``owner`` is a call parameter, so each user reaches ITS OWN table
(``<owner>_<nexus>_nodes``). A learning block that needs a special adaptation SUBCLASSES the
tool; it does not fork it.

``OWNER = 'chart'`` is only the default ``owner`` — kept because chart was the first user and its
callers lean on it; codemother's callers pass ``owner='codemother'`` since ticket 2b3d842bc118,
so no live codemother caller relies on the default.

THE LADDER (held-nexi-everywhere, 2026-07-28) made this rung load-bearing: a nexus's Claude
CEILING may only stand above a TREE, because the tree is the deposit path that makes inference
temporary.

THE TREES ARE THE LIBRARIAN'S — the ratified unification ("we'll use the same tools with the
librarian"), landed as an owner parameter, not a fork: each user reaches its own table through
cairn.devices.librarian.tools.trees.trees, whose deposit door and walks are the only door here.
This module never touches db_domain or the network directly (the composition lesson from stone
1, applied one layer up; the proof pins it by AST allowlist).

The verbs:

  counsel(vector)          — the walk between floor and ceiling: the nexus's nearest
                             prior learnings, with the resolution floor VISIBLE and
                             LABELED (imported from the librarian's loop — 0.65, an n=1
                             guess, never laundered as settled). Counsel is COUNSEL:
                             the tree surfaces candidates; the ceiling decides what
                             applies (the what-exists/what-applies discipline, extended
                             to the tree). A field the ceiling takes from a walked node
                             is marked provenance "tree" in the packet.
  (orient's own deposit_orient lives in cairn/devices/codemother/machines/orient — see the note below)
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
from contextlib import contextmanager

import cairn.devices.librarian.tools.trees.trees as trees
from cairn.devices.librarian.tools.trees.trees import RESOLUTION_FLOOR

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


@contextmanager
def scratch_nexus(kind: str, *, owner: str = OWNER):
    """A nexus whose table cannot outlive this process (ticket 201a37bf1613): the leaf
    table is minted through ``store.scratch()`` under the ``nexus_table`` rule and the
    NEXUS NAME is yielded, so ``nexus_table(name, owner=owner)`` is exactly the scratch
    table — dropped at exit, swept by pid if the process never gets there. For proofs
    and one-shot drains; a standing nexus is minted by ``nexus_table`` alone."""
    with trees.scratch_leaf(f"{owner}_{kind}", owner=owner, suffix="nodes") as table:
        yield table[len(owner) + 1:-len("_nodes")]


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

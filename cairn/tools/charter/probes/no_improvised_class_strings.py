"""PROBE — does every charter's node_class resolve to a registered class?

Berth for the WATCHME that ticket ``runtime-role-is-a-second-axis`` carries
(object ``no-improvised-class-strings``). Berthed beside ``cairn/tools/charter`` because that
is WHAT IT WATCHES: the charter fleet's vocabulary is the subject, and the recompile gate
(``cairn/tools/intentions_model_compiler/recompile_gate.sh``) is the event that refreshes
the census — the probe rides the recompile rather than adding a scan.

THE EFFICACY QUESTION. The parent ticket separated node_class (what a thing IS for proving
purposes) from runtime_role (what it ACTS AS at runtime). Four children built the vocabulary:
``the-axis-is-named-and-ruled`` added runtime_role to 48 charters and wired the sieve;
``the-parentheticals-are-deleted-or-promoted`` cleaned compound strings;
``three-classes-cannot-be-cast`` registered workflow versions for concept-piece, host-seam,
operational-driver; ``membership-is-derived-or-dropped`` derived node_class from the fleet
census. All four are PROVED.

THE WATCH ASKS: does the vocabulary stay settled? A new charter authored after this ticket
lands must not improvise a node_class value — the registered classes are the closed
vocabulary, and a value outside it is the defect this ticket exists to stop. Zero-across-a-
frozen-corpus is vacuous: the point is that a NEW charter cannot improvise, so ``enough``
requires at least one newly authored charter within the observation span.

NOT SATISFIABLE ON A FROZEN CORPUS: the enough condition requires at least one charter with
a commit date after the era floor AND zero unresolvable node_class values. A corpus that
has not grown cannot satisfy both.

AUTHORITY: none, by construction. This probe deposits and pokes; the back-edge that
re-opens the node is the OWNER's act (Law 6).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket

_REPO_ROOT = Path(__file__).resolve().parents[4]
_CLASS_SPACE = _REPO_ROOT / "cairn"
_NODE_CLASSES_DIR = _REPO_ROOT.parent / "CairnCommons" / "node_classes"

_OWNING_TICKET = "runtime-role-is-a-second-axis"

_ERA_FLOOR = "2026-09-01"


def _registered_classes() -> set[str]:
    """The set of node_class values the registry recognizes."""
    return {
        f.stem for f in _NODE_CLASSES_DIR.glob("*.json")
        if not f.name.startswith("_")
    }


def _charter_census() -> dict:
    """Census every charter's node_class, separating resolvable from improvised."""
    registered = _registered_classes()
    total = 0
    resolvable: list[dict] = []
    unresolvable: list[dict] = []
    missing: list[str] = []

    for charter_path in sorted(_CLASS_SPACE.rglob("intention+why.json")):
        if "__pycache__" in charter_path.parts or ".git" in charter_path.parts:
            continue
        try:
            charter = json.loads(charter_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        total += 1
        rel = str(charter_path.relative_to(_REPO_ROOT))
        nc = charter.get("node_class")
        if nc is None or nc == "":
            missing.append(rel)
            continue
        if nc in registered:
            resolvable.append({"path": rel, "node_class": nc})
        else:
            unresolvable.append({"path": rel, "node_class": nc})

    return {
        "era_floor": _ERA_FLOOR,
        "total_charters": total,
        "registered_classes": sorted(registered),
        "resolvable_count": len(resolvable),
        "unresolvable": unresolvable,
        "unresolvable_count": len(unresolvable),
        "missing_count": len(missing),
        "missing": missing,
    }


def _newly_authored_since_floor() -> int:
    """Count charters with a git commit after the era floor."""
    try:
        result = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "log", "--oneline",
             f"--since={_ERA_FLOOR}", "--diff-filter=A", "--name-only",
             "--", "cairn/**/intention+why.json"],
            capture_output=True, text=True, timeout=30,
        )
        return len([
            line for line in result.stdout.strip().splitlines()
            if line.endswith("intention+why.json")
        ])
    except Exception:
        return 0


def _trigger(now, context: dict) -> bool:
    """Fire when the fleet carries unresolvable node_class values — the problem to watch."""
    census = context.get("census") or _charter_census()
    return census["unresolvable_count"] > 0 or census["missing_count"] > 0


def _enough(context: dict) -> bool:
    """Zero unresolvable AND at least one newly authored charter since the era floor."""
    census = context.get("census") or _charter_census()
    if census["unresolvable_count"] > 0 or census["missing_count"] > 0:
        return False
    return _newly_authored_since_floor() >= 1


def _carry(context: dict) -> dict:
    """Census of the fleet's node_class vocabulary at fire time."""
    census = context.get("census") or _charter_census()
    return {
        "finding": (
            "charter fleet node_class census: %d resolvable, %d unresolvable, %d missing "
            "out of %d total charters (registered classes: %s)"
            % (census["resolvable_count"], census["unresolvable_count"],
               census["missing_count"], census["total_charters"],
               ", ".join(census["registered_classes"]))
        ),
        "census": census,
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": (
            "the ticket's falsifier: for all charters, node_class resolves to a "
            "registered class without improvising a string. Unresolvable values and "
            "missing fields are both counted."
        ),
    }


_HORIZON = 1000

PROBE = Probe(
    why="runtime_role separated from node_class across 48 charters, vocabulary settled by "
        "four children — but every charter authored after the settlement must use the "
        "registered vocabulary. Fires when any charter carries an unresolvable node_class or "
        "is missing the field entirely.",
    trigger=_trigger,
    to="charter",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    census = _charter_census()
    print(json.dumps({
        "census": census,
        "newly_authored_since_floor": _newly_authored_since_floor(),
        "would_trigger": _trigger(None, {"census": census}),
        "enough": _enough({"census": census}),
    }, indent=2))

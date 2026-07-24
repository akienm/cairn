"""harbor_master/register.py — the FLEET REGISTER: a compiled index over the boats' own records.

harbor_master owns the HARBOR through which workflows voyage. This is its first rung —
the TRUTH rung as an AGGREGATE: 'where you go to query open tickets', the fleet-scale
view of what is in port and what is still at sea. (The AUTHORITY rung — clearance for a
transition — is child b, and waits on the base-class emit-chokepoint; the JOURNEY view is
child c, deferred to meet the web_server. This file is child a alone.)

Two vantages, both already git-JSON on disk, mirroring the lifecycle CLAUDE.md names —
"a ticket stages in CairnCommons/tickets/, then migrates beside the code to become that
component's history":
  - OPEN boats  = tickets still voyaging in ``CairnCommons/tickets/`` (not yet berthed).
  - IN-PORT boats = components with a ``history.json`` beside their code (+ ``bin/``) —
    proven voyages, berthed. Their standing is exactly ``project(history).cursor``.

The register is an INDEX, not a rival record (Law 7). Every entry's standing is read from
the boat's OWN record and carries a ``source`` pointing back to it; the register invents
no truth a boat does not already hold. ``berth`` (open|in_port) is not an invented field —
it is a pure function of WHERE the boat lives, which is what the lifecycle already means.

Computed on read, never stored — so it cannot drift from the boats (Law 7), and child a's
filed "db-vs-git placement edge" DISSOLVES: there is nothing to place because there is no
second copy (Law 1 — the aggregate is compiled, not kept). If fleet queries ever turn hot,
an event-fired cache (the FileChanged pattern the intentions_model_compiler already uses)
is the grow-against-need step — never a poll.

The BaseDevice introspection FACE + bus-fronting (callers poke the harbor over the bus
rather than importing it) are a later runtime wrapper, deferred until a runtime pulls them —
exactly as inference_domain and db_domain deferred their faces. A filed edge, below.

Deliberately dependency-light: pure file reads + the projector's pure core. Runs bare.

    python3 -m cairn.harbor_master.register     # prints a human fleet summary
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from cairn.charter import projector

_REPO_ROOT = Path(__file__).resolve().parents[2]   # cairn/harbor_master/register.py -> repo root
_CAIRN = _REPO_ROOT / "cairn"
_SRC_ROOT = _REPO_ROOT.parent                        # ~/dev/src — the common parent of the two repos
_DEFAULT_TICKETS = _SRC_ROOT / "CairnCommons" / "tickets"

# The cursor marker in a ticket's ``state`` string is the bracketed [STAGE], e.g.
# "code-seam@v1: THINKME -> [TICKETME] -> BUILDME -> ...". Prose states ("building")
# carry no bracket and are taken verbatim — we report what the boat says, never invent one.
_CURSOR_RE = re.compile(r"\[([A-Z_]+)\]")


def _rel(path: Path) -> str:
    """A source pointer relative to the common src root when possible (portable, greppable)."""
    try:
        return str(path.relative_to(_SRC_ROOT))
    except ValueError:
        return str(path)


def _berthed_boats(cairn_root: Path) -> list[dict]:
    """In-port boats: every component carrying a ``history.json`` beside its code (+ bin/).

    The standing is the boat's OWN cursor — ``project(history).cursor`` — read here, not
    re-derived into something new (Law 1: the projector already answers 'where does this
    boat stand'; the register only gathers those answers).
    """
    dirs = [p.parent for p in cairn_root.glob("*/history.json")]
    bin_hist = cairn_root.parent / "bin" / "history.json"
    if bin_hist.exists():
        dirs.append(bin_hist.parent)
    boats = []
    for d in sorted(dirs):
        history = projector.read_history(str(d / "history.json"))
        cursor = projector.project(history)["cursor"] or {}
        boats.append({
            "id": d.name,
            "berth": "in_port",
            "standing": cursor.get("standing"),
            "gate": cursor.get("gate"),
            "seq": cursor.get("seq"),
            "source": _rel(d / "history.json"),
        })
    return boats


def _open_boats(tickets_dir: Path) -> list[dict]:
    """Open boats: every ticket still voyaging in the commons tickets folder.

    A boat is a ticket with an ``id`` and a string ``state`` cursor. The folder's own
    schema doc (no state) is not a boat and is skipped — the register carries workflows,
    not the form they are written on.
    """
    boats = []
    if not tickets_dir.exists():
        return boats
    for t in sorted(tickets_dir.glob("*.json")):
        try:
            d = json.loads(t.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue                      # unreadable/garbled ticket is not a silent boat
        state = d.get("state")
        if not d.get("id") or not isinstance(state, str):
            continue                      # not a boat (e.g. the folder's _charter+why schema doc)
        m = _CURSOR_RE.search(state)
        cursor = m.group(1) if m else state.strip()   # the [STAGE] marker, or the raw prose state
        boats.append({
            "id": d["id"],
            "berth": "open",
            "standing": cursor,
            "node_class": d.get("node_class"),
            "source": _rel(t),
        })
    return boats


def register(*, cairn_root: Path | str = _CAIRN, tickets_dir: Path | str = _DEFAULT_TICKETS) -> dict:
    """Compile the fleet register — a pure INDEX over the boats' own records.

    Returns ``{open, in_port, fleet, counts}``. Not stored: recomputed from the boats
    each call, so it can never be a rival record that drifts (Law 7). ``fleet`` is the
    union of both vantages; a boat mid-journey (an open ticket AND an early berthed
    history under one name) legitimately appears in BOTH — stitching those into one
    journey is child c's job, not this rung's, so the register shows each source
    faithfully rather than silently collapsing them.
    """
    in_port = _berthed_boats(Path(cairn_root))
    open_ = _open_boats(Path(tickets_dir))
    return {
        "open": open_,
        "in_port": in_port,
        "fleet": open_ + in_port,
        "counts": {"open": len(open_), "in_port": len(in_port), "fleet": len(open_) + len(in_port)},
    }


# ── query surface (the harbor's read face) ───────────────────────────────────


def open_boats(reg: dict) -> list[dict]:
    """The boats still at sea — 'query open tickets'."""
    return reg["open"]


def in_port(reg: dict) -> list[dict]:
    """The boats berthed — proven voyages beside their code."""
    return reg["in_port"]


def find(reg: dict, boat_id: str) -> list[dict]:
    """Every vantage of one boat by id — a LIST, because a boat mid-journey shows in both
    (an open ticket + its berthed history). One entry: berthed or open only. Two: mid-journey."""
    return [b for b in reg["fleet"] if b["id"] == boat_id]


def _main() -> int:
    reg = register()
    c = reg["counts"]
    print(f"HARBOR REGISTER — {c['fleet']} boats ({c['open']} open, {c['in_port']} in port)\n")
    print("OPEN (still at sea — CairnCommons/tickets/):")
    for b in reg["open"]:
        print(f"  {b['id']:32} @ {b['standing']}")
    print("\nIN PORT (berthed beside code):")
    for b in reg["in_port"]:
        gate = f" [{b['gate']}]" if b.get("gate") else ""
        print(f"  {b['id']:32} @ seq {b.get('seq')}{gate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

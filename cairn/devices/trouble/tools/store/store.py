"""The trouble store, read as files — the tool trouble publishes (ticket ee04bb869795).

Akien 2026-10-18: "TROUBLE TICKETS ARE A FILE ARTIFACT IN THE LOGGING TREE" / "THERE SHOULD BE
NO ROWS FOR TROUBLE TICKETS." Every reader outside the trouble component (cairn's pane,
web_server's socket, counting_block, base/transitions.py, the operator inbox, two base probes)
reads the store through this module and nothing else of trouble's. Until this build three of
them asked over the bus, and each reply stood as a bus row: 195 `live` replies (~325 KB) and
372 `clears` replies measured on the day.

A tool holds no state of its own (Law 6): it READS. It never folds pending emissions — folding
is the owner's write, done by TroubleDevice in its own process — so what it answers is the
store as it stands. It imports the address door and nothing else at module level, so a sieve
can ask where the store is without reaching a host (measured 2026-10-13,
test_inspector_nexus.py). Declared in this tool's charter's public_interface (RULE 1).
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.address import log_path

# What a reader is handed per live trouble (ticket fa9a2703a9c3): the occurrence tail and its
# details stay in the store, so a read grows with the number of live troubles and never with
# their history.
LIVE_SUMMARY_KEYS = ("id", "standing", "why", "count", "first_seen", "last_seen")

LIVE = "OPEN"
CLEARED_DIR = "cleared"


def store_root(roots: dict | None = None) -> Path:
    """Where the trouble store lives: ``log_path('cairn', 0, roots)/troubletickets``. Public,
    so every reader of the store asks here instead of naming the path (RULE 1)."""
    return log_path("cairn", 0, roots) / "troubletickets"


def _root(roots: dict | None, root) -> Path:
    return Path(root) if root is not None else store_root(roots)


def listing(folder: Path) -> list[dict]:
    """Every ticket file in ``folder``, whole. An absent folder is ``[]``; an unreadable file
    is a row saying so; an off-template record is a row saying where to read it."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    out = []
    for p in sorted(folder.glob("*.json")):
        try:
            ticket = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            # The lane must not go dark because one file is malformed — that would be a
            # silent failure in the very place built to end them.
            out.append({"id": p.stem, "standing": LIVE, "count": 1,
                        "why": f"UNREADABLE TROUBLE FILE: {exc}", "unreadable": True})
            continue
        if isinstance(ticket, dict) and "why" not in ticket:
            # OFF-TEMPLATE, AND SAYING SO IS THE WHOLE POINT (2026-08-12).
            # `the-runtime-spine-has-never-run` carries the fullest why in the store —
            # opened_by, the_claim_under_test, verdict, method, findings, the_map — under
            # none of those names, and the session banner rendered it as
            # "<no why recorded>". That is a reader turning a PRESENT record into an
            # ABSENCE claim: not collapsing an error into a coherent shape (which a
            # presentation surface may do) but MANUFACTURING one (Law 7). The fix belongs
            # here and not in the banner, because what a trouble's why IS belongs to this
            # lane (Law 6) — the banner already refuses to re-derive `live()` for the
            # same reason. Deliberately NOT a fallback key list: guessing which field is
            # really the why would freeze today's two off-template shapes into a schema,
            # and the shapes are the defect, not the vocabulary. The reader is told the
            # record is off-template, what it carries, and where to read it — which is the
            # `notes-store-template-gate-is-prose-not-physics` trouble showing its face at
            # session open instead of hiding behind a manufactured silence.
            ticket = dict(ticket)
            ticket["why"] = (
                "OFF-TEMPLATE TROUBLE RECORD — the why is almost certainly here, under a "
                "name this reader does not know, so this line is the READER's limit and "
                "not the author's silence. It carries: %s. Read it: %s"
                % (", ".join(k for k in ticket if k != "why"), p))
            ticket["off_template"] = True
        out.append(ticket)
    return out


def live(roots: dict | None = None, *, root=None) -> list[dict]:
    """The tickets still demanding attention, one LIVE_SUMMARY_KEYS row each. EMPTY is the
    normal operating state — so an ABSENT store RAISES, and no reader can render "we could not
    look" as zero troubles (Law 7). The top of the store is the list; cleared/ is not read.
    An unreadable file's row keeps ``unreadable: True``."""
    top = _root(roots, root)
    if not top.is_dir():
        raise FileNotFoundError(f"no trouble store at {top} — absent is not zero troubles")
    rows = []
    for t in listing(top):
        row = {k: t.get(k) for k in LIVE_SUMMARY_KEYS}
        if t.get("unreadable"):
            row["unreadable"] = True
        rows.append(row)
    return rows


def clears(prefix: str = "", roots: dict | None = None, *, root=None) -> list[dict]:
    """Every clear on the record, one {id, standing, by, hand_class, at} row each, over the
    top of the store and cleared/ — for the counting block, which learns whose hand cleared
    what (ticket 1c1b18bac2eb, D4). ``prefix`` narrows by trouble id. A stored class of
    'unknown' beside a stored cgroup is classed from that cgroup, so a clear recorded before
    the classifier walked outward is learned (ticket 4f8d11706516)."""
    from cairn.tools.system_word import fold
    top = _root(roots, root)
    rows = []
    for t in listing(top) + listing(top / CLEARED_DIR):
        if not str(t.get("id", "")).startswith(prefix or ""):
            continue
        for c in t.get("cleared_by") or []:
            hand = c.get("hand") if isinstance(c.get("hand"), dict) else {}
            hand_class = fold(hand.get("class")) if hand.get("class") else "unknown"
            if hand_class == "unknown" and isinstance(hand.get("cgroup"), str):
                from cairn.tools.artifact import artifact as door
                hand_class = fold(door.classify(hand["cgroup"])["class"])
            rows.append({"id": t.get("id"), "standing": t.get("standing"), "by": c.get("by"),
                         "hand_class": hand_class, "at": c.get("at")})
    return rows

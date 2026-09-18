"""cairn cast — the CLI face of the casting door, and the sweep that reads the store's
backlog back (ticket 23089d52d805, 2026-09-18).

Two mouths, one implementation (``transitions.cast_ticket``):

    python3 -m cairn.tools.base.cast <fields.json> --actor <who>   # exit 0 path / exit 1 refusal
    python3 -m cairn.tools.base.cast --sweep [commons_root]         # JSON, exit 0 always

THE SWEEP REPORTS AND FAILS NOTHING. The ticket's hard bound (constraints.out, and
watchme_spec.py's record of the same stone paid for twice): a check that retro-reds every
open boat is a check that gets disabled. So ``sweep_casts`` classifies every standing
ticket by the FIRST journal entry that names it and never raises — the classes are the
vocabulary the WATCHME probe (probes/the_casting_door_has_callers.py) counts arrivals
in, and the ``landing`` is the earliest cast that went through the door, derived from
the journal rather than stored anywhere:

    through_the_door   created (sha_before 'absent') with transitions.py's ``cast_ticket`` frame in the stack
    journaled_beside   created through the artifact door by some other frame
    pre_door           first entry is the journal's ``genesis`` of an already-standing file
    unjournaled        no journal entry names the file at all

Measured at the build (2026-09-18): 307 hex-id tickets — 289 pre_door, 18 journaled_beside,
0 unjournaled, 0 through_the_door. The first door-cast is the first row in the first class.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_CLASSES = ("through_the_door", "journaled_beside", "pre_door", "unjournaled")
# The door's OWN frame, not any function that happens to share its name: a scratch helper
# named cast_ticket wrote 5 tickets on 2026-09-16 (castlib.py:83:cast_ticket) and the bare
# ':cast_ticket' suffix credited them to a door that did not exist yet.
_DOOR_FRAME = re.compile(r"(^|/)transitions\.py:\d+:cast_ticket$")


def _is_ticket(p: Path) -> bool:
    return p.suffix == ".json" and not p.name.startswith("_")


def classify(first: dict | None) -> str:
    """The class of a ticket whose first journal entry is ``first`` (None: never named)."""
    if first is None:
        return "unjournaled"
    if first.get("verb") == "genesis":
        return "pre_door"
    if first.get("sha_before") == "absent" and any(
            _DOOR_FRAME.search(str(f)) for f in first.get("stack") or ()):
        return "through_the_door"
    return "journaled_beside"


def sweep_casts(commons_root: Path) -> dict:
    """Classify every ``tickets/*.json`` under ``commons_root`` by its first journal entry.

    Returns ``{"counts": {class: n}, "tickets": {rel: class}, "landing": entry|None}`` where
    ``landing`` is the earliest ``through_the_door`` entry in journal order. Never raises: an
    unreadable journal reads as empty (every ticket then ``unjournaled``), which is the
    loud reading — a sweep that could not see the journal must not report a green one."""
    commons_root = Path(commons_root)
    tickets_dir = commons_root / "tickets"
    try:
        from cairn.tools.artifact import artifact as door
        entries = door.read_journal(commons_root)
    except Exception:  # noqa: BLE001 — the sweep reports, it never fails
        entries = []
    first: dict[str, dict] = {}
    landing: dict | None = None
    for e in entries:
        rel = e.get("path")
        if not isinstance(rel, str) or not rel.startswith("tickets/"):
            continue
        if rel not in first:
            first[rel] = e
            if landing is None and classify(e) == "through_the_door":
                landing = e
    tickets: dict[str, str] = {}
    try:
        files = sorted(p for p in tickets_dir.glob("*.json") if _is_ticket(p))
    except OSError:
        files = []
    for p in files:
        rel = "tickets/" + p.name
        tickets[rel] = classify(first.get(rel))
    counts = {c: 0 for c in _CLASSES}
    for c in tickets.values():
        counts[c] += 1
    return {"counts": counts, "tickets": tickets, "landing": landing}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip().splitlines()[0])
        print("usage: cairn cast <fields.json> --actor <who> | cairn cast --sweep [commons_root]")
        return 0 if argv else 1
    if argv[0] == "--sweep":
        if len(argv) > 1:
            root = Path(argv[1])
        else:
            from cairn.tools.base.transitions import _TICKETS
            root = _TICKETS.parent
        print(json.dumps(sweep_casts(root), indent=2, ensure_ascii=False))
        return 0
    fields = Path(argv[0])
    actor = None
    if "--actor" in argv:
        i = argv.index("--actor")
        actor = argv[i + 1] if i + 1 < len(argv) else None
    if not actor:
        print("cairn cast refused: --actor <who> is required — a cast with no actor has no "
              "who on its journal line", file=sys.stderr)
        return 1
    try:
        doc = json.loads(fields.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"cairn cast refused: {fields} is not readable JSON ({e})", file=sys.stderr)
        return 1
    from cairn.tools.base.transitions import CastRefused, cast_ticket
    try:
        path = cast_ticket(doc, actor=actor)
    except CastRefused as e:
        print(str(e), file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

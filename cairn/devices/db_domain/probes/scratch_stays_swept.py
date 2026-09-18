"""PROBE — scratch-stays-swept

Berth for the WATCHME that ticket ``201a37bf1613`` carries. Berthed beside ``db_domain``
because that is WHERE THE INVARIANT LIVES: the store's ``cairn_owned`` registry and its
``cairn_scratch`` registry together say what may be in ``pg_tables`` — every standing
table is registered, and every scratch table is either owned by a live pid or already
gone. The tester sweeps dead-pid scratch before every seal (``tester/scratch_sweep.py``),
so a table that stands outside the two registries, or a scratch row whose minter is dead
and yet survives a seal, is a LEAKER — and the probe names it rather than counting it.

THE QUESTION: does the invariant hold on its own, seal after seal? Enough is seven days
after the ticket's PROVED crossing with the invariant holding at every survey; the first
survey where it does not is the finding, carrying the leaker's name (Law 7: loud, and
the complete diagnostic on the first report).

    python3 cairn/devices/db_domain/probes/scratch_stays_swept.py
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cairn.tools.base.probe import Probe, owning_ticket, once

_OWNING_TICKET = "201a37bf1613"
_ENOUGH_AFTER = timedelta(days=7)
_HISTORY = Path(__file__).resolve().parents[1] / "history.json"
# a standing (non-scratch) table carrying a pid nonce is a proof that minted OUTSIDE scratch():
# the name is never the sweep's predicate (constraint 2), but it is the probe's DETECTOR —
# the migration read the same shape over 8,399 of the 9,075 leaked tables.
_PID_NONCE = re.compile(r"_(\d{1,7})_(\d{6,12})(?:_|$)")


def _proved_at() -> datetime | None:
    """When the ticket crossed into PROVED, from the component's own history (None until it has)."""
    try:
        entries = json.loads(_HISTORY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for e in entries:
        if e.get("ticket") == _OWNING_TICKET and e.get("to") == "PROVED":
            try:
                at = datetime.fromisoformat(str(e.get("at")))
            except ValueError:
                return None
            return at if at.tzinfo else at.replace(tzinfo=timezone.utc)
    return None


def survey() -> dict:
    from cairn.devices.db_domain import store
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            present = {r[0] for r in cur.fetchall()}
            cur.execute(f'SELECT table_name FROM "{store._REGISTRY}"')
            owned = {r[0] for r in cur.fetchall()}
        rows = store.scratch_rows(conn=conn)
    finally:
        conn.close()
    scratch = {r["table_name"] for r in rows}
    alive = sorted(r["table_name"] for r in rows if store.minter_alive(r["pid"], r["created"]))
    dead = sorted(r["table_name"] for r in rows if r["table_name"] not in set(alive))
    unregistered = sorted(present - owned)
    absent = sorted(owned - present)
    standing = sorted(owned - scratch)
    nonced = []
    for name in standing:
        m = _PID_NONCE.search(name)
        if m and store.process_start(int(m.group(1))) is None:
            nonced.append(name)          # a dead pid's table, minted by hand — the leaker by name
    leakers = sorted(set(unregistered) | set(dead) | set(absent) | set(nonced))
    proved = _proved_at()
    return {
        "pg_tables": len(present),
        "standing_rows": len(standing),
        "scratch_rows": len(rows),
        "alive_scratch": alive,
        "dead_scratch": dead,
        "unregistered": unregistered,
        "registered_but_absent": absent,
        "minted_outside_scratch": nonced,
        "holds": not leakers,
        "leakers": leakers,
        "proved_at": proved.isoformat() if proved else None,
        "surveyed_at": datetime.now(timezone.utc).isoformat(),
    }


def _trigger(now, context: dict) -> bool:
    s = once(context, "survey", survey)
    return not s["holds"]


def _enough(context: dict) -> bool:
    s = once(context, "survey", survey)
    if not s["holds"]:
        return True                      # the first breach is the finding — stop and report it
    if not s["proved_at"]:
        return False
    return datetime.now(timezone.utc) - datetime.fromisoformat(s["proved_at"]) >= _ENOUGH_AFTER


def _carry(context: dict) -> dict:
    s = once(context, "survey", survey)
    if s["holds"]:
        finding = (f"HOLDS — {s['pg_tables']} table(s) in pg_tables = {s['standing_rows']} standing "
                   f"+ {len(s['alive_scratch'])} live-pid scratch; nothing stands outside the registries")
    else:
        finding = (f"LEAK — {len(s['leakers'])} table(s) outside the invariant: "
                   f"unregistered {s['unregistered']}, dead-pid scratch surviving a seal {s['dead_scratch']}, "
                   f"registered-but-absent {s['registered_but_absent']}, "
                   f"dead-pid tables minted outside scratch() {s['minted_outside_scratch']}")
    return {"finding": finding, "survey": s, "ticket": owning_ticket(_OWNING_TICKET)}


PROBE = Probe(
    why="9,075 dead tables made the store's working surface lie about what was running (CP4); "
        "the sweep on the tester's seal path is what keeps it true, and this probe watches "
        "that it does — seven days of the invariant holding, or the first leaker by name",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": "scratch-stays-swept"},
    carry=_carry,
    enough=_enough,
    horizon=1000,
)


if __name__ == "__main__":
    s = survey()
    print(json.dumps({
        "survey": s,
        "would_trigger": _trigger(None, {"survey": s}),
        "enough": _enough({"survey": s}),
        "carry": _carry({"survey": s}),
    }, indent=2, default=str))

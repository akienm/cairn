"""PROBE — does the home instance's answer tree and meter still carry what the migration dumped?

Berth for the live reading ticket 98ab0e9db57f's clause 7 makes ("the old table is gone, the
answer tree holds at least 11,366 leaves, the dump exists, and the metrics totals until the
dump's newest row equal the dump's spent and avoided"). Berthed beside
``cairn/devices/inferenceproxy`` because that is WHAT IT WATCHES: the answers and the meter the
migration carried across (``migrate_answers_to_their_tree.py``).

WHY A PROBE AND NOT A PROOF TOOTH (ticket a4c8bf408dc2). Measured 2026-11-23: under
``bin/cairn test``'s instance seal ``~/.cairn`` is a swapped mount, so a tooth's bus ask dials the
seal's own bus, and the cairn device's ``metrics`` verb answers from the run's partial
``cairn_testing`` copy (0/0 against the dump's 4640161/1051713; 829 testing leaves when nested in
the device-wide tooth). "Live" means the real component on real data (Akien 2026-09-28, reshaped
2026-10-05), never a bus dialled from inside a seal. So the live reading runs HERE, on the home
instance, and the proof judges the same judgement over a fixture (tooth 7 of
proofs/test_the_proxy_keeps_its_answers_in_a_tree_and_its_meter_in_the_log.py).

ONE JUDGEMENT. ``judge`` is the only place the carried-ness rule is written; the proof imports it.

THE CONSUMER: CodeMother's WATCHME gate (``codemother`` ``machines/watchme/watch``,
cairn/devices/codemother/machines/watchme/gate.py), the receiver every sibling probe in this
folder posts to. ``holds`` False there fails 98ab0e9db57f back to design with the finding.

TWO BUS READS, ONE BOX: ``inference``'s ``migration`` verb (ticket d9d87ccb97e5) and ``cairn``'s
``metrics`` totals, asked under both source names the device has recorded under (the carried
rows stand under the pre-rename source, measured 2026-11-13, ticket f942a413f26d). A bus that
cannot be reached raises; the carry reads a raise as holds False (Law 7).

AUTHORITY: none. This probe posts; fixing the meter is the owner's act (Law 6).

    python3 cairn/devices/inferenceproxy/probes/the_home_meter_carries_the_dump.py   # the live survey
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from cairn.tools.base.probe import Probe, once, owning_ticket, watch_carry

_TICKET_ID = "98ab0e9db57f"
_FLOOR_LEAVES = 11366  # 98ab0e9db57f clause 7: the leaves the migration carried on 2026-11-09
_WHY = "98ab0e9db57f clause 7, the home meter probe (a4c8bf408dc2)"


def judge(migration: dict, totals: list[dict]) -> dict:
    """The pure judgement: what the home instance's ``migration`` verb answered, against the
    metrics totals until the dump's newest row. Returns ``{holds, lacks, line}``; every lack is
    named. Separable from the reads so the proof feeds it fixtures."""
    lacks = []
    if migration.get("old_table_gone") is not True:
        lacks.append(f"the old table is still there: {migration.get('old_table_gone')!r}")
    n = migration.get("leaves")
    if not (isinstance(n, int) and n >= _FLOOR_LEAVES):
        lacks.append(f"{n} leaves in the answer tree, under the {_FLOOR_LEAVES} the migration carried")
    if not migration.get("dump_newest"):
        lacks.append("no dump of the old table")
    spent, avoided = migration.get("dump_spent"), migration.get("dump_avoided")
    m_spent = sum(t["sum"] for t in totals if t.get("name") == "inference.spent")
    m_saved = sum(t["sum"] for t in totals if t.get("name") == "inference.saved")
    if not (isinstance(spent, (int, float)) and isinstance(avoided, (int, float))):
        lacks.append(f"the dump states no spent/avoided: {spent!r}/{avoided!r}")
    elif (round(m_spent, 3), round(m_saved, 3)) != (round(spent, 3), round(avoided, 3)):
        lacks.append(f"metrics spent {m_spent} saved {m_saved} against the dump's spent {spent} "
                     f"avoided {avoided}")
    line = (f"dump spent {spent} avoided {avoided}; metrics spent {m_spent} saved {m_saved}; "
            f"leaves {n}")
    return {"holds": not lacks, "lacks": lacks, "line": line}


def survey_home(reach=None) -> dict:
    """The live read, on the instance this runs on: its ``migration`` answer and its metrics
    totals until the dump's newest row, judged. ``reach`` is injectable so the proof can stand a
    recording bus in its place; absent, it is the bus client's."""
    if reach is None:
        from cairn.tools.bus_client import reach
    migration = reach("inference").request(sender="inferenceproxy", to="inference",
                                           verb="migration", why=_WHY, body={})["body"]
    newest = migration.get("dump_newest")
    totals: list[dict] = []
    if newest:
        until = (datetime.fromisoformat(newest) + timedelta(seconds=1)).isoformat()
        from cairn.devices.inferenceproxy.rename_instance import OLD as recorded_before_the_move
        for src in (recorded_before_the_move, "inferenceproxy"):
            totals += reach("cairn").request(sender="inferenceproxy", to="cairn", verb="metrics",
                                             why=_WHY, body={"source": src, "totals": True,
                                                             "until": until})["body"]["totals"]
    return {"migration": migration, "totals": totals, **judge(migration, totals)}


def _survey(context: dict) -> dict:
    return once(context, "home_meter", survey_home)


def _trigger(now, context: dict) -> bool:
    """TRUE when the home instance no longer carries what the migration dumped."""
    return not _survey(context)["holds"]


def _carry(context: dict) -> dict:
    s = _survey(context)
    return {"finding": "; ".join(s["lacks"]) or f"the home meter carries the dump — {s['line']}",
            "line": s["line"],
            "ticket": owning_ticket(_TICKET_ID),
            "against_falsifier": "98ab0e9db57f clause 7: the old table is gone, the answer tree "
                                 "holds at least 11,366 leaves, the dump exists, and the metrics "
                                 "totals until the dump's newest row equal its spent and avoided",
            "suggests": "read migrate_answers_to_their_tree.report() and the metrics rows under "
                        "both source names; a lost leaf or meter row is the store's to explain"}


PROBE = Probe(
    why="the home instance's answer tree and meter must keep carrying what the migration "
        "dumped; a sealed test run cannot read them, so the home instance watches them",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    verb="machines/watchme/watch",
    carry=watch_carry(_TICKET_ID, _carry, fails=_trigger),
)


if __name__ == "__main__":
    s = survey_home()
    print(json.dumps({"holds": s["holds"], "lacks": s["lacks"], "line": s["line"]}, indent=2))

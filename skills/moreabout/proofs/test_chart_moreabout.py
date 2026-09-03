"""Proof for chart/moreabout.py — the learning door. Teeth a hollow build could not pass:

  - THE WALK SEES DEPOSITED STATE: expand surfaces a seeded node with the resolution
    floor visible and labeled (the n=1 guess says it is one).
  - UNDER-FLOOR HONESTY: a walk whose every node sits under the floor still returns the
    ranked nodes, flagged under_floor with the floor in the note — never collapsed to
    empty (ranking was measured right under the floor, 0.5775, 2026-07-28; laundering
    'under floor' into 'nothing known' is the red).
  - BERTHED STATE ATTACHES ONLY WHAT EXISTS: a provenance source that is a file on disk
    attaches parsed and matching; a non-file source passes through untouched; an
    unreadable file is named loudly — three honest shapes, no fabrication.
  - THE SIGNAL LANDS DATED: the ask becomes a node in the SAME tenant table, provenance
    kind moreabout_signal + date, born hypothesis; the tree grew by exactly one.
  - REFUSALS LEAVE THE TREE WHERE IT STOOD: an undated signal and an empty ask both
    refuse loudly (MoreaboutRefused) and deposit nothing.
  - A REPEAT ASK IS READABLE FREQUENCY: the identical signal again returns
    duplicate:true and writes nothing — dedup as data, not loss.
  - A WALK, NEVER A RE-RUN, BY IMPORT PHYSICS: AST allowlist on moreabout.py — its only
    cairn door is cairn.tools.tree.tree; cairn.devices.codemonkey.machines.orient.orient (the floor/gate machinery),
    the librarian, db_domain, and subprocess are structurally unreachable (the
    charter's falsifier 4 as physics, not prose).

Requires the one-time DB provisioning (as the tree proof does). Self-cleaning: the nonce
tables and their registry rows are dropped. The netns seal does not sever the DB — the
Unix socket is a file (db_domain's documented asymmetry).

    python3 skills/moreabout/proofs/test_chart_moreabout.py     # exit 0 = green
"""
from __future__ import annotations

import ast
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills.moreabout import moreabout as moreabout_mod
from skills.moreabout.moreabout import MoreaboutRefused, expand, signal
from cairn.tools.tree.tree import deposit_learning, nexus_table
from cairn.devices.db_domain import store
from cairn.devices.librarian import trees
from cairn.devices.librarian.loop import RESOLUTION_FLOOR

_STAMP = f"{os.getpid()}_{datetime.now().strftime('%H%M%S')}"
_NEXUS = f"orient_ma_{_STAMP}"          # the near-node corpus
_NEXUS_FAR = f"orient_far_{_STAMP}"     # the under-floor corpus
_TABLES = [nexus_table(_NEXUS), nexus_table(_NEXUS_FAR)]
_PROV = {"source": "proofs/test_chart_moreabout.py", "ground": "fixture"}


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def _state(nexus):
    return trees.tree_state(nexus, table=nexus_table(nexus), owner="chart")


def test_the_walk_sees_deposited_state_floor_labeled():
    deposit_learning(_NEXUS, "the orient nexus berths its packet in instance-space",
                     [1.0, 0.0, 0.0], _PROV)
    got = expand([1.0, 0.0, 0.0], nexus=_NEXUS)
    assert got["expansions"], "the walk sees the deposited node"
    assert got["expansions"][0]["content"].startswith("the orient nexus")
    assert got["floor"] == RESOLUTION_FLOOR, "the floor is imported, not re-minted"
    assert "guess" in got["floor_is"] and "n=1" in got["floor_is"], \
        "the floor's label travels"
    assert got["under_floor"] is False and got["under_floor_note"] is None
    assert got["above_floor"] >= 1


def test_under_floor_is_honest_never_empty():
    deposit_learning(_NEXUS_FAR, "a learning pointing far away from every query",
                     [0.0, 0.0, 1.0], _PROV)
    got = expand([1.0, 0.0, 0.0], nexus=_NEXUS_FAR)
    assert got["expansions"], \
        "an under-floor walk still returns the ranked nodes — never empty-handed"
    assert got["above_floor"] == 0 and got["under_floor"] is True
    note = got["under_floor_note"]
    assert note and "under the floor" in note and str(got["floor"]) in note, \
        "the flag names the floor it sits under"
    assert "nothing known" in note, "the note refuses the laundering by name"


def test_berthed_state_attaches_only_what_exists():
    with tempfile.TemporaryDirectory() as tmp:
        berthed = {"intent": "the deposited packet, whole", "confidence": 0.7}
        path = os.path.join(tmp, "orient-20260728T150000-abcdefabcdef.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(berthed, fh)
        broken = os.path.join(tmp, "broken.json")
        with open(broken, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        deposit_learning(_NEXUS, f"a node whose provenance berths on disk [{_STAMP}]",
                         [0.9, 0.1, 0.0], {"source": path})
        deposit_learning(_NEXUS, f"a node whose provenance names a session, not a file [{_STAMP}]",
                         [0.8, 0.2, 0.0], {"source": "session scans 2026-07-27"})
        deposit_learning(_NEXUS, f"a node whose berth cannot be read [{_STAMP}]",
                         [0.7, 0.3, 0.0], {"source": broken})
        got = expand([0.9, 0.1, 0.0], nexus=_NEXUS, k=10)
        by_content = {e["content"]: e for e in got["expansions"]}
        on_disk = by_content[f"a node whose provenance berths on disk [{_STAMP}]"]
        assert on_disk["berthed"] == berthed, \
            "a file source attaches parsed and matching — deposited state, read"
        session = by_content[f"a node whose provenance names a session, not a file [{_STAMP}]"]
        assert "berthed" not in session and "berthed_unreadable" not in session, \
            "a non-file source passes through untouched — nothing fabricated"
        unreadable = by_content[f"a node whose berth cannot be read [{_STAMP}]"]
        assert "berthed" not in unreadable and unreadable["berthed_unreadable"], \
            "an unreadable berth is named loudly, never silently skipped"


def test_the_signal_lands_dated():
    before = _state(_NEXUS)
    ask = f"moreabout: what did the orient packet's scope actually exclude? [{_STAMP}]"
    r = signal(ask, [0.5, 0.5, 0.0], date="2026-07-28", nexus=_NEXUS,
               about="orient-20260728T110828", field="scope")
    assert r["duplicate"] is False
    rows = store.read(trees.NODES_TABLE, where="node_id = %s",
                      params=(r["node_id"],))
    assert rows and rows[0]["content"] == ask, "the node's content is the ask itself"
    prov = rows[0]["provenance"]
    assert prov["kind"] == "moreabout_signal" and prov["date"] == "2026-07-28"
    assert prov["about"] == "orient-20260728T110828" and prov["field"] == "scope"
    assert rows[0]["standing"] == "hypothesis", "born a hypothesis (inherited physics)"
    after = _state(_NEXUS)
    assert after["nodes"] == before["nodes"] + 1, "the tree grew by exactly one"


def test_refusals_leave_the_tree_where_it_stood():
    before = _state(_NEXUS)
    msg = _refuses(MoreaboutRefused, signal, "a dated-less ask", [1.0, 0.0, 0.0],
                   date="", nexus=_NEXUS)
    assert "date" in msg, "the refusal names the missing date"
    _refuses(MoreaboutRefused, signal, "   ", [1.0, 0.0, 0.0],
             date="2026-07-28", nexus=_NEXUS)
    assert _state(_NEXUS) == before, \
        "a refused signal must leave the tree exactly where it stood"


def test_a_repeat_ask_is_readable_frequency():
    ask = f"moreabout: what did the orient packet's scope actually exclude? [{_STAMP}]"
    before = _state(_NEXUS)
    r = signal(ask, [0.5, 0.5, 0.0], date="2026-07-28", nexus=_NEXUS,
               about="orient-20260728T110828", field="scope")
    assert r["duplicate"] is True, "the identical ask again reads as frequency"
    assert _state(_NEXUS) == before, "and writes nothing"


def test_a_walk_never_a_rerun_import_physics():
    # Composed over orient's import_map (installed 2026-07-28): the allowlist
    # matches the module that ACTUALLY ENTERS, not the spelling.
    from cairn.tools.orient.orient import import_map
    allow = ("__future__", "json", "os", "cairn.tools.tree.tree")
    seen = import_map(moreabout_mod.__file__)["measured"]["imports"]
    offenders = [m for m in seen
                 if not any(m == p or m.startswith(p + ".") for p in allow)]
    assert not offenders, (
        f"moreabout.py imports outside its allowlist: {offenders} — the walk's only "
        "cairn door is chart's tree verbs")
    for forbidden in ("cairn.devices.codemonkey.machines.orient.orient", "cairn.devices.librarian", "cairn.devices.db_domain",
                      "subprocess"):
        assert not any(m == forbidden or m.startswith(forbidden + ".")
                       for m in seen), (
            f"moreabout.py reaches {forbidden} — a re-run (or a second door) is the "
            "charter's falsifier 4; the door walks, it never re-runs")


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            for t in _TABLES:
                cur.execute(f'DROP TABLE IF EXISTS "{t}"')
                cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_the_walk_sees_deposited_state_floor_labeled,
        test_under_floor_is_honest_never_empty,
        test_berthed_state_attaches_only_what_exists,
        test_the_signal_lands_dated,
        test_refusals_leave_the_tree_where_it_stood,
        test_a_repeat_ask_is_readable_frequency,
        test_a_walk_never_a_rerun_import_physics,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — chart/moreabout: the walk sees deposited state under a labeled "
          "floor, under-floor is honest never empty, berths attach only what exists, "
          "the signal lands dated and dedups readably, refusals leave the tree "
          "standing, and a re-run is impossible by import physics")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

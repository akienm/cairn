"""Proof for chart/tree.py + chart/dial.py — the tree stratum and the dial. Teeth a
hollow build could not pass:

  - THE TABLE IS BORN OWNED BY CHART: the nexus's table registers under owner 'chart',
    and a write wearing any other name is refused by db_domain's physics, not manners.
  - GATE BEFORE SEED: a malformed packet never reaches the tree (validate_orient runs at
    the deposit-back door), and a berth path that does not exist on disk refuses — a node
    whose provenance points at nothing is fabricated attribution one layer up.
  - DEPOSIT-BACK LANDS HONESTLY: content is the packet's intent, provenance names the
    berth, standing is hypothesis (inherited physics); a duplicate writes nothing.
  - COUNSEL KEEPS ITS FLOOR VISIBLE: the resolution floor rides every answer, labeled as
    the n=1 guess it is; above_floor holds only nodes at/above it; an empty tree is an
    honest empty counsel, not an error.
  - A NEXUS NAME IS IDENTITY: a name outside the class refuses — no table is minted for
    a name that cannot be one.
  - THE LIBRARIAN'S TOOLS ARE THE ONLY DOOR: AST allowlists on tree.py and dial.py — no
    direct db_domain, no network (the stone-1 composition lesson, one layer up).
  - THE DIAL READS TRUE: exact fractions on a synthetic berth, series in time order,
    unreadable packets reported by name (never silently skipped), an absent berth a
    nameable state, and the REAL berth checked by invariant (fractions sum to 1) — never
    by pinned value (live data moves; pinning it re-derives noise).
  - 'tree' IS A LEGAL STRATUM at the packet gate — the seam the ceiling writes through.

Requires the one-time DB provisioning (as the librarian's trees proof does). Self-cleaning:
the nonce table and its registry row are dropped. The netns seal does not sever the DB —
the Unix socket is a file (db_domain's documented asymmetry).

    python3 cairn/tools/tree/proofs/test_chart_tree.py     # exit 0 = green
"""
from __future__ import annotations

import ast
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills.chart import dial as dial_mod
from cairn.tools.tree import tree
from skills.chart.dial import dial
from cairn.tools.chain.grammar import (STRATA)
from cairn.devices.builder.machines.orient.orient import (OrientRefused, deposit_orient)
from cairn.tools.tree.tree import (
    TreeRefused, counsel, deposit_learning, nexus_table,
)
from cairn.devices.db_domain import store
from cairn.devices.db_domain.store import OwnershipError
from cairn.devices.librarian import trees
from cairn.devices.librarian.loop import RESOLUTION_FLOOR

_NEXUS = f"orient_{os.getpid()}_{datetime.now().strftime('%H%M%S')}"
_TABLE = nexus_table(_NEXUS)
_PROV = {"source": "proofs/test_chart_tree.py", "ground": "fixture"}


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def _packet(intent="wire the tree stratum into the orient nexus of the chart device",
            **over):
    p = {
        "intent": intent,
        "domain": "chart — the nexus machinery",
        "scope": "IN: the orient nexus's tree. OUT: everything else.",
        # A LIVE ref, and it must stay live: validate_orient refuses an unverifiable
        # ref BEFORE it reaches the berth check, so a fixture naming a component that
        # has stopped existing reds the berth tooth with the wrong reason. "chart"
        # stood here until 2026-08-13, when the decomposition made it a skill and not
        # a component; "tree" is the component this proof is about.
        "refs": ["tree"],
        "unknowns": [],
        "confidence": 0.7,
        # ONLY THE TWO THE DOOR DOES NOT MEASURE. It carried "refs": "floor" until
        # 2026-08-14, when provenance for refs/domain/unknowns stopped being the
        # sender's to write (ticket orient-floor-authors-and-provenance-is-measured) —
        # validate_orient now derives those by re-running the floor, and a fixture that
        # declares one gets refused for THAT rather than for the thing the tooth is
        # about, which is how this proof found the change.
        "provenance": {"intent": "claude", "scope": "claude"},
    }
    p.update(over)
    return p


def _berthed_fixture(tmp: str, packet: dict) -> str:
    path = os.path.join(tmp, "orient-20260728T120000-feedfacecafe.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(packet, fh)
    return path


def test_a_nexus_name_is_identity():
    for bad in ("Orient", "a-b", "", "9lives", None, 12):
        _refuses(TreeRefused, nexus_table, bad)
    assert nexus_table("orient") == "chart_orient_nodes"


def test_the_table_is_born_owned_by_chart():
    r = deposit_learning(_NEXUS, "the first learning of a chart-owned tree",
                         [1.0, 0.0, 0.0], _PROV)
    assert r["duplicate"] is False
    assert store.owner_of(_TABLE) == "chart", \
        "the nexus's table must register under owner 'chart' at birth (Law 6)"
    try:
        store.write(_TABLE, "librarian", {
            "node_id": "forced", "tree": _NEXUS, "content": "should never land",
            "vector": [1.0], "provenance": {"source": "x"}, "standing": "hypothesis"})
        raise AssertionError("a non-chart write must be REFUSED by db_domain (Law 6)")
    except OwnershipError:
        pass


def test_gate_before_seed():
    before = trees.tree_state(_NEXUS, table=_TABLE, owner="chart")
    with tempfile.TemporaryDirectory() as tmp:
        berth = _berthed_fixture(tmp, _packet())
        # A malformed packet (missing a required field) never reaches the tree.
        broken = _packet()
        del broken["confidence"]
        _refuses(OrientRefused, deposit_orient, broken, [1.0, 0.0, 0.0], berth_path=berth)
        # A berth that does not exist on disk refuses — provenance may not point at nothing.
        msg = _refuses(OrientRefused, deposit_orient, _packet(), [1.0, 0.0, 0.0],
                       berth_path=os.path.join(tmp, "no-such-berth.json"))
        assert "does not exist" in msg
    assert trees.tree_state(_NEXUS, table=_TABLE, owner="chart") == before, \
        "a refused deposit-back must leave the tree exactly where it stood"


def test_deposit_back_lands_and_dedups():
    with tempfile.TemporaryDirectory() as tmp:
        packet = _packet()
        berth = _berthed_fixture(tmp, packet)
        r = deposit_orient(packet, [0.9, 0.1, 0.0], berth_path=berth, nexus=_NEXUS)
        _CREATED_NODES.append(r["node_id"])
        assert r["duplicate"] is False
        node_rows = store.read(trees.NODES_TABLE, where="node_id = %s", params=(r["node_id"],))
        assert node_rows and node_rows[0]["content"] == packet["intent"], \
            "the node's content is the packet's intent"
        assert node_rows[0]["provenance"]["source"] == berth, "provenance names the berth"
        assert node_rows[0]["provenance"]["confidence"] == packet["confidence"]
        assert node_rows[0]["standing"] == "hypothesis", "born a hypothesis (inherited physics)"
        leaf_rows = store.read(_TABLE, where="node_id = %s", params=(r["node_id"],))
        assert leaf_rows, "a leaf must land in the nexus's table"
        # The same packet again: a duplicate writes nothing (Law 1).
        before = trees.tree_state(_NEXUS, table=_TABLE, owner="chart")
        r2 = deposit_orient(packet, [0.9, 0.1, 0.0], berth_path=berth, nexus=_NEXUS)
        assert r2["duplicate"] is True
        assert trees.tree_state(_NEXUS, table=_TABLE, owner="chart") == before


def test_counsel_keeps_its_floor_visible():
    # An empty tree is an honest empty counsel.
    got = counsel([1.0, 0.0, 0.0], nexus=f"{_NEXUS}_empty")
    assert got["walk"] == [] and got["above_floor"] == []
    assert got["floor"] == RESOLUTION_FLOOR, "the floor is imported, not re-minted"
    assert "guess" in got["floor_is"] and "n=1" in got["floor_is"], \
        "the floor's label travels — a guess must say it is one"
    # A populated tree: above_floor holds only nodes at/above the floor.
    r_far = deposit_learning(_NEXUS, "a learning pointing far away from the query",
                             [0.0, 0.0, 1.0], _PROV)
    _CREATED_NODES.append(r_far["node_id"])
    got = counsel([0.9, 0.1, 0.0], nexus=_NEXUS, k=10)
    assert got["walk"], "the walk sees the tree"
    assert all(n["similarity"] >= got["floor"] for n in got["above_floor"])
    assert all(n["similarity"] < got["floor"]
               for n in got["walk"] if n not in got["above_floor"])


def test_the_librarians_tools_are_the_only_door():
    allowed = {
        tree.__file__: ("__future__", "os", "re", "cairn.devices.builder.machines.orient.orient",
                        "cairn.devices.librarian.trees", "cairn.devices.librarian.loop"),
        # cairn.devices.builder.machines.constrain.constrain joined 2026-07-28 (chart-constrain), cairn.devices.builder.machines.survey.survey
        # and cairn.devices.builder.machines.decompose.decompose the same day (chart-survey, chart-decompose),
        # cairn.devices.builder.machines.triage.triage the same day again (chart-triage), then
        # cairn.devices.builder.machines.hypothesize.hypothesize and cairn.devices.builder.machines.validate.validate (chart-hypothesize,
        # chart-validate — the chain complete): the dial reads each stage's
        # packets against that stage's own field-shape — a stage registers here
        # when it lands.
        dial_mod.__file__: ("__future__", "json", "os", "re", "sys",
                            "cairn.devices.builder.machines.constrain.constrain", "cairn.devices.builder.machines.decompose.decompose",
                            "cairn.devices.builder.machines.hypothesize.hypothesize", "cairn.devices.builder.machines.orient.orient",
                            "cairn.tools.chain.grammar",
                            "cairn.devices.builder.machines.survey.survey", "cairn.devices.builder.machines.triage.triage",
                            "cairn.devices.builder.machines.validate.validate"),
    }
    # Composed over orient's import_map (installed 2026-07-28 through the brick loop,
    # seeded by THIS tooth's own twice-fired red): the allowlist matches the module
    # that ACTUALLY ENTERS, not the spelling.
    from cairn.tools.orient.orient import import_map
    for path, allow in allowed.items():
        seen = import_map(path)["measured"]["imports"]
        offenders = [m for m in seen
                     if not any(m == p or m.startswith(p + ".") for p in allow)]
        assert not offenders, (
            f"{Path(path).name} imports outside its allowlist: {offenders} — the tree is "
            "reached only through the librarian's tools, and the dial only reads the berth")


def _dial_fixture(tmp: str) -> None:
    packets = [
        ("orient-20260728T100000-aaaaaaaaaaaa.json",
         {"intent": "claude", "domain": "claude", "scope": "claude",
          "refs": "floor", "unknowns": "claude"}),          # floor .2 tree .0 claude .8
        ("orient-20260728T110000-bbbbbbbbbbbb.json",
         {"intent": "tree", "domain": "tree", "scope": "claude",
          "refs": "floor", "unknowns": "floor"}),           # floor .4 tree .4 claude .2
        ("orient-20260728T120000-cccccccccccc.json",
         {"intent": "floor", "domain": "tree", "scope": "tree",
          "refs": "floor", "unknowns": "tree"}),            # floor .4 tree .6 claude .0
    ]
    for name, prov in packets:
        with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
            json.dump(_packet(provenance=prov), fh)


def test_the_dial_reads_exact_fractions_in_time_order():
    with tempfile.TemporaryDirectory() as tmp:
        _dial_fixture(tmp)
        got = dial(tmp)
        assert got["packets"] == 3 and got["unreadable"] == []
        series = got["nexi"]["orient"]["series"]
        assert [e["at"] for e in series] == sorted(e["at"] for e in series), \
            "the series is in time order — the stamp rides the filename"
        assert (series[0]["floor"], series[0]["tree"], series[0]["claude"]) == (0.2, 0.0, 0.8)
        assert (series[1]["floor"], series[1]["tree"], series[1]["claude"]) == (0.4, 0.4, 0.2)
        assert (series[2]["floor"], series[2]["tree"], series[2]["claude"]) == (0.4, 0.6, 0.0)
        agg = got["nexi"]["orient"]["aggregate"]
        assert abs(sum(agg.values()) - 1.0) < 1e-9
        assert abs(agg["tree"] - (0.0 + 0.4 + 0.6) / 3) < 1e-9


def test_the_dial_reports_unreadable_never_skips():
    with tempfile.TemporaryDirectory() as tmp:
        _dial_fixture(tmp)
        with open(os.path.join(tmp, "orient-20260728T130000-dddddddddddd.json"),
                  "w", encoding="utf-8") as fh:
            fh.write("{not json")
        hole = _packet()
        del hole["provenance"]["scope"]
        with open(os.path.join(tmp, "orient-20260728T140000-eeeeeeeeeeee.json"),
                  "w", encoding="utf-8") as fh:
            json.dump(hole, fh)
        got = dial(tmp)
        assert got["packets"] == 3, "readable packets still count"
        assert len(got["unreadable"]) == 2, "both failures reported, neither skipped"
        names = {u["packet"] for u in got["unreadable"]}
        assert names == {"orient-20260728T130000-dddddddddddd.json",
                         "orient-20260728T140000-eeeeeeeeeeee.json"}
        assert all(u["why"] for u in got["unreadable"]), "every failure names its why"


def test_an_absent_berth_is_a_nameable_state():
    got = dial("/nonexistent/berth/for/this/proof")
    assert got["packets"] == 0 and got["nexi"] == {} and got["unreadable"] == []


def test_the_real_berth_by_invariant():
    # Live data moves — assert SHAPE, never pinned values (a pinned moving value turns a
    # normal step into a spurious red; the test_transitions lesson).
    got = dial()
    total = 0
    for nexus, reading in got["nexi"].items():
        assert reading["packets"] == len(reading["series"])
        total += reading["packets"]
        for entry in reading["series"]:
            assert abs(sum(entry[s] for s in STRATA) - 1.0) < 1e-6, \
                f"fractions must sum to 1 ({entry['packet']})"
        assert set(reading["aggregate"]) == set(STRATA)
    assert got["packets"] == total


def test_tree_is_a_legal_stratum_at_the_packet_gate():
    from cairn.devices.builder.machines.orient.orient import (validate_orient)
    p = _packet(provenance={"intent": "tree", "domain": "tree", "scope": "tree",
                            "unknowns": "tree"})
    assert validate_orient(p) is p, "the ceiling writes 'tree' through the standing gate"
    # A 'tree' DECLARATION SURVIVES THE FLOOR MEASUREMENT, and this is the clause the
    # 2026-08-14 door had to be careful about: it derives ``floor`` vs ``claude`` and
    # nothing else, so a field the ceiling says came from the TREE keeps saying so. The
    # alternative — overwriting every unreproducible field with ``claude`` — would trade
    # one wrong label for another and erase the only stratum the tree walk can claim.
    assert p["provenance"]["domain"] == "tree", p["provenance"]
    assert p["provenance"]["unknowns"] == "tree", p["provenance"]
    assert p["provenance"]["refs"] == "claude", \
        "an undeclared floor-authored field is derived, and this packet carries no request"


_CREATED_NODES: list[str] = []


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            for t in (_TABLE, nexus_table(f"{_NEXUS}_empty")):
                cur.execute(f'DROP TABLE IF EXISTS "{t}"')
                cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (t,))
            for nid in _CREATED_NODES:
                cur.execute(f'DELETE FROM "{trees.EMBEDDINGS_TABLE}" WHERE node_id = %s', (nid,))
                cur.execute(f'DELETE FROM "{trees.NODES_TABLE}" WHERE node_id = %s', (nid,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_a_nexus_name_is_identity,
        test_the_table_is_born_owned_by_chart,
        test_gate_before_seed,
        test_deposit_back_lands_and_dedups,
        test_counsel_keeps_its_floor_visible,
        test_the_librarians_tools_are_the_only_door,
        test_the_dial_reads_exact_fractions_in_time_order,
        test_the_dial_reports_unreadable_never_skips,
        test_an_absent_berth_is_a_nameable_state,
        test_the_real_berth_by_invariant,
        test_tree_is_a_legal_stratum_at_the_packet_gate,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — chart/tree + chart/dial: the table is born chart's, the gate runs "
          "before the seed, deposit-back lands honest and dedups, counsel keeps its "
          "labeled floor, the librarian's tools are the only door, and the dial reads "
          "true — exact on fixtures, by invariant on the live berth")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

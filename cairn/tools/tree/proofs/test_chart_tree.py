"""Proof for chart/tree.py + chart/dial.py — the tree stratum and the dial. Teeth a
hollow build could not pass:

  - THE TABLE IS BORN OWNED BY CHART: the nexus's table registers under owner 'chart',
    and a write wearing any other name is refused by db_domain's physics, not manners.
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
  The orient teeth (gate before seed, deposit-back, codemother's leaf, 'tree' a legal
  stratum) measure orient and live beside it since ticket a692614a4654:
  cairn/devices/codemother/machines/orient/proofs/test_orient_deposits_into_the_tree.py.

Requires the one-time DB provisioning (as the librarian's trees proof does). Self-cleaning:
the nonce table and its registry row are dropped. The netns seal does not sever the DB —
the Unix socket is a file (db_domain's documented asymmetry).

    python3 cairn/tools/tree/proofs/test_chart_tree.py     # exit 0 = green
"""
from __future__ import annotations

import contextlib
import ast
import json
import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills.chart import dial as dial_mod
from cairn.tools.tree import tree
from skills.chart.dial import dial
from cairn.tools.chain.grammar import (STRATA)
from cairn.tools.tree.tree import (
    TreeRefused, counsel, deposit_learning, nexus_table, scratch_nexus,
)
from cairn.devices.db_domain.tools.client import store
from cairn.devices.db_domain.tools.client.store import OwnershipError
from cairn.devices.librarian.tools.trees import trees
from cairn.devices.librarian.tools.trees.trees import RESOLUTION_FLOOR

# The falsifier of 9c46e187f2de is one unnumbered clause, so one composite tooth carries it.
PROVES = {
}

_SCRATCH = contextlib.ExitStack()   # the nexus tables this run mints ride store.scratch(): dropped at close, swept by pid if not
_HELD: list[tuple[str, str]] = []   # (nexus name, owner) — each forgotten under its own owner at close


def _nexus() -> str:
    """This run's own chart-owned nexus, minted on first use through tree.scratch_nexus()."""
    if not any(o == "chart" for _, o in _HELD):
        _HELD.append((_SCRATCH.enter_context(scratch_nexus("orient")), "chart"))
    return next(n for n, o in _HELD if o == "chart")


def _table() -> str:
    return nexus_table(_nexus())


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
        # ALL FIVE AUTHORED FIELDS, because this fixture stands for a BERTHED packet.
        # The write door (validate_orient with measure_provenance=True) refuses a
        # sender that declares refs/domain/unknowns and stamps them itself (ticket
        # orient-floor-authors-and-provenance-is-measured, 2026-08-14); the deposit
        # door (measure_provenance=False, since ticket 4c022c44de53) measures nothing
        # and REQUIRES coverage of every authored field — a berthed packet always has
        # it. A fixture carrying only intent/scope was refused with "provenance does
        # not cover: domain, refs, unknowns" one lack BEFORE the berth-existence check,
        # so the berth tooth asserted a refusal the door never reached (ticket
        # 9c46e187f2de). 'cc' is an accepted stratum; the value is not what the tooth
        # measures, the coverage is.
        "provenance": {"intent": "cc", "scope": "cc",
                       "domain": "cc", "refs": "cc", "unknowns": "cc"},
    }
    p.update(over)
    return p


def test_a_nexus_name_is_identity():
    for bad in ("Orient", "a-b", "", "9lives", None, 12):
        _refuses(TreeRefused, nexus_table, bad)
    assert nexus_table("orient") == "chart_orient_nodes"


def test_the_table_is_born_owned_by_chart():
    r = deposit_learning(_nexus(), "the first learning of a chart-owned tree",
                         [1.0, 0.0, 0.0], _PROV)
    assert r["duplicate"] is False
    assert store.owner_of(_table()) == "chart", \
        "the nexus's table must register under owner 'chart' at birth (Law 6)"
    try:
        store.write(_table(), "librarian", {
            "node_id": "forced", "tree": _nexus(), "content": "should never land",
            "vector": [1.0], "provenance": {"source": "x"}, "standing": "hypothesis"})
        raise AssertionError("a non-chart write must be REFUSED by db_domain (Law 6)")
    except OwnershipError:
        pass


def test_counsel_keeps_its_floor_visible():
    # An empty tree is an honest empty counsel.
    with scratch_nexus("orient_empty") as empty:     # a nexus nobody deposited into
        got = counsel([1.0, 0.0, 0.0], nexus=empty)
    assert got["walk"] == [] and got["above_floor"] == []
    assert got["floor"] == RESOLUTION_FLOOR, "the floor is imported, not re-minted"
    assert "guess" in got["floor_is"] and "n=1" in got["floor_is"], \
        "the floor's label travels — a guess must say it is one"
    # A populated tree: above_floor holds only nodes at/above the floor.
    r_far = deposit_learning(_nexus(), "a learning pointing far away from the query",
                             [0.0, 0.0, 1.0], _PROV)
    _CREATED_NODES.append(r_far["node_id"])
    got = counsel([0.9, 0.1, 0.0], nexus=_nexus(), k=10)
    assert got["walk"], "the walk sees the tree"
    assert all(n["similarity"] >= got["floor"] for n in got["above_floor"])
    assert all(n["similarity"] < got["floor"]
               for n in got["walk"] if n not in got["above_floor"])


def test_the_librarians_tools_are_the_only_door():
    allowed = {
        tree.__file__: ("__future__", "contextlib", "os", "re",   # contextlib: scratch_nexus (201a37bf1613)
                        "cairn.devices.codemother.machines.orient.orient",
                        "cairn.devices.librarian.tools.trees.trees", "cairn.devices.librarian.loop"),
        # cairn.devices.codemother.machines.constrain.constrain joined 2026-07-28 (chart-constrain), cairn.devices.codemother.machines.survey.survey
        # and cairn.devices.codemother.machines.decompose.decompose the same day (chart-survey, chart-decompose),
        # cairn.devices.codemother.machines.triage.triage the same day again (chart-triage), then
        # cairn.devices.codemother.machines.hypothesize.hypothesize and cairn.devices.codemother.machines.validate.validate (chart-hypothesize,
        # chart-validate — the chain complete): the dial reads each stage's
        # packets against that stage's own field-shape — a stage registers here
        # when it lands.
        dial_mod.__file__: ("__future__", "json", "os", "re", "sys",
                            "cairn.devices.codemother.machines.constrain.constrain", "cairn.devices.codemother.machines.decompose.decompose",
                            "cairn.devices.codemother.machines.hypothesize.hypothesize", "cairn.devices.codemother.machines.orient.orient",
                            "cairn.tools.chain.grammar",
                            "cairn.devices.codemother.machines.survey.survey", "cairn.devices.codemother.machines.triage.triage",
                            "cairn.devices.codemother.machines.validate.validate"),
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
         {"intent": "cc", "domain": "cc", "scope": "cc",
          "refs": "floor", "unknowns": "cc"}),          # floor .2 tree .0 claude .8
        ("orient-20260728T110000-bbbbbbbbbbbb.json",
         {"intent": "tree", "domain": "tree", "scope": "cc",
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
        assert (series[0]["floor"], series[0]["tree"], series[0]["cc"]) == (0.2, 0.0, 0.8)
        assert (series[1]["floor"], series[1]["tree"], series[1]["cc"]) == (0.4, 0.4, 0.2)
        assert (series[2]["floor"], series[2]["tree"], series[2]["cc"]) == (0.4, 0.6, 0.0)
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


_CREATED_NODES: list[str] = []


def _main() -> int:
    checks = [
        test_a_nexus_name_is_identity,
        test_the_table_is_born_owned_by_chart,
        test_counsel_keeps_its_floor_visible,
        test_the_librarians_tools_are_the_only_door,
        test_the_dial_reads_exact_fractions_in_time_order,
        test_the_dial_reports_unreadable_never_skips,
        test_an_absent_berth_is_a_nameable_state,
        test_the_real_berth_by_invariant,
    ]
    failed = []
    try:
        for check in checks:     # every tooth runs and reports: a tooth's failure is its verdict
            try:
                check()
                print(f"  PASS  {check.__name__}", flush=True)
            except Exception:    # noqa: BLE001 — loud, named, and counted (Law 7)
                import traceback
                traceback.print_exc()
                print(f"  FAIL  {check.__name__}", flush=True)
                failed.append(check.__name__)
    finally:
        for name, owner in _HELD:     # this run's rows out of the shared tables, then the scratch nexi dropped
            trees.forget_leaf(nexus_table(name, owner=owner))
        _SCRATCH.close()
    if failed:
        print(f"RED — {len(failed)} failure(s): {', '.join(failed)}")
        return 1
    print("green — chart/tree + chart/dial: the table is born chart's, counsel keeps its "
          "labeled floor, the librarian's tools are the only door, and the dial reads "
          "true — exact on fixtures, by invariant on the live berth")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

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
    cairn door is cairn.tools.tree.tree; cairn.devices.codemother.machines.orient.orient (the floor/gate machinery),
    the librarian, db_domain, and subprocess are structurally unreachable (the
    charter's falsifier 4 as physics, not prose).

  - EVERY WALK TOOTH RUNS OVER SCRATCH NEXI (ticket 4055324b8d34, outcome 1): the seven above
    run, each printed by name, over the two nexi tree.scratch_nexus() minted.
  - THE RUN'S NEXI ARE SCRATCH (outcome 2): both nexus tables carry a cairn_scratch row under
    this run's pid while it holds them, and no line of this proof mints or drops one by hand.
  - A KILLED RUN LEAVES NOTHING THE SWEEP CANNOT TAKE (outcome 3): a child that deposits into both nexi
    and is SIGKILLed before any close leaves its tables registered under its pid, and
    store.sweep_scratch() drops both.

Requires the one-time DB provisioning (as the tree proof does). Self-cleaning: the nexi
ride tree.scratch_nexus(), so _main's close drops them and a run that never reaches it is
swept by pid; this run's nodes leave the shared tables first. The netns seal does not sever the DB — the
Unix socket is a file (db_domain's documented asymmetry).

    python3 skills/moreabout/proofs/test_chart_moreabout.py     # exit 0 = green
"""
from __future__ import annotations

import ast
import contextlib
import json
import os
import signal as _signal
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills.moreabout import moreabout as moreabout_mod
from skills.moreabout.moreabout import MoreaboutRefused, expand, signal
from cairn.tools.tree.tree import deposit_learning, nexus_table, scratch_nexus
from cairn.devices.db_domain.tools.client import store
from cairn.devices.librarian.tools.trees import trees
from cairn.devices.librarian.tools.trees.trees import RESOLUTION_FLOOR

PROVES = {"4055324b8d34": {
    "1": "test_every_walk_tooth_runs_over_scratch_nexi",
    "2": "test_the_runs_nexi_are_registered_scratch_under_its_pid",
    "3": "test_a_killed_run_leaves_tables_the_sweep_takes",
}}

_STAMP = f"{os.getpid()}_{datetime.now().strftime('%H%M%S')}"   # content nonce, never a table name
# The two nexi this run deposits into ride tree.scratch_nexus() (ticket 4055324b8d34): minted
# on first use inside the run, registered under this pid, dropped when _main closes the stack,
# and swept by pid when a run dies before it gets there. Nothing is named at import.
_SCRATCH = contextlib.ExitStack()
_HELD: dict[str, str] = {}             # kind -> nexus name


def _held(kind: str) -> str:
    if kind not in _HELD:
        _HELD[kind] = _SCRATCH.enter_context(scratch_nexus(kind, owner=moreabout_mod.OWNER))
    return _HELD[kind]


def _near() -> str:
    """The near-node corpus."""
    return _held("orient_ma")


def _far() -> str:
    """The under-floor corpus."""
    return _held("orient_far")
_PROV = {"source": "proofs/test_chart_moreabout.py", "ground": "fixture"}


def _refuses(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc as e:
        return str(e)
    raise AssertionError(f"{fn.__name__} must refuse with {exc.__name__} — it did not")


def _state(nexus):
    return trees.tree_state(nexus, table=nexus_table(nexus, owner=moreabout_mod.OWNER),
                            owner=moreabout_mod.OWNER)


def test_the_walk_sees_deposited_state_floor_labeled():
    deposit_learning(_near(), "the orient nexus berths its packet in instance-space",
                     [1.0, 0.0, 0.0], _PROV, owner=moreabout_mod.OWNER)
    got = expand([1.0, 0.0, 0.0], nexus=_near())
    assert got["expansions"], "the walk sees the deposited node"
    assert got["expansions"][0]["content"].startswith("the orient nexus")
    assert got["floor"] == RESOLUTION_FLOOR, "the floor is imported, not re-minted"
    assert "guess" in got["floor_is"] and "n=1" in got["floor_is"], \
        "the floor's label travels"
    assert got["under_floor"] is False and got["under_floor_note"] is None
    assert got["above_floor"] >= 1


def test_under_floor_is_honest_never_empty():
    deposit_learning(_far(), "a learning pointing far away from every query",
                     [0.0, 0.0, 1.0], _PROV, owner=moreabout_mod.OWNER)
    got = expand([1.0, 0.0, 0.0], nexus=_far())
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
        deposit_learning(_near(), f"a node whose provenance berths on disk [{_STAMP}]",
                         [0.9, 0.1, 0.0], {"source": path}, owner=moreabout_mod.OWNER)
        deposit_learning(_near(), f"a node whose provenance names a session, not a file [{_STAMP}]",
                         [0.8, 0.2, 0.0], {"source": "session scans 2026-07-27"},
                         owner=moreabout_mod.OWNER)
        deposit_learning(_near(), f"a node whose berth cannot be read [{_STAMP}]",
                         [0.7, 0.3, 0.0], {"source": broken}, owner=moreabout_mod.OWNER)
        got = expand([0.9, 0.1, 0.0], nexus=_near(), k=10)
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
    before = _state(_near())
    ask = f"moreabout: what did the orient packet's scope actually exclude? [{_STAMP}]"
    r = signal(ask, [0.5, 0.5, 0.0], date="2026-07-28", nexus=_near(),
               about="orient-20260728T110828", field="scope")
    assert r["duplicate"] is False
    rows = store.read(trees.NODES_TABLE, where="node_id = %s",
                      params=(r["node_id"],))
    assert rows and rows[0]["content"] == ask, "the node's content is the ask itself"
    prov = rows[0]["provenance"]
    assert prov["kind"] == "moreabout_signal" and prov["date"] == "2026-07-28"
    assert prov["about"] == "orient-20260728T110828" and prov["field"] == "scope"
    assert rows[0]["standing"] == "hypothesis", "born a hypothesis (inherited physics)"
    after = _state(_near())
    assert after["nodes"] == before["nodes"] + 1, "the tree grew by exactly one"


def test_refusals_leave_the_tree_where_it_stood():
    before = _state(_near())
    msg = _refuses(MoreaboutRefused, signal, "a dated-less ask", [1.0, 0.0, 0.0],
                   date="", nexus=_near())
    assert "date" in msg, "the refusal names the missing date"
    _refuses(MoreaboutRefused, signal, "   ", [1.0, 0.0, 0.0],
             date="2026-07-28", nexus=_near())
    assert _state(_near()) == before, \
        "a refused signal must leave the tree exactly where it stood"


def test_a_repeat_ask_is_readable_frequency():
    ask = f"moreabout: what did the orient packet's scope actually exclude? [{_STAMP}]"
    before = _state(_near())
    r = signal(ask, [0.5, 0.5, 0.0], date="2026-07-28", nexus=_near(),
               about="orient-20260728T110828", field="scope")
    assert r["duplicate"] is True, "the identical ask again reads as frequency"
    assert _state(_near()) == before, "and writes nothing"


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
    for forbidden in ("cairn.devices.codemother.machines.orient.orient", "cairn.devices.librarian", "cairn.devices.db_domain",
                      "subprocess"):
        assert not any(m == forbidden or m.startswith(forbidden + ".")
                       for m in seen), (
            f"moreabout.py reaches {forbidden} — a re-run (or a second door) is the "
            "charter's falsifier 4; the door walks, it never re-runs")


_WALK_TEETH = (
    "test_the_walk_sees_deposited_state_floor_labeled",
    "test_under_floor_is_honest_never_empty",
    "test_berthed_state_attaches_only_what_exists",
    "test_the_signal_lands_dated",
    "test_refusals_leave_the_tree_where_it_stood",
    "test_a_repeat_ask_is_readable_frequency",
    "test_a_walk_never_a_rerun_import_physics",
)


def test_every_walk_tooth_runs_over_scratch_nexi():
    failed = []
    for name in _WALK_TEETH:     # each keeps its own claim and prints by name (Law 7)
        try:
            globals()[name]()
            print(f"  PASS  {name}", flush=True)
        except Exception:        # noqa: BLE001 — named and counted, the composite reds
            import traceback
            traceback.print_exc()
            print(f"  FAIL  {name}", flush=True)
            failed.append(name)
    assert not failed, f"walk teeth red over scratch nexi: {failed}"
    assert set(_HELD) == {"orient_ma", "orient_far"}, \
        f"the walk ran over nexi not minted by scratch_nexus: {_HELD}"


def test_the_runs_nexi_are_registered_scratch_under_its_pid():
    tables = {nexus_table(_near(), owner=moreabout_mod.OWNER),
              nexus_table(_far(), owner=moreabout_mod.OWNER)}
    rows = {r["table_name"]: r for r in store.scratch_rows()}
    missing = sorted(t for t in tables if t not in rows)
    assert not missing, f"this run's nexus tables carry no cairn_scratch row: {missing}"
    pids = {t: rows[t]["pid"] for t in tables}
    assert set(pids.values()) == {os.getpid()}, \
        f"registered under {pids}, the run is pid {os.getpid()}"
    # and no name in this proof mints or drops a table by hand: no DROP, no registry row
    # touched, and nexus_table() is never called at module level (a name minted at import).
    tree_ = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    hand = [n.value for n in ast.walk(tree_)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and ("DROP" + " TABLE") in n.value.upper()]
    hand += [ast.unparse(n) for n in ast.walk(tree_)
             if isinstance(n, ast.Attribute) and n.attr == "_REGISTRY"]
    hand += [ast.unparse(n) for top in tree_.body if not isinstance(top, (ast.FunctionDef, ast.If))
             for n in ast.walk(top)
             if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "nexus_table"]
    assert not hand, f"the proof still mints or drops a table by hand: {hand}"


# A run killed before _main's close: the child imports this proof, deposits one node into
# each nexus the way the teeth do, says its tables, and waits to be killed.
_KILLED = r"""
import json, sys, time
sys.path.insert(0, sys.argv[1])
import runpy
mod = runpy.run_path(sys.argv[2], run_name="killed_run")
from cairn.tools.tree.tree import deposit_learning, nexus_table
owner = mod["moreabout_mod"].OWNER
names = [mod["_near"](), mod["_far"]()]
for n in names:
    deposit_learning(n, "a node a killed run deposited", [1.0, 0.0, 0.0],
                     {"source": "proofs/test_chart_moreabout.py", "ground": "fixture"}, owner=owner)
print(json.dumps([nexus_table(n, owner=owner) for n in names]), flush=True)
time.sleep(60)
"""


def test_a_killed_run_leaves_tables_the_sweep_takes():
    from cairn.devices.librarian.tools.trees.trees import forget_leaf
    child = subprocess.Popen([sys.executable, "-c", _KILLED, str(_REPO_ROOT), __file__],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        said = child.stdout.readline()
    finally:
        child.send_signal(_signal.SIGKILL)
        child.wait(timeout=30)
    assert said.strip(), f"the killed run named no tables: {child.stderr.read()[-800:]}"
    tables = json.loads(said)
    try:
        for t in tables:
            assert store.owner_of(t) is not None, f"{t} was never minted"
        rows = {r["table_name"]: r["pid"] for r in store.scratch_rows()}
        stray = sorted(t for t in tables if rows.get(t) != child.pid)
        assert not stray, (f"a killed run left {stray} with no cairn_scratch row under its pid "
                           f"{child.pid} — nothing the sweep can take: {rows}")
    finally:
        for t in tables:
            forget_leaf(t)               # its nodes out of the shared tables before the leaf goes
    dropped: list[str] = []
    store.sweep_scratch(report=dropped)
    assert set(tables) <= set(dropped), f"the sweep dropped {dropped}, not {tables}"
    left = [t for t in tables if store.owner_of(t) is not None]
    assert not left, f"still standing after the sweep: {left}"


def _main() -> int:
    checks = [
        test_every_walk_tooth_runs_over_scratch_nexi,
        test_the_runs_nexi_are_registered_scratch_under_its_pid,
        test_a_killed_run_leaves_tables_the_sweep_takes,
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
        from cairn.devices.librarian.tools.trees.trees import forget_leaf
        for name in _HELD.values():   # this run's nodes out of the shared tables, then the nexi dropped
            forget_leaf(nexus_table(name, owner=moreabout_mod.OWNER))
        _SCRATCH.close()
    if failed:
        print(f"RED — {len(failed)} failure(s): {', '.join(failed)}")
        return 1
    print("green — chart/moreabout: the walk sees deposited state under a labeled "
          "floor, under-floor is honest never empty, berths attach only what exists, "
          "the signal lands dated and dedups readably, refusals leave the tree "
          "standing, and a re-run is impossible by import physics")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

"""Proof for ticket 2b3d842bc118 — codemother's learning lands in tables she owns.

Measured 2026-11-05: eight codemother calls into the tree tool pass no owner, so they fall back
to tree.OWNER = "chart" and her learning sits in chart_<nexus>_nodes (constrain 537, decompose
532, hypothesize 4220, orient 531, survey 538, triage 526, validate 547, verdict 6, codemother
16). Akien 2026-11-05: "yes, codemother's learning goes in its own tables." Measured
2026-11-06: watch.py's counsel passed query_text=, a TypeError its except swallowed, so
tree_hits was always 0.

1. clause_1_every_tree_call_names_codemother: an AST census of every non-proof module under
   cairn/devices/codemother finds no call to deposit_learning, counsel, propose, nexus_table or
   scratch_nexus whose owner is not 'codemother' (a literal or a module constant equal to it);
2. clause_2_surveys_deposit_lands_in_codemothers_leaf: deposit_survey's leaf row lands in
   codemother_<scratch>_nodes and none in chart_<scratch>_nodes (its gate is stubbed; the nexus
   is redirected to a scratch name; the owner is whatever survey passes);
3. clause_3_the_migration_moves_and_refuses_a_mismatch: over a scratch chart_<x>_nodes leaf of
   N rows, migrate() leaves codemother_<x>_nodes owned by codemother with the same node-id set
   and drops chart_<x>_nodes; a second run changes nothing; a leaf whose leaf_id already names a
   different node in the destination drops nothing and reports not ok;
4. clause_4_the_live_tables_are_hers: live, read-only — for each of the nine nexi
   codemother_<n>_nodes is owned by codemother with at least the 2026-11-05 census rows and
   chart_<n>_nodes does not exist (green only after the one live migration);
5. clause_5_watch_counsel_returns_hits: watch.activate over a codemother scratch nexus holding a
   deposited vector returns tree_hits >= 1 and does not escalate (embed, hex and log stubbed);
6. clause_6_the_codemother_proofs_stay_green: the codemother proofs this ticket touches, and
   test_watch.py, run green through bin/cairn test.

Subjects are bound at tooth time. Scratch nexi via tree.scratch_nexus; a red run that mints a
chart_<scratch>_nodes outside the scratch scope drops it.

Run bare:  PYTHONPATH=. python3 cairn/devices/codemother/proofs/test_codemother_learning_lands_in_its_own_tables.py
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "2b3d842bc118": {
        "1": "clause_1_every_tree_call_names_codemother",
        "2": "clause_2_surveys_deposit_lands_in_codemothers_leaf",
        "3": "clause_3_the_migration_moves_and_refuses_a_mismatch",
        "4": "clause_4_the_live_tables_are_hers",
        "5": "clause_5_watch_counsel_returns_hits",
        "6": "clause_6_the_codemother_proofs_stay_green",
    },
}

FAILURES: list[str] = []
DEVICE = REPO / "cairn" / "devices" / "codemother"
_HERE = "cairn/devices/codemother/proofs/test_codemother_learning_lands_in_its_own_tables.py"
_TREE_FUNCS = {"deposit_learning", "counsel", "propose", "nexus_table", "scratch_nexus"}
_CENSUS = {"constrain": 537, "decompose": 532, "hypothesize": 4220, "orient": 531,
           "survey": 538, "triage": 526, "validate": 547, "verdict": 6, "codemother": 16}
_VEC = [1.0, 0.0, 0.0]
_TOUCHED = [
    "cairn/devices/codemother/proofs/test_a_failed_deposit_is_written_to_the_ledger.py",
    "cairn/devices/codemother/proofs/test_deposit.py",
    "cairn/devices/codemother/proofs/test_the_chart_deposit_is_a_codemother_verb.py",
    "cairn/devices/codemother/proofs/test_watch.py",
] + [f"cairn/devices/codemother/machines/{m}/proofs/test_chart_{m}.py"
     for m in ("decompose", "constrain", "validate", "survey", "verdict", "triage", "hypothesize")]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:900]}")
    if not ok:
        FAILURES.append(name)


def _prov(berth: str) -> dict:
    return {"source": berth, "ground": "fixture"}


def _berth() -> str:
    from cairn.tools.scratch.scratch import scratch_dir
    p = scratch_dir("testing-2b3d842bc118-") / "berth.json"
    p.write_text("{}", encoding="utf-8")
    return str(p)


def _drop_if_chart(table: str) -> None:
    from cairn.devices.db_domain.tools.client import store
    if store.owner_of(table) == "chart":
        store.drop_table(table, "chart")


# ---- clause 1 -------------------------------------------------------------------------------

def _offences(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    consts = {t.id: n.value.value for n in tree.body if isinstance(n, ast.Assign)
              and isinstance(n.value, ast.Constant) for t in n.targets if isinstance(t, ast.Name)}
    names: dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "cairn.tools.tree.tree":
            for a in n.names:
                if a.name in _TREE_FUNCS:
                    names[a.asname or a.name] = a.name
    out = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in names):
            continue
        kw = {k.arg: k.value for k in n.keywords}
        v = kw.get("owner")
        val = (v.value if isinstance(v, ast.Constant)
               else consts.get(v.id) if isinstance(v, ast.Name) else None)
        if val != "codemother":
            out.append(f"{path.relative_to(REPO)}:{n.lineno} {names[n.func.id]} owner={val!r}")
    return out


def tooth_1() -> None:
    name = PROVES["2b3d842bc118"]["1"]
    try:
        mods = [p for p in DEVICE.rglob("*.py") if "proofs" not in p.parts]
        bad = [o for p in mods for o in _offences(p)]
        check(name, bool(mods) and not bad, f"{len(mods)} modules; offences={bad}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


# ---- clause 2 -------------------------------------------------------------------------------

def tooth_2(nexus: str) -> None:
    name = PROVES["2b3d842bc118"]["2"]
    from cairn.tools.tree.tree import nexus_table
    from cairn.devices.librarian.tools.trees import trees
    chart = nexus_table(nexus, owner="chart")
    try:
        from cairn.devices.codemother.machines.survey import survey
        from cairn.tools.tree import tree as tree_mod
        real = tree_mod.deposit_learning
        saved = (survey.validate_survey_at_deposit, survey.survey_node_content,
                 survey.deposit_learning)
        survey.validate_survey_at_deposit = lambda packet, root=None: None
        survey.survey_node_content = lambda packet: f"a survey codemother holds [{nexus}]"
        survey.deposit_learning = lambda _n, *a, **kw: real(nexus, *a, **kw)
        try:
            from cairn.devices.db_domain.tools.client import store
            own = nexus_table(nexus, owner="codemother")
            before = trees.tree_state(nexus, table=own, owner="codemother")["nodes"]
            survey.deposit_survey({"constrain_ref": "fixture", "confidence": 0.5}, _VEC,
                                  berth_path=_berth())
            after = trees.tree_state(nexus, table=own, owner="codemother")["nodes"]
            chart_owner = store.owner_of(chart)
        finally:
            (survey.validate_survey_at_deposit, survey.survey_node_content,
             survey.deposit_learning) = saved
        check(name, after == before + 1 and chart_owner is None,
              f"{own}: {before} -> {after}; {chart} owner={chart_owner!r}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")
    finally:
        _drop_if_chart(chart)


# ---- clause 3 -------------------------------------------------------------------------------

def _node_ids(table: str) -> set[str]:
    from cairn.devices.db_domain.tools.client import store
    return {r["node_id"] for r in store.read(table)}


def tooth_3() -> None:
    name = PROVES["2b3d842bc118"]["3"]
    from cairn.tools.tree.tree import scratch_nexus, nexus_table, deposit_learning
    from cairn.devices.db_domain.tools.client import store
    minted: list[str] = []
    try:
        from cairn.devices.codemother import migrate_learning_to_own_tables as mig
        berth = _berth()
        notes = []
        with scratch_nexus("testing_2b3d_move", owner="chart") as n:
            src, dst = nexus_table(n, owner="chart"), nexus_table(n, owner="codemother")
            minted.append(dst)
            for i in range(3):
                deposit_learning(n, f"a moved learning {i} [{n}]", [1.0, float(i + 1), 0.0],
                                 _prov(berth), owner="chart")
            want = _node_ids(src)
            first = mig.migrate([n])
            moved = (first["ok"] and store.owner_of(dst) == "codemother"
                     and _node_ids(dst) == want and len(want) == 3
                     and store.owner_of(src) is None)
            notes.append(f"first={first} dst_ids={len(_node_ids(dst))}/{len(want)}")
            snap = sorted(r["leaf_id"] for r in store.read(dst))
            second = mig.migrate([n])
            idem = second["ok"] and sorted(r["leaf_id"] for r in store.read(dst)) == snap
            notes.append(f"second={second}")
        with scratch_nexus("testing_2b3d_clash", owner="chart") as m:
            src, dst = nexus_table(m, owner="chart"), nexus_table(m, owner="codemother")
            minted.append(dst)
            deposit_learning(m, f"a clashing learning [{m}]", _VEC, _prov(berth), owner="chart")
            row = store.read(src)[0]
            other = deposit_learning(m, f"a different node [{m}]", [0.0, 1.0, 0.0],
                                     _prov(berth), owner="codemother")["node_id"]
            store.write(dst, "codemother", dict(row, node_id=other))
            third = mig.migrate([m])
            refused = (not third["ok"] and store.owner_of(src) == "chart"
                       and len(store.read(src)) == 1)
            notes.append(f"clash={third}")
        check(name, moved and idem and refused,
              f"moved={moved} idempotent={idem} refused={refused}; " + " | ".join(notes))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")
    finally:
        for t in minted:
            if store.owner_of(t) == "codemother":
                store.drop_table(t, "codemother")


# ---- clause 4 -------------------------------------------------------------------------------

def tooth_4() -> None:
    name = PROVES["2b3d842bc118"]["4"]
    try:
        from cairn.devices.db_domain.tools.client import store
        bad = []
        for n, floor in _CENSUS.items():
            own, chart = f"codemother_{n}_nodes", f"chart_{n}_nodes"
            owner = store.owner_of(own)
            rows = len(store.read(own)) if owner else 0
            if owner != "codemother" or rows < floor or store.owner_of(chart) is not None:
                bad.append(f"{n}: {own} owner={owner!r} rows={rows}/{floor} "
                           f"{chart} owner={store.owner_of(chart)!r}")
        check(name, not bad, f"bad={bad}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


# ---- clause 5 -------------------------------------------------------------------------------

def tooth_5(nexus: str) -> None:
    name = PROVES["2b3d842bc118"]["5"]
    try:
        from cairn.devices.codemother import watch
        from cairn.tools.tree.tree import deposit_learning
        deposit_learning(nexus, f"a learning the watcher finds [{nexus}]", _VEC,
                         _prov(_berth()), owner="codemother")
        missing = object()
        saved = {k: getattr(watch, k, missing)
                 for k in ("_embed", "_escalate_to_hex", "_log_activation", "WATCH_NEXUS")}
        watch._embed = lambda text: list(_VEC)
        watch._escalate_to_hex = lambda *a, **kw: {"nodes": []}
        watch._log_activation = lambda record: None
        watch.WATCH_NEXUS = nexus
        try:
            got = watch.activate("cairn/devices/codemother", "testing: 2b3d842bc118 clause 5")
        finally:
            for k, v in saved.items():
                if v is missing:
                    delattr(watch, k)
                else:
                    setattr(watch, k, v)
        check(name, got.get("tree_hits", 0) >= 1 and not got.get("escalated"),
              f"tree_hits={got.get('tree_hits')} escalated={got.get('escalated')} "
              f"findings={len(got.get('findings') or [])}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


# ---- clause 6 -------------------------------------------------------------------------------

def tooth_6() -> None:
    from cairn.tools.base.script_argv import bash_script_argv
    name = PROVES["2b3d842bc118"]["6"]
    try:
        r = subprocess.run([*bash_script_argv(REPO / "bin" / "cairn"), "test", "--timeout", "600", *_TOUCHED],
                           capture_output=True, text=True, timeout=1500, cwd=REPO)
        tail = r.stdout.strip().splitlines()
        summary = next((ln for ln in tail if " proofs · " in ln), "")
        ok = r.returncode == 0 and f"{len(_TOUCHED)} green · 0 red" in summary
        check(name, ok, f"rc={r.returncode} {summary!r} " + "\n".join(tail[-14:]))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.tree.tree import scratch_nexus
    tooth_1()
    with scratch_nexus("testing_2b3d_survey", owner="codemother") as n:
        tooth_2(n)
    tooth_3()
    tooth_4()
    with scratch_nexus("testing_2b3d_watch", owner="codemother") as n:
        tooth_5(n)
    tooth_6()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

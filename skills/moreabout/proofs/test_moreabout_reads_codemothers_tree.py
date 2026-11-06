"""Proof for ticket 99e658a96747 — /moreabout walks and signals in codemother's own trees.

Measured 2026-11-05: skills/moreabout/moreabout.py sets OWNER = "chart", so expand() and
signal() default to chart_<nexus>_nodes. The parent 2b3d842bc118 moves codemother's learning
to codemother_<nexus>_nodes (Akien 2026-11-05: "codemother's learning goes in its own
tables"); a reader left on 'chart' would walk an empty table once it moves. Children prove
before parents.

1. clause_1_the_default_owner_is_codemother: moreabout.OWNER is "codemother" and expand()
   and signal() default their owner to it;
2. clause_2_a_default_walk_reads_codemothers_leaf: a node deposited into a scratch nexus
   owned by codemother is seen by expand() called with no owner;
3. clause_3_a_default_signal_lands_in_codemothers_leaf: signal() called with no owner grows
   codemother_<scratch>_nodes by one, and no chart_<scratch>_nodes is minted.

The subject is bound at tooth time. Scratch nexi through tree.scratch_nexus (dropped at exit).

Run bare:  PYTHONPATH=. python3 skills/moreabout/proofs/test_moreabout_reads_codemothers_tree.py
"""
from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "99e658a96747": {
        "1": "clause_1_the_default_owner_is_codemother",
        "2": "clause_2_a_default_walk_reads_codemothers_leaf",
        "3": "clause_3_a_default_signal_lands_in_codemothers_leaf",
    },
}

FAILURES: list[str] = []
_PROV = {"source": "skills/moreabout/proofs/test_moreabout_reads_codemothers_tree.py", "ground": "fixture"}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:600]}")
    if not ok:
        FAILURES.append(name)


def tooth_1() -> None:
    name = PROVES["99e658a96747"]["1"]
    try:
        from skills.moreabout import moreabout as m
        d_expand = inspect.signature(m.expand).parameters["owner"].default
        d_signal = inspect.signature(m.signal).parameters["owner"].default
        check(name, m.OWNER == "codemother" and d_expand == d_signal == "codemother",
              f"OWNER={m.OWNER!r} expand={d_expand!r} signal={d_signal!r}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(nexus: str) -> None:
    name = PROVES["99e658a96747"]["2"]
    try:
        from skills.moreabout.moreabout import expand
        from cairn.tools.tree.tree import deposit_learning
        content = f"a learning codemother holds [{os.getpid()}]"
        deposit_learning(nexus, content, [1.0, 0.0, 0.0], _PROV, owner="codemother")
        got = expand([1.0, 0.0, 0.0], nexus=nexus)
        seen = [e.get("content") for e in got.get("expansions", [])]
        check(name, content in seen, f"expansions={seen}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(nexus: str) -> None:
    name = PROVES["99e658a96747"]["3"]
    try:
        from skills.moreabout.moreabout import signal
        from cairn.tools.tree.tree import nexus_table
        from cairn.devices.db_domain.tools.client import store
        from cairn.devices.librarian.tools.trees import trees
        own = nexus_table(nexus, owner="codemother")
        before = trees.tree_state(nexus, table=own, owner="codemother")["nodes"]
        signal(f"moreabout: where does codemother's learning live? [{os.getpid()}]",
               [0.0, 1.0, 0.0], date="2026-11-05", nexus=nexus)
        after = trees.tree_state(nexus, table=own, owner="codemother")["nodes"]
        chart = nexus_table(nexus, owner="chart")
        chart_owner = store.owner_of(chart)
        check(name, after == before + 1 and chart_owner is None,
              f"{own}: {before} -> {after}; {chart} owner={chart_owner!r}")
        if chart_owner == "chart":  # a red run minted it outside scratch; do not leak it
            store.drop_table(chart, "chart")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.tree.tree import scratch_nexus
    tooth_1()
    with scratch_nexus("testing_99e6_walk", owner="codemother") as walk_nexus:
        tooth_2(walk_nexus)
    with scratch_nexus("testing_99e6_signal", owner="codemother") as signal_nexus:
        tooth_3(signal_nexus)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Proof for ticket 67d446a1a33a — /chart's live counsel defaults to codemother's own trees.

Measured 2026-11-05: skills/chart/live.py `_counsel` passes no owner unless argv names one,
so tree.counsel falls back to tree.OWNER = "chart" and walks chart_<nexus>_nodes. The
parent 2b3d842bc118 moves codemother's learning to codemother_<nexus>_nodes (Akien
2026-11-05: "codemother's learning goes in its own tables"); a counsel left on 'chart'
walks an empty table once it moves. Children prove before parents.

1. clause_1_the_default_owner_is_codemother: live.OWNER is "codemother";
2. clause_2_a_default_counsel_walks_codemothers_leaf: a node deposited into a scratch nexus
   owned by codemother is in the walk `live counsel "<request>" <nexus>` prints, with no
   owner named;
3. clause_3_the_payload_names_the_owner_walked: the served payload carries "owner" — the
   default prints "codemother", and `live counsel "<request>" <nexus> chart` prints "chart"
   and walks a chart-owned scratch nexus (the grafted tenants' explicit owner still wins).

The bus legs (embed, drain) are stubbed on the module so the walk is the subject; the tree
read is real. The subject is bound at tooth time. Scratch nexi via tree.scratch_nexus.

Run bare:  PYTHONPATH=. python3 skills/chart/proofs/test_live_counsel_reads_codemothers_tree.py
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "67d446a1a33a": {
        "1": "clause_1_the_default_owner_is_codemother",
        "2": "clause_2_a_default_counsel_walks_codemothers_leaf",
        "3": "clause_3_the_payload_names_the_owner_walked",
    },
}

FAILURES: list[str] = []
_PROV = {"source": "skills/chart/proofs/test_live_counsel_reads_codemothers_tree.py",
         "ground": "fixture"}
_VEC = [1.0, 0.0, 0.0]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:600]}")
    if not ok:
        FAILURES.append(name)


def _walk(argv: list[str]) -> dict:
    """Run live._counsel with the bus legs stubbed; return the served payload."""
    from skills.chart import live
    saved = (live._embed, live._drain_before_serving)
    live._embed = lambda text: list(_VEC)
    live._drain_before_serving = lambda: []
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            live._counsel(argv)
    finally:
        live._embed, live._drain_before_serving = saved
    return json.loads(out.getvalue())


def _contents(payload: dict) -> list[str]:
    return [n["content"] for n in payload["walk"]]


def _no_leak(nexus: str) -> None:
    """A red run reads the default on 'chart' and mints chart_<scratch>_nodes outside the
    scratch scope; drop it so a hollow reading leaves nothing behind."""
    from cairn.tools.tree.tree import nexus_table
    from cairn.devices.db_domain.tools.client import store
    leaked = nexus_table(nexus, owner="chart")
    if store.owner_of(leaked) == "chart":
        store.drop_table(leaked, "chart")


def tooth_1() -> None:
    name = PROVES["67d446a1a33a"]["1"]
    try:
        from skills.chart import live
        got = getattr(live, "OWNER", None)
        check(name, got == "codemother", f"live.OWNER={got!r}")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(nexus: str) -> None:
    name = PROVES["67d446a1a33a"]["2"]
    try:
        from cairn.tools.tree.tree import deposit_learning
        content = f"a learning codemother holds for counsel [{os.getpid()}]"
        deposit_learning(nexus, content, _VEC, _PROV, owner="codemother")
        try:
            seen = _contents(_walk(["where does codemother's learning live?", nexus]))
        finally:
            _no_leak(nexus)
        check(name, content in seen, f"walk={seen}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(nexus: str, own_nexus: str) -> None:
    name = PROVES["67d446a1a33a"]["3"]
    try:
        from cairn.tools.tree.tree import deposit_learning
        content = f"a learning a named owner holds [{os.getpid()}]"
        deposit_learning(nexus, content, _VEC, _PROV, owner="chart")
        named = _walk(["a named owner's walk", nexus, "chart"])
        try:
            default = _walk(["a default walk", own_nexus])
        finally:
            _no_leak(own_nexus)
        ok = (content in _contents(named) and named.get("owner") == "chart"
              and default.get("owner") == "codemother")
        check(name, ok, f"named owner={named.get('owner')!r} walk={_contents(named)}; "
                        f"default owner={default.get('owner')!r}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.tree.tree import scratch_nexus
    tooth_1()
    with scratch_nexus("testing_67d4_default", owner="codemother") as own_nexus:
        tooth_2(own_nexus)
        with scratch_nexus("testing_67d4_named", owner="chart") as named_nexus:
            tooth_3(named_nexus, own_nexus)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

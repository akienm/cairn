"""Proof for ticket d51aa52bfca2: no trouble proof tests the retired `clears` read.

Measured 2026-11-13 (the orchestrator's Linux reseal): ticket 6935a4a71f93 deleted store.clears
on 2026-11-08 (f2b0d8105; tools/store/store.py:8-9 says so), but two proofs sealed green on
11-06 still called it. On reseal test_an_operators_measured_clear_closes.py redded its tooth
the_clears_verb_answers_one_small_row_per_clear ("module ... store has no attribute 'clears'"),
and test_a_recorded_clear_is_classed_from_its_cgroup.py redded all three of its teeth, because
every one reads through clears. Those teeth retire with the verb; the live ones stay.

  1. test_no_proof_calls_clears: no file under cairn/devices/trouble/proofs/ calls `.clears(`;
  2. test_the_live_clear_teeth_stand: test_an_operators_measured_clear_closes.py still keys
     1c1b18bac2eb clauses 1 and 2 (and nothing else), and run bare it exits 0.

    bin/cairn test cairn/devices/trouble/proofs/test_no_trouble_proof_tests_the_retired_clears.py
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
_PROOFS = _REPO / "cairn" / "devices" / "trouble" / "proofs"
_LIVE = _PROOFS / "test_an_operators_measured_clear_closes.py"

PROVES = {"d51aa52bfca2": {
    "1": "test_no_proof_calls_clears",
    "2": "test_the_live_clear_teeth_stand",
}}

_failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail}"))
    if not ok:
        _failures.append(name)


def _calls_clears(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "clears"
               for n in ast.walk(tree))


def test_no_proof_calls_clears() -> None:
    hits = sorted(p.name for p in _PROOFS.glob("*.py") if _calls_clears(p))
    check("test_no_proof_calls_clears", not hits, f"still calling the retired clears: {hits}")


def _proves(path: Path) -> dict:
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PROVES" for t in node.targets):
            return ast.literal_eval(node.value)
    return {}


def test_the_live_clear_teeth_stand() -> None:
    keys = sorted((_proves(_LIVE).get("1c1b18bac2eb") or {}))
    env = dict(os.environ, PYTHONPATH=str(_REPO))
    r = subprocess.run([sys.executable, str(_LIVE)], cwd=str(_REPO), env=env, capture_output=True,
                       text=True, timeout=120, stdin=subprocess.DEVNULL)
    check("test_the_live_clear_teeth_stand", keys == ["1", "2"] and r.returncode == 0,
          f"keys={keys} rc={r.returncode} out={r.stdout[-300:]!r}")


def main() -> int:
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                check(name, False, f"raised {type(exc).__name__}: {exc}")
    print("\nGREEN" if not _failures else f"\nRED — {len(_failures)} failure(s)")
    return 1 if _failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

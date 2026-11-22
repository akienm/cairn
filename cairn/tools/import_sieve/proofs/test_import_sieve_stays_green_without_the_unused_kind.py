#!/usr/bin/env python3
"""Proof: import_sieve carries only rule kinds something declares (ticket 27f5ad6f62dc).

Measured 2026-11-13 on akienyoga9i, and again 2026-11-22 on akiendelllinux: git grep finds
the retired rule kind only in sieve.py and its own three tests. No rule set, charter or
caller declares it, and RULE 1's physics is build_inspector's encapsulation_holds (ticket
124c0312c2d8). The orchestrator ruled: delete it.

Outline 1.3.7.1.1: a retirement checks its callers in the same act as the deletion, and
nothing checks afterwards, so this proof keeps no tooth that the kind stays gone. The kind
is a branch inside sieve.py, not a path, so `cairn codemother retire` cannot move it aside.
The build does by hand what retire does for a path: it runs the namers' proof before and
after the branch leaves. These teeth are that check, and they stand only as present-tense
claims about the kinds that remain.

  1. the one proof that names the kind, test_import_sieve.py (its three teeth for the kind
     deleted with the branch), runs green.
  2. the kinds still in use still catch: a sole_path rule over a planted dialer reds it, and
     the same rule over the same graph without the dialer is clean (paired, per the charter's
     gates, so a sieve gutted by the deletion cannot pass).

    python3 cairn/tools/import_sieve/proofs/test_import_sieve_stays_green_without_the_unused_kind.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.tools.import_sieve import sieve

PROVES = {"27f5ad6f62dc": {
    "1": "test_the_namers_proof_runs_green",
    "2": "test_sole_path_still_catches_a_planted_dialer",
}}

_HERE = Path(__file__).resolve().parent

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""), flush=True)
    if not ok:
        FAILURES.append(name)


def test_the_namers_proof_runs_green() -> None:
    proc = subprocess.run([sys.executable, str(_HERE / "test_import_sieve.py")], cwd=str(_REPO),
                          capture_output=True, text=True, timeout=600)
    tail = (proc.stdout or "").strip().splitlines()[-3:]
    check("test_the_namers_proof_runs_green", proc.returncode == 0,
          f"test_import_sieve.py exit {proc.returncode}; tail {tail}; stderr {(proc.stderr or '')[-300:]!r}")


def test_sole_path_still_catches_a_planted_dialer() -> None:
    rule = {"kind": "sole_path", "capability": "the inference host",
            "modules": ("socket", "urllib.request"), "only": "cairn/devices/inferenceproxy/"}
    door = {"cairn/devices/inferenceproxy/host.py": {"urllib.request"}}
    planted = dict(door, **{"skills/rogue/probe.py": {"socket"}})
    caught = sieve.catches(planted, rule, floor=1)
    clean = sieve.catches(door, rule, floor=1)
    ok = len(caught) == 1 and "skills/rogue/probe.py" in caught[0] and clean == []
    check("test_sole_path_still_catches_a_planted_dialer", ok,
          f"planted caught {caught}; without the dialer caught {clean}")


def main() -> int:
    for tooth in (test_the_namers_proof_runs_green, test_sole_path_still_catches_a_planted_dialer):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

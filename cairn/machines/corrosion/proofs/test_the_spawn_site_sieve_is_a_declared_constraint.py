"""Proof: the every_spawn_site_takes_the_helper sieve is a declared constraint in corrosion's set.

The sieve holds the whole-tree coverage windowless_spawn's own proofs gave before they moved to
fixtures (RULE 1, ticket bce45318b2e0). constraint_enforcement_holds only watches what the set
lists, so an unlisted sieve could be dropped without the corrosion check seeing it.

Reads corrosion's own constraint_set.json and checks that the entry's path resolves in this repo,
which is the same existence test the predicate applies. Spawns nothing, needs no bus.

    python3 cairn/machines/corrosion/proofs/test_the_spawn_site_sieve_is_a_declared_constraint.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SET = Path(__file__).resolve().parents[1] / "constraint_set.json"
SIEVE_PATH = "cairn/machines/build_inspector/sieves/every_spawn_site_takes_the_helper.json"


def test_the_set_lists_the_spawn_site_sieve():
    entries = json.loads(SET.read_text(encoding="utf-8"))["constraints"]
    hits = [e for e in entries if e.get("path") == SIEVE_PATH]
    assert len(hits) == 1, f"the set lists the spawn-site sieve {len(hits)} times, not once: {hits}"
    e = hits[0]
    assert e.get("kind") == "check" and e.get("id") == "every-spawn-site-takes-the-helper", e
    assert (ROOT / SIEVE_PATH).is_file(), f"the declared path does not resolve: {SIEVE_PATH}"


def _main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — a proof reports every red (Law 7)
            failed += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

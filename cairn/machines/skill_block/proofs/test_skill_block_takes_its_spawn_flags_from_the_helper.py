"""Proof (ticket 02a7583655a0): every spawn site in cairn/machines/skill_block takes its flags from windowless_spawn.

Measured 2026-11-20 on akiendell: counters.py called
subprocess with neither detached_kwargs nor windowless_kwargs, so each opened a console window on
Windows while Akien worked. It now asks windowless_spawn.windowless_kwargs.

RULE 1: this scans only cairn/machines/skill_block/, through the scanner windowless_spawn publishes. Reads
files, spawns nothing, runs on any host.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CC = "cairn/machines/skill_block"

PROVES = {"02a7583655a0": {
    "1": "test_no_skill_block_site_spawns_without_the_helper",
    "2": "test_counters_still_imports_and_names_the_helper_keywords",
}}

def test_no_skill_block_site_spawns_without_the_helper():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    assert (ROOT / CC / "counters.py").is_file(), "the scan would be hollow"
    bad = unhelped_sites(ROOT, CC)
    assert not bad, "a skill_block site spawns without the helper's keywords:\n" + "\n".join(bad)


def test_counters_still_imports_and_names_the_helper_keywords():
    import importlib
    src = (ROOT / CC / "counters.py").read_text(encoding="utf-8")
    assert "windowless_kwargs" in src, "counters.py never takes the keywords"
    importlib.import_module("cairn.machines.skill_block.counters")


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

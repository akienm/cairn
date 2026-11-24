"""Proof (ticket 1759bdafbb60): every spawn site in cairn/devices/cairn takes its flags from windowless_spawn.

Measured 2026-11-20 on akiendell: the_constraint_door_is_the_only_alter.py called
subprocess with neither detached_kwargs nor windowless_kwargs, so each opened a console window on
Windows while Akien worked. It now asks windowless_spawn.windowless_kwargs.

RULE 1: this scans only cairn/devices/db_domain/, through the scanner windowless_spawn publishes. Reads
files, spawns nothing, runs on any host.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CC = "cairn/devices/db_domain"

PROVES = {"1759bdafbb60": {
    "1": "test_no_db_domain_site_spawns_without_the_helper",
    "2": "test_the_alter_probe_still_imports_and_names_the_helper_keywords",
}}

def test_no_db_domain_site_spawns_without_the_helper():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    assert (ROOT / CC / "probes/the_constraint_door_is_the_only_alter.py").is_file(), "the scan would be hollow"
    bad = unhelped_sites(ROOT, CC)
    assert not bad, "a db_domain site spawns without the helper's keywords:\n" + "\n".join(bad)


def test_the_alter_probe_still_imports_and_names_the_helper_keywords():
    src = (ROOT / CC / "probes/the_constraint_door_is_the_only_alter.py").read_text(encoding="utf-8")
    assert "windowless_kwargs" in src, "the_constraint_door_is_the_only_alter.py never takes the keywords"
    import importlib
    importlib.import_module("cairn.devices.db_domain.probes.the_constraint_door_is_the_only_alter")


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

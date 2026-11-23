"""Proof (ticket 00954ec7e8e5): every spawn site in cairn/devices/cc takes its flags from windowless_spawn.

Measured 2026-11-20 on akiendell: scripts/commons_paths.py, house_paths.py and memory_link.py called
subprocess with neither detached_kwargs nor windowless_kwargs, so each opened a console window on
Windows while Akien worked. They now ask windowless_spawn.windowless_kwargs.

RULE 1: this scans only cairn/devices/cc/, through the scanner windowless_spawn publishes. Reads
files, spawns nothing, runs on any host.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CC = "cairn/devices/cc"

PROVES = {"00954ec7e8e5": {
    "1": "test_no_cc_site_spawns_without_the_helper",
    "2": "test_cc_scripts_still_import_and_name_the_helper_keywords",
}}

SCRIPTS = ("commons_paths.py", "house_paths.py", "memory_link.py")


def test_no_cc_site_spawns_without_the_helper():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    assert (ROOT / CC / "scripts" / "memory_link.py").is_file(), "the scan would be hollow"
    bad = unhelped_sites(ROOT, CC)
    assert not bad, "a cc site spawns without the helper's keywords:\n" + "\n".join(bad)


def test_cc_scripts_still_import_and_name_the_helper_keywords():
    import importlib.util
    for name in SCRIPTS:
        path = ROOT / CC / "scripts" / name
        assert "windowless_kwargs" in path.read_text(encoding="utf-8"), f"{name} never takes the keywords"
        spec = importlib.util.spec_from_file_location("ccscript_" + path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)          # the import must not raise (the guarded helper import)


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

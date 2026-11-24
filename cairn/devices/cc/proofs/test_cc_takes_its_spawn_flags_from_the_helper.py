"""Proof (ticket 00954ec7e8e5): every spawn site in cairn/devices/cc takes its flags from windowless_spawn.

Measured 2026-11-23 on akiendell: scripts/commons_paths.py, house_paths.py and memory_link.py called
subprocess with neither detached_kwargs nor windowless_kwargs, so each opened a console window on
Windows while Akien worked. They now ask windowless_spawn.windowless_kwargs.

These scripts run as `python3 <path>` from close.sh and prove.sh with cwd = a repo that is not the
class-space checkout and no PYTHONPATH, so the import must resolve from the script's own location
(clause 2 runs them that way and reads the answer).

RULE 1: scans only cairn/devices/cc/, through the scanner windowless_spawn publishes.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CC = "cairn/devices/cc"
SCRIPTS = ["commons_paths.py", "house_paths.py", "memory_link.py"]

PROVES = {"00954ec7e8e5": {
    "1": "test_no_cc_site_spawns_without_the_helper",
    "2": "test_the_cc_scripts_still_run_alone_from_another_cwd_and_name_the_helper_keywords",
}}


def test_no_cc_site_spawns_without_the_helper():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    assert (ROOT / CC / "scripts" / "commons_paths.py").is_file(), "the scan would be hollow"
    bad = unhelped_sites(ROOT, CC)
    assert not bad, "a cc site spawns without the helper's keywords:\n" + "\n".join(bad)


def test_the_cc_scripts_still_run_alone_from_another_cwd_and_name_the_helper_keywords():
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONUTF8"] = "1"
    with tempfile.TemporaryDirectory() as tmp:
        for name in SCRIPTS:
            path = ROOT / CC / "scripts" / name
            assert "windowless_kwargs" in path.read_text(encoding="utf-8"), f"{name} never takes the keywords"
            args = ["--help"] if name == "memory_link.py" else []
            r = subprocess.run([sys.executable, str(path), *args], cwd=tmp, env=env,
                               capture_output=True, text=True, timeout=60)
            said = r.stdout + r.stderr
            assert "ModuleNotFoundError" not in said and "ImportError" not in said, (
                f"{name} cannot import the helper when run alone from another cwd:\n{said[-600:]}")
            assert "usage" in said.lower(), f"{name} did not answer as it did before:\n{said[-600:]}"


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

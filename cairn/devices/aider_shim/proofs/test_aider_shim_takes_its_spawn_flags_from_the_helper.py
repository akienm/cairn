"""Proof (ticket 6a6e009daeac): every spawn site in cairn/devices/aider_shim takes its flags from windowless_spawn.

Measured 2026-11-20 on akiendell: aider_shim.py called
subprocess with neither detached_kwargs nor windowless_kwargs, so each opened a console window on
Windows while Akien worked. It now asks windowless_spawn.windowless_kwargs.

RULE 1: this scans only cairn/devices/aider_shim/, through the scanner windowless_spawn publishes. Reads
files, spawns nothing, runs on any host.

    PYTHONUTF8=1 PYTHONPATH=. python bin/cairn.py test --seal <this file>
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CC = "cairn/devices/aider_shim"

PROVES = {"6a6e009daeac": {
    "1": "test_no_aider_shim_site_spawns_without_the_helper",
    "2": "test_aider_shim_still_imports_and_names_the_helper_keywords",
}}

def test_no_aider_shim_site_spawns_without_the_helper():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    assert (ROOT / CC / "driver.py").is_file(), "the scan would be hollow"
    bad = unhelped_sites(ROOT, CC)
    assert not bad, "an aider_shim site spawns without the helper's keywords:\n" + "\n".join(bad)


def test_aider_shim_still_imports_and_names_the_helper_keywords():
    for name in ("driver.py", "probes/edit_survival_probe.py", "venv.py"):
        src = (ROOT / CC / name).read_text(encoding="utf-8")
        assert "windowless_kwargs" in src, f"{name} never takes the keywords"
    import importlib
    importlib.import_module("cairn.devices.aider_shim.driver")
    importlib.import_module("cairn.devices.aider_shim.venv")
    _a_failing_setup_step_still_fails_loud_with_its_stderr()  # Law 7: capturing must not swallow a failed install


def _a_failing_setup_step_still_fails_loud_with_its_stderr():
    """Drives venv.build(), the public setup entry, with a pip that exits 3 writing known stderr (a fake `pip`
    package first on the child's PYTHONPATH). Reds on any build that swallows the child's output or its exit."""
    import contextlib, io, os, subprocess, tempfile
    from cairn.devices.aider_shim import venv
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "fakepip" / "pip"
        fake.mkdir(parents=True)
        (fake / "__init__.py").write_bytes(b"")
        (fake / "__main__.py").write_bytes(b"import sys\nsys.stderr.write('PIP-STDERR-MARK\\n')\nsys.exit(3)\n")
        saved = (venv.python, venv.packages, os.environ.get("PYTHONPATH"))
        venv.python = lambda: Path(sys.executable)      # exists, so no venv is created: only the pip step runs
        venv.packages = lambda: ["a-package"]
        os.environ["PYTHONPATH"] = str(fake.parent)
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                try:
                    venv.build()
                except subprocess.CalledProcessError as exc:
                    assert exc.returncode == 3, exc.returncode
                else:
                    raise AssertionError("a failing pip did not raise")
        finally:
            venv.python, venv.packages = saved[0], saved[1]
            if saved[2] is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = saved[2]
    assert "PIP-STDERR-MARK" in err.getvalue(), "the failed pip's stderr never reached the parent's stderr"


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

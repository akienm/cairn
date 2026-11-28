"""Proof (ticket 880aff74422d): every spawn site in cairn/devices/tester takes its flags from windowless_spawn.

Measured 2026-11-20 on akiendell: seven tester files (cli.py, hollow.py, isolation.py,
probes/a_commit_that_reseals_leaves_a_clean_tree.py, red_tickets.py, reseal.py, working_bytes.py)
called subprocess with neither detached_kwargs nor windowless_kwargs, so each child could open a
console window on Windows while Akien worked at the box. Each call now takes windowless_kwargs:
the bare form where the call captures stdout and stderr itself, and ``given=`` naming the streams
it sets where it inherits one, so an inherited stream is handed through instead of landing in a
new hidden console (ticket aab7f9ca2068).

RULE 1: this scans only cairn/devices/tester/, through the scanner windowless_spawn publishes.

    PYTHONPATH=. bin/cairn test --seal cairn/devices/tester/proofs/test_tester_takes_its_spawn_flags_from_the_helper.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CC = "cairn/devices/tester"
FILES = ("cli.py", "hollow.py", "isolation.py", "probes/a_commit_that_reseals_leaves_a_clean_tree.py",
         "red_tickets.py", "reseal.py", "working_bytes.py")
SPAWNS = {"run", "Popen", "call", "check_call", "check_output"}

PROVES = {"880aff74422d": {
    "1": "test_no_tester_site_spawns_without_the_helper",
    "2": "test_every_tester_spawn_call_carries_the_helper_keywords_and_imports",
}}


def _spawn_calls(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"
                and node.func.attr in SPAWNS):
            yield node


def test_no_tester_site_spawns_without_the_helper():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    for f in FILES:
        assert (ROOT / CC / f).is_file(), f"{f} is gone, so the scan would be hollow"
    bad = unhelped_sites(ROOT, CC)
    assert not bad, "a tester site spawns without the helper's keywords:\n" + "\n".join(bad)


def test_every_tester_spawn_call_carries_the_helper_keywords_and_imports():
    """Clause 2's floor: the scan is per file, so this reads per CALL. Every subprocess spawn in
    the seven files unpacks windowless_kwargs(...), and each module still imports."""
    import importlib
    missing, calls = [], 0
    for f in FILES:
        for node in _spawn_calls(ROOT / CC / f):
            calls += 1
            ok = any(k.arg is None and isinstance(k.value, ast.Call)
                     and getattr(k.value.func, "id", None) == "windowless_kwargs"
                     for k in node.keywords)
            if not ok:
                missing.append(f"{f}:{node.lineno}")
    assert calls >= 40, f"only {calls} spawn calls found; the read would be hollow"
    assert not missing, "a spawn call takes no windowless_kwargs:\n" + "\n".join(missing)
    for f in FILES:
        importlib.import_module((CC + "/" + f[:-3]).replace("/", "."))


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

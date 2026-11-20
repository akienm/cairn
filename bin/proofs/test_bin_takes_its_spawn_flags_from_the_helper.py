"""Proof (ticket 0d7dcc7b667a): every subprocess spawn in bin/cairn.py takes its keywords from
cairn.tools.windowless_spawn, so none opens a visible console window on Windows.

Measured 2026-11-20 by akiendell_cc_0: bin/cairn.py spawns at three sites, all
``subprocess.call`` (``_run``, and ``_bus`` twice: the CAIRN_BUS_MOUTH script and the bus_client
module), and none passes the helper's keywords. ``unhelped_sites`` alone reads that GREEN: it
names a file only for ``Popen(`` or a hand-built flag needle, and a bare ``subprocess.call`` is
neither (widening it is the parent 364704f371dd's work, outside this ticket's bounds). So tooth 1
asks the published scanner AND walks cairn.py's own syntax tree for every subprocess spawn call;
the walk is what makes the tooth red before the build (D1: every subprocess call in cairn.py takes
the helper's keywords).

  1. ``unhelped_sites`` over bin names no file, and every ``subprocess.call/run/Popen/check_call/
     check_output`` in bin/cairn.py passes ``**windowless_kwargs()`` or ``**detached_kwargs()``,
     or carries the marker comment ``# visible-console:`` on its line (a call that must show a
     terminal);
  2. behaviour is unchanged: each of the three spawn sites, driven with ``subprocess.call``
     replaced by a recorder, is called with the same argv, cwd and env as before the edit, and any
     keyword beyond those is exactly what the helper hands this host.

RULE 1: reads bin's own files and calls the scanner and keyword functions windowless_spawn
publishes. Spawns nothing; runs on any host.

    python3 bin/proofs/test_bin_takes_its_spawn_flags_from_the_helper.py
"""
from __future__ import annotations

import ast
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CAIRN_PY = ROOT / "bin" / "cairn.py"
SPAWNERS = {"call", "run", "Popen", "check_call", "check_output"}
HELPERS = {"windowless_kwargs", "detached_kwargs"}
MARKER = "# visible-console:"

PROVES = {"0d7dcc7b667a": {
    "1": "test_every_bin_spawn_takes_the_helpers_keywords",
    "2": "test_each_spawn_site_passes_the_argv_cwd_and_env_it_passed_before",
}}


def _spawn_calls(tree: ast.AST) -> list[ast.Call]:
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in SPAWNERS and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"):
            out.append(node)
    return out


def _takes_helper(call: ast.Call) -> bool:
    for kw in call.keywords:
        if kw.arg is None and isinstance(kw.value, ast.Call):
            f = kw.value.func
            name = f.id if isinstance(f, ast.Name) else getattr(f, "attr", "")
            if name in HELPERS:
                return True
    return False


def test_every_bin_spawn_takes_the_helpers_keywords():
    from cairn.tools.windowless_spawn.windowless_spawn import unhelped_sites
    assert CAIRN_PY.is_file(), "bin/cairn.py is gone: the walk would be hollow"
    bad = list(unhelped_sites(ROOT, "bin"))
    text = CAIRN_PY.read_text(encoding="utf-8")
    lines = text.splitlines()
    calls = _spawn_calls(ast.parse(text))
    assert calls, "no subprocess spawn found in bin/cairn.py: the walk would be hollow"
    for c in calls:
        span = lines[c.lineno - 1:(c.end_lineno or c.lineno)]
        if not _takes_helper(c) and not any(MARKER in ln for ln in span):
            bad.append(f"bin/cairn.py:{c.lineno}: subprocess.{c.func.attr} takes no keywords from the helper")
    assert not bad, "a bin spawn builds its own flags or none:\n" + "\n".join(bad)


def _load_cairn_py():
    spec = importlib.util.spec_from_file_location("_cairn_py_under_proof", CAIRN_PY)
    mod = importlib.util.module_from_spec(spec)
    saved = list(sys.path)
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = saved
    return mod


def test_each_spawn_site_passes_the_argv_cwd_and_env_it_passed_before():
    from cairn.tools.windowless_spawn.windowless_spawn import detached_kwargs, windowless_kwargs
    allowed = [{}, windowless_kwargs(), detached_kwargs()]
    m = _load_cairn_py()
    seen: list[tuple[list, dict]] = []

    def recorder(argv, **kw):
        seen.append((list(argv), kw))
        return 0

    with tempfile.TemporaryDirectory(prefix="cairn-bin-spawn-proof-") as d:
        script = Path(d) / "mouth.py"
        script.write_text("#!/usr/bin/env python3\n")
        real_call, saved_mouth = m.subprocess.call, os.environ.pop("CAIRN_BUS_MOUTH", None)
        m.subprocess.call = recorder
        try:
            m._run(script, ["a", "b"])
            os.environ["CAIRN_BUS_MOUTH"] = str(script)
            m._bus("somebus", ["x"])
            os.environ.pop("CAIRN_BUS_MOUTH", None)
            m._bus("somebus", ["y"])
        finally:
            m.subprocess.call = real_call
            if saved_mouth is not None:
                os.environ["CAIRN_BUS_MOUTH"] = saved_mouth
    assert len(seen) == 3, f"expected 3 spawns, saw {len(seen)}: {seen!r}"
    (a1, k1), (a2, k2), (a3, k3) = seen
    assert a1 == [sys.executable, str(script), "a", "b"], a1
    assert a2 == [sys.executable, str(script), "somebus", "x"], a2
    assert a3 == [sys.executable, "-m", "cairn.tools.bus_client", "somebus", "y"], a3
    assert k3.get("cwd") == str(m.REPO), k3
    assert str(m.REPO) in k3.get("env", {}).get("PYTHONPATH", "").split(os.pathsep), k3
    for kw in (k1, k2, {k: v for k, v in k3.items() if k not in ("cwd", "env")}):
        assert kw in allowed, f"a spawn took keywords the helper does not hand this host: {kw!r}"


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

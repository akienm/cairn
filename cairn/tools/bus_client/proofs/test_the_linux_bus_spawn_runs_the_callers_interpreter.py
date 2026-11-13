"""The Linux bus spawn runs the caller's own interpreter (ticket 5370ad4f474d).

remote.py's two Linux spawns, ``_spawn`` (systemd-run) and ``_setsid`` (its fall-through),
started the bus as a bare ``python3``. Which python that is depends on the caller's PATH.
Measured 2026-11-13 (Linux census, pass 2): under ``PATH=/usr/bin:/bin`` it was the system
python, which has no psycopg2, so the bus died at ``import psycopg2`` and 29 proofs read
"no bus". The Windows spawn (``_detached``) already ran ``background_python()``, the caller's
``sys.executable``.

  1. ``_spawn``'s systemd-run argv runs ``sys.executable``, not ``python3``, under a PATH
     holding no python3.
  2. ``_setsid``'s Popen argv runs ``sys.executable`` under the same PATH.
  3. The tooth reds when either path's argv[0] is put back to ``python3``: a mutant of
     remote.py's own source, with that one change, fails clauses 1 and 2.

``subprocess.run`` and ``subprocess.Popen`` are stubbed, so no bus and no unit is started.
The bus home and the log are under a scratch dir.

    python3 cairn/tools/bus_client/proofs/test_the_linux_bus_spawn_runs_the_callers_interpreter.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.bus_client import remote  # noqa: E402

PROVES = {"5370ad4f474d": {
    "1": "test_the_unit_spawn_runs_the_callers_interpreter",
    "2": "test_the_setsid_spawn_runs_the_callers_interpreter",
    "3": "test_a_bare_python3_reds_both_spawns",
}}

_REMOTE_SRC = Path(remote.__file__).read_text(encoding="utf-8")


class _Done:
    returncode = 0
    stdout = ""
    stderr = ""


def _captured(mod, fn_name: str) -> list[list[str]]:
    """Run mod.<fn_name> with subprocess stubbed and PATH holding no python3; return every argv."""
    seen: list[list[str]] = []

    def fake_run(argv, *a, **k):
        seen.append(list(argv))
        return _Done()

    class FakePopen:
        def __init__(self, argv, *a, **k):
            seen.append(list(argv))

    work = scratch_dir("busspawn")
    empty_bin = work / "bin"
    empty_bin.mkdir(parents=True, exist_ok=True)
    saved = (mod.subprocess.run, mod.subprocess.Popen, os.environ.get("PATH"), mod._LOG)
    mod.subprocess.run, mod.subprocess.Popen = fake_run, FakePopen
    os.environ["PATH"] = str(empty_bin)
    mod._LOG = work / "bus.log"
    try:
        home = work / "bushome"
        if fn_name == "_spawn":
            mod._spawn(home, True)
        else:
            mod._setsid(home, True, mod._LOG, "proof")
    finally:
        mod.subprocess.run, mod.subprocess.Popen = saved[0], saved[1]
        if saved[2] is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = saved[2]
        mod._LOG = saved[3]
    return seen


def _bus_argv0(seen: list[list[str]]) -> str:
    """argv[0] of the bus command: after systemd-run's '--', or the Popen argv itself."""
    for argv in seen:
        if remote._BUS_MODULE in argv:
            cmd = argv[argv.index("--") + 1:] if "--" in argv else argv
            return cmd[0]
    raise AssertionError(f"no bus command among the spawned argvs: {seen}")


def _check(mod, fn_name: str) -> None:
    got = _bus_argv0(_captured(mod, fn_name))
    assert got == sys.executable, (
        f"{fn_name} runs the bus as {got!r}, not the caller's interpreter {sys.executable!r}")


def _mutant() -> types.ModuleType:
    """remote.py's own source with the bus command's argv[0] put back to a bare python3."""
    src = _REMOTE_SRC.replace('[background_python(), "-m", _BUS_MODULE', '["python3", "-m", _BUS_MODULE')
    assert src != _REMOTE_SRC, "the mutant changed nothing: remote.py no longer spells the spawn this proof reads"
    mod = types.ModuleType("remote_mutant")
    mod.__file__ = remote.__file__
    sys.modules["remote_mutant"] = mod
    exec(compile(src, remote.__file__, "exec"), mod.__dict__)
    return mod


def test_the_unit_spawn_runs_the_callers_interpreter():
    if os.name == "nt":
        return
    _check(remote, "_spawn")


def test_the_setsid_spawn_runs_the_callers_interpreter():
    if os.name == "nt":
        return
    _check(remote, "_setsid")


def test_a_bare_python3_reds_both_spawns():
    if os.name == "nt":
        return
    mod = _mutant()
    for fn_name in ("_spawn", "_setsid"):
        try:
            _check(mod, fn_name)
        except AssertionError:
            continue
        raise AssertionError(f"the mutant's {fn_name} still passed: the tooth cannot see a bare python3")


def main() -> int:
    fails = 0
    teeth = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in teeth:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not fails else 'RED'} — {len(teeth) - fails}/{len(teeth)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

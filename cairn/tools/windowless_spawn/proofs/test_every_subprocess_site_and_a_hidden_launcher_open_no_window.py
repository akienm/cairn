"""Proof for ticket 364704f371dd — the scan sees every subprocess spawn, and a hidden launcher exists.

Measured 2026-11-20 on akiendell: unhelped_sites('.') returned 0 because it looked only for
``Popen(``, while 46 of 57 non-proof files calling subprocess.run/call/check_output carried
neither detached_kwargs nor windowless_kwargs. A bare subprocess.run from a windowless parent
can open a console, and the scan could not see it.

  1. unhelped_sites names a scratch file that calls subprocess.run, call, check_call or
     check_output without helper keywords, and does not name one that takes detached_kwargs
     or windowless_kwargs.
  2. ``python -m cairn.tools.windowless_spawn.hidden <log> <argv...>`` runs the argv list and
     exits with the child's exit code, the child's stdout and stderr in the named log.
  3. on Windows, a console child started through the launcher and a grandchild it starts both
     report GetConsoleWindow() == 0. Off nt this tooth prints UNMEASURED: a state, never a green.

RULE 1: every tooth measures only windowless_spawn; scans run over scratch trees. Every tooth
binds what the build adds at call time, never at import.

    python cairn/tools/windowless_spawn/proofs/test_every_subprocess_site_and_a_hidden_launcher_open_no_window.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "364704f371dd": {
        "1": "the_scan_names_every_unhelped_subprocess_call_form",
        "2": "the_hidden_launcher_runs_an_argv_and_returns_its_exit_code",
        "3": "a_launched_child_and_its_grandchild_have_no_console_window",
    },
}

_LAUNCHER = "cairn.tools.windowless_spawn.hidden"


class Unmeasured(Exception):
    """The tooth cannot run here; that is a state, never a green."""


def _ws():
    from cairn.tools.windowless_spawn import windowless_spawn as ws
    return ws


def _nowin() -> dict:
    return {"creationflags": 0x08000000} if os.name == "nt" else {}


def the_scan_names_every_unhelped_subprocess_call_form():
    ws = _ws()
    forms = ("run", "call", "check_call", "check_output")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "cairn" / "x").mkdir(parents=True)
        for f in forms:
            (root / f"cairn/x/bare_{f}.py").write_text(
                f"import subprocess\nsubprocess.{f}(['a'])\n", encoding="utf-8")
        (root / "cairn/x/helped_run.py").write_text(
            "from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs\n"
            "import subprocess\nsubprocess.run(['a'], **windowless_kwargs())\n", encoding="utf-8")
        (root / "cairn/x/helped_detached.py").write_text(
            "from cairn.tools.windowless_spawn.windowless_spawn import detached_kwargs\n"
            "import subprocess\nsubprocess.check_output(['a'], **detached_kwargs())\n", encoding="utf-8")
        bad = " ".join(ws.unhelped_sites(root))
        missed = [f for f in forms if f"bare_{f}.py" not in bad]
        assert not missed, f"subprocess.{missed} without the helper was not named: {bad!r}"
        assert "helped_run.py" not in bad and "helped_detached.py" not in bad, f"a helped site was named: {bad!r}"


def the_hidden_launcher_runs_an_argv_and_returns_its_exit_code():
    child = ("import sys; print('out-line-364704'); "
             "print('err-line-364704', file=sys.stderr); sys.exit(7)")
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "hidden.log"
        got = subprocess.run([sys.executable, "-m", _LAUNCHER, str(log), sys.executable, "-c", child],
                             cwd=str(REPO), capture_output=True, text=True, timeout=120, **_nowin())
        assert got.returncode == 7, (
            f"the launcher exited {got.returncode}, not the child's 7; stderr {got.stderr[-400:]!r}")
        assert log.exists(), f"no log at {log}"
        text = log.read_text(encoding="utf-8", errors="replace")
        assert "out-line-364704" in text and "err-line-364704" in text, f"the log lacks the child's output: {text!r}"


def a_launched_child_and_its_grandchild_have_no_console_window():
    if os.name != "nt":
        raise Unmeasured("not a Windows box: GetConsoleWindow can only be read on NT")
    ws = _ws()
    probe = "import ctypes; print(ctypes.windll.kernel32.GetConsoleWindow())"
    child = ("import ctypes, subprocess, sys; "
             "print('child', ctypes.windll.kernel32.GetConsoleWindow(), flush=True); "
             f"print('grandchild', subprocess.run([sys.executable, '-c', {probe!r}], "
             "capture_output=True, text=True).stdout.strip(), flush=True)")
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "hidden.log"
        got = subprocess.run([ws.background_pythonw(), "-m", _LAUNCHER, str(log), sys.executable, "-c", child],
                             cwd=str(REPO), capture_output=True, text=True, timeout=120, **_nowin())
        text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
        assert got.returncode == 0, f"the launcher exited {got.returncode}; log {text!r}"
        lines = dict(l.split(" ", 1) for l in text.splitlines() if l.startswith(("child ", "grandchild ")))
        assert lines.get("child") == "0", f"the child reports a console window: {text!r}"
        assert lines.get("grandchild") == "0", f"the grandchild reports a console window: {text!r}"


TEETH = [the_scan_names_every_unhelped_subprocess_call_form,
         the_hidden_launcher_runs_an_argv_and_returns_its_exit_code,
         a_launched_child_and_its_grandchild_have_no_console_window]


def main() -> int:
    failed = unmeasured = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}", flush=True)
        except Unmeasured as e:
            unmeasured += 1
            print(f"  UNMEASURED  {t.__name__}: {e}", flush=True)
        except Exception as e:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {e}", flush=True)
    print(f"\n{len(TEETH) - failed - unmeasured}/{len(TEETH)} teeth green, {unmeasured} unmeasured")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

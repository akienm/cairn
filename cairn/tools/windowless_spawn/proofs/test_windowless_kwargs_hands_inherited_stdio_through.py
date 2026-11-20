"""Proof for ticket aab7f9ca2068 — windowless_kwargs hands the caller's inherited stdin, stdout and stderr
to an attached child, so a windowless child's output still reaches its caller.

Measured 2026-11-20 on akiendell: from a parent with no console and an inherited stdout pipe, a child
started with ``**windowless_kwargs()`` printed nothing (CREATE_NO_WINDOW without STARTF_USESTDHANDLES hands
it a new hidden console), while a bare child printed and an explicit ``stdout=sys.stdout`` fixed it.

Red first: written before ``given`` existed, so every tooth reads red on the old helper
(``windowless_kwargs() got an unexpected keyword argument 'given'``, or no ``given`` parameter).
Tooth 1 runs its parent with DETACHED_PROCESS on Windows, so the parent owns no console and its stdout
is the pipe this proof reads: the shape of a hook or the harness. Tooth 2 spawns a ``pythonw`` parent and
is UNMEASURED off Windows, a state and never a green. A true console parent is not run: it needs a
visible window, and is named unmeasured in the ticket.

    python <this file>
"""

from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "aab7f9ca2068": {
        "1": "a_windowless_child_of_a_no_console_pipe_parent_delivers_its_output",
        "2": "a_pythonw_parent_opens_no_window_and_adds_no_stream_it_lacks",
        "3": "a_caller_that_passes_its_own_stdout_still_captures_with_no_duplicate",
        "4": "a_caller_that_names_its_own_stdin_is_not_overwritten",
        "5": "the_default_return_is_unchanged_so_the_testers_or_merge_still_reads_integers",
    },
}

_NT = os.name == "nt"
_PARENT = """
import subprocess, sys
sys.path.insert(0, {repo!r})
from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs
child = [sys.executable, "-c", "print('child-says-hi')"]
sys.exit(subprocess.call(child, **windowless_kwargs(given=())))
"""
_PYTHONW_PARENT = """
import json, subprocess, sys
sys.path.insert(0, {repo!r})
from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs
kw = windowless_kwargs(given=())
child = [sys.executable.replace("pythonw.exe", "python.exe"), "-c",
         "import ctypes, sys; sys.exit(0 if ctypes.windll.kernel32.GetConsoleWindow() == 0 else 3)"]
rc = subprocess.call(child, **kw)
open({out!r}, "w").write(json.dumps({{"rc": rc, "keys": sorted(kw), "stdout_is_none": sys.stdout is None}}))
"""


class Unmeasured(Exception):
    """The tooth cannot run here; that is a state, never a green."""


def _child(text: str) -> list[str]:
    return [sys.executable, "-c", f"print({text!r})"]


def a_windowless_child_of_a_no_console_pipe_parent_delivers_its_output():
    """The parent owns no console on Windows (DETACHED_PROCESS) and its stdout is the pipe read here, as
    under a hook. Its windowless child prints; the print must arrive."""
    flags = 0x00000008 if _NT else 0      # DETACHED_PROCESS
    r = subprocess.run([sys.executable, "-c", _PARENT.format(repo=str(REPO))], capture_output=True,
                       text=True, timeout=60, creationflags=flags)
    assert r.returncode == 0, f"parent failed rc={r.returncode}: {r.stderr[-400:]}"
    assert "child-says-hi" in r.stdout, f"the child's print did not reach the caller: stdout={r.stdout!r} stderr={r.stderr[-300:]!r}"


def a_pythonw_parent_opens_no_window_and_adds_no_stream_it_lacks():
    if not _NT:
        raise Unmeasured("pythonw and consoles are Windows concepts; not run on this host")
    pyw = Path(sys.executable).with_name("pythonw.exe")
    if not pyw.exists():
        raise Unmeasured(f"no pythonw.exe beside {sys.executable}")
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "out.json"
        script = Path(d) / "parent.py"
        script.write_text(_PYTHONW_PARENT.format(repo=str(REPO), out=str(out)), encoding="utf-8")
        subprocess.run([str(pyw), str(script)], timeout=60)
        assert out.exists(), "the pythonw parent wrote no result: it failed before the call"
        got = json.loads(out.read_text(encoding="utf-8"))
    assert got["rc"] == 0, f"the child reported a console window or failed: rc={got['rc']}"
    assert got["stdout_is_none"], "pythonw was expected to have no stdout"
    streams = {"stdin", "stdout", "stderr"} & set(got["keys"])
    assert "stdout" not in streams and "stderr" not in streams, f"a stream the parent lacks was added: {sorted(streams)}"


def a_caller_that_passes_its_own_stdout_still_captures_with_no_duplicate():
    from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs
    kw = windowless_kwargs(given=("stdout",))
    assert "stdout" not in kw, "the helper added stdout though the caller named it: a duplicate keyword"
    r = subprocess.run(_child("captured-ok"), stdout=subprocess.PIPE, text=True, timeout=60, **kw)
    assert r.returncode == 0 and "captured-ok" in r.stdout, f"the caller's own stdout=PIPE did not capture: {r.stdout!r}"


def a_caller_that_names_its_own_stdin_is_not_overwritten():
    from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs
    kw = windowless_kwargs(given=("stdin", "stdout"))
    assert "stdin" not in kw and "stdout" not in kw, "the helper added a stream though the caller named it"
    r = subprocess.run([sys.executable, "-c", "import sys; print(sys.stdin.read())"], input="mine",
                       stdout=subprocess.PIPE, text=True, timeout=60, **kw)
    assert r.stdout.strip() == "mine", f"the caller's own stdin did not reach the child: {r.stdout!r}"


def the_default_return_is_unchanged_so_the_testers_or_merge_still_reads_integers():
    from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs
    p = inspect.signature(windowless_kwargs).parameters
    assert "given" in p and p["given"].kind is inspect.Parameter.KEYWORD_ONLY and p["given"].default is None, \
        "windowless_kwargs has no keyword-only given=None"
    nt = windowless_kwargs("nt")
    assert set(nt) == {"creationflags"} and all(isinstance(v, int) for v in nt.values()), \
        f"the default return on nt carries more than integer flags: {nt!r}"
    assert windowless_kwargs("posix") == {}, "the default return off Windows is not empty"


TEETH = [a_windowless_child_of_a_no_console_pipe_parent_delivers_its_output,
         a_pythonw_parent_opens_no_window_and_adds_no_stream_it_lacks,
         a_caller_that_passes_its_own_stdout_still_captures_with_no_duplicate,
         a_caller_that_names_its_own_stdin_is_not_overwritten,
         the_default_return_is_unchanged_so_the_testers_or_merge_still_reads_integers]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Unmeasured as e:
            print(f"  UNMEASURED  {t.__name__}: {e}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth not red")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

"""Proof (the second way the bus dies): a background child is spawned on the venv's interpreter when the caller is not in a venv.

A plain ``python <proof>`` from the system python has no psycopg2, ``background_python()`` returned that caller's own ``sys.executable``,
and the scratch bus it spawned died at ``import psycopg2`` (measured 2026-11-14 on akiendell, ~/.cairn/logs/bus.log:
``ModuleNotFoundError: No module named 'psycopg2'``). The interpreter is now resolved the way the launcher resolves it (``cairn_python``,
recovery/bootstrap.sh) when the caller is outside a venv, and is the caller's own everywhere else, so a Linux run that already is the
venv's spawns exactly what it did before.

  (1) launched from a NON-venv interpreter (the base python, in a real child process), ``background_python()`` answers the venv's;
  (2) a venv caller, a box with no venv, and an explicit ``executable`` all keep their answer;
  (3) both venv layouts are found (``bin/python3`` and ``Scripts/python.exe``), ``$CAIRN_VENV`` is honoured, and ``bin`` wins.

    python <this file>
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.windowless_spawn import windowless_spawn as ws  # noqa: E402

PROVES = {
    "337dcf060614": {
        "1": "launched_from_a_non_venv_interpreter_the_spawn_interpreter_is_the_venvs",
        "2": "a_venv_caller_no_venv_and_an_explicit_executable_keep_their_answer",
        "3": "both_venv_layouts_are_found_cairn_venv_is_honoured_and_bin_wins",
    },
}


def _base_python() -> str | None:
    """A real interpreter that is NOT in a venv: the one the running python was built from."""
    cand = getattr(sys, "_base_executable", None) or sys.executable
    return cand if cand and os.path.isfile(cand) else None


def _fake_venv(root: Path, layout: str) -> str:
    rel = {"posix": "bin/python3", "nt": "Scripts/python.exe"}[layout]
    f = root / Path(*rel.split("/"))
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(b"")
    return str(f)


def launched_from_a_non_venv_interpreter_the_spawn_interpreter_is_the_venvs() -> None:
    base = _base_python()
    assert base, "no base interpreter to launch from: the tooth would measure nothing"
    tmp = Path(str(scratch_dir("spawn_interpreter_")))
    try:
        want = _fake_venv(tmp / "venv", "posix" if os.name != "nt" else "nt")
        # the REAL, unadorned call, from a real process that is outside any venv (the base interpreter run directly)
        code = ("import sys; assert sys.prefix == sys.base_prefix, 'not a non-venv caller'; "
                "from cairn.tools.windowless_spawn.windowless_spawn import background_python; print(background_python())")
        env = dict(os.environ, CAIRN_VENV=str(tmp / "venv"), PYTHONPATH=str(REPO))
        got = subprocess.run([base, "-c", code], env=env, capture_output=True, text=True, cwd=str(REPO))
        assert got.returncode == 0, f"the child failed: {got.stderr.strip()[-300:]}"
        assert got.stdout.strip() == want, f"a plain run from the base python spawned {got.stdout.strip()!r}, not the venv's {want!r}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def a_venv_caller_no_venv_and_an_explicit_executable_keep_their_answer() -> None:
    assert ws.background_python(in_venv=True, venv="/v/bin/python3") == sys.executable, "a venv caller must keep its own interpreter"
    tmp = Path(str(scratch_dir("spawn_interpreter_none_")))
    saved = os.environ.get("CAIRN_VENV")
    os.environ["CAIRN_VENV"] = str(tmp / "absent")
    try:
        got = ws.background_python(in_venv=False)
        assert got == sys.executable, f"with no venv standing the caller's own must answer: {got!r}"
    finally:
        if saved is None:
            os.environ.pop("CAIRN_VENV", None)
        else:
            os.environ["CAIRN_VENV"] = saved
        shutil.rmtree(tmp, ignore_errors=True)
    assert ws.background_python("posix", executable="/usr/bin/python3") == "/usr/bin/python3", "an explicit executable always wins"
    assert ws.background_python("nt", executable="C:/v/Scripts/python.exe", in_venv=False, venv="/other") == "C:/v/Scripts/python.exe"


def both_venv_layouts_are_found_cairn_venv_is_honoured_and_bin_wins() -> None:
    tmp = Path(str(scratch_dir("spawn_interpreter_layouts_")))
    try:
        posix = _fake_venv(tmp / "a", "posix")
        nt = _fake_venv(tmp / "b", "nt")
        assert ws.venv_python({"CAIRN_VENV": str(tmp / "a")}) == posix, "bin/python3 was not found"
        assert ws.venv_python({"CAIRN_VENV": str(tmp / "b")}) == nt, "Scripts/python.exe was not found"
        both = tmp / "c"
        p, _ = _fake_venv(both, "posix"), _fake_venv(both, "nt")
        assert ws.venv_python({"CAIRN_VENV": str(both)}) == p, "bin/python3 must win over Scripts/python.exe, as the launcher orders them"
        home = tmp / "home"
        under_home = _fake_venv(home / ".cairn" / "venv", "posix")
        assert ws.venv_python({}, home=str(home)) == under_home, "with no $CAIRN_VENV the venv is ~/.cairn/venv"
        assert ws.venv_python({"CAIRN_VENV": str(tmp / "nowhere")}) is None, "a venv that does not stand must answer None, not a guess"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TEETH = [launched_from_a_non_venv_interpreter_the_spawn_interpreter_is_the_venvs,
         a_venv_caller_no_venv_and_an_explicit_executable_keep_their_answer,
         both_venv_layouts_are_found_cairn_venv_is_honoured_and_bin_wins]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

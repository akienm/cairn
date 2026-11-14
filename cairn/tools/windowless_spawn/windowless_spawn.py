"""windowless_spawn — the Popen keywords for a detached background child, one place.

Six call sites each hand-built their own (``start_new_session=True`` alone, which does
nothing on Windows), and the one that did pass the Windows flags still showed a window.
``detached_kwargs`` is the single answer; ``background_python`` names the interpreter.

    subprocess.Popen([background_python(), "-m", mod], **detached_kwargs(), stdout=fh, ...)
"""

from __future__ import annotations

import os
import subprocess
import sys

# Values stand beside the names so a proof on Linux can read what a Windows spawn passes.
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)


def detached_kwargs(os_name: str | None = None) -> dict:
    """Popen keywords that start a child with no console, outliving its parent.

    ``os_name`` is ``os.name`` unless a proof injects one."""
    if (os_name or os.name) == "nt":
        return {"creationflags": DETACHED_PROCESS | CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP,
                "close_fds": True}
    return {"start_new_session": True}


def venv_python(environ=None, home: str | None = None, exists=os.path.isfile) -> str | None:
    """Cairn's own venv interpreter, found the way the launcher finds it (``cairn_python`` in recovery/bootstrap.sh): under
    ``$CAIRN_VENV`` or ``~/.cairn/venv``, ``bin/python3`` first, then Windows' ``Scripts/python.exe``. None when neither stands."""
    env = os.environ if environ is None else environ
    root = env.get("CAIRN_VENV") or os.path.join(home or os.path.expanduser("~"), ".cairn", "venv")
    for rel in ("bin/python3", "Scripts/python.exe"):
        cand = os.path.join(root, *rel.split("/"))
        if exists(cand):
            return cand
    return None


def _in_a_venv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def background_python(os_name: str | None = None, executable: str | None = None, *,
                      in_venv: bool | None = None, venv: str | None = None) -> str:
    """The interpreter to spawn a background child with: the caller's own when that is a venv's, so the child
    sees the same site-packages; Cairn's venv interpreter when the caller is NOT in a venv.

    A plain ``python <proof>`` from the system python has no psycopg2, and the scratch bus it spawned died at
    ``import psycopg2`` (measured 2026-11-14, ``~/.cairn/logs/bus.log``: ``No module named 'psycopg2'``). Outside a venv the
    interpreter is now resolved the way the launcher resolves it (``venv_python``); inside one, and when no venv stands, it is
    the caller's own ``sys.executable``, so every run that already is the venv's (every Linux run) spawns exactly what it did
    before. ``in_venv`` and ``venv`` are injection for proofs.

    This once returned the base interpreter named by ``pyvenv.cfg`` on the guess that a
    venv launcher's child owns a console. The guess was never measured, and running the
    base ``python.exe`` directly does not enter the venv: the bus child died at
    ``import psycopg2`` (measured 2026-11-12, ``~/.cairn/logs/bus.log``). A console in the
    spawned tree is tooth 2's question and stays unmeasured until it runs."""
    if executable:
        return executable
    if in_venv if in_venv is not None else _in_a_venv():
        return sys.executable
    return (venv if venv is not None else venv_python()) or sys.executable


def background_pythonw(os_name: str | None = None, executable: str | None = None, exists=os.path.exists) -> str:
    """The interpreter for a LONG-LIVED background child: on Windows the caller's own venv
    ``pythonw.exe`` when it stands beside it, else ``background_python()``.

    Measured 2026-11-13 on akiendell: a child spawned through the venv ``python.exe`` launcher
    with DETACHED_PROCESS | CREATE_NO_WINDOW still owns a ``conhost.exe`` (launcher python.exe ->
    real python.exe -> conhost); through ``pythonw.exe`` the tree holds two pythonw.exe and no
    console host, and the child reports the venv's own prefix. pythonw has no stdout or stderr,
    so a caller redirects both (every site does). A caller that reads the child's output keeps
    ``background_python()``."""
    py = background_python(os_name, executable)
    if (os_name or os.name) != "nt":
        return py
    w = os.path.join(os.path.dirname(py), "pythonw.exe")
    return w if exists(w) else py

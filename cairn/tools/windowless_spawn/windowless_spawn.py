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


def windowless_kwargs(os_name: str | None = None) -> dict:
    """Popen keywords for an ATTACHED child the caller waits on: no console window, and
    nothing else — no detach, no new group, no new session.

    The tester's run_owned starts each proof in a Windows job and waits on it; it passed
    CREATE_NO_WINDOW alone, measured green on akiendell under ticket 715d2205a2ec, and this
    is that flag from the one place (ticket 0156856b1fae). ``os_name`` is ``os.name`` unless
    a proof injects one."""
    if (os_name or os.name) == "nt":
        return {"creationflags": CREATE_NO_WINDOW}
    return {}


def background_python(os_name: str | None = None, executable: str | None = None) -> str:
    """The interpreter to spawn a background child with: the caller's own, so the child
    sees the same site-packages.

    This once returned the base interpreter named by ``pyvenv.cfg`` on the guess that a
    venv launcher's child owns a console. The guess was never measured, and running the
    base ``python.exe`` directly does not enter the venv: the bus child died at
    ``import psycopg2`` (measured 2026-11-12, ``~/.cairn/logs/bus.log``). A console in the
    spawned tree is tooth 2's question and stays unmeasured until it runs."""
    return executable or sys.executable


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

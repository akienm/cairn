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


def background_python(os_name: str | None = None, executable: str | None = None) -> str:
    """The interpreter to spawn a background child with: the caller's own, so the child
    sees the same site-packages.

    This once returned the base interpreter named by ``pyvenv.cfg`` on the guess that a
    venv launcher's child owns a console. The guess was never measured, and running the
    base ``python.exe`` directly does not enter the venv: the bus child died at
    ``import psycopg2`` (measured 2026-11-12, ``~/.cairn/logs/bus.log``).

    A console in the spawned tree is tooth 2's question, and it was measured red on
    2026-11-13 (ticket 96cf285e299b): the venv ``python.exe`` launcher re-spawns the base
    interpreter without the detached flags and the base interpreter allocates a
    ``conhost.exe``. The ``pythonw.exe`` beside the venv python does not. So on Windows,
    where one sits beside the executable, that is the interpreter returned. Two things a
    caller must know: the pythonw launcher exits at once while the real child runs on, so a
    child is not tracked by ``Popen.pid`` or ``poll()``; and ``sys.stdout`` is ``None`` in a
    pythonw child, so it logs through a file handler, not ``print``."""
    exe = executable or sys.executable
    if (os_name or os.name) == "nt":
        pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.isfile(pyw):
            return pyw
    return exe

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
from pathlib import Path

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
    """The interpreter to spawn a background child with.

    On Windows a venv's ``Scripts\\python.exe`` is a launcher that starts the real
    interpreter as a child; that child can own a console the launcher's flags never
    reached. So inside a venv this returns the base interpreter named by ``pyvenv.cfg``
    ``home`` when it exists, else ``executable``. Elsewhere it is ``executable``."""
    exe = executable or sys.executable
    if (os_name or os.name) != "nt":
        return exe
    cfg = Path(exe).resolve().parent.parent / "pyvenv.cfg"
    try:
        lines = cfg.read_text(encoding="utf-8").splitlines()
    except OSError:
        return exe
    for line in lines:
        key, _, value = line.partition("=")
        if key.strip() == "home":
            base = Path(value.strip()) / "python.exe"
            return str(base) if base.exists() else exe
    return exe

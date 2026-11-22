"""windowless_spawn — the Popen keywords for a detached background child, one place.

Six call sites each hand-built their own (``start_new_session=True`` alone, which does
nothing on Windows), and the one that did pass the Windows flags still showed a window.
``detached_kwargs`` is the single answer for a detached child, ``windowless_kwargs`` for an
attached one the caller waits on; ``background_python`` names the interpreter.

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


def windowless_kwargs(os_name: str | None = None, *, given=None) -> dict:
    """Popen keywords for an ATTACHED child that the caller waits on: no console window, and
    nothing else (ticket bce45318b2e0).

    ``detached_kwargs`` is wrong for such a child. DETACHED_PROCESS leaves it with no console
    at all, so each console grandchild it starts opens a window of its own, and
    CREATE_NEW_PROCESS_GROUP takes it out of the caller's Ctrl+C. The tester's ``run_owned``
    holds its child in a job object and reads its output, so it takes these. Off Windows there
    is nothing to add.

    ``given`` is how a caller says it wants its std streams handed through (ticket aab7f9ca2068).
    Measured 2026-11-20 on akiendell: ``CREATE_NO_WINDOW`` without explicit std handles gives the
    child a new hidden console, so a child of a parent with no console and an inherited stdout pipe
    printed nothing. With ``given`` omitted (None) this returns only the flags, as the tester's
    OR-merge needs. With ``given`` passed, a tuple of the std keys the caller sets itself
    (``()`` for none), it adds ``stdin``/``stdout``/``stderr`` = the matching ``sys`` stream for each
    key not in ``given`` whose stream has a usable fileno; a stream that is None (pythonw) or has no
    fileno is skipped. A caller that passes ``stdout=PIPE`` names it in ``given``, so no keyword
    is duplicated."""
    kw: dict = {"creationflags": CREATE_NO_WINDOW} if (os_name or os.name) == "nt" else {}
    if given is None:
        return kw
    for key, stream in (("stdin", sys.stdin), ("stdout", sys.stdout), ("stderr", sys.stderr)):
        if key in given or stream is None:
            continue
        try:
            stream.fileno()
        except (AttributeError, OSError, ValueError):
            continue
        kw[key] = stream
    return kw


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


HAND_NEEDLES = ("start_new_session=True", "creationflags=", '"creationflags"', "'creationflags'",
                '"start_new_session"', "'start_new_session'", "DETACHED_PROCESS", "CREATE_NO_WINDOW")


# Every call form that starts a child: a bare subprocess.run from a windowless parent can open a
# console as surely as a Popen (ticket 364704f371dd, measured 2026-11-20: 46 of 57 such files unhelped).
SPAWN_NEEDLES = ("Popen(", "subprocess.run(", "subprocess.call(", "subprocess.check_call(",
                 "subprocess.check_output(")


def unhelped_sites(root, under: str = "cairn") -> list[str]:
    """Name every spawn site under ``root/under`` that does not take its keywords from this helper.

    A site is a non-proof ``.py`` file that spawns (any of ``SPAWN_NEEDLES``: ``Popen(`` and the
    ``subprocess.run/call/check_call/check_output`` call forms) or builds a flag set (any of
    ``HAND_NEEDLES``). It is named if it takes neither ``detached_kwargs`` nor ``windowless_kwargs``,
    and once for each flag it builds by hand. Paths are posix and relative to ``root``. The function
    scans the tree; it reads no list of known sites. Callers pass the subtree they own (a component's
    proof: its own directory) or the whole tree (the build_inspector sieve)."""
    root = Path(root)
    bad = []
    base = root / under
    for p in sorted(base.rglob("*.py")):
        rel = p.relative_to(root).as_posix()
        if "/proofs/" in rel or p.name == "windowless_spawn.py" or "/__pycache__/" in rel:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        spawns = any(n in text for n in SPAWN_NEEDLES)
        hand = [n for n in HAND_NEEDLES if n in text]
        if not (spawns or hand):
            continue
        if "detached_kwargs" not in text and "windowless_kwargs" not in text:
            bad.append(f"{rel}: spawns or builds a flag set without taking keywords from the helper")
        for n in hand:
            bad.append(f"{rel}: hand-builds {n}")
    return bad

"""Every python process a tester run starts says what it loaded (ticket 734b22d09f2e).

The tester puts this directory first on the subject's ``PYTHONPATH`` and names a host temp
file in ``CAIRN_TESTER_REACH_LOG``. ``site`` imports ``sitecustomize`` in every interpreter
that starts with that path — the subject, and every ``python`` it runs, ``-m`` or a script,
because a child inherits the environment. At exit each one appends one JSON line,
``{"pid": ..., "files": [...]}``, every module ``__file__`` it held. The tester reads the
lines at seal: the files its proof's component owns join ``fingerprint_closure``, and the
components the rest belong to become ``evidence.reached``.

WHY A SITECUSTOMIZE AND NOT THE CLOSURE RUNNER. The runner wraps the subject alone; a
subprocess the subject starts is a fresh interpreter the runner never sees, and that was the
blind spot this ticket names (a meta-proof's seal did not cover the proof it ran). The only
thing every interpreter on the path runs uninvited is ``sitecustomize``.

IT IMPORTS NOTHING FROM ``cairn``. It runs in every process before that process's own first
line; importing the package here would put the package in every closure it measures — the
instrument changing the reading.

IT SHADOWS ONE, SO IT RUNS THAT ONE. Being first on the path hides any ``sitecustomize``
further down (this host carries one in the stdlib dir, the apport hook). Losing it would make
a sealed run differ from a bare one, so the next one on ``sys.path`` past this directory is
executed here, as ``site`` would have.

IT ALSO SAYS WHAT IT SPAWNED (ticket 56b61c10bdbe, orchestrator ruling C). An audit hook keeps
the argv[0] of every process it started (``subprocess.Popen``, ``os.system``, ``os.spawn*``,
``os.posix_spawn``, ``os.exec*``), and the line carries them as ``"spawned"``. On Windows a
prevent-kind seal runs the subject at Low integrity, where MSYS bash cannot start (it exits
0xC0000142). A subject that spawns bash there has not measured what it claims, and the tester
reads this list to say so: INDETERMINATE naming bash, never a red against the proof.

A process that ends in ``os._exit`` (a forked worker) skips ``atexit`` and logs nothing; the
seal reads only what was logged, and an absence is not invented into a reach.
"""

import atexit
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.realpath(__file__))
_LOG = os.environ.get("CAIRN_TESTER_REACH_LOG")
_SPAWNED = []


def _first_word(cmd):
    # Windows hands Popen's audit a command LINE (list2cmdline), so a quoted path is one word.
    cmd = cmd.strip()
    if cmd.startswith('"'):
        end = cmd.find('"', 1)
        return cmd[1:end] if end > 0 else cmd[1:]
    return cmd.split()[0] if cmd else None


def _argv0(event, args):
    try:
        if event == "subprocess.Popen":
            exe, argv = args[0], args[1]
            if exe:
                return str(exe)
            if isinstance(argv, (str, bytes)):
                return _first_word(os.fsdecode(argv))
            return os.fsdecode(list(argv)[0])
        if event == "os.system":
            return _first_word(os.fsdecode(args[0]))
        if event == "os.spawn":
            return os.fsdecode(args[1])
        if event in ("os.posix_spawn", "os.exec"):
            return os.fsdecode(args[0])
    except Exception:  # noqa: BLE001 - an argv this cannot read is not a spawn it may invent
        return None
    return None


def _hear_spawn(event, args):
    if event in ("subprocess.Popen", "os.system", "os.spawn", "os.posix_spawn", "os.exec"):
        argv0 = _argv0(event, args)
        if argv0:
            _SPAWNED.append(argv0)


def _log_what_was_loaded():
    files = sorted({f for f in (getattr(m, "__file__", None) for m in list(sys.modules.values()))
                    if isinstance(f, str)})
    line = (json.dumps({"pid": os.getpid(), "files": files, "spawned": _SPAWNED}) + "\n").encode("utf-8")
    try:
        fd = os.open(_LOG, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    except OSError:
        return
    try:
        os.write(fd, line)  # one write on an O_APPEND fd: concurrent processes do not interleave
    finally:
        os.close(fd)


if _LOG:
    atexit.register(_log_what_was_loaded)
    sys.addaudithook(_hear_spawn)


def _run_the_shadowed_one():
    for entry in sys.path:
        d = os.path.realpath(entry or os.getcwd())
        if d == _HERE:
            continue
        candidate = os.path.join(d, "sitecustomize.py")
        if os.path.isfile(candidate):
            spec = importlib.util.spec_from_file_location("sitecustomize", candidate)
            spec.loader.exec_module(importlib.util.module_from_spec(spec))
            return


_run_the_shadowed_one()

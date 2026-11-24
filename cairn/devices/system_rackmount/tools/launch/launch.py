"""launch — the tool the system device publishes for the OS questions a launcher asks.

Ticket 60f16ffccd43 (child 1 of c3cd232ba0cf). The bash superclaude answered these itself, in
bash (uname, hostname -I, sudo, systemd-run units and scopes, ss); a Python launcher asks HERE,
so no launch-path module tests the OS (RULE 1; Akien 2026-11-21, "hostname should come from the
system device"). ``host`` answers "which box"; this tool is its side-effecting sibling.

Every action returns ``{"ok", "how", "detail"}``. ``how`` says which way it was answered:
systemd, setsid, detached, held, scope, plain, passwordless, password-held, none, elevated,
not-elevated, not-on-this-box. A box that cannot do a thing gets a stated answer, never silence.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from cairn.devices.system_rackmount.tools.host.host import os_id
from cairn.tools.windowless_spawn.windowless_spawn import detached_kwargs, windowless_kwargs

_HELD_WORDS = ("already loaded", "fragment file", "already exists", "already active")


def _result(ok: bool, how: str, detail: str, **extra) -> dict:
    return {"ok": ok, "how": how, "detail": detail, **extra}


def _windows() -> bool:
    return os_id() == "windows"


def venv_bin_dir(venv) -> Path:
    """Where a venv keeps its executables: ``Scripts`` on Windows, ``bin`` elsewhere."""
    return Path(venv) / ("Scripts" if _windows() else "bin")


def box_addresses() -> list:
    """This box's own addresses, as ``hostname -I`` lists them; empty where it cannot be asked."""
    if _windows() or not shutil.which("hostname"):
        return []
    got = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=10,
                         **windowless_kwargs())
    return got.stdout.split() if got.returncode == 0 else []


def port_listening(port: int) -> bool:
    """Is a TCP socket listening on ``port``, any address? (``ss -tlnH`` on Linux; netstat on Windows.)

    Read from the kernel's own tables, never by dialing: this tool may not import a module that
    can dial (build_inspector's sole_path rule).
    """
    port = int(port)
    if _windows():
        got = subprocess.run(["netstat", "-an", "-p", "TCP"], capture_output=True, text=True,
                             timeout=30, **windowless_kwargs())
        for line in got.stdout.splitlines():
            f = line.split()
            if len(f) >= 4 and f[-1].upper() == "LISTENING" and f[1].rsplit(":", 1)[-1] == str(port):
                return True
        return False
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            rows = Path(table).read_text().splitlines()[1:]
        except OSError:
            continue
        for row in rows:
            f = row.split()
            if len(f) > 3 and f[3] == "0A" and int(f[1].rsplit(":", 1)[1], 16) == port:
                return True
    return False


def runs_shell_scripts() -> bool:
    """Does this box run shell scripts? Windows runs Python, never bash (Akien)."""
    return not _windows()


def stream_is_console(stream) -> bool:
    """Is this stream a terminal (a console on Windows)?"""
    try:
        return os.isatty(stream.fileno())
    except (AttributeError, OSError, ValueError):
        return False


def _systemd_user() -> bool:
    return not _windows() and shutil.which("systemd-run") is not None


def _unit_active(unit: str) -> bool:
    got = subprocess.run(["systemctl", "--user", "is-active", f"{unit}.service"],
                         capture_output=True, text=True, timeout=30, **windowless_kwargs())
    return got.stdout.strip() in ("active", "activating", "reloading")


def service_spawn(unit: str, argv, log, cwd=None, env=None) -> dict:
    """Start ``argv`` as a long-lived service named ``unit``, outliving the caller.

    Linux with systemd --user: a transient user unit parented on the user manager, HOME and PATH
    carried in, stdout/stderr appended to ``log``; a held name reads ``held`` and starts nothing,
    and a failed leftover of the name is reset and tried once more. Without systemd-run: a new
    session (setsid). Windows: a detached process with no console window.
    """
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    cwd = str(cwd or os.getcwd())
    argv = [str(a) for a in argv]
    if _systemd_user():
        if _unit_active(unit):
            return _result(True, "held", f"{unit}.service is already running; nothing started")
        envs = dict(env or {})
        envs.setdefault("HOME", os.environ.get("HOME", ""))
        envs.setdefault("PATH", os.environ.get("PATH", ""))
        cmd = (["systemd-run", "--user", "--quiet", "--unit", unit, "--working-directory", cwd]
               + [f"--setenv={k}={v}" for k, v in envs.items()]
               + ["-p", f"StandardOutput=append:{log}", "-p", f"StandardError=append:{log}"]
               # A unit a test run asked for is collected when it fails, so the run leaves no corpse
               # (ticket 7bb0d4894a62, as the shell superclaude did). It must ride the start:
               # systemctl set-property refuses CollectMode afterwards (measured 2026-11-23).
               + (["-p", "CollectMode=inactive-or-failed"] if envs.get("CAIRN_TESTER_TEST_ID") else [])
               + ["--"] + argv)
        got = subprocess.run(cmd, capture_output=True, text=True, timeout=60, **windowless_kwargs())
        if got.returncode == 0:
            return _result(True, "systemd", f"started as {unit}.service")
        err = (got.stderr or got.stdout).strip()
        if any(w in err for w in _HELD_WORDS):
            if _unit_active(unit):
                return _result(True, "held", f"{unit}.service is already running: {err}")
            subprocess.run(["systemctl", "--user", "reset-failed", f"{unit}.service"],
                           capture_output=True, timeout=30, **windowless_kwargs())
            got = subprocess.run(cmd, capture_output=True, text=True, timeout=60, **windowless_kwargs())
            if got.returncode == 0:
                return _result(True, "systemd", f"started as {unit}.service after reset-failed")
            err = (got.stderr or got.stdout).strip()
        return _result(False, "systemd", f"{unit}.service refused: {err}")
    full = dict(os.environ, **(env or {}))
    with open(log, "ab") as fh:
        if _windows():
            subprocess.Popen(argv, cwd=cwd, env=full, stdin=subprocess.DEVNULL, stdout=fh,
                             stderr=subprocess.STDOUT, **detached_kwargs())
            return _result(True, "detached", f"{unit} spawned detached with no console window")
        subprocess.Popen(argv, cwd=cwd, env=full, stdin=subprocess.DEVNULL, stdout=fh,
                         stderr=subprocess.STDOUT, start_new_session=True, **windowless_kwargs())
    return _result(True, "setsid", f"{unit}: systemd-run unavailable, spawned in a new session; "
                                   "it stays in this cgroup and dies with it")


def scoped_argv(argv, mem_high: str, mem_max: str, swap_max: str, unit: str | None = None) -> dict:
    """The command line that runs ``argv`` under a memory-capped scope, and which way it was made.

    The start attempt is the probe: a scope is offered only where ``systemd-run --user --scope``
    can start one now. Elsewhere the argv comes back as given, ``how`` saying so.
    """
    argv = [str(a) for a in argv]
    if _windows():
        return _result(True, "not-on-this-box", "no memory scope on Windows; runs unscoped", argv=argv)
    if not _systemd_user():
        return _result(True, "plain", "systemd-run unavailable; runs unscoped", argv=argv)
    probe = subprocess.run(["systemd-run", "--user", "--scope", "--quiet", "--", "true"],
                           capture_output=True, text=True, timeout=30, **windowless_kwargs())
    if probe.returncode != 0:
        return _result(True, "plain", f"a scope would not start: {(probe.stderr or probe.stdout).strip()}",
                       argv=argv)
    unit = unit or f"superclaude-{os.getpid()}"
    return _result(True, "scope",
                   f"MemoryHigh={mem_high} MemoryMax={mem_max} MemorySwapMax={swap_max} (unit {unit}.scope)",
                   argv=["systemd-run", "--user", "--scope", "--quiet", "--unit", f"{unit}.scope",
                         "-p", f"MemoryHigh={mem_high}", "-p", f"MemoryMax={mem_max}",
                         "-p", f"MemorySwapMax={swap_max}", "--"] + argv)


def scoped_exec(argv, mem_high: str, mem_max: str, swap_max: str, unit: str | None = None, log=None):
    """Replace this process with ``argv`` under a memory scope where the box has one.

    ``log`` (a callable taking one line) hears which way it went before the exec. On Windows
    there is no exec that keeps the console: the child runs and this process exits with its code.
    """
    res = scoped_argv(argv, mem_high, mem_max, swap_max, unit)
    if log:
        log(f"scope: {res['how']}: {res['detail']}")
    if _windows():
        sys.exit(subprocess.run(res["argv"]).returncode)
    sys.stdout.flush(); sys.stderr.flush()
    os.execvp(res["argv"][0], res["argv"])


def password_elevates(password: str) -> bool:
    """Does this password elevate (sudo -S -k, over stdin, never on a command line)?"""
    if _windows() or not shutil.which("sudo"):
        return False
    got = subprocess.run(["sudo", "-S", "-k", "-p", "", "true"], input=password + "\n",
                         capture_output=True, text=True, timeout=30, **windowless_kwargs())
    return got.returncode == 0


def elevation() -> dict:
    """Can this session elevate, and how: passwordless, a held password, or not at all."""
    if _windows():
        try:
            import ctypes
            admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            admin = False
        return _result(admin, "elevated" if admin else "not-elevated",
                       "the token is elevated" if admin else "the token is not elevated; sudo is not on Windows")
    if not shutil.which("sudo"):
        return _result(False, "none", "sudo is not on PATH")
    if subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=30,
                      **windowless_kwargs()).returncode == 0:
        return _result(True, "passwordless", "sudo -n works")
    pw = os.environ.get("CAIRN_SUDO_PW")
    if pw and password_elevates(pw):
        return _result(True, "password-held", "CAIRN_SUDO_PW elevates; serve it with SUDO_ASKPASS")
    return _result(False, "none", "sudo needs a password and none is held")

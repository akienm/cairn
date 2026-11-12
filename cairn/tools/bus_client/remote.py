"""remote — the client side of the instance's one bus process (ticket 48519f4789b1).

A tool: it speaks only the socket ``<home>/bus.sock`` and imports nothing from the bus
package (RULE 1 — the bus's public interface is the socket, and this is its published client).
The process itself is ``python3 -m cairn.devices.cairn.machines.bus serve``, spawned here by
``ensure_bus`` the way ``ensure_ground_loop`` spawns the heartbeat: the command lazy-inits the
system, and the bus's own flock decides who runs.

``RemoteBus`` has the face callers already used on a ``BusDevice`` (post, read, request,
undelivered, record_delivery, digest, list, toggle, flush, ring_depth), so the callers moved
by changing what they were handed, not how they speak. ``wire_delivery`` holds the device in
the bus process — delivery happens THERE, and the local hook is dropped by design.

THE BUS SERVES THE CODE THAT ASKS (decision 4). Every request carries this file's class root;
a bus started from another root, or one whose code changed under it, answers ``stale``, and
``_call`` shuts it down, starts one from this root, and retries once.

THE ADDRESS (ticket 5183005fa134). A home is a folder or ``host:port``. A folder is this box's
bus: ``<home>/bus.sock`` where Python has AF_UNIX, else the loopback port and key the bus wrote
to ``<home>/bus.port`` (Windows has no AF_UNIX — measured 2026-11-04 on akiendell). ``host:port``
is another box's bus, dialled over pinned mutual TLS (``tls``): never started from here, never
replaced from here, and never stale (it runs its own box's code).
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from cairn.tools.base.diagnostic import DiagnosticBase

# cairn/tools/bus_client/remote.py → three parents up is the class root.
_CLASS_ROOT = Path(__file__).resolve().parents[3]
_BUS_MODULE = "cairn.devices.cairn.machines.bus"
_DEFAULT_HOME = Path("~/.cairn/devices/cairn/machines/bus/0")
_LOG = Path("~/.cairn/logs/bus.log")
_NAME_HELD = ("already loaded", "fragment file", "already exists")
# A bounded wait in the launcher for the process it just started — not a poller (decision 5).
_START_WAIT_S = 15.0
# A verb may run a slow device (the librarian answers in seconds, a request can wait on a
# reply); the socket waits as long as the slowest caller already waited in-process.
_TIMEOUT_S = 900.0
# host:port — another box's bus. Two characters of host at least, so ``C:7419`` stays a path.
_REMOTE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]+:\d+$")
_PORT_FILE = "bus.port"


class BusStale(RuntimeError):
    """The bus process is running different code than the caller (decision 4)."""


def bus_home(home: str | Path | None = None) -> Path:
    if home is not None:
        return Path(home).expanduser()
    env = os.environ.get("CAIRN_BUS_HOME")
    return Path(env).expanduser() if env else _DEFAULT_HOME.expanduser()


def remote_address(home: str | Path | None = None) -> tuple[str, int] | None:
    """``(host, port)`` when the home names another box's bus, else None."""
    raw = str(home) if home is not None else os.environ.get("CAIRN_BUS_HOME", "")
    if not _REMOTE_RE.match(raw):
        return None
    host, _, port = raw.rpartition(":")
    return host, int(port)


def tls_dir() -> Path:
    """This box's identity and pins: ``CAIRN_BUS_TLS_DIR``, else the live bus home's ``tls``."""
    env = os.environ.get("CAIRN_BUS_TLS_DIR")
    return Path(env).expanduser() if env else _live_home() / "tls"


def _live_home() -> Path:
    """The instance's own bus home, read from the account's home directory in the password
    database — never from ``HOME``, which a proof points at a scratch folder. Windows has no
    password database; there the profile folder is the account's home."""
    try:
        import pwd
    except ImportError:
        return Path(os.path.expanduser("~")) / ".cairn/devices/cairn/machines/bus/0"
    return Path(pwd.getpwuid(os.getuid()).pw_dir) / ".cairn/devices/cairn/machines/bus/0"


def _unit(home: Path) -> str:
    """The systemd unit name for the bus at ``home`` (decision 11): ``CAIRN_BUS_UNIT`` if set,
    ``cairn-bus`` for the live instance's home, else ``cairn-bus-<hash of home>`` — one unit
    per bus home, so a scratch HOME never takes the live unit's name and never waits on it."""
    env = os.environ.get("CAIRN_BUS_UNIT")
    if env:
        return env
    if home == _live_home():
        return "cairn-bus"
    import hashlib
    return "cairn-bus-" + hashlib.sha1(str(home).encode()).hexdigest()[:10]


# The bus process registers itself here (``answer_in_process``), so code it hosts — a shim
# whose handler calls ``reach()`` — is answered on its OWN thread, never over the socket.
# Measured 2026-10-03: codemother's commit handler, running inside the bus under the hold
# lock, reached the bus through the socket; a second handler thread then waited on that lock
# for ever. On the same thread the bus's RLocks re-enter, as they did in one process before.
_IN_PROCESS: tuple[Path, object] | None = None


def answer_in_process(home: Path, answer) -> None:
    """Called once by the bus process at ``home``: requests to that home from inside the
    process go to ``answer(req) -> reply`` directly."""
    global _IN_PROCESS
    _IN_PROCESS = (Path(home), answer)


def exchange(request: dict, home: str | Path | None = None, *, timeout: float = _TIMEOUT_S) -> dict:
    """One JSON line out, one back. ``root`` is filled with this class root unless the
    request names one. ConnectionRefusedError / FileNotFoundError propagate: no bus."""
    req = {"root": str(_CLASS_ROOT), **request}
    if _IN_PROCESS is not None and bus_home(home) == _IN_PROCESS[0]:
        # The wire's shape both ways, so a caller cannot tell which path answered it.
        req = json.loads(json.dumps(req, default=str))
        return json.loads(json.dumps(_IN_PROCESS[1](req), default=str))
    line = _wire(req, home, timeout)
    if not line:
        raise ConnectionError("the bus process closed the socket without an answer")
    return json.loads(line)


def _wire(req: dict, home, timeout: float) -> str:
    """Send one line, read one, over the transport the address names."""
    far = remote_address(home)
    if far is not None:
        from cairn.tools.bus_client import tls
        conn = tls.dial(tls_dir(), far[0], far[1], timeout=timeout)
    elif hasattr(socket, "AF_UNIX"):
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            conn.settimeout(timeout)
            conn.connect(str(bus_home(home) / "bus.sock"))
        except BaseException:
            conn.close()
            raise
    else:
        # No AF_UNIX (Windows): the bus wrote its loopback port and key beside its lock. No
        # record is no bus — FileNotFoundError, the same signal a missing bus.sock gives.
        rec = json.loads((bus_home(home) / _PORT_FILE).read_text())
        if not rec.get("port"):
            raise FileNotFoundError(f"{bus_home(home) / _PORT_FILE} names no loopback port")
        req = {**req, "key": rec["key"]}
        conn = socket.create_connection(("127.0.0.1", int(rec["port"])), timeout=timeout)
    with conn:
        conn.sendall((json.dumps(req, default=str) + "\n").encode())
        with conn.makefile("r", encoding="utf-8") as fh:
            return fh.readline()


def _answers(home) -> dict | None:
    try:
        return exchange({"op": "stats"}, home, timeout=5)
    except (OSError, ValueError):
        return None


def _last_answer(home) -> str:
    try:
        return repr(exchange({"op": "stats"}, home, timeout=5))[:300]
    except Exception as exc:  # noqa: BLE001 — this IS the report of what went wrong
        return f"{type(exc).__name__}: {exc}"


def _note(text: str) -> None:
    log = _LOG.expanduser()
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().astimezone().isoformat(timespec='seconds')} client: {text}\n")
    except OSError:
        pass


def _beside_the_manager() -> bool:
    """Whether this process sees the filesystem the systemd user manager sees. A unit runs in
    the MANAGER's mount namespace: a caller inside a sandbox that swapped ``~/.cairn`` (the
    tester's instance seal) would start a bus serving the real home, never the one it can see
    — measured 2026-10-03, every proof that reached the bus under that seal read "spawned:
    none" against the live unit's name. The manager reports its namespace through a transient
    unit (measured 23ms); no systemd at all reads as beside it, and the setsid path runs."""
    try:
        r = subprocess.run(["systemd-run", "--user", "--wait", "--pipe", "--quiet", "--",
                            "readlink", "/proc/self/ns/mnt"],
                           capture_output=True, text=True, timeout=30)
        mine = os.readlink("/proc/self/ns/mnt")
    except (OSError, subprocess.SubprocessError):
        return True
    return r.returncode != 0 or r.stdout.strip() == mine


def _spawn(home: Path, scratch: bool, *, via_unit: bool = True) -> str:
    """Start the bus process — ``ensure_ground_loop``'s systemd-run block, spelled again for
    the bus (unit, SuccessExitStatus=3, append log, reset-failed retry, setsid fall-through).
    ``via_unit=False`` goes straight to setsid: the caller's filesystem is not the manager's."""
    log = _LOG.expanduser()
    log.parent.mkdir(parents=True, exist_ok=True)
    if not via_unit:
        return _setsid(home, scratch, log, "this process's mount namespace is not the user "
                                           "manager's — bus spawned with setsid beside it")
    if os.name == "nt":
        return _detached(home, scratch, log)
    unit = _unit(home)
    cmd = ["python3", "-m", _BUS_MODULE, "serve", "--home", str(home)]
    if scratch:
        cmd.append("--scratch")
    if not hasattr(socket, "AF_UNIX"):
        cmd.append("--tcp")
    env_home = os.environ.get("HOME", str(Path.home()))
    argv = ["systemd-run", "--user", "--quiet", "--unit", unit,
            "--working-directory", str(_CLASS_ROOT),
            f"--setenv=HOME={env_home}", f"--setenv=PATH={os.environ.get('PATH', '')}",
            "-p", "SuccessExitStatus=3",
            "-p", f"StandardOutput=append:{log}", "-p", f"StandardError=append:{log}"]
    # inside a test run the bus is the run's (the twin of 2120e74dcf44's mark on the loop):
    # systemd-run hands a unit the MANAGER's environment, so the run's id is carried by hand where
    # the tester's stop reads it (the manager's record), and a failed bus of a run collects itself
    test_id = os.environ.get("CAIRN_TESTER_TEST_ID")
    if test_id:
        argv += [f"--setenv=CAIRN_TESTER_TEST_ID={test_id}", "-p", "CollectMode=inactive-or-failed"]
    argv += ["--", *cmd]
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        r = None
    if r is not None and r.returncode == 0:
        _note(f"bus spawn attempted as {unit}.service (the flock decides; loser exits 3)")
        return "unit"
    if r is not None:
        err = (r.stderr or "") + (r.stdout or "")
        _note(err.strip())
        if any(k in err for k in _NAME_HELD) or ("Unit " in err and "already" in err):
            subprocess.run(["systemctl", "--user", "reset-failed", f"{unit}.service"],
                           capture_output=True, text=True, timeout=30)
            r2 = subprocess.run(argv, capture_output=True, text=True, timeout=30)
            if r2.returncode == 0:
                _note(f"bus spawn attempted as {unit}.service after reset-failed")
                return "unit"
            _note(f"{unit}.service refused the start — the name is held, so a bus already "
                  f"holds it: {((r2.stderr or '') + (r2.stdout or '')).strip()[:200]}")
            return "none"
    return _setsid(home, scratch, log,
                   "systemd-run unavailable — bus spawned with setsid (dies with this session)")


# Windows: the bus outlives the console that started it and opens no window. The values
# stand beside the names so a proof on Linux can read the flags a Windows spawn would pass.
_DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
_CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)


def _detached(home: Path, scratch: bool, log: Path) -> str:
    """The Windows spawn (the shape of superclaude's _sc_spawn_detached): this venv's python,
    TCP loopback, no console, its own process group."""
    cmd = [sys.executable, "-m", _BUS_MODULE, "serve", "--home", str(home), "--tcp"]
    if scratch:
        cmd.append("--scratch")
    with open(log, "a", encoding="utf-8") as fh:
        subprocess.Popen(cmd, cwd=str(_CLASS_ROOT), stdin=subprocess.DEVNULL, stdout=fh,
                         stderr=fh, close_fds=True,
                         creationflags=_DETACHED_PROCESS | _CREATE_NO_WINDOW
                         | _CREATE_NEW_PROCESS_GROUP)
    _note("bus spawned detached (Windows: no systemd, no AF_UNIX — loopback TCP)")
    return "detached"


def _setsid(home: Path, scratch: bool, log: Path, why: str) -> str:
    cmd = ["python3", "-m", _BUS_MODULE, "serve",
           "--home", str(home)]
    if scratch:
        cmd.append("--scratch")
    if not hasattr(socket, "AF_UNIX"):
        cmd.append("--tcp")
    with open(log, "a", encoding="utf-8") as fh:
        subprocess.Popen(cmd, cwd=str(_CLASS_ROOT), start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=fh, stderr=fh)
    _note(why)
    return "setsid"


def _unit_active(home: Path) -> bool:
    try:
        r = subprocess.run(["systemctl", "--user", "is-active", f"{_unit(home)}.service"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.stdout.strip() in ("active", "activating", "deactivating", "reloading")


def ensure_bus(home: str | Path | None = None, *, scratch: bool = False) -> dict:
    """The instance's bus process is answering when this returns, or it raises.

    Answering already = one stats exchange and nothing else. A bus answering ``stale`` is
    shut down and replaced by one from this class root. Returns the stats it ended with."""
    far = remote_address(home)
    if far is not None:
        # Another box's bus is that box's to start (Law 6): answer, or say who did not.
        found = _answers(home)
        if found is not None and found.get("ok"):
            return found["json"]
        raise ConnectionError(f"the bus at {far[0]}:{far[1]} did not answer "
                              f"(last answer: {_last_answer(home)}) — it is started on its box")
    home = bus_home(home)
    found = _answers(home)
    if found is not None and found.get("stale"):
        reply = _replace(home)
        found = None
        if reply and reply.get("draining"):
            # The stale bus is draining and serves on: use it. A spawn now would lose
            # bus.lock to it and raise (ticket 99258e9bbdb1).
            again = _answers(home)
            if again is not None and again.get("ok"):
                _note(f"stale bus at {home} draining {reply['draining']} request(s); "
                      "served by it until it exits")
                return again["json"]
    if found is not None and found.get("ok"):
        return found["json"]
    # A bus at any home but the live instance's rides a throwaway table (decision 11): a
    # proof's scratch HOME holds every shim it asks for, and holding drains mail — live mail
    # drained into a throwaway instance would be receipted and lost.
    beside = _beside_the_manager()
    # Beside a different filesystem the bus rides a throwaway table too: the home it serves
    # is a sandbox's copy, and mail drained into it would be receipted and lost.
    scratch = scratch or home != _live_home() or not beside
    spawned = _spawn(home, scratch, via_unit=beside)
    deadline = time.monotonic() + _START_WAIT_S
    while time.monotonic() < deadline:
        found = _answers(home)
        if found is not None and found.get("ok"):
            return found["json"]
        if spawned == "none" and not _unit_active(home):
            # The name was held by a bus on its way out (a stale one just shut down); once
            # the unit is gone the name is free, so start ours.
            spawned = _spawn(home, scratch, via_unit=beside)
        time.sleep(0.05)
    # What the socket last said is the diagnosis (Law 7): silence, a refusal, or stale.
    raise ConnectionError(f"no bus process answered at {home / 'bus.sock'} within "
                          f"{_START_WAIT_S:.0f}s (spawned: {spawned}; last answer: "
                          f"{_last_answer(home)}; log {_LOG})")


def _replace(home: Path) -> dict | None:
    """Shut a stale bus down and wait (bounded) for its socket to stop answering. Returns the
    shutdown's reply (None when the exchange raised). A bus holding requests answers
    ``draining`` and serves on until they are answered (ticket 1029d5146152): that reply
    returns at once, since waiting for it to stop answering would outlast the wait."""
    try:
        reply = exchange({"op": "shutdown"}, home, timeout=30)
    except (OSError, ValueError):
        reply = None
    if reply and reply.get("draining"):
        return reply
    deadline = time.monotonic() + _START_WAIT_S
    while time.monotonic() < deadline and _answers(home) is not None:
        time.sleep(0.05)
    unit = _unit(home)
    try:
        subprocess.run(["systemctl", "--user", "reset-failed", f"{unit}.service"],
                       capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        pass   # no systemd (Windows): nothing holds a unit name
    return reply


class RemoteBus(DiagnosticBase):
    """A bus handle that is a socket to the instance's one bus process."""

    def __init__(self, home: str | Path | None = None, *, scratch: bool = False) -> None:
        self._far = remote_address(home)
        self._home = str(home if home is not None else os.environ["CAIRN_BUS_HOME"]) \
            if self._far else bus_home(home)
        self._scratch = scratch

    def _call(self, request: dict) -> dict:
        try:
            reply = exchange(request, self._home)
        except (FileNotFoundError, ConnectionRefusedError):
            if self._far is not None:
                raise
            # No bus answers at this box's home: the command lazy-inits the system.
            ensure_bus(self._home, scratch=self._scratch)
            reply = exchange(request, self._home)
        if reply.get("stale") and self._far is not None:
            raise BusStale(f"the bus at {self._home} answered stale ({reply.get('root')}) — "
                           "a bus on another box is never replaced from here")
        if reply.get("stale"):
            _replace(self._home)
            ensure_bus(self._home, scratch=self._scratch)
            reply = exchange(request, self._home)
            if reply.get("stale"):
                raise BusStale(f"the bus process still runs other code ({reply.get('root')})")
        if not reply.get("ok"):
            error = reply.get("error", "the bus process refused without a reason")
            if error.startswith("LookupError: ") or error.startswith("no shim answers to"):
                raise LookupError(error.removeprefix("LookupError: "))
            raise RuntimeError(f"bus process: {error}")
        return reply

    def _method(self, method: str, **kwargs):
        return self._call({"op": "call", "method": method, "kwargs": kwargs}).get("json")

    # --- the BusDevice face -----------------------------------------------------------

    def post(self, **kwargs):
        return self._method("post", **kwargs)

    def read(self, **kwargs):
        return self._method("read", **kwargs)

    def count(self, **kwargs):
        return self._method("count", **kwargs)

    def request(self, **kwargs):
        return self._method("request", **kwargs)

    def undelivered(self, **kwargs):
        return self._method("undelivered", **kwargs)

    def record_delivery(self, *args, **kwargs):
        if args:
            kwargs = {"envelope_id": args[0], **kwargs}
        return self._method("record_delivery", **kwargs)

    def digest(self, **kwargs):
        return self._method("digest", **kwargs)

    def list(self, **kwargs):
        return self._method("list", **kwargs)

    def toggle(self, device_id: str, channel: str, enabled: bool) -> dict:
        return self._method("toggle", device_id=device_id, channel=channel, enabled=enabled)

    def flush(self) -> dict:
        return self._call({"op": "flush"}).get("json")

    def stats(self) -> dict:
        return self._call({"op": "stats"}).get("json")

    @property
    def ring_depth(self) -> int:
        return int(self.stats()["ring_depth"])

    def shutdown(self) -> dict:
        return exchange({"op": "shutdown"}, self._home, timeout=60)

    # --- the shims the process holds --------------------------------------------------

    def hold(self, *devices: str) -> dict:
        return self._call({"op": "hold", "devices": list(devices)})

    def hold_shim(self, spec: str) -> dict:
        return self._call({"op": "hold", "shim": spec})

    def verbs(self, device_or_shim: str, argv: list[str]) -> dict:
        key = "shim" if ":" in device_or_shim else "device"
        return self._call({"op": "verbs", key: device_or_shim, "verbs": list(argv)})

    def wire_delivery(self, device_id: str, _deliver=None) -> None:
        """Delivery happens in the bus process: holding the device there IS the wiring."""
        self.hold(device_id)

    def unwire_delivery(self, device_id: str) -> None:
        return None

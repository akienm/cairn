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
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

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


class BusStale(RuntimeError):
    """The bus process is running different code than the caller (decision 4)."""


def bus_home(home: str | Path | None = None) -> Path:
    if home is not None:
        return Path(home).expanduser()
    env = os.environ.get("CAIRN_BUS_HOME")
    return Path(env).expanduser() if env else _DEFAULT_HOME.expanduser()


def _live_home() -> Path:
    """The instance's own bus home, read from the account's home directory in the password
    database — never from ``HOME``, which a proof points at a scratch folder."""
    import pwd
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
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(timeout)
        conn.connect(str(bus_home(home) / "bus.sock"))
        conn.sendall((json.dumps(req, default=str) + "\n").encode())
        with conn.makefile("r", encoding="utf-8") as fh:
            line = fh.readline()
    if not line:
        raise ConnectionError("the bus process closed the socket without an answer")
    return json.loads(line)


def _answers(home) -> dict | None:
    try:
        return exchange({"op": "stats"}, home, timeout=5)
    except (OSError, ValueError):
        return None


def _note(text: str) -> None:
    log = _LOG.expanduser()
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().astimezone().isoformat(timespec='seconds')} client: {text}\n")
    except OSError:
        pass


def _spawn(home: Path, scratch: bool) -> str:
    """Start the bus process — ``ensure_ground_loop``'s systemd-run block, spelled again for
    the bus (unit, SuccessExitStatus=3, append log, reset-failed retry, setsid fall-through)."""
    log = _LOG.expanduser()
    log.parent.mkdir(parents=True, exist_ok=True)
    unit = _unit(home)
    cmd = ["python3", "-m", _BUS_MODULE, "serve", "--home", str(home)]
    if scratch:
        cmd.append("--scratch")
    env_home = os.environ.get("HOME", str(Path.home()))
    argv = ["systemd-run", "--user", "--quiet", "--unit", unit,
            "--working-directory", str(_CLASS_ROOT),
            f"--setenv=HOME={env_home}", f"--setenv=PATH={os.environ.get('PATH', '')}",
            "-p", "SuccessExitStatus=3",
            "-p", f"StandardOutput=append:{log}", "-p", f"StandardError=append:{log}",
            "--", *cmd]
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
    with open(log, "a", encoding="utf-8") as fh:
        subprocess.Popen(cmd, cwd=str(_CLASS_ROOT), start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=fh, stderr=fh)
    _note("systemd-run unavailable — bus spawned with setsid (dies with this session)")
    return "setsid"


def _unit_active(home: Path) -> bool:
    r = subprocess.run(["systemctl", "--user", "is-active", f"{_unit(home)}.service"],
                       capture_output=True, text=True, timeout=30)
    return r.stdout.strip() in ("active", "activating", "deactivating", "reloading")


def ensure_bus(home: str | Path | None = None, *, scratch: bool = False) -> dict:
    """The instance's bus process is answering when this returns, or it raises.

    Answering already = one stats exchange and nothing else. A bus answering ``stale`` is
    shut down and replaced by one from this class root. Returns the stats it ended with."""
    home = bus_home(home)
    found = _answers(home)
    if found is not None and found.get("stale"):
        _replace(home)
        found = None
    if found is not None and found.get("ok"):
        return found["json"]
    # A bus at any home but the live instance's rides a throwaway table (decision 11): a
    # proof's scratch HOME holds every shim it asks for, and holding drains mail — live mail
    # drained into a throwaway instance would be receipted and lost.
    spawned = _spawn(home, scratch or home != _live_home())
    deadline = time.monotonic() + _START_WAIT_S
    while time.monotonic() < deadline:
        found = _answers(home)
        if found is not None and found.get("ok"):
            return found["json"]
        if spawned == "none" and not _unit_active(home):
            # The name was held by a bus on its way out (a stale one just shut down); once
            # the unit is gone the name is free, so start ours.
            spawned = _spawn(home, scratch or home != _live_home())
        time.sleep(0.05)
    raise ConnectionError(f"no bus process answered at {home / 'bus.sock'} within "
                          f"{_START_WAIT_S:.0f}s (spawned: {spawned}; log {_LOG})")


def _replace(home: Path) -> None:
    """Shut a stale bus down and wait (bounded) for its socket to stop answering."""
    try:
        exchange({"op": "shutdown"}, home, timeout=30)
    except (OSError, ValueError):
        pass
    deadline = time.monotonic() + _START_WAIT_S
    while time.monotonic() < deadline and _answers(home) is not None:
        time.sleep(0.05)
    unit = _unit(home)
    subprocess.run(["systemctl", "--user", "reset-failed", f"{unit}.service"],
                   capture_output=True, text=True, timeout=30)


class RemoteBus:
    """A bus handle that is a socket to the instance's one bus process."""

    def __init__(self, home: str | Path | None = None, *, scratch: bool = False) -> None:
        self._home = bus_home(home)
        self._scratch = scratch

    def _call(self, request: dict) -> dict:
        reply = exchange(request, self._home)
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

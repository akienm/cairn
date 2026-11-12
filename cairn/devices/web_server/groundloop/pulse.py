"""web_server/groundloop/pulse.py — the ground loop's beat, as the web server's shim hears it.

The ground loop launches this file once a beat (heartbeat.spawn_pulses) and asks it nothing
back. It answers open-68fe4af67c6d, (b): the ground loop's pulse starts the web server's shim
like every other declared instance (outline 5.8.3.4.1). Ticket 0482542c2b7c.

- It reads its own device's DECLARED instances, the folders ``cairn/devices/web_server/<n>/``
  (outline 5.7.3.4), and pulses each one.
- Pulsing an instance whose shim is not up starts it (5.8.3.4.3). The shim lives in
  listener.py's process, and "up" is the port in the kernel's listen table: its own word that
  some process holds it, never a record's age, and read rather than dialled.
- When the shim is up there is nothing more to do. Nothing inside the web server's shim needs a
  beat; every request is an event.
- It runs on the cairn home only (outline 15.3.5): "a box that joins the instance starts no
  web server of its own". The home is CAIRN_HOME_HOST (6.3.7.4), read the way superclaude's
  ``_sc_is_cairn_home`` reads it: unset means not yet asked, and the box behaves as a home.
  The ground loop runs as a systemd unit, which does not see the shell rc the installer writes
  the answer into, so the rc line is read when the environment has none.

``ensure`` takes a port, a bind address, a unit name and a log, so a proof can drive it over a
scratch port with no unit; the live beat passes nothing.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEVICE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
LISTENER = DEVICE_DIR / "listener.py"
UNIT = "cairn-web-server"
LOG = Path.home() / ".cairn" / "logs" / "web_server.log"
HOME_VAR = "CAIRN_HOME_HOST"
PORT_VAR = "CAIRN_WEB_SERVER_PORT"


def declared_instances(device_dir: Path = DEVICE_DIR) -> list[str]:
    """The instance folders declared in class-space (5.7.3.4): every numbered subfolder."""
    return sorted((p.name for p in device_dir.iterdir() if p.is_dir() and p.name.isdigit()),
                  key=int)


def home_host(env=None, rc: Path | None = None) -> str:
    """CAIRN_HOME_HOST from the environment, else from the installer's ``export`` line in the
    shell rc; '' when neither holds it."""
    env = os.environ if env is None else env
    have = str(env.get(HOME_VAR, "")).strip()
    if have:
        return have
    rc = rc if rc is not None else Path.home() / ".bashrc"
    start = f"export {HOME_VAR}="
    try:
        for line in rc.read_text(errors="replace").splitlines():
            if line.strip().startswith(start):
                return line.strip()[len(start):].strip("'\"").strip()
    except OSError:
        pass
    return ""


def _addresses() -> set[str]:
    try:
        r = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5)
        return set(r.stdout.split())
    except (OSError, subprocess.SubprocessError):
        return set()


def is_cairn_home(host: str, *, me: str | None = None, addresses=None) -> bool:
    """Is this box the cairn home? Unset, this box's name, localhost, or one of its addresses."""
    if not host:
        return True
    h = host.lower().split(".")[0]
    me = (me if me is not None else platform.node()).lower().split(".")[0]
    if h in (me, "localhost", "127"):
        return True
    return host in (addresses if addresses is not None else _addresses())


def _listen_ports() -> set[int]:
    """The TCP ports some process LISTENS on, read from the kernel's own table: /proc/net/tcp
    and tcp6 (state 0A) on linux, ``netstat -ano -p TCP`` elsewhere. Read, never dialled, so
    the pulse opens no second door to any host (sole_path_holds)."""
    ports: set[int] = set()
    found = False
    for name in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            rows = Path(name).read_text().splitlines()[1:]
        except OSError:
            continue
        found = True
        for row in rows:
            f = row.split()
            if len(f) > 3 and f[3] == "0A":
                ports.add(int(f[1].rsplit(":", 1)[1], 16))
    if found:
        return ports
    try:
        r = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True,
                           timeout=10)
        for row in r.stdout.splitlines():
            f = row.split()
            if len(f) >= 4 and f[3].upper() == "LISTENING":
                ports.add(int(f[1].rsplit(":", 1)[1]))
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return ports


def listening(port: int) -> bool:
    """Does some process hold the port? The kernel's word, read from its listen table."""
    return port in _listen_ports()


def _note(log: Path, text: str) -> None:
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().astimezone().isoformat(timespec='seconds')} pulse: {text}\n")
    except OSError:
        pass


def _detached(argv: list[str], log: Path) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    kw: dict = {"cwd": str(REPO_ROOT), "stdin": subprocess.DEVNULL,
                "env": {**os.environ, "PYTHONPATH": str(REPO_ROOT)}}
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x08000000   # DETACHED_PROCESS | CREATE_NO_WINDOW
    else:
        kw["start_new_session"] = True
    with open(log, "ab") as fh:
        return subprocess.Popen(argv, stdout=fh, stderr=fh, **kw).pid


def ensure(port: int = 80, bind: str = "0.0.0.0", *, unit: str | None = UNIT,
           log: Path = LOG, python: str = sys.executable) -> dict:
    """Start the shim's process when nothing answers on ``port``. Returns
    ``{port, up, spawned, pid?, note}``, with spawned 'none' | 'unit' | 'setsid'. ``unit=None``
    skips systemd (a proof's scratch run). Never raises: every failure is a note in the log."""
    if listening(port):
        return {"port": port, "up": True, "spawned": "none", "note": "the shim answers"}
    argv = [python, str(LISTENER), "--port", str(port), "--bind", bind]
    try:
        if unit:
            r = subprocess.run(
                ["systemd-run", "--user", "--quiet", "--unit", unit,
                 "--working-directory", str(REPO_ROOT),
                 f"--setenv=HOME={os.environ.get('HOME', str(Path.home()))}",
                 f"--setenv=PATH={os.environ.get('PATH', '')}",
                 "-p", f"StandardOutput=append:{log}", "-p", f"StandardError=append:{log}",
                 "--", *argv], capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                _note(log, f"port {port} silent: started the shim as {unit}.service")
                return {"port": port, "up": False, "spawned": "unit", "note": f"{unit}.service"}
            err = ((r.stderr or "") + (r.stdout or "")).strip()
            if "already" in err or "fragment file" in err:
                # a unit of that name exists and the port is silent: it failed or is starting.
                subprocess.run(["systemctl", "--user", "reset-failed", f"{unit}.service"],
                               capture_output=True, text=True, timeout=30)
                _note(log, f"port {port} silent and {unit}.service exists: {err[:200]}; reset-failed, next beat retries")
                return {"port": port, "up": False, "spawned": "none", "note": f"unit exists: {err[:200]}"}
            _note(log, f"systemd-run refused ({err[:200]}); starting detached")
        pid = _detached(argv, log)
        _note(log, f"port {port} silent: started the shim detached, pid {pid}")
        return {"port": port, "up": False, "spawned": "setsid", "pid": pid, "note": "detached"}
    except FileNotFoundError:
        pid = _detached(argv, log)
        _note(log, f"systemd-run absent: started the shim detached, pid {pid}")
        return {"port": port, "up": False, "spawned": "setsid", "pid": pid, "note": "detached"}
    except Exception as exc:  # noqa: BLE001
        _note(log, f"start failed ({type(exc).__name__}: {exc})")
        return {"port": port, "up": False, "spawned": "none", "note": f"start failed: {exc}"}


def pulse(*, env=None, rc: Path | None = None, device_dir: Path = DEVICE_DIR,
          me: str | None = None, addresses=None, ensure_fn=ensure) -> list[dict]:
    """One beat: each declared instance, on the cairn home only. Instance 0 holds the port
    (CAIRN_WEB_SERVER_PORT, default 80); there is one web server (15.3.1), so a further
    instance is reported, never started on a second port nobody declared."""
    env = os.environ if env is None else env
    host = home_host(env, rc)
    out = []
    for n in declared_instances(device_dir):
        if not is_cairn_home(host, me=me, addresses=addresses):
            out.append({"instance": n, "spawned": "none",
                        "note": f"this box attaches to the cairn home {host} (outline 15.3.5)"})
        elif n == "0":
            out.append({"instance": n, **ensure_fn(int(env.get(PORT_VAR, "80") or 80))})
        else:
            out.append({"instance": n, "spawned": "none",
                        "note": "one web server (outline 15.3.1): only instance 0 holds a port"})
    return out


if __name__ == "__main__":
    print(json.dumps(pulse()))

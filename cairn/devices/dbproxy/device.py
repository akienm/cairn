"""device.py — the database proxy's face on the bus (ticket a22eb3c25ccd).

The bus constructs this on ``cairn database start``; construction is the wake. If the record's
pid is not alive the face spawns ``python -m cairn.devices.dbproxy`` detached and windowless
(outline 5.3.5.3.2), so the relay is its own process (outline 2.3.2), never the bus's thread.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from cairn.tools.base.device import BaseDevice

MODULE = "cairn.devices.dbproxy"
REPO = Path(__file__).resolve().parents[3]


def pid_alive(pid, os_name: str | None = None) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if (os_name or os.name) == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)        # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259         # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def spawn_argv_and_kwargs(os_name: str | None = None) -> tuple[list, dict]:
    from cairn.tools.windowless_spawn.windowless_spawn import background_pythonw, detached_kwargs
    name = os_name or os.name
    exe = background_pythonw(os_name=name) if name == "nt" else "python3"
    return [exe, "-m", MODULE], detached_kwargs(os_name=name)


class DatabaseProxyDevice(BaseDevice):

    def __init__(self, popen=subprocess.Popen, os_name: str | None = None) -> None:
        super().__init__()
        self._popen = popen
        self._os_name = os_name
        self.spawned_pid = None
        self.wake()

    @property
    def device_id(self) -> str:
        return "database"

    def _record(self) -> dict:
        from cairn.devices.dbproxy.__main__ import record_path
        try:
            return json.loads(record_path().read_text())
        except (OSError, ValueError):
            return {}

    def wake(self):
        rec = self._record()
        if rec.get("state") == "listening" and pid_alive(rec.get("pid"), self._os_name):
            return None
        from cairn.devices.dbproxy.__main__ import record_path
        log = record_path().with_name("relay.log")
        log.parent.mkdir(parents=True, exist_ok=True)
        argv, kw = spawn_argv_and_kwargs(self._os_name)
        with open(log, "ab") as fh:
            proc = self._popen(argv, cwd=str(REPO), stdin=subprocess.DEVNULL,
                               stdout=fh, stderr=fh, **kw)
        self.spawned_pid = proc.pid
        self.emit("relay_spawned", values={"pid": proc.pid, "argv": argv, "was": rec.get("state")})
        return proc

    def declared_verbs(self) -> dict:
        return {**super().declared_verbs()}

    def intention(self) -> dict:
        return {"what": "The database proxy: the one door a box's processes reach their database by.",
                "why": "One owner gates every write (Law 6); every box runs its own instance (outline 11.3.7)."}

    def state(self) -> dict:
        rec = self._record()
        if rec.get("state") == "listening" and not pid_alive(rec.get("pid"), self._os_name):
            rec = {**rec, "state": "stopped"}
        return rec

    def settings(self) -> dict:
        from cairn.devices.dbproxy.__main__ import ports
        listen, upstream = ports()
        return {"CAIRN_DBPROXY_LISTEN_PORT": listen, "CAIRN_DBPROXY_POSTGRES_PORT": upstream}

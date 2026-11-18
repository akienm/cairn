"""Proof for ticket cad4a0d27e0a — `start` re-wakes a dead relay while the proxy's face is up.

Measured 2026-11-18 on akienlivingroom at 7c07ae3a4: with the device face up, the relay was
killed (0 listeners on 5432); `cairn database start` answered 'database already running' while
`show status hot` read state stopped, and store.connect() raised 'still refused 60s after waking
the database proxy'. The face's presence was read as the relay's liveness.

1. with the face up and the relay's recorded pid dead, `start` calls the face's wake() and says
   'started database', never 'already running';
2. with the face up and the relay alive, `start` says 'already running' and wakes nothing;
3. with the face down, `start` brings the face up, whose construction is the wake.

In-process: the face is a DatabaseProxyDevice subclass whose record and wake are recorders,
and the shim's last_known snapshot is kept off disk.

    bin/cairn test cairn/devices/dbproxy/proofs/test_start_rewakes_a_dead_relay_under_a_live_face.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"cad4a0d27e0a": {
    "1": "test_a_dead_relay_under_a_live_face_is_rewoken",
    "2": "test_a_live_relay_is_already_running",
    "3": "test_a_down_face_is_brought_up_by_start",
}}


def _dead_pid() -> int:
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def _world(record: dict):
    """A shim whose face records wakes and whose relay record is `record` (mutable)."""
    from cairn.devices.dbproxy.device import DatabaseProxyDevice
    from cairn.devices.dbproxy.shim import DatabaseProxyShim
    wakes: list = []

    class _Face(DatabaseProxyDevice):
        def _record(self):
            return dict(record)

        def wake(self):
            wakes.append(dict(record))
            record.update(state="listening", pid=os.getpid())
            return None

    shim = DatabaseProxyShim(bus=None)
    shim._persist_last_known = lambda: None
    shim._read_last_known = lambda: None
    shim._start_device = lambda: _Face()
    return shim, wakes


def _up(shim, wakes):
    shim._ensure_device()
    assert shim._device is not None
    wakes.clear()


def test_a_dead_relay_under_a_live_face_is_rewoken():
    record = {"state": "listening", "pid": os.getpid()}
    shim, wakes = _world(record)
    _up(shim, wakes)
    record.update(state="listening", pid=_dead_pid())          # the relay crashed; the face lives
    out = shim.resolve(["start"])
    assert out["exit"] == 0, out
    assert "already running" not in out["text"], out
    assert out["text"] == "started database", out
    assert len(wakes) == 1, wakes


def test_a_live_relay_is_already_running():
    record = {"state": "listening", "pid": os.getpid()}
    shim, wakes = _world(record)
    _up(shim, wakes)
    out = shim.resolve(["start"])
    assert out["text"] == "database already running", out
    assert wakes == [], wakes


def test_a_down_face_is_brought_up_by_start():
    record = {"state": "stopped", "pid": _dead_pid()}
    shim, wakes = _world(record)
    out = shim.resolve(["start"])
    assert out["text"] == "started database", out
    assert len(wakes) == 1 and shim._device is not None, wakes


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)

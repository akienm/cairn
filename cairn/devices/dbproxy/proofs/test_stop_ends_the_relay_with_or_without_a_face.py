"""Proof for ticket 68d8d3add713 — `stop` ends the relay whether or not the proxy's face is up.

Measured 2026-11-18 on akienlivingroom (twice: at 7c07ae3a4 and at ddf670792): a relay outlived
the face host that spawned it, and `cairn database stop` answered 'database is not running' while
that relay still held 5432; it took Stop-Process to end it. And with the face up, stop only dropped
the in-process face: the relay process was never ended.

1. with the face down and the relay's recorded pid alive, `stop` ends that pid and says
   'stopped database';
2. with the face up and the relay alive, `stop` ends the relay's pid and the face reads down;
3. with the relay's recorded pid dead and the face down, `stop` says 'database is not running'
   and ends nothing.

In-process: the relay record lives at a scratch path (record_path is swapped), the kill is a
recorder (the "alive" pid is this process's own, so it must never really be signalled), and the
shim's last_known snapshot is kept off disk.

    bin/cairn test cairn/devices/dbproxy/proofs/test_stop_ends_the_relay_with_or_without_a_face.py
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"68d8d3add713": {
    "1": "test_stop_ends_an_orphaned_relay",
    "2": "test_stop_ends_the_relay_under_a_live_face",
    "3": "test_stop_over_a_dead_relay_is_not_running",
}}


def _dead_pid() -> int:
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


@contextlib.contextmanager
def _world(record: dict):
    """A shim over a relay record at a scratch path; kills and wakes are recorded, never done."""
    from cairn.devices.dbproxy import __main__ as relay_main
    from cairn.devices.dbproxy.device import DatabaseProxyDevice
    from cairn.devices.dbproxy.shim import DatabaseProxyShim
    kills: list = []
    with tempfile.TemporaryDirectory() as tmp:
        rec = Path(tmp) / "relay.json"
        rec.write_text(json.dumps(record))
        saved = relay_main.record_path
        relay_main.record_path = lambda: rec

        class _Face(DatabaseProxyDevice):
            def wake(self):
                return None

        shim = DatabaseProxyShim(bus=None)
        shim._persist_last_known = lambda: None
        shim._read_last_known = lambda: None
        shim._start_device = lambda: _Face()
        shim._kill = lambda pid: kills.append(pid)
        try:
            yield shim, kills, rec
        finally:
            relay_main.record_path = saved


def test_stop_ends_an_orphaned_relay():
    me = os.getpid()
    with _world({"state": "listening", "pid": me}) as (shim, kills, rec):
        assert shim._device is None
        out = shim.resolve(["stop"])
        assert out["text"] == "stopped database", out
        assert kills == [me], kills


def test_stop_ends_the_relay_under_a_live_face():
    me = os.getpid()
    with _world({"state": "listening", "pid": me}) as (shim, kills, rec):
        shim.resolve(["start"])
        assert shim._device is not None
        out = shim.resolve(["stop"])
        assert out["text"] == "stopped database", out
        assert kills == [me], kills
        assert shim._device is None, "the face still reads up after stop"


def test_stop_over_a_dead_relay_is_not_running():
    with _world({"state": "listening", "pid": _dead_pid()}) as (shim, kills, rec):
        out = shim.resolve(["stop"])
        assert out["text"] == "database is not running", out
        assert kills == [], kills


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

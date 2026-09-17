"""The root verbs resolve in the shim base, once (ticket b41b0c0fff0e; vocabulary ruled
2026-09-06 on 15d6a0ef9c11: list show get stop start settings, and `hot` the modifier).

PROVES: (1) a cold `list` names the six verbs and the two root views and starts nothing;
(2) a cold `show status` before any run prints `never run` and starts nothing; (3) `show status
hot` starts the device and the snapshot's timestamp is after the instant before the call;
(4) a NEW process's cold `show status` after (3) answers cached with (3)'s timestamp and starts
nothing; (5) `get status` is one line of JSON with exactly device/view/cached/timestamp/data;
(6) `settings` on a device with none prints exactly `No settings`, on the other the rendered
dict; (7) `start` then `stop` in one process read started/stopped and the snapshot's presence
ONLINE then OFFLINE, and a fresh process's `stop` reads not running; (8) `hot` as the verb and
an unknown verb are refused exit 2 with the six named; (9) no cairn/devices/*/shim.py declares
a `def resolve` and the base declares exactly one; (10) a device view named `status` is
refused as a collision.

THE SHIM IS DRIVEN IN A SUBPROCESS PER COMMAND UNDER A SCRATCH HOME — the instance root is read
from HOME at import (address.py), so the snapshot file lands under the scratch and the live
instance is never touched; a fresh process per command is the model every `cairn <device> ...`
actually runs under. The scratch carries a LIVE liveness record before any shim constructs, so
the d6eb399ab6ad start-the-loop check spawns nothing (that path is that ticket's proof).

A hollow build could not pass: teeth 3, 4 and 7 need a real device to wake, a real snapshot on
disk, and a second process to read it back.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.tools.base.shim import NEVER_BOOTED, OFFLINE, ONLINE, ROOT_VERBS, ROOT_VIEWS, BaseShim, cli_main  # noqa: E402

PROVES = [
    "cold list names the six verbs and the two root views and starts nothing",
    "cold show status before any run prints never run and starts nothing",
    "show status hot starts the device and stamps a timestamp after the call began",
    "a new process's cold show status answers cached with the hot run's timestamp",
    "get status is one line of JSON with exactly device/view/cached/timestamp/data",
    "settings prints exactly No settings on an empty dict and the rendered dict otherwise",
    "start then stop read started/stopped with presence ONLINE then OFFLINE; a fresh stop reads not running",
    "hot as the verb and an unknown verb are refused exit 2 with the six named",
    "def resolve lives once, in the base, and in no device shim",
    "a device view named status is refused as a collision",
]


# --- the fixtures: two devices, two shims ------------------------------------------------

class _Fixture(BaseDevice):
    def __init__(self, device_id: str) -> None:
        super().__init__()
        self._device_id = device_id

    @property
    def device_id(self) -> str:
        return self._device_id

    def intention(self) -> dict:
        return {"what": f"fixture {self._device_id}", "why": "proof"}

    def state(self) -> dict:
        return {"awake": True}

    def settings(self) -> dict:
        return {}


class WeatherDevice(_Fixture):
    def settings(self) -> dict:
        return {"colour": "red"}

    def declared_views(self) -> dict:
        return {"weather": lambda: {"sky": "clear"}}


class BareDevice(_Fixture):
    pass


class CollidingDevice(_Fixture):
    def declared_views(self) -> dict:
        return {"status": lambda: {"mine": True}}


class WeatherShim(BaseShim):
    @property
    def device_id(self) -> str:
        return "b41b-weather"

    def _start_device(self):
        return WeatherDevice(self.device_id)


class BareShim(BaseShim):
    @property
    def device_id(self) -> str:
        return "b41b-bare"

    def _start_device(self):
        return BareDevice(self.device_id)


class CollidingShim(BaseShim):
    @property
    def device_id(self) -> str:
        return "b41b-colliding"

    def _start_device(self):
        return CollidingDevice(self.device_id)


SHIMS = {"weather": WeatherShim, "bare": BareShim, "colliding": CollidingShim}


# --- the harness: one fresh process per command, under a scratch HOME ------------------------

def _scratch() -> Path:
    home = Path(tempfile.mkdtemp(prefix="b41b-home-"))
    from cairn.devices.cairn.machines.ground_loop.liveness import write_liveness
    lh = home / ".cairn" / "devices" / "cairn" / "0" / "machines" / "ground_loop"
    lh.mkdir(parents=True)
    write_liveness(datetime.now(timezone.utc).astimezone(), {"beats": 1, "subscribers": []}, os.getpid(), lh)
    return home


def _run(home: Path, which: str, *argv: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, HOME=str(home), PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, __file__, "--drive", which, *argv], env=env,
                          capture_output=True, text=True, timeout=120, cwd=str(ROOT))


def _snapshot(home: Path, which: str) -> dict | None:
    p = home / ".cairn" / "devices" / SHIMS[which]().device_id / "0" / "last_known.json"
    return json.loads(p.read_text()) if p.exists() else None


def _snapshot_path_exists(home: Path, which: str) -> bool:
    return (home / ".cairn" / "devices" / f"b41b-{which}" / "0" / "last_known.json").exists()


# --- the teeth ---------------------------------------------------------------------------------

def test_cold_list_starts_nothing(home: Path) -> None:
    r = _run(home, "weather", "list")
    assert r.returncode == 0, r.stderr
    lines = [ln.strip() for ln in r.stdout.splitlines()]
    for v in ROOT_VERBS:
        assert v in lines, (v, r.stdout)
    for v in ROOT_VIEWS:
        assert v in lines, (v, r.stdout)
    assert "weather" not in lines, "a cold list read the device's own views without a contract"
    assert not _snapshot_path_exists(home, "weather"), "a cold list wrote a snapshot — something started"
    print("ok test_cold_list_starts_nothing")


def test_cold_show_never_run(home: Path) -> None:
    r = _run(home, "weather", "show", "status")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "never run", r.stdout
    assert not _snapshot_path_exists(home, "weather"), "a cold show started the device"
    print("ok test_cold_show_never_run")


def test_hot_show_starts_and_stamps(home: Path) -> str:
    before = datetime.now(timezone.utc)
    r = _run(home, "weather", "show", "status", "hot")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data == {"intention": {"what": "fixture b41b-weather", "why": "proof"}, "state": {"awake": True}}, data
    snap = _snapshot(home, "weather")
    assert snap is not None and snap["presence"] == ONLINE, snap
    stamp = datetime.fromisoformat(snap["timestamp"])
    assert stamp >= before, (stamp, before)
    assert snap["introspect"]["settings"] == {"colour": "red"}, snap
    print(f"ok test_hot_show_starts_and_stamps ({snap['timestamp']})")
    return snap["timestamp"]


def test_new_process_cold_show_is_cached(home: Path, stamp: str) -> None:
    r = _run(home, "weather", "show", "status")
    assert r.returncode == 0, r.stderr
    head, body = r.stdout.split("\n", 1)
    assert head == f"cached {stamp} — the b41b-weather is not running; add hot for live values", head
    assert json.loads(body)["state"] == {"awake": True}, body
    assert _snapshot(home, "weather")["timestamp"] == stamp, "a cold show re-stamped the snapshot"
    print("ok test_new_process_cold_show_is_cached")


def test_get_is_one_line_one_shape(home: Path, stamp: str) -> None:
    r = _run(home, "weather", "get", "status")
    assert r.returncode == 0, r.stderr
    assert r.stdout.count("\n") == 1, r.stdout
    payload = json.loads(r.stdout)
    assert list(payload) == ["device", "view", "cached", "timestamp", "data"], list(payload)
    assert payload["device"] == "b41b-weather" and payload["view"] == "status"
    assert payload["cached"] is True and payload["timestamp"] == stamp, payload
    r = _run(home, "weather", "get", "weather", "hot")
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    assert payload["cached"] is False and payload["data"] == {"sky": "clear"}, payload
    r = _run(home, "bare", "get", "status")
    payload = json.loads(r.stdout)
    assert payload["data"] is None and payload["cached"] is True, payload
    print("ok test_get_is_one_line_one_shape")


def test_settings_literal_and_rendered(home: Path) -> None:
    r = _run(home, "bare", "settings", "hot")
    assert r.returncode == 0 and r.stdout.strip() == "No settings", (r.stdout, r.stderr)
    r = _run(home, "bare", "settings")
    assert r.returncode == 0 and r.stdout.strip() == "No settings", (r.stdout, r.stderr)
    r = _run(home, "weather", "settings", "hot")
    assert r.returncode == 0 and json.loads(r.stdout) == {"colour": "red"}, (r.stdout, r.stderr)
    r = _run(home, "weather", "show", "settings")
    assert r.returncode == 0 and r.stdout.startswith("cached ") and '"colour": "red"' in r.stdout, r.stdout
    print("ok test_settings_literal_and_rendered")


def test_start_then_stop(home: Path) -> None:
    # One process: start then stop — presence is this process's (every `cairn ...` is fresh).
    r = _run(home, "bare", "--then", "start", "--then", "stop")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["started b41b-bare", f"{ONLINE}", "stopped b41b-bare", f"{OFFLINE}"], r.stdout
    snap = _snapshot(home, "bare")
    assert snap["presence"] == OFFLINE and "introspect" in snap, snap
    r = _run(home, "bare", "stop")
    assert r.returncode == 0 and r.stdout.strip() == "b41b-bare is not running", (r.stdout, r.stderr)
    r = _run(home, "bare", "--then", "start", "--then", "start")
    assert r.stdout.splitlines()[2] == "b41b-bare already running", r.stdout
    print("ok test_start_then_stop")


def test_refusals_name_the_six(home: Path) -> None:
    for argv in (["hot"], ["frob"], ["HOT", "status"]):
        r = _run(home, "weather", *argv)
        assert r.returncode == 2, (argv, r.returncode, r.stdout, r.stderr)
        assert r.stdout == "", (argv, r.stdout)
    assert "root verbs: list show get stop start settings" in _run(home, "weather", "frob").stderr
    assert "modifier" in _run(home, "weather", "hot").stderr
    r = _run(home, "weather", "show")
    assert r.returncode == 2 and "views: status settings" in r.stderr, (r.stdout, r.stderr)
    r = _run(home, "weather", "show", "nothing", "hot")
    assert r.returncode == 2 and "views: status settings weather" in r.stderr, (r.stdout, r.stderr)
    r = _run(home, "weather", "SHOW", "Status", "Hot")   # system words fold (ruled 2026-09-07)
    assert r.returncode == 0 and json.loads(r.stdout)["state"] == {"awake": True}, (r.stdout, r.stderr)
    print("ok test_refusals_name_the_six")


def test_resolve_lives_in_the_base_only() -> None:
    r = subprocess.run(["git", "grep", "-n", "def resolve(", "--", "cairn/devices/*/shim.py"],
                       cwd=str(ROOT), capture_output=True, text=True)
    assert r.stdout.strip() == "", r.stdout
    base = (ROOT / "cairn" / "tools" / "base" / "shim.py").read_text()
    assert base.count("def resolve(") == 1, base.count("def resolve(")
    print("ok test_resolve_lives_in_the_base_only")


def test_status_view_collision_refused(home: Path) -> None:
    r = _run(home, "colliding", "show", "status", "hot")
    assert r.returncode == 2 and "collides with the root view" in r.stderr, (r.returncode, r.stdout, r.stderr)
    print("ok test_status_view_collision_refused")


# --- the driver: what the subprocess runs --------------------------------------------------

def _drive(argv: list[str]) -> int:
    which, rest = argv[0], argv[1:]
    cls = SHIMS[which]
    if "--then" not in rest:
        return cli_main(cls, rest)
    # `--then start --then stop`: several lines through ONE shim, presence printed after each.
    shim = cls()
    code = 0
    for word in [w for w in rest if w != "--then"]:
        result = shim.resolve([word])
        print(result["text"])
        print(shim.presence)
        code = code or result["exit"]
    return code


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drive":
        sys.exit(_drive(sys.argv[2:]))
    test_resolve_lives_in_the_base_only()
    home = _scratch()
    try:
        test_cold_list_starts_nothing(home)
        test_cold_show_never_run(home)
        stamp = test_hot_show_starts_and_stamps(home)
        test_new_process_cold_show_is_cached(home, stamp)
        test_get_is_one_line_one_shape(home, stamp)
        test_settings_literal_and_rendered(home)
        test_start_then_stop(home)
        test_refusals_name_the_six(home)
        test_status_view_collision_refused(home)
    finally:
        shutil.rmtree(home, ignore_errors=True)
    print("test_root_verbs: green")

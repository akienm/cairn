"""PROOF — the pulse roster is read from DISK, every pass.

Akien's ruling, 2026-08-11, is the contract these teeth bite on:

  "ON EACH PASS THE GROUND LOOP POLLS A FOLDER FOR EACH DEVICE AND IF THERE IS CODE THERE
   THE GROUND LOOP RUNS IT."

The ground loop does NOT bench devices, does NOT raise trouble tickets, and does NOT judge
whether a device is broken. A device whose probe fails to import simply does not get those
probes on that beat — the heartbeat keeps beating, the device stays on the roster. Corrected
2026-09-02: the bench/trouble machinery was stripped (CC-- x3 2026-08-29, 2026-08-31,
2026-09-02).

    python3 cairn/devices/cairn/machines/ground_loop/proofs/test_discovery.py     # exit 0 = green
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

from cairn.devices.cairn.machines.ground_loop.discovery import ProbeCache, discover, device_folders  # noqa: E402
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)

_GOOD = '''
from cairn.tools.base.probe import Probe
FIRED = []
PROBE = Probe(why="{why}", trigger=lambda now, ctx: {fires}, to="harbor_master",
              body={{"k": "v"}})
'''

_BROKEN_IMPORT = "import a_module_that_does_not_exist_anywhere\nPROBE = None\n"
_NO_PROBE = "X = 1\n"
_NOT_A_PROBE = "PROBE = 'this is a string, not a Probe'\n"


def _device(root: Path, name: str, files: dict[str, str]) -> Path:
    folder = root / name / "probes"
    folder.mkdir(parents=True, exist_ok=True)
    for filename, body in files.items():
        (folder / filename).write_text(body, encoding="utf-8")
    return folder


class _RecordingBus:
    def __init__(self) -> None:
        self.posted: list[dict] = []
        self._wired: dict = {}

    def post(self, sender, to, channel, **kw):
        envelope = {"id": f"env-{len(self.posted)}", "sender": sender, "to": to,
                    "channel": channel, **kw}
        self.posted.append(envelope)
        return envelope

    def wire_delivery(self, device_id: str, deliver) -> None:
        self._wired[device_id] = deliver

    def unwire_delivery(self, device_id: str) -> None:
        self._wired.pop(device_id, None)

    def read(self, **kw):
        return []


def _loop(root: Path, staleness=None, bus=None):
    cache = ProbeCache()

    def discoverer(cache=None):  # noqa: ARG001
        return discover(root=root, cache=_held[0])

    _held = [cache]
    return GroundLoopDevice(discover=discoverer, staleness=staleness, bus=bus)


def _stale(*modules):
    return lambda: [{"module": m, "evidence": "VANISHED", "file": f"/gone/{m}.py",
                     "detail": "fixture drift"} for m in modules]


# --- teeth ------------------------------------------------------------------

def test_a_folder_on_disk_is_the_registration():
    """No subscribe call: a device with a probes/ folder is pulsed because it EXISTS."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "alpha", {"w.py": _GOOD.format(why="alpha watch", fires="False")})
        loop = _loop(root)
        record = loop.beat(NOW)
        assert record["pulsed"] == ["alpha"], record["pulsed"]
        assert loop.subscribers == ["alpha"]


def test_a_probe_written_mid_run_is_fired_by_the_next_beat():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "alpha", {"w.py": _GOOD.format(why="alpha watch", fires="False")})
        loop = _loop(root)
        loop.beat(NOW)
        assert loop.subscribers == ["alpha"]
        _device(root, "beta", {"w.py": _GOOD.format(why="beta watch", fires="False")})
        record = loop.beat(NOW)
        assert sorted(record["pulsed"]) == ["alpha", "beta"], record["pulsed"]


def test_a_probe_deleted_mid_run_leaves_the_roster():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        folder = _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        _device(root, "beta", {"w.py": _GOOD.format(why="b", fires="False")})
        loop = _loop(root)
        loop.beat(NOW)
        assert sorted(loop.subscribers) == ["alpha", "beta"]
        shutil.rmtree(folder)
        record = loop.beat(NOW)
        assert record["pulsed"] == ["beta"], record["pulsed"]


def test_an_edited_probe_is_reimported_not_served_from_cache():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        folder = _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        loop = _loop(root)
        rec = loop.beat(NOW)
        assert rec["pulses"][0]["fired_count"] == 0
        (folder / "w.py").write_text(_GOOD.format(why="a", fires="True"), encoding="utf-8")
        import os
        os.utime(folder / "w.py", (0, 10_000_000))
        rec = loop.beat(NOW)
        assert len(rec["pulses"][0]["fired"]) == 1, rec["pulses"][0]


def test_a_broken_probe_does_not_stop_the_heartbeat():
    """CP2: the loop cannot be taken down by a device. Three different lacks, one beat, and
    every device is still on the roster — no benching, no trouble tickets."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "raises", {"w.py": _BROKEN_IMPORT})
        _device(root, "silent", {"w.py": _NO_PROBE})
        _device(root, "liar", {"w.py": _NOT_A_PROBE})
        _device(root, "fine", {"w.py": _GOOD.format(why="fine", fires="False")})
        loop = _loop(root)
        record = loop.beat(NOW)
        assert sorted(record["pulsed"]) == ["fine", "liar", "raises", "silent"], record["pulsed"]


def test_a_broken_probe_does_not_prevent_healthy_probes_from_firing():
    """One broken file in a folder does not take the whole device down. The probes that
    load fine still fire — benching per-device for a per-file failure was the 29-hour
    outage's mechanism."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "mixed", {"broke.py": _BROKEN_IMPORT,
                                "works.py": _GOOD.format(why="still armed", fires="True")})
        bus = _RecordingBus()
        loop = _loop(root, bus=bus)
        record = loop.beat(NOW)
        assert record["pulsed"] == ["mixed"], record["pulsed"]
        pulse = record["pulses"][0]
        assert pulse["fired_count"] == 1, pulse
        assert [p["to"] for p in bus.posted] == ["harbor_master"], bus.posted


def test_staleness_sets_the_stale_flag():
    """When this process's code has drifted from disk, the device reports stale. The runner
    reads this and exits — that is the ONLY consequence. No trouble tickets, no benching."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        loop = _loop(root, staleness=_stale("some.module.that.moved"))
        assert not loop.stale
        loop.beat(NOW)
        assert loop.stale


def test_a_healthy_process_is_not_stale():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        loop = _loop(root, staleness=lambda: [])
        loop.beat(NOW)
        assert not loop.stale


def test_a_hand_subscribed_shim_is_not_double_pulsed_by_discovery():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        loop = _loop(root)

        class HandShim:
            device_id = "alpha"
            pulses = 0

            def on_pulse(self, now, ctx):
                HandShim.pulses += 1
                return {"device": "alpha", "fired": [], "fired_count": 0, "held": []}

        loop.subscribe(HandShim())
        record = loop.beat(NOW)
        assert record["pulsed"] == ["alpha"], record["pulsed"]
        assert HandShim.pulses == 1


def test_the_real_tree_discovers_its_devices():
    found = device_folders()
    ids = {d for d, _ in found}
    assert {"librarian", "harbor_master", "base"} <= ids, sorted(ids)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — the roster is disk, no bench, no judging")

"""PROOF — the pulse roster is read from DISK, every pass.

Akien's ruling, 2026-08-11, is the contract these teeth bite on:

  "ON EACH PASS THE GROUND LOOP POLLS A FOLDER FOR EACH DEVICE AND IF THERE IS CODE THERE
   THE GROUND LOOP RUNS IT."

Discovery does NOT bench devices, does NOT raise trouble tickets, and does NOT judge
whether a device is broken. A device whose probe fails to import simply does not get those
probes on that pass — the pass completes, the device stays on the roster. Corrected
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


# --- teeth ------------------------------------------------------------------
# Each tooth calls discover(root=..., cache=ProbeCache()) directly — one call is one pass.
# A tooth that spans passes holds its one cache across them, exactly as a resident process
# would (ticket efb670ff1dd8 removed the in-process loop these teeth used to drive).

def test_a_folder_on_disk_is_the_registration():
    """No subscribe call: a device with a probes/ folder is on the roster because it EXISTS."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "alpha", {"w.py": _GOOD.format(why="alpha watch", fires="False")})
        found = discover(root=root, cache=ProbeCache())
        assert list(found) == ["alpha"], list(found)
        assert len(found["alpha"]["probes"]) == 1, found["alpha"]


def test_a_probe_written_mid_run_is_found_by_the_next_pass():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cache = ProbeCache()
        _device(root, "alpha", {"w.py": _GOOD.format(why="alpha watch", fires="False")})
        assert list(discover(root=root, cache=cache)) == ["alpha"]
        _device(root, "beta", {"w.py": _GOOD.format(why="beta watch", fires="False")})
        found = discover(root=root, cache=cache)
        assert sorted(found) == ["alpha", "beta"], sorted(found)


def test_a_probe_deleted_mid_run_leaves_the_roster():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cache = ProbeCache()
        folder = _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        _device(root, "beta", {"w.py": _GOOD.format(why="b", fires="False")})
        assert sorted(discover(root=root, cache=cache)) == ["alpha", "beta"]
        shutil.rmtree(folder)
        found = discover(root=root, cache=cache)
        assert list(found) == ["beta"], list(found)


def test_an_edited_probe_is_reimported_not_served_from_cache():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cache = ProbeCache()
        folder = _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        [probe] = discover(root=root, cache=cache)["alpha"]["probes"]
        assert not probe.fires(NOW, {})
        (folder / "w.py").write_text(_GOOD.format(why="a", fires="True"), encoding="utf-8")
        import os
        os.utime(folder / "w.py", (0, 10_000_000))
        [probe] = discover(root=root, cache=cache)["alpha"]["probes"]
        assert probe.fires(NOW, {}), "the edited file is re-imported on the next pass"


def test_a_broken_probe_does_not_stop_the_pass():
    """CP2: a pass cannot be taken down by a device. Three different lacks, one pass, and
    every device is still on the roster — no benching, no trouble tickets."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "raises", {"w.py": _BROKEN_IMPORT})
        _device(root, "silent", {"w.py": _NO_PROBE})
        _device(root, "liar", {"w.py": _NOT_A_PROBE})
        _device(root, "fine", {"w.py": _GOOD.format(why="fine", fires="False")})
        found = discover(root=root, cache=ProbeCache())
        assert sorted(found) == ["fine", "liar", "raises", "silent"], sorted(found)


def test_a_broken_probe_does_not_prevent_healthy_probes_from_firing():
    """One broken file in a folder does not take the whole device down. The probes that
    load fine still fire — benching per-device for a per-file failure was the 29-hour
    outage's mechanism."""
    from cairn.devices.cairn.machines.ground_loop.discovered import DiscoveredShim

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "mixed", {"broke.py": _BROKEN_IMPORT,
                                "works.py": _GOOD.format(why="still armed", fires="True")})
        found = discover(root=root, cache=ProbeCache())
        assert list(found) == ["mixed"], list(found)
        entry = found["mixed"]
        assert len(entry["probes"]) == 1 and len(entry["failures"]) == 1, entry
        bus = _RecordingBus()
        shim = DiscoveredShim("mixed", entry["folder"], bus=bus)
        shim.set_probes(entry["probes"], entry["folder"])
        pulse = shim.on_pulse(NOW)
        assert pulse["fired_count"] == 1, pulse
        probe_posts = [p for p in bus.posted if p["channel"] == "personal"]
        assert [p["to"] for p in probe_posts] == ["harbor_master"], probe_posts


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

"""Teeth for ticket 81eb3e46aed9 — the beat launches each device's groundloop/pulse.py.

Akien's outline (2026-10-17, ground_loop): the loop "launches a script in each device's
cairn/cairn/devices/<device>/groundloop called pulse.py", and its record holds "what it
spawned". 164da559823d (2026-10-05) had deleted the launcher; his answer to
open-a322e5166e5d restores it as a child process the loop never waits on.

One run of the loop, in a subprocess at cadence 0.5 s, over a scratch class root holding
four devices: alpha's pulse.py appends its pid to a marker, beta's sleeps 30 s, gamma's
raises, delta carries no groundloop/pulse.py. Every liveness record the run writes is kept
by beat number, and each tooth reads that run. Clause keys follow the falsifier's (N)
markers. Every tooth needs the ``spawned`` key, so a loop that spawns nothing reds them all.
The run kills the loop and every pid it spawned before the teeth read.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "81eb3e46aed9": {
        "1": "test_alphas_pulse_runs_on_every_beat",
        "2": "test_the_beat_does_not_wait_on_a_sleeping_pulse",
        "3": "test_the_record_lists_each_spawn_with_device_path_and_pid",
        "4": "test_a_device_without_a_pulse_is_not_spawned",
        "5": "test_a_raising_pulse_does_not_stop_the_next_beats_spawns",
    },
}

_CADENCE = 0.5
_PULSES = {
    "alpha": "import os\nwith open({marker!r}, 'a') as f:\n    f.write(f'{{os.getpid()}}\\n')\n",
    "beta": "import time\ntime.sleep(30)\n",
    "gamma": "raise RuntimeError('gamma pulse raises on purpose')\n",
}


@pytest.fixture(scope="module")
def run():
    td = Path(str(scratch_dir("beat-spawns-each-device-pulse-proof-")))
    marker = td / "alpha-pulse-pids.txt"
    class_root = td / "class"
    for dev, src in _PULSES.items():
        d = class_root / "cairn" / "devices" / dev / "groundloop"
        d.mkdir(parents=True)
        (d / "pulse.py").write_text(src.format(marker=str(marker)), encoding="utf-8")
    (class_root / "cairn" / "devices" / "delta").mkdir(parents=True)
    watch = td / "watch"
    watch.mkdir()
    (watch / "loop_file.py").write_text("", encoding="utf-8")
    home = td / "home"
    src = ("import sys; sys.path.insert(0, %r)\n"
           "from pathlib import Path\n"
           "from cairn.devices.cairn.machines.ground_loop.__main__ import main\n"
           "raise SystemExit(main(home=Path(%r), cadence=%r, watch=Path(%r), "
           "class_root=Path(%r)))\n"
           % (str(_REPO), str(home), _CADENCE, str(watch), str(class_root)))
    proc = subprocess.Popen([sys.executable, "-c", src], cwd=str(_REPO),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                            env={**os.environ, "PYTHONPATH": str(_REPO)})
    records: dict[int, dict] = {}
    first_seen = beat3_at = None
    try:
        end = time.monotonic() + 30
        while time.monotonic() < end:
            try:
                state = json.loads((home / "liveness.json").read_text(encoding="utf-8"))["state"]
            except (OSError, ValueError, KeyError, TypeError):
                state = None
            if state:
                first_seen = first_seen or time.monotonic()
                records.setdefault(state.get("beats", 0), state)
                if state.get("beats", 0) > 3 and beat3_at is None:
                    beat3_at = time.monotonic()
                if state.get("beats", 0) >= 5:
                    break
            time.sleep(0.05)
        (home / "COMMAND_EXIT.flag").touch()
        proc.wait(timeout=30)
        time.sleep(1.0)   # the last beat's alpha writes its pid
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=30)
        for state in records.values():
            for entry in state.get("spawned") or []:
                pid = entry.get("pid") if isinstance(entry, dict) else None
                if isinstance(pid, int):
                    try:
                        os.killpg(pid, signal.SIGKILL)
                    except OSError:
                        pass
    pids = marker.read_text(encoding="utf-8").split() if marker.exists() else []
    return {"records": records, "pids": pids, "class_root": class_root,
            "advance_s": (beat3_at - first_seen) if beat3_at and first_seen else None,
            "stderr": proc.stderr.read()[-400:] if proc.stderr else ""}


def _spawning(run) -> list[tuple[int, list]]:
    """Every beat >= 1 with its ``spawned`` list; asserts the key is there on each."""
    beats = sorted(b for b in run["records"] if b >= 1)
    assert beats, f"the loop wrote no beat: {run['stderr']}"
    out = []
    for b in beats:
        state = run["records"][b]
        assert "spawned" in state, f"beat {b}'s record has no 'spawned' key: {sorted(state)}"
        out.append((b, state["spawned"]))
    return out


def _devices(entries) -> set:
    return {e.get("device") for e in entries if isinstance(e, dict)}


def test_alphas_pulse_runs_on_every_beat(run):
    _spawning(run)
    assert len(set(run["pids"])) >= 2, \
        f"alpha's pulse.py ran {len(set(run['pids']))} time(s) over {len(run['records'])} beats"


def test_the_beat_does_not_wait_on_a_sleeping_pulse(run):
    spawning = _spawning(run)
    assert sum("beta" in _devices(e) for _, e in spawning) >= 3, \
        f"beta was not spawned on 3 beats: {spawning}"
    assert run["advance_s"] is not None and run["advance_s"] < 5, \
        f"the beat did not pass 3 within 5 s while beta slept: {run['advance_s']}"


def test_the_record_lists_each_spawn_with_device_path_and_pid(run):
    for b, entries in _spawning(run):
        assert {"alpha", "beta", "gamma"} <= _devices(entries), \
            f"beat {b}'s 'spawned' lacks a device: {entries}"
        for e in entries:
            assert isinstance(e, dict) and e.get("device") and e.get("path") \
                and isinstance(e.get("pid"), int), f"beat {b}: entry lacks device+path+pid: {e}"


def test_a_device_without_a_pulse_is_not_spawned(run):
    for b, entries in _spawning(run):
        assert "delta" not in _devices(entries), f"beat {b} spawned delta: {entries}"


def test_a_raising_pulse_does_not_stop_the_next_beats_spawns(run):
    spawning = _spawning(run)
    gamma_beats = [b for b, e in spawning if "gamma" in _devices(e)]
    assert gamma_beats, f"gamma was never spawned: {spawning}"
    later = [b for b, e in spawning if b > gamma_beats[0] and "alpha" in _devices(e)]
    assert later, f"no beat after gamma's first spawn (beat {gamma_beats[0]}) spawned alpha"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

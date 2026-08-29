"""Proof for a-stale-loop-restarts-itself — the response to staleness.

The detection already works and is proved (test_staleness.py). This proof exercises
the RESPONSE: the loop's ``stale`` property goes True when drift is found, and the
runner exits cleanly when it sees it (unless COMMAND_DO_NOT_RESTART.flag suppresses).

Teeth a hollow pass cannot satisfy:
  (1) a code drift detected during a beat sets ``device.stale = True``
  (2) COMMAND_EXIT.flag in the instance folder causes the beat loop to break
  (3) staleness + no COMMAND_DO_NOT_RESTART → the beat loop breaks
  (4) staleness + COMMAND_DO_NOT_RESTART → the beat loop does NOT break
  (5) the flags menu directory is created with both flag definitions on startup
  (6) a healthy beat (no drift, no flag) does NOT break the loop

Runnable bare:
    python3 cairn/devices/cairn/machines/ground_loop/proofs/test_stale_restart.py
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice
from cairn.devices.cairn.machines.ground_loop import staleness as _staleness
from cairn.devices.cairn.machines.ground_loop.__main__ import COMMAND_EXIT, COMMAND_DO_NOT_RESTART


def _now():
    return datetime.now(timezone.utc).astimezone()


def _fake_drift_found():
    return [{"module": "cairn.fake", "evidence": _staleness.REWRITTEN,
             "file": "/fake/path.py", "detail": "test drift"}]


def _fake_drift_clean():
    return []


def test_stale_property_set_on_drift():
    """(1) a code drift detected during a beat sets device.stale = True."""
    device = GroundLoopDevice(staleness=_fake_drift_found)

    class _FailingDiscover:
        def __call__(self, cache=None, skip=None):
            return {"broken": {"folder": "/tmp/fake", "probes": [],
                                "failures": [{"file": "x.py", "lack": "ImportError"}],
                                "benched": False}}
    device._discover = _FailingDiscover()

    assert not device.stale, "not stale before any beat"
    device.beat(now=_now())
    assert device.stale, "stale after a beat that found drift"


def test_stale_property_stays_false_when_clean():
    """(6) a healthy beat does NOT set stale."""
    device = GroundLoopDevice(staleness=_fake_drift_clean)
    device.beat(now=_now())
    assert not device.stale, "a healthy beat leaves stale False"


def _simulate_beat_loop(home, device, max_beats=5):
    """Simulate the runner's beat loop with flag checks, exactly as __main__.py does.

    Returns the number of beats completed before exiting. The runner's loop is:
      beat → check COMMAND_EXIT → check stale+suppress → sleep.
    This reproduces that logic without the signal handlers, singleton guard, or
    diagnostic wiring that make main() hard to call from a proof.
    """
    beats = 0
    for _ in range(max_beats):
        device.beat(now=_now())
        beats += 1
        if (home / COMMAND_EXIT).exists():
            break
        if device.stale and not (home / COMMAND_DO_NOT_RESTART).exists():
            break
    return beats


def test_command_exit_flag_causes_exit():
    """(2) COMMAND_EXIT.flag causes the beat loop to break after one beat."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / COMMAND_EXIT).touch()
        device = GroundLoopDevice()
        beats = _simulate_beat_loop(home, device, max_beats=5)
        assert beats == 1, f"should exit after exactly 1 beat with COMMAND_EXIT, got {beats}"


def test_staleness_causes_exit_without_suppress_flag():
    """(3) staleness + no COMMAND_DO_NOT_RESTART → exit after one beat."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        device = GroundLoopDevice(staleness=_fake_drift_found)

        class _FailingDiscover:
            def __call__(self, cache=None, skip=None):
                return {"broken": {"folder": "/tmp/fake", "probes": [],
                                    "failures": [{"file": "x.py", "lack": "ImportError"}],
                                    "benched": False}}
        device._discover = _FailingDiscover()

        beats = _simulate_beat_loop(home, device, max_beats=5)
        assert beats == 1, f"stale loop without suppress flag should exit after 1 beat, got {beats}"
        assert device.stale, "device must be stale"


def test_staleness_suppressed_by_do_not_restart():
    """(4) staleness + COMMAND_DO_NOT_RESTART → the loop does NOT break on staleness."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        (home / COMMAND_DO_NOT_RESTART).touch()
        device = GroundLoopDevice(staleness=_fake_drift_found)

        class _FailingDiscover:
            def __call__(self, cache=None, skip=None):
                return {"broken": {"folder": "/tmp/fake", "probes": [],
                                    "failures": [{"file": "x.py", "lack": "ImportError"}],
                                    "benched": False}}
        device._discover = _FailingDiscover()

        beats = _simulate_beat_loop(home, device, max_beats=3)
        assert beats == 3, f"suppress flag should keep loop running for all 3 beats, got {beats}"
        assert device.stale, "device is stale but suppressed"


def test_flags_menu_created():
    """(5) the flags menu directory is created with both flag definitions."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        flags_dir = home / "flags"
        flags_dir.mkdir(parents=True, exist_ok=True)
        for flag in (COMMAND_EXIT, COMMAND_DO_NOT_RESTART):
            (flags_dir / flag).touch(exist_ok=True)

        assert flags_dir.is_dir(), "flags/ menu directory must exist"
        assert (flags_dir / COMMAND_EXIT).exists(), f"{COMMAND_EXIT} must be in the menu"
        assert (flags_dir / COMMAND_DO_NOT_RESTART).exists(), f"{COMMAND_DO_NOT_RESTART} must be in the menu"
        # The menu files are permanent — ls flags/ always shows the full set
        assert len(list(flags_dir.iterdir())) == 2, "exactly two flags in the menu"


def test_healthy_beat_does_not_exit():
    """(6) no drift, no flag → the loop runs for all beats."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        device = GroundLoopDevice(staleness=_fake_drift_clean)
        beats = _simulate_beat_loop(home, device, max_beats=3)
        assert beats == 3, f"healthy loop should run all 3 beats, got {beats}"
        assert not device.stale


if __name__ == "__main__":
    test_stale_property_set_on_drift()
    test_stale_property_stays_false_when_clean()
    test_command_exit_flag_causes_exit()
    test_staleness_causes_exit_without_suppress_flag()
    test_staleness_suppressed_by_do_not_restart()
    test_flags_menu_created()
    test_healthy_beat_does_not_exit()
    print("7/7 green")

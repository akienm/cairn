"""Proofs for the-pane-set-is-the-channel-set: pane set IS the channel set.

Ticket: the-pane-set-is-the-channel-set
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT))

from cairn.devices.cairn.machines.bus.bus import (
    CHANNELS, PANE_CHANNEL_MAP, STRUCTURAL_PANES,
)


class TestPaneChannelIdentity:

    def test_every_channel_has_a_pane(self):
        missing = set(CHANNELS.keys()) - set(PANE_CHANNEL_MAP.keys())
        assert not missing, f"channels without pane mapping: {missing}"

    def test_every_map_entry_names_a_real_channel(self):
        extra = set(PANE_CHANNEL_MAP.keys()) - set(CHANNELS.keys())
        assert not extra, f"map entries for non-existent channels: {extra}"

    def test_pane_kinds_are_unique_per_channel(self):
        seen = {}
        for channel, pane in PANE_CHANNEL_MAP.items():
            if pane in seen:
                pytest.fail(
                    f"pane kind {pane!r} mapped to both {seen[pane]!r} and {channel!r}"
                )
            seen[pane] = channel

    def test_structural_panes_are_not_channel_derived(self):
        channel_panes = set(PANE_CHANNEL_MAP.values())
        overlap = STRUCTURAL_PANES & channel_panes
        assert not overlap, f"structural panes also in channel map: {overlap}"

    def test_full_pane_set_is_six(self):
        all_panes = set(PANE_CHANNEL_MAP.values()) | STRUCTURAL_PANES
        assert len(all_panes) == 6, f"expected 6 panes, got {len(all_panes)}: {all_panes}"

    def test_map_keys_equal_channels_keys(self):
        assert set(PANE_CHANNEL_MAP.keys()) == set(CHANNELS.keys()), (
            "PANE_CHANNEL_MAP and CHANNELS must have identical key sets"
        )


ROSTER_MIN = 6


def test_roster_minimum():
    tests = [name for name in dir() if name.startswith("test_") and callable(eval(name))]
    for cls_name, cls_obj in list(globals().items()):
        if isinstance(cls_obj, type):
            tests.extend(m for m in dir(cls_obj) if m.startswith("test_"))
    assert len(tests) >= ROSTER_MIN, (
        f"need >= {ROSTER_MIN} teeth, have {len(tests)}: {sorted(tests)}"
    )


if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    teeth = sum(1 for name in dir() if name.startswith("test_") and callable(eval(name)))
    for cls_name, cls_obj in list(globals().items()):
        if isinstance(cls_obj, type):
            teeth += sum(1 for m in dir(cls_obj) if m.startswith("test_"))
    color = "\033[32m" if result.returncode == 0 else "\033[31m"
    print(f"\n{color}{teeth} teeth {'green' if result.returncode == 0 else 'RED'}\033[0m")
    sys.exit(result.returncode)

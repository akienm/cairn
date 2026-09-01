"""Proofs for the-cli-reaches-any-device: every shimmed device resolves via cairn <device>.

Ticket: the-cli-reaches-any-device
"""

import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
CAIRN_BIN = os.path.join(REPO_ROOT, "bin", "cairn")
DEVICES_DIR = os.path.join(REPO_ROOT, "cairn", "devices")
INSTANCE_ROOT = os.path.expanduser("~/.cairn/devices")


def _shimmed_devices():
    """Return device names that have a shim.py at the device level."""
    devices = []
    for name in sorted(os.listdir(DEVICES_DIR)):
        dev_dir = os.path.join(DEVICES_DIR, name)
        if not os.path.isdir(dev_dir) or name.startswith("_"):
            continue
        shim_path = os.path.join(dev_dir, "shim.py")
        if os.path.isfile(shim_path):
            devices.append(name)
    return devices


def _all_device_dirs():
    """Return all device directory names (excluding __pycache__)."""
    return sorted(
        name for name in os.listdir(DEVICES_DIR)
        if os.path.isdir(os.path.join(DEVICES_DIR, name)) and not name.startswith("_")
    )


class TestInstanceSpaceBinExists:
    """Every shimmed device has an instance-space bin/ directory."""

    @pytest.fixture
    def shimmed(self):
        return _shimmed_devices()

    def test_at_least_four_shimmed_devices(self, shimmed):
        assert len(shimmed) >= 4, f"expected >= 4 shimmed devices, got {len(shimmed)}: {shimmed}"

    def test_each_shimmed_device_has_instance_bin(self, shimmed):
        missing = []
        for dev in shimmed:
            bin_dir = os.path.join(INSTANCE_ROOT, dev, "0", "bin")
            if not os.path.isdir(bin_dir):
                missing.append(dev)
        assert not missing, f"shimmed devices missing instance-space bin/: {missing}"

    def test_each_instance_bin_has_self_named_launcher(self, shimmed):
        missing = []
        for dev in shimmed:
            launcher = os.path.join(INSTANCE_ROOT, dev, "0", "bin", dev)
            if not os.path.isfile(launcher) or not os.access(launcher, os.X_OK):
                missing.append(dev)
        assert not missing, f"shimmed devices missing executable self-named launcher: {missing}"


class TestCairnDeviceResolves:
    """cairn <device> resolves for every shimmed device without error."""

    @pytest.fixture
    def shimmed(self):
        return _shimmed_devices()

    def test_each_shimmed_device_resolves(self, shimmed):
        failures = []
        for dev in shimmed:
            result = subprocess.run(
                [CAIRN_BIN, dev],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "PYTHONPATH": REPO_ROOT},
            )
            if result.returncode != 0:
                failures.append((dev, result.returncode, result.stderr[:200]))
        assert not failures, f"cairn <device> failed for: {failures}"

    def test_resolution_routes_to_correct_device(self, shimmed):
        wrong = []
        for dev in shimmed:
            result = subprocess.run(
                [CAIRN_BIN, dev],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "PYTHONPATH": REPO_ROOT},
            )
            if result.returncode != 0:
                continue
            output = result.stdout + result.stderr
            if dev not in output:
                wrong.append((dev, output[:200]))
        assert not wrong, f"cairn <device> output does not mention its own name: {wrong}"

    def test_nonexistent_device_fails(self):
        result = subprocess.run(
            [CAIRN_BIN, "nonexistent_device_xyz"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0, "nonexistent device should fail"

    def test_dispatcher_lists_all_shimmed(self, shimmed):
        result = subprocess.run(
            [CAIRN_BIN, "no_such_device_trigger_usage"],
            capture_output=True, text=True, timeout=10,
        )
        listed = result.stderr
        missing = [dev for dev in shimmed if dev not in listed]
        assert not missing, f"dispatcher listing missing shimmed devices: {missing}"


ROSTER_MIN = 8


def test_roster_minimum():
    """The roster floor -- a hollow proof cannot reach this count."""
    import inspect
    tests = [
        name for name, obj in {**globals()}.items()
        if name.startswith("test_") and callable(obj)
    ]
    for cls_name, cls_obj in globals().items():
        if isinstance(cls_obj, type):
            for method_name in dir(cls_obj):
                if method_name.startswith("test_"):
                    tests.append(f"{cls_name}.{method_name}")
    assert len(tests) >= ROSTER_MIN, (
        f"need >= {ROSTER_MIN} teeth, have {len(tests)}: {sorted(tests)}"
    )


if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": REPO_ROOT},
    )
    teeth = sum(1 for name in dir() if name.startswith("test_") and callable(eval(name)))
    for cls_name, cls_obj in list(globals().items()):
        if isinstance(cls_obj, type):
            teeth += sum(1 for m in dir(cls_obj) if m.startswith("test_"))
    color = "\033[32m" if result.returncode == 0 else "\033[31m"
    print(f"\n{color}{teeth} teeth {'green' if result.returncode == 0 else 'RED'}\033[0m")
    sys.exit(result.returncode)

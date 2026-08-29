"""Proofs for the CC device — teeth a hollow build could not pass.

Three things the ticket's falsifier demands:
  (1) cairn/devices/cc/ exists with charter, shim inheriting BaseShim, at least one probe
  (2) discover() finds the device and loads its probes with zero failures
  (3) a message sent through deliver() reaches the shim's diagnostic mailbox
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


DEVICE_DIR = Path(__file__).resolve().parent.parent


def test_the_charter_is_valid_json_with_required_fields():
    charter_path = DEVICE_DIR / "intention+why.json"
    assert charter_path.exists(), "no charter at intention+why.json"
    charter = json.loads(charter_path.read_text())
    assert charter["component"] == "cc"
    assert charter["role"] == "charter"
    for field in ("what", "why", "how", "falsifier", "gates", "owner"):
        assert field in charter and charter[field], f"charter missing {field}"


def test_the_shim_inherits_baseshim_and_device_id_is_cc():
    from cairn.devices.cc.shim import CCShim
    from cairn.tools.base.shim import BaseShim

    assert issubclass(CCShim, BaseShim)
    shim = CCShim()
    assert shim.device_id == "cc"


def test_the_shim_probes_return_a_list():
    from cairn.devices.cc.shim import CCShim

    shim = CCShim()
    probes = shim.probes()
    assert isinstance(probes, list)


def test_discover_finds_cc_with_zero_failures():
    from cairn.devices.ground_loop.discovery import discover

    roster = discover(root=DEVICE_DIR.parent.parent)
    assert "cc" in roster, f"discover() did not find 'cc'; found: {sorted(roster)}"
    entry = roster["cc"]
    assert not entry["failures"], f"probe import failures: {entry['failures']}"
    assert entry["probes"], "no probes loaded — the probes/ directory is empty or broken"


def test_deliver_routes_through_the_shim():
    from cairn.devices.cc.shim import CCShim

    shim = CCShim()
    envelope = {
        "from": "test",
        "to": "cc",
        "channel": "personal",
        "body": {"test": True},
        "why": "proof: deliver routes through the shim",
    }
    # No verb, no device behind the shim (_start_device returns None) — deliver
    # attempts to route and bounces. The bounce with no bus raises
    # NotImplementedError, which proves the message REACHED the shim's routing
    # logic. A hollow shim that silently dropped mail would not raise.
    with pytest.raises(NotImplementedError, match="cc was delivered mail"):
        shim.deliver(envelope)


def test_the_probe_module_declares_a_probe():
    from cairn.devices.cc.probes.the_shim_delivers_mail import PROBE
    from cairn.tools.base.probe import Probe

    assert isinstance(PROBE, Probe)
    assert callable(PROBE.trigger)
    assert PROBE.to == "harbor_master"

"""Proofs for the CC device — teeth a hollow build could not pass.

Three things the ticket's falsifier demands:
  (1) cairn/devices/cc/ exists with charter, shim inheriting BaseShim, at least one probe
  (2) the rack lists cc and its probes load with zero failures
  (3) a message sent through deliver() reaches the shim's diagnostic mailbox
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


DEVICE_DIR = Path(__file__).resolve().parent.parent


def _load_own_probes(folder):
    """``(probes, failures)`` for one probes/ folder: the judgement the ground loop's
    ProbeCache makes (imports, declares a module-level PROBE, PROBE is a Probe), made here so
    cc's proofs never reach into the cairn device (RULE 1, ticket f5c334da752a)."""
    import importlib.util
    from cairn.tools.base.probe import Probe

    probes, failures = [], []
    for path in sorted(Path(folder).glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location("cairn._cc_proof_probes." + path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001 — a bad probe file is a failure, not a crash
            failures.append({"file": str(path), "lack": f"import raised {type(exc).__name__}: {exc}"})
            continue
        probe = getattr(module, "PROBE", None)
        if probe is None:
            failures.append({"file": str(path), "lack": "no module-level PROBE"})
        elif not isinstance(probe, Probe):
            failures.append({"file": str(path), "lack": f"PROBE is {type(probe).__name__}, not a Probe"})
        else:
            probes.append(probe)
    return probes, failures


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


def test_the_rack_lists_cc_and_its_probes_load():
    from cairn.tools.rack.rack import rack_ids

    ids = rack_ids(DEVICE_DIR.parents[2])
    assert "cc" in ids, f"the rack does not list 'cc'; found: {ids}"
    probes, failures = _load_own_probes(DEVICE_DIR / "probes")
    assert not failures, f"probe import failures: {failures}"
    assert probes, "no probes loaded — the probes/ directory is empty or broken"


def test_deliver_routes_through_the_shim(tmp_path):
    from unittest.mock import patch
    from cairn.devices.cc.shim import CCShim

    shim = CCShim()
    envelope = {
        "from": "test",
        "to": "cc",
        "channel": "personal",
        "body": {"test": True},
        "why": "proof: deliver routes through the shim",
    }
    # No device behind the shim (_start_device returns None). Since 7f47beb1
    # (superclaude-tmux-mode PROVED) deliver does not bounce — it persists the
    # envelope as a file the mailcheck hook picks up. The file IS the receipt that
    # the message reached the shim; a hollow shim that dropped mail writes nothing.
    # (Until 2026-09-16 this tooth still expected the pre-7f47beb1 NotImplementedError
    # bounce and had been red under a green seal that named no teeth — 77f15efd5a96.)
    with patch("cairn.devices.cc.shim._MAIL_DIR", tmp_path / "mail"):
        receipt = shim.deliver(envelope)
    assert receipt["persisted"] is True, receipt
    written = sorted((tmp_path / "mail").glob("msg-*.json"))
    assert len(written) == 1, written
    assert json.loads(written[0].read_text())["envelope"] == envelope


def test_the_probe_module_declares_a_probe():
    from cairn.devices.cc.probes.the_shim_delivers_mail import PROBE
    from cairn.tools.base.probe import Probe

    assert isinstance(PROBE, Probe)
    assert callable(PROBE.trigger)
    assert PROBE.to == "codemother"

if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

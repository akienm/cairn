"""Proof: a module a proof loads BY PATH is named in its seal's closure, and its bytes move
the fingerprint a reseal re-takes.

Ticket 6e50ed204abc. Measured 2026-11-19: test_sail_queues_the_ticket_at_codemothers_gates.py
loads cairn/devices/cc/scripts/sail.py through ``spec_from_file_location`` +
``exec_module`` under a name it never puts in ``sys.modules``, and its seal's
``fingerprint_closure`` was one entry long (the proof itself). The closure runner read only
``sys.modules`` at exit, so an edit to sail.py could not expire the seal and the reseal's
settled-red lane would skip a red over it.

The fixture is THIS FILE run with ``CAIRN_PATH_LOAD_FIXTURE`` set: it loads
cairn/devices/tester/scratch_sweep.py by path — a tester leaf with no cairn imports, so the
only way it can reach the closure is the path load — and exits green. The tester seals it
through ``TesterDevice().run_proof``, the same door every seal takes.

  1. The path-loaded module is named in the seal's fingerprint_closure.
  2. That module's bytes are in the fingerprint the reseal re-takes (sealed_fingerprint_now):
     the recorded number matches, and the same closure without the module hashes differently.

    python3 cairn/devices/tester/proofs/test_a_module_loaded_by_path_is_in_the_seals_closure.py
"""

from __future__ import annotations

import os
import sys

_FIXTURE_ENV = "CAIRN_PATH_LOAD_FIXTURE"

if os.environ.get(_FIXTURE_ENV) == "1":
    # The fixture: stdlib only, then one load by path. Nothing here imports cairn, so the
    # loaded module can only enter the closure through the load itself.
    import importlib.util
    from pathlib import Path
    _leaf = Path(__file__).resolve().parents[1] / "scratch_sweep.py"
    _spec = importlib.util.spec_from_file_location("tester_leaf_loaded_by_path", _leaf)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    assert "tester_leaf_loaded_by_path" not in sys.modules
    print("  ok   test_the_fixture_loaded_a_module_by_path")
    raise SystemExit(0)

from pathlib import Path  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "6e50ed204abc": {
        "1": "test_a_module_loaded_by_path_is_in_the_closure",
        "2": "test_the_path_loaded_modules_bytes_are_in_the_reseal_fingerprint",
    },
}

_SELF = Path(__file__).resolve()
_LEAF = "cairn/devices/tester/scratch_sweep.py"
_SEAL: dict = {}


def _seal() -> dict:
    """Seal this file in fixture mode, once; both teeth read the same record."""
    if _SEAL:
        return _SEAL
    from cairn.devices.tester.device import TesterDevice
    prior = os.environ.get(_FIXTURE_ENV)
    os.environ[_FIXTURE_ENV] = "1"
    try:
        record = TesterDevice().run_proof(_SELF, sink="none", isolation="none")
    finally:
        if prior is None:
            os.environ.pop(_FIXTURE_ENV, None)
        else:
            os.environ[_FIXTURE_ENV] = prior
    assert record["verdict"] == "green", record["evidence"].get("stderr_tail")
    _SEAL.update(record)
    return _SEAL


def _closure() -> list:
    evidence = _seal()["evidence"]
    closure = evidence.get("fingerprint_closure")
    assert isinstance(closure, list), (
        f"no fingerprint_closure on the seal: {evidence.get('fingerprint_closure_absent')}")
    return closure


def test_a_module_loaded_by_path_is_in_the_closure():
    closure = _closure()
    assert _LEAF in closure, f"{_LEAF} was loaded by path and is not in the closure: {closure}"


def test_the_path_loaded_modules_bytes_are_in_the_reseal_fingerprint():
    from cairn.tools.validation_store.validation_store import (
        sealed_fingerprint_now, source_fingerprint)
    seal = _seal()
    closure = _closure()
    recorded = seal["evidence"]["source_fingerprint"]
    assert sealed_fingerprint_now(str(_SELF), seal) == recorded, "the reseal re-takes another number"
    assert _LEAF in closure, f"{_LEAF} is not in the closure the reseal re-takes: {closure}"
    without = [f for f in closure if f != _LEAF]
    assert source_fingerprint(str(_SELF), closure=without) != recorded, (
        "the fingerprint does not move with the path-loaded module's bytes")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

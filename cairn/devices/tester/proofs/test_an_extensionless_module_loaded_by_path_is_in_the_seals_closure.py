"""Proof: an EXTENSIONLESS repo file a proof executes by path (loaded in-process, or run as a
subprocess) is named in its seal's closure, so an edit to it stales the seal.

Ticket b7d5df9919fe. Measured 2026-11-20 (eb2f8f9b0b8c): after bin/cmd/deletegate changed, the
reseal-at-commit read test_delete_gate as "settled red, closure unmoved" and did not rerun it;
its fingerprint_closure was the proof alone. Two ``.py``-only filters dropped the gate: the exec
audit hook in cairn/devices/tester/device.py (ticket 6e50ed204abc's prior art) and
repo_relative_closure in cairn/tools/validation_store/validation_store.py. 9 proofs load an
extensionless file through spec_from_loader(name, SourceFileLoader(name, path)) + exec_module;
8 were blind by the filters. The ninth, cairn/tools/base/proofs/test_only_the_gate_writes_a_certificate.py,
loads bin/cmd/artifactgate, a file another component owns, so its closure drops it by design
(Akien 2026-10-05, ticket 184d211153ff: the closure stops at the component boundary). Counting
it blind was a measurement error, found when its built seal still omitted the gate. A subprocess-run one was blind by the second filter alone.

The fixture is THIS FILE run with ``CAIRN_EXTLESS_FIXTURE`` set to a mode, against the
extensionless, stdlib-only cairn/devices/tester/proofs/fixtures/extensionless_leaf:

  load  — spec_from_loader + SourceFileLoader + exec_module (the measured proofs' form)
  sub   — run it as a subprocess, never loading it in-process
  data  — open() it and read its bytes, never executing it

Each is sealed through ``TesterDevice().run_proof`` with sink none, the door every seal takes.

  1. load: the leaf is in fingerprint_closure, and its bytes are in the fingerprint the reseal
     re-takes (the recorded number matches; the closure without the leaf hashes differently).
  2. live: bin/proofs/test_delete_gate.py sealed by the built tester names bin/cmd/deletegate,
     and the fingerprint moves with its bytes; and every one of the 8 measured-blind proofs'
     committed validation names the extensionless file(s) it loads (red until they reseal).
  3. data: a file only READ is not in the closure, and neither is a .json read beside it.
  4. sub: the leaf run only as a subprocess is in fingerprint_closure (via the reach log).

    python3 cairn/devices/tester/proofs/test_an_extensionless_module_loaded_by_path_is_in_the_seals_closure.py
"""

from __future__ import annotations

import json
import os
import sys

_FIXTURE_ENV = "CAIRN_EXTLESS_FIXTURE"
_MODE = os.environ.get(_FIXTURE_ENV)

if _MODE:
    # The fixture: stdlib only, then exactly one touch of the leaf. Nothing here imports cairn.
    import importlib.machinery
    import importlib.util
    import subprocess
    from pathlib import Path
    _here = Path(__file__).resolve().parent
    _leaf = _here / "fixtures" / "extensionless_leaf"
    if _MODE == "load":
        _name = "tester_extensionless_leaf"
        _loader = importlib.machinery.SourceFileLoader(_name, str(_leaf))
        _spec = importlib.util.spec_from_loader(_name, _loader)
        _mod = importlib.util.module_from_spec(_spec)
        _loader.exec_module(_mod)
        assert _mod.VALUE == "extensionless leaf" and _name not in sys.modules
    elif _MODE == "sub":
        _out = subprocess.run([sys.executable, str(_leaf)], capture_output=True, text=True)
        assert _out.returncode == 0 and _out.stdout.strip() == "extensionless leaf", _out
    elif _MODE == "data":
        assert b"extensionless leaf" in _leaf.read_bytes()
        assert json.loads((_here.parent / "intention+why.json").read_text())
    else:
        raise SystemExit(f"unknown fixture mode {_MODE!r}")
    print(f"  ok   the fixture touched the leaf ({_MODE})")
    raise SystemExit(0)

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "b7d5df9919fe": {
        "1": "test_a_file_loaded_by_source_file_loader_is_in_the_closure",
        "2": "test_the_gate_proofs_seals_name_the_gates_they_load",
        "3": "test_a_file_only_read_is_not_in_the_closure",
        "4": "test_a_file_run_only_as_a_subprocess_is_in_the_closure",
    },
}

# Nested seals (four fixtures and test_delete_gate) run inside this one.
PROOF_TIMEOUT_S = 900

_SELF = Path(__file__).resolve()
_LEAF = "cairn/devices/tester/proofs/fixtures/extensionless_leaf"
_SEALS: dict = {}

# The measured blind set: proof → the extensionless file(s) it loads by path.
BLIND = {
    "bin/proofs/test_a_door_write_journaled_mid_pass_is_not_named.py": ["bin/cmd/artifactgate"],
    "bin/proofs/test_a_record_path_refusal_names_every_way_out.py": ["bin/cmd/artifactgate"],
    "bin/proofs/test_a_var_script_slot_runs_a_proof_only_through_its_loop.py": ["bin/cmd/proofgate"],
    "bin/proofs/test_artifact_gate.py": ["bin/cmd/artifactgate"],
    "bin/proofs/test_askscan.py": ["bin/cmd/askscan"],
    "bin/proofs/test_delete_gate.py": ["bin/cmd/deletegate", "bin/cmd/trash"],
    "bin/proofs/test_probescan.py": ["bin/cmd/probescan"],
    "bin/proofs/test_proof_gate.py": ["bin/cmd/proofgate"],
}
# Not blind: cairn/tools/base/proofs/test_only_the_gate_writes_a_certificate.py loads
# bin/cmd/artifactgate, which bin owns, and its closure stops at tools/base (ticket 184d211153ff).


def _seal(mode: str) -> dict:
    """Seal this file in one fixture mode, once per mode."""
    if mode in _SEALS:
        return _SEALS[mode]
    from cairn.devices.tester.device import TesterDevice
    prior = os.environ.get(_FIXTURE_ENV)
    os.environ[_FIXTURE_ENV] = mode
    try:
        record = TesterDevice().run_proof(_SELF, sink="none", isolation="none")
    finally:
        if prior is None:
            os.environ.pop(_FIXTURE_ENV, None)
        else:
            os.environ[_FIXTURE_ENV] = prior
    assert record["verdict"] == "green", record["evidence"].get("stderr_tail")
    _SEALS[mode] = record
    return record


def _closure(record: dict) -> list:
    evidence = record["evidence"]
    closure = evidence.get("fingerprint_closure")
    assert isinstance(closure, list), (
        f"no fingerprint_closure on the seal: {evidence.get('fingerprint_closure_absent')}")
    return closure


def _bytes_move_the_fingerprint(proof: Path, record: dict, rel: str) -> None:
    from cairn.tools.validation_store.validation_store import (
        sealed_fingerprint_now, source_fingerprint)
    closure = _closure(record)
    recorded = record["evidence"]["source_fingerprint"]
    assert sealed_fingerprint_now(str(proof), record) == recorded, "the reseal re-takes another number"
    without = [f for f in closure if f != rel]
    assert source_fingerprint(str(proof), closure=without) != recorded, (
        f"the fingerprint does not move with {rel}'s bytes")


def test_a_file_loaded_by_source_file_loader_is_in_the_closure():
    record = _seal("load")
    closure = _closure(record)
    assert _LEAF in closure, f"{_LEAF} was loaded by SourceFileLoader and is not in the closure: {closure}"
    _bytes_move_the_fingerprint(_SELF, record, _LEAF)


def test_the_gate_proofs_seals_name_the_gates_they_load():
    from cairn.devices.tester.device import TesterDevice
    proof = _REPO_ROOT / "bin" / "proofs" / "test_delete_gate.py"
    record = TesterDevice().run_proof(proof, sink="none", isolation="none")
    assert record["verdict"] == "green", record["evidence"].get("stderr_tail")
    closure = _closure(record)
    for rel in BLIND["bin/proofs/test_delete_gate.py"]:
        assert rel in closure, f"test_delete_gate's live seal does not name {rel}: {closure}"
        _bytes_move_the_fingerprint(proof, record, rel)

    blind = []
    for rel_proof, wanted in BLIND.items():
        p = Path(rel_proof)
        vpath = _REPO_ROOT / p.parent.parent / "validations" / (p.stem + ".json")
        try:
            entries = json.loads(vpath.read_text())
        except (OSError, ValueError) as exc:
            blind.append(f"{rel_proof}: validation unreadable ({exc})")
            continue
        entries = entries if isinstance(entries, list) else [entries]
        sealed = [e for e in entries
                  if isinstance(e, dict) and (e.get("evidence") or {}).get("fingerprint_closure")]
        if not sealed:
            blind.append(f"{rel_proof}: no sealed closure")
            continue
        closure = sealed[-1]["evidence"]["fingerprint_closure"]
        missing = [w for w in wanted if w not in closure]
        if missing:
            blind.append(f"{rel_proof}: closure {closure} does not name {missing}")
    assert not blind, ("committed seals still blind to the extensionless file they load — reseal "
                       "them under the built tester:\n  " + "\n  ".join(blind))


def test_a_file_only_read_is_not_in_the_closure():
    closure = _closure(_seal("data"))
    assert _LEAF not in closure, f"{_LEAF} was only READ and entered the closure: {closure}"
    assert "cairn/devices/tester/intention+why.json" not in closure, closure


def test_a_file_run_only_as_a_subprocess_is_in_the_closure():
    record = _seal("sub")
    closure = _closure(record)
    assert _LEAF in closure, f"{_LEAF} ran as a subprocess and is not in the closure: {closure}"
    _bytes_move_the_fingerprint(_SELF, record, _LEAF)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

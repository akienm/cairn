"""Proof: a script a proof runs as a subprocess is in its seal's closure even when the script ends
by falling off its last line.

Ticket 0a807f816e9f. Measured 2026-11-20 on akiendelllinux (CPython 3.14.4): under the reach
sitecustomize, ``print(1)`` alone logged no script, while ``raise SystemExit(0)`` and
``sys.exit(0)`` did. 3.14 pops ``__main__.__file__`` when a script runs to its end, and the
atexit logger read only ``__file__``. So a meta-proof whose subprocess script ended normally
sealed blind to that script. The fix (D1) makes the logger also record the ``argv[0]`` it
resolved at load, when ``__main__`` has lost ``__file__`` and ``argv[0]`` named a file.

The fixture is THIS FILE run with ``CAIRN_ENDS_NORMALLY_FIXTURE`` set to a mode:

  py   — run fixtures/a_script_that_ends_normally.py as a subprocess
  ext  — run fixtures/an_extensionless_script_that_ends_normally as a subprocess
  c    — run a ``python -c`` child
  m    — run a ``python -m json.tool --help`` child (a stdlib module that keeps __file__)

Each is sealed through ``TesterDevice().run_proof`` with sink none, the door every seal takes.

  1. py: the script is in fingerprint_closure, and its bytes are in the fingerprint the reseal
     re-takes (the recorded number matches; the closure without it hashes differently).
  2. ext: the same for the extensionless script.
  3. c and m: the closure holds nothing but the proof and the reach logger (nothing invented), and
     test_a_seal_records_what_it_reached.py seals green under the built logger.

    bin/cairn test cairn/devices/tester/proofs/test_a_subprocess_script_that_ends_normally_is_in_the_seals_closure.py
"""

from __future__ import annotations

import os
import sys

_FIXTURE_ENV = "CAIRN_ENDS_NORMALLY_FIXTURE"
_MODE = os.environ.get(_FIXTURE_ENV)

if _MODE:
    # The fixture: stdlib only, then exactly one subprocess. Nothing here imports cairn.
    import subprocess
    from pathlib import Path
    _fx = Path(__file__).resolve().parent / "fixtures"
    argv = {"py": [sys.executable, str(_fx / "a_script_that_ends_normally.py")],
            "ext": [sys.executable, str(_fx / "an_extensionless_script_that_ends_normally")],
            "c": [sys.executable, "-c", "print('a -c child')"],
            "m": [sys.executable, "-m", "json.tool", "--help"]}.get(_MODE)
    if argv is None:
        raise SystemExit(f"unknown fixture mode {_MODE!r}")
    _out = subprocess.run(argv, capture_output=True, text=True)
    assert _out.returncode == 0 and _out.stdout.strip(), _out
    print(f"  ok   the fixture ran its child ({_MODE})")
    raise SystemExit(0)

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "0a807f816e9f": {
        "1": "test_a_py_script_that_ends_normally_is_in_the_closure",
        "2": "test_an_extensionless_script_that_ends_normally_is_in_the_closure",
        "3": "test_a_c_or_m_child_invents_no_path",
    },
}

# Nested seals (four fixture modes and test_a_seal_records_what_it_reached) run inside this one.
PROOF_TIMEOUT_S = 900

_SELF = Path(__file__).resolve()
_SELF_REL = "cairn/devices/tester/proofs/" + _SELF.name
_PY = "cairn/devices/tester/proofs/fixtures/a_script_that_ends_normally.py"
_EXT = "cairn/devices/tester/proofs/fixtures/an_extensionless_script_that_ends_normally"
# Every child under the tester loads the reach logger itself; that file is executed, never invented.
_REACH = "cairn/devices/tester/reach/sitecustomize.py"
_SEALS: dict = {}


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


def _named_and_moves(mode: str, rel: str) -> None:
    from cairn.tools.validation_store.validation_store import (
        sealed_fingerprint_now, source_fingerprint)
    record = _seal(mode)
    closure = _closure(record)
    assert rel in closure, f"{rel} ran as a subprocess, ended normally, and is not in the closure: {closure}"
    recorded = record["evidence"]["source_fingerprint"]
    assert sealed_fingerprint_now(str(_SELF), record) == recorded, "the reseal re-takes another number"
    without = [f for f in closure if f != rel]
    assert source_fingerprint(str(_SELF), closure=without) != recorded, (
        f"the fingerprint does not move with {rel}'s bytes")


def test_a_py_script_that_ends_normally_is_in_the_closure():
    _named_and_moves("py", _PY)


def test_an_extensionless_script_that_ends_normally_is_in_the_closure():
    _named_and_moves("ext", _EXT)


def test_a_c_or_m_child_invents_no_path():
    for mode in ("c", "m"):
        closure = _closure(_seal(mode))
        invented = sorted(set(closure) - {_SELF_REL, _REACH})
        assert not invented, f"a -{mode} child put files in the closure it never executed: {invented}"
    from cairn.devices.tester.device import TesterDevice
    sibling = _REPO_ROOT / "cairn" / "devices" / "tester" / "proofs" / "test_a_seal_records_what_it_reached.py"
    record = TesterDevice().run_proof(sibling, sink="none", isolation="none")
    assert record["verdict"] == "green", record["evidence"].get("stderr_tail")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

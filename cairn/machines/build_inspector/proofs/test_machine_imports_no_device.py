"""Proof of the machine_imports_no_device sieve (ticket 76639374d9f9): a top-level machine that
imports a device reds, named by file and module; db_domain is forgiven by ENUMERATION (a
look-alike device is not); an instrument under proofs/ or probes/ may read what it measures; a
device row and a nested machine row are not this sieve's to judge; and an empty tree raises
rather than reading clean.

Its own file rather than a section of test_inspector.py, and the reason is the coverage
grammar: test_inspector.py prints one closing line and no tooth by name, so a tooth declared
there can never stand in a seal's ``teeth_green`` — proof_coverage could not credit clause
(a) to it, and a hollow reversion of inspector.py could never be seen to red it. Named teeth
are what make a proof evidence rather than a verdict.
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.machines.build_inspector.inspector import SIEVES, machine_imports_no_device
from cairn.tools.import_sieve.sieve import HollowScan

# Coverage declaration read by cairn.tools.proof_coverage: clause (a) of 76639374d9f9 is
# "openai_wire imports no device — the new machine_imports_no_device sieve says so, not a
# reading". The sieve saying so is this tooth; openai_wire reading clean under it is the
# build gate's measurement at the crossing.
PROVES = {
    "76639374d9f9": {"a": "a_machine_importing_a_device_reds_by_file_and_module"},
}

PASS = 0
FAIL = 0
_TMP: list[str] = []


def _scratch(prefix):
    d = tempfile.mkdtemp(prefix=prefix)
    _TMP.append(d)
    return Path(d)


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _fixture_root():
    mr = _scratch("inspector-proof-machines-") / "cairn"
    for name, line in [("dialer", "from cairn.devices.inference_domain import domain\n"),
                       ("storer", "from cairn.devices.db_domain import store\n"),
                       ("lookalike", "import cairn.devices.db_domain_x.store\n"),
                       ("clean", "import json\n")]:
        d = mr / "machines" / name
        (d / "proofs").mkdir(parents=True)
        (d / "probes").mkdir()
        (d / "x.py").write_text(line)
        (d / "proofs" / "test_x.py").write_text("from cairn.devices.inference_domain import domain\n")
        (d / "probes" / "p.py").write_text("from cairn.devices.bus import bus\n")
    return mr


MR = _fixture_root()


def _shake(name, dir_=None):
    row = {"dir": dir_ or f"machines/{name}", "component": name}
    return machine_imports_no_device(row, MR / row["dir"])


def the_sieve_is_registered_under_its_own_name():
    assert SIEVES["machine_imports_no_device"] is machine_imports_no_device


def a_machine_importing_a_device_reds_by_file_and_module():
    caught = _shake("dialer")
    assert [f["method"] for f in caught] == ["machine_imports_no_device"], caught
    assert "dialer/x.py" in caught[0]["about"] and "cairn.devices.inference_domain" in caught[0]["about"], caught
    assert caught[0]["values"]["file"].endswith("machines/dialer/x.py"), caught


def db_domain_is_the_one_forgiven_device():
    assert _shake("storer") == []


def the_exemption_is_enumerated_not_a_prefix():
    look = _shake("lookalike")
    assert len(look) == 1 and "db_domain_x" in look[0]["about"], look


def proofs_and_probes_are_instruments_and_may_read_a_device():
    assert _shake("clean") == []


def a_device_row_and_a_nested_machine_are_not_this_sieves_to_judge():
    assert _shake("dialer", "devices/dialer") == []
    assert _shake("dialer", "devices/x/machines/dialer") == []


def an_empty_tree_raises_rather_than_reading_clean():
    hollow = _scratch("inspector-proof-hollow-") / "cairn" / "machines" / "hollow"
    hollow.mkdir(parents=True)
    try:
        machine_imports_no_device({"dir": "machines/hollow", "component": "hollow"}, hollow)
    except HollowScan:
        return
    raise AssertionError("an empty machines tree read clean instead of raising HollowScan")


TEETH = [
    the_sieve_is_registered_under_its_own_name,
    a_machine_importing_a_device_reds_by_file_and_module,
    db_domain_is_the_one_forgiven_device,
    the_exemption_is_enumerated_not_a_prefix,
    proofs_and_probes_are_instruments_and_may_read_a_device,
    a_device_row_and_a_nested_machine_are_not_this_sieves_to_judge,
    an_empty_tree_raises_rather_than_reading_clean,
]

if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn.__name__, fn)
    finally:
        for d in _TMP:
            shutil.rmtree(d, ignore_errors=True)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

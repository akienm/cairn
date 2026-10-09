"""Proof for ticket c54d744aa9ac — a seal inside a seal INHERITS, it never asks for a second one.

THE MEASURED FAILURE THIS EXISTS FOR. On this host (AppArmor unpriv_bwrap, kernel 7.0.0-34) a
process already inside a bwrap namespace cannot create another: bwrap prints "No permissions to
create a new namespace" and exits 1. The tester wraps EVERY proof in bwrap for the instance seal
(``NoIsolation.wrap`` with a swap) and for the network seal (``NetnsIsolation.wrap``), so any
proof that drives ``cairn test`` as a subprocess died the moment the outer run was itself
sealed. Measured 2026-10-01: the pre-commit reseal read test_a_first_seal_is_taken_under_the_seal
red with exactly that bwrap line, a proof that is green bare.

The network seal already knew how to inherit (``SEAL_MARKER``, ticket 481221f45884). The instance
seal did not: it had no marker, so an inner run re-bound a swap it could not mount, and its probe
read INDETERMINATE. The build gives the instance seal the same shape — a marker set by the
sandbox that carries the swap, wraps that skip bwrap when nothing new is needed, and an inherited
branch in ``check_instance_seal`` that MEASURES the inherited mount rather than trusting the
marker.

The network seal is retired (ticket d80360545e91): the outer sandbox now carries the instance
seal alone, and the inner run seals with plain ``--seal``. What this proof measures — that a
sandbox inside a sandbox inherits instead of asking for a second namespace — is unchanged.

Teeth a hollow build could not pass:

  1. A NESTED TESTER RUN REPORTS ITS FIXTURE GREEN. ``cairn test --seal`` driven from inside
     a tester sandbox carrying the instance seal exits 0 and lands a green record.
  2. THE INNER WRITE LANDS IN THE OUTER SWAP ONLY. The fixture writes a file under ``~/.cairn``;
     it is in the swap, not in the live root, and the inner run's own record witnessed it.
  3. THE MARKER WITHOUT A MOUNT READS BREACHED. Set ``CAIRN_TESTER_INSTANCE_SEALED=1`` by hand
     over a directory that is no mount point and the inherited branch says BREACHED — the marker
     chooses which question to ask, the mount table answers it.

    python3 cairn/devices/tester/proofs/test_a_seal_inside_a_seal_inherits.py   # exit 0 = green
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"c54d744aa9ac": {"1": "test_a_nested_tester_run_reports_its_fixture_green",
                           "2": "test_the_inner_write_lands_in_the_outer_swap_only",
                           "3": "test_the_instance_marker_without_a_mount_reads_breached"}}

# The fixture's file name carries this process's pid, so a leaked copy says whose it was.
_FIXTURE_NAME = f"nested-seal-fixture-{os.getpid()}"


def _fixture(tmp: str) -> Path:
    comp = Path(tmp) / "somecomp"
    (comp / "proofs").mkdir(parents=True)
    (comp / "intention+why.json").write_text(
        json.dumps({"what": "a throwaway", "why": "a throwaway"}), encoding="utf-8")
    (comp / "proofs" / "test_nested_fixture.py").write_text(
        "from pathlib import Path\n\n"
        "def test_one():\n"
        f"    (Path.home() / '.cairn' / {_FIXTURE_NAME!r}).write_text('x')\n"
        "    assert True\n\n"
        "if __name__ == '__main__':\n    test_one(); print('PASS: one')\n",
        encoding="utf-8")
    return comp


def _outer(inner_argv: list[str]):
    """Run ``inner_argv`` inside a tester sandbox carrying the instance seal; return (run, swap).

    AT WHATEVER DEPTH THIS PROOF FINDS ITSELF, like its sibling's nested tooth: under the
    tester's own seal it already IS the outer sandbox and runs the inner argv directly (swap is
    the inherited ``_INSTANCE_ROOT``); bare, it cuts the outer sandbox itself (swap is a fresh
    snapshot the caller removes)."""
    from cairn.devices.tester import isolation as I

    if I.inside_an_instance_seal():
        run = subprocess.run(inner_argv, capture_output=True, text=True, cwd=os.getcwd())
        return run, None
    swap = I.snapshot_instance_space()
    argv = I.NoIsolation().wrap(inner_argv, os.getcwd(), instance_swap=swap)
    run = subprocess.run(argv, capture_output=True, text=True, cwd=os.getcwd())
    return run, swap


def _last_entry(comp: Path) -> dict:
    landed = sorted((comp / "validations").glob("*.json"))
    assert len(landed) == 1, f"expected one landed validation, got {landed}"
    return json.loads(landed[0].read_text(encoding="utf-8"))[-1]


def _inner(comp: Path) -> list[str]:
    return [sys.executable, "-m", "cairn.devices.tester.cli", str(comp),
            "--seal", "--timeout", "120"]


def test_a_nested_tester_run_reports_its_fixture_green():
    with tempfile.TemporaryDirectory() as tmp:
        comp = _fixture(tmp)
        run, swap = _outer(_inner(comp))
        try:
            assert run.returncode == 0, (
                f"a tester run nested inside a tester sandbox did not run green "
                f"(rc={run.returncode}):\n{run.stdout[-2000:]}\n{run.stderr[-2000:]}")
            entry = _last_entry(comp)
            assert entry["verdict"] == "green", json.dumps(entry, indent=1)[:3000]
        finally:
            if swap is not None:
                shutil.rmtree(Path(swap).parent, ignore_errors=True)
            (Path.home() / ".cairn" / _FIXTURE_NAME).unlink(missing_ok=True)


def test_the_inner_write_lands_in_the_outer_swap_only():
    from cairn.devices.tester import isolation as I

    with tempfile.TemporaryDirectory() as tmp:
        comp = _fixture(tmp)
        run, swap = _outer(_inner(comp))
        try:
            assert run.returncode == 0, (
                f"the nested run did not complete (rc={run.returncode}):\n"
                f"{run.stdout[-2000:]}\n{run.stderr[-2000:]}")
            if swap is not None:
                assert (Path(swap) / _FIXTURE_NAME).exists(), \
                    f"the fixture's write is not in the outer swap {swap}"
                assert not (Path(I._INSTANCE_ROOT) / _FIXTURE_NAME).exists(), \
                    "the fixture's write reached the LIVE instance root"
            else:
                # Inherited depth: the live root is not visible from in here; _INSTANCE_ROOT IS
                # the outer swap, which the inner run shared rather than re-binding.
                assert (Path(I._INSTANCE_ROOT) / _FIXTURE_NAME).exists(), \
                    "the fixture's write is not in the inherited swap"
            wrote = (_last_entry(comp).get("evidence") or {}) \
                .get("instance_seal", {}).get("wrote_to_instance")
            assert _FIXTURE_NAME in json.dumps(wrote), (
                f"the inner run did not witness its subject's write: wrote_to_instance={wrote}")
        finally:
            if swap is not None:
                shutil.rmtree(Path(swap).parent, ignore_errors=True)
            (Path.home() / ".cairn" / _FIXTURE_NAME).unlink(missing_ok=True)


def test_the_instance_marker_without_a_mount_reads_breached():
    from cairn.devices.tester import isolation as I
    from cairn.tools.scratch.scratch import scratch_dir

    was = os.environ.get("CAIRN_TESTER_INSTANCE_SEALED")
    os.environ["CAIRN_TESTER_INSTANCE_SEALED"] = "1"
    try:
        seal = I.check_instance_seal(I.NoIsolation(),
                                     str(scratch_dir("nested_seal_fixture_unmounted_")),
                                     os.getcwd())
    finally:
        if was is None:
            os.environ.pop("CAIRN_TESTER_INSTANCE_SEALED", None)
        else:
            os.environ["CAIRN_TESTER_INSTANCE_SEALED"] = was
    assert seal.verdict == I.BREACHED, f"{seal.verdict}: {seal.detail}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))

#!/usr/bin/env python3
"""Proof that the chart's validate door refuses a criterion whose instrument the sealer cannot run (477f3b58142e).

Measured twice. 2026-11-19 on akiendelllinux: a4892e762b70's validate (drafted on Windows) carried
'cairn/devices/codemother/machines/clearance/proofs/test_declaring_returns_posix_paths.py run with the
venv python'; ``verdict.extract_command`` returned it as runnable because the head path exists, and the
verdict exited 126. 2026-11-22: a4a3f5634e7c's verdict ran
'cairn/devices/codemother/machines/build_inspector/proofs/test_a_ticket_whose_build_is_on_main_has_crossed.py'
and exited 126, "Permission denied". Both heads are git mode 100644: the sealer's checkout holds the
index mode, whatever the drafting box's disk says (outline 9.4.8.1).

The world is a scratch git repo: a proof committed 100644, an executable committed 100755, and the
validate door run over a packet naming them, rooted there. No instrument forks.

    bin/cairn test cairn/devices/codemother/machines/validate/proofs/test_the_chart_refuses_an_instrument_this_box_cannot_run.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

PROVES = {"477f3b58142e": {
    "1": "test_an_instrument_headed_by_a_100644_proof_is_refused",
    "2": "test_extract_command_reads_the_index_mode_on_any_box",
    "3": "test_the_same_proof_through_an_executable_runner_passes",
}}

ENTRY = "every_criterion_instrument_runs_on_the_sealer"
PROOF = "x/proofs/test_a.py"
EXE = "bin/runner"


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                   env=dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull))


def _repo(tmp: str) -> Path:
    """A scratch repo: PROOF committed 100644 (but chmod +x on disk), EXE committed 100755."""
    root = Path(tmp) / "repo"
    (root / "x" / "proofs").mkdir(parents=True)
    (root / "bin").mkdir()
    (root / PROOF).write_text("PROVES = {}\n", encoding="utf-8")
    (root / EXE).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", "--", PROOF, EXE)
    _git(root, "update-index", "--chmod=-x", "--", PROOF)
    _git(root, "update-index", "--chmod=+x", "--", EXE)
    _git(root, "-c", "user.name=fx", "-c", "user.email=fx@example.invalid", "commit", "-q", "-m", "fx")
    os.chmod(root / PROOF, 0o755)  # executable on THIS disk; the index says otherwise
    os.chmod(root / EXE, 0o755)
    return root


def _packet(*instruments: str) -> dict:
    return {"ticket": "000000000000", "unknowns": ["none"], "confidence": 0.9,
            "provenance": {"criteria": "cc", "unknowns": "cc"},
            "criteria": [{"claim": f"claim {i}", "instrument": ins, "covers": ["the piece"]}
                         for i, ins in enumerate(instruments, 1)]}


def _entry(root: Path, packet: dict):
    from cairn.devices.codemother.machines.validate import validate as VD
    found = [e for e in VD.inspect_validate(packet, root=str(root)) if e.get("identity") == ENTRY]
    return found[0] if found else None


def _passed(e) -> bool:
    return bool(e) and e["expected"] == e["actual"]


def _lack(e) -> str:
    return str((e or {}).get("values", {}).get("lack") or "")


def test_an_instrument_headed_by_a_100644_proof_is_refused():
    """(1) the a4892e762b70 / a4a3f5634e7c shape is refused, naming the criterion, quoting the
    instrument; a prose criterion beside a good one is refused by the same entry, naming only it."""
    with tempfile.TemporaryDirectory(prefix="unrunnable-") as t:
        root = _repo(t)
        ins = f"{PROOF} run with the venv python"
        e = _entry(root, _packet(ins))
        prose = "the proof is green when it is run"
        e2 = _entry(root, _packet(f"{EXE} test {PROOF}", prose))
    assert e is not None, f"the validate door asked no {ENTRY} question"
    assert not _passed(e) and "claim 1" in _lack(e) and ins in _lack(e), (e, _lack(e))
    assert e2 is not None and not _passed(e2), e2
    assert "claim 2" in _lack(e2) and prose in _lack(e2) and "claim 1" not in _lack(e2), _lack(e2)
    print("ok test_an_instrument_headed_by_a_100644_proof_is_refused")


def test_extract_command_reads_the_index_mode_on_any_box():
    """(2) the head's git index mode decides, never this disk's bit: a 100644 proof executable on
    disk extracts to None, so the verdict has nothing to run; a 100755 head still extracts; an
    untracked path in the checkout is not on the sealer and extracts to None; shell heads,
    PATH-resolved heads, assignments and a path outside the repo extract unchanged."""
    from cairn.devices.codemother.machines.verdict import verdict as V
    with tempfile.TemporaryDirectory(prefix="unrunnable-") as t:
        root = _repo(t)
        assert os.access(root / PROOF, os.X_OK), "fixture: the proof must be executable on disk"
        got_proof = V.extract_command(f"{PROOF} run with the venv python", str(root))
        got_exe = V.extract_command(f"{EXE} test {PROOF}", str(root))
        fresh = root / "bin" / "fresh"
        fresh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        os.chmod(fresh, 0o755)
        got_fresh = V.extract_command("bin/fresh go", str(root))
        outside = Path(t) / "outside.sh"
        outside.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        os.chmod(outside, 0o755)
        same = {cmd: V.extract_command(cmd, str(root)) for cmd in (
            "cd x && true", f"python3 {PROOF}", f"PYTHONPATH=. python3 {PROOF}", f"{outside} go")}
    assert got_proof is None, got_proof
    assert got_exe == f"{EXE} test {PROOF}", got_exe
    assert got_fresh is None, got_fresh
    assert all(k == v for k, v in same.items()), same
    print("ok test_extract_command_reads_the_index_mode_on_any_box")


def test_the_same_proof_through_an_executable_runner_passes():
    """(3) the same criterion re-headed by a 100755 runner (bin/cairn test <proof>) passes."""
    with tempfile.TemporaryDirectory(prefix="unrunnable-") as t:
        root = _repo(t)
        e = _entry(root, _packet(f"{EXE} test {PROOF}"))
    assert e is not None and _passed(e), e
    print("ok test_the_same_proof_through_an_executable_runner_passes")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

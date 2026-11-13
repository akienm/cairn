"""Proof for ticket a4892e762b70 — the clearance gate's declaring() returns posix proof paths.

Measured 2026-11-13 on Windows: the PROVEME crossing of 703d3ec3619c journaled proven_by with
backslashes because ClearanceGate.proven_by falls back to declaring(), which returned
str(p.relative_to(repo)). A record of truth is written posix at its writer.

    python3 cairn/devices/codemother/machines/clearance/proofs/test_declaring_returns_posix_paths.py
"""
from __future__ import annotations

import tempfile
from pathlib import Path

PROVES = {"a4892e762b70": {
    "1": "test_declaring_returns_a_forward_slash_path",
    "2": "test_declaring_still_finds_the_proof",
}}

TID = "a4892e762b70"


def _declared(tmp: str):
    from cairn.devices.codemother.machines.clearance.gate import ClearanceGate
    repo = Path(tmp) / "cairn"
    commons = Path(tmp) / "CairnCommons"
    proofs = repo / "cairn" / "devices" / "alpha" / "proofs"
    proofs.mkdir(parents=True)
    commons.mkdir()
    (proofs / "test_alpha.py").write_text(
        f'PROVES = {{"{TID}": {{"1": "test_x"}}}}\n\ndef test_x():\n    pass\n', encoding="utf-8")
    gate = ClearanceGate(participant=object(),
                         roots={"repo": repo, "commons": commons, "instance": Path(tmp) / ".cairn"})
    return gate.declaring(TID)


def test_declaring_returns_a_forward_slash_path():
    with tempfile.TemporaryDirectory() as tmp:
        got = _declared(tmp)
        assert got == ["cairn/devices/alpha/proofs/test_alpha.py"], got
        assert all("\\" not in one for one in got), got


def test_declaring_still_finds_the_proof():
    with tempfile.TemporaryDirectory() as tmp:
        assert len(_declared(tmp)) == 1


if __name__ == "__main__":
    import sys
    bad = 0
    for name in PROVES[TID].values():
        try:
            globals()[name]()
            print("  PASS ", name)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print("  FAIL ", name, repr(e))
    sys.exit(1 if bad else 0)

"""Proof — the hollow-anchor fixture repo pins core.autocrlf false.

Measured 2026-11-13 on Windows: with git's default autocrlf=true the fixture wrote subject.py LF
and git stored the blob, but the worktree read back CRLF, so the anchor-holds-every-file tooth read a
reading where Linux raises. A fixture that holds the bytes git stored on every box does not depend on
the host's git config.

One tooth, one clause: build the fixture for real and read the scratch repo's own config.

    python3 cairn/devices/tester/proofs/test_the_anchor_fixture_pins_its_line_endings.py
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for _p in (str(ROOT), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

PROVES = {"2c3ea22bc266": {"1": "test_the_fixture_repo_pins_core_autocrlf_false"}}


def test_the_fixture_repo_pins_core_autocrlf_false():
    anchors = importlib.import_module("test_hollow_anchors_before_the_build_that_stands")
    repo, _commons, _berths, _shas = anchors._fixture(
        [("commit", "2020-01-01T00:00:00", "c0", 1, True)])
    got = subprocess.run(["git", "-C", str(repo), "config", "--local", "--get", "core.autocrlf"],
                         capture_output=True, text=True)
    assert got.stdout.strip() == "false", (got.returncode, got.stdout, got.stderr)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

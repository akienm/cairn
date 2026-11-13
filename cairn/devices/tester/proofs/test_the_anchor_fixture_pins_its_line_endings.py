"""Proof that the hollow-anchor fixture repo holds the bytes it writes, on every box.

Measured 2026-11-13 on Windows: test_hollow_anchors_before_the_build_that_stands.py's
``_fixture`` ran ``git init`` and nothing else, so the box's ``core.autocrlf=true`` applied. The
fixture writes subject.py with ``write_text`` (CRLF on Windows) and git stored LF, so a worktree
checked out from the anchor held different bytes from the blob, ``hollow._revert`` read an
unchanged file as ``reverted``, and test_an_anchor_holding_every_file_raises_naming_the_anchor
returned a green reading where it must refuse. The real repo is LF-pinned; the fixture repo had
no pin of its own.

The tooth builds the fixture for real and reads the repo's own config, so it reds on Linux too
(an unset autocrlf reads as nothing, not ``false``).

    python <this file>
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SUBJECT = Path(__file__).resolve().parent / "test_hollow_anchors_before_the_build_that_stands.py"

PROVES = {
    "2c3ea22bc266": {
        "1": "the_fixture_repo_pins_core_autocrlf_false",
    },
}


def test_the_fixture_repo_pins_core_autocrlf_false():
    sys.path.insert(0, str(REPO))
    spec = importlib.util.spec_from_file_location("anchor_fixture_subject", SUBJECT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    repo, _commons, _berths, _c = m._fixture([("commit", "2020-01-01T00:00:00", "c0", 1, False)])
    got = subprocess.run(["git", "-C", str(repo), "config", "--local", "--get", "core.autocrlf"],
                         capture_output=True, text=True).stdout.strip()
    assert got == "false", f"the fixture repo's own core.autocrlf is {got!r}, not 'false'"


def main() -> int:
    try:
        test_the_fixture_repo_pins_core_autocrlf_false()
    except Exception as e:  # noqa: BLE001
        print(f"  FAIL test_the_fixture_repo_pins_core_autocrlf_false: {e}")
        return 1
    print("  ok   test_the_fixture_repo_pins_core_autocrlf_false")
    return 0


if __name__ == "__main__":
    sys.exit(main())

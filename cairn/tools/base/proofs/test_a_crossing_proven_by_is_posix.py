"""Proof for ticket 703d3ec3619c — a crossing's proven_by is a posix path, written and read.

Measured 2026-11-13 by the orchestrator's Linux run: ``cairn test --hollow`` refused 15 Windows
tickets because their PROVEME crossings stored backslash proof paths, which
``proven_by_since_buildme`` handed raw to hollow, proof_coverage and codemother.

    python3 cairn/tools/base/proofs/test_a_crossing_proven_by_is_posix.py
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

PROVES = {"703d3ec3619c": {
    "1": "test_a_backslash_record_reads_back_posix",
    "2": "test_the_crossing_writes_forward_slashes",
}}


def test_a_backslash_record_reads_back_posix():
    from cairn.tools.base import crossings
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "cairn"
        (repo / "cairn" / "devices" / "alpha").mkdir(parents=True)
        commons = Path(tmp) / "CairnCommons"
        commons.mkdir()
        w = {"repo": repo, "commons": commons, "instance": Path(tmp) / ".cairn"}
        absolute = str(repo / "cairn" / "devices" / "alpha" / "proofs" / "b.py").replace("/", "\\")
        entries = [{"to": "BUILDME", "from": None, "at": "2026-01-01T10:00:00", "ticket": "t1",
                    "direction": "forward"},
                   {"to": "PROVEME", "from": None, "at": "2026-01-01T11:00:00", "ticket": "t1",
                    "direction": "forward",
                    "proven_by": ["cairn\\devices\\alpha\\proofs\\a.py", absolute]}]
        j = repo / "cairn" / "devices" / "alpha" / "history.json"
        j.write_text(json.dumps(entries), encoding="utf-8")
        got = crossings.proven_by_since_buildme("t1", roots=w)
        assert got == ["cairn/devices/alpha/proofs/a.py", "cairn/devices/alpha/proofs/b.py"], got


def test_the_crossing_writes_forward_slashes():
    from cairn.tools.base import cross
    out = cross.posix_proofs(["cairn\\devices\\sudo_relay\\proofs\\t.py", "a/b.py"])
    assert out == ["cairn/devices/sudo_relay/proofs/t.py", "a/b.py"], out
    import inspect
    src = inspect.getsource(cross.cross)
    assert "posix_proofs(proven_by)" in src, "cross() no longer writes proven_by through posix_proofs"


if __name__ == "__main__":
    import sys
    bad = 0
    for name in PROVES["703d3ec3619c"].values():
        try:
            globals()[name]()
            print("  PASS ", name)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print("  FAIL ", name, repr(e))
    sys.exit(1 if bad else 0)

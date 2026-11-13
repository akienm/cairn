"""Proof — feedback.producers() names every component with forward slashes on every box.

Measured 2026-11-13 on Windows: producers() returned 'cairn\\tools\\widget' for the fixture
component, so a route declared at the charter's address ('cairn/tools/widget') never matched
the producer it was declared for. A component address in this system is one spelling, the
slash one, and the producer list is read against charters that write it that way.

Tooth: a fixture root with one component whose module calls a finding constructor yields
exactly ['cairn/tools/widget'], and no entry carries a backslash.

    python3 cairn/tools/feedback/proofs/test_producers_name_components_with_forward_slashes.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"f68bd50f2902": {"1": "test_producers_name_components_with_forward_slashes"}}


def test_producers_name_components_with_forward_slashes():
    from cairn.tools.feedback import feedback
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "cairn" / "tools" / "widget"
        d.mkdir(parents=True)
        (d / feedback.CHARTER).write_text(json.dumps(
            {"component": "widget", "role": "charter", "what": "x", "why": "y"}), encoding="utf-8")
        (d / "widget.py").write_text("from x import gate\ngate.proved(a=1)\n", encoding="utf-8")
        got = feedback.producers(tmp)
    assert got == ["cairn/tools/widget"], got
    assert not any("\\" in p for p in got), got


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

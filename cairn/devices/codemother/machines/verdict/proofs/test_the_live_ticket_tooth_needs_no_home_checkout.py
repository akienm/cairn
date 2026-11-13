"""Proof — test_falsifier_verdict's live-ticket tooth finds the commons beside the repo, never through ~/dev/src/cairn.

Measured 2026-11-13: that tooth derived the repo root as Path(__file__).parents[5], which is
the inner package dir (repo/cairn), not the repo root (parents[6]). Nothing sits beside it,
so the tooth fell back to ~/dev/src/cairn: absent on Windows (red there), present on Linux
(green only by that fallback).

One tooth, one clause: run the live-ticket tooth in a child process whose HOME and
USERPROFILE name an empty scratch dir, so the fallback has nothing to reach. It must pass.

    python3 cairn/devices/codemother/machines/verdict/proofs/test_the_live_ticket_tooth_needs_no_home_checkout.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"b2454092e6e2": {"1": "test_the_live_ticket_tooth_passes_with_no_home_checkout"}}

_CHILD = (
    "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r)\n"
    "import test_falsifier_verdict as m\n"
    "m.test_the_real_ticket_that_built_this_form_yields_its_clauses(None, None)\n"
)


def test_the_live_ticket_tooth_passes_with_no_home_checkout():
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("verdict-no-home-checkout-")
    assert not (home / "dev" / "src" / "cairn").exists()
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PYTHONUTF8="1")
    code = _CHILD % (str(ROOT), str(Path(__file__).resolve().parent))
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0, (r.returncode, r.stdout[-600:], r.stderr[-900:])


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

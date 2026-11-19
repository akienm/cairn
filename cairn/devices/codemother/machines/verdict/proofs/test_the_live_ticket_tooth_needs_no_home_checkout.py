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

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"b2454092e6e2": {"1": "test_the_live_ticket_tooth_passes_with_no_home_checkout"},
          "8e0cfb77827c": {"1": "test_every_scratch_home_child_here_gets_its_env_from_home_env",
                     "2": "test_the_child_env_holds_its_home_in_the_scratch_on_every_platform"}}

_CHILD = (
    "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r)\n"
    "import test_falsifier_verdict as m\n"
    "m.test_the_real_ticket_that_built_this_form_yields_its_clauses(None, None)\n"
)


def _env(home) -> dict:
    from cairn.tools.scratch.scratch import home_env  # HOME + USERPROFILE, CAIRN_BUS_* scrubbed (ticket 8e0cfb77827c)
    return home_env(home, PYTHONUTF8="1")


def test_the_live_ticket_tooth_passes_with_no_home_checkout():
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("verdict-no-home-checkout-")
    assert not (home / "dev" / "src" / "cairn").exists()
    env = _env(home)
    code = _CHILD % (str(ROOT), str(Path(__file__).resolve().parent))
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0, (r.returncode, r.stdout[-600:], r.stderr[-900:])


def test_every_scratch_home_child_here_gets_its_env_from_home_env():
    """8e0cfb77827c clause 1: no proof of this component builds a scratch-HOME env by hand."""
    from pathlib import Path
    from cairn.tools.scratch.scratch import scratch_home_bypass
    here = Path(__file__).resolve().parents[1]
    got = scratch_home_bypass(here)
    assert got == [], f"scratch-HOME env built by hand, around home_env: {got}"


def test_the_child_env_holds_its_home_in_the_scratch_on_every_platform():
    """8e0cfb77827c clause 2: the child's HOME and USERPROFILE (Path.home() on Windows) are the scratch,
    and a bus address the session carries does not ride into it, so a Windows run writes nothing
    under the live ~/.cairn. A hand-built env keeps the bus address, so this reds on Linux too."""
    import os
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("cairn-verdict-clause2-home-")
    planted = "CAIRN_BUS_HOME"
    before = os.environ.get(planted)
    os.environ[planted] = "fixture-live-bus.invalid:7419"
    try:
        envs = {"_env": _env(home)}
    finally:
        if before is None:
            os.environ.pop(planted, None)
        else:
            os.environ[planted] = before
    bad = {name: dict(HOME=e.get("HOME"), USERPROFILE=e.get("USERPROFILE"),
                       leaked=sorted(k for k in e if k.startswith("CAIRN_BUS_")))
           for name, e in envs.items()
           if e.get("HOME") != str(home) or e.get("USERPROFILE") != str(home)
           or any(k.startswith("CAIRN_BUS_") for k in e)}
    assert not bad, dict(scratch=str(home), bad=bad)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

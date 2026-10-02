"""Proof: the aider venv's verify() measures that a stated package IMPORTS, not that it is on disk.

Measured 2026-10-01 (ticket a1a2156a2a17): the venv was rebuilt on Python 3.14, which has no
stdlib audioop (removed in 3.13, PEP 594), so pydub 0.25.1 — which imports it unconditionally —
raised at import and test_driver.py went red 21 teeth deep. verify() read green over it,
because find_spec answers "is there a file", and the file was there.

Teeth a hollow build could not pass:

  1. A PRESENT-BUT-BROKEN PACKAGE REDS VERIFY. A scratch venv holds a package whose import
     raises; verify(), pointed at it, returns ok False and names that package under
     unimportable_required with the exception it raised. find_spec alone passes it.
  2. THE STATED SET CARRIES THE BACKPORT. Some entry of packages() — the one list build()
     installs — is audioop-lts under a python_version >= '3.13' marker.

The sealed proof never reads instance-space: tooth 1 builds its own venv under scratch_dir
and points venv.VENV at it for the call. The live venv's verify is the host-seam half.

    python3 cairn/devices/aider_shim/proofs/test_venv_imports.py   # exit 0 = green
"""

from __future__ import annotations

import importlib
import subprocess
import sys
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

PROVES = {
    "a1a2156a2a17": {
        "1": "test_a_present_but_broken_package_reds_verify",
        "2": "test_the_stated_set_carries_the_audioop_backport",
    },
}

_FIXTURE = "cairn_fixture_raises"
_RAISES = "fixture: present but broken"


def _venv():
    return importlib.import_module("cairn.devices.aider_shim.venv")


def test_a_present_but_broken_package_reds_verify():
    v = _venv()
    root = scratch_dir("aider_venv_fixture_") / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(root)], check=True)
    site = next(root.glob("lib/python*/site-packages"))
    (site / _FIXTURE).mkdir()
    (site / _FIXTURE / "__init__.py").write_text(f"raise ImportError({_RAISES!r})\n")
    saved = v.VENV
    v.VENV = root
    try:
        out = v.verify(import_names=[_FIXTURE])
    finally:
        v.VENV = saved
    assert out.get("ok") is False, out
    broken = out.get("unimportable_required") or {}
    assert _FIXTURE in broken, f"verify must name the package that fails to import: {out}"
    assert _RAISES in broken[_FIXTURE], broken
    assert _FIXTURE not in (out.get("missing_required") or []), \
        "the package IS on disk — find_spec finds it; only the import fails"


def test_the_stated_set_carries_the_audioop_backport():
    pkgs = _venv().packages()
    hits = [p for p in pkgs if p.startswith("audioop-lts") and "python_version >= '3.13'" in p]
    assert len(hits) == 1, f"build() must install audioop-lts for Python 3.13+: {pkgs}"


def _main() -> int:
    teeth = [test_a_present_but_broken_package_reds_verify,
             test_the_stated_set_carries_the_audioop_backport]
    failed = []
    for tooth in teeth:
        try:
            tooth()
        except Exception as e:  # noqa: BLE001 — the reason is the record
            failed.append(tooth.__name__)
            print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {str(e)[:400]}")
            traceback.print_exc(limit=2)
            continue
        print(f"  PASS  {tooth.__name__}")
    if failed:
        print(f"red — {len(failed)} of {len(teeth)} teeth: {', '.join(failed)}")
        return 1
    print(f"green — {len(teeth)} teeth: verify names a stated package that is present but fails to "
          "import, and the set build() installs carries audioop-lts for Python 3.13+")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

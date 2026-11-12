"""Proof for ticket 033f607c5316 — the orient floor and census emit forward-slash paths.

Measured 2026-11-12 on akiendell: call_sites("write_trace") returned
``cairn\\machines\\learning_block\\engine.py``; a ref written with backslashes does not compare
equal to the same ref on another box. Red first: written before the build.

Teeth bind what the build changed at call time, never at import.

    python <this file>
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "033f607c5316": {
        "1": "no_emitted_path_contains_a_backslash",
        "2": "the_emitted_paths_still_resolve",
    },
}


def _orient():
    from cairn.tools.orient import orient
    return orient


def _sites() -> list[dict]:
    return _orient().call_sites("write_trace")["measured"]["sites"]


def _components() -> list[dict]:
    return _orient().device_census()["measured"]["components"]


def no_emitted_path_contains_a_backslash():
    sites, comps = _sites(), _components()
    assert sites and comps, f"nothing to measure: {len(sites)} sites, {len(comps)} components"
    bad = [s["file"] for s in sites if "\\" in s["file"]]
    bad += [c["dir"] for c in comps if "\\" in c.get("dir", "")]
    assert not bad, f"{len(bad)} emitted path(s) carry a backslash, e.g. {bad[:3]}"


def the_emitted_paths_still_resolve():
    for s in _sites():
        assert (REPO / s["file"]).is_file(), f"call-site file does not resolve from the repo root: {s['file']}"
    for c in _components():
        assert (REPO / "cairn" / c["dir"]).is_dir(), f"component dir does not resolve under cairn/: {c['dir']}"


TEETH = [no_emitted_path_contains_a_backslash, the_emitted_paths_still_resolve]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:500]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

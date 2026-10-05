"""The build-time sole-path seat spares the bus client's socket, and only that file (ticket f5a344e6c629).

sole_path_holds is the inference sole-path rule at the other moment: every component, every
inspection. Akien's answer to CairnCommons/questions/open-10941757e6b7.json admits
cairn/tools/bus_client/remote.py, whose socket opens only the local AF_UNIX bus socket. At this
seat the graph is rooted at comp_dir.parent, so a tool's file reads as bus_client/<file>.

Two teeth: the real bus_client row is clean, and a seeded bus_client with a second dialer beside
remote.py reds for that file alone. The inspector is imported inside each tooth, so a reverted
inspector.py reds a tooth instead of breaking the file.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"f5a344e6c629": {
    "4": "test_the_real_bus_client_row_is_clean",
    "5": "test_a_second_bus_client_dialer_is_caught",
}}


def test_the_real_bus_client_row_is_clean():
    from cairn.machines.build_inspector import inspector
    found = inspector.sole_path_holds({"component": "bus_client"},
                                      _REPO_ROOT / "cairn" / "tools" / "bus_client")
    assert found == [], [f.get("about") for f in found]


def test_a_second_bus_client_dialer_is_caught():
    from cairn.machines.build_inspector import inspector
    root = scratch_dir("cairn-sole-path-bus-client-")
    for i in range(25):
        (root / "filler" / f"m{i}.py").parent.mkdir(parents=True, exist_ok=True)
        (root / "filler" / f"m{i}.py").write_text("import json\n")
    comp = root / "bus_client"
    comp.mkdir()
    (comp / "remote.py").write_text("import socket\n")
    (comp / "other.py").write_text("import socket\n")
    found = inspector.sole_path_holds({"component": "bus_client"}, comp)
    abouts = [f.get("about", "") for f in found]
    assert len(found) == 1 and "other.py" in abouts[0], abouts


def main() -> int:
    fails = 0
    for name in PROVES["f5a344e6c629"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

"""Proof for ticket 0f7a8cada1ca — address names a device's existing instances and the next free one.

The shim's start --new (ticket d13859e2ae46) must read instance folders through address, never glob
devices/<device>/ itself. address had path builders and no lister. Every tooth runs over a SCRATCH roots dict,
imports address inside its body (so a reverted address.py reds the teeth and not this file's import), creates
nothing outside the scratch dir and starts no process.

    python <this file>
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "0f7a8cada1ca": {
        "1": "instances_lists_the_numeric_folders_and_creates_nothing",
        "2": "next_free_instance_is_the_lowest_unused_number",
    },
}


def _world(td: str, device: str, names: list[str]) -> dict:
    root = Path(td) / "inst"
    for n in names:
        (root / "devices" / device / n).mkdir(parents=True)
    root.mkdir(parents=True, exist_ok=True)
    return {"repo": Path(td) / "repo", "commons": Path(td) / "commons", "instance": root}


def instances_lists_the_numeric_folders_and_creates_nothing() -> None:
    from cairn.tools.base import address
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        roots = _world(td, "cc", ["0", "2", "10", "scratch", "01", "-1"])
        (Path(td) / "inst" / "devices" / "cc" / "last_known.json").write_text("{}", encoding="utf-8", newline="\n")
        assert address.instances("cc", roots) == [0, 2, 10], address.instances("cc", roots)
        before = sorted(p.name for p in (Path(td) / "inst" / "devices").iterdir())
        assert address.instances("nobody", roots) == [], "a device with no folder has no instances"
        after = sorted(p.name for p in (Path(td) / "inst" / "devices").iterdir())
        assert before == after == ["cc"], f"reading created a folder: {before} -> {after}"


def next_free_instance_is_the_lowest_unused_number() -> None:
    from cairn.tools.base import address
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        roots = _world(td, "cc", ["0", "2"])
        assert address.next_free_instance("cc", roots) == 1, "[0, 2] gives 1"
        assert address.next_free_instance("nobody", roots) == 0, "no instances gives 0"
        (Path(td) / "inst" / "devices" / "cc" / "1").mkdir()
        assert address.next_free_instance("cc", roots) == 3, "[0, 1, 2] gives 3"


TEETH = [instances_lists_the_numeric_folders_and_creates_nothing, next_free_instance_is_the_lowest_unused_number]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

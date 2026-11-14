"""Proof for ticket d13859e2ae46 — the shim names the instance it would take, and refuses a name already live.

Akien, outline 5.3.5.2.2: "the launcher has to ask the shim to create the instance, and so it's the shim's job
to say ... we have a cc_0 instance, so I'll launch it with cc_1". The launcher asks, the shim names, the launcher
launches. The shim names through shim.name_instance, a MODULE-LEVEL function: no shim is constructed and nothing
is started. Refusing an explicit live name is CC's reading of Q#93, not his words.

Every tooth runs over a SCRATCH roots dict, imports the shim inside its body (so a reverted shim.py reds the
teeth and not this file's import), creates nothing outside the scratch dir, and starts no process.

    python <this file>
"""

from __future__ import annotations

import inspect
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "d13859e2ae46": {
        "1": "name_instance_answers_the_lowest_free_number_with_no_shim_running",
        "2": "name_instance_refuses_a_live_name_and_allows_a_free_one",
    },
}


def _world(td: str, device: str, names: list[str]) -> dict:
    root = Path(td) / "inst"
    root.mkdir(parents=True, exist_ok=True)
    for n in names:
        (root / "devices" / device / n).mkdir(parents=True)
    return {"repo": Path(td) / "repo", "commons": Path(td) / "commons", "instance": root}


def name_instance_answers_the_lowest_free_number_with_no_shim_running() -> None:
    from cairn.tools.base import shim
    assert inspect.isfunction(shim.name_instance), "name_instance must be a plain module-level function, not a method"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        assert shim.name_instance("cc", roots=_world(td, "cc", ["0", "2"])) == 1, "[0, 2] gives 1"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        roots = _world(td, "cc", [])
        assert shim.name_instance("cc", roots=roots) == 0, "no instances gives 0"
        assert not (Path(td) / "inst" / "devices" / "cc").exists(), "asking for a name created a folder"


def name_instance_refuses_a_live_name_and_allows_a_free_one() -> None:
    from cairn.tools.base import shim
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        roots = _world(td, "cc", ["0", "1"])
        assert shim.name_instance("cc", requested=2, roots=roots) == 2, "a free number is returned as asked"
        try:
            shim.name_instance("cc", requested=1, roots=roots)
        except shim.InstanceTaken as exc:
            assert "cc" in str(exc) and "1" in str(exc), f"the refusal must name the device and number: {exc}"
        else:
            raise AssertionError("a name already live was not refused: two would share it")


TEETH = [name_instance_answers_the_lowest_free_number_with_no_shim_running,
         name_instance_refuses_a_live_name_and_allows_a_free_one]


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

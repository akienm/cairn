"""Proof for ticket eb1b46bed3d8 — the superclaude floor proof's uncreatable-path fixture is absent on every host.

Measured 2026-11-13 on Windows: bin/proofs/test_superclaude_is_never_refused_by_the_floor.py named UNCREATABLE = /proc/cairn-no-such-dir/venv; on
Windows /proc is C:\\proc, an earlier run left C:\\proc\\cairn-no-such-dir there, and the
non-vacuity guard reds with 'exists'. A path beneath a regular file refuses a mkdir on every host.

Both teeth red on Linux against the unedited file (the /proc literal is there; its parent is not a
file). Neither spawns a process.

    python <this file>
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

TARGET = REPO / "bin/proofs/test_superclaude_is_never_refused_by_the_floor.py"

PROVES = {
    "eb1b46bed3d8": {
        "1": "the_target_names_no_proc_path",
        "2": "uncreatable_is_beneath_a_regular_file_and_refuses_makedirs",
    },
}


def the_target_names_no_proc_path():
    tree = ast.parse(TARGET.read_text(encoding="utf-8"), filename=str(TARGET))
    bad = [f"line {n.lineno}: {n.value!r}" for n in ast.walk(tree)
           if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("/proc/")]
    assert not bad, f"a /proc path stands as a fixture: {bad}"


def uncreatable_is_beneath_a_regular_file_and_refuses_makedirs():
    spec = importlib.util.spec_from_file_location("_target_proof", TARGET)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    path = Path(mod.UNCREATABLE)
    assert not path.exists(), f"{path} exists"
    assert path.parent.is_file(), f"the parent of {path} is not a regular file"
    try:
        os.makedirs(path)
    except OSError:
        return
    raise AssertionError(f"os.makedirs made {path}")


TEETH = [the_target_names_no_proc_path, uncreatable_is_beneath_a_regular_file_and_refuses_makedirs]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {type(e).__name__}: {e}  [{t.__name__}]")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

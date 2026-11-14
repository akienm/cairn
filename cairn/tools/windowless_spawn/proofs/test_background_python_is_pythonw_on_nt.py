"""Proof for ticket 96cf285e299b — a long-lived background child on Windows starts through pythonw.

The code shipped under 0156856b1fae (6ea474469) as background_pythonw(); this ticket is proofs-only. Its
exact-path and fallback branches had no tooth. A scratch dir holds a fake python.exe and pythonw.exe; the
live venv is never touched and nothing is spawned. os_name is passed in, never patched.

    python <this file>
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.windowless_spawn.windowless_spawn import background_pythonw, background_python  # noqa: E402

PROVES = {
    "96cf285e299b": {
        "1": "nt_with_pythonw_beside_returns_the_pythonw_path",
        "2": "no_pythonw_beside_and_posix_return_the_executable",
    },
}


def _scratch(d: str, with_pythonw: bool) -> Path:
    py = Path(d) / "python.exe"
    py.write_text("")
    if with_pythonw:
        (Path(d) / "pythonw.exe").write_text("")
    return py


def nt_with_pythonw_beside_returns_the_pythonw_path() -> None:
    with tempfile.TemporaryDirectory() as d:
        py = _scratch(d, with_pythonw=True)
        got = background_pythonw("nt", executable=str(py))
        assert Path(got) == Path(d) / "pythonw.exe", f"expected the pythonw beside the interpreter, got {got!r}"
        assert Path(got) != py, "returned the python.exe path"
        # background_python keeps python.exe: a reader of the child's output needs its stdout, which pythonw lacks
        assert background_python("nt", executable=str(py)) == str(py), "background_python no longer returns the executable"


def no_pythonw_beside_and_posix_return_the_executable() -> None:
    with tempfile.TemporaryDirectory() as d:
        py = _scratch(d, with_pythonw=False)
        assert background_pythonw("nt", executable=str(py)) == str(py), "no pythonw beside it must fall back to the executable"
    with tempfile.TemporaryDirectory() as d:
        py = _scratch(d, with_pythonw=True)
        assert background_pythonw("posix", executable=str(py)) == str(py), "posix must return the executable even with a pythonw beside it"


TEETH = [nt_with_pythonw_beside_returns_the_pythonw_path, no_pythonw_beside_and_posix_return_the_executable]


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

"""Proof for ticket 96cf285e299b — a background child on Windows starts through pythonw.

Measured 2026-11-13 on Windows: tooth 2 of test_a_cairn_spawn_opens_no_console_window.py reds
because the venv launcher's base interpreter allocates a console host (conhost.exe) when the
launcher was started with no console. The same spawn through the pythonw.exe beside the venv
python leaves no console host in the tree. That tooth (0156856b1fae) is the live instrument;
these teeth pin the choice of interpreter without spawning anything.

    python <this file>
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"96cf285e299b": {
    "1": "test_nt_returns_the_pythonw_beside_the_executable",
    "2": "test_without_a_pythonw_or_off_nt_the_executable_is_unchanged",
}}


def _ws():
    from cairn.tools.windowless_spawn import windowless_spawn as ws
    return ws


def test_nt_returns_the_pythonw_beside_the_executable():
    ws = _ws()
    with tempfile.TemporaryDirectory() as tmp:
        py, pyw = Path(tmp) / "python.exe", Path(tmp) / "pythonw.exe"
        py.write_text("", encoding="utf-8")
        pyw.write_text("", encoding="utf-8")
        got = ws.background_python("nt", executable=str(py))
        assert Path(got) == pyw, got


def test_without_a_pythonw_or_off_nt_the_executable_is_unchanged():
    ws = _ws()
    with tempfile.TemporaryDirectory() as tmp:
        py = Path(tmp) / "python.exe"
        py.write_text("", encoding="utf-8")
        assert ws.background_python("nt", executable=str(py)) == str(py)
        (Path(tmp) / "pythonw.exe").write_text("", encoding="utf-8")
        assert ws.background_python("posix", executable="/usr/bin/python3") == "/usr/bin/python3"
        assert ws.background_python("posix", executable=str(py)) == str(py)


if __name__ == "__main__":
    bad = 0
    for name in PROVES["96cf285e299b"].values():
        try:
            globals()[name]()
            print("  PASS ", name)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print("  FAIL ", name, repr(e))
    sys.exit(1 if bad else 0)

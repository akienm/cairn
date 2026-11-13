"""Proof for ticket 5a37dd56fa45 — one tools/base file-lock helper stands for fcntl.flock.

Measured 2026-11-13 on Windows: 13 proofs raised ModuleNotFoundError: No module named 'fcntl',
through cairn/devices/inference_domain/host.py and cairn/devices/cairn/metrics.py, which import
fcntl at module top. Each tooth binds what the build ADDED at call time, never at import, and
each reds on Linux against the unedited modules (tooth 1 hides fcntl; tooth 2 reads the source;
tooth 3 needs the helper to exist).

    python <this file>
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "5a37dd56fa45": {
        "1": "host_and_metrics_import_with_fcntl_hidden",
        "2": "neither_module_imports_fcntl_at_top_level",
        "3": "a_contended_nonblocking_take_raises_and_frees_on_unlock",
    },
}

MODULES = ["cairn/devices/inference_domain/host.py", "cairn/devices/cairn/metrics.py"]


def host_and_metrics_import_with_fcntl_hidden():
    code = ("import sys; sys.modules['fcntl'] = None; "
            "import cairn.devices.inference_domain.host, cairn.devices.cairn.metrics")
    env = dict(os.environ, PYTHONPATH=str(REPO))
    got = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env,
                         creationflags=0x08000000 if os.name == "nt" else 0)
    assert got.returncode == 0, f"import failed with fcntl hidden: {got.stderr.strip()[-400:]}"


def neither_module_imports_fcntl_at_top_level():
    bad = []
    for rel in MODULES:
        tree = ast.parse((REPO / rel).read_text(encoding="utf-8"), filename=rel)
        for node in tree.body:
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            if any(n.split(".")[0] == "fcntl" for n in names):
                bad.append(f"{rel}:{node.lineno}")
    assert not bad, f"module-level import fcntl at {bad}"


def a_contended_nonblocking_take_raises_and_frees_on_unlock():
    from cairn.tools.base import flock
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "x.lock")
        a = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        b = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            flock.lock(a)
            try:
                flock.lock(b, block=False)
            except BlockingIOError:
                pass
            else:
                raise AssertionError("a second descriptor took the lock while the first held it")
            flock.unlock(a)
            flock.lock(b, block=False)
            flock.unlock(b)
        finally:
            os.close(a)
            os.close(b)


TEETH = [host_and_metrics_import_with_fcntl_hidden,
         neither_module_imports_fcntl_at_top_level,
         a_contended_nonblocking_take_raises_and_frees_on_unlock]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

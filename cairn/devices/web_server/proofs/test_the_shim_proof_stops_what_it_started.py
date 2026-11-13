"""Proof for ticket 3a38e2e1cfe0 — the web-server shim proof stops the listener tree it started.

Measured 2026-11-13 on Windows: test_web_server_shim.py ended its teardown in os.killpg, which
does not exist there, and swallowed the AttributeError; two listener.py processes outlived their
dead parent holding web_server.log inside the scratch dir, and every later proof's scratch sweep
failed on it (WinError 32).

Neither tooth spawns a process. Both red on Linux against the unedited shim proof: tooth 1 reads
its source, tooth 2 calls the ``_stop_tree`` the build adds, with ``os`` and ``subprocess`` swapped
for recorders so the nt branch is exercised on any host.

    python <this file>
"""

from __future__ import annotations

import ast
import importlib.util
import signal
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SHIM_PROOF = REPO / "cairn/devices/web_server/proofs/test_web_server_shim.py"

PROVES = {
    "3a38e2e1cfe0": {
        "1": "the_teardown_has_a_taskkill_branch_and_no_bare_killpg",
        "2": "stop_tree_runs_taskkill_tree_on_nt_and_killpg_on_posix",
    },
}


def the_teardown_has_a_taskkill_branch_and_no_bare_killpg():
    src = SHIM_PROOF.read_text(encoding="utf-8")
    tree = ast.parse(src)
    assert "taskkill" in src, "no taskkill tree-stop in the shim proof"
    bare = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef) or fn.name == "_stop_tree":
            continue
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "killpg"):
                bare.append(f"{fn.name}:{node.lineno}")
    assert not bare, f"os.killpg called outside _stop_tree: {bare}"


def stop_tree_runs_taskkill_tree_on_nt_and_killpg_on_posix():
    spec = importlib.util.spec_from_file_location("_ws_shim_proof", SHIM_PROOF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    stop = getattr(mod, "_stop_tree", None)
    assert stop is not None, "the shim proof has no _stop_tree"

    ran: list = []
    mod.subprocess = types.SimpleNamespace(
        run=lambda argv, **k: ran.append(list(argv)), DEVNULL=None, PIPE=None)
    mod.os = types.SimpleNamespace(name="nt")
    stop(4242)
    assert len(ran) == 1, f"nt: expected one taskkill run, got {ran}"
    argv = [str(a).lower() for a in ran[0]]
    assert argv[0].startswith("taskkill") and "/t" in argv and "/f" in argv and "4242" in argv, ran[0]

    killed: list = []
    ran.clear()
    mod.os = types.SimpleNamespace(name="posix", killpg=lambda pid, sig: killed.append((pid, sig)))
    stop(4242)
    assert killed == [(4242, signal.SIGTERM)] and not ran, (killed, ran)


TEETH = [the_teardown_has_a_taskkill_branch_and_no_bare_killpg,
         stop_tree_runs_taskkill_tree_on_nt_and_killpg_on_posix]


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

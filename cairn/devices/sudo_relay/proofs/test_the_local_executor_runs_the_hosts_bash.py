"""Proof for ticket c603e904432c — the sudo relay's local executor runs its command under the host's bash.

Measured 2026-11-12 on akiendell: a bare ``["bash", ...]`` argv resolves through CreateProcess to the WSL
launcher, so relay.local_executor ran in WSL (uname: Linux ...WSL2, backslashes eaten). The fix names the
host's bash once, in relay._bash.

    python3 cairn/devices/sudo_relay/proofs/test_the_local_executor_runs_the_hosts_bash.py
"""
from __future__ import annotations

import ast
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"c603e904432c": {
    "1": "test_the_local_executor_spawns_the_hosts_bash",
    "2": "test_no_bare_bash_list_stands_in_the_relay_outside_its_one_helper",
}}


def test_the_local_executor_spawns_the_hosts_bash():
    from cairn.devices.sudo_relay import relay
    seen = []
    real = relay._run
    relay._run = lambda argv, *, timeout: seen.append(list(argv)) or (0, "", "")
    try:
        relay.local_executor("echo hi")
    finally:
        relay._run = real
    want = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"
    assert seen and seen[0][0] == want, f"argv {seen}: first element is not {want!r}"
    assert seen[0][1:] == ["-c", "echo hi"], seen
    print(f"local_executor argv starts with {want}")


def test_no_bare_bash_list_stands_in_the_relay_outside_its_one_helper():
    src = (REPO / "cairn/devices/sudo_relay/relay.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    helper_lines = set()
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name == "_bash":
            helper_lines = set(range(fn.lineno, (fn.end_lineno or fn.lineno) + 1))
    bare = [n.lineno for n in ast.walk(tree)
            if isinstance(n, ast.List) and n.elts and isinstance(n.elts[0], ast.Constant)
            and n.elts[0].value == "bash" and n.lineno not in helper_lines]
    assert bare == [], f"bare 'bash' argv list(s) at relay.py line(s) {bare}"
    print("relay.py names no bare bash argv outside _bash")


def main() -> int:
    bad = 0
    for t in (test_the_local_executor_spawns_the_hosts_bash,
              test_no_bare_bash_list_stands_in_the_relay_outside_its_one_helper):
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            bad += 1
            print(f"  FAIL  {t.__name__}\n        {type(exc).__name__}: {str(exc)[:300]}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

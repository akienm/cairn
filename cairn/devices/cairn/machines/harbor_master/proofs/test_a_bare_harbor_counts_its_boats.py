"""PROOF — a bare harbor counts its boats (ticket f30daa73a599; outline 9.4.1.5).

Outline 9.4.1.5 COMMANDS: ``cairn codemother harbor_master`` -> "652 boats (570 open, 82 in
port)". Measured 2026-11-13: the bare command printed the base shim's
"device: harbor_master / class:  cairn/devices/harbor_master/", a path that no longer exists.
HarborMasterShim overrides ``_bare`` (the one bare hook, ticket 59f7456dd9f5) to answer the
fleet register's count.

  1. bare ``cairn codemother harbor_master`` exits 0 and prints exactly one line matching
     "N boats (x open, y in port)".
  2. N = x + y, and x and y equal the map's counts read from the same device at the same
     moment; the stale class path is not printed.

What a hollow build cannot pass (Law 8): a constant line passes the shape in clause 1 and
fails clause 2, which compares it with the live register's counts, and the live fleet is
never empty.

    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_a_bare_harbor_counts_its_boats.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"f30daa73a599": {
    "1": "test_the_bare_command_prints_one_count_line",
    "2": "test_the_count_is_the_registers_own",
}}

_LINE = re.compile(r"^(\d+) boats \((\d+) open, (\d+) in port\)$")


def test_the_bare_command_prints_one_count_line():
    from cairn.tools.base.script_argv import bash_script_argv
    r = subprocess.run([*bash_script_argv(_REPO_ROOT / "bin" / "cairn"), "codemother", "harbor_master"],
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, f"bare command exited {r.returncode}: {r.stderr[-400:]}"
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    assert len(lines) == 1 and _LINE.match(lines[0]), f"not one count line: {r.stdout!r}"


def test_the_count_is_the_registers_own():
    from cairn.devices.cairn.machines.harbor_master.shim import HarborMasterShim
    shim = HarborMasterShim()
    got = shim._resolve([])
    text = got.get("text") or ""
    assert got.get("exit") == 0, f"bare answer exited {got.get('exit')}: {text}"
    assert "class:" not in text and "cairn/devices/harbor_master" not in text, f"stale class path: {text!r}"
    m = _LINE.match(text.strip())
    assert m, f"not a count line: {text!r}"
    n, x, y = (int(g) for g in m.groups())
    c = shim.device()._fleet_map()["counts"]
    assert n == x + y, f"{n} boats is not {x} open + {y} in port"
    assert (x, y) == (c["open"], c["in_port"]), f"line says ({x}, {y}); the register says {c}"
    assert n > 0, "the live fleet read empty, so the count cannot tell a constant from a reading"


def main() -> int:
    fails = 0
    teeth = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in teeth:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            fails += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(teeth) - fails}/{len(teeth)} green")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

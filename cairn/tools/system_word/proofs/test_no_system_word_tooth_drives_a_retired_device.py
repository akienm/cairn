"""Proof for the harbor_master tooth retirement: no system_word tooth drives a device class-space no longer holds.

Measured 2026-11-13: test_system_word.py's test_the_real_harbor_master_takes_uppercase_show_map_open
runs `cairn harbor_master show map open` through the real bin/cairn. The harbor_master device left
class-space in 6ae83e7e1 (cairn-device-absorbs-foundational-infrastructure); outline 9.4.1 now
places it as a machine reached as `cairn codemother harbor_master`. On akienasus the tooth is red;
on Linux boxes it passes only because a hand-placed ~/.cairn/devices/harbor_master/0/bin/harbor_master
from Sep 2 still answers — the same class as the hand-placed cairn launcher.

  1. Every literal first word of a `_cairn(...)` call in test_system_word.py that does not swap in a
     fixture (CAIRN_CMD_DIR or CAIRN_INSTANCE_ROOT) names a class-space device under cairn/devices/
     or a command under bin/cmd/.
  2. Every value in test_system_word.py's PROVES names a function the file defines, and no PROVES
     key names the retired harbor_master tooth.

    bin/cairn test cairn/tools/system_word/proofs/test_no_system_word_tooth_drives_a_retired_device.py
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SUBJECT = REPO / "cairn" / "tools" / "system_word" / "proofs" / "test_system_word.py"
RETIRED = "test_the_real_harbor_master_takes_uppercase_show_map_open"
FIXTURE_ENV = {"CAIRN_CMD_DIR", "CAIRN_INSTANCE_ROOT"}

PROVES = {"a6068ba32ce7": {
    "1": "test_every_live_cairn_call_names_a_standing_device",
    "2": "test_proves_names_only_standing_teeth",
}}


def _tree() -> ast.Module:
    return ast.parse(SUBJECT.read_text(encoding="utf-8"))


def _resolves(word: str) -> bool:
    w = word.lower()
    return (REPO / "cairn" / "devices" / w).is_dir() or (REPO / "bin" / "cmd" / w).exists()


def test_every_live_cairn_call_names_a_standing_device():
    bad = []
    for node in ast.walk(_tree()):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "_cairn" and node.args):
            continue
        first = node.args[0]
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            continue
        if {k.arg for k in node.keywords} & FIXTURE_ENV:
            continue
        if not _resolves(first.value):
            bad.append(f"line {node.lineno}: {first.value!r}")
    assert not bad, f"live _cairn calls naming no class-space device or command: {bad}"


def test_proves_names_only_standing_teeth():
    tree = _tree()
    defs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    proves = None
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PROVES"
                                             for t in n.targets):
            proves = ast.literal_eval(n.value)
    assert proves, "test_system_word.py declares PROVES"
    dangling = [(t, k, v) for t, m in proves.items() for k, v in m.items() if v not in defs]
    retired = [(t, k) for t, m in proves.items() for k, v in m.items() if v == RETIRED]
    assert not dangling and not retired and RETIRED not in defs, (
        f"dangling={dangling} retired_keys={retired} retired_def_stands={RETIRED in defs}")


def main() -> int:
    failures = []
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}", flush=True)
            except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                print(f"  FAIL  {name}\n        {type(exc).__name__}: {str(exc)[:1200]}", flush=True)
                failures.append(name)
    print("\nGREEN" if not failures else f"\nRED — {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

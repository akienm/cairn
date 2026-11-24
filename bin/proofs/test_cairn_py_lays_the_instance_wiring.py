"""Proof for ticket 80a220a86873 — bin/cairn.py lays the instance wiring the bash launcher laid.

Measured 2026-11-20 on akiendell at main d4b139be4: with CAIRN_INSTANCE_ROOT at an empty directory,
`bash bin/cairn probescan` left 58 entries under it (bin/cairn's _floor_instance sources bootstrap.sh and
runs cairn_wire_instances) and `bin\\cairn.cmd probescan`, which runs bin/cairn.py, left 0.

  1. with an empty instance root, a verb run through bin/cairn.py leaves every class verb
     (cairn/devices/*/0/bin/*) present under <root>/<device>/0/bin, and superclaude under superclaude/0/bin.
  2. a hand-placed file where a class verb would link is left as it was and named on stderr.
  3. `help` wires nothing: an empty root is still empty after it.

    python3 bin/proofs/test_cairn_py_lays_the_instance_wiring.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROOF_TIMEOUT_S = 240

PROVES = {"80a220a86873": {
    "1": "tooth_1_an_empty_instance_root_is_wired_by_cairn_py",
    "2": "tooth_2_a_hand_placed_file_is_left_and_named",
    "3": "tooth_3_help_wires_nothing",
}}

_LAUNCHER = REPO / "bin" / "cairn.py"
_DEVICES = REPO / "cairn" / "devices"


def _class_verbs() -> list[tuple[str, str]]:
    out = []
    for bindir in sorted(_DEVICES.glob("*/0/bin")):
        for f in sorted(bindir.iterdir()):
            if f.is_file():
                out.append((bindir.parent.parent.name, f.name))
    return out


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, CAIRN_INSTANCE_ROOT=str(root))
    return subprocess.run([sys.executable, str(_LAUNCHER), *args], capture_output=True, text=True,
                          env=env, cwd=str(REPO), timeout=180)


def _entries(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() or p.is_symlink()]


def tooth_1_an_empty_instance_root_is_wired_by_cairn_py() -> None:
    verbs = _class_verbs()
    assert len(verbs) > 10, f"found only {len(verbs)} class verbs; the walk has nothing to measure"
    with tempfile.TemporaryDirectory(prefix="wire80-") as tmp:
        root = Path(tmp)
        _run(root, "probescan")
        missing = [f"{d}/0/bin/{n}" for d, n in verbs if not (root / d / "0" / "bin" / n).exists()]
        assert not missing, f"{len(missing)} of {len(verbs)} class verbs not laid, e.g. {missing[:4]}"
        sc = REPO / "cairn" / "devices" / "cc" / "superclaude.py"
        if sc.is_file():
            assert (root / "superclaude" / "0" / "bin" / "superclaude").exists(), "superclaude not laid"


def tooth_2_a_hand_placed_file_is_left_and_named() -> None:
    dev, name = _class_verbs()[0]
    with tempfile.TemporaryDirectory(prefix="wire80-") as tmp:
        root = Path(tmp)
        placed = root / dev / "0" / "bin" / name
        placed.parent.mkdir(parents=True)
        placed.write_text("hand placed\n", encoding="utf-8")
        r = _run(root, "probescan")
        assert placed.read_text(encoding="utf-8") == "hand placed\n", "the hand-placed file was overwritten"
        assert "hand-placed" in r.stderr and name in r.stderr, f"stderr does not name it: {r.stderr[:300]}"


def tooth_3_help_wires_nothing() -> None:
    with tempfile.TemporaryDirectory(prefix="wire80-") as tmp:
        root = Path(tmp)
        r = _run(root, "help")
        assert r.returncode == 0, f"help rc={r.returncode}: {r.stderr[:200]}"
        left = _entries(root)
        assert not left, f"help laid {len(left)} entries, e.g. {left[:3]}"


if __name__ == "__main__":
    fails = 0
    for fn in (tooth_1_an_empty_instance_root_is_wired_by_cairn_py,
               tooth_2_a_hand_placed_file_is_left_and_named, tooth_3_help_wires_nothing):
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print(f"  FAIL {fn.__name__}: {type(exc).__name__}: {exc}")
    sys.exit(1 if fails else 0)

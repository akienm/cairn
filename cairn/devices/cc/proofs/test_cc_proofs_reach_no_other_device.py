"""cc's proofs reach no other device (ticket f5c334da752a) — teeth a hollow build could not pass.

RULE 1: a device's public interface is the bus. Three cc proofs reached into the cairn device's
ground_loop.discovery to load cc's own probes and to ask whether cc is on the roster; this
proof holds that no cc file imports another device, and that the loader each of those three
proofs now carries still JUDGES (a PROBE-less file and a raising file are failures, a private
file is never read) and still loads every cc probe.
"""

from __future__ import annotations

import ast
import importlib
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "f5c334da752a": {
        "1": "test_no_cc_file_imports_another_device",
        "2": "test_each_loader_still_judges",
        "3": "test_each_loader_loads_ccs_probes",
    },
}

_DEVICE = _REPO_ROOT / "cairn" / "devices" / "cc"
LOADERS = (
    "cairn.devices.cc.proofs.test_cc_device",
    "cairn.devices.cc.proofs.test_memory_probe",
    "cairn.devices.cc.proofs.test_the_shim_delivers_mail",
)


def _crossings() -> list[str]:
    out = []
    for path in sorted(_DEVICE.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            else:
                continue
            for name in names:
                parts = name.split(".")
                if len(parts) >= 3 and parts[:2] == ["cairn", "devices"] and parts[2] != "cc":
                    out.append(f"{path.relative_to(_REPO_ROOT)}:{node.lineno} imports {name}")
    return out


def test_no_cc_file_imports_another_device():
    crossings = _crossings()
    assert not crossings, "cc reaches into another device: " + "; ".join(crossings)


def test_each_loader_still_judges():
    from cairn.tools.scratch.scratch import scratch_dir

    folder = Path(scratch_dir("testing-f5c334da752a-"))
    shutil.copy(_DEVICE / "probes" / "the_shim_delivers_mail.py", folder / "good.py")
    (folder / "none.py").write_text("X = 1\n")
    (folder / "boom.py").write_text("raise RuntimeError('boom')\n")
    (folder / "_private.py").write_text("raise RuntimeError('never read')\n")
    for name in LOADERS:
        mod = importlib.import_module(name)
        probes, failures = mod._load_own_probes(folder)
        assert len(probes) == 1, f"{name}: loaded {len(probes)} probes, want 1 (good.py)"
        got = sorted(Path(f["file"]).name for f in failures)
        assert got == ["boom.py", "none.py"], f"{name}: failures {failures}"


def test_each_loader_loads_ccs_probes():
    folder = _DEVICE / "probes"
    want = len([p for p in folder.glob("*.py") if not p.name.startswith("_")])
    for name in LOADERS:
        mod = importlib.import_module(name)
        probes, failures = mod._load_own_probes(folder)
        assert failures == [], f"{name}: {failures}"
        assert len(probes) == want, f"{name}: loaded {len(probes)} of {want} cc probes"


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {exc}")
    sys.exit(1 if failed else 0)

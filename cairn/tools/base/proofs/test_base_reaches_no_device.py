"""Base reaches no device (ticket d81baa1b5cb8) — teeth a hollow build could not pass.

RULE 1: every component talks to every other only through its public interface. On
2026-11-05 ``encapsulation_breaches`` listed ten rows under cairn/tools/base/; six sat in four
files with mechanical fixes. external.py imported the bus device for a type hint;
workflow_grammar.py reached system_word's module instead of its package; two proofs imported
device classes (the ground loop's discover(), BusDevice, HeartbeatPage) to check base's own
claims. This proof holds that those four files carry no breach, and that the two rewritten
teeth still JUDGE: base's own probe loader reds a broken probe file, and the device-class
tooth reads its classes' bases by AST, importing no device.

The three BusDevice.scratch rows (test_chat_pane, test_console_pane, test_probe_carry) are
out of scope and stand.

    PYTHONPATH=. python3 cairn/tools/base/proofs/test_base_reaches_no_device.py   # exit 0 = green
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

PROVES = {
    "d81baa1b5cb8": {
        "1": "test_the_four_files_carry_no_breach",
        "2": "test_the_probe_loader_reds_a_broken_probe",
        "3": "test_the_class_tooth_reads_bases_by_ast",
    },
}

_BASE = _ROOT / "cairn" / "tools" / "base"
_FOUR = (
    "cairn/tools/base/external.py",
    "cairn/tools/base/workflow_grammar.py",
    "cairn/tools/base/proofs/test_deviceness.py",
    "cairn/tools/base/proofs/test_device_logs_unwired.py",
)


def _rel(f: str) -> str:
    p = Path(f)
    if p.is_absolute():
        try:
            p = p.relative_to(_ROOT)
        except ValueError:
            pass
    return p.as_posix()


def _load(name: str):
    """A sibling proof module, loaded at call time: a build without it reds a tooth."""
    path = _BASE / "proofs" / name
    spec = importlib.util.spec_from_file_location("_d81b_" + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_four_files_carry_no_breach():
    from cairn.machines.build_inspector.inspector import encapsulation_breaches

    rows = [r for r in encapsulation_breaches(str(_ROOT)) if _rel(r.get("file", "")) in _FOUR]
    assert not rows, "base still reaches off an interface: " + "; ".join(
        f"{_rel(r['file'])}:{r.get('line')} -> {r.get('module')} ({r.get('reason')})" for r in rows)


def test_the_probe_loader_reds_a_broken_probe():
    from cairn.tools.scratch.scratch import scratch_dir

    mod = _load("test_deviceness.py")
    loader = getattr(mod, "_load_own_probes", None)
    assert callable(loader), "test_deviceness.py has no _load_own_probes"
    folder = Path(scratch_dir("testing-d81baa1b5cb8-"))
    (folder / "raises.py").write_text('raise RuntimeError("x")\n', encoding="utf-8")
    (folder / "noprobe.py").write_text("X = 1\n", encoding="utf-8")
    probes, failures = loader(folder)
    assert probes == [] and len(failures) == 2, (
        f"the loader must refuse both broken files; probes={probes} failures={failures}")
    real, real_failures = loader(_BASE / "probes")
    assert not real_failures and any("CLAIM device-hood" in p.why for p in real), (
        f"base's own probes must load and carry the device-hood probe: {real_failures}")


def test_the_class_tooth_reads_bases_by_ast():
    path = _BASE / "proofs" / "test_device_logs_unwired.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    reaches = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        elif isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        else:
            continue
        reaches += [f"{node.lineno}:{n}" for n in names if n.startswith("cairn.devices.")]
    assert not reaches, f"test_device_logs_unwired.py imports a device: {reaches}"
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name == "test_real_device_classes_name_their_own_component"), None)
    assert fn is not None, "the device-class tooth is gone"
    src = ast.get_source_segment(path.read_text(encoding="utf-8"), fn) or ""
    assert "ast.parse" in src and "BaseDevice" in src, (
        "the device-class tooth must read each class's bases by AST")


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

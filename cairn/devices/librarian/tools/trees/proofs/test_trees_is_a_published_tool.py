"""Proof for ticket 883abe55d04c — the librarian's graph-tree store is a client tool the librarian
publishes, and no tenant reaches into the librarian's insides to deposit or walk.

RULE 1 (Akien, 2026-10-01): every component talks to every other only through its public
interface; a device's is the bus plus any client tool it publishes. The graph trees ship vectors
on every walk, too heavy for a bus round trip per row, so the librarian publishes its store the
way db_domain publishes its client (ticket 4cbf6e28126e). The shared node and embedding tables
stay the librarian's; each tenant's leaf table stays the tenant's (Law 6). Measured before the
build: 13 encapsulation rows landed on cairn.devices.librarian.trees and 3 on
cairn.devices.librarian.loop (each for RESOLUTION_FLOOR).

One tooth per numbered falsifier clause, over the LIVE repo (invariants, never snapshots):

  1. NOTHING REACHES INTO THE LIBRARIAN FOR ITS TREES. No encapsulation_breaches row names
     cairn.devices.librarian.trees or cairn.devices.librarian.loop.
  2. THE OLD ADDRESS IS GONE. No .py file names the old module, cairn/devices/librarian/trees.py
     does not exist, and the tool holds no device class.
  3. THE TOOL IS PUBLISHED. Its charter declares published_by_device and exactly its one module,
     it imports no device code but db_domain's client, it exposes the store's surface, the
     librarian's loop reads the tool's floor, and the device class stands in the device.

    python3 cairn/devices/librarian/tools/trees/proofs/test_trees_is_a_published_tool.py   # exit 0 = green
"""
import ast
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class _Late:
    """The build's names resolve AT CALL TIME, so `cairn test --hollow` taking the tool away
    reads as red teeth rather than an import that never ran."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.machines.build_inspector.inspector")

PROVES = {"883abe55d04c": {"1": "nothing_reaches_into_the_librarian_for_its_trees",
                           "2": "the_old_address_is_gone",
                           "3": "the_tool_is_published"}}

OLD = "cairn.devices.librarian.trees"
OLD_LOOP = "cairn.devices.librarian.loop"
TOOL = "cairn.devices.librarian.tools.trees.trees"
TOOL_DIR = _REPO_ROOT / "cairn" / "devices" / "librarian" / "tools" / "trees"
ALLOWED_DEVICE_IMPORT = "cairn.devices.db_domain.tools.client"
SURFACE = ("deposit", "nearest", "neighbors", "scratch_leaf")
VOCABULARY = ("NODES", "RESOLUTION_FLOOR")
_OLD_RE = re.compile(re.escape(OLD) + r"(?!\w)"
                     r"|from\s+cairn\.devices\.librarian\s+import\s+[^\n]*\btrees\b")

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def nothing_reaches_into_the_librarian_for_its_trees():
    rows = [b for b in _inspector.encapsulation_breaches(str(_REPO_ROOT))
            if b["module"] in (OLD, OLD_LOOP)]
    assert not rows, f"{len(rows)} reach(es) into the librarian for its trees: " + \
        "; ".join(f"{b['file']}:{b['line']} {b['module']}" for b in rows[:8])


def _code_files():
    for p in _REPO_ROOT.rglob("*.py"):
        if (p != Path(__file__).resolve() and "__pycache__" not in p.parts
                and ".git" not in p.parts):
            yield p


def the_old_address_is_gone():
    naming = []
    for p in _code_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if _OLD_RE.search(text):
            naming.append(str(p.relative_to(_REPO_ROOT)))
    assert not naming, f"{len(naming)} file(s) still name the librarian's old trees module: " \
        f"{sorted(naming)[:8]}"
    assert not (_REPO_ROOT / "cairn/devices/librarian/trees.py").exists(), \
        "cairn/devices/librarian/trees.py still stands"
    src = (TOOL_DIR / "trees.py").read_text(encoding="utf-8")
    classes = [n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ClassDef)]
    assert "LibrarianDevice" not in classes, "the published tool still holds the device class"


def the_tool_is_published():
    charter = json.loads((TOOL_DIR / ("intention+" + "why.json")).read_text())
    assert charter.get("published_by_device") is True, "the charter does not say published_by_device"
    assert charter.get("public_interface") == [TOOL], charter.get("public_interface")
    reaches = []
    for node in ast.walk(ast.parse((TOOL_DIR / "trees.py").read_text(encoding="utf-8"))):
        mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        reaches += [m for m in mods if m.startswith("cairn.devices")
                    and not m.startswith(ALLOWED_DEVICE_IMPORT)]
    assert not reaches, f"the tool imports device code: {reaches}"
    import importlib
    mod = importlib.import_module(TOOL)
    missing = [n for n in SURFACE if not callable(getattr(mod, n, None))]
    missing += [n for n in VOCABULARY if not hasattr(mod, n)]
    assert not missing, f"the tool does not expose {missing}"
    # ONE FLOOR, NOT TWO: the librarian's own loop walks against the same floor every tenant reads.
    loop = importlib.import_module(OLD_LOOP)
    assert loop.RESOLUTION_FLOOR == mod.RESOLUTION_FLOOR, \
        f"the loop's floor {loop.RESOLUTION_FLOOR} is not the tool's {mod.RESOLUTION_FLOOR}"
    device = importlib.import_module("cairn.devices.librarian.device")
    assert isinstance(getattr(device, "LibrarianDevice", None), type), \
        "cairn.devices.librarian.device.LibrarianDevice is missing"


TEETH = [nothing_reaches_into_the_librarian_for_its_trees, the_old_address_is_gone,
         the_tool_is_published]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

"""Proof: no proof outside CodeMother imports build_inspector (ticket 149b9a1ab9c4, D3).

CodeMother answers build_inspector's judges over the bus (``inspect``, ticket 266d39d56d06), so a
proof in any other component that imports the inspector reaches into code it does not own
(RULE 1). Measured 2026-11-13: 76 proofs and probes outside codemother imported or path-joined
it. This is the census that holds the door once they ask over the bus instead.

WHAT COUNTS AS AN IMPORT. An AST read of every tracked ``proofs/*.py`` outside
``cairn/devices/codemother/`` and outside the inspector's own directory:
  - an ``import`` or ``from ... import`` naming the inspector's module or its package;
  - a call (``importlib.import_module``, ``__import__``, a late loader) whose first argument
    is the module name, either as a literal or as a module-level name bound to one.
A path join to ``inspector.py`` that only reads its text, and the module name inside a fixture
string that a sieve is fed, are not imports and are not counted.

Two teeth:
  1. The live census answers nothing: no outside proof imports the inspector.
  2. The census catches each spelling on fixture sources, and passes the two that are not
     imports. It's what stops tooth 1 from passing because the detector sees nothing.

    python3 cairn/tools/base/proofs/test_no_outside_proof_imports_build_inspector.py
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "149b9a1ab9c4": {
        "1": "test_no_outside_proof_imports_the_inspector",
    },
}

_MODULES = ("cairn.machines.build_inspector", "cairn.devices.codemother.machines.build_inspector")
_INSIDE = ("cairn/devices/codemother/", "cairn/machines/build_inspector/")


def _names_the_inspector(name: object) -> bool:
    return isinstance(name, str) and any(
        name == m or name.startswith(m + ".") for m in _MODULES)


def imports_of_the_inspector(source: str) -> list[int]:
    """Line numbers in ``source`` where the inspector is imported, by any spelling counted."""
    tree = ast.parse(source)
    bound = {}  # module-level NAME = "cairn.machines.build_inspector..."
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    bound[t.id] = node.value.value
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(_names_the_inspector(a.name) for a in node.names):
                hits.append(node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if _names_the_inspector(node.module) or any(
                    _names_the_inspector(f"{node.module}.{a.name}") for a in node.names):
                hits.append(node.lineno)
        elif isinstance(node, ast.Call) and node.args:
            first = node.args[0]
            value = first.value if isinstance(first, ast.Constant) else (
                bound.get(first.id) if isinstance(first, ast.Name) else None)
            if _names_the_inspector(value):
                hits.append(node.lineno)
    return sorted(set(hits))


def _outside_proofs() -> list[str]:
    out = subprocess.run(["git", "-C", str(_REPO_ROOT), "ls-files", "--", "*proofs/*.py"],
                         capture_output=True, text=True, check=True).stdout.split()
    return [p for p in out if "/proofs/" in "/" + p and not p.startswith(_INSIDE)]


def test_no_outside_proof_imports_the_inspector():
    proofs = _outside_proofs()
    assert len(proofs) > 100, f"the census read only {len(proofs)} proofs; git ls-files is wrong"
    found = {}
    for rel in proofs:
        path = _REPO_ROOT / rel
        if not path.is_file():
            continue
        lines = imports_of_the_inspector(path.read_text(encoding="utf-8"))
        if lines:
            found[rel] = lines
    assert not found, (f"{len(found)} proofs outside codemother import build_inspector; each "
                       f"asks codemother's inspect verb instead (ticket 149b9a1ab9c4):\n"
                       + "\n".join(f"  {k}:{v}" for k, v in sorted(found.items())))


def test_the_census_sees_every_spelling():
    caught = {
        "plain": "import cairn.machines.build_inspector.inspector as I\n",
        "from_module": "from cairn.machines.build_inspector.inspector import SIEVES\n",
        "from_package": "from cairn.machines.build_inspector import inspector\n",
        "codemother_address": "from cairn.devices.codemother.machines.build_inspector import x\n",
        "inside_a_function": "def f():\n    from cairn.machines.build_inspector import inspector\n",
        "importlib_literal": ("import importlib\n"
                              "m = importlib.import_module('cairn.machines.build_inspector.inspector')\n"),
        "late_loader_by_name": ("_MOD = 'cairn.machines.build_inspector.inspector'\n"
                                "m = _Late(_MOD)\n"),
    }
    for label, src in caught.items():
        assert imports_of_the_inspector(src), f"the census missed the {label} spelling"
    passed = {
        "path_join_read": ("from pathlib import Path\n"
                           "t = (Path('cairn') / 'machines' / 'build_inspector' / 'inspector.py')"
                           ".read_text()\n"),
        "fixture_string": "caught = sieve.imports_in('from cairn.machines.build_inspector import inspector')\n",
        "a_neighbour": "from cairn.machines.build_inspector_notes import x\n",
    }
    for label, src in passed.items():
        assert not imports_of_the_inspector(src), f"the census counted the {label}, not an import"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

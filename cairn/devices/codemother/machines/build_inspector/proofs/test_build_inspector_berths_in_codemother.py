#!/usr/bin/env python3
"""Proof for ticket 93fa3e3a6199: build_inspector berths among codemother's machines.

  1. no tracked file remains under cairn/machines/build_inspector/, and the moved charter
     names codemother as owner with gated_by unchanged (["codemother", "CC"]);
  2. no tracked code outside cairn/devices/codemother/ imports or path-joins either
     address (history records are left as written, so only .py code is read);
  3. encapsulation_holds reads no finding naming build_inspector. (The other half of
     clause 3, every moved proof resealing green, is the seal itself.)

Clause 2 is read by AST, so prose, docstrings and fixture strings that name the old
address as an example do not count. What counts: an import statement, an
importlib.import_module / __import__ call or a module-level name bound to a string that
spells either module, a ``/`` join whose string parts spell machines -> build_inspector, and a
string that spells the new address whole AND is used: joined, handed to a call (opened, a
Path, a walk's start) or the value of a ``start`` key. A string that only sits in data, e.g. a
set mirroring exemption_set.json's path keys, is a mention, not a reach (93fa decision, the
orchestrator's ruling 2026-11-13); _the_narrowing_holds_on_both_sides keeps it from widening.

    bin/cairn test cairn/devices/codemother/machines/build_inspector/proofs/test_build_inspector_berths_in_codemother.py
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"93fa3e3a6199": {
    "1": "nothing_stands_at_the_old_address_and_codemother_owns_it",
    "2": "no_outside_code_imports_or_path_joins_the_inspector",
    "3": "encapsulation_names_no_build_inspector_finding",
}}

OLD = "cairn/machines/build_inspector"
NEW = "cairn/devices/codemother/machines/build_inspector"
_MODULES = ("cairn.machines.build_inspector", "cairn.devices.codemother.machines.build_inspector")
_INSIDE = "cairn/devices/codemother/"


def _tracked() -> list[str]:
    out = subprocess.run(["git", "-C", str(_REPO), "ls-files", "-z"], capture_output=True,
                         check=True).stdout.decode("utf-8")
    return [f for f in out.split("\0") if f]


def _names_module(s: object) -> bool:
    return isinstance(s, str) and any(s == m or s.startswith(m + ".") for m in _MODULES)


def _div_parts(node: ast.AST) -> list:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _div_parts(node.left) + _div_parts(node.right)
    return [node]


def _joins_the_address(parts: list) -> bool:
    words: list[str] = []
    for p in parts:
        if isinstance(p, ast.Constant) and isinstance(p.value, str):
            words.extend(w for w in p.value.replace("\\", "/").split("/") if w)
        else:
            words.append("\0")
    return any(a == "machines" and b == "build_inspector" for a, b in zip(words, words[1:]))


def reaches_of(source: str) -> list[int]:
    """Line numbers in ``source`` that import or path-join the inspector."""
    tree = ast.parse(source)
    bound = {t.id for n in tree.body if isinstance(n, ast.Assign)
             and isinstance(n.value, ast.Constant) and _names_module(n.value.value)
             for t in n.targets if isinstance(t, ast.Name)}
    used = set()   # string constants a path is reached through, not merely written in data
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            used.update(id(a) for a in [*n.args, *(k.value for k in n.keywords)])
        elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            used.update(id(p) for p in _div_parts(n))
        elif isinstance(n, ast.Dict):
            used.update(id(v) for k, v in zip(n.keys, n.values)
                        if isinstance(k, ast.Constant) and k.value == "start")
    hits = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(_names_module(a.name) for a in node.names):
            hits.add(node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and _names_module(node.module):
            hits.add(node.lineno)
        elif isinstance(node, ast.Call) and node.args:
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            arg = node.args[0]
            if name in ("import_module", "__import__") and (
                    (isinstance(arg, ast.Constant) and _names_module(arg.value))
                    or (isinstance(arg, ast.Name) and arg.id in bound)):
                hits.add(node.lineno)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            if _joins_the_address(_div_parts(node)):
                hits.add(node.lineno)
        elif (isinstance(node, ast.Constant) and isinstance(node.value, str)
              and id(node) in used and NEW in node.value.replace("\\", "/")):
            hits.add(node.lineno)   # a path spelled whole and reached through, e.g. a walk's start
    return sorted(hits)


def nothing_stands_at_the_old_address_and_codemother_owns_it() -> None:
    left = [f for f in _tracked() if f.startswith(OLD + "/")]
    assert not left, f"{len(left)} tracked file(s) still at {OLD}/: {left[:5]}"
    charter = json.loads((_REPO / NEW / "intention+why.json").read_text(encoding="utf-8"))
    assert str(charter.get("owner", "")).startswith("codemother"), (
        f"the moved charter's owner does not name codemother first: {charter.get('owner', '')[:120]!r}")
    assert charter.get("gated_by") == ["codemother", "CC"], f"gated_by changed: {charter.get('gated_by')}"


def no_outside_code_imports_or_path_joins_the_inspector() -> None:
    found = []
    for f in _tracked():
        if not f.endswith(".py") or f.startswith(_INSIDE):
            continue
        try:
            lines = reaches_of((_REPO / f).read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            continue
        found += [f"{f}:{n}" for n in lines]
    assert not found, f"{len(found)} outside reach(es) into build_inspector: {found}"


def _reader_floor() -> None:
    """The reader must catch every spelling it claims, or tooth 2 is green over nothing."""
    planted = {
        "import cairn.machines.build_inspector.inspector as I\n": 1,
        "from cairn.devices.codemother.machines.build_inspector import inspector\n": 1,
        "import importlib\nm = importlib.import_module('cairn.machines.build_inspector.inspector')\n": 1,
        "_M = 'cairn.machines.build_inspector'\nimport importlib\nimportlib.import_module(_M)\n": 1,
        "from pathlib import Path\np = Path('x') / 'machines' / 'build_inspector' / 'sieves'\n": 1,
        "from pathlib import Path\np = Path('x') / 'cairn/devices/codemother/machines/build_inspector'\n": 1,
        "g = {'start': 'cairn/devices/codemother/machines/build_inspector/inspector.py'}\n": 1,
        "def f():\n    \"\"\"reads cairn/devices/codemother/machines/build_inspector by hand\"\"\"\n": 0,
        "s = 'from cairn.machines.build_inspector import inspector'\n": 0,
        "from cairn.machines.build_inspector_notes import x\n": 0,
    }
    for src, want in planted.items():
        got = len(reaches_of(src))
        assert got == want, f"the reader counted {got}, want {want}, over: {src!r}"


def _the_narrowing_holds_on_both_sides() -> None:
    """The reader's two sides of the mention/reach line (93fa decision): a joined, opened or
    walked path reds; the same path as a bare string in data mirroring exemption_set.json reads
    green. Either side moving makes this tooth red, so the narrowing cannot drift wider."""
    reach = {
        "from pathlib import Path\nR = Path('.')\np = R / 'cairn/devices/codemother/machines/build_inspector/inspector.py'\n": 1,
        "t = open('cairn/devices/codemother/machines/build_inspector/inspector.py').read()\n": 1,
        "from x import sieve\nsieve.reaches(g, 'cairn/devices/codemother/machines/build_inspector/inspector.py')\n": 1,
    }
    mention = {
        "want = {'cairn/devices/codemother/machines/exemptions/exemption_set.json',\n"
        "        'cairn/devices/codemother/machines/build_inspector/inspector.py'}\n": 0,
        "_MOVED = ('cairn/devices/codemother/machines/build_inspector/proofs/t.py',)\n": 0,
    }
    for src, want in {**reach, **mention}.items():
        got = len(reaches_of(src))
        assert got == want, f"the reader counted {got}, want {want}, over: {src!r}"


def encapsulation_names_no_build_inspector_finding() -> None:
    from cairn.tools.inspect_wire.inspect_wire import ask
    breaches = ask("encapsulation_breaches", str(_REPO))
    named = [b for b in breaches if "build_inspector" in json.dumps(b, default=str)]
    assert not named, f"encapsulation_holds names build_inspector: {named}"


def main() -> int:
    red = 0
    for fn in (_reader_floor, _the_narrowing_holds_on_both_sides, nothing_stands_at_the_old_address_and_codemother_owns_it,
               no_outside_code_imports_or_path_joins_the_inspector,
               encapsulation_names_no_build_inspector_finding):
        try:
            fn()
            print(f"  green  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            red += 1
            print(f"  RED    {fn.__name__}: {type(e).__name__}: {e}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

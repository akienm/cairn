"""Proof for ticket 580ad3b46cd0 — the trees tool's proof measures only the trees tool.

RULE 1 (Akien, 2026-10-01): a ticket's build lives inside its own component, and its proofs
measure only that component. 883abe55d04c's clause 3 put two checks about the LIBRARIAN into the
trees TOOL's proof: the loop walks the tool's floor (importlib of cairn.devices.librarian.loop,
invisible to the sieve) and LibrarianDevice stands in the device (importlib of
cairn.devices.librarian.device, line 131). Measured before this ticket: 1 encapsulation_breaches
row with source cairn/devices/librarian/tools/trees, target cairn/devices/librarian, 'undeclared'.

One tooth per numbered falsifier clause, over the LIVE repo (invariants, never snapshots):

  1. NOTHING IN THE TOOL REACHES ITS HOLDER. No encapsulation_breaches row has source
     cairn/devices/librarian/tools/trees.
  2. THE TOOL'S PROOF IMPORTS NONE OF THE LIBRARIAN. The trees proof names neither
     cairn.devices.librarian.device nor cairn.devices.librarian.loop in an import statement or
     an import_module call (the second is the reach the sieve cannot see).
  3. THE HOLDER KEEPS ONE FLOOR. The librarian's loop walks against the very RESOLUTION_FLOOR
     its published trees tool declares.

    python3 cairn/devices/librarian/proofs/test_librarian_holds_its_trees_checks.py   # exit 0 = green
"""
import ast
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class _Late:
    """The inspector resolves AT CALL TIME, so `cairn test --hollow` reads as red teeth
    rather than an import that never ran."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.machines.build_inspector.inspector")

PROVES = {"580ad3b46cd0": {"1": "nothing_in_the_tool_reaches_its_holder",
                           "2": "the_tools_proof_imports_none_of_the_librarian",
                           "3": "the_holder_keeps_one_floor"}}

TOOL_SOURCE = "cairn/devices/librarian/tools/trees"
TREES_PROOF = _REPO_ROOT / TOOL_SOURCE / "proofs" / "test_trees_is_a_published_tool.py"
HOLDER_MODULES = ("cairn.devices.librarian.device", "cairn.devices.librarian.loop")

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
        print(f"  ok    {name}")


def nothing_in_the_tool_reaches_its_holder():
    rows = [r for r in _inspector.encapsulation_breaches(str(_REPO_ROOT)) if r["source"] == TOOL_SOURCE]
    assert not rows, f"{len(rows)} reach(es) out of the trees tool: " \
        f"{[(r['file'], r['line'], r['module'], r['reason']) for r in rows]}"


def _module_constants(tree):
    """Module-level NAME = 'string' bindings, so import_module(NAME) resolves to what it imports."""
    out = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = node.value.value
    return out


def the_tools_proof_imports_none_of_the_librarian():
    tree = ast.parse(TREES_PROOF.read_text(encoding="utf-8"))
    consts = _module_constants(tree)
    named = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            named += [(node.lineno, a.name) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            named.append((node.lineno, node.module or ""))
        elif (isinstance(node, ast.Call) and node.args
              and getattr(node.func, "attr", getattr(node.func, "id", "")) == "import_module"):
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                named.append((node.lineno, arg.value))
            elif isinstance(arg, ast.Name) and arg.id in consts:
                named.append((node.lineno, consts[arg.id]))
    reaches = [(line, m) for line, m in named
               if any(m == h or m.startswith(h + ".") for h in HOLDER_MODULES)]
    assert not reaches, f"the trees tool's proof imports the librarian: {reaches}"


def the_holder_keeps_one_floor():
    import importlib
    loop = importlib.import_module("cairn.devices.librarian.loop")
    trees = importlib.import_module("cairn.devices.librarian.tools.trees.trees")
    assert loop.RESOLUTION_FLOOR == trees.RESOLUTION_FLOOR, \
        f"the loop's floor {loop.RESOLUTION_FLOOR} is not the trees tool's {trees.RESOLUTION_FLOOR}"


TEETH = [nothing_in_the_tool_reaches_its_holder, the_tools_proof_imports_none_of_the_librarian,
         the_holder_keeps_one_floor]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

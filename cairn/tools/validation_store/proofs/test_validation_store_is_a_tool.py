"""Proof for ticket fe1cba85cb12 — the validation store lives in a tool, and no component
reaches into the tester device to read or write a seal.

RULE 1 (Akien, 2026-10-01): every component talks to every other only through its public
interface; a device's is the bus plus any client tool it publishes. The store is a file
reader/writer over each component's own validations/, and the only things it took from the
tester were record vocabulary (GREEN, VALIDATION_FIELDS, the isolation verdicts) — so it is a
tool everyone uses the same way, not the tester's interface. Measured before the build: 27
encapsulation rows landed on cairn.devices.tester.validation_store.

One tooth per numbered falsifier clause, over the LIVE repo (invariants, never snapshots):

  1. NOTHING REACHES INTO THE TESTER FOR THE STORE. No encapsulation_breaches row names it.
  2. THE OLD ADDRESS IS GONE. No .py file or bin/ command names the store under the tester,
     dotted or as `from cairn.devices.tester import validation_store`, and
     cairn/devices/tester/validation_store.py does not exist.
  3. THE TOOL STANDS. Its charter declares exactly its one module, that module imports
     nothing from cairn.devices, and it exposes the store's surface and its vocabulary.

    python3 cairn/tools/validation_store/proofs/test_validation_store_is_a_tool.py   # exit 0 = green
"""
import ast
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
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

PROVES = {"fe1cba85cb12": {"1": "nothing_reaches_into_the_tester_for_the_store",
                           "2": "the_old_address_is_gone",
                           "3": "the_tool_stands"}}

OLD = "cairn.devices.tester.validation_store"
TOOL = "cairn.tools.validation_store.validation_store"
TOOL_DIR = _REPO_ROOT / "cairn" / "tools" / "validation_store"
SURFACE = ("standing", "persist_validation", "record_hollow", "read_validations",
           "source_fingerprint")
VOCABULARY = ("GREEN", "RED", "VALIDATION_FIELDS", "SEALED", "OPEN", "INDETERMINATE", "BREACHED")
_OLD_RE = re.compile(re.escape(OLD) + r"(?![\w])"
                     r"|from\s+cairn\.devices\.tester\s+import\s+[^\n]*\bvalidation_store\b")

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


def nothing_reaches_into_the_tester_for_the_store():
    rows = [b for b in _inspector.encapsulation_breaches(str(_REPO_ROOT)) if b["module"] == OLD]
    assert not rows, f"{len(rows)} reach(es) into the tester for the store: " + \
        "; ".join(f"{b['file']}:{b['line']}" for b in rows[:8])


def _code_files():
    for p in _REPO_ROOT.rglob("*.py"):
        if (p != Path(__file__).resolve() and "__pycache__" not in p.parts
                and ".git" not in p.parts):
            yield p
    for p in (_REPO_ROOT / "bin").rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix in ("", ".py", ".sh"):
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
    assert not naming, f"{len(naming)} file(s) still name the store under the tester: " \
        f"{sorted(naming)[:8]}"
    assert not (_REPO_ROOT / "cairn/devices/tester/validation_store.py").exists(), \
        "cairn/devices/tester/validation_store.py still stands"


def the_tool_stands():
    charter = json.loads((TOOL_DIR / ("intention+" + "why.json")).read_text())
    assert charter.get("public_interface") == [TOOL], charter.get("public_interface")
    src = TOOL_DIR / "validation_store.py"
    reaches = []
    for node in ast.walk(ast.parse(src.read_text(encoding="utf-8"))):
        mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        reaches += [m for m in mods if m.startswith("cairn.devices")]
    assert not reaches, f"the tool imports device code: {reaches}"
    import importlib
    mod = importlib.import_module(TOOL)
    missing = [n for n in SURFACE if not callable(getattr(mod, n, None))]
    missing += [n for n in VOCABULARY if not hasattr(mod, n)]
    assert not missing, f"the tool does not expose {missing}"


TEETH = [nothing_reaches_into_the_tester_for_the_store, the_old_address_is_gone, the_tool_stands]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

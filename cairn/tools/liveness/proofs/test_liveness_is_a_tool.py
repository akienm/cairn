"""Proof for ticket 59ade57ef280 — the liveness record's reader and writer live in a tool, and
no component reaches into the cairn device's ground loop to ask whether the system is up.

RULE 1 (Akien, 2026-10-01): every component talks to every other only through its public
interface; a device's is the bus plus any client tool it publishes. The liveness module is an
atomic stamp and a staleness verdict over a file, importing nothing but
cairn.tools.base.address — so it is a tool its users reach the same way, and the shim's
lazy-init (cairn/tools/base/shim.py) reads it without reaching into a device. Measured before
the build: 6 encapsulation rows landed on cairn.devices.cairn.machines.ground_loop.liveness.

One tooth per numbered falsifier clause, over the LIVE repo (invariants, never snapshots):

  1. NOTHING REACHES INTO THE GROUND LOOP FOR LIVENESS. No encapsulation_breaches row names it.
  2. THE OLD ADDRESS IS GONE. No .py file or bin/ command names liveness under the ground loop,
     dotted or as `from cairn.devices.cairn.machines.ground_loop import liveness`, and
     cairn/devices/cairn/machines/ground_loop/liveness.py does not exist.
  3. THE TOOL STANDS. Its charter declares exactly its one module, that module imports
     nothing from cairn.devices, it exposes the record's surface, and the record it reads by
     default is still the one the running ground loop writes.

    python3 cairn/tools/liveness/proofs/test_liveness_is_a_tool.py   # exit 0 = green
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

PROVES = {"59ade57ef280": {"1": "nothing_reaches_into_the_ground_loop_for_liveness",
                           "2": "the_old_address_is_gone",
                           "3": "the_tool_stands"}}

OLD = "cairn.devices.cairn.machines.ground_loop.liveness"
TOOL = "cairn.tools.liveness.liveness"
TOOL_DIR = _REPO_ROOT / "cairn" / "tools" / "liveness"
SURFACE = ("instance_home", "write_liveness", "read_liveness")
VOCABULARY = ("STALENESS_THRESHOLD_S", "RECORD_NAME")
_OLD_RE = re.compile(re.escape(OLD) + r"(?![\w])"
                     r"|from\s+cairn\.devices\.cairn\.machines\.ground_loop\s+import\s+[^\n]*\bliveness\b")

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


def nothing_reaches_into_the_ground_loop_for_liveness():
    rows = [b for b in _inspector.encapsulation_breaches(str(_REPO_ROOT)) if b["module"] == OLD]
    assert not rows, f"{len(rows)} reach(es) into the ground loop for liveness: " + \
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
    assert not naming, f"{len(naming)} file(s) still name liveness under the ground loop: " \
        f"{sorted(naming)[:8]}"
    assert not (_REPO_ROOT / "cairn/devices/cairn/machines/ground_loop/liveness.py").exists(), \
        "cairn/devices/cairn/machines/ground_loop/liveness.py still stands"


def the_tool_stands():
    charter = json.loads((TOOL_DIR / ("intention+" + "why.json")).read_text())
    assert charter.get("public_interface") == [TOOL], charter.get("public_interface")
    src = TOOL_DIR / "liveness.py"
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
    # THE RECORD DID NOT MOVE, only its reader did: a running ground loop keeps writing where it
    # always has, and a shim asking "is the system up" must read that same file.
    from cairn.tools.base.address import instance_path
    want = instance_path("cairn", 0) / "machines" / "ground_loop"
    assert mod.instance_home() == want, f"the default record home moved: {mod.instance_home()} != {want}"


TEETH = [nothing_reaches_into_the_ground_loop_for_liveness, the_old_address_is_gone, the_tool_stands]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

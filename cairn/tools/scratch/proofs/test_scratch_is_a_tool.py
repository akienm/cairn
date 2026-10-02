"""Proof for ticket 9245b9cbce53 — the proof fixture primitives live in a tool, and no proof
reaches into the tester device for a temp directory.

RULE 1 (Akien, 2026-10-01): every component talks to every other only through its public
interface; a device's is the bus plus any client tool it publishes. scratch_dir,
scratch_worktree and git_env touch no tester state (scratch.py imports only the standard
library), so they are a tool everyone uses, not the tester's interface. Measured before the
build: 90 into_device rows landed on cairn.devices.tester.scratch.

One tooth per numbered falsifier clause, over the LIVE repo (invariants, never snapshots):

  1. NOTHING REACHES INTO THE TESTER FOR SCRATCH. No encapsulation_breaches row names it.
  2. THE OLD ADDRESS IS GONE. No .py file or bin/ command names cairn.devices.tester.scratch
     as a dotted path, and cairn/devices/tester/scratch.py does not exist.
  3. THE TOOL STANDS. Its charter declares exactly its one module, that module exposes the
     three primitives, and its moved proof test_scratch.py exits 0.

    python3 cairn/tools/scratch/proofs/test_scratch_is_a_tool.py   # exit 0 = green
"""
import json
import re
import subprocess
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

PROVES = {"9245b9cbce53": {"1": "nothing_reaches_into_the_tester_for_scratch",
                           "2": "the_old_address_is_gone",
                           "3": "the_tool_stands"}}

OLD = "cairn.devices.tester.scratch"
TOOL = "cairn.tools.scratch.scratch"
TOOL_DIR = _REPO_ROOT / "cairn" / "tools" / "scratch"
SURFACE = ("scratch_dir", "scratch_worktree", "git_env")
# the dotted path itself, not its sibling cairn.devices.tester.scratch_sweep (the db sweep stays)
_OLD_RE = re.compile(re.escape(OLD) + r"(?![\w])")

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


def nothing_reaches_into_the_tester_for_scratch():
    rows = [b for b in _inspector.encapsulation_breaches(str(_REPO_ROOT)) if b["module"] == OLD]
    assert not rows, f"{len(rows)} reach(es) into the tester for scratch: " + \
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
    assert not naming, f"{len(naming)} file(s) still name {OLD}: {sorted(naming)[:8]}"
    assert not (_REPO_ROOT / "cairn/devices/tester/scratch.py").exists(), \
        "cairn/devices/tester/scratch.py still stands"


def the_tool_stands():
    charter = json.loads((TOOL_DIR / "intention+why.json").read_text())
    assert charter.get("public_interface") == [TOOL], charter.get("public_interface")
    import importlib
    mod = importlib.import_module(TOOL)
    missing = [n for n in SURFACE if not callable(getattr(mod, n, None))]
    assert not missing, f"the tool does not expose {missing}"
    moved = TOOL_DIR / "proofs" / "test_scratch.py"
    r = subprocess.run([sys.executable, str(moved)], cwd=_REPO_ROOT, capture_output=True,
                       text=True, timeout=600)
    assert r.returncode == 0, f"{moved.name} exit {r.returncode}: {(r.stdout + r.stderr)[-600:]}"


TEETH = [nothing_reaches_into_the_tester_for_scratch, the_old_address_is_gone, the_tool_stands]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

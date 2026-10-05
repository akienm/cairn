"""Proof for ticket 0527c3962d86 — codemother reaches system_word through its package.

RULE 1 (Akien, 2026-10-01): a component is reached only through its DECLARED public interface.
system_word declares cairn.tools.system_word (its __init__ re-exports is_word); b984567d8c05 added a
function-local import in codemother's _handle_sealed naming the inner module
cairn.tools.system_word.system_word. Measured before this ticket: 1 encapsulation_breaches row
'undeclared' on cairn/tools/system_word, from cairn/devices/codemother/shim.py:326.

One tooth, over the LIVE repo (an invariant, never a snapshot):

  1. NOTHING IN CODEMOTHER REACHES SYSTEM_WORD UNDECLARED. No encapsulation_breaches row has a
     file under cairn/devices/codemother/ and target cairn/tools/system_word.

    python3 cairn/devices/codemother/proofs/test_codemother_reaches_system_word_through_its_package.py   # exit 0 = green
"""
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

PROVES = {"0527c3962d86": {"1": "nothing_in_codemother_reaches_system_word_undeclared"}}

SOURCE = "cairn/devices/codemother/"
TARGET = "cairn/tools/system_word"

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


def nothing_in_codemother_reaches_system_word_undeclared():
    rows = [r for r in _inspector.encapsulation_breaches(str(_REPO_ROOT))
            if r["file"].startswith(SOURCE) and r["target"] == TARGET]
    assert not rows, f"{len(rows)} reach(es) from codemother into system_word off its interface: " \
        f"{[(r['file'], r['line'], r['module'], r['reason']) for r in rows]}"


TEETH = [nothing_in_codemother_reaches_system_word_undeclared]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

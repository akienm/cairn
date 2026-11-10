"""tellmeabout reaches trouble through its store tool (ticket def08e6af7cb) — teeth a hollow build could not pass.

RULE 1 (outline 17.13.1): a device is reached through the bus or a tool it publishes. tellmeabout
imported cairn.devices.trouble.trouble for store_root; trouble publishes that read as
cairn.devices.trouble.tools.store.store (its charter declares published_by_device).
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "def08e6af7cb": {
        "1": "test_no_file_reaches_trouble_but_its_tool",
        "2": "test_the_live_sieve_reads_no_row_under_tellmeabout",
        "3": "test_the_store_named_is_the_tools_store",
    },
}

_SKILL = _REPO_ROOT / "skills" / "tellmeabout"
_TOOL = "cairn.devices.trouble.tools.store.store"


def test_no_file_reaches_trouble_but_its_tool():
    reach = []
    for p in sorted(_SKILL.rglob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for node in ast.walk(tree):
            names = ([node.module] if isinstance(node, ast.ImportFrom) and node.module
                     else [a.name for a in node.names] if isinstance(node, ast.Import) else [])
            reach += [f"{p.relative_to(_REPO_ROOT)}:{node.lineno} {n}" for n in names
                      if n.startswith("cairn.devices") and n != _TOOL]
    assert not reach, f"tellmeabout reaches device code: {reach}"


def test_the_live_sieve_reads_no_row_under_tellmeabout():
    from cairn.machines.build_inspector.inspector import encapsulation_breaches
    rows = [r for r in encapsulation_breaches(str(_REPO_ROOT))
            if str(r.get("file", "")).startswith("skills/tellmeabout/")]
    assert not rows, f"the RULE 1 sieve reads {rows}"


def test_the_store_named_is_the_tools_store():
    from cairn.devices.trouble.tools.store.store import store_root
    spec = importlib.util.spec_from_file_location("tellmeabout_under_proof", _SKILL / "tellmeabout.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod._trouble_store() == store_root(), (mod._trouble_store(), store_root())


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except BaseException as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {str(exc)[:300]}")
    sys.exit(1 if failed else 0)

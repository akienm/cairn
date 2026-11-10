"""the harbor's clearance proof reaches trouble through its store tool (ticket 53a2027c00f9) — teeth a hollow build could not pass.

RULE 1 (outline 17.13.1): a device is reached through the bus or a tool it publishes. These lines
imported the trouble device's own module; trouble publishes what they need as cairn.devices.trouble.tools.store.store
(its charter cairn/devices/trouble/tools/store/intention+why.json declares published_by_device).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "53a2027c00f9": {
        "1": "test_the_named_lines_reach_only_the_tool",
        "2": "test_the_live_sieve_reads_no_row_at_the_named_lines",
    },
}

_DEVICE = "cairn.devices.trouble"
_TOOL = "cairn.devices.trouble.tools.store.store"
_SITES = [["cairn/devices/cairn/machines/harbor_master/proofs/test_clearance.py", 2008]]


def _imports_at(rel: str, line: int) -> list[str]:
    p = _REPO_ROOT / rel
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    out = []
    for node in ast.walk(tree):
        if getattr(node, "lineno", None) != line:
            continue
        if isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
        elif isinstance(node, ast.Import):
            out += [a.name for a in node.names]
    return out


def test_the_named_lines_reach_only_the_tool():
    bad, seen = [], 0
    for rel, line in _SITES:
        mods = _imports_at(rel, line)
        seen += len(mods)
        bad += [f"{rel}:{line} {m}" for m in mods if m.startswith(_DEVICE) and m != _TOOL]
    assert seen == len(_SITES), f"expected an import at each named line, found {seen} over {len(_SITES)}"
    assert not bad, f"device code reached: {bad}"


def test_the_live_sieve_reads_no_row_at_the_named_lines():
    from cairn.machines.build_inspector.inspector import encapsulation_breaches
    want = {(rel, line) for rel, line in _SITES}
    rows = [r for r in encapsulation_breaches(str(_REPO_ROOT)) if (r.get("file"), r.get("line")) in want]
    assert not rows, f"the RULE 1 sieve reads {rows}"


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

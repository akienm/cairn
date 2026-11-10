"""The discovered shim leaves the heartbeat (ticket 2438292fae7c) — teeth a hollow build could not pass.

Outline 5.6.3: ground_loop must never grow back a shim. DiscoveredShim (and the _FeedbackDevice
mailbox it starts) lived at cairn/devices/cairn/machines/ground_loop/discovered.py, importing
only cairn.tools.base, and two tools reached into the cairn device for it (RULE 1). It is a base
tool now, and every importer reaches it there.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "2438292fae7c": {
        "1": "test_the_shim_stands_in_base_and_not_in_the_heartbeat",
        "2": "test_nothing_names_the_old_address",
        "3": "test_the_live_sieve_reads_no_reach_to_the_old_address",
        "4": "test_the_charters_publish_it_from_base",
    },
}

_OLD = "cairn.devices.cairn.machines." + "ground_loop.discovered"
_NEW_FILE = _REPO_ROOT / "cairn" / "tools" / "base" / "discovered.py"
_OLD_FILE = _REPO_ROOT / "cairn" / "devices" / "cairn" / "machines" / "ground_loop" / "discovered.py"


def test_the_shim_stands_in_base_and_not_in_the_heartbeat():
    assert _NEW_FILE.is_file(), f"{_NEW_FILE.relative_to(_REPO_ROOT)} does not exist"
    tree = ast.parse(_NEW_FILE.read_text(encoding="utf-8"))
    classes = {n.name for n in tree.body if isinstance(n, ast.ClassDef)}
    assert {"DiscoveredShim", "_FeedbackDevice"} <= classes, f"classes defined: {sorted(classes)}"
    assert not _OLD_FILE.exists(), f"{_OLD_FILE.relative_to(_REPO_ROOT)} still stands"


def test_nothing_names_the_old_address():
    hits = []
    for p in _REPO_ROOT.rglob("*.py"):
        if ".git" in p.parts or "__pycache__" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if _OLD in line:
                hits.append(f"{p.relative_to(_REPO_ROOT)}:{i}")
    assert not hits, f"the old address is still named at: {hits}"


def test_the_live_sieve_reads_no_reach_to_the_old_address():
    from cairn.machines.build_inspector.inspector import encapsulation_breaches

    rows = [r for r in encapsulation_breaches(str(_REPO_ROOT)) if r.get("module") == _OLD]
    assert not rows, f"reaches into the heartbeat for the shim: {rows}"


def _interface(rel: str) -> list:
    return json.loads((_REPO_ROOT / rel / "intention+why.json").read_text(encoding="utf-8")).get(
        "public_interface", [])


def test_the_charters_publish_it_from_base():
    base = _interface("cairn/tools/base")
    assert "cairn.tools.base.discovered" in base, "base's public_interface does not list discovered"
    loop = _interface("cairn/devices/cairn/machines/ground_loop")
    stale = [m for m in loop if m in (_OLD, "cairn.devices.cairn.machines.ground_loop.loop")]
    assert not stale, f"ground_loop's public_interface still lists {stale}"


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

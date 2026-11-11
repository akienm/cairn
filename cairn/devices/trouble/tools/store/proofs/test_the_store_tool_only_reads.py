#!/usr/bin/env python3
"""Proof for ticket 40b05ea65eed: the store tool trouble publishes is proved at its own address.

Measured 2026-11-11: the build inspector filed proofs_exist and claim_provenance findings on
devices/trouble/tools/store. Its proofs sat at the trouble device, so the tool read as
unproved where it lives, and its falsifier's "the tool never writes the store" was measured
nowhere. These teeth measure the tool alone (RULE 1); the device's proofs still prove its
readers.

One tooth per falsifier clause (PROVES below), each binding the tool at call time so a hollow
reading reds the tooth instead of crashing the reader:
  (1) the inspector's claim_provenance sieve answers [] on this tool's charter;
  (2) this proofs/ directory is a proof the inspector counts: proofs_exist answers [];
  (3) live() and listing() over a scratch store leave every path, size and mtime_ns unchanged,
      and store.py calls no write, delete, rename or mkdir;
  (4) live() over an absent store raises, and over a seeded one answers exactly the top-level
      tickets and none from cleared/.

    bin/cairn test cairn/devices/trouble/tools/store/proofs/test_the_store_tool_only_reads.py
"""

from __future__ import annotations

import ast
import importlib
import json
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_TOOL_DIR = _REPO / "cairn" / "devices" / "trouble" / "tools" / "store"
_TOOL = "cairn.devices.trouble.tools.store.store"
_COMPONENT = "devices/trouble/tools/store"
_WRITES = {"write_text", "write_bytes", "unlink", "rename", "replace", "mkdir", "rmdir",
           "rmtree", "touch", "remove", "makedirs", "symlink_to", "chmod"}

PROVES = {"40b05ea65eed": {
    "1": "test_the_charter_carries_its_provenance",
    "2": "test_the_tool_has_proofs_of_its_own",
    "3": "test_the_tool_writes_nothing",
    "4": "test_an_absent_store_raises_and_a_seeded_one_reads_its_top",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:400]}")
    if not ok:
        FAILURES.append(name)


def _seed(store: Path) -> None:
    def put(folder: Path, ident: str, standing: str = "OPEN") -> None:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{ident}.json").write_text(json.dumps({
            "id": ident, "standing": standing, "why": f"a proof's trouble ({ident})",
            "count": 1, "first_seen": "2026-11-11T00:00:00+00:00",
            "last_seen": "2026-11-11T00:00:00+00:00"}) + "\n", encoding="utf-8")
    put(store, "proof-40b0-live-a")
    put(store, "proof-40b0-live-b")
    put(store / "cleared", "proof-40b0-cleared", standing="CLEARED")


def _snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): (p.is_dir(), p.stat().st_size, p.stat().st_mtime_ns)
            for p in sorted(root.rglob("*"))}


def test_the_charter_carries_its_provenance() -> None:
    inspector = importlib.import_module("cairn.machines.build_inspector.inspector")
    got = inspector.claim_provenance({"component": _COMPONENT}, _TOOL_DIR)
    check("test_the_charter_carries_its_provenance", got == [], f"findings={got}")


def test_the_tool_has_proofs_of_its_own() -> None:
    inspector = importlib.import_module("cairn.machines.build_inspector.inspector")
    proofs = sorted(p.name for p in (_TOOL_DIR / "proofs").glob("test_*.py"))
    got = inspector.proofs_exist({"component": _COMPONENT, "proofs": len(proofs)}, _TOOL_DIR)
    check("test_the_tool_has_proofs_of_its_own", bool(proofs) and got == [],
          f"proofs={proofs} findings={got}")


def test_the_tool_writes_nothing() -> None:
    tool = importlib.import_module(_TOOL)
    with tempfile.TemporaryDirectory(prefix="40b0-reads-") as d:
        store = Path(d) / "troubletickets"
        _seed(store)
        (store / "proof-40b0-unreadable.json").write_text("{not json", encoding="utf-8")
        before = _snapshot(Path(d))
        tool.live(root=store)
        tool.listing(store)
        tool.listing(store / "cleared")
        after = _snapshot(Path(d))
    tree = ast.parse(Path(tool.__file__).read_text(encoding="utf-8"))
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name in _WRITES:
                calls.add(name)
            if name == "open":
                modes = [a.value for a in node.args[1:2] if isinstance(a, ast.Constant)]
                modes += [k.value.value for k in node.keywords
                          if k.arg == "mode" and isinstance(k.value, ast.Constant)]
                if any(set(str(m)) & set("wax+") for m in modes):
                    calls.add(f"open({modes})")
    changed = sorted(set(before) ^ set(after)) + sorted(
        k for k in before if k in after and before[k] != after[k])
    check("test_the_tool_writes_nothing", not changed and not calls,
          f"changed={changed} write_calls={sorted(calls)}")


def test_an_absent_store_raises_and_a_seeded_one_reads_its_top() -> None:
    tool = importlib.import_module(_TOOL)
    with tempfile.TemporaryDirectory(prefix="40b0-live-") as d:
        try:
            absent = tool.live(root=Path(d) / "no-store-here")
            raised = False
        except FileNotFoundError as exc:
            absent, raised = f"FileNotFoundError: {exc}", True
        store = Path(d) / "troubletickets"
        _seed(store)
        ids = sorted(r.get("id") for r in tool.live(root=store))
    check("test_an_absent_store_raises_and_a_seeded_one_reads_its_top",
          raised and ids == ["proof-40b0-live-a", "proof-40b0-live-b"],
          f"absent={absent!r} ids={ids}")


def main() -> int:
    for tooth in (test_the_charter_carries_its_provenance, test_the_tool_has_proofs_of_its_own,
                  test_the_tool_writes_nothing,
                  test_an_absent_store_raises_and_a_seeded_one_reads_its_top):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

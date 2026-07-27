"""Proofs for build_inspector — filters judge measurements, findings are complete,
and the gate cannot silently inspect nothing.

Hermetic: a synthetic tree pins each filter's fire-and-stay-quiet behavior; the real
tree is asserted by invariant only (shape and floors, never a snapshot of findings —
the sweep's real findings are work items, not constants; memory:
proof-over-live-data-assert-invariants).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.build_inspector.inspector import FILTERS, inspect  # noqa: E402
from cairn.charter import projector  # noqa: E402
from cairn.orient.orient import ScanRefused  # noqa: E402

_FINDING_SHAPE = {"filter", "component", "finding", "evidence", "why_it_matters"}


def _refuses(fn, because):
    try:
        fn()
    except ScanRefused:
        return
    except Exception as e:  # noqa: BLE001
        raise AssertionError(
            f"THE GATE DID NOT REFUSE — {because}. Instead: {type(e).__name__}: {e}."
        ) from None
    raise AssertionError(f"NO REFUSAL AT ALL — {because}.")


def _component(root: Path, name: str, *, charter=True, proof=True, device=True, emits=True):
    d = root / name
    (d / "proofs").mkdir(parents=True)
    if charter:
        (d / "intention+why.json").write_text('{"component": "%s"}' % name)
    if proof:
        (d / "proofs" / "test_x.py").write_text("assert True\n")
    body = "from base import BaseDevice\n\n\nclass D(BaseDevice):\n    def work(self):\n"
    body += "        self.emit('gate')\n" if emits else "        return 1\n"
    (d / "dev.py").write_text(body if device else "def helper():\n    return 1\n")
    return d


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="inspector-proof-"))
    root = tmp / "cairn"

    # A healthy component and one broken per filter.
    _component(root, "healthy")
    _component(root, "no_charter", charter=False)
    _component(root, "no_proofs", proof=False)
    _component(root, "silent", emits=False)
    _component(root, "plain_lib", device=False, emits=False)  # not a device: silence is fine

    # 1 — a healthy component is CLEAN: a gate that always fires is a smoke alarm
    #     nobody wires in (and 'plain_lib' shows silent_device scopes to devices only).
    r = inspect(root=root, component="healthy")
    assert r["clean"] and r["findings"] == [], r["findings"]
    assert inspect(root=root, component="plain_lib")["clean"]

    # 2 — each seeded failure fires exactly its filter, nothing else.
    for comp, expected in [("no_charter", "charter_on_disk"),
                           ("no_proofs", "proofs_exist"),
                           ("silent", "silent_device")]:
        f = inspect(root=root, component=comp)["findings"]
        assert [x["filter"] for x in f] == [expected], (comp, f)

    # 3 — state_is_projection: a voyage written THROUGH THE DOOR is clean...
    h, s = root / "healthy" / "history.json", root / "healthy" / "state.json"
    projector.append_entry(str(h), str(s), {"standing": "BUILDME", "note": "born"})
    assert inspect(root=root, component="healthy")["clean"]

    # 4 — ...and a HAND-EDIT to state.json is caught as drift, with the diverging keys.
    edited = json.loads(s.read_text())
    edited["cursor"] = {"gate": "PROVED"}  # the lie: promotion without a crossing
    s.write_text(json.dumps(edited))
    f = inspect(root=root, component="healthy")["findings"]
    assert [x["filter"] for x in f] == ["state_is_projection"], f
    assert "cursor" in f[0]["evidence"]["diverging_keys"], f[0]

    # 5 — repair goes through the door (append), never an edit — and the gate agrees.
    projector.append_entry(str(h), str(s), {"standing": "BUILDME", "note": "re-projected"})
    assert inspect(root=root, component="healthy")["clean"]

    # 6 — an orphan half of the pair is a finding (state without history).
    orphan = _component(root, "orphan")
    (orphan / "state.json").write_text("{}")
    f = inspect(root=root, component="orphan")["findings"]
    assert [x["filter"] for x in f] == ["state_is_projection"] and "without" in f[0]["finding"]

    # 7 — the gate cannot silently inspect nothing: unknown component refuses, and
    #     names what the census actually sees (complete on first pass).
    _refuses(lambda: inspect(root=root, component="ghost"),
             "inspecting a nonexistent component must refuse — a gate that inspects "
             "nothing passes everything")

    # 8 — a bad root refuses (inherited from the census, verified at THIS surface).
    _refuses(lambda: inspect(root=tmp / "nowhere"),
             "a sweep of nowhere must refuse, not report a clean empty world")

    # 9 — every finding is complete on first pass: full shape, non-empty why.
    sweep = inspect(root=root)
    assert not sweep["clean"]
    for x in sweep["findings"]:
        assert set(x) == _FINDING_SHAPE and len(x["why_it_matters"]) > 40, x

    # 10 — THE LEARNING-DEVICE SHAPE: every filter's docstring carries a provenance
    #      naming its seeding failure (dated or IOU-named) — a filter nobody was
    #      taught by is refused here, same tooth as orient's scans.
    for name, judge in FILTERS.items():
        doc = judge.__doc__ or ""
        assert "Provenance:" in doc, f"{name}: no provenance — a check nobody was taught by"

    # 11 — REAL TREE, invariants only: the sweep runs, sees the tree, exits gate-ably.
    real = inspect()
    assert real["components_inspected"] >= 10, "the sweep barely saw the tree"
    assert real["filters_run"] == sorted(FILTERS)
    for x in real["findings"]:
        assert set(x) == _FINDING_SHAPE, x
    assert real["clean"] == (not real["findings"])

    # 12 — the inspector is inference-free BY IMPORT: no deepen, no inference_domain,
    #      no outbound-capable module in inspector.py.
    import ast as _ast
    src = (_REPO_ROOT / "cairn" / "build_inspector" / "inspector.py").read_text()
    tree = _ast.parse(src)
    imported = {
        n.name.split(".")[0]
        for node in _ast.walk(tree) if isinstance(node, _ast.Import) for n in node.names
    } | {
        node.module.split(".")[0]
        for node in _ast.walk(tree)
        if isinstance(node, _ast.ImportFrom) and node.module
    }
    forbidden = {"urllib", "http", "requests", "httpx", "aiohttp", "socket"}
    assert not (imported & forbidden), f"outbound-capable import: {imported & forbidden}"
    assert "deepen" not in src.split('"""', 2)[2], (
        "the inspector consults no oracle — a gate that asks Hex is not a gate"
    )

    print("build_inspector proofs: all teeth green")


if __name__ == "__main__":
    main()

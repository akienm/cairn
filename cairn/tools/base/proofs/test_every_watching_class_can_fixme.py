"""Proof: every node class that can carry a WATCHME and builds can be sent back to FIXME.

Ticket 5f217a2d4bd6 (2026-10-03). Akien's answer to open-291189a9766a: a WATCHME that cannot name
its receiver "is a fault and goes back for fixing" — and the answer names no class exception.
Ticket 72d2f79daf0a gave code-seam v2 the edge; skill v2, bug v1 and concept-piece v1 carry
WATCHME too and had none, so the watch verb answered 18693659d16b (skill@v2) with
"IllegalTransition: 'FIXME' is not in the skill@v2 vocabulary" (measured 2026-10-03).

Teeth, one per falsifier clause:

  1. A census over the LIVE node classes finds no version that carries WATCHME in
     free_summons and BUILDME on its path without repair_summons {"FIXME": "BUILDME"}.
  2. On each such live class, a back-edge into FIXME from PROVEME lands at FIXME placed
     immediately before BUILDME — the reader is class-agnostic, measured not read.

The classes are read LIVE (no fixture copy), because the build IS the live class write:
reverting it must red tooth 1. host-seam v1 carries WATCHME with no BUILDME on its path and
is out of scope by construction (its own ticket carries the question of where it re-enters).

    python3 cairn/tools/base/proofs/test_every_watching_class_can_fixme.py   # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.base import transitions  # noqa: E402

PROVES = {
    "5f217a2d4bd6": {
        "1": "test_every_watching_class_that_builds_declares_the_fixme_edge",
        "2": "test_a_back_edge_lands_at_fixme_on_every_watching_class",
    },
}

# Read where test_fixme reads the commons: beside the repo when it is there, else at the home
# path, so the teeth run the same in a hollow /tmp worktree.
_COMMONS_CLASSES = (transitions._NODE_CLASSES if transitions._NODE_CLASSES.is_dir()
                    else Path.home() / "dev" / "src" / "CairnCommons" / "node_classes")


def _watching_builders() -> list[tuple[str, str, dict]]:
    """(class, version, workflow) for every live version that can WATCHME and has BUILDME."""
    out = []
    for p in sorted(_COMMONS_CLASSES.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for ver, wf in (d.get("workflow_versions") or {}).items():
            if "WATCHME" in (wf.get("free_summons") or []) and "BUILDME" in (wf.get("path") or []):
                out.append((p.stem, ver, wf))
    return out


def test_every_watching_class_that_builds_declares_the_fixme_edge():
    found = _watching_builders()
    names = {f"{c}@{v}" for c, v, _ in found}
    # Non-hollow floor: the four the census measured on 2026-10-03 must all be in view, so a
    # glob that reads nothing cannot pass by finding nothing to check.
    assert {"code-seam@v2", "skill@v2", "bug@v1", "concept-piece@v1"} <= names, names
    lacking = [f"{c}@{v}" for c, v, wf in found
               if (wf.get("repair_summons") or {}).get("FIXME") != "BUILDME"]
    assert not lacking, f"can carry WATCHME and builds, but cannot be sent back to FIXME: {lacking}"


def test_a_back_edge_lands_at_fixme_on_every_watching_class():
    from cairn.tools.base.transitions import emit, parse_workflow
    from cairn.tools.charter import projector
    for cls, ver, wf in _watching_builders():
        path = list(wf["path"])
        i = path.index("PROVEME")
        at_proveme = f"{cls}@{ver}: " + " -> ".join(
            f"[{s}]" if n == i else s for n, s in enumerate(path))
        comp = scratch_dir(f"every_class_fixme_fixture_{cls}_") / "comp"
        comp.mkdir()
        hist, state = str(comp / "history.json"), str(comp / "state.json")
        new = emit(at_proveme, "FIXME", history_path=hist, state_path=state,
                   node_class_root=_COMMONS_CLASSES, ticket=f"every_class_fixme_fixture_{cls}",
                   missing=["the receiver is unnamed"])
        got = parse_workflow(new)
        assert got.here == "FIXME", (cls, new)
        assert got.cursor == got.path.index("BUILDME") - 1, (cls, new)
        assert projector.read_history(hist)[-1].get("direction") == "back", cls


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

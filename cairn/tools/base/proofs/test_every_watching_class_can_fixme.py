"""Proof: every node class that can carry a WATCHME can be sent back to FIXME.

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

Ticket 3ee0d23164e6 (2026-11-11) widens both teeth from "carries WATCHME and builds" to
"carries WATCHME": host-seam v1 carries WATCHME with no BUILDME on its path, and Akien's answer
to open-8bc1eaf1f568 ("a agreed") puts its FIXME before POCME, the host-seam's build-analogue.
Tooth 3 drives a host-seam@v1 fixture from WATCHME back to FIXME and forward out of it, and
measures that FIXME exits to POCME.

The classes are read LIVE (no fixture copy), because the build IS the live class write:
reverting it must red tooth 1.

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
    "3ee0d23164e6": {
        "all": "test_a_host_seam_watch_fault_goes_back_to_fixme_and_out_to_pocme",
    },
}

# Where each watching class's FIXME re-enters: BUILDME wherever the path builds
# (5f217a2d4bd6), POCME for host-seam (Akien's answer to open-8bc1eaf1f568).
_ANCHOR = {"host-seam": "POCME"}

# Read where test_fixme reads the commons: beside the repo when it is there, else at the home
# path, so the teeth run the same in a hollow /tmp worktree.
_COMMONS_CLASSES = (transitions._NODE_CLASSES if transitions._NODE_CLASSES.is_dir()
                    else Path.home() / "dev" / "src" / "CairnCommons" / "node_classes")


def _watching_classes() -> list[tuple[str, str, dict]]:
    """(class, version, workflow) for every live version that can carry a WATCHME."""
    out = []
    for p in sorted(_COMMONS_CLASSES.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for ver, wf in (d.get("workflow_versions") or {}).items():
            if "WATCHME" in (wf.get("free_summons") or []):
                out.append((p.stem, ver, wf))
    return out


def _anchor(cls: str) -> str:
    return _ANCHOR.get(cls, "BUILDME")


def test_every_watching_class_that_builds_declares_the_fixme_edge():
    found = _watching_classes()
    names = {f"{c}@{v}" for c, v, _ in found}
    # Non-hollow floor: the four the census measured on 2026-10-03 and host-seam must all be in
    # view, so a glob that reads nothing cannot pass by finding nothing to check.
    assert {"code-seam@v2", "skill@v2", "bug@v1", "concept-piece@v1", "host-seam@v1"} <= names, names
    lacking = [f"{c}@{v}" for c, v, wf in found
               if (wf.get("repair_summons") or {}).get("FIXME") != _anchor(c)
               or _anchor(c) not in (wf.get("path") or [])]
    assert not lacking, f"can carry WATCHME, but cannot be sent back to FIXME: {lacking}"


def test_a_back_edge_lands_at_fixme_on_every_watching_class():
    from cairn.tools.base.transitions import emit, parse_workflow
    from cairn.tools.charter import projector
    for cls, ver, wf in _watching_classes():
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
        assert got.cursor == got.path.index(_anchor(cls)) - 1, (cls, new)
        assert projector.read_history(hist)[-1].get("direction") == "back", cls


def test_a_host_seam_watch_fault_goes_back_to_fixme_and_out_to_pocme():
    """A host-seam@v1 ticket resting at WATCHME is sent back (the act the watch verb does on
    holds=False, through Ticket.failed -> emit): the cursor lands at [FIXME], placed directly
    before POCME, and the next forward crossing out of FIXME lands at POCME."""
    from cairn.tools.base.transitions import emit, parse_workflow
    from cairn.tools.charter import projector
    at_watch = ("host-seam@v1: THINKME -> TICKETME -> RESEARCHME -> POCME -> PROVEME -> "
                "[WATCHME(the host still holds)] -> PROVED")
    comp = scratch_dir("host_seam_fixme_fixture_") / "comp"
    comp.mkdir()
    hist, state = str(comp / "history.json"), str(comp / "state.json")
    tid = "host_seam_fixme_fixture"
    back = emit(at_watch, "FIXME", history_path=hist, state_path=state,
                node_class_root=_COMMONS_CLASSES, ticket=tid,
                missing=["[watchme] the receiver is unnamed"])
    got = parse_workflow(back)
    assert got.here == "FIXME", back
    assert got.path[got.cursor + 1] == "POCME", back
    assert projector.read_history(hist)[-1].get("direction") == "back", back
    # The FIXME gate reads the ticket off disk and admits the exit once every entry is answered
    # at or after the kick-back (the test_a_fixme_answer_binds_to_its_kick_back.py fixture).
    from datetime import datetime
    from cairn.tools.base import ticket_file
    kicked = datetime.fromisoformat(projector.read_history(hist)[-1]["at"]).astimezone()
    tickets = scratch_dir("host_seam_fixme_fixture_tickets_")
    (tickets / f"{tid}.json").write_text(json.dumps({
        "fixme": ["[watchme] the receiver is unnamed"],
        "decisions": [{"step": "FIXME 1", "text": "the receiver is named",
                       "at": kicked.isoformat(timespec="seconds")}]}), encoding="utf-8")
    saved, ticket_file._TICKETS = ticket_file._TICKETS, tickets
    try:
        out = emit(back, "POCME", history_path=hist, state_path=state,
                   node_class_root=_COMMONS_CLASSES, ticket=tid)
    finally:
        ticket_file._TICKETS = saved
    assert parse_workflow(out).here == "POCME", out
    assert projector.read_history(hist)[-1].get("direction") == "forward", out


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

"""Proof for ticket ee9637b02525 — a crossing made by a sail verb leaves its records committed.

Measured 2026-11-19: ``sail.py cross <id> FIXME|SUPERSEDED`` crosses through ``tools/base/cross.py``
-> ``transitions.emit``, which appends to the component's history.json and state.json and commits
nothing; only close.sh ever committed those. So after its crossing ``sail.cross`` commits the
crossed component's two records through the ticket machine's published helper
(``commit_crossing_records``, ticket 79875eb17ac2).

The world is a scratch git repo holding the component (``comp/``, with its charter) and another
ticket's dirty records (``other/``), and a scratch tickets store; the house tree is never touched.

    python3 cairn/devices/cc/proofs/test_a_crossing_made_by_a_sail_verb_leaves_its_records_committed.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"ee9637b02525": {
    "1": "test_a_sail_cross_to_a_disposition_or_fixme_leaves_its_records_committed",
    "2": "test_another_tickets_dirt_is_not_committed_by_a_sail_cross",
}}

_TID = "fixtureee96a"
_LIVE_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"
_CLASSES = _LIVE_STORE_CHARTER.parents[1] / "node_classes"


def _wf(cursor: str) -> str:
    steps = ["THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"]
    return "code-seam@v2: " + " -> ".join(f"[{s}]" if s == cursor else s for s in steps)


def _git(cwd, *args) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    out = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=env)
    assert out.returncode == 0, f"git {args}: {out.stderr}"
    return out.stdout


@contextmanager
def _world():
    """comp/ (charter + records, committed) and other/ (dirty) in a scratch repo; a scratch
    commons whose tickets dir holds one ticket at BUILDME owned by comp's charter."""
    import cairn.tools.base.ticket_file as tf
    import cairn.tools.base.transitions as tr
    tmp = scratch_dir("tee96-sail-")
    repo = tmp / "repo"
    (repo / "comp").mkdir(parents=True)
    (repo / "other").mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "proof@example.invalid")
    _git(repo, "config", "user.name", "proof")
    (repo / "comp" / "intention+why.json").write_text("{}\n")
    for d in ("comp", "other"):
        (repo / d / "history.json").write_text("[]\n")
        (repo / d / "state.json").write_text("{}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "baseline")
    (repo / "other" / "history.json").write_text('[{"standing": "someone else, uncommitted"}]\n')
    commons = tmp / "commons"
    store = commons / "tickets"
    store.mkdir(parents=True)
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "comp/intention+why.json",
                                "workflow_and_state": _wf("BUILDME"), "decisions": []},
                               indent=2) + "\n", encoding="utf-8", newline="\n")
    saved = (tf._TICKETS, tr._REPO_ROOT, tr._NODE_CLASSES)
    tf._TICKETS, tr._REPO_ROOT, tr._NODE_CLASSES = store, repo, _CLASSES
    try:
        yield {"repo": repo, "store": store}
    finally:
        tf._TICKETS, tr._REPO_ROOT, tr._NODE_CLASSES = saved
        shutil.rmtree(tmp, ignore_errors=True)


def _sail_cross(w, target, **kw) -> int:
    import cairn.devices.cc.scripts.sail as sail
    errs: list[str] = []
    rc = sail.cross(_TID, target, why="fixture crossing", tickets_dir=w["store"],
                    out=lambda s: None, err=errs.append, **kw)
    assert rc == 0, f"sail.cross refused: {errs}"
    return rc


def _dirty(w) -> list[str]:
    return [ln[3:].strip() for ln in _git(w["repo"], "status", "--porcelain").splitlines()]


def test_a_sail_cross_to_a_disposition_or_fixme_leaves_its_records_committed():
    """Clause 1: after sail cross lands FIXME (and, separately, SUPERSEDED), comp's two records
    are committed and clean."""
    for target, kw in (("FIXME", {"missing": ["clause 2 has no tooth"]}), ("SUPERSEDED", {})):
        with _world() as w:
            before = _git(w["repo"], "rev-list", "--count", "HEAD").strip()
            _sail_cross(w, target, **kw)
            dirty = _dirty(w)
            assert not [d for d in dirty if d.startswith("comp/")], f"{target}: comp dirty: {dirty}"
            assert _git(w["repo"], "rev-list", "--count", "HEAD").strip() != before, \
                f"{target}: no commit made"
            assert "comp/history.json" in _git(w["repo"], "show", "--name-only", "--format=", "HEAD")
    print("ok test_a_sail_cross_to_a_disposition_or_fixme_leaves_its_records_committed")


def test_another_tickets_dirt_is_not_committed_by_a_sail_cross():
    """Clause 2: other/ stays dirty and out of the commit."""
    with _world() as w:
        _sail_cross(w, "FIXME", missing=["x"])
        assert "other/history.json" in _dirty(w), "other's dirt was committed"
        shown = _git(w["repo"], "show", "--name-only", "--format=", "HEAD")
        assert "other/" not in shown, f"the commit carried other's records: {shown}"
    print("ok test_another_tickets_dirt_is_not_committed_by_a_sail_cross")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))

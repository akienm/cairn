"""Proof for ticket 2955a4a316d3 — a clearance refusal that sends a boat to FIXME leaves its records committed.

Measured 2026-11-19: ``_send_to_fixme`` (clearance.py) calls ``transitions.emit`` directly, not
``Ticket.failed``, so nothing committed the crossing it wrote. It stays off ``Ticket.failed``
because Akien's ruling (2026-10-01, ticket 973574dddb77) is that a coverage refusal raises no
ticket trouble and ``Ticket.failed`` raises one. So it calls the ticket machine's published
``commit_crossing_records`` (ticket 79875eb17ac2) after its emit.

The world is a scratch git repo holding the boat's component (``comp/``) and another ticket's
dirty records (``other/``), plus a scratch commons tickets dir; nothing touches the house tree.

    python3 cairn/devices/codemother/machines/clearance/proofs/test_a_clearance_refusal_to_fixme_leaves_its_records_committed.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"2955a4a316d3": {
    "1": "test_a_refusal_to_fixme_leaves_its_records_committed",
    "2": "test_the_refusal_still_raises_no_trouble_and_writes_the_lacks",
    "3": "test_another_tickets_dirt_is_not_committed_by_the_refusal",
}}

_TID = "fixture2955a"
_WF = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> [PROVEME] -> PROVED"
_LACKS = [{"kind": "coverage", "why": "clause 2 has no tooth"}]
_LIVE_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"

# a run in a worktree with no CairnCommons beside it reads the class table from the home checkout
if not (_REPO_ROOT.parent / "CairnCommons").is_dir():
    from cairn.tools.base import transitions as _transitions
    _transitions._NODE_CLASSES = _LIVE_STORE_CHARTER.parents[1] / "node_classes"
    for _fn in (_transitions.emit, _transitions.load_class_def):
        for _k in ("node_class_root", "root"):
            if _k in (_fn.__kwdefaults__ or {}):
                _fn.__kwdefaults__[_k] = _LIVE_STORE_CHARTER.parents[1] / "node_classes"


def _git(cwd, *args) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    out = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=env)
    assert out.returncode == 0, f"git {args}: {out.stderr}"
    return out.stdout


@contextmanager
def _world():
    """A scratch git repo (comp/ the boat's component, other/ dirty) and a scratch commons whose
    tickets dir holds the boat's ticket; ``_crossing_roots`` is pointed at it."""
    import cairn.devices.codemother.machines.clearance.clearance as cl
    tmp = scratch_dir("t2955-fixme-")
    repo = tmp / "repo"
    (repo / "comp").mkdir(parents=True)
    (repo / "other").mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "proof@example.invalid")
    _git(repo, "config", "user.name", "proof")
    for d in ("comp", "other"):
        (repo / d / "history.json").write_text("[]\n")
        (repo / d / "state.json").write_text("{}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "baseline")
    (repo / "other" / "history.json").write_text('[{"standing": "someone else, uncommitted"}]\n')
    commons = tmp / "commons"
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    shutil.copy(_LIVE_STORE_CHARTER, tickets / "_charter+why.json")
    plan = tickets / f"{_TID}-a-fixture-boat.json"
    plan.write_text(json.dumps({"id": _TID, "workflow_and_state": _WF, "decisions": []},
                               indent=2) + "\n", encoding="utf-8", newline="\n")
    was = cl._crossing_roots
    cl._crossing_roots = lambda: {"commons": str(commons)}
    try:
        yield {"repo": repo, "plan": plan, "cl": cl,
               "history": str(repo / "comp" / "history.json"),
               "state": str(repo / "comp" / "state.json")}
    finally:
        cl._crossing_roots = was
        shutil.rmtree(tmp, ignore_errors=True)


def _dirty(w) -> list[str]:
    return [ln[3:].strip() for ln in _git(w["repo"], "status", "--porcelain").splitlines()]


def test_a_refusal_to_fixme_leaves_its_records_committed():
    """Clause 1: after the refusal sends the boat to FIXME, comp's history.json and state.json
    are committed and clean."""
    with _world() as w:
        before = _git(w["repo"], "rev-list", "--count", "HEAD").strip()
        w["cl"]._send_to_fixme(_WF, _TID, _LACKS, actor="codemother",
                               history_path=w["history"], state_path=w["state"])
        dirty = _dirty(w)
        assert not [d for d in dirty if d.startswith("comp/")], f"comp left dirty: {dirty}"
        assert _git(w["repo"], "rev-list", "--count", "HEAD").strip() != before, "no commit made"
        assert "comp/history.json" in _git(w["repo"], "show", "--name-only", "--format=", "HEAD")
    print("ok test_a_refusal_to_fixme_leaves_its_records_committed")


def test_the_refusal_still_raises_no_trouble_and_writes_the_lacks():
    """Clause 2: still no ticket trouble (973574dddb77), and the lacks still land on the ticket."""
    import cairn.tools.base.diagnostic as diag
    import cairn.tools.base.ticket_file as tf
    seen: list[dict] = []
    real_rewrite, real_raise = tf.rewrite_ticket, diag.DiagnosticBase.raise_trouble

    def spy(plan, doc, **kw):
        seen.append(doc)
        return real_rewrite(plan, doc, **kw)

    def no_trouble(self, identity, **kw):
        raise AssertionError(f"the refusal raised a trouble: {identity}")

    tf.rewrite_ticket, diag.DiagnosticBase.raise_trouble = spy, no_trouble
    try:
        with _world() as w:
            w["cl"]._send_to_fixme(_WF, _TID, _LACKS, actor="codemother",
                                   history_path=w["history"], state_path=w["state"])
    finally:
        tf.rewrite_ticket, diag.DiagnosticBase.raise_trouble = real_rewrite, real_raise
    assert seen, "the refusal never wrote the ticket"
    fixme = seen[-1].get("fixme") or []
    assert fixme == [{"n": 1, "kind": "coverage", "missing": "clause 2 has no tooth"}], seen[-1]
    print("ok test_the_refusal_still_raises_no_trouble_and_writes_the_lacks")


def test_another_tickets_dirt_is_not_committed_by_the_refusal():
    """Clause 3: other/ stays dirty and out of the commit."""
    with _world() as w:
        w["cl"]._send_to_fixme(_WF, _TID, _LACKS, actor="codemother",
                               history_path=w["history"], state_path=w["state"])
        assert "other/history.json" in _dirty(w), "other's dirt was committed"
        shown = _git(w["repo"], "show", "--name-only", "--format=", "HEAD")
        assert "other/" not in shown, f"the commit carried other's records: {shown}"
    print("ok test_another_tickets_dirt_is_not_committed_by_the_refusal")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))

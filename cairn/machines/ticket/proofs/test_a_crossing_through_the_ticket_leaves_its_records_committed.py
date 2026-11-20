"""Proof for ticket 79875eb17ac2 — a crossing through the ticket machine leaves its records committed.

Measured 2026-11-19 on akiendell: five crossings (tester seq 408, codemother seq 172, verdict
seq 32, chart_gate seq 9 and 10) sat as uncommitted history.json / state.json dirt, because the
only committer of a crossing's records was close.sh at a close. Three of them came through
``Ticket.failed`` (chart_gate/gate.py ``_fail``), none from sail.py. So the ticket machine
commits the crossed component's two files itself, at the end of ``Ticket.passed`` and
``Ticket.failed``, through one published helper, ``commit_crossing_records``.

The world is a scratch git repo holding a component (``comp/``) and another ticket's dirty
records (``other/``), and a scratch tickets store; nothing touches the house tree.

    python3 cairn/machines/ticket/proofs/test_a_crossing_through_the_ticket_leaves_its_records_committed.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

from cairn.tools.scratch.scratch import scratch_dir

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"79875eb17ac2": {
    "1": "test_a_failed_ticket_leaves_its_records_committed",
    "2": "test_a_passed_ticket_leaves_its_records_committed",
    "3": "test_another_tickets_dirt_is_not_committed",
    "4": "test_append_entry_still_makes_no_git_call",
    "5": "test_the_helper_is_published_and_commits_only_the_two_files",
}}

_TID = "fixture79875"
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


def _wf(cursor: str) -> str:
    steps = ["THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED"]
    return "code-seam@v2: " + " -> ".join(f"[{s}]" if s == cursor else s for s in steps)


class _Spy:
    def request(self, **kw):
        raise AssertionError(f"a crossing asked something: {kw}")

    def post(self, *, to, **_):
        return {"id": "post"}


def _git(cwd, *args) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    out = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=env)
    assert out.returncode == 0, f"git {args}: {out.stderr}"
    return out.stdout


@contextmanager
def _world(cursor: str):
    """A scratch git repo: ``comp/`` the crossed component, ``other/`` another ticket's records
    left dirty, and a scratch tickets store holding one ticket at ``cursor``."""
    import cairn.tools.base.ticket_file as tf
    tmp = scratch_dir("t79-crossing-")
    repo = tmp / "repo"
    (repo / "comp").mkdir(parents=True)
    (repo / "other").mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "proof@example.invalid")
    _git(repo, "config", "user.name", "proof")
    (repo / "comp" / "history.json").write_text("[]\n")
    (repo / "comp" / "state.json").write_text("{}\n")
    (repo / "other" / "history.json").write_text("[]\n")
    (repo / "other" / "state.json").write_text("{}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "baseline")
    (repo / "other" / "history.json").write_text('[{"standing": "someone else, uncommitted"}]\n')
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "cairn/machines/ticket/intention+why.json"},
                               indent=2) + "\n")
    tf.state_path(plan).write_text(json.dumps({"workflow_and_state": _wf(cursor),
                                               "node_class": "code-seam"}, indent=2) + "\n")
    roots = {k: tmp / k for k in ("repo_root", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    was = tf._TICKETS
    tf._TICKETS = store
    try:
        yield {"tmp": tmp, "repo": repo, "store": store, "plan": plan, "roots": roots,
               "history": str(repo / "comp" / "history.json"),
               "state": str(repo / "comp" / "state.json")}
    finally:
        tf._TICKETS = was
        shutil.rmtree(tmp, ignore_errors=True)


def _ticket(w):
    from cairn.machines.ticket.ticket import Ticket
    return Ticket.at(_TID, tickets_dir=w["store"], roots=w["roots"])


def _dirty(w) -> list[str]:
    return [ln[3:].strip() for ln in _git(w["repo"], "status", "--porcelain").splitlines()]


def test_a_failed_ticket_leaves_its_records_committed():
    """Clause 1: Ticket.failed to FIXME (the chart gate's _fail path) leaves comp's history and
    state committed, and the tree clean of them."""
    with _world("BUILDME") as w:
        before = _git(w["repo"], "rev-list", "--count", "HEAD").strip()
        _ticket(w).failed([{"kind": "coverage", "why": "clause 2 has no tooth"}],
                          participant=_Spy(), history_path=w["history"], state_path=w["state"],
                          actor="codemother", why="fixture fail")
        dirty = _dirty(w)
        assert not [d for d in dirty if d.startswith("comp/")], f"comp left dirty: {dirty}"
        assert _git(w["repo"], "rev-list", "--count", "HEAD").strip() != before, "no commit made"
        assert "comp/history.json" in _git(w["repo"], "show", "--name-only", "--format=", "HEAD")
    print("ok test_a_failed_ticket_leaves_its_records_committed")


def test_a_passed_ticket_leaves_its_records_committed():
    """Clause 2: Ticket.passed forward leaves comp's history and state committed."""
    with _world("THINKME") as w:
        before = _git(w["repo"], "rev-list", "--count", "HEAD").strip()
        _ticket(w).passed("TICKETME", participant=_Spy(), history_path=w["history"],
                          state_path=w["state"], actor="cc", why="fixture pass")
        dirty = _dirty(w)
        assert not [d for d in dirty if d.startswith("comp/")], f"comp left dirty: {dirty}"
        assert _git(w["repo"], "rev-list", "--count", "HEAD").strip() != before, "no commit made"
    print("ok test_a_passed_ticket_leaves_its_records_committed")


def test_another_tickets_dirt_is_not_committed():
    """Clause 3: other/ stays dirty and uncommitted through both crossings."""
    for cursor, how in (("BUILDME", "failed"), ("THINKME", "passed")):
        with _world(cursor) as w:
            t = _ticket(w)
            if how == "failed":
                t.failed([{"kind": "coverage", "why": "x"}], participant=_Spy(),
                         history_path=w["history"], state_path=w["state"], actor="cc", why="f")
            else:
                t.passed("TICKETME", participant=_Spy(), history_path=w["history"],
                         state_path=w["state"], actor="cc", why="f")
            assert "other/history.json" in _dirty(w), f"{how}: other's dirt was committed"
            shown = _git(w["repo"], "show", "--name-only", "--format=", "HEAD")
            assert "other/" not in shown, f"{how}: the commit carried other's records: {shown}"
    print("ok test_another_tickets_dirt_is_not_committed")


def test_append_entry_still_makes_no_git_call():
    """Clause 4: the append door writes and runs no git: after it, comp is dirty, not committed."""
    from cairn.tools.charter import projector
    with _world("BUILDME") as w:
        before = _git(w["repo"], "rev-list", "--count", "HEAD").strip()
        projector.append_entry(w["history"], w["state"], {"id": "w", "standing": "BUILDME"})
        assert _git(w["repo"], "rev-list", "--count", "HEAD").strip() == before, "append committed"
        assert any(d.startswith("comp/") for d in _dirty(w)), "append left comp clean: it ran git"
    print("ok test_append_entry_still_makes_no_git_call")


def test_the_helper_is_published_and_commits_only_the_two_files():
    """Clause 5: named in the ticket charter's public_interface; called alone it commits only
    the component's history.json and state.json."""
    from cairn.machines.ticket import ticket as mod
    charter = json.loads((_REPO_ROOT / "cairn" / "machines" / "ticket"
                          / "intention+why.json").read_text(encoding="utf-8"))
    assert "cairn.machines.ticket.ticket.commit_crossing_records" in charter["public_interface"], \
        charter["public_interface"]
    with _world("BUILDME") as w:
        (Path(w["repo"]) / "comp" / "history.json").write_text('[{"standing": "x"}]\n')
        (Path(w["repo"]) / "comp" / "notes.txt").write_text("not a crossing record\n")
        sha = mod.commit_crossing_records(w["history"], w["state"], "fixture")
        assert sha, "nothing committed"
        shown = _git(w["repo"], "show", "--name-only", "--format=", "HEAD").split()
        assert shown == ["comp/history.json"], shown
        dirty = _dirty(w)
        assert "comp/notes.txt" in dirty and "other/history.json" in dirty, dirty
    print("ok test_the_helper_is_published_and_commits_only_the_two_files")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))

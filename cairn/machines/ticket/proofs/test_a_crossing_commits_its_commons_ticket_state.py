"""Proof for ticket db1475029939 — a crossing also commits the ticket's commons state file.

Measured 2026-11-19: ``Ticket.passed`` and ``Ticket.failed`` rewrite the ticket's
``<id>-<slug>.state.json`` in the commons, and ticket 79875eb17ac2 commits only the crossed
component's history.json and state.json. The commons state file was left as dirt on one disk
until someone committed it by hand.

The world is two scratch git repos: ``repo`` (the component, as in 79875's proof) and
``commons`` (holding ``tickets/`` and another ticket's dirty file). Nothing touches the house.

    python3 cairn/machines/ticket/proofs/test_a_crossing_commits_its_commons_ticket_state.py
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

PROVES = {"db1475029939": {
    "1": "test_a_crossing_leaves_the_commons_state_committed",
    "2": "test_another_tickets_commons_dirt_is_not_committed",
    "3": "test_a_scratch_commons_outside_git_does_not_raise",
}}

_TID = "fixturedb147"
_LIVE_STORE_CHARTER = _REPO_ROOT.parent / "CairnCommons" / "tickets" / "_charter+why.json"
if not _LIVE_STORE_CHARTER.is_file():
    _LIVE_STORE_CHARTER = Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json"

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


def _init(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "proof@example.invalid")
    _git(repo, "config", "user.name", "proof")


@contextmanager
def _world(cursor: str, commons_in_git: bool = True):
    """A component repo and a commons store holding one ticket at ``cursor``. With
    ``commons_in_git`` the commons is its own git repo (the ticket's state tracked, another
    ticket's file left dirty); without, it is a bare scratch directory."""
    import cairn.tools.base.ticket_file as tf
    tmp = scratch_dir("tdb147-crossing-")
    repo = tmp / "repo"
    (repo / "comp").mkdir(parents=True)
    _init(repo)
    (repo / "comp" / "history.json").write_text("[]\n")
    (repo / "comp" / "state.json").write_text("{}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "baseline")
    commons = tmp / "cmrepo"
    store = commons / "tickets"
    store.mkdir(parents=True)
    shutil.copy(_LIVE_STORE_CHARTER, store / "_charter+why.json")
    plan = store / f"{_TID}-a-fixture-ticket.json"
    plan.write_text(json.dumps({"id": _TID, "title": "a fixture ticket",
                                "owning_intention": "cairn/machines/ticket/intention+why.json"},
                               indent=2) + "\n")
    other = store / "aaaaaaaaaaaa-another-ticket.state.json"
    other.write_text("{}\n")
    tf.state_path(plan).write_text(json.dumps({"workflow_and_state": _wf(cursor),
                                               "node_class": "code-seam"}, indent=2) + "\n")
    if commons_in_git:
        _init(commons)
        _git(commons, "add", "-A")
        _git(commons, "commit", "-q", "-m", "baseline")
        other.write_text('{"standing": "someone else, uncommitted"}\n')
    roots = {k: tmp / k for k in ("repo_root", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    was = tf._TICKETS
    tf._TICKETS = store
    try:
        yield {"tmp": tmp, "repo": repo, "commons": commons, "store": store, "plan": plan,
               "roots": roots, "other": other,
               "history": str(repo / "comp" / "history.json"),
               "state": str(repo / "comp" / "state.json")}
    finally:
        tf._TICKETS = was
        shutil.rmtree(tmp, ignore_errors=True)


def _ticket(w):
    from cairn.machines.ticket.ticket import Ticket
    return Ticket.at(_TID, tickets_dir=w["store"], roots=w["roots"])


def _cross(w, how: str) -> None:
    t = _ticket(w)
    if how == "failed":
        t.failed([{"kind": "coverage", "why": "x"}], participant=_Spy(), history_path=w["history"],
                 state_path=w["state"], actor="cc", why="fixture fail")
    else:
        t.passed("TICKETME", participant=_Spy(), history_path=w["history"],
                 state_path=w["state"], actor="cc", why="fixture pass")


def _dirty(root) -> list[str]:
    return [ln[3:].strip() for ln in _git(root, "status", "--porcelain").splitlines()]


def test_a_crossing_leaves_the_commons_state_committed():
    """Clause 1: after passed or failed, the ticket's state file is clean in the commons and a
    commons commit names it."""
    for cursor, how in (("THINKME", "passed"), ("BUILDME", "failed")):
        with _world(cursor) as w:
            before = _git(w["commons"], "rev-list", "--count", "HEAD").strip()
            base = _git(w["commons"], "rev-parse", "HEAD").strip()
            _cross(w, how)
            state_rel = f"tickets/{_TID}-a-fixture-ticket.state.json"
            assert state_rel not in _dirty(w["commons"]), f"{how}: commons state left dirty"
            assert _git(w["commons"], "rev-list", "--count", "HEAD").strip() != before, \
                f"{how}: no commons commit"
            shown = _git(w["commons"], "log", "--name-only", "--format=", f"{base}..HEAD")
            assert state_rel in shown, f"{how}: no commons commit names the state file: {shown}"
    print("ok test_a_crossing_leaves_the_commons_state_committed")


def test_another_tickets_commons_dirt_is_not_committed():
    """Clause 2: another ticket's dirty file in the same commons stays dirty and uncommitted."""
    for cursor, how in (("THINKME", "passed"), ("BUILDME", "failed")):
        with _world(cursor) as w:
            base = _git(w["commons"], "rev-parse", "HEAD").strip()
            _cross(w, how)
            assert "tickets/aaaaaaaaaaaa-another-ticket.state.json" in _dirty(w["commons"]), \
                f"{how}: another ticket's dirt was committed"
            shown = _git(w["commons"], "log", "--name-only", "--format=", f"{base}..HEAD")
            assert "aaaaaaaaaaaa" not in shown, f"{how}: a commit carried other's file: {shown}"
    print("ok test_another_tickets_commons_dirt_is_not_committed")


def test_a_scratch_commons_outside_git_does_not_raise():
    """Clause 3: a ticket whose commons sits in no git work tree crosses without raising."""
    for cursor, how in (("THINKME", "passed"), ("BUILDME", "failed")):
        with _world(cursor, commons_in_git=False) as w:
            _cross(w, how)
    print("ok test_a_scratch_commons_outside_git_does_not_raise")


if __name__ == "__main__":
    fails = 0
    for fn in (test_a_crossing_leaves_the_commons_state_committed,
               test_another_tickets_commons_dirt_is_not_committed,
               test_a_scratch_commons_outside_git_does_not_raise):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print(f"FAIL {fn.__name__}: {type(exc).__name__}: {exc}")
    sys.exit(1 if fails else 0)

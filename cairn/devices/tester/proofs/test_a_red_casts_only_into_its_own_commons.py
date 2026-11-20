"""Proof for ticket 58e242c8be4f: a tester run casts reds only into its own checkout's commons.

Measured 2026-11-19: a reseal in worktree wt-93fa, whose CairnCommons was a symlink to the house
commons, cast red ticket 1d547c70f1c3 into the house commons and blocked four PROVED closes
(withdrawn at CairnCommons 271e3e32). Law 6: the house commons is not a worktree run's to write.

Fixture, all marked testing: a scratch git repo (the checkout) beside a CairnCommons that is a
symlink to a second scratch git commons (the "house"); the tester's roots point through the
symlink, the way a worktree's derived store does.

  1. ticket_what_is_new over a red raises StoreUnreachable naming the symlink and its target,
     and the house gains no file;
  2. in the same symlinked setup, cast_ticket through the symlinked store lands (the tester's own
     doc, cast by the door directly), so only red casting is guarded and the deliberate symlink
     setups of the chart doors and hollow runs keep working.

    bin/cairn test cairn/devices/tester/proofs/test_a_red_casts_only_into_its_own_commons.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import types
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"58e242c8be4f": {
    "1": "test_a_red_through_a_symlinked_commons_casts_nothing_there",
    "2": "test_a_cast_through_the_same_symlinked_store_lands"}}

RED = "cairn/a/proofs/test_a.py"


def _git(where: Path, *args: str) -> str:
    got = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True)
    assert got.returncode == 0, (args, got.stderr)
    return got.stdout.strip()


def _world(tag: str, monkeypatch) -> types.SimpleNamespace:
    from cairn.devices.tester import red_tickets
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    from cairn.tools.base import transitions
    top = Path(scratch_dir(f"testing-58e2-{tag}-"))
    repo, house, link = top / "repo", top / "house" / "CairnCommons", top / "CairnCommons"
    (repo / "cairn" / "a" / "proofs").mkdir(parents=True)
    (repo / "cairn" / "a" / "intention+why.json").write_text(json.dumps({"component": "a"}),
                                                             encoding="utf-8")
    (repo / RED).write_text('"""testing: a proof that reds."""\nraise SystemExit(1)\n', encoding="utf-8")
    for cmd in (["init", "-q"], ["add", "-A"]):
        _git(repo, *cmd)
    (house / "tickets").mkdir(parents=True)
    live = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    shutil.copyfile(live, house / "tickets" / "_charter+why.json")
    for cmd in (["init", "-q"], ["config", "user.name", "testing"],
                ["config", "user.email", "testing@invalid"], ["add", "-A"],
                ["commit", "-q", "-m", "testing: the store charter"]):
        _git(house, *cmd)
    link.symlink_to(house, target_is_directory=True)   # the worktree's CairnCommons -> the house
    tickets = link / "tickets"
    monkeypatch.setattr(red_tickets, "ROOTS", {
        "repo": repo, "tickets": tickets, "commons": link, "berths": top / "berths",
        "trace": top / "trace",
        "raiser": {"repo": top / "world", "commons": top / "world", "instance": top / "world"}})
    A.set_diagnostic_roots({"CairnCommons": house, "cairn": repo})
    monkeypatch.setenv(transitions.PROOF_ENV, "testing-58e242c8be4f")
    return types.SimpleNamespace(top=top, repo=repo, house=house, link=link, tickets=tickets)


def _files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(root).parts}


def _restore():
    from cairn.tools.artifact import artifact as A
    A.set_diagnostic_roots(None)


def test_a_red_through_a_symlinked_commons_casts_nothing_there(monkeypatch):
    from cairn.devices.tester import red_tickets
    w = _world("red", monkeypatch)
    try:
        before = _files(w.house)
        try:
            red_tickets.ticket_what_is_new([{"proof": str(w.repo / RED), "verdict": "red"}])
        except red_tickets.StoreUnreachable as exc:
            said = str(exc)
        else:
            raise AssertionError("a red through a symlinked commons was not refused")
        assert str(w.link) in said and str(w.house.resolve()) in said, said
        assert _files(w.house) == before, sorted(_files(w.house) - before)
    finally:
        _restore()


def test_a_cast_through_the_same_symlinked_store_lands(monkeypatch):
    from cairn.devices.tester import red_tickets
    w = _world("cast", monkeypatch)
    try:
        item = red_tickets.red_keys([{"proof": str(w.repo / RED), "verdict": "red"}], w.repo)[0]
        plan, _ = red_tickets._cast(item, w.repo.resolve(), None, w.tickets)
        assert plan.is_file(), plan
        assert plan.resolve().parent == (w.house / "tickets").resolve(), plan.resolve()
    finally:
        _restore()


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

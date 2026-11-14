"""Proof for ticket 207c4074b3d5: each test run tickets every new red and orphaned file it finds.

Outline 9.4.2.3.7.5 (Akien 2026-11-13): "every test failure, every orphaned file, HAS TO BE FIXED
... reds don't get lost". cairn/devices/tester/red_tickets.py casts the tickets; run_proof calls
it on every red, and a whole-tree run calls it with scan_orphans=True.

Fixture: a scratch git repo holding component cairn/a (a red proof test_a.py, and a seal
validations/test_gone.json whose proof is gone) and cairn/stray/loose.py under no charter; a
scratch commons with the live store charter; scratch berth and trace roots. Every door is the
real one, pointed at scratch through red_tickets.ROOTS and artifact.set_diagnostic_roots.

  1. run_proof over the red proof and a red fixture, then a whole-tree call, casts exactly three
     tickets: the red, orphan (a) and orphan (b), each with its file in fixes and a sorted berth
     on disk (the fixture, which another proof runs to see a red, is never ticketed);
  2. the same run repeated casts nothing;
  3. a red whose proof an open ticket names in bounds.in casts nothing (and casts one without it);
  4. a cast the door refuses raises out of run_proof naming the refusal, and no ticket lands;
  5. what the run casts it commits in the same act (D7): the commons tree is clean after, a commit
     per call that cast carries every cast file, and the remote is where it was (nothing pushed);
  6. when the commons holds someone else's staged change, the run casts and commits nothing, the
     staged change is untouched, and each would-be cast lands as a tester trouble emission;
  7. (FIXME 1, measured 2026-11-14 on the Dell: every `bin/cairn test` from a worktree with no
     commons beside it died in run_proof's tail on RedTicketRefused "the ticket store ... is in
     no git tree") a red run whose ticket store is in no git tree returns its red record whole,
     casts nothing, and names on stderr that the red was not ticketed and why.

    bin/cairn test cairn/devices/tester/proofs/test_each_run_tickets_its_new_reds_and_orphans.py
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

PROVES = {"207c4074b3d5": {
    "1": "test_a_run_casts_one_ticket_per_red_and_orphan",
    "2": "test_the_same_run_repeated_casts_nothing",
    "3": "test_a_red_an_open_ticket_bounds_casts_nothing",
    "4": "test_a_refused_cast_raises_and_lands_nothing",
    "5": "test_a_cast_commits_in_the_same_act_and_does_not_push",
    "6": "test_staged_changes_from_another_hold_the_casts_as_troubles",
    "7": "test_a_store_in_no_git_tree_leaves_the_run_whole_and_says_so"}}

RED = "cairn/a/proofs/test_a.py"
ORPHAN_SEAL = "cairn/a/validations/test_gone.json"
ORPHAN_FILE = "cairn/stray/loose.py"
FIXTURE = "cairn/a/proofs/fixtures/red_proof.py"   # a fixture another proof runs: never ticketed
OPEN = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"


def _world(tag: str, monkeypatch) -> types.SimpleNamespace:
    from cairn.devices.tester import red_tickets
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    top = Path(scratch_dir(f"testing-207c-{tag}-"))
    repo, commons = top / "repo", top / "CairnCommons"
    (repo / "cairn" / "a" / "proofs").mkdir(parents=True)
    (repo / "cairn" / "a" / "validations").mkdir()
    (repo / "cairn" / "stray").mkdir()
    (repo / "cairn" / "a" / "proofs" / "fixtures").mkdir()
    (repo / FIXTURE).write_text('"""testing: a fixture that reds."""\nraise SystemExit(1)\n', encoding="utf-8")
    (repo / "cairn" / "a" / "intention+why.json").write_text(json.dumps({"component": "a"}), encoding="utf-8")
    (repo / RED).write_text('"""testing: a proof that reds."""\nraise SystemExit(1)\n', encoding="utf-8")
    (repo / ORPHAN_SEAL).write_text("[]\n", encoding="utf-8")
    (repo / ORPHAN_FILE).write_text("x = 1\n", encoding="utf-8")
    (repo / "cairn" / "__init__.py").write_text("", encoding="utf-8")   # plumbing, never an orphan
    for cmd in (["init", "-q"], ["add", "-A"]):
        subprocess.run(["git", "-C", str(repo), *cmd], check=True, capture_output=True)
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    live = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    shutil.copyfile(live, tickets / "_charter+why.json")
    remote = top / "remote.git"
    _git(top, "init", "-q", "--bare", str(remote))
    for cmd in (["init", "-q"], ["config", "user.name", "testing"],
                ["config", "user.email", "testing@invalid"], ["add", "-A"],
                ["commit", "-q", "-m", "testing: the store charter"],
                ["remote", "add", "origin", str(remote)], ["push", "-q", "origin", "HEAD:main"]):
        _git(commons, *cmd)
    raiser = {"repo": top / "world", "commons": top / "world", "instance": top / "world"}
    monkeypatch.setattr(red_tickets, "ROOTS", {"repo": repo, "tickets": tickets, "commons": commons,
                                               "berths": top / "berths", "trace": top / "trace",
                                               "raiser": raiser})
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": repo})
    # the casts' doors ask the inspector (transitions.ask_inspector); a proof's ask rides
    # inspect_wire's in-process scratch CodeMother, never the live one, whether or not the
    # run that started this proof handed it the tester's env (FIXME 1 of 207c4074b3d5:
    # measured 2026-11-14, a bare run from a worktree reached the house bus and was refused
    # BusStale in 5 of 6 teeth)
    from cairn.tools.base import transitions
    monkeypatch.setenv(transitions.PROOF_ENV, "testing-207c4074b3d5")
    return types.SimpleNamespace(top=top, repo=repo, commons=commons, tickets=tickets,
                                 remote=remote, raiser=raiser)


def _git(where: Path, *args: str) -> str:
    got = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True)
    assert got.returncode == 0, (args, got.stderr)
    return got.stdout.strip()


def _plans(w) -> list[Path]:
    from cairn.tools.base import ticket_file as tf
    return tf.plans(w.tickets)


def _run(w):
    """One whole run: the red proof through run_proof (its wiring tickets the red), then the
    whole-tree call that scans orphans."""
    from cairn.devices.tester import red_tickets
    from cairn.devices.tester.device import TesterDevice
    for proof in (RED, FIXTURE):
        record = TesterDevice().run_proof(w.repo / proof, sink="none", timeout=60)
        assert record["verdict"] == "red", (proof, record["verdict"])
    return red_tickets.ticket_what_is_new([], scan_orphans=True)


def _restore():
    from cairn.tools.artifact import artifact as A
    A.set_diagnostic_roots(None)


def test_a_run_casts_one_ticket_per_red_and_orphan(monkeypatch):
    from cairn.tools.base.ticket_file import read_ticket
    w = _world("cast", monkeypatch)
    try:
        _run(w)
        docs = [read_ticket(p) for p in _plans(w)]
        fixed = sorted(Path(f).resolve().relative_to(w.repo.resolve()).as_posix()
                       for d in docs for f in d["fixes"])
        assert fixed == sorted([RED, ORPHAN_SEAL, ORPHAN_FILE]), fixed
        for d in docs:
            assert Path(d["sorted_berth"]).is_file(), d["sorted_berth"]
            assert json.loads(Path(d["sorted_berth"]).read_text(encoding="utf-8"))["skill"] == "sorted"
        red = next(d for d in docs if d["fixes"][0].endswith(RED))
        assert "red:cairn/a/proofs/test_a.py::*" in red["measured"][0]["how"], red["measured"]
        assert red["owning_intention"] == "cairn/a/intention+why.json", red["owning_intention"]
    finally:
        _restore()


def test_the_same_run_repeated_casts_nothing(monkeypatch):
    w = _world("repeat", monkeypatch)
    try:
        _run(w)
        first = _plans(w)
        assert len(first) == 3, [p.name for p in first]
        again = _run(w)
        assert again == [] and _plans(w) == first, [p.name for p in _plans(w)]
    finally:
        _restore()


def _open_ticket(w, tid: str, bounds_in: list[str]) -> None:
    (w.tickets / f"{tid}-testing-an-open-ticket.json").write_text(json.dumps({
        "id": tid, "title": "testing an open ticket", "workflow_and_state": OPEN,
        "bounds": {"in": bounds_in, "out": []}}), encoding="utf-8")


def test_a_red_an_open_ticket_bounds_casts_nothing(monkeypatch):
    from cairn.devices.tester import red_tickets
    red = [{"proof": None, "verdict": "red"}]
    w = _world("bounds", monkeypatch)
    try:
        red[0]["proof"] = str(w.repo / RED)
        _open_ticket(w, "207c00000b01", [RED])
        assert red_tickets.ticket_what_is_new(red) == [], [p.name for p in _plans(w)]
        assert len(_plans(w)) == 1, [p.name for p in _plans(w)]
    finally:
        _restore()
    w2 = _world("unbound", monkeypatch)
    try:
        red[0]["proof"] = str(w2.repo / RED)
        _open_ticket(w2, "207c00000b02", ["cairn/a/elsewhere.py"])
        assert len(red_tickets.ticket_what_is_new(red)) == 1, "the unbound red cast nothing: " \
            "the bounded case would pass for the wrong reason"
    finally:
        _restore()


def test_a_refused_cast_raises_and_lands_nothing(monkeypatch):
    from cairn.devices.tester import red_tickets
    from cairn.devices.tester.device import TesterDevice
    w = _world("refused", monkeypatch)
    try:
        held = "207c00000c01"
        _open_ticket(w, held, ["cairn/a/elsewhere.py"])
        monkeypatch.setattr(red_tickets.uuid, "uuid4", lambda: types.SimpleNamespace(hex=held * 2))
        before = _plans(w)
        try:
            TesterDevice().run_proof(w.repo / RED, sink="none", timeout=60)
        except red_tickets.RedTicketRefused as exc:
            assert exc.door == "cast" and any("already held" in str(x) for x in exc.lacks), exc
            assert RED in str(exc), str(exc)
        else:
            raise AssertionError("the refused cast did not raise out of the run")
        assert _plans(w) == before, [p.name for p in _plans(w)]
    finally:
        _restore()


def test_a_cast_commits_in_the_same_act_and_does_not_push(monkeypatch):
    w = _world("commit", monkeypatch)
    try:
        before = _git(w.commons, "rev-parse", "HEAD")
        _run(w)
        assert len(_plans(w)) == 3, [p.name for p in _plans(w)]
        assert _git(w.commons, "status", "--porcelain", "--untracked-files=all") == "", \
            _git(w.commons, "status", "--porcelain", "--untracked-files=all")
        log = _git(w.commons, "rev-list", f"{before}..HEAD").split()
        # one commit per call that cast: run_proof's red, then the whole-tree orphan scan
        assert len(log) == 2, log
        files = set(_git(w.commons, "diff", "--name-only", before, "HEAD").split())
        for plan in _plans(w):
            assert plan.resolve().relative_to(w.commons.resolve()).as_posix() in files, (plan, files)
        assert any(f.startswith("berths/sorted/") for f in files), files
        assert _git(w.remote, "rev-parse", "main") == before, "the run pushed"
    finally:
        _restore()


def _raised(w) -> list[dict]:
    from cairn.tools.base.address import log_path
    home = Path(log_path("tester", 0, w.raiser))
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(home.glob("*.raise_trouble.json"))] if home.exists() else []


def test_staged_changes_from_another_hold_the_casts_as_troubles(monkeypatch):
    w = _world("held", monkeypatch)
    try:
        (w.commons / "another.txt").write_text("someone else's work\n", encoding="utf-8")
        _git(w.commons, "add", "--", "another.txt")
        before = _git(w.commons, "rev-parse", "HEAD")
        assert _run(w) == []
        assert _plans(w) == [], [p.name for p in _plans(w)]
        assert _git(w.commons, "rev-parse", "HEAD") == before, "the run committed over a staged tree"
        assert _git(w.commons, "diff", "--cached", "--name-only") == "another.txt"
        assert _git(w.commons, "status", "--porcelain", "--untracked-files=all") == "A  another.txt"
        held = sorted(r["pointer"] for r in _raised(w))
        assert held == sorted(f"red_tickets:held:{k}" for k in (
            f"red:{RED}::*", f"orphan:{ORPHAN_SEAL}", f"orphan:{ORPHAN_FILE}")), held
        detail = {r["values"]["detail"]["path"] for r in _raised(w)}
        assert detail == {RED, ORPHAN_SEAL, ORPHAN_FILE}, detail
    finally:
        _restore()


def test_a_store_in_no_git_tree_leaves_the_run_whole_and_says_so(monkeypatch, capsys):
    from cairn.devices.tester import red_tickets
    from cairn.devices.tester.device import TesterDevice
    w = _world("nogit", monkeypatch)
    try:
        nowhere = Path(scratch_dir("testing-207c-nogit-store-")) / "CairnCommons" / "tickets"
        monkeypatch.setattr(red_tickets, "ROOTS", {**red_tickets.ROOTS, "tickets": nowhere})
        record = TesterDevice().run_proof(w.repo / RED, sink="none", timeout=60)
        assert record["verdict"] == "red", record["verdict"]
        err = capsys.readouterr().err
        assert "NOT ticketed" in err and "in no git tree" in err and RED in err.replace("\\", "/"), err
        assert not nowhere.exists() or not list(nowhere.iterdir()), "a store in no git tree was written"
    finally:
        _restore()


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

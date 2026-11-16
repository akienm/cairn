"""Proof for ticket a5be53f269ac: a tester-cast red ticket carries its outline check.

Measured 2026-11-15: 133df5f7de08 and 8d6936a7d080 were cast by cairn/devices/tester/red_tickets.py,
and the integrator's land of each stopped at the BUILDME lane the_ticket_was_checked_against_the_outline
(the lane buildme_rides_the_outline_check), because no outline check had read them. The
tester's caster never ran one. Now it runs codemother's published ``cairn outlinecheck <id>``
once per cast, in sequence, before the commit that carries the cast.

  1. a red cast by ticket_what_is_new carries a ran:true outline-check record, and the BUILDME
     lane over the ticket, asked of codemother's inspect verb, names no lack;
  2. the record rides the cast's own commit, and the commons is clean after the run;
  3. a run casting three tickets makes exactly three reader calls, and no two overlap (each
     ticket costs one Haiku read in the field; the reads never burst concurrently);
  4. a reader that fails still lands and commits the cast, and a tester trouble names the ticket.

The world: a scratch repo holding three red proofs and a small outline at
press_office/CairnComponentOutline.txt; a scratch commons with the live store charter, in git.
The reader is a fake claude script (red_tickets.ROOTS["claude"], which the caster hands the
check as CAIRN_REHEARSAL_CLAUDE). It logs each call and holds a lock file while it "reads".

    bin/cairn test cairn/devices/tester/proofs/test_a_tester_cast_red_ticket_carries_its_outline_check.py
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

PROVES = {"a5be53f269ac": {
    "1": "test_a_cast_red_ticket_carries_a_ran_outline_check",
    "2": "test_the_outline_check_rides_the_casts_commit",
    "3": "test_three_casts_make_three_reads_and_none_overlap",
    "4": "test_a_failed_read_still_lands_the_cast_and_raises_a_trouble"}}

PROOF_TIMEOUT_S = 600

REDS = ("cairn/a/proofs/test_one.py", "cairn/a/proofs/test_two.py", "cairn/a/proofs/test_three.py")
OUTLINE = "1 Cairn\n  1.1 the tester\n    1.1.1 every red is ticketed\n"

_FAKE = r'''#!/usr/bin/env python3
"""testing: a fake claude reader for ticket a5be53f269ac. Logs the call; holds a lock while reading."""
import json, os, sys, time
here = os.path.dirname(os.path.abspath(__file__))
sys.stdin.read()
lock = os.path.join(here, "reading.lock")
try:
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
except FileExistsError:
    open(os.path.join(here, "overlaps"), "a").write("x\n")
    fd = None
with open(os.path.join(here, "calls"), "a") as f:
    f.write("call\n")
time.sleep(0.3)
if fd is not None:
    os.close(fd)
    os.unlink(lock)
if MODE == "fail":
    print(json.dumps({"is_error": True, "result": "testing: the reader is down"}))
else:
    print(json.dumps({"is_error": False, "structured_output": {"touches": ["1.1.1"], "conflicts": []}}))
'''


def _git(where: Path, *args: str) -> str:
    got = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True)
    assert got.returncode == 0, (args, got.stderr)
    return got.stdout.strip()


def _world(tag: str, monkeypatch, mode: str = "ok") -> types.SimpleNamespace:
    from cairn.devices.tester import red_tickets
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.ticket_log import _LIVE_CHARTER
    top = Path(scratch_dir(f"testing-a5be-{tag}-"))
    repo, commons, reader = top / "repo", top / "CairnCommons", top / "reader"
    (repo / "cairn" / "a" / "proofs").mkdir(parents=True)
    (repo / "press_office").mkdir()
    (repo / "press_office" / "CairnComponentOutline.txt").write_text(OUTLINE, encoding="utf-8")
    (repo / "cairn" / "a" / "intention+why.json").write_text(json.dumps({"component": "a"}), encoding="utf-8")
    for rel in REDS:
        (repo / rel).write_text('"""testing: a proof that reds."""\nraise SystemExit(1)\n', encoding="utf-8")
    for cmd in (["init", "-q"], ["add", "-A"]):
        subprocess.run(["git", "-C", str(repo), *cmd], check=True, capture_output=True)
    tickets = commons / "tickets"
    tickets.mkdir(parents=True)
    live = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
        Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
    shutil.copyfile(live, tickets / "_charter+why.json")
    for cmd in (["init", "-q"], ["config", "user.name", "testing"],
                ["config", "user.email", "testing@invalid"], ["add", "-A"],
                ["commit", "-q", "-m", "testing: the store charter"]):
        _git(commons, *cmd)
    reader.mkdir()
    fake = reader / "claude"
    fake.write_text(_FAKE.replace('if MODE == "fail"', f'if {mode!r} == "fail"'), encoding="utf-8")
    fake.chmod(0o755)
    raiser = {"repo": top / "world", "commons": top / "world", "instance": top / "world"}
    monkeypatch.setattr(red_tickets, "ROOTS", {"repo": repo, "tickets": tickets, "commons": commons,
                                               "berths": top / "berths", "trace": top / "trace",
                                               "raiser": raiser, "claude": fake})
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": repo})
    from cairn.tools.base import transitions
    monkeypatch.setenv(transitions.PROOF_ENV, "testing-a5be53f269ac")
    return types.SimpleNamespace(top=top, repo=repo, commons=commons, tickets=tickets,
                                 reader=reader, raiser=raiser)


def _restore():
    from cairn.tools.artifact import artifact as A
    A.set_diagnostic_roots(None)


def _cast(w, reds=REDS[:1]) -> list[Path]:
    from cairn.devices.tester import red_tickets
    results = [{"proof": rel, "verdict": "red", "teeth_red": ["test_it"]} for rel in reds]
    return red_tickets.ticket_what_is_new(results)


def _id(plan: Path) -> str:
    return plan.name.split("-", 1)[0]


def _records(w, tid: str) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((w.commons / "outline_checks").glob(f"{tid}-*.json"))]


def _calls(w) -> int:
    p = w.reader / "calls"
    return len(p.read_text().splitlines()) if p.exists() else 0


def test_a_cast_red_ticket_carries_a_ran_outline_check(monkeypatch):
    from cairn.tools.inspect_wire.inspect_wire import ask
    from cairn.machines.rehearsal import rehearsal as R
    w = _world("ran", monkeypatch)
    try:
        plans = _cast(w)
        assert len(plans) == 1, plans
        tid = _id(plans[0])
        assert R.ticket_file(tid, w.commons) is not None, "the lane must see the ticket, or it passes vacuously"
        recs = _records(w, tid)
        assert [r.get("ran") for r in recs] == [True], recs
        assert recs[0]["touches"] == [{"number": "1.1.1", "text": "every red is ticketed"}], recs[0]
        # codemother answers the lane over her inspect verb (ticket 149b9a1ab9c4); under
        # PROOF_ENV the ask rides inspect_wire's in-process scratch CodeMother, never the live one
        lacks = ask("buildme_rides_the_outline_check", tid, root=w.commons)
        assert lacks == [], lacks
    finally:
        _restore()


def test_the_outline_check_rides_the_casts_commit(monkeypatch):
    w = _world("commit", monkeypatch)
    try:
        before = _git(w.commons, "rev-parse", "HEAD")
        plans = _cast(w)
        tid = _id(plans[0])
        assert _git(w.commons, "status", "--porcelain", "--untracked-files=all") == "", \
            _git(w.commons, "status", "--porcelain", "--untracked-files=all")
        log = _git(w.commons, "rev-list", f"{before}..HEAD").split()
        assert len(log) == 1, log
        files = set(_git(w.commons, "diff", "--name-only", before, "HEAD").split())
        assert any(f.startswith(f"outline_checks/{tid}-") for f in files), files
        assert plans[0].resolve().relative_to(w.commons.resolve()).as_posix() in files, files
    finally:
        _restore()


def test_three_casts_make_three_reads_and_none_overlap(monkeypatch):
    w = _world("three", monkeypatch)
    try:
        plans = _cast(w, REDS)
        assert len(plans) == 3, plans
        assert _calls(w) == 3, f"three casts must make exactly three reads, made {_calls(w)}"
        assert not (w.reader / "overlaps").exists(), "two reads ran at once"
        for plan in plans:
            assert [r.get("ran") for r in _records(w, _id(plan))] == [True], _id(plan)
    finally:
        _restore()


def test_a_failed_read_still_lands_the_cast_and_raises_a_trouble(monkeypatch):
    from cairn.tools.base.address import log_path
    w = _world("fail", monkeypatch, mode="fail")
    try:
        before = _git(w.commons, "rev-parse", "HEAD")
        plans = _cast(w)
        assert len(plans) == 1, plans
        tid = _id(plans[0])
        files = set(_git(w.commons, "diff", "--name-only", before, "HEAD").split())
        assert plans[0].resolve().relative_to(w.commons.resolve()).as_posix() in files, files
        assert _git(w.commons, "status", "--porcelain", "--untracked-files=all") == "", \
            _git(w.commons, "status", "--porcelain", "--untracked-files=all")
        home = Path(log_path("tester", 0, w.raiser))
        raised = [json.loads(p.read_text(encoding="utf-8"))
                  for p in sorted(home.glob("*.raise_trouble.json"))] if home.exists() else []
        assert any(tid in json.dumps(r) and "outline" in json.dumps(r) for r in raised), raised
    finally:
        _restore()


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

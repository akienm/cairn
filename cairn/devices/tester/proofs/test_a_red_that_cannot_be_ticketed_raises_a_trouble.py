"""Proof for ticket 0da92a7c054a: a tester red whose checkout has no commons to ticket it in raises
a trouble naming the proof, never only a stderr line.

Measured 2026-11-20 on akiendelllinux: a red measured from a /var/tmp worktree (no CairnCommons
beside it) printed "is red and was NOT ticketed" to the run's stderr and emitted red_unticketed
into the tester's own trail, which no inbox reads. The red was lost to everyone but the run log.

Fixture, all marked testing (the harness of test_a_red_casts_only_into_its_own_commons.py): a
scratch git checkout with one component and one proof, and NO CairnCommons beside it, so the
derived ticket store is in no git tree. The tester device runs over a scratch trail
(set_diagnostic_roots); the trouble store's published live() is read from that trail's raises
and clears, so "stands" means what the holder would fold from this device's emissions.

  1. a red raises trouble 'tester-red-unticketed:<proof rel path>' whose why names the proof and
     the unreachable store, and run_proof still returns the red record;
  2. in that run no CairnCommons file is written, the house's included, and the stderr line
     'was NOT ticketed' still prints;
  3. the same proof run green clears that trouble; a second green, with nothing standing,
     writes no clear.

    bin/cairn test cairn/devices/tester/proofs/test_a_red_that_cannot_be_ticketed_raises_a_trouble.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import types
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"0da92a7c054a": {
    "1": "test_an_unticketable_red_raises_a_trouble_naming_the_proof",
    "2": "test_that_run_writes_no_commons_and_still_says_so_on_stderr",
    "3": "test_a_green_clears_the_trouble_and_an_unraised_green_writes_no_clear"}}

PROOF = "cairn/a/proofs/test_a.py"
IDENTITY = "tester-red-unticketed:" + PROOF
RED_BODY = '"""testing: a proof that reds."""\nraise SystemExit(1)\n'
GREEN_BODY = '"""testing: a proof that greens."""\nprint("  ok   test_x")\nraise SystemExit(0)\n'
HOUSE = Path.home() / "dev" / "src" / "CairnCommons"


def _git(where: Path, *args: str) -> str:
    got = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True)
    assert got.returncode == 0, (args, got.stderr)
    return got.stdout.strip()


def _world(tag: str, monkeypatch) -> types.SimpleNamespace:
    from cairn.devices.tester import red_tickets
    from cairn.devices.tester.device import TesterDevice
    from cairn.devices.trouble.tools.store import store as trouble_store
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base import transitions
    top = Path(scratch_dir(f"testing-0da9-{tag}-"))
    repo = top / "repo"
    (repo / "cairn" / "a" / "proofs").mkdir(parents=True)
    (repo / "cairn" / "a" / "intention+why.json").write_text(json.dumps({"component": "a"}),
                                                             encoding="utf-8")
    (repo / PROOF).write_text(RED_BODY, encoding="utf-8")
    for cmd in (["init", "-q"], ["add", "-A"]):
        _git(repo, *cmd)
    commons = top / "CairnCommons"          # never created: the checkout has no commons beside it
    monkeypatch.setattr(red_tickets, "ROOTS", {
        "repo": repo, "tickets": commons / "tickets", "commons": commons,
        "berths": top / "berths", "trace": top / "trace",
        "raiser": {"repo": top / "world", "commons": top / "world", "instance": top / "world"}})
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": repo})
    monkeypatch.setenv(transitions.PROOF_ENV, "testing-0da92a7c054a")
    tester = TesterDevice()
    tester.set_diagnostic_roots({"repo": top / "trail", "commons": top / "trail",
                                 "instance": top / "trail"})

    def standing():
        up = set()
        for r in tester.diagnostic_records():
            if r.get("gate") == "raise_trouble":
                up.add(r.get("pointer"))
            elif r.get("gate") == "clear_trouble":
                up.discard(r.get("pointer"))
        return up

    monkeypatch.setattr(trouble_store, "live",
                        lambda *a, **k: [{"id": i} for i in sorted(standing())])
    return types.SimpleNamespace(top=top, repo=repo, commons=commons, tester=tester,
                                 standing=standing)


def _run(w):
    return w.tester.run_proof(w.repo / PROOF, sink="none", caller="testing 0da92a7c054a",
                              isolation="none")


def _gates(w, gate: str) -> list[dict]:
    return [r for r in w.tester.diagnostic_records()
            if r.get("gate") == gate and r.get("pointer") == IDENTITY]


def _house_touched(since: float, top: Path) -> list[str]:
    """House commons files changed since ``since`` that name this fixture's checkout."""
    hit = []
    if not HOUSE.is_dir():
        return hit
    for sub in ("tickets", "questions", "troubles"):
        d = HOUSE / sub
        if not d.is_dir():
            continue
        for p in d.iterdir():
            try:
                if p.is_file() and p.stat().st_mtime >= since and str(top) in p.read_text(
                        encoding="utf-8", errors="replace"):
                    hit.append(str(p))
            except OSError:
                continue
    return hit


def _restore():
    from cairn.tools.artifact import artifact as A
    A.set_diagnostic_roots(None)


def test_an_unticketable_red_raises_a_trouble_naming_the_proof(monkeypatch):
    w = _world("raise", monkeypatch)
    try:
        record = _run(w)
        assert record["verdict"] == "red", record
        raised = _gates(w, "raise_trouble")
        assert len(raised) == 1, [r.get("pointer") for r in w.tester.diagnostic_records()]
        why = raised[0]["values"]["why"]
        assert str(w.repo / PROOF) in why, why
        assert "in no git tree" in why and str(w.commons) in why, why
        detail = raised[0]["values"]["detail"]
        assert detail["proof"] == str(w.repo / PROOF) and detail["store_reason"], detail
        assert w.standing() == {IDENTITY}, w.standing()
    finally:
        _restore()


def test_that_run_writes_no_commons_and_still_says_so_on_stderr(monkeypatch, capsys):
    w = _world("quiet", monkeypatch)
    try:
        t0 = time.time() - 1
        record = _run(w)
        err = capsys.readouterr().err
        assert record["verdict"] == "red", record
        assert w.standing() == {IDENTITY}, "that run is the one that raised the trouble"
        assert "is red and was NOT ticketed" in err, err[-2000:]
        assert not w.commons.exists(), sorted(str(p) for p in w.commons.rglob("*"))
        assert not [p for p in w.top.rglob("CairnCommons")], "a CairnCommons appeared in scratch"
        assert _house_touched(t0, w.top) == []
    finally:
        _restore()


def test_a_green_clears_the_trouble_and_an_unraised_green_writes_no_clear(monkeypatch):
    w = _world("clear", monkeypatch)
    try:
        assert _run(w)["verdict"] == "red"
        assert w.standing() == {IDENTITY}, w.standing()
        (w.repo / PROOF).write_text(GREEN_BODY, encoding="utf-8")
        assert _run(w)["verdict"] == "green"
        clears = _gates(w, "clear_trouble")
        assert len(clears) == 1 and w.standing() == set(), (clears, w.standing())
        assert clears[0]["values"]["by"] == "cc", clears[0]["values"]
        assert _run(w)["verdict"] == "green"
        assert len(_gates(w, "clear_trouble")) == 1, "a green with nothing standing wrote a clear"
    finally:
        _restore()


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

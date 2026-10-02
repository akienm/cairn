"""Teeth for ticket 054bcbe02f12 — the hollow measures each proof at its seal's depth.

MEASURED 2026-10-02: c54d744aa9ac's hollow (HEAD 5a58b1a8) read two teeth of
``cairn/devices/tester/proofs/test_a_seal_inside_a_seal_inherits.py`` red AT HEAD and refused
to attribute anything, though that proof is sealed green under netns and passes bare. hollow.py
ran every proof with ``isolation="none"``, which still binds the instance seal, and inside that
instance-only sandbox the proof's own nested network seal is a namespace inside a namespace —
refused by this host. The build makes measure() read each proof's standing validation in the
LIVE repo and run it at ``netns`` when that seal reads ``sealed``, ``none`` otherwise, and name
the depth per proof in the finding and on the command's output.

Clause keys follow the falsifier's (N) markers. Tooth (1) measures the live ticket that bore
this one; teeth (2) and (3) read a fixture repo through a stub tester that records the isolation
it was handed, so no proof is actually run under a namespace there.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester import hollow  # noqa: E402
from cairn.devices.tester.hollow import HollowUnmeasurable, measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402

PROVES = {
    "054bcbe02f12": {
        "1": "test_c54d_hollow_reads_every_declared_tooth_green_at_head",
        "2": "test_each_proof_runs_at_the_isolation_its_standing_seal_was_taken_under",
        "3": "test_the_reading_names_the_isolation_per_proof",
    },
}

FIXTURE = "f1x7de9700c1"
_C54D = "c54d744aa9ac"
_C54D_PROOF = "cairn/devices/tester/proofs/test_a_seal_inside_a_seal_inherits.py"

_PROOF_SRC = '''\
PROVES = {"%s": {"1": "%s"}}
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import subject

if __name__ == "__main__":
    print(("ok" if subject.VALUE == 2 else "FAIL") + " %s")
'''


def _git(repo: Path, *args: str, env=None) -> None:
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                         env=env or git_env())
    assert out.returncode == 0, f"fixture git {args}: {out.stderr.strip()}"


def _validation(repo: Path, stem: str, verdict: str) -> None:
    """A standing validation for a fixture proof, UNTRACKED on purpose: the hollow's worktree
    is a checkout at HEAD and carries no untracked file, so a depth read from the worktree
    instead of the live repo comes back 'none' for both and tooth (2) reds."""
    path = repo / "validations" / f"{stem}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([{"verdict": "green", "evidence": {
        "seal": {"verdict": verdict, "detail": "fixture"}}}]), encoding="utf-8")


def _fixture(tmp: Path) -> tuple[Path, Path, Path]:
    """Three proofs over one changed file: one sealed under netns, one sealed open, one never
    sealed. The build commit dates after the journal's BUILDME, as in the live corpus."""
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    (repo / "proofs").mkdir(parents=True)
    (commons / "tickets").mkdir(parents=True)
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    _git(repo, "init", "-q", "-b", "main", env=env)
    for stem in ("test_netns_sealed", "test_open_sealed", "test_never_sealed"):
        tooth = f"{stem}_tooth"
        (repo / "proofs" / f"{stem}.py").write_text(_PROOF_SRC % (FIXTURE, tooth, tooth))
    for value, date in ((1, "2020-01-01T00:00:00"), (2, "2020-01-03T00:00:00")):
        (repo / "subject.py").write_text(f"VALUE = {value}\n")
        _git(repo, "add", "-A", env=env)
        _git(repo, "commit", "-qm", f"commit {value}",
             env={**env, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
    _validation(repo, "test_netns_sealed", "sealed")
    _validation(repo, "test_open_sealed", "open")

    packet = berths / "0" / "packets" / f"decompose-20200103T000000-{FIXTURE}.json"
    packet.parent.mkdir(parents=True)
    packet.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose", "sub_problems": [
        {"what": "the build", "kind": "build", "writes_to": ["subject.py"]}]}), encoding="utf-8")
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    (repo / "history.json").write_text(json.dumps({"entries": [
        {"ticket": FIXTURE, "direction": "forward", "actor": "fixture",
         "at": "2020-01-02T00:00:00", "to": "BUILDME",
         "proven_by": ["proofs/test_netns_sealed.py", "proofs/test_open_sealed.py",
                       "proofs/test_never_sealed.py"]}]}), encoding="utf-8")
    return repo, commons, berths


class _Recording:
    """Hands back every declared tooth green and records the isolation each run was asked for."""

    def __init__(self):
        self.asked: list[tuple[str, str]] = []

    def run_proof(self, path, **kw):
        stem = Path(path).stem
        self.asked.append((stem, kw.get("isolation")))
        return {"evidence": {"teeth_green": [f"{stem}_tooth"], "teeth_red": [],
                             "returncode": 0, "stderr_tail": ""}}


def _measured() -> tuple[dict, _Recording]:
    repo, commons, berths = _fixture(Path(str(scratch_dir("hollow-depth-proof-"))))
    tester = _Recording()
    finding = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths,
                      timeout=60, tester=tester)
    return finding, tester


def test_c54d_hollow_reads_every_declared_tooth_green_at_head():
    try:
        measure(_C54D, timeout=600)
    except HollowUnmeasurable as why:
        assert "teeth_not_green" not in str(why), \
            f"the hollow still reads declared teeth of {_C54D_PROOF} red at HEAD: {why}"
        raise
    return True


def test_each_proof_runs_at_the_isolation_its_standing_seal_was_taken_under():
    _finding, tester = _measured()
    want = {"test_netns_sealed": "netns", "test_open_sealed": "none", "test_never_sealed": "none"}
    by_proof: dict[str, set] = {}
    for stem, iso in tester.asked:
        by_proof.setdefault(stem, set()).add(iso)
    assert by_proof == {k: {v} for k, v in want.items()}, \
        f"isolation asked per proof {by_proof}, want {want}"
    seal_isolation = getattr(hollow, "seal_isolation", None)
    assert callable(seal_isolation), "hollow.py carries no seal_isolation(proof)"
    return True


def test_the_reading_names_the_isolation_per_proof():
    finding, _tester = _measured()
    assert finding.get("isolation") == {"proofs/test_netns_sealed.py": "netns",
                                        "proofs/test_open_sealed.py": "none",
                                        "proofs/test_never_sealed.py": "none"}, \
        f"the finding's isolation map is {finding.get('isolation')!r}"
    src = (_REPO_ROOT / "cairn/devices/tester/cli.py").read_text(encoding="utf-8")
    assert "isolation:" in src.split("def _hollow_run", 1)[1].split("\ndef ", 1)[0], \
        "cli._hollow_run prints no '  isolation: <rel> <depth>' line"
    return True


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

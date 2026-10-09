"""Teeth for ticket d80360545e91 — proofs run without a network seal, and standing seal records
stay as written.

The tester stops cutting the network. Every run is taken at isolation ``none`` (which still
binds the instance seal), ``--netns`` refuses with exit 2 before anything runs, and a proof whose
standing record reads ``sealed`` lands its next run ``open`` with the retirement written into
``evidence.unsealing_because`` by the store's own guard — so a standing record changes only when
its own proof next lands, and says why.

Clause keys follow the falsifier's (N) markers. Every fixture is a scratch directory
(cairn.tools.scratch), never the live corpus: (1) drives ``cli.main`` in-process with
``subprocess.run`` spied, so the sandbox argv is read rather than inferred; (2) drives the reseal
door with a recording wrapper over the real tester; (3) reads the hollow's depth and runs
``measure`` over a fixture repo through a stub tester; (4) runs ``bin/cairn test --netns`` as a
subprocess over a fixture proof that leaves a marker if it is ever run; (5) runs ``bin/cairn test``
and ``bin/cairn test --seal`` as subprocesses over one fixture proof per standing seal verdict, plus
one with no record, and reads the CLI's own refusal lanes.

    cairn test --exec "python3 cairn/devices/tester/proofs/test_the_network_seal_is_retired.py"
"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402

PROVES = {
    "d80360545e91": {
        "1": "test_a_seal_over_a_sealed_record_runs_bare_and_says_why",
        "2": "test_the_reseal_door_runs_bare_and_says_why",
        "3": "test_the_hollow_measures_bare_inside_the_instance_seal",
        "4": "test_netns_refuses_and_runs_nothing",
        "5": "test_no_cairn_test_path_produces_a_refused_seal",
    },
}

_TICKET = "d80360545e91"
CAIRN = _REPO_ROOT / "bin" / "cairn"
GREEN_SRC = "print('  ok   network-seal-retired fixture')\nraise SystemExit(0)\n"


def _pose_standing(proof: Path, verdict: str, *, fingerprint: str | None = None) -> None:
    """A real standing VALIDATION beside `proof` carrying the named seal verdict.

    Built from a genuine run at ``none`` and re-fingerprinted, so the record is the shape the
    tester reads in life. ``fingerprint`` overrides the recorded one when a fixture needs its
    standing seal to read stale (the reseal door re-runs only a proof whose closure moved)."""
    from cairn.tools.validation_store import validation_store as vs
    from cairn.devices.tester.device import TesterDevice

    real = TesterDevice().run_proof(proof, sink="none", isolation="none")
    evidence = dict(real["evidence"],
                    seal=dict(real["evidence"]["seal"], verdict=verdict),
                    source_fingerprint=fingerprint or vs.source_fingerprint(str(proof)))
    vs.persist_validation(dict(real, evidence=evidence), proof_path=str(proof))


def _latest(proof: Path) -> dict:
    from cairn.tools.validation_store import validation_store as vs
    trail = vs.read_validations(str(proof))
    assert trail, f"no validation landed beside {proof}"
    return trail[-1]


def test_a_seal_over_a_sealed_record_runs_bare_and_says_why():
    from cairn.devices.tester import cli
    from cairn.tools.validation_store import validation_store as vs

    proofs = Path(str(scratch_dir("network-seal-retired-cli-"))) / "proofs"
    proofs.mkdir(parents=True)
    run, sibling = proofs / "test_run.py", proofs / "test_sibling.py"
    for p in (run, sibling):
        p.write_text(GREEN_SRC, encoding="utf-8")
        _pose_standing(p, "sealed")
    sibling_bytes = Path(vs.validations_path_for(str(sibling))).read_bytes()

    argvs: list[list[str]] = []
    real_run = subprocess.run

    def spy(args, *a, **kw):
        if isinstance(args, (list, tuple)):
            argvs.append([str(x) for x in args])
        return real_run(args, *a, **kw)

    out = io.StringIO()
    subprocess.run = spy
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            rc = cli.main([str(run), "--seal"])
    finally:
        subprocess.run = real_run
    text = out.getvalue()

    assert "REFUSED" not in text, f"`cairn test --seal` refused over a sealed record:\n{text}"
    assert rc == 0, f"`cairn test --seal` exited {rc}:\n{text}"
    netns = [a for a in argvs if "--unshare-net" in a]
    assert not netns, f"a run cut the network: {netns[0]}"
    assert any(str(run) in " ".join(a) for a in argvs), \
        f"the spy saw no run of {run.name} — the tooth would pass on an empty population"
    record = _latest(run)
    evidence = record.get("evidence") or {}
    assert record.get("verdict") == "green", f"landed {record.get('verdict')!r}, want green"
    assert (evidence.get("seal") or {}).get("verdict") == "open", \
        f"landed seal {(evidence.get('seal') or {}).get('verdict')!r}, want 'open'"
    assert _TICKET in str(evidence.get("unsealing_because") or ""), \
        f"evidence.unsealing_because is {evidence.get('unsealing_because')!r}; it must name {_TICKET}"
    assert Path(vs.validations_path_for(str(sibling))).read_bytes() == sibling_bytes, \
        "a run rewrote a sibling proof's standing validation"
    return True


class _FakeRaiser:
    """Records what the door raised and cleared, so the proof files nothing into the live
    trouble store (a proof seeding the tree it reads)."""

    def __init__(self):
        self.raised, self.cleared = [], []

    def raise_trouble(self, identity, *, why, detail=None):
        self.raised.append({"identity": identity, "why": why, "detail": detail or {}})

    def clear_trouble(self, identity, *, by, what_changed):
        self.cleared.append({"identity": identity, "by": by, "what_changed": what_changed})


class _AskedTester:
    """The real tester, recording the isolation each run was asked for."""

    def __init__(self):
        from cairn.devices.tester.device import TesterDevice
        self.real, self.asked = TesterDevice(), []

    def run_proof(self, path, **kw):
        self.asked.append(kw.get("isolation"))
        return self.real.run_proof(path, **kw)


def test_the_reseal_door_runs_bare_and_says_why():
    from cairn.devices.tester.reseal import reseal

    proofs = Path(str(scratch_dir("network-seal-retired-reseal-"))) / "proofs"
    proofs.mkdir(parents=True)
    proof = proofs / "test_resealed.py"
    proof.write_text(GREEN_SRC, encoding="utf-8")
    _pose_standing(proof, "sealed", fingerprint="stale-fixture-fingerprint")

    tester = _AskedTester()
    out = reseal(proof, tester=tester, raiser=_FakeRaiser())
    assert out.get("ran") is True, f"the reseal door did not run the proof: {out}"
    assert tester.asked == ["none"], f"the reseal door asked isolation {tester.asked}, want ['none']"
    record = _latest(proof)
    evidence = record.get("evidence") or {}
    assert record.get("verdict") == "green", f"landed {record.get('verdict')!r}, want green: {out}"
    assert (evidence.get("seal") or {}).get("verdict") == "open", \
        f"landed seal {(evidence.get('seal') or {}).get('verdict')!r}, want 'open'"
    assert _TICKET in str(evidence.get("unsealing_because") or ""), \
        f"evidence.unsealing_because is {evidence.get('unsealing_because')!r}; it must name {_TICKET}"
    return True


_HOLLOW_FIXTURE = "f1x7d8036000"
_HOLLOW_PROOF_SRC = '''\
PROVES = {"%s": {"1": "test_sealed_tooth"}}
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import subject

if __name__ == "__main__":
    print(("ok" if subject.VALUE == 2 else "FAIL") + " test_sealed_tooth")
'''


def _git(repo: Path, *args: str, env=None) -> None:
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                         env=env or git_env())
    assert out.returncode == 0, f"fixture git {args}: {out.stderr.strip()}"


def _hollow_fixture(tmp: Path) -> tuple[Path, Path, Path]:
    """One proof standing 'sealed' over one changed file; the build commit dates after the
    journal's BUILDME, as in the live corpus (shape of test_the_hollow_measures_at_the_seals_depth)."""
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    (repo / "proofs").mkdir(parents=True)
    (commons / "tickets").mkdir(parents=True)
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    _git(repo, "init", "-q", "-b", "main", env=env)
    (repo / "proofs" / "test_sealed.py").write_text(_HOLLOW_PROOF_SRC % _HOLLOW_FIXTURE)
    for value, date in ((1, "2020-01-01T00:00:00"), (2, "2020-01-03T00:00:00")):
        (repo / "subject.py").write_text(f"VALUE = {value}\n")
        _git(repo, "add", "-A", env=env)
        _git(repo, "commit", "-qm", f"commit {value}",
             env={**env, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
    validation = repo / "validations" / "test_sealed.json"
    validation.parent.mkdir(parents=True)
    validation.write_text(json.dumps([{"verdict": "green", "evidence": {
        "seal": {"verdict": "sealed", "detail": "fixture"}}}]), encoding="utf-8")

    packet = berths / "0" / "packets" / f"decompose-20200103T000000-{_HOLLOW_FIXTURE}.json"
    packet.parent.mkdir(parents=True)
    packet.write_text(json.dumps({"ticket": _HOLLOW_FIXTURE, "stage": "decompose", "sub_problems": [
        {"what": "the build", "kind": "build", "writes_to": ["subject.py"]}]}), encoding="utf-8")
    (commons / "tickets" / f"{_HOLLOW_FIXTURE}-fixture.json").write_text(
        json.dumps({"id": _HOLLOW_FIXTURE}))
    (repo / "history.json").write_text(json.dumps({"entries": [
        {"ticket": _HOLLOW_FIXTURE, "direction": "forward", "actor": "fixture",
         "at": "2020-01-02T00:00:00", "to": "BUILDME",
         "proven_by": ["proofs/test_sealed.py"]}]}), encoding="utf-8")
    return repo, commons, berths


class _Recording:
    """Hands back the declared tooth green and records the isolation each run was asked for."""

    def __init__(self):
        self.asked: list[str] = []

    def run_proof(self, path, **kw):
        self.asked.append(kw.get("isolation"))
        return {"evidence": {"teeth_green": ["test_sealed_tooth"], "teeth_red": [],
                             "returncode": 0, "stderr_tail": ""}}


def test_the_hollow_measures_bare_inside_the_instance_seal():
    from cairn.devices.tester import hollow
    from cairn.devices.tester.isolation import inside_a_seal, inside_an_instance_seal

    assert inside_an_instance_seal() and not inside_a_seal(), (
        "precondition: this tooth measures a hollow started inside the tester's instance "
        "sandbox with no network seal around it — run it through `cairn test`")
    repo, commons, berths = _hollow_fixture(Path(str(scratch_dir("network-seal-retired-hollow-"))))
    depth = hollow.seal_isolation(repo / "proofs" / "test_sealed.py")
    assert depth == "none", f"hollow.seal_isolation reads {depth!r} for a sealed proof, want 'none'"
    tester = _Recording()
    try:
        hollow.measure(_HOLLOW_FIXTURE, repo_root=repo, commons=commons, berths_root=berths,
                       timeout=60, tester=tester)
    except hollow.HollowUnmeasurable as why:
        raise AssertionError(f"the hollow refused instead of measuring: {why}") from why
    assert tester.asked and set(tester.asked) == {"none"}, \
        f"the hollow asked isolation {tester.asked}, want only 'none'"
    return True


def test_netns_refuses_and_runs_nothing():
    from cairn.devices.tester import isolation
    from cairn.tools.validation_store import validation_store as vs

    proofs = Path(str(scratch_dir("network-seal-retired-netns-"))) / "proofs"
    proofs.mkdir(parents=True)
    marker = proofs.parent / "ran.marker"
    proof = proofs / "test_must_not_run.py"
    proof.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n"
                     "raise SystemExit(0)\n", encoding="utf-8")
    for args in (("--netns",), ("--seal", "--netns")):
        r = subprocess.run([str(CAIRN), "test", *args, str(proof)],
                           capture_output=True, text=True, timeout=300)
        text = r.stdout + r.stderr
        assert r.returncode == 2, f"`cairn test {' '.join(args)}` exited {r.returncode}, want 2:\n{text}"
        assert _TICKET in text, f"`cairn test {' '.join(args)}` did not name {_TICKET}:\n{text}"
        assert not marker.exists(), f"`cairn test {' '.join(args)}` ran the proof"
        assert not Path(vs.validations_path_for(str(proof))).exists(), \
            f"`cairn test {' '.join(args)}` landed a validation"

    for name in ("netns", "seal"):
        try:
            isolation.get_isolation(name)
        except ValueError as why:
            assert _TICKET in str(why), f"get_isolation({name!r}) refused without naming {_TICKET}: {why}"
        else:
            raise AssertionError(f"get_isolation({name!r}) still builds a network seal")
    assert _TICKET in str(getattr(isolation, "NETWORK_SEAL_RETIRED", "")), \
        f"isolation.NETWORK_SEAL_RETIRED is missing or does not name {_TICKET}"
    return True


def test_no_cairn_test_path_produces_a_refused_seal():
    """With the network seal retired, cli.py's SealDowngradeRefused/SealConversionRefused lane is
    deleted as dead (open-914da176b1ed, answer A). That premise was measured on a prototype, not
    on this build, so this tooth measures it here: over every standing seal verdict the tester
    can write, and over a proof with no record at all, neither a diagnostic run nor a ``--seal``
    run reports a refusal of any kind, and both exit 0 over green fixtures."""
    from cairn.devices.tester.isolation import BREACHED, INDETERMINATE, OPEN, SEALED

    proofs = Path(str(scratch_dir("network-seal-retired-no-refusal-"))) / "proofs"
    proofs.mkdir(parents=True)
    standing = {"unrecorded": None, "sealed": SEALED, "open": OPEN,
                "breached": BREACHED, "indeterminate": INDETERMINATE}
    for name, verdict in standing.items():
        proof = proofs / f"test_standing_{name}.py"
        proof.write_text(GREEN_SRC, encoding="utf-8")
        if verdict is not None:
            _pose_standing(proof, verdict)

    for args in ((), ("--seal",)):
        r = subprocess.run([str(CAIRN), "test", *args, str(proofs)],
                           capture_output=True, text=True, timeout=600)
        text = r.stdout + r.stderr
        label = "`cairn test" + "".join(f" {a}" for a in args) + "`"
        for name in standing:
            assert f"test_standing_{name}" in text, \
                f"{label} never reported test_standing_{name} — the tooth would pass on an empty population:\n{text}"
        assert "REFUSED" not in text, f"{label} refused a seal:\n{text}"
        assert "seal-refused" not in text, f"{label} counted a refused seal:\n{text}"
        assert r.returncode == 0, f"{label} exited {r.returncode}, want 0:\n{text}"
    return True


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))

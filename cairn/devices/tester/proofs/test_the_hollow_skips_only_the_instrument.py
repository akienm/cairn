"""Teeth for ticket 763379e32e3b — the hollow skips only the instrument.

MEASURED 2026-10-05 on 580ad3b46cd0 (a RULE 1 fix: two checks moved out of the trees tool's
proof into a new librarian proof). Its build wrote only files under proofs/, so
``cairn test --hollow`` skipped both as instruments, measured nothing, and clearance refused
PROVED with [hollow_nothing_measured]. But the trees proof was the build's SUBJECT: the
instrument was the librarian proof watching it. The skip's own reason — "reverting the
instrument makes the reading meaningless" — is true only of the instrument.

THE RULE THESE TEETH HOLD. A file under proofs/ is skipped as an instrument only when it is one
of the ticket's proven_by proofs or a proofs/ module one of them imports (transitively). Any
other proofs/ file the build wrote is reverted and its teeth watched, like source. A build that
writes only the instrument still measures nothing (open-155ed994d17b: the gate stays hard).

Every fixture is a scratch repo with its own journal and decompose berth, the pattern of
test_the_hollow_anchor_ignores_instrument_commits.py. The fixture instrument reads its subject
proof as TEXT, never by import, the way 580ad3b46cd0's proof reads the trees proof.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 600  # measured 2026-11-21 (ticket 50987e27621c): 118 s solo through bin/cairn test once tooth 4 read seals instead of re-running three proofs; was 2700

from cairn.devices.tester.hollow import SKIP_INSTRUMENT, measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402
from cairn.tools.validation_store.validation_store import (  # noqa: E402
    sealed_fingerprint_now, standing, validations_path_for)

PROVES = {
    "763379e32e3b": {
        "1": "test_a_proof_the_build_wrote_that_is_not_the_instrument_is_measured",
        "2": "test_the_instrument_and_what_it_imports_are_still_skipped",
        "3": "test_a_build_of_only_the_instrument_still_measures_nothing",
        "4": "test_the_standing_hollow_proofs_stay_green",
    },
    # ticket 50987e27621c: the standing tooth reads the seals instead of re-running the proofs
    "50987e27621c": {"1": "test_the_standing_hollow_proofs_stay_green",
                     "2": "test_a_red_or_stale_seal_reds_the_standing_reader",
                     "3": "test_the_standing_tooth_runs_no_proof"},
}

FIXTURE = "f1x7763379e3"
TOOTH = "test_the_subject_proof_is_clean"
INSTRUMENT = "proofs/test_fixture.py"
HELPER = "proofs/helper.py"
SUBJECT = "other/proofs/test_other.py"

_HELPER_SRC = 'DIRTY = "REACHES_INTO_THE_HOLDER"\n'

_PROOF_SRC = '''\
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from proofs.helper import DIRTY

PROVES = {"%s": {"1": "%s"}}

def %s():
    p = Path(__file__).resolve().parents[1] / "%s"
    return p.is_file() and DIRTY not in p.read_text()

if __name__ == "__main__":
    ok = %s()
    print(("ok" if ok else "FAIL") + " %s")
    raise SystemExit(0 if ok else 1)
''' % (FIXTURE, TOOTH, TOOTH, SUBJECT, TOOTH, TOOTH)

_SUBJECT_DIRTY = "def test_other():\n    assert True  # REACHES_INTO_THE_HOLDER\n"
_SUBJECT_CLEAN = "def test_other():\n    assert True\n"

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}


def _git(repo, *args, at=None):
    env = dict(_ENV)
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(build: dict, writes_to: list[str], subject0: str = _SUBJECT_DIRTY) -> tuple[Path, Path, Path, dict]:
    """A scratch repo whose instrument (proofs/test_fixture.py, importing proofs/helper.py)
    stands before BUILDME, then one build commit naming the ticket writes ``build``."""
    tmp = scratch_dir("cairn-hollowsubj-")
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", repo / "other" / "proofs", commons / "tickets"):
        d.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / INSTRUMENT).write_text(_PROOF_SRC)
    (repo / HELPER).write_text(_HELPER_SRC)
    (repo / SUBJECT).write_text(subject0)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "unrelated: c0", at="2020-01-01T00:00:00")
    shas = {"c0": _git(repo, "rev-parse", "HEAD").stdout.strip()}
    for rel, text in build.items():
        (repo / rel).write_text(text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"{FIXTURE}: build", at="2020-01-02T00:00:00")
    shas["build"] = _git(repo, "rev-parse", "HEAD").stdout.strip()
    entries = [{"ticket": FIXTURE, "direction": "forward", "actor": "fixture",
                "at": at, "from": frm, "to": to, "proven_by": INSTRUMENT}
               for at, frm, to in (("2020-01-01T12:00:00", "TICKETME", "BUILDME"),
                                   ("2020-01-02T12:00:00", "BUILDME", "PROVEME"))]
    (repo / "history.json").write_text(json.dumps({"entries": entries}))
    berth = berths / "0" / "packets" / f"decompose-20200101T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": writes_to}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    return repo, commons, berths, shas


def _measure(repo, commons, berths):
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)


def _skips(f: dict) -> dict:
    return {s["file"]: s["why"] for s in f["skipped"]}


def test_a_proof_the_build_wrote_that_is_not_the_instrument_is_measured():
    """580ad3b46cd0's shape: the build cleans a proof that no crossing names and the instrument
    does not import. The hollow reverts it, and the instrument's tooth reds."""
    repo, commons, berths, c = _fixture({SUBJECT: _SUBJECT_CLEAN}, [SUBJECT])
    f = _measure(repo, commons, berths)
    assert _skips(f).get(SUBJECT) != SKIP_INSTRUMENT, ("skipped as the instrument", f["skipped"])
    assert f["measured"].get(SUBJECT) == [TOOTH], (f["measured"], f["skipped"], f["reasons"])
    assert f["commit"] == c["c0"], ("anchored at", f["commit"], c)


def test_the_instrument_and_what_it_imports_are_still_skipped():
    """The proven_by proof and the proofs/ module it imports are the instrument: listed in
    writes_to beside the subject, both are skipped and the subject is still measured."""
    repo, commons, berths, _ = _fixture(
        {SUBJECT: _SUBJECT_CLEAN, INSTRUMENT: _PROOF_SRC + "# touched\n",
         HELPER: _HELPER_SRC + "# touched\n"},
        [SUBJECT, INSTRUMENT, HELPER])
    f = _measure(repo, commons, berths)
    skips = _skips(f)
    assert skips.get(INSTRUMENT) == SKIP_INSTRUMENT, skips
    assert skips.get(HELPER) == SKIP_INSTRUMENT, skips
    assert f["measured"].get(SUBJECT) == [TOOTH], (f["measured"], skips)


def test_a_build_of_only_the_instrument_still_measures_nothing():
    """open-155ed994d17b: the gate stays hard. A build that wrote only the instrument and its
    import is not measured, and the run says it measured nothing."""
    repo, commons, berths, _ = _fixture(
        {INSTRUMENT: _PROOF_SRC + "# touched\n", HELPER: _HELPER_SRC + "# touched\n"},
        [INSTRUMENT, HELPER], subject0=_SUBJECT_CLEAN)
    f = _measure(repo, commons, berths)
    assert not f["measured"], f["measured"]
    assert any("measured nothing" in r for r in f["reasons"]), f["reasons"]
    assert f["verdict"] == "red", f["verdict"]


# TICKET 50987e27621c: THE STANDING PROOFS ARE READ FROM THEIR SEALS, NEVER RE-RUN. Measured
# 2026-11-21 on akiendelllinux, solo: re-running them took at least 1415 s, so one proof timed
# out at 900 s and the other sealed red after 1522 s. Each one carries its own seal, and validation_store.standing() reads
# that seal exactly as component_color does: a missing seal, a red seal, and a green seal
# whose source_fingerprint no longer matches the closure it recorded all read NOT proven. So
# the tooth trusts no stale green (Law 8) and re-derives nothing a seal already settled (Law 1).
STANDING = (
    "cairn/devices/tester/proofs/test_hollow.py",
    "cairn/devices/tester/proofs/test_the_hollow_anchor_ignores_instrument_commits.py",
    "cairn/devices/tester/proofs/test_the_hollow_measures_the_repaired_build.py",
)


def _unproven(paths, root=_REPO_ROOT):
    """``[(path, why)]`` for each named proof whose seal does not stand right now."""
    out = []
    for rel in paths:
        s = standing(str(Path(root) / rel))
        if not s["proven"]:
            out.append((str(rel), s["why"]))
    return out


def _plant(verdict, fingerprint):
    """A scratch component holding one proof and its seal; ``fingerprint`` is a string to
    record, or ``"match"`` for the one the proof's tree really has. Returns the proof path."""
    comp = scratch_dir("cairn-standplant-") / "comp"
    proof = comp / "proofs" / "test_planted.py"
    proof.parent.mkdir(parents=True)
    proof.write_text("def test_planted():\n    assert True\n")
    seal = {"claim": "planted", "caller": "fixture", "date": "2020-01-01T00:00:00",
            "verdict": verdict, "evidence": {"returncode": 0 if verdict == "green" else 1}}
    seal["evidence"]["source_fingerprint"] = (
        sealed_fingerprint_now(str(proof), seal) if fingerprint == "match" else fingerprint)
    seal_path = Path(validations_path_for(str(proof)))
    seal_path.parent.mkdir(parents=True)
    seal_path.write_text(json.dumps([seal]))
    return proof


def test_the_standing_hollow_proofs_stay_green():
    """The named standing proofs each stand proven RIGHT NOW: read from their seals,
    fingerprint included, never re-run (ticket 50987e27621c)."""
    bad = _unproven(STANDING)
    assert not bad, "a standing proof's seal does not stand: %s" % bad


def test_a_red_or_stale_seal_reds_the_standing_reader():
    """Ticket 50987e27621c clause 2: a red seal and a green seal over a moved fingerprint both
    read unproven, and a green seal over the real fingerprint reads proven, so a reader that
    always says red cannot pass this tooth."""
    red, stale, good = _plant("red", "match"), _plant("green", "0" * 64), _plant("green", "match")
    assert [p for p, _ in _unproven([red])] == [str(red)], "a red seal read as standing"
    found = _unproven([stale])
    assert [p for p, _ in found] == [str(stale)], "a green seal over a moved fingerprint read as standing"
    assert "HORIZON HAS CLOSED" in found[0][1], found
    assert _unproven([good]) == [], "a green seal over the real fingerprint read as unproven"


def test_the_standing_tooth_runs_no_proof():
    """Ticket 50987e27621c clause 3: no subprocess call here runs a proof (none hands it
    sys.executable or a proofs/ path), and the standing tooth answers through standing()."""
    tree = ast.parse(Path(__file__).read_text())
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"):
            continue
        seg = ast.dump(node)
        assert "attr='executable'" not in seg, ("a subprocess call runs python", node.lineno)
        names = [n.value for n in ast.walk(node)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        assert not any("proofs/" in s or s.endswith(".py") for s in names), (
            "a subprocess call names a proof", node.lineno, names)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    calls = lambda f: {c.func.id for c in ast.walk(funcs[f])
                       if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
    assert "_unproven" in calls("test_the_standing_hollow_proofs_stay_green"), calls("test_the_standing_hollow_proofs_stay_green")
    assert "standing" in calls("_unproven"), calls("_unproven")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))

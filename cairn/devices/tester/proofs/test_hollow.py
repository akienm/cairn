"""Teeth for `cairn test --hollow` — does the hollow detector itself hold up?

THE PROOF OF AN INSTRUMENT HAS TO ANSWER A HARDER QUESTION THAN "does it run": it has to
show the instrument distinguishes the two readings it exists to tell apart. So the fixture
below builds a two-commit repo carrying BOTH cases at once — one file a declared tooth
really checks, one file nothing checks — and requires the verb to name exactly one of them.
A detector that called both hollow, or neither, would pass a smoke test and be worthless.

The fixture repo is real git, not a mock: the whole mechanism under test is `git worktree
add` and `git show <commit>:<path>`, so mocking git would prove the mock.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.hollow import (  # noqa: E402
    HollowUnmeasurable, SKIP_INSTRUMENT, measure,
)
from cairn.devices.tester.scratch import scratch_dir, scratch_worktree  # noqa: E402
from cairn.devices.tester.validation_store import (  # noqa: E402
    VALIDATION_FIELDS, read_validations, persist_validation, record_hollow,
)
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "d0f2b03952e3": {
        "1": "test_a_reverted_file_reds_its_declared_tooth_and_a_checked_by_nothing_file_is_named_hollow",
        "2": "test_the_same_run_names_the_hollow_file_and_exits_the_verb_non_zero",
        "3": "test_the_live_tree_is_byte_identical_after_a_run_that_raises_midway",
        "4": "test_evidence_hollow_lands_inside_the_seal_and_the_eight_fields_still_stand",
        "5": "test_the_live_run_reads_every_writes_to_file_it_did_not_skip_for_a_named_reason",
    }
}

FIXTURE = "f1x7u2e00001"

_PROOF_SRC = '''\
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import subject

def test_value_is_two():
    return subject.VALUE == 2

if __name__ == "__main__":
    ok = False
    try:
        ok = test_value_is_two()
    except Exception:
        ok = False
    print(("ok" if ok else "FAIL") + " test_value_is_two")
    raise SystemExit(0 if ok else 1)
'''


def _git(repo, *args, **kw):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, **kw)


def _fixture(tmp: Path, *, with_added: bool = False) -> tuple[Path, Path]:
    """A two-commit repo plus the commons entry the verb reads, wired like a real ticket.

    `subject.py` is what the tooth checks; `unchecked.py` is in the SAME writes_to list and
    nothing checks it. Both change between the commits, so the two readings differ only in
    whether a declared tooth is sensitive to the file — which is the one thing being measured.
    """
    repo, commons = tmp / "repo", tmp / "commons"
    (repo / "proofs").mkdir(parents=True)
    (commons / "tickets").mkdir(parents=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    _git(repo, "init", "-q", "-b", "main", env=env)

    (repo / "subject.py").write_text("VALUE = 1\n")
    (repo / "unchecked.py").write_text("MARK = 'before the build'\n")
    src = _PROOF_SRC.replace("import subject\n", "import subject\nimport added_by_build\n") \
        if with_added else _PROOF_SRC
    (repo / "proofs" / "test_fixture.py").write_text(
        'PROVES = {"%s": {"1": "test_value_is_two"}}\n\n' % FIXTURE + src)
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-qm", "before the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-01T00:00:00", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00"})

    if with_added:
        (repo / "added_by_build.py").write_text("EXTRA = 9\n")
    (repo / "subject.py").write_text("VALUE = 2\n")
    (repo / "unchecked.py").write_text("MARK = 'after the build'\n")
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-qm", "the build",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-03T00:00:00", "GIT_COMMITTER_DATE": "2020-01-03T00:00:00"})

    berth = tmp / "decompose.json"
    berth.write_text(json.dumps({"sub_problems": [
        {"what": "the build", "kind": "build",
         "writes_to": ["subject.py", "unchecked.py", "proofs/test_fixture.py"]}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({
        "id": FIXTURE,
        "chart_chain": {"decompose": str(berth)},
        "crossings": [{"to": "BUILDME", "date": "2020-01-02T00:00:00",
                       "proven_by": "proofs/test_fixture.py"}]}))
    return repo, commons


def _measured(tmp: Path) -> dict:
    repo, commons = _fixture(tmp)
    return measure(FIXTURE, repo_root=repo, commons=commons, timeout=60)


def test_a_reverted_file_reds_its_declared_tooth_and_a_checked_by_nothing_file_is_named_hollow():
    """THE DISCRIMINATING TOOTH — both readings from ONE run, over two files that differ
    only in whether a tooth is sensitive to them. Asserting either half alone would pass on
    a detector stuck at 'everything is hollow' or stuck at 'nothing is'."""
    f = _measured(scratch_dir("cairn-hollowproof-"))
    assert f["measured"]["subject.py"] == ["test_value_is_two"], f["measured"]
    assert f["measured"]["unchecked.py"] == [], f["measured"]
    assert f["hollow"] == ["unchecked.py"], f["hollow"]
    # And the instrument itself was skipped for the stated reason, not silently dropped.
    assert [s["file"] for s in f["skipped"]] == ["proofs/test_fixture.py"], f["skipped"]
    assert f["skipped"][0]["why"] == SKIP_INSTRUMENT, f["skipped"]
    return True


def test_the_same_run_names_the_hollow_file_and_exits_the_verb_non_zero():
    """A finding nobody's exit code carries is a finding that does not gate anything.

    THE EXIT CODE IS READ OFF THE FIXTURE, NOT OFF A LIVE TICKET — and that is the claiming
    criterion's own wording ("a green-under-revert FIXTURE is named hollow with exit non-zero").
    The first cut of this tooth ran the verb against live ticket 9579a6f9cec6 and asserted
    `rc == 1`, which was wrong twice over. It flaked (2 reds in 11 runs; the verb run ALONE was
    6-for-6 byte-identical, so the nondeterminism was in the live reading, and the traceback was
    never caught) — and worse, it was a SNAPSHOT assertion of exactly the kind this file's live
    tooth exists to avoid: `rc == 1` means "9579 is still hollow today", so the tooth would have
    redded outright on the day someone wrote 9579's missing teeth. That is the day the system got
    BETTER. The fixture is hollow BY CONSTRUCTION and cannot move under anyone's later work; the
    live verb keeps its own tooth below, which asserts invariants and never the day's counts.
    """
    tmp = scratch_dir("cairn-hollowproof-")
    repo, commons = _fixture(tmp)
    f = measure(FIXTURE, repo_root=repo, commons=commons, timeout=60)
    assert f["verdict"] == "red", f["verdict"]
    assert any("hollow: unchecked.py reverted, no declared tooth redded" == r
               for r in f["reasons"]), f["reasons"]

    # The CLI is what actually returns the code, so the code is read from the CLI, not inferred.
    # The child points the verb's two roots at the fixture and changes NOTHING else: it runs the
    # real `_hollow_run` — its reasons printing, its summary line, and its `red -> 1` return.
    child = subprocess.run(
        [sys.executable, "-c",
         "import sys, functools, pathlib\n"
         "sys.path.insert(0, %r)\n"
         "import cairn.devices.tester.hollow as h\n"
         "import cairn.devices.tester.cli as cli\n"
         "h.measure = functools.partial(h.measure, commons=pathlib.Path(%r))\n"
         "cli.REPO_ROOT = pathlib.Path(%r)\n"
         "sys.exit(cli.main(['--hollow', %r, '-q']))\n"
         % (str(_REPO_ROOT), str(commons), str(repo), FIXTURE)],
        cwd=str(_REPO_ROOT), capture_output=True, text=True)
    assert child.returncode == 1, (child.returncode, child.stdout[-2000:], child.stderr[-2000:])
    # The exit code and the NAMED file come from the same run — a bare non-zero could be a crash.
    assert "unchecked.py" in child.stdout, child.stdout
    return True


def _tree_state() -> tuple[str, str]:
    """git's own view of the live tree, plus a content hash — two readings, because
    `git status` is blind to a file rewritten with identical mtime and different bytes."""
    status = _git(_REPO_ROOT, "status", "--porcelain").stdout
    h = hashlib.sha256()
    for rel in sorted(_git(_REPO_ROOT, "ls-files").stdout.split()):
        p = _REPO_ROOT / rel
        if p.is_file():
            h.update(rel.encode())
            h.update(p.read_bytes())
    return status, h.hexdigest()


def test_the_live_tree_is_byte_identical_after_a_run_that_raises_midway():
    """THE SAFETY PROPERTY, MEASURED UNDER THE CASE THAT BREAKS THE NAIVE DESIGN.

    A revert-in-place implementation passes a happy-path check and leaves the operator's tree
    wrong the first time a run dies between the revert and the restore. So the tester here is
    one that RAISES on its second proof run, and the tree is compared across the raise — plus
    `git worktree list`, because a worktree leaks in two places and removing the directory
    without deregistering it leaves git naming a path that is not there.
    """
    class Exploding:
        def __init__(self):
            self.n = 0

        def run_proof(self, path, **kw):
            self.n += 1
            if self.n > 1:
                raise RuntimeError("fixture: the run dies midway, deliberately")
            return {"evidence": {"teeth_green": ["test_value_is_two"], "teeth_red": []}}

    before_status, before_hash = _tree_state()
    before_wt = _git(_REPO_ROOT, "worktree", "list").stdout

    tmp = scratch_dir("cairn-hollowproof-")
    repo, commons = _fixture(tmp)
    raised = False
    try:
        measure(FIXTURE, repo_root=repo, commons=commons, timeout=60, tester=Exploding())
    except RuntimeError:
        raised = True
    assert raised, "the fixture tester was supposed to raise and did not"

    after_status, after_hash = _tree_state()
    assert (before_status, before_hash) == (after_status, after_hash), \
        "the live tree moved across a hollow run that raised midway"

    # The worktree the raising run made is swept by the door's atexit hook, which has not run
    # yet inside this process — so what is asserted here is the thing that would be a LEAK if
    # it were wrong: the live repo gained no worktree at any path but that scratch one.
    added = [ln for ln in _git(_REPO_ROOT, "worktree", "list").stdout.splitlines()
             if ln not in before_wt.splitlines()]
    assert all("/cairn-hollow-" in ln for ln in added), added

    # And a worktree taken and released in a CHILD process leaves nothing behind at all —
    # which is the sweep itself, measured rather than assumed from the atexit registration.
    child = subprocess.run(
        [sys.executable, "-c",
         "import sys;sys.path.insert(0,%r)\n"
         "from cairn.devices.tester.scratch import scratch_worktree\n"
         "import subprocess\n"
         "h=subprocess.run(['git','-C',%r,'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()\n"
         "print(scratch_worktree(h, repo_root=%r))\n" % (str(_REPO_ROOT), str(_REPO_ROOT), str(_REPO_ROOT))],
        capture_output=True, text=True)
    made = child.stdout.strip().splitlines()[-1] if child.stdout.strip() else ""
    assert made, child.stderr[-500:]
    assert not Path(made).exists(), f"the worktree directory survived its process: {made}"
    assert made not in _git(_REPO_ROOT, "worktree", "list").stdout, \
        f"the worktree REGISTRATION survived its process: {made}"
    return True


def test_evidence_hollow_lands_inside_the_seal_and_the_eight_fields_still_stand():
    """The reading rides `evidence`, keyed by ticket — and the record is still the ratified eight."""
    tmp = scratch_dir("cairn-hollowseal-")
    proof = tmp / "component" / "proofs" / "test_thing.py"
    proof.parent.mkdir(parents=True)
    proof.write_text("# a proof standing in for a real one\n")

    # THE EIGHT ARE SPELLED OUT AND THEN CHECKED AGAINST THE LIVE TUPLE, not filtered by it.
    # Filtering would make this tooth agree with whatever the shape happened to be — including
    # a shape this ticket had quietly changed, which is the one thing it is here to catch.
    seed = {
        "claim": "the thing holds", "caller": "fixture", "date": "2026-09-09T00:00:00",
        "method": "ran it", "verdict": "green",
        "evidence": {"returncode": 0, "teeth_green": ["test_thing"],
                     "seal": {"verdict": "open", "detail": "none: no seal requested"}},
        "falsifier": "the thing stops holding",
        "horizon": "until the proof or the code it proves changes",
    }
    assert set(seed) == set(VALIDATION_FIELDS), sorted(set(seed) ^ set(VALIDATION_FIELDS))
    persist_validation(seed, proof_path=str(proof))

    assert record_hollow(str(proof), "d0f2b03952e3", {"a.py": ["test_thing"], "b.py": []}) is True
    landed = read_validations(str(proof))[-1]
    assert set(landed) == set(VALIDATION_FIELDS), sorted(set(landed) ^ set(VALIDATION_FIELDS))
    assert landed["evidence"]["hollow"]["d0f2b03952e3"] == {"a.py": ["test_thing"], "b.py": []}
    # The seal and verdict came through untouched — a hollow run seals nothing about outcome.
    assert landed["verdict"] == "green" and landed["evidence"]["seal"]["verdict"] == "open"
    # A second ticket's reading joins it rather than replacing it — the keying is the point.
    record_hollow(str(proof), "other0000000", {"c.py": []})
    again = read_validations(str(proof))[-1]["evidence"]["hollow"]
    assert set(again) == {"d0f2b03952e3", "other0000000"}, sorted(again)
    # And a proof with nothing standing is False, not an invented seal.
    assert record_hollow(str(tmp / "component" / "proofs" / "test_absent.py"), "x", {}) is False
    return True


def test_the_live_run_reads_every_writes_to_file_it_did_not_skip_for_a_named_reason():
    """THE LIVE FIRING, against ticket 9579a6f9cec6 — invariants, never the day's counts.

    Snapshotting "5 hollow" here would red the day someone writes the missing teeth, which is
    the day the system got BETTER. What must hold forever is the instrument's contract: every
    writes_to file is either measured or skipped for one of the two stated reasons, no file is
    both, the pre-build commit really precedes the crossing, and the whole thing fits inside
    the ticket's five-minute bound.
    """
    import time
    from cairn.devices.tester.hollow import writes_to, _ticket_path
    started = time.time()
    proc = subprocess.run([sys.executable, "-m", "cairn.devices.tester.cli",
                           "--hollow", "9579a6f9cec6"],
                          cwd=str(_REPO_ROOT), capture_output=True, text=True)
    elapsed = time.time() - started
    assert proc.returncode in (0, 1), (proc.returncode, proc.stderr[-800:])
    assert elapsed < 300, f"a single ticket took {elapsed:.0f}s against the ticket's 5-minute bound"

    ticket = json.loads(_ticket_path("9579a6f9cec6").read_text(encoding="utf-8"))
    declared_files = writes_to(ticket)
    f = measure("9579a6f9cec6", repo_root=_REPO_ROOT, timeout=120)
    seen = set(f["measured"]) | {s["file"] for s in f["skipped"]} | set(f["unchanged"])
    assert seen == set(declared_files), sorted(seen ^ set(declared_files))
    assert not (set(f["measured"]) & {s["file"] for s in f["skipped"]}), "a file both measured and skipped"
    assert f["measured"], "every file was skipped — a measurement of the empty set is not a pass"
    for s in f["skipped"]:
        assert s["why"] in (SKIP_INSTRUMENT,) or "not a path in this repo" in s["why"] \
            or "not present at HEAD" in s["why"], s
    # The commit reverted to must genuinely precede the crossing that named the build.
    at = _git(_REPO_ROOT, "show", "-s", "--format=%cI", f["commit"]).stdout.strip()
    assert at[:19] < f["buildme_at"][:19], (at, f["buildme_at"])
    return True


def test_a_run_that_could_not_be_measured_says_so_instead_of_passing():
    """Law 3 held as a type: 'not measured' may not travel through the same return as 'clean'."""
    tmp = scratch_dir("cairn-hollowproof-")
    repo, commons = _fixture(tmp)
    t = json.loads((commons / "tickets" / f"{FIXTURE}-fixture.json").read_text())
    t["crossings"] = [{"to": "PROVEME", "date": "2020-01-02T00:00:00"}]  # no BUILDME, no proof
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps(t))
    try:
        measure(FIXTURE, repo_root=repo, commons=commons, timeout=60)
    except HollowUnmeasurable as why:
        assert "BUILDME" in str(why), why
        return True
    raise AssertionError("a ticket with no BUILDME crossing was measured instead of refused")


def test_an_unchanged_file_is_reported_unwritten_not_hollow():
    """A no-op reversion reds nothing BY CONSTRUCTION — calling that hollow would be the
    right verdict reached for entirely the wrong reason, which is the coin-toss green."""
    tmp = scratch_dir("cairn-hollowproof-")
    repo, commons = _fixture(tmp)
    berth = json.loads((tmp / "decompose.json").read_text())
    berth["sub_problems"][0]["writes_to"].append("untouched.py")
    (tmp / "decompose.json").write_text(json.dumps(berth))
    # Present and identical at BOTH commits — so reverting it changes nothing.
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "HEAD~1"], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "main"], capture_output=True)
    f = measure(FIXTURE, repo_root=repo, commons=commons, timeout=60)
    assert "untouched.py" not in f["measured"], f["measured"]
    return True


def test_a_proof_under_revert_imports_the_worktree_and_not_the_live_tree():
    """THE ASSUMPTION THE WHOLE DESIGN RESTS ON, MEASURED RATHER THAN REASONED.

    `cairn` is installed editable, so a path hook in site-packages points `import cairn` at
    the LIVE tree. If that hook won the resolution, every proof run in a worktree would import
    the code the revert was supposed to remove and nothing would ever red — the detector would
    report a clean corpus forever. What actually wins is each proof's own
    `sys.path.insert(0, _REPO_ROOT)` off `__file__`, and this asserts that, in a subprocess,
    the way a real proof runs.
    """
    head = _git(_REPO_ROOT, "rev-parse", "HEAD").stdout.strip()
    wt = scratch_worktree(head, repo_root=_REPO_ROOT)
    probe = wt / "cairn" / "devices" / "tester" / "proofs" / "_where_did_cairn_come_from.py"
    probe.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[4]))\n"
        "import cairn.devices.tester.scratch as m\nprint(m.__file__)\n")
    out = subprocess.run([sys.executable, str(probe)], cwd=str(wt),
                         capture_output=True, text=True).stdout.strip()
    assert out.startswith(str(wt)), f"the proof imported {out}, not the worktree at {wt}"
    assert not out.startswith(str(_REPO_ROOT) + "/cairn"), out
    return True


def test_a_file_absent_before_the_build_is_REMOVED_and_not_emptied():
    """THE COUNTERFACTUAL MUST BE 'THE BUILD HAD NOT HAPPENED', AND EMPTYING IS A WEAKER ONE.

    An emptied module still imports — as a module with nothing in it — and still satisfies
    every path check. A file that did not EXIST before the build must therefore be removed, or
    the reversion silently measures a world where the build half-happened. The two are told
    apart by behaviour rather than by inspecting the act: the fixture's proof IMPORTS a module
    the build added, so removing it kills the import and the reading comes back UNREADABLE
    (the proof printed no teeth at all), while emptying it would let the import succeed and
    produce an ordinary measured reading. This tooth was written because a mutation that
    emptied instead of removing left all eight teeth green — the bound was in the ticket and
    in the code and in nothing that could fail.
    """
    tmp = scratch_dir("cairn-hollowproof-")
    repo, commons = _fixture(tmp, with_added=True)
    berth = json.loads((tmp / "decompose.json").read_text())
    berth["sub_problems"][0]["writes_to"].append("added_by_build.py")
    (tmp / "decompose.json").write_text(json.dumps(berth))

    f = measure(FIXTURE, repo_root=repo, commons=commons, timeout=60)
    assert "added_by_build.py" in f["unran"], (f["unran"], f["measured"])
    assert f["unran"]["added_by_build.py"] == ["proofs/test_fixture.py"], f["unran"]
    assert any("unreadable: added_by_build.py" in r for r in f["reasons"]), f["reasons"]
    # And it is NOT filed as hollow: "the instrument stopped running" and "nothing checks
    # this file" are different findings and must not collapse into one.
    assert "added_by_build.py" not in f["hollow"], f["hollow"]
    return True


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))


def test_a_same_size_rewrite_inside_one_second_is_read_fresh_and_not_from_bytecode():
    """THE DEFECT THAT MADE THIS INSTRUMENT REPORT THE OPPOSITE OF THE TRUTH, held deterministic.

    The verb reverts a file, runs the proof, restores it and runs again — three writes that
    routinely land inside one clock second. CPython keys `.pyc` validity on the source's
    (mtime, size) with WHOLE-SECOND mtime, so when the two versions are the same LENGTH both
    fields match and the reader gets bytecode compiled from a version no longer on disk. In the
    fixture that surfaced as `unchecked.py` — which nothing checks — reading as COVERED, because
    the PREVIOUS file's reversion was still in the cache and the wrong file was credited for the
    red. It fired 3 times in 14 runs, and a 1-in-5 wrong answer from a measuring instrument is
    worse than a loud break.

    THE COLLISION IS FORCED HERE, NOT WAITED FOR: both versions are the same length and the
    mtime is stamped identical by hand, so the stale-cache condition holds on every run rather
    than on the runs where the clock happens to cooperate. The tooth asserts BOTH halves from one
    setup — that the collision is real (else it would pass on a machine where nothing was ever
    wrong) and that the purge defeats it.
    """
    from cairn.devices.tester.hollow import _purge_bytecode
    tmp = scratch_dir("cairn-hollowpyc-")
    (tmp / "subject.py").write_text("VALUE = 2\n")
    (tmp / "reader.py").write_text("import subject\nprint(subject.VALUE)\n")

    def read() -> str:
        return subprocess.run([sys.executable, "reader.py"], cwd=str(tmp),
                              capture_output=True, text=True).stdout.strip()

    stamp = (1_600_000_000, 1_600_000_000)
    os.utime(tmp / "subject.py", stamp)
    assert read() == "2", "the fixture did not read its own starting value"

    # The reversion: same LENGTH, same stamped mtime — the exact shape _revert produces.
    (tmp / "subject.py").write_text("VALUE = 1\n")
    os.utime(tmp / "subject.py", stamp)
    assert len("VALUE = 1\n") == len("VALUE = 2\n"), "the collision needs equal sizes to exist"
    assert read() == "2", \
        "the stale-bytecode collision did not occur, so this tooth is not measuring what it claims"

    # And the purge is what makes the reading true again — the source now wins.
    _purge_bytecode(tmp)
    assert not list(tmp.rglob("__pycache__")), "the purge left a cache behind"
    assert read() == "1", "after the purge the reader STILL did not see the file that is on disk"
    return True

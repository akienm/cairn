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
    HollowUnmeasurable, SKIP_INSTRUMENT, SKIP_RECORD, _restore, measure,
)
from cairn.devices.tester.scratch import git_env, scratch_dir, scratch_worktree  # noqa: E402
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
        "6": "test_a_proof_named_on_an_earlier_crossing_still_counts_and_the_file_it_checks_is_not_hollow",
        "7": "test_a_proof_declaring_no_tooth_for_this_ticket_is_dropped_and_never_run",
    },
    "95e3b9911dd0": {
        # THE LETTERED KEYS ARE THE ONES THE GATE ASKS FOR. This ticket's falsifier enumerates
        # its DONE-when list (a)..(d), and until 2026-09-10 proof_coverage.clauses() read digit
        # markers only — so a four-clause falsifier came back as the one-clause fallback "all"
        # and three of its four clauses needed no tooth. Fixed in this voyage (_lettered_run);
        # what it fixed shows up here, as four demands instead of one.
        "a": "test_the_reader_names_no_stored_chart_chain_and_calls_the_derivation_instead",
        "b": "test_no_ticket_in_the_live_commons_carries_a_stored_chart_chain",
        "c": "test_a_ticket_no_decompose_berth_claims_raises_the_named_lack_not_an_empty_list",
        "d": "test_the_derived_decompose_berth_equals_a_stored_one_the_fixture_authored",
        # Clause (c) has a SECOND half the key above cannot carry — "never an AttributeError,
        # the two bare-string carriers are the regression test". One proof declares one tooth
        # per clause key, so that half stands under "4" below rather than going unrecorded.
        #
        # THE NUMBERED KEYS BELOW ARE THE VALIDATE BERTH'S TWELVE CRITERIA, kept because they
        # are the map from a criterion to the tooth that answers it. The gate does not read
        # them for this ticket (it wants a..d); a reader tracing a criterion does.
        "1": "test_the_reader_names_no_stored_chart_chain_and_calls_the_derivation_instead",
        "2": "test_the_derived_decompose_berth_equals_a_stored_one_the_fixture_authored",
        "3": "test_a_ticket_no_decompose_berth_claims_raises_the_named_lack_not_an_empty_list",
        "4": "test_a_bare_string_chart_chain_is_no_longer_dereferenced_by_the_reader",
        "6": "test_the_derived_reader_teeth_red_against_the_stored_field_reader",
        "7": "test_no_ticket_in_the_live_commons_carries_a_stored_chart_chain",
        "8": "test_the_migration_removes_one_key_and_carries_what_it_cannot_re_derive_to_notes",
        "9": "test_the_migrations_dry_run_names_exactly_the_files_the_apply_run_writes",
        "10": "test_the_watch_probe_reports_a_carrier_that_reappears_and_does_not_clear_on_zero_alone",
        "11": "test_the_watch_probe_reports_a_carrier_that_reappears_and_does_not_clear_on_zero_alone",
    },
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
    """Git against the FIXTURE repo — through the door's own env scrub, on purpose.

    These fixtures build scratch repos, and a scratch repo is exactly what an inherited
    ``GIT_INDEX_FILE`` steals: run under a git hook (which is how the reseal door runs proofs)
    every ``git -C <fixture>`` here would resolve its index against the caller's tree instead.
    Importing ``git_env`` rather than re-deriving the tuple keeps ONE answer to "which variables
    lie about which repo" — and means these teeth exercise the door they depend on."""
    kw.setdefault("env", git_env())
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
    # git_env(), NOT os.environ: the identity fields are what this dict is FOR, and inheriting
    # the rest is how a hook's GIT_INDEX_FILE reached the fixture repo (see _git above).
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
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

    _berth_decompose(tmp, ["subject.py", "unchecked.py", "proofs/test_fixture.py"])
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    _journal(repo, [{"to": "BUILDME", "proven_by": "proofs/test_fixture.py"}])
    return repo, commons


def _berths_root(tmp: Path) -> Path:
    """The fixture world's THIRD root.

    Until 2026-09-10 a fixture needed two — its own repo and its own commons — because the
    decompose berth's address was a string on the ticket and a string needs no store. Deriving
    the berth (ticket 95e3b9911dd0) made the berth STORE part of what a measurement reads, so a
    fixture that cannot supply one is measuring production. The layout mirrors the live store
    exactly, because chain._packet_index globs ``<root>/*/packets/*.json`` and a flattened
    sandbox would index nothing — green for want of looking."""
    return tmp / "berths"


def _berth_path(tmp: Path) -> Path:
    return _berths_root(tmp) / "0" / "packets" / "decompose-20200103T000000-f1x7u2e00001.json"


def _berth_decompose(tmp: Path, files: list) -> Path:
    """One berthed decompose packet CLAIMING the fixture ticket. The claim is the whole
    mechanism — the derivation finds a berth by the ticket it names, never by its filename."""
    path = _berth_path(tmp)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "ticket": FIXTURE, "stage": "decompose",
        "sub_problems": [{"what": "the build", "kind": "build", "writes_to": files}]}),
        encoding="utf-8")
    return path


def _journal(repo: Path, crossings: list[dict], *, at: str = "history.json") -> Path:
    """The fixture world's crossing record, in the ONE shape the derivation reads.

    Since 2026-09-10 (ruling crossings-are-derived-never-written) a ticket carries no
    ``crossings`` key and hollow derives them from history.json in the two roots it is handed.
    So a fixture that wants a crossing writes a journal — which is also what ``emit`` does, so
    the fixture and the world now agree about where a crossing comes from. Untracked on
    purpose: the journal describes the build, it is not part of it, and hollow must not revert it.
    """
    path = repo / at
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    for i, one in enumerate(crossings):
        entry = {"ticket": FIXTURE, "direction": "forward", "actor": "fixture",
                 "at": f"2020-01-02T00:0{i}:00"}
        entry.update(one)
        entries.append(entry)
    path.write_text(json.dumps({"entries": entries}, indent=2), encoding="utf-8")
    return path


def _measured(tmp: Path) -> dict:
    repo, commons = _fixture(tmp)
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=_berths_root(tmp), timeout=60)


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
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=_berths_root(tmp), timeout=60)
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
         "h.measure = functools.partial(h.measure, commons=pathlib.Path(%r), "
         "berths_root=%r)\n"
         "cli.REPO_ROOT = pathlib.Path(%r)\n"
         "sys.exit(cli.main(['--hollow', %r, '-q']))\n"
         % (str(_REPO_ROOT), str(commons), str(_berths_root(tmp)), str(repo), FIXTURE)],
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
        measure(FIXTURE, repo_root=repo, commons=commons, berths_root=_berths_root(tmp), timeout=60, tester=Exploding())
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
    both, the pre-build commit really precedes the crossing, and the per-file loop shares ONE
    worktree rather than building a fresh one for every file.

    THE WALL-CLOCK BOUND THAT STOOD HERE WAS A COIN TOSS, AND MEASUREMENT KILLED IT.
    Ticket d0f2b03952e3 wrote "a single ticket takes more than five minutes -> the design is
    wrong", and named its own remedy in the same breath: "the per-file loop shares one worktree
    and one instance swap, not a different design". This tooth asserted the five minutes
    literally. Four readings of the same command on one box, 2026-09-10: 157.4s, ~300s, 366.3s,
    382.2s — a 2.4x spread with the instrument unchanged between them, and the 382s run's own
    log records loadavg climbing 1.88 -> 6.79 while it ran. Two of the four redded. A tooth
    whose verdict is set by what else the laptop happens to be doing is not a measurement of
    this code, and under Law 8 a random red still costs the resolver every time it fires.

    AND THE BOUND COULD NEVER HAVE CAUGHT WHAT IT WAS WRITTEN FOR. The instrumented run breaks
    down as 156.8s of a 157.4s total spent inside 27 pytest invocations — 99.6% of the wall is
    this verb running OTHER components' proofs. The worktree setup the clause is actually about
    is ~0.6s. Regressing to one worktree per file would move the total by well under one
    percent: invisible beneath a 2.4x load swing. The clock was reading the box's speed and had
    no view of the design at all.

    What replaces it reads the design directly and does not care how loaded the box is: count
    the worktree creations in one real run over a ticket with many declared files. One shared
    worktree is the contract; one per file is precisely the failure d0f2b03952e3 names. The
    loose guard at the end catches a hang, which is the only thing a wall clock here can
    honestly report.

    ONE RUN, NOT TWO. This tooth used to fire the whole measurement twice — once as a timed
    CLI subprocess and again in-process for the invariants — so it paid the full cost twice and
    threw the expensive half away. That is why a session asserting "under 300s" took 455s of
    wall to do it. The CLI return path keeps its own tooth above
    (test_the_same_run_names_the_hollow_file_and_exits_the_verb_non_zero), which drives the real
    `_hollow_run` over the fixture world, so nothing is uncovered by measuring once here.
    """
    import time
    from cairn.devices.tester import hollow as _h
    from cairn.devices.tester.hollow import writes_to, _ticket_path

    made: list[str] = []
    real_worktree = _h.scratch_worktree

    def counting(*a, **kw):
        wt = real_worktree(*a, **kw)
        made.append(str(wt))
        return wt

    _h.scratch_worktree = counting
    started = time.time()
    try:
        f = measure("9579a6f9cec6", repo_root=_REPO_ROOT, timeout=120)
    finally:
        _h.scratch_worktree = real_worktree
    elapsed = time.time() - started

    ticket = json.loads(_ticket_path("9579a6f9cec6").read_text(encoding="utf-8"))
    declared_files = writes_to(ticket)
    seen = set(f["measured"]) | {s["file"] for s in f["skipped"]} | set(f["unchanged"])
    assert seen == set(declared_files), sorted(seen ^ set(declared_files))
    assert not (set(f["measured"]) & {s["file"] for s in f["skipped"]}), "a file both measured and skipped"
    assert f["measured"], "every file was skipped — a measurement of the empty set is not a pass"
    for s in f["skipped"]:
        assert s["why"] in (SKIP_INSTRUMENT,) or "not a path in this repo" in s["why"] \
            or "not present at HEAD" in s["why"], s

    # THE DESIGN INVARIANT the killed clock was a proxy for. Many files, ONE worktree.
    assert len(declared_files) > 1, \
        f"this tooth can say nothing about a per-file loop that runs once: {declared_files}"
    assert made == [f["worktree"]], \
        (f"the loop built {len(made)} worktree(s) for {len(declared_files)} declared files; "
         f"ticket d0f2b03952e3 requires ONE shared worktree for the whole run: {made}")

    # A hang is the only thing a wall clock can honestly report here — see the docstring.
    assert elapsed < 1800, f"the run took {elapsed:.0f}s, which is a hang, not a slow box"

    # The commit reverted to must genuinely precede the crossing that named the build.
    at = _git(_REPO_ROOT, "show", "-s", "--format=%cI", f["commit"]).stdout.strip()
    assert at[:19] < f["buildme_at"][:19], (at, f["buildme_at"])
    return True


def test_a_run_that_could_not_be_measured_says_so_instead_of_passing():
    """Law 3 held as a type: 'not measured' may not travel through the same return as 'clean'."""
    tmp = scratch_dir("cairn-hollowproof-")
    repo, commons = _fixture(tmp)
    _journal(repo, [{"to": "PROVEME"}])  # rewritten: no BUILDME anywhere, and no proof named
    try:
        measure(FIXTURE, repo_root=repo, commons=commons, berths_root=_berths_root(tmp), timeout=60)
    except HollowUnmeasurable as why:
        assert "BUILDME" in str(why), why
        return True
    raise AssertionError("a ticket with no BUILDME crossing was measured instead of refused")


def test_a_reversion_that_cannot_be_UNDONE_stops_the_run_instead_of_measuring_past_it():
    """AN UNPERFORMED UNDO DOES NOT FAIL ITS OWN FILE — IT CORRUPTS EVERY FILE AFTER IT.

    The run reverts one file at a time on top of HEAD and restores it before the next, so the
    counterfactual is always \"everything as it stands, except this one file\". If the restore
    silently does nothing, file N stays reverted while N+1 is measured: N+1's teeth red for a
    reason that has nothing to do with N+1, that red is read as \"a declared tooth checks this
    file\", and a file that really is hollow is reported ok. **A hollow read as green, produced
    inside the verb whose entire job is catching one** — worse than a red, because a peer leans
    on it (Law 8).

    NOT HYPOTHETICAL, measured 2026-09-09: under a git hook's environment
    (``GIT_INDEX_FILE=.git/index``, a RELATIVE path) this checkout resolved against the
    caller's index instead of the worktree's and did exactly that — the tooth below this one in
    the file asserted one hollow file and got none. ``git_env`` is the fix for that cause; this
    tooth is the fix for the CLASS, because the next thing that stops a checkout will not be an
    env var, and Law 3 says the un-taken measurement may not ride home in the clean return.

    A directory that is no repository at all is the cheapest way to make the checkout fail for
    a reason that is not the one already fixed — which is the point: the guard must not be
    coupled to the env var that revealed it.
    """
    tmp = scratch_dir("cairn-hollowrestore-")
    (tmp / "not_a_repo").mkdir()
    (tmp / "not_a_repo" / "subject.py").write_text("VALUE = 1\n")
    try:
        _restore(tmp / "not_a_repo", "subject.py")
    except HollowUnmeasurable as why:
        assert "restore" in str(why) and "subject.py" in str(why), why
        return True
    raise AssertionError(
        "a checkout that could not restore the reverted file returned quietly — every file "
        "measured after it would be read against a tree still carrying the last reversion")


def test_an_unchanged_file_is_reported_unwritten_not_hollow():
    """A no-op reversion reds nothing BY CONSTRUCTION — calling that hollow would be the
    right verdict reached for entirely the wrong reason, which is the coin-toss green."""
    tmp = scratch_dir("cairn-hollowproof-")
    repo, commons = _fixture(tmp)
    berth = json.loads(_berth_path(tmp).read_text())
    berth["sub_problems"][0]["writes_to"].append("untouched.py")
    _berth_path(tmp).write_text(json.dumps(berth))
    # Present and identical at BOTH commits — so reverting it changes nothing.
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "HEAD~1"], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "main"], capture_output=True)
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=_berths_root(tmp), timeout=60)
    assert "untouched.py" not in f["measured"], f["measured"]
    return True


def test_a_record_named_in_writes_to_is_skipped_and_a_plain_json_beside_it_is_not():
    """A RECORD REDS NOTHING BY CONSTRUCTION, AND CALLING THAT HOLLOW IS A COLLAPSE (Law 7).

    `history.json` is append-only, `state.json` is compiled from the component's tickets, and
    anything under `validations/` is written BY the tester about a proof. No proof asserts over
    any of them, so reverting one can only ever red nothing — which is the same sentence the
    verb already prints for a build whose CODE nothing checks. Two findings, one word, and they
    send a builder to opposite work: one to nothing at all, one to go write a tooth that cannot
    exist.

    AND THE SECOND HALF IS THE ONE THAT KEEPS THE SKIP HONEST. `constraint_set.json` is a plain
    json beside the records and it IS source — the corrosion sieve walks it — so it must stay
    measured and, here, be named hollow, because nothing in this fixture checks it. A rule that
    skipped "the json files" would have swallowed it and every charter with it, and the skip
    list is the cheapest way past this check forever if it is allowed to grow by kind rather
    than by name.
    """
    tmp = scratch_dir("cairn-hollowproof-")
    repo, commons = _fixture(tmp)
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    # NESTED UNDER comp/ BECAUSE THE FIXTURE'S OWN BUILDME JOURNAL IS repo/history.json —
    # untracked on purpose (see _journal), and overwriting it takes the crossing away.
    records = ["comp/history.json", "comp/state.json", "comp/validations/test_fixture.json"]
    (repo / "comp" / "validations").mkdir(parents=True, exist_ok=True)
    for rel in records:
        (repo / rel).write_text('[{"written": "by the build"}]\n')
    # NOT a record: a plain json the corrosion sieve's real counterpart is read from.
    (repo / "comp" / "constraint_set.json").write_text('{"constraints": []}\n')
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-qm", "the build writes its records",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-03T01:00:00",
              "GIT_COMMITTER_DATE": "2020-01-03T01:00:00"})

    berth = json.loads(_berth_path(tmp).read_text())
    berth["sub_problems"][0]["writes_to"].extend(records + ["comp/constraint_set.json"])
    _berth_path(tmp).write_text(json.dumps(berth))

    f = measure(FIXTURE, repo_root=repo, commons=commons,
                berths_root=_berths_root(tmp), timeout=60)
    skipped = {s["file"]: s["why"] for s in f["skipped"]}
    for rel in records:
        assert skipped.get(rel) == SKIP_RECORD, (rel, skipped)
        assert rel not in f["hollow"], (rel, f["hollow"])
        assert rel not in f["measured"], (rel, f["measured"])
    assert "comp/constraint_set.json" not in skipped, skipped
    assert "comp/constraint_set.json" in f["hollow"], f["hollow"]
    return True


def test_every_writes_to_file_being_a_record_is_still_a_red_not_a_free_green():
    """THE SKIP LIST IS NOT AN ESCAPE HATCH, and the tooth above is exactly what would turn it
    into one if this did not hold. A ticket whose whole writes_to is records measures nothing,
    and `measure` already reds a run that measured the empty set — this pins that the new class
    rides that guard rather than around it."""
    tmp = scratch_dir("cairn-hollowproof-")
    repo, commons = _fixture(tmp)
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    (repo / "comp").mkdir(parents=True, exist_ok=True)
    (repo / "comp" / "history.json").write_text('[{"written": "by the build"}]\n')
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-qm", "records only",
         env={**env, "GIT_AUTHOR_DATE": "2020-01-03T01:00:00",
              "GIT_COMMITTER_DATE": "2020-01-03T01:00:00"})
    berth = json.loads(_berth_path(tmp).read_text())
    berth["sub_problems"][0]["writes_to"] = ["comp/history.json"]
    _berth_path(tmp).write_text(json.dumps(berth))

    f = measure(FIXTURE, repo_root=repo, commons=commons,
                berths_root=_berths_root(tmp), timeout=60)
    assert f["verdict"] == "red", f
    assert any("measured nothing" in r for r in f["reasons"]), f["reasons"]
    return True


def test_a_proof_under_revert_imports_the_worktree_and_not_the_live_tree():
    """THE ASSUMPTION THE WHOLE DESIGN RESTS ON, MEASURED THE WAY A REAL PROOF RUNS.

    `cairn` is installed editable and every launcher exports PYTHONPATH at the LIVE tree, so
    a proof run in a worktree can import the code the revert was supposed to remove — then
    nothing ever reds and the detector reports a clean corpus forever. UNTIL 2026-09-09 THIS
    TOOTH MEASURED A PROBE THAT PINNED ITS OWN `sys.path` — the convention 175 of 204 proofs
    follow — and so read green while the other 29 imported the live tree (ticket fc93d8cd5961's
    proof was one: 5/5 green over a reverted worktree under the live path, 4/5 under its own).
    Now the probe pins NOTHING, the environment is the launcher's, and the run goes through
    `run_proof` — the one address the instrument (`_env_pinned_to`) lives at.
    """
    from cairn.devices.tester.device import TesterDevice
    head = _git(_REPO_ROOT, "rev-parse", "HEAD").stdout.strip()
    wt = scratch_worktree(head, repo_root=_REPO_ROOT)
    probe = wt / "cairn" / "devices" / "tester" / "proofs" / "_where_did_cairn_come_from.py"
    probe.write_text(
        "import cairn.devices.tester.scratch as m\nprint('  ok   ' + m.__file__)\n")
    prior = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = str(_REPO_ROOT)          # what every launcher hands us
    try:
        record = TesterDevice().run_proof(probe, sink="none", caller="test_hollow",
                                          isolation="none")
    finally:
        if prior is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = prior
    tail = record["evidence"].get("stdout_tail", "")
    assert record["verdict"] == "green", record["evidence"]
    assert str(wt) in tail, f"the proof imported outside the worktree at {wt}: {tail!r}"
    assert str(_REPO_ROOT) + "/cairn" not in tail, tail
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
    berth = json.loads(_berth_path(tmp).read_text())
    berth["sub_problems"][0]["writes_to"].append("added_by_build.py")
    _berth_path(tmp).write_text(json.dumps(berth))

    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=_berths_root(tmp), timeout=60)
    assert "added_by_build.py" in f["unran"], (f["unran"], f["measured"])
    assert f["unran"]["added_by_build.py"] == ["proofs/test_fixture.py"], f["unran"]
    assert any("unreadable: added_by_build.py" in r for r in f["reasons"]), f["reasons"]
    # And it is NOT filed as hollow: "the instrument stopped running" and "nothing checks
    # this file" are different findings and must not collapse into one.
    assert "added_by_build.py" not in f["hollow"], f["hollow"]
    return True



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


_SPREAD_PROOF_SRC = '''\
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import %(mod)s

def %(tooth)s():
    return %(mod)s.%(const)s == 2

if __name__ == "__main__":
    ok = False
    try:
        ok = %(tooth)s()
    except Exception:
        ok = False
    print(("ok" if ok else "FAIL") + " %(tooth)s")
    raise SystemExit(0 if ok else 1)
'''

# Declares a tooth for a DIFFERENT ticket and none for this one. It runs clean and prints a
# green tooth, so nothing about its own health explains why it must not be run here.
_SILENT_PROOF_SRC = '''\
PROVES = {"0000nother00": {"1": "test_unrelated_to_this_ticket"}}


def test_unrelated_to_this_ticket():
    return True

if __name__ == "__main__":
    print("ok test_unrelated_to_this_ticket")
    raise SystemExit(0)
'''


def _fixture_spread(tmp: Path, *, with_silent: bool = False) -> tuple[Path, Path]:
    """A ticket whose coverage is SPREAD ACROSS TWO CROSSINGS — the shape a seam actually has.

    `subject.py` is checked only by the proof named on the BUILDME crossing; `second.py` only by
    the proof named on the LATER crossing; `unchecked.py` by neither. A reader that takes the
    latest crossing alone therefore loses subject.py's tooth and calls a load-bearing file
    hollow — which is not hypothetical: it is what the shipped verb did to five of ticket
    9579a6f9cec6's eight files on 2026-09-09. With `with_silent`, a third proof rides the later
    crossing declaring teeth for a different ticket entirely.
    """
    repo, commons = tmp / "repo", tmp / "commons"
    (repo / "proofs").mkdir(parents=True)
    (commons / "tickets").mkdir(parents=True)
    # git_env(), NOT os.environ: the identity fields are what this dict is FOR, and inheriting
    # the rest is how a hook's GIT_INDEX_FILE reached the fixture repo (see _git above).
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    _git(repo, "init", "-q", "-b", "main", env=env)

    def _proof(name: str, mod: str, const: str, tooth: str) -> None:
        (repo / "proofs" / name).write_text(
            'PROVES = {"%s": {"1": "%s"}}\n\n' % (FIXTURE, tooth)
            + _SPREAD_PROOF_SRC % {"mod": mod, "const": const, "tooth": tooth})

    for value in (1, 2):
        (repo / "subject.py").write_text(f"VALUE = {value}\n")
        (repo / "second.py").write_text(f"OTHER = {value}\n")
        (repo / "unchecked.py").write_text(f"MARK = {value}\n")
        if value == 1:
            _proof("test_fixture.py", "subject", "VALUE", "test_value_is_two")
            _proof("test_second.py", "second", "OTHER", "test_other_is_two")
            if with_silent:
                (repo / "proofs" / "test_silent.py").write_text(_SILENT_PROOF_SRC)
        _git(repo, "add", "-A", env=env)
        date = "2020-01-01T00:00:00" if value == 1 else "2020-01-03T00:00:00"
        _git(repo, "commit", "-qm", f"commit {value}",
             env={**env, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})

    later = ["proofs/test_second.py"] + (["proofs/test_silent.py"] if with_silent else [])
    _berth_decompose(tmp, ["subject.py", "second.py", "unchecked.py"])
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    _journal(repo, [
        {"to": "BUILDME", "proven_by": "proofs/test_fixture.py"},
        {"to": "PROVEME", "proven_by": later},
    ])
    return repo, commons


def test_a_proof_named_on_an_earlier_crossing_still_counts_and_the_file_it_checks_is_not_hollow():
    """THE FALSE-HOLLOW GENERATOR, HELD SHUT — a verb that reads one crossing accuses a live build.

    `proven_by` here is deliberately NOT `proof_coverage._proven_by`, which answers the LATEST
    crossing only. That rule is right for the clearance gate ("which proof stands behind the
    crossing being made now?") and wrong for this verb ("what is the total declared coverage
    this ticket claims?"), and the difference is not cosmetic: read latest-only, the verb called
    five of ticket 9579a6f9cec6's eight files hollow — files a tooth on the earlier crossing's
    proof does in fact red. A hollow finding is an accusation that a build is load-bearing for
    nothing, so manufacturing them is the exact failure this module exists to prevent, aimed
    inward.

    The two halves are asserted from ONE run because either alone passes on a broken reader:
    subject.py (earlier crossing) reds its tooth, second.py (later crossing) reds its tooth, and
    unchecked.py still comes back hollow — so the union widened coverage without softening the
    finding into "nothing is ever hollow".
    """
    tmp = scratch_dir("cairn-hollowspread-")
    repo, commons = _fixture_spread(tmp)
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=_berths_root(tmp), timeout=60)
    assert f["proofs"] == ["proofs/test_fixture.py", "proofs/test_second.py"], f["proofs"]
    assert f["measured"]["subject.py"] == ["test_value_is_two"], f["measured"]
    assert f["measured"]["second.py"] == ["test_other_is_two"], f["measured"]
    assert f["hollow"] == ["unchecked.py"], f["hollow"]
    return True


def test_a_proof_declaring_no_tooth_for_this_ticket_is_dropped_and_never_run():
    """RUNNING A PROOF THAT CANNOT SPEAK IS PURE COST — and the cost broke the ticket's bound.

    Only declared teeth are counted, so a proof holding none for this ticket cannot contribute a
    red however its reversion goes. MEASURED 2026-09-09 on 9579a6f9cec6: five named proofs, three
    declaring zero teeth for it, over eight files — 45 proof runs and 501.7s against the ticket's
    stated five-minute WRONG INTENT threshold. Dropping the mute three leaves the reading byte-for-
    byte identical at 40% of the runs.

    So the tooth measures the RUNS, not the wall clock: a timing assertion would pass or fail on
    the machine's mood, while "test_silent.py was never handed to the tester" is the same answer
    on every box. And the drop is NAMED in the finding — "we did not run it" and "it had nothing
    to say" are different facts, and Law 7 says a record of truth may not collapse them.
    """
    class Counting:
        def __init__(self):
            from cairn.devices.tester.device import TesterDevice
            self.inner = TesterDevice()
            self.ran: list[str] = []

        def run_proof(self, path, **kw):
            self.ran.append(Path(path).name)
            return self.inner.run_proof(path, **kw)

    tmp = scratch_dir("cairn-hollowsilent-")
    repo, commons = _fixture_spread(tmp, with_silent=True)
    counter = Counting()
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=_berths_root(tmp), timeout=60, tester=counter)

    assert f["silent_proofs"] == ["proofs/test_silent.py"], f["silent_proofs"]
    assert "proofs/test_silent.py" not in f["proofs"], f["proofs"]
    assert "test_silent.py" not in counter.ran, counter.ran
    # One baseline plus one pass per measured file, two proofs each — and the mute proof would
    # have added a third column to every one of those passes.
    assert len(counter.ran) == 2 * (1 + len(f["measured"])), (len(counter.ran), f["measured"])
    # THE SAVING CHANGED THE COST AND NOT THE ANSWER, and that is measured rather than argued:
    # the same fixture without the mute proof is read again and the two findings are compared.
    # A filter that also moved the verdict would be an optimisation that edits the truth.
    plain_tmp = scratch_dir("cairn-hollowsilent-")
    plain_repo, plain_commons = _fixture_spread(plain_tmp)
    plain = measure(FIXTURE, repo_root=plain_repo, commons=plain_commons,
                    berths_root=_berths_root(plain_tmp), timeout=60)
    assert (f["measured"], f["hollow"], f["verdict"]) == \
        (plain["measured"], plain["hollow"], plain["verdict"]), (f, plain)
    assert f["hollow"] == ["unchecked.py"], f["hollow"]
    return True


# ---------------------------------------------------------------------------------------
# TICKET 95e3b9911dd0 — hollow derives the chart chain from the berths, never from a stored
# copy. The defect these check: a gate reading its own evidence off the ticket it is judging.
# On 2026-09-10 the field had ONE reader (line 188 here), ZERO writers anywhere in the tree,
# and TWENTY-FOUR carriers, so every one of them was typed by a hand — while the BUILDME
# entry gate had been deriving the same chain from the berth store for months.
# ---------------------------------------------------------------------------------------

_HOLLOW_SRC = _REPO_ROOT / "cairn" / "devices" / "tester" / "hollow.py"

# The pre-change reader, verbatim as it stood before this ticket. Tooth 6 puts it BACK, in a
# scratch copy, and requires these teeth to red against it — a tooth that passes both ways is
# measuring nothing.
_OLD_READER = 'berth = (ticket.get("chart_chain") or {}).get("decompose")'
_NEW_READER = ('berth = chain_for_ticket(tid, berths_root=berths_root)["decompose"] '
               'if tid else None')


def _reads_the_stored_field(source: str) -> list:
    """Every line of a source that dereferences the ticket-side chart_chain key.

    Comments do not count and MUST not: this module's own docstrings name the field a dozen
    times, and a check that could not tell prose from a dereference would red the record of
    why the field went away."""
    hits = []
    for lineno, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if 'ticket.get("chart_chain")' in line or "ticket['chart_chain']" in line \
                or 'ticket["chart_chain"]' in line:
            hits.append((lineno, stripped))
    return hits


def _sandbox_chain(tmp: Path, ticket: str, stage: str = "decompose", **packet_extra) -> tuple:
    """A berths root holding one berthed packet claiming ``ticket`` at ``stage``.

    Returns (berths_root, packet_path). Real files in a real directory, because
    ``claiming_packet_paths`` globs and reads them — a mock would prove the mock."""
    # THE LAYOUT IS THE INDEX'S, not a convenience: chain._packet_index globs
    # ``<root>/*/packets/*.json``, where the middle segment is the INSTANCE. A sandbox that
    # flattened it would index nothing and every derivation here would read None — green for
    # the wrong reason, which is this proof module's own recorded failure shape.
    root = tmp / "berths"
    packets = root / "0" / "packets"
    packets.mkdir(parents=True, exist_ok=True)
    path = packets / f"{stage}-20260910T000000-aaaaaaaaaaaa.json"
    packet = {"ticket": ticket, "stage": stage}
    packet.update(packet_extra)
    path.write_text(json.dumps(packet), encoding="utf-8")
    return str(root), str(path)


def test_the_reader_names_no_stored_chart_chain_and_calls_the_derivation_instead():
    """CRITERION 1 — the reader dereferences no stored value, and the berth comes from the
    derivation the entry gate already used."""
    source = _HOLLOW_SRC.read_text(encoding="utf-8")
    hits = _reads_the_stored_field(source)
    assert hits == [], f"hollow still dereferences the ticket-side chart_chain: {hits}"
    assert "from cairn.tools.chain.chain import chain_for_ticket" in source, \
        "the derivation is not imported — the reader cannot be deriving anything"
    assert _NEW_READER in source, "the derived reader is not at its call site"
    return True


def test_the_derived_decompose_berth_equals_a_stored_one_the_fixture_authored():
    """CRITERION 2 — an INVARIANT, not the day's corpus count.

    The one-shot reading over the 24 live carriers cannot be re-run after the migration deletes
    the stored side, so it is recorded once at
    ``cairn/tools/chain/proofs/evidence-2026-09-10-derived-equals-stored.json`` (decompose:
    22 same, 0 different, 0 lost). What is checked HERE, forever, is the property that reading
    made plausible: where a berth claims the ticket at decompose, the derivation returns that
    berth's path — so a stored copy of it was never carrying anything the derivation lacks."""
    tmp = scratch_dir("cairn-chainderive-")
    root, packet_path = _sandbox_chain(tmp, FIXTURE, writes_to=["a.py"])
    from cairn.tools.chain.chain import chain_for_ticket
    derived = chain_for_ticket(FIXTURE, berths_root=root)["decompose"]
    assert derived == packet_path, (derived, packet_path)
    # And the LATEST wins, which is the whole reason a stored copy goes stale: a second berth
    # lands and the ticket's typed string still names the first.
    later = Path(root) / "0" / "packets" / "decompose-20260911T000000-bbbbbbbbbbbb.json"
    later.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose"}), encoding="utf-8")
    assert chain_for_ticket(FIXTURE, berths_root=root)["decompose"] == str(later)
    return True


def test_a_ticket_no_decompose_berth_claims_raises_the_named_lack_not_an_empty_list():
    """CRITERION 3 — Law 3 held as a type. 'Nothing declares what this build writes' may not
    travel back through the same return as 'this build writes nothing'."""
    from cairn.devices.tester.hollow import writes_to
    try:
        writes_to({"id": "n0such7icke7"})
    except HollowUnmeasurable as why:
        assert "n0such7icke7" in str(why), why
        assert "decompose" in str(why), why
        return True
    raise AssertionError("a ticket no berth claims returned a file list instead of refusing")


def test_a_bare_string_chart_chain_is_no_longer_dereferenced_by_the_reader():
    """CRITERION 4 — the shape error is gone BECAUSE nothing is dereferenced.

    Two of the 24 carriers (2744aab73ff3, 81f719868158) stored PROSE where the reader called
    ``.get`` on it, so those two reached the instrument as an ``AttributeError`` — an unnamed
    crash where a named lack belonged. The fix is not a type check. The reader stopped looking
    at the field, so its shape cannot reach the reader at all."""
    from cairn.devices.tester.hollow import writes_to
    ticket = {"id": "n0such7icke7",
              "chart_chain": "the chain ran on 2026-08-10, see cairn.machines.chart.live"}
    try:
        writes_to(ticket)
    except AttributeError as boom:  # the pre-change failure, and it must not be reachable
        raise AssertionError(f"the reader dereferenced the stored string: {boom}")
    except HollowUnmeasurable as why:
        assert "decompose" in str(why), why
        return True
    raise AssertionError("a bare-string carrier returned a file list — the field is being read")


def test_the_derived_reader_teeth_red_against_the_stored_field_reader():
    """CRITERION 6 — THE ANTI-HOLLOW TOOTH. Put the old reader back in a scratch copy and
    require the teeth above to fail against it. A tooth green both ways checks nothing, which
    is the exact failure the instrument these teeth belong to exists to catch."""
    source = _HOLLOW_SRC.read_text(encoding="utf-8")
    assert _NEW_READER in source, "cannot revert what is not there"
    reverted = source.replace(_NEW_READER, _OLD_READER, 1)
    assert reverted != source

    # Tooth 1 must red on the reverted source.
    assert _reads_the_stored_field(reverted), \
        "the reverted source did not trip tooth 1 — tooth 1 is not measuring the reversion"

    # Tooth 4 must red on the reverted READER, not merely on the reverted text. So the scratch
    # copy is really imported and really called.
    # AT THE SAME DEPTH AS THE ORIGINAL: the module computes its REPO_ROOT from ``__file__``
    # at import time, so a scratch copy dropped at the top of a temp dir dies on an IndexError
    # before the reader is ever reached — and a tooth that fails for THAT reason is measuring
    # the fixture, not the reversion.
    tmp = scratch_dir("cairn-hollowrevert-")
    mod_dir = tmp / "cairn" / "devices" / "tester"
    mod_dir.mkdir(parents=True, exist_ok=True)
    mod_path = mod_dir / "hollow_reverted.py"
    mod_path.write_text(reverted, encoding="utf-8")
    import importlib.util
    spec = importlib.util.spec_from_file_location("hollow_reverted", mod_path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    try:
        old.writes_to({"id": "n0such7icke7",
                       "chart_chain": "the chain ran on 2026-08-10, see cairn.machines.chart.live"})
    except AttributeError:
        return True  # the pre-change reader crashes exactly where the ticket said it did
    except Exception as other:
        raise AssertionError(
            f"the pre-change reader did not raise AttributeError on a bare string; it raised "
            f"{type(other).__name__}: {other}. Tooth 4 is then not measuring what it claims.")
    raise AssertionError("the pre-change reader accepted a bare string — tooth 4 is hollow")


def test_no_ticket_in_the_live_commons_carries_a_stored_chart_chain():
    """CRITERION 7 — an INVARIANT over the live corpus: zero, forever, not 'zero today'.

    This is the one tooth that reads the real store, and it must: the defect was hands typing
    a field, and a fixture cannot have hands. It asserts a count of zero rather than a
    difference from 24, so it stays true as the corpus grows and reds the day one comes back."""
    from cairn.tools.chain.chain import carriers
    found = carriers()
    assert found == [], f"{len(found)} ticket(s) carry a stored chart_chain again: {found[:5]}"
    return True


def test_the_migration_removes_one_key_and_carries_what_it_cannot_re_derive_to_notes():
    """CRITERION 8 — the migration deletes the key and NOTHING ELSE, and what the derivation
    cannot reproduce is carried rather than dropped.

    The dry run over the live corpus surfaced why this tooth is not paranoia: one ticket stored
    three keys that are not chain stages at all, one of them ~500 characters of friction
    reporting for Akien that appears nowhere else in either root. A migration written against a
    key allowlist would have deleted it silently."""
    from cairn.tools.chain.chain import drop_stored_chart_chain
    tmp = scratch_dir("cairn-chartmigrate-")
    root, packet_path = _sandbox_chain(tmp, FIXTURE)
    tickets = tmp / "tickets"
    tickets.mkdir()
    keeper = {"id": FIXTURE, "title": "a fixture", "cursor": "x", "notes": ["an existing note"],
              "chart_chain": {"decompose": packet_path,
                              "note": "SOMETHING NO DERIVATION CAN REPRODUCE"}}
    path = tickets / f"{FIXTURE}-a-fixture.json"
    path.write_text(json.dumps(keeper, indent=2) + "\n", encoding="utf-8")
    untouched = {"id": "0ther7icke700", "title": "no chain here"}
    other = tickets / "0ther7icke700-no-chain-here.json"
    other.write_text(json.dumps(untouched, indent=2) + "\n", encoding="utf-8")
    before_other = other.read_bytes()

    report = drop_stored_chart_chain(str(tickets), apply=True)
    assert report["applied"] is True, report
    after = json.loads(path.read_text(encoding="utf-8"))
    assert "chart_chain" not in after, after
    # EVERY OTHER FIELD BYTE-FOR-BYTE — the door is an edit, never a reformat.
    for key, value in keeper.items():
        if key in ("chart_chain", "notes"):
            continue
        assert after[key] == value, (key, after.get(key), value)
    carried = " ".join(str(n) for n in after["notes"])
    assert "an existing note" in carried, "the standing notes were replaced instead of appended"
    assert "SOMETHING NO DERIVATION CAN REPRODUCE" in carried, \
        f"the non-derivable value was dropped rather than carried: {after['notes']}"
    # A ticket that never carried the key is not opened, written, or touched.
    assert other.read_bytes() == before_other, "the migration rewrote a ticket it had no business in"
    return True


def test_the_migrations_dry_run_names_exactly_the_files_the_apply_run_writes():
    """CRITERION 9 — the dry run is a PREVIEW, which means it is worthless if it can disagree
    with the run it previews. Same corpus, twice, compared key by key."""
    from cairn.tools.chain.chain import drop_stored_chart_chain

    def _spread(tag):
        tmp = scratch_dir(tag)
        root, packet_path = _sandbox_chain(tmp, FIXTURE)
        _spread.roots.append(root)
        tickets = tmp / "tickets"
        tickets.mkdir()
        (tickets / "a.json").write_text(json.dumps(
            {"id": FIXTURE, "chart_chain": {"decompose": packet_path}}, indent=2) + "\n",
            encoding="utf-8")
        (tickets / "b.json").write_text(json.dumps(
            {"id": "b0b0b0b0b0b0", "chart_chain": "prose, not a mapping"}, indent=2) + "\n",
            encoding="utf-8")
        (tickets / "c.json").write_text(json.dumps({"id": "c0c0c0c0c0c0"}, indent=2) + "\n",
                                        encoding="utf-8")
        return tickets

    _spread.roots = []
    dry_tickets, wet_tickets = _spread("cairn-chartdry-"), _spread("cairn-chartwet-")
    dry_root, wet_root = _spread.roots
    dry = drop_stored_chart_chain(str(dry_tickets), berths_root=dry_root)
    wet = drop_stored_chart_chain(str(wet_tickets), apply=True, berths_root=wet_root)
    assert dry["applied"] is False and wet["applied"] is True, (dry["applied"], wet["applied"])
    # THE ABSOLUTE PATHS DIFFER BY CONSTRUCTION — two scratch spreads, two temp roots — so the
    # comparison is over SHAPE, not bytes. A comparison that demanded byte equality here would
    # be red every run for a reason that has nothing to do with the property under test.
    for key in ("removed", "prose_moved", "empty", "notes_carried", "unreadable"):
        assert dry[key] == wet[key], f"dry run and apply disagree on {key}: {dry[key]} vs {wet[key]}"
    assert [d["ticket"] for d in dry["disagreed"]] == [d["ticket"] for d in wet["disagreed"]], \
        (dry["disagreed"], wet["disagreed"])
    # And the sandbox berth really is being derived against, so 'disagreed' is empty for the
    # ticket whose stored value the sandbox berth reproduces.
    assert dry["disagreed"] == [], f"the derivation did not see the sandbox berth: {dry['disagreed']}"
    return True


def test_the_watch_probe_reports_a_carrier_that_reappears_and_does_not_clear_on_zero_alone():
    """CRITERION 10 — the probe fires on ONE reappearance, and its clear is not a historical
    fact.

    The sibling ``a_pickup_is_witnessed`` cleared on ``pickups >= 1``, took its 1 in August 2026
    and read green off it for a month. So this checks the property that failure lacked: every
    clause can go back DOWN, and zero carriers alone is not enough to clear."""
    from cairn.tools.base.probes import no_ticket_carries_a_stored_chart_chain as probe

    clean = {"corpus": {"carrier_count": 0, "carriers": [], "reader_reads_the_stored_key": [],
                        "voyages_since_migration": 9, "voyage_tickets": ["x"]}}
    assert probe._trigger(None, clean) is False, "the probe fires on a clean corpus"
    assert probe._enough(clean) is True, "a clean corpus with traffic does not clear the watch"

    # ONE reappearance is the whole failure — no floor, no warm-up.
    one_back = {"corpus": dict(clean["corpus"], carrier_count=1,
                               carriers=[{"ticket": FIXTURE, "file": "f.json", "kind": "dict",
                                          "entries": 1}])}
    assert probe._trigger(None, one_back) is True, "one hand-written key did not fire the probe"
    assert probe._enough(one_back) is False, "the watch cleared with a carrier standing"
    assert FIXTURE in json.dumps(probe._carry(one_back)), "the carry does not name the carrier"

    # A FALLBACK inside the reader is the same hand at one remove, and cannot be seen by
    # counting keys — so it is its own clause.
    fallback = {"corpus": dict(clean["corpus"],
                               reader_reads_the_stored_key=[{"line": 188, "text": "..."}])}
    assert probe._trigger(None, fallback) is True, "a reader fallback did not fire the probe"
    assert probe._enough(fallback) is False, "the watch cleared with a reader fallback standing"

    # THE ANTI-HOLLOW CLAUSE: zero carriers with no traffic is what the migration LEFT BEHIND.
    idle = {"corpus": dict(clean["corpus"], voyages_since_migration=0, voyage_tickets=[])}
    assert probe._enough(idle) is False, \
        "the watch cleared on zero carriers alone — that is a_pickup_is_witnessed all over again"

    # And it reaches no oracle (CRITERION 11): the base tool's charter forbids one at this
    # address, and the check is over the module's own imports rather than a promise about them.
    source = Path(probe.__file__).read_text(encoding="utf-8")
    for reach in ("inference", "psycopg", "requests", "httpx", "socket", "anthropic", "urllib"):
        for lineno, line in enumerate(source.splitlines(), 1):
            if line.startswith(("import ", "from ")) and reach in line:
                raise AssertionError(f"the probe reaches an oracle at line {lineno}: {line!r}")
    return True


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))


def test_the_migration_names_a_notes_reshape_and_refuses_a_shape_it_cannot_carry():
    """CRITERION 8, THE HALF THE EYEBALL DIFF MISSED — a migration may not reshape a field it
    was not asked to touch without saying so, and may not reshape one it cannot carry at all.

    HOW THIS WAS FOUND, because the method is the point. Criterion 8 was first answered by
    reading `git show --numstat` per file: 20 files at 0-added, 4 with small additions, no
    reformats, verdict pass. Then the same commit was diffed KEY BY KEY through the parser
    instead of by line, and one file disagreed with the eye: 782554235fca's `notes` had been a
    bare STRING and came out a four-element LIST. Nothing was lost (the original string is
    element 0, verbatim, and this tooth pins that), but the migration had changed the TYPE of a
    field outside its remit and its report said nothing at all. Twenty files at 0-added is
    exactly the reading that makes a careful reader stop looking.

    The str case is legitimate and stays: a string has nowhere to append, so promoting it to a
    one-element list is the only way to carry a value without destroying the prose. It now
    lands in `notes_reshaped` so the run declares it.

    The dict case is NOT legitimate and is now refused. Measured across the 272-ticket corpus:
    `notes` is a list 51 times and a dict 3 times. Wrapping a mapping in a list to make room
    invents an ordering the ticket never had and buries its keys behind an index — so the
    ticket is skipped whole, with its `chart_chain` left in place and the refusal reported.
    Leaving the key is the safe failure here precisely because the key is a SECOND COPY of an
    address `chain_for_ticket` derives: nothing is lost by not deleting it, and something real
    would be lost by mangling the notes to delete it."""
    from cairn.tools.chain.chain import drop_stored_chart_chain
    tmp = scratch_dir("cairn-notesshape-")
    root, packet_path = _sandbox_chain(tmp, FIXTURE)
    tickets = tmp / "tickets"
    tickets.mkdir()

    prose = "Akien-facing friction reporting that appears nowhere else in either root."
    stringy = tickets / f"{FIXTURE}-string-notes.json"
    stringy.write_text(json.dumps(
        {"id": FIXTURE, "notes": prose,
         "chart_chain": {"decompose": packet_path, "note": "NOT REPRODUCIBLE"}},
        indent=2) + "\n", encoding="utf-8")

    dicty = tickets / "d1c7d1c7d1c7-dict-notes.json"
    dict_notes = {"2026-08-01": "the first note", "2026-08-02": "the second"}
    dicty.write_text(json.dumps(
        {"id": "d1c7d1c7d1c7", "notes": dict_notes,
         "chart_chain": {"decompose": packet_path, "note": "ALSO NOT REPRODUCIBLE"}},
        indent=2) + "\n", encoding="utf-8")
    dict_bytes_before = dicty.read_bytes()

    report = drop_stored_chart_chain(str(tickets), apply=True)

    # THE STRING CASE: reshaped, carried verbatim, and DECLARED.
    after = json.loads(stringy.read_text(encoding="utf-8"))
    assert isinstance(after["notes"], list), after["notes"]
    assert after["notes"][0] == prose, \
        f"the original prose was not preserved verbatim as element 0: {after['notes'][0]!r}"
    assert "chart_chain" not in after, after
    reshapes = {r["ticket"]: r for r in report["notes_reshaped"]}
    assert FIXTURE in reshapes, \
        f"the run reshaped a notes field and did not say so — the whole defect: {report['notes_reshaped']}"
    assert reshapes[FIXTURE]["from"] == "str" and reshapes[FIXTURE]["to"] == "list", reshapes[FIXTURE]
    assert reshapes[FIXTURE]["chars"] == len(prose), reshapes[FIXTURE]

    # THE DICT CASE: refused whole, byte-identical on disk, and reported.
    assert dicty.read_bytes() == dict_bytes_before, \
        "a ticket whose notes could not carry the value was written anyway"
    after_dict = json.loads(dicty.read_text(encoding="utf-8"))
    assert after_dict["notes"] == dict_notes, "the mapping was mangled"
    assert "chart_chain" in after_dict, \
        "the key was deleted from a ticket whose carried value had nowhere to land"
    refused = {r["ticket"]: r for r in report["refused"]}
    assert "d1c7d1c7d1c7" in refused, \
        f"the run skipped a ticket silently instead of reporting the refusal: {report['refused']}"
    assert refused["d1c7d1c7d1c7"]["notes_shape"] == "dict", refused["d1c7d1c7d1c7"]
    return True


def test_an_unmeasurable_baseline_says_whether_the_proof_failed_or_never_ran():
    """THE 24TH TOOTH — a refusal that sends the reader to the right place.

    HOW THIS WAS FOUND, because the finding is about a message and not about a number.
    Ticket 95e3b9911dd0's own live fire — the voyage measuring itself, which is what the
    criterion asked for — came back:

        hollow: these declared teeth are not green at HEAD, so no reversion reading can be
        attributed to a file: {"cairn/devices/tester/proofs/test_hollow.py": [ ...nine... ]}

    Nine teeth named, all nine healthy. The suite was green twice on that exact tree at
    264.72s and 234.01s, and ``cairn test --hollow`` passes ``--timeout`` (default 120s)
    straight through to ``run_proof``. So the proof was KILLED at 120s, printed no tooth at
    all, and every declared tooth read "not green" — a true sentence that points at nine
    files to repair when the entire fix is one flag.

    THE INFORMATION WAS NEVER MISSING. ``device.run_proof``'s ``TimeoutExpired`` arm already
    records ``returncode: None`` and ``timed out after Ns``, and deliberately writes
    ``teeth_green``/``teeth_red`` as EMPTY rather than absent so that "we did not look" and
    "we looked and found none" stay distinguishable downstream. ``run_all`` then read the two
    tooth lists and dropped the rest of the record on the floor, which is where the
    distinction died — one line after it was carefully preserved.

    Law 7: a diagnostic surface may collapse an error into a coherent shape only when it is
    not a record of truth, and this refusal is the record hollow leaves behind. "Not green"
    was coherent and wrong about what to do next, which is the specific failure the Law names.

    THE TOOTH ASSERTS THE DISTINCTION, NOT THE WORDING — both arms run the same measurement
    against the same fixture and differ only in what the tester reports, so a message that
    stops separating them reds here.
    """
    tmp = scratch_dir("cairn-hollowcause-")
    repo, commons = _fixture(tmp)

    class TimedOut:
        """What device.py writes when a proof is killed: no returncode, empty tooth lists."""
        def run_proof(self, path, **kw):
            return {"evidence": {"returncode": None, "stdout_tail": "",
                                 "stderr_tail": "timed out after 120s",
                                 "teeth_green": [], "teeth_red": []}}

    class ToothFailed:
        """What device.py writes when the proof RAN and a declared tooth asserted false."""
        def run_proof(self, path, **kw):
            return {"evidence": {"returncode": 1, "stdout_tail": "", "stderr_tail": "",
                                 "teeth_green": ["test_something_else"],
                                 "teeth_red": ["test_value_is_two"]}}

    def refusal(tester) -> str:
        try:
            measure(FIXTURE, repo_root=repo, commons=commons,
                    berths_root=_berths_root(tmp), timeout=120, tester=tester)
        except HollowUnmeasurable as exc:
            return str(exc)
        raise AssertionError("hollow was supposed to refuse an unmeasurable baseline and did not")

    killed = refusal(TimedOut())
    failed = refusal(ToothFailed())

    # THE KILLED RUN SAYS SO, AND SAYS WHAT TO DO. The old message said neither.
    assert "never finished" in killed, killed
    assert "timed out after 120s" in killed, killed
    assert "--timeout" in killed, killed
    assert '"teeth_that_ran_at_all": 0' in killed, killed

    # THE FAILED TOOTH IS NOT DESCRIBED AS A TIMEOUT — the arm that would make the repair
    # above a lie by firing on both.
    assert "never finished" not in failed, failed
    assert "--timeout" not in failed, failed
    assert "assertion failed" in failed, failed
    # It ran: two teeth printed, one of them the declared one that went red.
    assert '"teeth_that_ran_at_all": 2' in failed, failed

    # AND BOTH STILL NAME THE DECLARED TOOTH THAT IS MISSING — the repair adds a cause, it
    # does not trade the original finding away for it.
    assert "test_value_is_two" in killed and "test_value_is_two" in failed

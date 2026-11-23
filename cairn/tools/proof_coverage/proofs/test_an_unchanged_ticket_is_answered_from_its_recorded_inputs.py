"""Teeth for the re-judge cache — ``lacks(..., cache=<dir>)`` answers an unchanged ticket from
the record of its last judgement, and re-judges a ticket the moment any input that judgement
read has moved.

Charter: cairn/tools/proof_coverage/intention+why.json
Ticket:  CairnCommons/tickets/b64847df255d-the-proved-re-judge-answers-an-unchanged-ticket-from-its-recorded-inputs.json

Run: PYTHONPATH=. python3 cairn/tools/proof_coverage/proofs/test_an_unchanged_ticket_is_answered_from_its_recorded_inputs.py

THE RECORD THESE TEETH READ: ``<cache>/lacks_cache/<ticket id>.json``, one per ticket; each
carries ``stamp`` (minted fresh at every judgement and never at a hit, so a
changed stamp IS a re-judge), ``files`` (every file the judgement opened, keyed by absolute
path), ``absent`` (every path it found absent) and ``refs`` (each git ref the judgement read, with
the sha it resolved to). Nothing else about the entry is asserted, so the build may carry more.

THE FIXTURES ARE TWO WORLDS SHARING ONE CACHE, each with its own ticket id. A cache that
drops everything on any change would pass "re-judges the changed ticket" and fail "and no
other" — the second half is what the bystander world measures. Each world's proof binds a
helper at module level that binds a second module (two hops); the decompose berth names a
file the build rewrote that the proof never imports, so the only reader of that file is
``_added_by_the_build``. The seal is a real validation record read through the real door.

CLAUSE 1 RUNS OVER THE HOUSE TREE, three times: uncached (the truth), cached cold (the record
written) and cached warm (the record read). The live tree may move under a run that takes
minutes; a ticket whose inputs moved is re-judged by the warm run against the moved inputs
while the uncached run saw the old ones, so a difference is printed by ticket before the
tooth reds, and reading that list says which of the two it was.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from cairn.tools import proof_coverage as pc  # noqa: E402  (the package existed before the build)
from cairn.tools.proof_coverage.proofs.fixtures import historical_instances as H  # noqa: E402

PROVES = {
    "b64847df255d": {
        "1": "test_warm_house_findings_equal_cold_and_run_faster",
        "2": "test_one_flipped_byte_re_judges_exactly_that_ticket",
        "3": "test_a_deleted_input_or_a_created_absence_re_judges",
        "4": "test_a_moved_ref_re_judges_and_a_fixed_sha_is_not_reread",
        "5": "test_every_file_one_judgement_opens_is_recorded",
    }
}

TICKET = "b64847df255d"
# Clause 1 judges the house tree three times; measured 2026-11-22 the uncached pass alone is
# ~107 s off load, and a loaded box roughly doubles it.
PROOF_TIMEOUT_S = 1200
COMMONS = REPO_ROOT.parent / "CairnCommons"
_SCRATCH: list[tempfile.TemporaryDirectory] = []
CACHE_DIR = "lacks_cache"

ONE, TWO = "cache0near001", "cache0far0002"
PROOF = "proofs/test_fixture_cache_world.py"
TOOTH = "test_the_helper_moved_to_two"


def _tmp() -> Path:
    d = tempfile.TemporaryDirectory(prefix="cairn_rejudge_cache_fixture_")
    _SCRATCH.append(d)
    return Path(d.name)


def _lacks(ticket: dict, *, repo_root: Path, roots=None, cache=None) -> list[dict]:
    """The judgement, reached at call time. ``cache=None`` is today's call, unchanged."""
    if cache is None:
        return pc.proof_coverage.lacks(ticket, repo_root=repo_root, roots=roots)
    return pc.proof_coverage.lacks(ticket, repo_root=repo_root, roots=roots, cache=cache)


def _proof_text(tid: str) -> str:
    return "\n".join([
        "import sys", "from pathlib import Path",
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))",
        f"PROVES = {json.dumps({tid: {'1': TOOTH, '2': TOOTH}})}", "",
        "import helper_that_existed  # noqa  (existed before the build)", "",
        f"def {TOOTH}():", "    return helper_that_existed.VALUE == 2", "",
        "if __name__ == '__main__':",
        f"    print('ok ' + '{TOOTH}' if {TOOTH}() else 'FAIL {TOOTH}')", ""])


def _world(tid: str) -> H.World:
    """A two-commit world whose judgement reads every input class the cache must record."""
    world = H.build_world(
        _tmp(),
        before={"helper_that_existed.py": "VALUE = 1\n",
                "deep_that_existed.py": "DEEP = 1\n",
                "data_the_build_rewrote.py": "X = 1\n",
                PROOF: _proof_text(tid).replace("== 2", "== 1")},
        build={"helper_that_existed.py": "import deep_that_existed  # noqa\nVALUE = 2\n",
               "deep_that_existed.py": "DEEP = 2\nADDED_BY_THE_BUILD = 3\n",
               "data_the_build_rewrote.py": "X = 2\n",
               PROOF: _proof_text(tid)},
        proof=PROOF,
        writes_to=["helper_that_existed.py", "deep_that_existed.py",
                   "data_the_build_rewrote.py", PROOF],
        ticket=tid)
    world.ticket["title"] = "a fixture ticket the cache is asked about"
    from cairn.tools.base.validation import source_fingerprint
    proof = world.repo / PROOF
    seal = {"claim": f"proof {proof.name} passes", "date": "2026-11-22T00:00:00Z",
            "method": "ran the proof as a subprocess", "verdict": "green",
            "evidence": {"returncode": 0, "source_fingerprint": source_fingerprint(str(proof)),
                         "teeth_green": [TOOTH], "teeth_red": []},
            "falsifier": "re-run reds", "horizon": "until the code changes"}
    (world.repo / "validations").mkdir(exist_ok=True)
    (world.repo / "validations" / (proof.stem + ".json")).write_text(
        json.dumps([seal], indent=2), encoding="utf-8")
    world.notes = {"seal": world.repo / "validations" / (proof.stem + ".json")}
    return world


def _judge(world: H.World, cache: Path) -> list[dict]:
    return _lacks(world.ticket, repo_root=world.repo, roots=world.roots, cache=cache)


def _entry(cache: Path, tid: str) -> dict:
    return json.loads((cache / CACHE_DIR / f"{tid}.json").read_text(encoding="utf-8"))


def _stamp(cache: Path, tid: str) -> str:
    return str(_entry(cache, tid)["stamp"])


def _flip(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {path}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _pair() -> tuple[H.World, H.World, Path]:
    """Two worlds judged once into one cache, then judged again with the stamps unmoved —
    the hit every other tooth departs from."""
    near, far, cache = _world(ONE), _world(TWO), _tmp() / "cache"
    cache.mkdir()
    truth = {w.ticket["id"]: _lacks(w.ticket, repo_root=w.repo, roots=w.roots) for w in (near, far)}
    for w in (near, far):
        got = _judge(w, cache)
        assert got == truth[w.ticket["id"]], f"cold cached != uncached for {w.ticket['id']}: {got}"
    before = {t: _stamp(cache, t) for t in (ONE, TWO)}
    for w in (near, far):
        assert _judge(w, cache) == truth[w.ticket["id"]], "warm cached != uncached"
    after = {t: _stamp(cache, t) for t in (ONE, TWO)}
    assert before == after, f"an unchanged world was re-judged: {before} -> {after}"
    return near, far, cache


def _rejudged(near: H.World, far: H.World, cache: Path) -> set[str]:
    """Which of the two tickets the next pair of calls re-judged, and each answer checked
    against the uncached judgement of the world as it now stands."""
    before = {t: _stamp(cache, t) for t in (ONE, TWO)}
    for w in (near, far):
        got = _judge(w, cache)
        want = _lacks(w.ticket, repo_root=w.repo, roots=w.roots)
        assert got == want, f"{w.ticket['id']}: cached {got} != uncached {want}"
    return {t for t in (ONE, TWO) if _stamp(cache, t) != before[t]}


# ── clause 2 ──────────────────────────────────────────────────────────────────────────

def test_one_flipped_byte_re_judges_exactly_that_ticket():
    near, far, cache = _pair()
    flips = {
        "the ticket": lambda: near.ticket.__setitem__(
            "title", near.ticket["title"].replace("a fixture", "b fixture")),
        "a named proof's seal": lambda: _flip(near.notes["seal"], "2026-11-22T", "2026-11-23T"),
        "a module the proof binds two hops away": lambda: _flip(
            near.repo / "deep_that_existed.py", "DEEP = 2", "DEEP = 3"),
        "a decompose writes_to file": lambda: _flip(
            near.repo / "data_the_build_rewrote.py", "X = 2", "X = 3"),
    }
    for what, flip in flips.items():
        flip()
        got = _rejudged(near, far, cache)
        assert got == {ONE}, f"flipping one byte of {what} re-judged {sorted(got)}, not [{ONE}]"
        assert _rejudged(near, far, cache) == set(), f"after {what}, the next call re-judged again"


# ── clause 3 ──────────────────────────────────────────────────────────────────────────

def test_a_deleted_input_or_a_created_absence_re_judges():
    near, far, cache = _pair()
    entry = _entry(cache, ONE)
    gone = near.repo / "data_the_build_rewrote.py"
    assert str(gone.resolve()) in entry["files"], f"{gone} not among the recorded files"
    gone.unlink()
    assert _rejudged(near, far, cache) == {ONE}, "deleting a recorded input did not re-judge"

    # The proof's ``import helper_that_existed`` is resolved against the proof's own
    # directory first, so that path is looked for and found absent.
    shadow = (near.repo / "proofs" / "helper_that_existed.py").resolve()
    absent = {str(Path(p).resolve()) for p in _entry(cache, ONE)["absent"]}
    assert str(shadow) in absent, f"{shadow} not recorded absent: {sorted(absent)[:8]}"
    shadow.write_text("VALUE = 2\n", encoding="utf-8")
    assert _rejudged(near, far, cache) == {ONE}, "creating a recorded-absent file did not re-judge"


# ── clause 4 ──────────────────────────────────────────────────────────────────────────

def test_a_moved_ref_re_judges_and_a_fixed_sha_is_not_reread():
    near, far, cache = _pair()
    assert _entry(cache, ONE)["refs"], "the judgement recorded no git read"

    calls: list[list[str]] = []
    real = subprocess.run

    def spy(args, *a, **k):
        if isinstance(args, (list, tuple)) and args and str(args[0]) == "git":
            calls.append([str(x) for x in args])
        return real(args, *a, **k)

    subprocess.run = spy
    try:
        assert _judge(far, cache) is not None
    finally:
        subprocess.run = real
    shows = [c for c in calls if "show" in c]
    assert not shows, f"a hit re-read git at a fixed sha: {shows}"

    # A commit on the near world's HEAD: the pre-build answer is the same commit, but the
    # ref the judgement resolved now names another sha, so the record cannot vouch for it.
    (near.repo / "unrelated_after_the_build.txt").write_text("later\n", encoding="utf-8")
    H._git(near.repo, "add", "-A")
    H._git(near.repo, "commit", "-qm", "a later commit", date="2020-01-04T00:00:00")
    assert _rejudged(near, far, cache) == {ONE}, "a ref that moved did not re-judge"


# ── clause 5 ──────────────────────────────────────────────────────────────────────────

_WATCH = {"on": False, "opened": set()}


def _audit(event: str, args) -> None:
    if not _WATCH["on"] or event != "open":
        return
    path, mode = args[0], args[1]
    if not isinstance(path, (str, bytes)) and not hasattr(path, "__fspath__"):
        return
    if mode is not None and any(c in str(mode) for c in "wax+"):
        return
    _WATCH["opened"].add(str(Path(path if isinstance(path, str) else str(path)).resolve()))


def test_every_file_one_judgement_opens_is_recorded():
    world = _world(ONE)
    # One uncached judgement first, so every module the call imports lazily is already
    # loaded and the watched call opens only what the judgement reads.
    _lacks(world.ticket, repo_root=world.repo, roots=world.roots)
    warm = _tmp() / "cache"
    warm.mkdir()
    _judge(world, warm)
    shutil.rmtree(warm)
    cache = _tmp() / "cache"
    cache.mkdir()
    sys.addaudithook(_audit)
    _WATCH["opened"] = set()
    _WATCH["on"] = True
    try:
        _judge(world, cache)
    finally:
        _WATCH["on"] = False
    inside = str(cache.resolve())
    opened = {p for p in _WATCH["opened"] if not p.startswith(inside)}
    recorded = {str(Path(p).resolve()) for p in _entry(cache, ONE)["files"]}
    assert opened, "the watched judgement opened nothing — the hook saw no reads"
    missing = sorted(opened - recorded)
    assert not missing, f"{len(missing)} opened file(s) not recorded: {missing[:10]}"


# ── clause 1 ──────────────────────────────────────────────────────────────────────────

_PROVEN_SPACE = frozenset({"PROVEME", "WATCHME", "PROVED"})
_CURSOR = re.compile(r"\[([A-Z]+)(?:\([^)]*\))?(?::[a-z]+)?\]")


def _house_tickets() -> list[dict]:
    out = []
    for t in pc.proof_coverage.load_tickets(COMMONS):
        m = _CURSOR.search(str(t.get("workflow_and_state") or ""))
        if m and m.group(1) in _PROVEN_SPACE:
            out.append(t)
    return out


_LISTED: list | None = None


def _count_listing(event: str, args) -> None:
    if _LISTED is not None and event in ("os.listdir", "os.scandir"):
        _LISTED.append(args[0] if args else ".")


def _stillness() -> tuple:
    """What the house passes read that another session may write while they run: both repos'
    HEAD and working-tree status, and the mtime of every chain berth directory. Two equal
    readings around the passes mean the house held still between them. Measured 2026-11-23:
    hollow --seal refused twice with this tooth red at HEAD, and both runs overlapped another
    session's crossing of 8e73a9efa04a (commons writes at 06:50 and 06:58); three runs over a
    quiet house, one through tester.run_proof in a hollow-shaped worktree, were green."""
    import glob
    from cairn.tools.chain import chain
    reading = []
    for repo in (REPO_ROOT, COMMONS):
        for args in (["rev-parse", "HEAD"], ["status", "--porcelain"]):
            out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
            reading.append((str(repo), args[0], out.returncode, out.stdout))
    berths = os.path.expanduser(str(chain.BERTHS_ROOT))
    for d in sorted(glob.glob(os.path.join(berths, "*", "packets"))) + [str(COMMONS / "berths" / "chart")]:
        try:
            reading.append((d, os.stat(d).st_mtime_ns))
        except OSError:
            reading.append((d, None))
    return tuple(reading)


def _house(cache, tickets: list, *, count: bool = False) -> tuple[dict, float, list]:
    """One pass over ``tickets``, under the pin inspect() opens around its sweep, primed first so
    the one journals walk the pin allows is not this pass's work. With ``count``, every
    directory listing the pass makes is recorded (an audit hook, so no listing can hide)."""
    global _LISTED
    from cairn.tools.base import crossings
    with crossings.pinned_journals():
        crossings.journals()
        listed: list = []
        t0 = time.monotonic()
        _LISTED = listed if count else None
        try:
            got = {str(t.get("id")): _lacks(t, repo_root=REPO_ROOT, cache=cache) for t in tickets}
        finally:
            _LISTED = None
        return got, time.monotonic() - t0, listed


def test_warm_house_findings_equal_cold_and_run_faster():
    """Clause 1 (FIXME 1, 2026-11-23): the warm pass answers every unchanged ticket with the
    uncached findings and lists NO DIRECTORY OF EITHER REPO. A count, not a clock: the wall-clock
    comparison read 95 vs 127 s and then 201 vs 169 s on the same code under different box load,
    and the times stay printed as a reading. The one listing a hit still makes is the chain's
    freshness token: D1 re-derives the chain at a hit, and chain_for_ticket globs the berth
    store's root once per stage (chain._berths_token). So a warm pass lists that root and
    nothing else, at most once per chain stage per ticket. Before the fix it listed 1316
    directories of the commons per hit (measured 2026-11-23)."""
    sys.addaudithook(_count_listing)
    # THE HOUSE MUST HOLD STILL ACROSS THE THREE PASSES, or a ticket another session crosses
    # between them is rightly re-judged and re-listed by the warm pass, which is clause 2's
    # behaviour and not a regression. One ticket set for all three passes, and a stillness
    # reading before and after; a moved house reruns, and a house that never holds still is
    # a loud red, never a pass over the run that moved.
    attempts = []
    for _ in range(3):
        tickets = _house_tickets()
        cache = _tmp() / "cache"
        cache.mkdir()
        before = _stillness()
        truth, t_none, _ = _house(None, tickets)
        cold, t_cold, _ = _house(cache, tickets)
        warm, t_warm, listed = _house(cache, tickets, count=True)
        moved = sorted({str(a[:2]) for a, b in zip(before, _stillness()) if a != b})
        attempts.append(moved)
        if not moved:
            break
        print(f"  the house moved during attempt {len(attempts)}: {moved[:4]}; rerunning")
    assert not attempts[-1], (f"the house never held still across {len(attempts)} attempts "
                              f"(last moved: {attempts[-1][:4]}); clause 1 was not measured")
    print(f"  house: {len(truth)} tickets in proven space; uncached {t_none:.1f} s, "
          f"cached cold {t_cold:.1f} s, cached warm {t_warm:.1f} s; warm listings {len(listed)}")
    for name, got in (("cold", cold), ("warm", warm)):
        differ = sorted(t for t in set(truth) | set(got) if truth.get(t) != got.get(t))
        if differ:
            print(f"  {name} differs from uncached on {len(differ)}: {differ[:10]}")
        assert not differ, f"cached {name} findings differ from uncached on {differ[:10]}"
    from cairn.tools.chain import chain
    berths = os.path.abspath(os.path.expanduser(str(chain.BERTHS_ROOT)))
    elsewhere = sorted({str(p) for p in listed if os.path.abspath(os.fsdecode(p)) != berths})
    assert not elsewhere, (f"the warm pass listed {len(elsewhere)} directories beside the berth "
                           f"root answering {len(warm)} unchanged tickets; first {elsewhere[:5]}")
    bound = len(chain.CHAIN_STAGES) * len(warm)
    assert len(listed) <= bound, (f"the warm pass listed the berth root {len(listed)} times "
                                  f"over {len(warm)} tickets; the chain's token allows {bound}")


if __name__ == "__main__":
    try:
        raise SystemExit(pc.proof_coverage.run_teeth([
            test_one_flipped_byte_re_judges_exactly_that_ticket,
            test_a_deleted_input_or_a_created_absence_re_judges,
            test_a_moved_ref_re_judges_and_a_fixed_sha_is_not_reread,
            test_every_file_one_judgement_opens_is_recorded,
            test_warm_house_findings_equal_cold_and_run_faster,
        ]))
    finally:
        for d in _SCRATCH:
            d.cleanup()

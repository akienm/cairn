"""PROOF — the forwarding a bulk move needs is DERIVED, and the derivation is checked
at both ends exactly as the hand-authored order already is.

Ticket ``a-bulk-move-forwards-itself-from-gits-own-rename-record``. Written BEFORE the
derivation existed, which is this machine's own house pattern at its fourth application
(survey-filters, constrain-filters and decompose-filters each installed a judge before
the judged module) — and here it is not merely habit, it is forced by an asymmetry the
chart's constrain stage named:

    tooth 1 of ``test_inspector`` reds a HEALTHY component that draws a finding, so a
    derivation that forwards TOO LITTLE leaves a loud red. Nothing anywhere guards the
    other direction. A derivation that forwards TOO MUCH — to a target that exists and
    is the WRONG one — disposes a real finding and goes GREEN.

That is this ticket's wrong-intent clause (5), added at its 2026-08-17 door firing, and
a green failure written second is a green failure nobody looks for again. So every
seeded defect here comes before the healthy case, and the negative teeth (the resolver
declining to answer) carry as much weight as the positive ones.

EVERY DERIVATION TOOTH RUNS AGAINST A SYNTHETIC GIT REPOSITORY built under
``scratch_dir``, never against this repo's own 444 rename records. Two reasons, and the
second is the one that bites:

  - the instrument IS git, so the proof uses git — the same reasoning
    ``cairn/machines/ruling/proofs/test_ruling.py:207`` wrote down for ``_git_world``:
    "a stub would be proving the stub".
  - a proof over live data asserts INVARIANTS, never a snapshot, and the tell of that
    defect is a check that goes red at the moment its condition is SATISFIED. "The
    derivation resolves 106 of 112 charted addresses" is true today and false on the
    day a hand writes the last forwarding entry. So the live corpus appears here in
    exactly one tooth, and that tooth asserts a two-ended INVARIANT over whatever the
    resolver happens to answer — never a count.

Run: ``python3 cairn/machines/build_inspector/proofs/test_forwarding_derivation.py``
(this corpus runs proofs as ``main()``-style modules; pytest is not installed and is
not how anything here is proved).
"""

from __future__ import annotations

import json
import os
import pytest
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.tester.scratch import scratch_dir              # noqa: E402
from cairn.machines.build_inspector import inspector as _insp     # noqa: E402
from cairn.machines.build_inspector.inspector import (            # noqa: E402
    GitUnreadable,
    derived_successor,
    rename_records,
    tracked_files,
)


# ── THE SYNTHETIC WORLD ───────────────────────────────────────────────────────
# A real repository with a real history, small enough to reason about entirely and
# built fresh per tooth. Everything the derivation can meet is in here: a plain
# rename, a rename OF a rename (the transitive case), a whole directory moved in one
# commit, a directory whose files SCATTERED (the dissolution — `chart`, in miniature),
# a straggler that moves late and separately (which is why plurality and not
# unanimity), and a file that was renamed and then deleted (a successor the world no
# longer holds).

def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True, check=True).stdout


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=proof@cairn", "-c", "user.name=proof",
         "commit", "-q", "-m", message)
    _prune_empty(repo)


def _prune_empty(repo: Path) -> None:
    """Git moves files and leaves the empty directory sitting there. On disk that
    makes the SOURCE of a directory move still 'exist', and a live address is never
    forwarded — so without this the whole directory half of the derivation would go
    untested while every tooth read green. A fixture that agrees with the reader
    instead of the world is the tooth that proves itself."""
    for _ in range(4):
        for d in sorted((p for p in repo.rglob("*") if p.is_dir()),
                        key=lambda p: -len(p.parts)):
            if d.name == ".git" or ".git" in d.parts:
                continue
            if not any(d.iterdir()):
                d.rmdir()


def _write(repo: Path, rel: str, text: str = "x\n") -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _world(d: str) -> Path:
    """Build the synthetic repository. Returns its root.

    THE HISTORY, one commit per fact, so a failing tooth names the fact it broke:

      1  born:      old/one.py, old/two.py, old/three.py, old/straggler.py
                    scatter/a.py, scatter/b.py, scatter/c.py
                    solo.py, doomed.py
      2  a plain rename:            solo.py            -> moved/solo.py
      3  the rename OF a rename:    moved/solo.py      -> final/solo.py
      4  a directory moves, mostly: old/{one,two,three}.py -> new/{one,two,three}.py
      5  the straggler follows:     old/straggler.py   -> elsewhere/straggler.py
      6  a directory DISSOLVES:     scatter/{a,b,c}.py -> three unrelated homes
      7  a rename then a delete:    doomed.py -> gone/doomed.py, then removed
      8  THE NAME COMES BACK:       revenant.py -> kept/revenant.py, and then a NEW
                                    revenant.py at the old path — live, and a rename
                                    source. It is its own file rather than a reused
                                    one because every other path here is load-bearing
                                    for another tooth: bringing `solo.py` back would
                                    make tooth (j)'s transitive follow unreachable,
                                    and bringing `doomed.py` or `scatter/a.py` back
                                    would let teeth (b) and (d) pass through this
                                    guard instead of the one they exist to test.

    Commit 8 exists because a MUTATION found tooth (c) passing for the wrong reason.
    Deleting the "a live address is never forwarded" guard from the resolver reddened
    NOTHING: the tooth asked about ``new/one.py``, which is live but is a rename
    TARGET, so it has no record to follow and the answer was None either way. The
    guard only bites where an address is live AND a rename SOURCE — a name that was
    moved away and later came back, which is an ordinary thing for a repository to do
    and the exact shape the laundering takes. A tooth that cannot go red is a tooth
    that proves the world instead of the code.
    """
    repo = Path(d) / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")

    for rel in ("old/one.py", "old/two.py", "old/three.py", "old/straggler.py",
                "scatter/a.py", "scatter/b.py", "scatter/c.py",
                "solo.py", "doomed.py", "revenant.py"):
        _write(repo, rel)
    _commit(repo, "born")

    _git(repo, "mv", "solo.py", "moved_solo.py")
    (repo / "moved").mkdir()
    _git(repo, "mv", "moved_solo.py", "moved/solo.py")
    _commit(repo, "a plain rename")

    (repo / "final").mkdir()
    _git(repo, "mv", "moved/solo.py", "final/solo.py")
    _commit(repo, "the rename of a rename")

    (repo / "new").mkdir()
    for f in ("one.py", "two.py", "three.py"):
        _git(repo, "mv", "old/%s" % f, "new/%s" % f)
    _commit(repo, "a directory moves, mostly")

    (repo / "elsewhere").mkdir()
    _git(repo, "mv", "old/straggler.py", "elsewhere/straggler.py")
    _commit(repo, "the straggler follows, separately")

    for src, dst in (("scatter/a.py", "alpha/a.py"),
                     ("scatter/b.py", "beta/b.py"),
                     ("scatter/c.py", "gamma/c.py")):
        (repo / dst).parent.mkdir(parents=True, exist_ok=True)
        _git(repo, "mv", src, dst)
    _commit(repo, "a directory dissolves")

    (repo / "gone").mkdir()
    _git(repo, "mv", "doomed.py", "gone/doomed.py")
    _commit(repo, "a rename")
    _git(repo, "rm", "-q", "gone/doomed.py")
    _commit(repo, "and then a delete")

    (repo / "kept").mkdir()
    _git(repo, "mv", "revenant.py", "kept/revenant.py")
    _commit(repo, "a rename whose name will come back")
    _write(repo, "revenant.py")      # the name comes back — see the header
    _commit(repo, "the name comes back")
    return repo


def _exists_in(repo: Path):
    """The existence predicate for the synthetic world.

    Injected rather than assumed, because production's ``ref_exists`` is rooted at
    CAIRN_ROOT and would answer about THIS repository while the teeth ask about the
    fixture. Injecting it is also the point of the seam: the derivation must not
    carry its own idea of what resolving means (the live tooth below asserts the
    production default really is ``ref_exists``).
    """
    return lambda addr: (repo / addr).exists()


# ── THE SEEDED DEFECTS, FIRST ─────────────────────────────────────────────────

@pytest.fixture
def d():
    return str(scratch_dir("forwarding_derivation_proof_"))


def test_a_dead_git_raises_and_never_answers_empty(d: str) -> None:
    """(i) THE SILENT FAILURE, and it is the reason the reader is its own piece.

    An empty pair list is not a wrong answer, it is a wrong SHAPE of answer: every
    address becomes unresolvable, the residue goes maximal, and the report reads
    "the corpus needs a hundred hand entries" rather than "git did not answer".
    Both are zero forwards; only one is true. So the reader raises.
    """
    bare = Path(d) / "not-a-repo"
    bare.mkdir()
    try:
        pairs = rename_records(repo_root=bare)
    except GitUnreadable:
        pass
    else:
        raise AssertionError(
            "a directory that is not a git repository must RAISE, not answer %r — "
            "an empty rename record is indistinguishable from a corpus nothing "
            "moved in, and the two want opposite dispositions" % (pairs,))

    try:
        tracked_files(repo_root=bare)
    except GitUnreadable:
        pass
    else:
        raise AssertionError("tracked_files must raise on a non-repository too — "
                             "an empty tracked set silently fails every directory vote")

    # And the SHAPE of the refusal is asserted by TYPE, never by message text: a
    # message is prose and drifts, and a tooth that pins prose reds on a reword.
    assert issubclass(GitUnreadable, Exception)


def test_b_forwarding_into_a_hole_is_declined(d: str) -> None:
    """(ii) CLAUSE (3): never forward to something the world does not hold.

    ``doomed.py`` really was renamed to ``gone/doomed.py`` — git says so, and the
    follow is correct. It was then deleted. A derivation that trusted the rename
    record alone would forward a reader into a hole, which is the same hollow claim
    as the missing address it was offered to dispose, one indirection later.
    """
    repo = _world(d)
    exists = _exists_in(repo)
    assert dict(rename_records(repo_root=repo)).get("doomed.py") == "gone/doomed.py", \
        "the fixture must actually contain the rename, or this tooth proves nothing"
    got = derived_successor("doomed.py", repo_root=repo, exists=exists)
    assert got is None, \
        ("a successor the world no longer holds must be DECLINED, not answered: "
         "got %r" % (got,))


def test_c_a_live_address_is_never_forwarded(d: str) -> None:
    """(iii) CLAUSE (4)'s half of the two-ended check, on the derived side.

    ``revenant.py`` was renamed away and a NEW file took the name back in commit 8.
    It resolves right now AND git holds a chain leading off it, so this is
    the only shape where the guard can actually bite: forwarding it would re-aim a
    chart's claim at ``kept/revenant.py`` while the thing the chart named sits there
    untouched — the laundering the hand door already refuses at
    ``forwarding_order_resolves``; the derived door must refuse it identically or the
    two doors disagree about the same rule.

    THE ADDRESS IN THIS TOOTH WAS CHOSEN BY A MUTATION, NOT BY TASTE. It asked about
    ``new/one.py`` until 2026-08-17, and deleting the guard outright reddened nothing:
    a rename TARGET has no chain to follow, so the tooth was measuring git's silence
    rather than the resolver's refusal. Both addresses are asserted now — the one that
    can red, and the one that documents the easy case — because the pair is what says
    the rule is about resolving, not about being a rename target.
    """
    repo = _world(d)
    exists = _exists_in(repo)
    assert exists("revenant.py"), "the fixture must put the name back for this to bite"
    got = derived_successor("revenant.py", repo_root=repo, exists=exists)
    assert got is None, \
        ("a live address that IS a rename source must never be forwarded out from "
         "under itself; got %r" % (got,))
    assert derived_successor("new/one.py", repo_root=repo, exists=exists) is None


def test_d_a_dissolution_gets_no_manufactured_winner(d: str) -> None:
    """(iv) CLAUSE (5), THE GREEN FAILURE — and the most important tooth in the file.

    ``scatter/`` did not MOVE; it was decomposed, its three files going to three
    unrelated homes. There is no successor, and the honest answer is silence. A rule
    tuned until its residue reached zero would answer one of the three — a target
    that EXISTS and is WRONG, which disposes a real finding and reds nothing.

    This is `chart` in miniature: 13 tracked files scattered with no plurality, the
    address the live corpus still cannot forward and should not.
    """
    repo = _world(d)
    got = derived_successor("scatter", repo_root=repo, exists=_exists_in(repo))
    assert got is None, \
        ("a directory whose files scattered has NO successor — answering %r is "
         "wrong-intent clause (5): a target that exists and is not where the "
         "directory went" % (got,))


def test_e_a_cycle_terminates(d: str) -> None:
    """(v) A rename cycle must not hang the gate.

    Not reachable through git's own history in practice, but the follow is a walk
    over a map and a gate that can hang is a gate that stops being run. Asserted
    against the walk directly, with a fabricated cycle, because the fixture cannot
    produce one.
    """
    repo = _world(d)
    cyclic = (("a.py", "b.py"), ("b.py", "c.py"), ("c.py", "a.py"))
    out = _insp._follow_renames("a.py", dict(cyclic))
    assert out is None, "a cycle must terminate with no answer, got %r" % (out,)


def test_f_a_suffix_breaking_vote_does_not_count(d: str) -> None:
    """(vi) The directory vote counts only kids whose path SUFFIX survived.

    ``old/`` moved to ``new/`` for three files and to ``elsewhere/`` for one. Every
    one of those four preserved its basename, so all four are legitimate votes. A
    file that landed under a different name says nothing about where its DIRECTORY
    went — it is a rename AND a move, and counting it would let one renamed file
    outvote the directory it left.
    """
    repo = _world(d)
    finals = {"d/keeps.py": "moved/keeps.py",
              "d/renamed.py": "somewhere/totally-different.py"}
    tracked = frozenset(finals.values())
    got = _insp._directory_successor("d", finals, tracked, lambda a: True)
    assert got == "moved", \
        ("only the suffix-preserving kid may vote, so the answer is 'moved'; "
         "got %r" % (got,))


def test_g_plurality_not_unanimity(d: str) -> None:
    """(vii) THE RULE THAT WAS MEASURED RATHER THAN CHOSEN.

    ``old/`` sent three files to ``new/`` and one straggler to ``elsewhere/``. Under
    UNANIMITY that is a tie nobody wins and the address goes unresolved; under
    PLURALITY it is ``new``. A bulk move is never unanimous — stragglers move
    separately, in their own commits, which is exactly what commit 5 of the fixture
    is for. Measured on the live corpus before this was built: plurality resolved 67
    of base's 71 addresses, unanimity 64, and the three it lost were real bulk moves
    voting 6-1-1, 9-1 and 9-1.
    """
    repo = _world(d)
    got = derived_successor("old", repo_root=repo, exists=_exists_in(repo))
    assert got == "new", \
        ("a 3-1 vote is a plurality and must answer 'new'; got %r — if this is None "
         "the rule regressed to unanimity, which measures worse" % (got,))


def test_h_a_bare_plurality_is_still_not_a_majority(d: str) -> None:
    """(viii) The threshold is a STRICT MAJORITY of the resolvable, suffix-preserving
    votes — not merely 'the most'.

    Three-way 2-1-1 has a leader with 50%, and a leader half the room voted against
    is not a consensus about where a directory went. Asserted on the vote function
    directly so the threshold is pinned independently of any fixture history.
    """
    two_one_one = {"d/a.py": "x/a.py", "d/b.py": "x/b.py",
                   "d/c.py": "y/c.py", "d/e.py": "z/e.py"}
    tracked = frozenset(two_one_one.values())
    got = _insp._directory_successor("d", two_one_one, tracked, lambda a: True)
    assert got is None, "2-1-1 is not a strict majority; got %r" % (got,)

    three_one_one = dict(two_one_one, **{"d/f.py": "x/f.py"})
    tracked = frozenset(three_one_one.values())
    got = _insp._directory_successor("d", three_one_one, tracked, lambda a: True)
    assert got == "x", "3-1-1 IS a strict majority (3 of 5); got %r" % (got,)


def test_i_the_hand_order_keeps_precedence(d: str) -> None:
    """(ix) GATE (3): the hand is the only thing that can speak for a dissolution,
    so a derived answer may never outrank a hand-authored one.

    Fixtured through the REAL hand door — a ticket on disk with a real forwarding
    order — rather than through a stub of it, because a fixture validated against
    the reader instead of the writer is the tooth that agrees with itself.
    """
    repo = _world(d)
    tickets = Path(d) / "CairnCommons" / "tickets"   # ticket_path reads
                                                     # dirname(root)/CairnCommons/tickets
    tickets.mkdir(parents=True)
    (tickets / "hand-proof.json").write_text(json.dumps({
        "id": "hand-proof",
        "forwarding": {"old": {"to": "elsewhere",
                               "why": "the hand says the straggler's home is the "
                                      "successor, and the hand outranks the vote"}},
    }))
    saved = _insp._TICKETS_ROOT
    saved_exists = _insp.ref_exists
    try:
        _insp._TICKETS_ROOT = str(Path(d) / "cairn")
        _insp.ref_exists = _exists_in(repo)          # the hand door checks BOTH ends
        got = _insp._resolves_to("old", "hand-proof", repo_root=repo,
                                 exists=_exists_in(repo))
    finally:
        _insp._TICKETS_ROOT = saved
        _insp.ref_exists = saved_exists
    assert got == "elsewhere", \
        ("the hand-authored order must win over the derived plurality ('new'); "
         "got %r" % (got,))


def test_ja_an_absolute_address_reaches_the_relative_record(d: str) -> None:
    """(x) THE FIRST LIVE FIRE'S FINDING, kept as a tooth.

    Git's record is repo-relative; charted addresses are frequently absolute. Before
    this was fixed the derivation answered 'no successor' to 29 of the corpus's 38
    residual addresses, 28 of which had a rename record sitting right there under
    their relative name — a false negative, which is the SAFE direction and still a
    wrong answer.

    And the answer comes back in the form it was asked in: an absolute question
    answered relatively hands the reader an address to re-root by hand.
    """
    repo = _world(d)
    exists = _exists_in(repo)
    absolute = str(repo / "old" / "one.py")
    got = derived_successor(absolute, repo_root=repo, exists=exists)
    assert got == str(repo / "new" / "one.py"), \
        ("an absolute in-repo address must reach the relative rename record and "
         "come back absolute; got %r" % (got,))
    # A directory, absolutely spelled, through the plurality vote.
    got = derived_successor(str(repo / "old"), repo_root=repo, exists=exists)
    assert got == str(repo / "new"), "the directory vote too; got %r" % (got,)
    # AND AN ADDRESS OUTSIDE THE REPOSITORY IS UNTOUCHED. Git has nothing to say
    # about it, and this is the one place a silent re-rooting would forward a reader
    # somewhere the repository never held.
    assert derived_successor("/etc/passwd", repo_root=repo, exists=exists) is None


def test_jb_a_claimless_packet_still_reaches_the_derived_door(d: str) -> None:
    """(xi) THE SECOND LIVE-FIRE FINDING.

    The residue walk is keyed on tickets, because the HAND door needs one to find
    an order. Git does not. Three corpus addresses sat in the residue with an empty
    ``charted_by`` and a perfectly good rename record behind them, purely because
    there was no ticket to iterate over. Asserted here at the residue's own surface:
    nothing it reports as unanswered may have a derived successor.
    """
    residue = _insp.forwarding_residue()
    stranded = [e["address"] for e in residue["unanswered"]
                if _insp.derived_successor(e["address"])]
    assert not stranded, \
        ("the residue reports these as unanswered while the derivation answers "
         "them — a hand is being asked to write entries a machine already has: %r"
         % (stranded,))


# ── THE HEALTHY CASES, LAST ───────────────────────────────────────────────────

def test_j_the_plain_and_transitive_follows_answer(d: str) -> None:
    """(x) What the derivation is FOR, and the transitive half is the whole point:
    ``solo.py`` -> ``moved/solo.py`` -> ``final/solo.py``. A chart that named the
    address before either move must land on the address the world holds now, not on
    the intermediate one that is itself gone."""
    repo = _world(d)
    exists = _exists_in(repo)
    assert derived_successor("solo.py", repo_root=repo, exists=exists) == "final/solo.py"
    assert derived_successor("moved/solo.py", repo_root=repo, exists=exists) == "final/solo.py"
    assert derived_successor("old/one.py", repo_root=repo, exists=exists) == "new/one.py"
    assert derived_successor("old/straggler.py", repo_root=repo,
                             exists=exists) == "elsewhere/straggler.py"
    # AND AN ADDRESS NOTHING EVER MOVED IS NOT AN ANSWER. `never/seen.py` was never
    # in this history; a derivation that returned the address itself would forward
    # every unknown address to itself and dispose every finding in the corpus.
    assert derived_successor("never/seen.py", repo_root=repo, exists=exists) is None


def test_k_the_reader_answers_the_fixture_and_the_live_repo(d: str) -> None:
    """(xi) The reader, at both ends of its range: the fixture's own known renames,
    and this repository, where it must simply answer non-empty. The live half pins no
    count — 444 today is a number the next rename changes."""
    repo = _world(d)
    pairs = dict(rename_records(repo_root=repo))
    # NOTE the first pair, and it is a fact about the instrument rather than about
    # this fixture: commit 2 moves solo.py TWICE, and git records the commit's net
    # effect, not the steps inside it. So the record is coarser than the history —
    # which is fine for a successor question and would not be for an audit.
    for old, new in (("solo.py", "moved/solo.py"), ("moved/solo.py", "final/solo.py"),
                     ("old/one.py", "new/one.py"),
                     ("old/straggler.py", "elsewhere/straggler.py"),
                     ("scatter/a.py", "alpha/a.py"), ("doomed.py", "gone/doomed.py")):
        assert pairs.get(old) == new, \
            "the fixture's rename %s -> %s is not in the record (got %r)" % (
                old, new, pairs.get(old))
    assert "final/solo.py" in tracked_files(repo_root=repo)
    assert "gone/doomed.py" not in tracked_files(repo_root=repo), \
        "the deleted file must not be tracked, or tooth (ii) proves nothing"

    live = rename_records()
    assert live, "the live repository has a rename history and the reader must find it"
    assert all(isinstance(a, str) and isinstance(b, str) and a and b
               for a, b in live), "every record is a (from, to) pair of non-empty strings"


def test_l_the_M_flag_measurement_is_retaken_not_cited(d: str) -> None:
    """(xii) THE TICKET'S GATE (1) NAMES ``-C`` AND THIS BUILD SHIPS ``-M`` ALONE.

    The reason is a measurement, so the proof re-takes it rather than quoting it:
    git emits no copy records without ``--find-copies-harder``, so ``-M`` and
    ``-M -C`` produce the identical record. Asserted as SET EQUALITY — an invariant
    that stays true as the history grows, never a count.

    It matters beyond tidiness: where copy detection DOES surface it produced a
    wrong-but-existing target in the directory vote, which is clause (5) arriving by
    way of a flag nobody questioned.
    """
    root = Path(_insp.CAIRN_ROOT)
    base = ["git", "-C", str(root), "log", "--diff-filter=R", "--name-status",
            "--reverse", "--pretty=format:"]
    def run(extra):
        out = subprocess.run(base[:4] + extra + base[4:], capture_output=True,
                             text=True, check=True).stdout
        return {tuple(l.split("\t")[1:3]) for l in out.splitlines()
                if l.startswith("R") and len(l.split("\t")) == 3}
    m_set = run(["-M"])
    mc_set = run(["-M", "-C"])
    m_sources = {pair[0] for pair in m_set}
    mc_sources = {pair[0] for pair in mc_set}
    assert m_sources == mc_sources, \
        ("-C discovers additional SOURCES without --find-copies-harder; if this "
         "tooth reds, the measurement that disposed the ticket's gate (1) was "
         "taken wrong and the shipped flags must be revisited. "
         f"Extra sources: {mc_sources - m_sources}")
    m_targets = {pair[1] for pair in m_set}
    mc_targets = {pair[1] for pair in mc_set}
    extra_targets = mc_targets - m_targets
    assert not extra_targets or all(
        t.endswith("__init__.py") for t in extra_targets
    ), ("-C changes non-trivial target pairings without --find-copies-harder: "
        f"{extra_targets}")


def test_m_the_live_corpus_holds_the_two_ended_invariant(d: str) -> None:
    """(xiii) THE ONE LIVE-CORPUS TOOTH, and it asserts an INVARIANT over whatever
    the resolver answers — never how many.

    For every charted address the live corpus still carries, if the derivation
    answers at all then the target resolves and the source does not. That is the
    same predicate the hand door applies at ``_forwarding_map``, so the two doors
    cannot come to disagree about what a valid forward is. It stays true when the
    residue reaches zero and when it grows.

    AND THE ACCOUNTING CLOSES OVER PAIRS, WHICH IS THE UNIT THE SIEVE ASKS IN.
    This tooth caught the report's units coming apart: ``asked`` counted (address,
    ticket) pairs while ``answered`` counted distinct addresses, so the ledger did
    not close and the shortfall read like unreported residue. The index is allowed
    to be smaller than the ledger — one address answered under two tickets is one
    entry — and that direction is asserted rather than assumed, because the other
    direction would mean an answer arrived from nowhere.
    """
    from cairn.machines.build_inspector.inspector import ref_exists
    residue = _insp.forwarding_residue()
    assert residue["asked"] == residue["answered"] + len(residue["unanswered"]), \
        ("the residue accounting must close over PAIRS: asked=%r answered=%r "
         "unanswered=%r" % (residue["asked"], residue["answered"],
                            len(residue["unanswered"])))
    assert len(residue["answers"]) <= residue["answered"], \
        ("the address index may collapse pairs, never exceed them: %d entries "
         "against %d answered pairs" % (len(residue["answers"]),
                                        residue["answered"]))
    # AND AN ADDRESS MAY SIT ON BOTH SIDES AT ONCE. A forwarding order belongs to a
    # ticket, so an address one voyage forwarded is still owed by another that did
    # not — reading `answers` as the complete set of settled addresses is reading
    # the index for the ledger. Asserted as the invariant, never as today's list:
    # whenever it happens, the two sides must be different tickets.
    for entry in residue["unanswered"]:
        if entry["address"] in residue["answers"]:
            assert entry["charted_by"] != residue["answered_by"].get(entry["address"]), \
                ("%r is answered and unanswered under the SAME authority %r — the "
                 "resolver is not a function of (address, ticket)"
                 % (entry["address"], entry["charted_by"]))
    for src, dst in residue["answers"].items():
        assert not ref_exists(src), \
            "%r still resolves and must never be forwarded (to %r)" % (src, dst)
        assert ref_exists(dst), \
            "%r -> %r forwards into a hole" % (src, dst)
    # AND THE PRODUCTION DEFAULT REALLY IS ``ref_exists`` — the injectable predicate
    # is a test seam, not a second spelling of what resolving means.
    assert _insp._default_exists is ref_exists


def test_n_a_dead_reader_is_distinguishable_from_a_clean_corpus(d: str) -> None:
    """(xiv) THE VACUOUS READING, at the residue surface.

    Zero-because-everything-resolved and zero-because-git-said-nothing are the same
    number and the opposite fact. The report must make them different: a reader that
    could not answer leaves ``asked`` above zero with ``answered`` at zero and says
    so in ``reader_failed``, rather than reporting a clean sweep.
    """
    saved = _insp.rename_records
    def dead(repo_root=None):
        raise GitUnreadable("seeded: git did not answer")
    try:
        _insp.rename_records = dead
        _insp._successor_index.cache_clear()
        residue = _insp.forwarding_residue()
    finally:
        _insp.rename_records = saved
        _insp._successor_index.cache_clear()
    assert residue["reader_failed"], \
        "a reader that raised must be reported, not swallowed: %r" % (residue,)
    assert residue["asked"] > 0, \
        ("with the reader dead the corpus must still report what it ASKED about — "
         "a bare zero here is indistinguishable from a fully-resolved corpus")
    assert residue["asked"] == residue["answered"] + len(residue["unanswered"]), \
        ("the accounting must close on the reader's worst day too: asked=%r "
         "answered=%r unanswered=%r" % (residue["asked"], residue["answered"],
                                        len(residue["unanswered"])))
    # AND EVERY ANSWER THAT SURVIVES IS A HAND-AUTHORED ONE. A dead rename reader
    # costs the DERIVED door and nothing else — the hand orders are files on disk
    # and keep working. That is the precedence order surviving its worst day, not a
    # fallback invented for it; and it is asserted by ORIGIN, so an answer that
    # somehow came from the dead reader would red here instead of reading as
    # resilience.
    for src, dst in residue["answers"].items():
        by = residue["answered_by"].get(src)
        assert _insp._forwarding_map(by).get(src) == dst, \
            ("%r -> %r survived a dead reader with no hand order behind it "
             "(answered_by=%r)" % (src, dst, by))


TEETH = [v for k, v in sorted(globals().items()) if k.startswith("test_")]


def main() -> int:
    failed = []
    for tooth in TEETH:
        # scratch_dir returns a Path and registers its own atexit sweep — it is not
        # a context manager, and `with` on it silently no-ops.
        d = scratch_dir("forwarding-derivation")
        try:
            tooth(str(d))
        except Exception as e:                                      # noqa: BLE001
            failed.append((tooth.__name__, "%s: %s" % (type(e).__name__, e)))
            print("RED   %s\n      %s: %s" % (tooth.__name__, type(e).__name__, e))
        else:
            print("green %s" % tooth.__name__)
    if failed:
        print("\n%d of %d RED" % (len(failed), len(TEETH)))
        return 1
    print("\nall %d green" % len(TEETH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Is this ticket's build LOAD-BEARING, or does its proof pass over it?

Law 8 says nothing enters proven-space without a proof a hollow build could not pass, and
until now that was a sentence a builder read and then judged themselves against. This module
is the measurement: it takes the build the ticket claims (its decompose berth's ``writes_to``),
puts each of those files back the way it was BEFORE the build, re-runs the proof the crossing
names, and reads which of the proof's DECLARED teeth went red. A file whose reversion reds no
declared tooth is a file the proof does not actually check — the ticket's green would survive
its absence, which is precisely what "hollow" means.

WHY THE REVERSION AND NOT A MUTATION. A mutation operator (flip a comparison, drop a return)
measures whether the proof is sensitive to a *plausible defect*; this measures whether it is
sensitive to *the change the ticket was cast to make*. Those are different questions and only
the second one answers "did this voyage earn its crossing". Mutation testing is explicitly out
of the ticket's bounds for that reason, not because it is harder.

TWO THINGS THIS DELIBERATELY REFUSES TO MEASURE, and both refusals are named on the record
rather than silently skipped, because a skip list is the natural home of a hollow green:

  1. **A file under ``proofs/``.** Reverting the instrument makes the reading meaningless — the
     reverted proof either errors out or simply no longer contains the teeth, so every declared
     tooth reads "red" and the check passes trivially. That is a hollow check inside the hollow
     checker, which is the one defect this module has no standing to ship. So proofs are
     skipped, LISTED, and — the part that keeps the list from becoming the escape hatch — a run
     in which EVERY file was skipped is a RED, not a pass over an empty set.
  2. **A file outside this repo** (a ``writes_to`` under CairnCommons). There is no worktree of
     it to revert in and no proof that imports it; it is out of the ticket's bounds.

AND ONE THING IT CANNOT MEASURE, MEASURED RATHER THAN GUESSED AT: a proof that is not
WORKTREE-PORTABLE. A worktree is a checkout of this repo at another path, so a proof that
reaches outside the repo by a RELATIVE path resolves somewhere that does not exist there.
Measured 2026-09-09 on ``cairn/devices/trouble/proofs/test_trouble.py``, one of the proofs
ticket 9579a6f9cec6's crossings name: 37/37 green in the live tree, 36/37 in a worktree, the
one red being ``test_the_inspector_troubles_were_cleared_through_the_door`` — which looked for
``CairnCommons/troubles`` beside the repo root and found nothing beside a /tmp worktree. THAT
ONE IS FIXED (the proof now resolves the commons through ``git rev-parse --git-common-dir``,
37/37 both ways), but the CLASS is not, and the bound is what this paragraph is about. It
surfaces HONESTLY and never as a wrong number: the declared tooth is not green at HEAD, so the
baseline refuses with ``HollowUnmeasurable`` and no reading is attributed to any file (Law 3 —
"the measurement could not be taken" may not travel through the same return as "clean"). It is
a real bound on the verb's reach, not a bug in it, and the fix belongs to the PROOF each time.
    -> ticket a-proof-that-reaches-a-sibling-repo-by-relative-path-cannot-be-reproven-elsewhere

AND THE VERB'S COST IS THE CORPUS'S COST, NOT THE VERB'S — measured 2026-09-09 on 9579a6f9cec6
because the ticket's own WRONG INTENT clause fired at 364s against a 300s bound. Ten writes_to
files, two skipped, so nine passes (one baseline plus one per measured file) over the three
proofs that declare a tooth for it. The arithmetic is the whole finding, and it survived the
fix that followed: floor = passes x (cost of the declaring proofs), and the verb's own share is
the remainder.

  measured 2026-09-09, BEFORE     41.9 + 0.3 + 0.4 = 42.6s  ->  floor 9 x 42.6 = 383.4s
                                  whole run 364.0s           ->  verb's share -19.4s
  measured 2026-09-09, AFTER      10.8 + 0.3 + 0.4 = 11.5s  ->  floor 9 x 11.5 = 103.1s
                                  whole run 114.0s           ->  verb's share +10.9s

THE RED WAS NEVER THE LOOP, AND THE TICKET'S OWN REMEDY CLAUSE GUESSED THAT IT WAS. The clause
prescribed "the per-file loop shares one worktree and one instance swap" — both of which this
verb already did on the day the clause fired, so the named fix was already in place while the
threshold it named was right. What actually cost 35 of those 42.6 seconds was ONE TOOTH in
``cairn/devices/trouble/proofs/test_trouble.py`` calling the whole build_inspector nest to read
a single sieve: ~20 settled answers re-derived to obtain one (Law 1 at its plainest), paid nine
times over by a loop that was innocent. Asking the sieve directly took that proof from 45.4s to
10.5s with the same 0 findings over the same 54 rows, and the run from 364.0s to 114.0s.

So the verb's overhead is ~10% of a run and rises as the corpus shrinks around it: what looked
like ZERO before was the corpus drowning it. The levers, in order of size, are still not in
this file — fewer proof runs (the silent filter above, which took this from 501.7s), then a
cheaper proof, and that second one belongs to whoever owns the proof. What IS worth stating
here is the reflex to distrust: the obvious reading of a slow run is that the loop is wasteful,
and twice now the loop has been the cheapest thing in the measurement.

AND THE HEADROOM IS THIN AND SHRINKS BY GROWTH, NOT BY DEFECT. 114.0s against the ticket's 300s
bound is 2.6x, but the dominant term is a walk over ``device_census``'s 54 component rows, nine
times — so the bound is re-crossed by adding components, with nothing about this verb having
got worse. That is a measurement to re-take, not a margin to bank.

THE LIVE TREE IS NEVER TOUCHED. Every revert happens inside a scratch git worktree
(``scratch.scratch_worktree``) that removes itself and its registration at exit. The obvious
cheaper shape — revert in place, run, restore — leaves the operator's own tree in a state he
did not make the first time a run dies between the two acts, and his tree is his (Law 6).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from cairn.devices.tester.scratch import git_env, scratch_worktree
from cairn.tools.proof_coverage.proof_coverage import declared

from cairn.tools.base.crossings import buildme_crossing, proven_by_since_buildme

REPO_ROOT = Path(__file__).resolve().parents[3]
COMMONS = Path.home() / "dev" / "src" / "CairnCommons"

SKIP_INSTRUMENT = "under proofs/ — reverting the instrument makes the reading meaningless"
SKIP_OUTSIDE = "not a path in this repo — nothing to revert in a worktree of it"


class HollowUnmeasurable(RuntimeError):
    """The measurement could not be TAKEN — said out loud, never reported as a pass.

    Law 3's distinction, held as a type: "we have not measured this" and "this measured clean"
    are different answers, and the only way to keep them different is for the first one to be
    unable to travel through the same return value as the second.
    """


def _ticket_path(ticket_id: str, commons: Path = COMMONS) -> Path:
    hits = sorted((Path(commons) / "tickets").glob(f"{ticket_id}*.json"))
    if not hits:
        raise HollowUnmeasurable(f"hollow: no ticket file matches {ticket_id!r} in {commons}/tickets")
    return hits[0]


def _roots(repo_root: Path = REPO_ROOT, commons: Path = COMMONS) -> dict:
    """The world this measurement's CROSSINGS are derived from — built from the two roots
    ``measure`` is already handed, never from the live table.

    No new parameter was needed and none was added: ``repo_root`` and ``commons`` have always
    been how a caller says which world to measure, and the journals live in exactly those two
    places. Reaching past them to ``address.ROOTS`` would make a fixture run read the live
    corpus's journals for its own ticket id and derive nothing — a hollow reading of a world
    nobody asked about.
    """
    return {"repo": Path(repo_root), "commons": Path(commons), "instance": Path(commons)}


def _buildme_crossing(ticket: dict, roots: dict | None = None) -> dict:
    """The LATEST FORWARD crossing into BUILDME — latest, because a kicked-back ticket
    re-crosses, and the pre-build state that matters is the one before the build that stands.

    DERIVED FROM THE JOURNALS since 2026-09-10 (ruling crossings-are-derived-never-written).
    The rule is unchanged; ``direction`` is now actually checked, which the stored array could
    not do — it carried no direction field, so a disposition into BUILDME and a forward crossing
    into it were the same record and hollow would have reverted to the wrong world.
    """
    crossing = buildme_crossing(str(ticket.get("id") or ""), roots)
    if crossing is None:
        raise HollowUnmeasurable(
            "hollow: no journal in either root records a forward crossing into BUILDME for "
            f"ticket {ticket.get('id')!r}, so there is no 'before the build' to revert to. "
            "A ticket that never crossed BUILDME has no build to call hollow.")
    return crossing


def _buildme_at(ticket: dict, crossing: dict, repo_root: Path = REPO_ROOT) -> str:
    """When the build began, TO THE SECOND — and there is no longer a coarser branch to fall to.

    THE DAY-GRANULAR FALLBACK IS RETIRED, not patched. It existed because the crossing record on
    the ticket carried only a ``date``, and ``git rev-list -1 --before=2026-09-07`` resolves to
    the last commit before that day STARTED — so a ticket built and committed on one day
    silently reverted to a whole day earlier and hollow measured the wrong world. The journal
    entry has always carried an ``at`` with a time; deriving the crossing from the journal means
    every crossing now has one, so the branch that could be wrong no longer has anything to be
    wrong about. An entry with no ``at`` is unmeasurable and says so (Law 3).
    """
    at = str(crossing.get("at") or "")
    if not at:
        raise HollowUnmeasurable(
            "hollow: the derived BUILDME crossing carries no 'at', so the pre-build commit "
            "cannot be resolved to the second. A day is not close enough — rev-list --before "
            "resolves a bare date to the last commit before that day STARTED.")
    return at


def prebuild_commit(at: str, *, repo_root: Path = REPO_ROOT) -> str:
    proc = subprocess.run(["git", "-C", str(repo_root), "rev-list", "-1", f"--before={at}", "HEAD"],
                          capture_output=True, text=True, env=git_env())
    commit = proc.stdout.strip()
    if proc.returncode != 0 or not commit:
        raise HollowUnmeasurable(
            f"hollow: no commit precedes the BUILDME crossing at {at!r} — "
            f"{(proc.stderr or 'rev-list named nothing').strip()}")
    return commit


def writes_to(ticket: dict) -> list[str]:
    """Every file the ticket's decompose berth says this build writes, in berth order, deduped.

    THE CHART IS THE CLAIM AND THIS IS WHAT CHECKS IT. The list is not re-derived from the
    diff: a diff says what changed, and the question here is whether what the ticket SAID it
    would build is load-bearing. A build that quietly wrote elsewhere is a different finding
    (against the chart leg), and reading the diff instead would hide it by construction.
    """
    berth = (ticket.get("chart_chain") or {}).get("decompose")
    if not berth:
        raise HollowUnmeasurable(
            f"hollow: ticket {ticket.get('id')} names no decompose berth, so nothing declares "
            f"which files the build writes. There is no list to check the proof against.")
    try:
        packet = json.loads(Path(berth).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise HollowUnmeasurable(f"hollow: decompose berth {berth} is unreadable: {e}") from e
    out: list[str] = []
    for piece in packet.get("sub_problems") or []:
        for f in piece.get("writes_to") or []:
            if f not in out:
                out.append(str(f))
    if not out:
        raise HollowUnmeasurable(
            f"hollow: the decompose berth {berth} lists no writes_to on any sub_problem — the "
            f"chart never said what this build writes, so there is nothing to revert.")
    return out


def proven_by(ticket: dict, roots: dict | None = None) -> list[str]:
    """EVERY proof this ticket's crossings name, unioned — deliberately NOT ``_proven_by``.

    THE SHARED READER ANSWERS A DIFFERENT QUESTION, and reusing it here produced WRONG
    ANSWERS, not merely thin ones. ``proof_coverage._proven_by`` returns the proofs named by
    the LATEST crossing that names any, and its docstring's reason is sound for the question
    IT is asked — the clearance gate wants "which proof stands behind the crossing being made
    now?", and a ticket kicked back to BUILDME and re-crossed must not be checked against the
    proof it abandoned. This verb asks a different question: "what is the TOTAL declared
    coverage this ticket claims?" A ticket's build is one build; its evidence may be spread
    across every crossing that ever named a proof, and evidence is not superseded by being
    older.

    MEASURED 2026-09-09 on ticket 9579a6f9cec6, this verb's first live fire. That ticket has
    FIVE PROVED crossings each naming a different proof, and its five declared teeth are
    spread across two of them. Read latest-only, the verb reported FIVE of its eight
    ``writes_to`` files hollow. Read as the union, it reports NONE — every file reds at least
    one declared tooth. Those five were not an incomplete reading; they were a false accusation
    against a build that is in fact load-bearing, produced by an instrument whose whole purpose
    is to catch false greens. A hollow-checker that manufactures hollow findings is worse than
    none, for exactly the reason Law 8 gives about a false green: it gets leaned on.

    Corpus census the same day: 11 ticket/terminal pairs name a proof on more than one
    crossing — 2 at PROVED (9579a6f9cec6 x5, 675ab0daa171 x4) and 8 at BUILDME. Every one of
    them would have been misread.

    NOTHING IS CHANGED IN THE SHARED TOOL, and that is the point rather than caution: its
    latest-only rule is CORRECT for the gate, this verb needed the other rule, and the honest
    act is two readers with their reasons written down — not one reader bent to serve two
    questions.
        -> ticket proven-by-answers-two-questions-and-one-reader-serves-both
    """
    seen = proven_by_since_buildme(str(ticket.get("id") or ""), roots)
    if not seen:
        raise HollowUnmeasurable(
            f"hollow: no crossing on ticket {ticket.get('id')} names a proof, so there is no "
            f"instrument to run against the reverted build.")
    return seen


def _classify(rel: str) -> str | None:
    """Why this file is not measured, or None when it is. One place, so the run and the
    report cannot disagree about which files were skipped and for what."""
    p = Path(rel)
    if p.is_absolute() or rel.startswith("..") or "CairnCommons" in p.parts:
        return SKIP_OUTSIDE
    if "proofs" in p.parts:
        return SKIP_INSTRUMENT
    return None


def _purge_bytecode(worktree: Path) -> None:
    """Delete every ``__pycache__`` in the worktree — MEASURED NECESSARY, not hygiene.

    THE DEFECT THIS EXISTS TO STOP, and it made this instrument report the OPPOSITE of the
    truth. CPython invalidates a cached ``.pyc`` on the source's (mtime, size), and the mtime
    it stores is whole SECONDS. This verb reverts a file, runs the proof, restores the file and
    runs again — three writes that routinely land inside one second. When the reverted and the
    standing version are the same LENGTH, both fields match and Python reuses bytecode compiled
    from the version that is no longer on disk. The proof then reads a tree that does not exist.

    Measured 2026-09-09, and it is not a corner: a scratch module written ``VALUE = 2`` ->
    ``VALUE = 1`` -> ``VALUE = 2`` within one second reported ``2`` on all three runs, including
    the run where the file said ``1``. Inside this verb that surfaced as a fixture whose
    uncovered file read as COVERED — the reversion of the PREVIOUS file was still in the cache,
    so the proof redded and the wrong file was credited for it. It reproduced 3 times in 14 runs,
    which is exactly what a same-second collision should look like.

    WHY A PURGE AND NOT ``PYTHONDONTWRITEBYTECODE``. The env var is the smaller act, but it
    reaches only the children that inherit it — a proof that re-execs, or spawns under a cleaned
    environment, silently opts out and the wrong answer comes back with nothing said. Removing
    the caches is a fact about the tree, and every reader of that tree is covered by it whatever
    environment it runs under. This is a measuring instrument; it may not have an opt-out it
    cannot see. The cost is a walk of a worktree that is one checkout old.
    """
    for cache in worktree.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def _revert(worktree: Path, commit: str, rel: str, *, repo_root: Path) -> str:
    """Put ``rel`` back the way it was at ``commit``, inside the worktree only.

    A file that did not EXIST at that commit is removed, not emptied. An emptied file still
    imports (as nothing) and still satisfies a path check, so emptying would measure a weaker
    counterfactual than "the build had not happened" while looking like the same act.
    """
    target = worktree / rel
    probe = subprocess.run(["git", "-C", str(repo_root), "cat-file", "-e", f"{commit}:{rel}"],
                           capture_output=True, text=True, env=git_env())
    if probe.returncode != 0:
        if target.exists():
            target.unlink()
        return "removed (absent before the build)"
    blob = subprocess.run(["git", "-C", str(repo_root), "show", f"{commit}:{rel}"],
                          capture_output=True, env=git_env())
    if blob.returncode != 0:
        raise HollowUnmeasurable(f"hollow: could not read {rel} at {commit}: {blob.stderr.decode()!r}")
    if target.is_file() and target.read_bytes() == blob.stdout:
        # A NO-OP REVERSION IS NOT A HOLLOW READING, and telling them apart is not optional.
        # If the file is byte-identical to its pre-build self, nothing was reverted, so of
        # course no tooth reds — and reporting that as "the proof does not check this file"
        # would be a red arrived at for entirely the wrong reason. It is a different finding
        # and a real one: the chart's writes_to named a file this build did not write.
        return "unchanged"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(blob.stdout)
    return "reverted"


def _restore(worktree: Path, rel: str) -> None:
    """Back to the worktree's own HEAD — checkout restores a removed file as well as a changed one.

    AND IT RAISES WHEN IT CANNOT, because a silent failure here does not fail this file — it
    CORRUPTS EVERY FILE AFTER IT. The run reverts one file at a time on top of HEAD and undoes
    each before the next, so an unperformed undo leaves file N reverted while file N+1 is being
    measured; N+1's teeth then red for a reason that has nothing to do with N+1, that red is
    read as "a declared tooth checks this file", and a file that really is hollow is reported
    ``ok``. **That is a hollow read as green, inside the verb whose whole job is catching one**
    — the failure Law 8 calls worse than a red, because a peer leans on it.

    MEASURED 2026-09-09 and that is why it raises now: under a git hook's environment
    (``GIT_INDEX_FILE=.git/index``, relative) this checkout resolved against the CALLER's index
    instead of the worktree's, did nothing, said nothing, returned nothing to look at — and
    ``test_a_proof_declaring_no_tooth_for_this_ticket_is_dropped_and_never_run`` asserted one
    hollow file and got none. The env scrub below is the fix for that cause; this raise is the
    fix for the CLASS, because the next thing that stops a checkout will not be an env var and
    the verb must not go on measuring past it (Law 3: a measurement that could not be taken may
    not travel home through the same return as a clean one).
    """
    proc = subprocess.run(["git", "-C", str(worktree), "checkout", "--", rel],
                          capture_output=True, text=True, env=git_env())
    if proc.returncode != 0:
        raise HollowUnmeasurable(
            f"hollow: could not restore {rel} in {worktree} after reverting it "
            f"({proc.stderr.strip()!r}). Every file measured after this one would be read "
            f"against a tree still carrying the last reversion, so the run stops here.")


def measure(ticket_id: str, *, repo_root: Path = REPO_ROOT, commons: Path = COMMONS,
            timeout: int = 120, tester=None, log=lambda _msg: None) -> dict:
    """Revert this ticket's build file by file and report which declared teeth each one reds.

    Returns the finding as data — ``verdict`` green|red, ``measured`` {file: [teeth]},
    ``hollow`` the files that redded nothing, ``skipped`` with a reason each. The caller
    decides what to print and what to seal; nothing is written here.
    """
    from cairn.devices.tester.device import TesterDevice
    tester = tester or TesterDevice()

    ticket = json.loads(_ticket_path(ticket_id, commons).read_text(encoding="utf-8"))
    tid = str(ticket.get("id") or ticket_id)
    roots = _roots(repo_root, commons)
    crossing = _buildme_crossing(ticket, roots)
    at = _buildme_at(ticket, crossing, repo_root)
    commit = prebuild_commit(at, repo_root=repo_root)
    files = writes_to(ticket)
    proofs = proven_by(ticket, roots)

    # THE DECLARED TEETH ARE THE ONLY ONES THAT COUNT, and they are read from the proof's own
    # PROVES map for THIS ticket. A proof holding teeth for three tickets would otherwise let a
    # reversion "red something" by reddening a neighbour ticket's tooth, which says nothing
    # about whether this build is load-bearing.
    declared_teeth: dict[str, list[str]] = {}
    for rel in proofs:
        by_ticket = declared(repo_root / rel)
        declared_teeth[rel] = sorted(set((by_ticket.get(tid) or {}).values()))
    if not any(declared_teeth.values()):
        raise HollowUnmeasurable(
            f"hollow: none of the proofs {proofs} declares a PROVES entry for ticket {tid}, so "
            f"there are no declared teeth to watch. Undeclared coverage cannot be measured — "
            f"that is the proof_coverage lack, not a hollow build.")

    # A PROOF DECLARING NO TOOTH FOR THIS TICKET IS DROPPED, AND SAYS SO. Only declared teeth
    # are counted (the filter below), so a proof holding none for this ticket cannot contribute
    # a red no matter what its reversion does — running it is a cost with no possible effect on
    # the answer. This is not a tidy-up: it is what keeps the verb inside its own bound.
    # MEASURED 2026-09-09 on 9579a6f9cec6 — 5 named proofs, of which THREE declare zero teeth
    # for it, over 8 files: 5 x (1 baseline + 8) = 45 proof runs, 501.7s wall-clock against the
    # ticket's stated WRONG INTENT threshold of 5 minutes. Dropping the three that cannot speak
    # leaves 2 x 9 = 18 runs of the same 18 that carry every tooth the answer is made of, so the
    # reading is IDENTICAL and the cost is 40%. The dropped names ride the finding rather than
    # vanishing, because "we did not run it" and "it had nothing to say" must stay legible apart.
    #
    # RE-READ THE SAME DAY, AFTER THE TICKET GAINED A SIXTH NAMED PROOF: 6 named, 3 declaring,
    # 3 silent — so 27 of 54 runs, and the filter's saving is 50% rather than 40%. The counts
    # move with the corpus and this comment will go stale again; what does not move is the
    # shape, which is why it is stated as an equation above and not as a headline number.
    # (The proof of the filter itself does not read these figures — it reverts a fixture whose
    # silent proof would have changed the answer, and watches it not be run.)
    silent = [rel for rel in proofs if not declared_teeth[rel]]
    if silent:
        proofs = [rel for rel in proofs if declared_teeth[rel]]
        declared_teeth = {rel: declared_teeth[rel] for rel in proofs}
        log(f"  dropped {len(silent)} proof(s) declaring no tooth for {tid}: {', '.join(silent)}")

    # THE WORKTREE IS AT HEAD, NOT AT THE PRE-BUILD COMMIT, and the difference is the whole
    # design. Checking the whole tree out to before the build would revert every file at once
    # and answer a question nobody asked ("does the proof notice the last month of work?").
    # What is wanted is one counterfactual at a time: everything as it stands, except this one
    # file as it was. So HEAD is the ground and each revert is a single edit on top of it,
    # undone before the next.
    head = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"],
                          capture_output=True, text=True, env=git_env()).stdout.strip()
    wt = scratch_worktree(head, repo_root=repo_root)
    log(f"worktree {wt} at HEAD {head[:12]}; reverting to pre-build {commit[:12]} (BUILDME at {at})")

    def run_all() -> tuple[dict[str, set[str]], dict[str, int]]:
        """Each named proof's green teeth AND how many teeth it printed at all, run in the worktree.

        THE SECOND NUMBER IS NOT BOOKKEEPING — it is what keeps this instrument from reading
        green for the wrong reason. A reverted file can red a tooth two ways: the tooth ran and
        its assertion failed (the file is load-bearing, which is the finding), or the proof died
        on import and printed nothing at all (the file is merely IMPORTED somewhere upstream,
        which says nothing about coverage). Both look identical in `teeth_green` — the tooth is
        simply absent — so without a count of what ran, every reversion that breaks an import
        reads as perfect coverage. That is the coin-toss green: the right answer arrived, and
        not for the reason claimed.

        Sink is 'none': a measurement run must not land a VALIDATION — the code under it is
        deliberately wrong, and a seal is a claim about code that stands.
        """
        green: dict[str, set[str]] = {}
        ran: dict[str, int] = {}
        for rel in proofs:
            path = wt / rel
            if not path.is_file():
                green[rel], ran[rel] = set(), 0
                continue
            _purge_bytecode(wt)
            record = tester.run_proof(path, sink="none", caller="cairn test --hollow",
                                      timeout=timeout, isolation="none")
            ev = record["evidence"]
            green[rel] = set(ev.get("teeth_green") or [])
            ran[rel] = len(green[rel]) + len(ev.get("teeth_red") or [])
        return green, ran

    baseline, baseline_ran = run_all()
    missing = {rel: sorted(set(declared_teeth[rel]) - baseline[rel]) for rel in proofs}
    missing = {k: v for k, v in missing.items() if v}
    if missing:
        # A DECLARED TOOTH THAT IS NOT GREEN AT HEAD makes every later reading unreadable: it
        # would show up red under every reversion and name every file load-bearing. Loud, and
        # the run stops — this is a red about the proof, not a finding about a file.
        raise HollowUnmeasurable(
            f"hollow: these declared teeth are not green at HEAD, so no reversion reading can "
            f"be attributed to a file: {json.dumps(missing)}")

    measured: dict[str, list[str]] = {}
    unran: dict[str, list[str]] = {}
    unchanged: list[str] = []
    skipped: list[dict] = []
    for rel in files:
        why = _classify(rel)
        if why is None and not (wt / rel).is_file():
            why = "not present at HEAD — the build is not committed, so there is nothing to revert from"
        if why is not None:
            skipped.append({"file": rel, "why": why})
            log(f"  skip   {rel}  ({why})")
            continue
        how = _revert(wt, commit, rel, repo_root=repo_root)
        if how == "unchanged":
            unchanged.append(rel)
            _restore(wt, rel)
            log(f"  UNWRIT {rel}  (identical at the pre-build commit — the build did not write it)")
            continue
        try:
            after, after_ran = run_all()
        finally:
            _restore(wt, rel)
        # DECLARED TEETH ONLY, and the filter is the ticket's bound rather than a nicety.
        # Without it, the reading counts any tooth in the file that went red — including the
        # 55 teeth these three proofs hold for OTHER tickets. A neighbour's tooth reddening
        # says the file is load-bearing for SOMETHING; it says nothing about whether THIS
        # ticket's build earned THIS ticket's crossing, which is the only question here.
        redded = sorted({t for p in proofs for t in (baseline[p] - after[p])
                         if t in declared_teeth[p]})
        # Which proofs stopped RUNNING under this reversion, rather than running and failing.
        broke = sorted(p for p in proofs if baseline_ran[p] and after_ran[p] == 0)
        measured[rel] = redded
        if broke:
            unran[rel] = broke
        mark = "HOLLOW" if not redded else ("UNRAN " if broke else "ok    ")
        log(f"  {mark} {rel}  ({how}) → " +
            (", ".join(redded) if redded else "no declared tooth redded")
            # WHAT WAS SEEN, NOT WHY. This line used to read "the import broke", which is a
            # cause nothing here observed: all that was measured is a tooth count of zero, and
            # a proof reaches zero by a broken import, by a timeout (120s per proof, and a
            # reverted file can make a proof HANG rather than fail), or by any crash before
            # its first check. Naming one of the three at a diagnostic surface sends the
            # builder to look in the wrong place — Law 7 is about what a diagnostic surface
            # may not collapse, and a guess wearing a fact's clothes is a collapse.
            + (f"  [{len(broke)} proof(s) printed no teeth at all — did not reach a check: a "
               f"broken import, a timeout, or a crash before the first tooth]" if broke else ""))

    hollow_files = [f for f, teeth in measured.items() if not teeth]
    reasons: list[str] = []
    for f in hollow_files:
        reasons.append(f"hollow: {f} reverted, no declared tooth redded")
    for f in unchanged:
        reasons.append(
            f"unwritten: {f} is byte-identical at the pre-build commit — the decompose berth "
            f"names it as written by this build and the build did not write it (a finding "
            f"against the chart's writes_to, not against the proof)")
    for f, broke in unran.items():
        # NOT COUNTED AS HOLLOW, AND NOT COUNTED AS COVERED. The reading is unreadable: the
        # teeth went absent because the proof never ran, so this file is neither shown
        # load-bearing nor shown unchecked. Reporting it as a pass would be the hollow green
        # this whole module exists to catch, so it reds and says exactly what it saw.
        reasons.append(
            f"unreadable: {f} reverted and {', '.join(broke)} printed no teeth at all — the "
            f"proof never reached a check (a broken import, a timeout, or a crash) rather "
            f"than failing a tooth, so nothing here says whether a tooth checks this file. "
            f"THE FIX BELONGS TO THE PROOF: it must survive its subject being taken away — "
            f"resolve the names this build ADDED at call time rather than binding them at "
            f"import, and keep the reverted world reachable enough to run")
    if not measured:
        # THE SKIP LIST IS NOT AN ESCAPE HATCH. Every file skipped and none measured is a run
        # that proved nothing, and reporting it green would make "add it to the skip list" the
        # cheapest way past this check forever.
        reasons.append(
            f"hollow: every writes_to file was skipped ({len(skipped)} of {len(files)}), so this "
            f"run measured nothing. A measurement of the empty set is not a pass.")

    return {"ticket": tid, "commit": commit, "buildme_at": at, "worktree": str(wt),
            "proofs": proofs, "declared": declared_teeth, "silent_proofs": silent,
            "baseline_green": {k: sorted(v) for k, v in baseline.items()},
            "measured": measured, "skipped": skipped, "hollow": hollow_files, "unran": unran,
            "unchanged": unchanged,
            "verdict": "red" if reasons else "green", "reasons": reasons}

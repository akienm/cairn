"""proof_coverage — does the proof this ticket names actually prove THIS ticket?

Charter + why: cairn/tools/proof_coverage/intention+why.json
Ticket:        CairnCommons/tickets/feeb4c786b14-proof-coverage-is-declared-and-a-proveme-ticket-without-it-reads-red.json

THE MEASUREMENT THAT BUILT THIS (2026-09-07). Nineteen tickets sit at PROVEME:waiting.
Twelve name a proof carrying a green seal; seven name none. Three of the twelve — sleep
cycle token, idle detection, token rotation — name ``cairn/devices/cairn/proofs/test_trouble_panel.py``,
a file containing zero mentions of sleep, idle, rotation or token. A fourth, post-build
reflection, names ``test_codemother.py``, which never mentions reflection. So a green seal
on the named proof said NOTHING about whether the ticket was proven, and nothing on disk
could see it: four of twelve were the hollow green Law 8 is written against, wearing a
real seal.

THE FIX IS A JOIN, NOT A JUDGEMENT. A proof declares, at module level, which ticket
clauses each of its teeth covers::

    PROVES = {"feeb4c786b14": {"1": "test_a_sealed_proof_records_every_tooth_it_printed",
                               "2": "test_an_undeclared_clause_is_named"}}

and the seal records which teeth actually printed green. Coverage is then the intersection
of three things already on disk — the ticket's clauses, the proof's declaration, the seal's
teeth — and every lack is a NAMED clause rather than a feeling. Nothing here judges whether
a tooth is a GOOD tooth; that is the caster's job at /sorted, and a sieve that tried would
be a sieve with an opinion (memory: sieves-measure-not-judge).

WHY THE DECLARATION LIVES IN THE PROOF AND THE CLAUSES LIVE IN THE TICKET. Both halves have
exactly one owner and neither can be edited to flatter the other in the same act: moving a
clause is a commons edit, moving a tooth is a code edit, and the seal that binds them is
minted by the tester and by nothing else. A declaration kept in the ticket alone would let a
ticket claim its own coverage; a declaration kept in the proof alone would let a proof
invent the clauses it covers.

IT READS. IT DOES NOT RUN ANYTHING, and it never imports a proof — ``PROVES`` is read out
of the AST. Importing a proof to read one dict would execute the module, which is the
instrument seeding the tree it reads (the same defect the tester's instance seal exists to
remove).
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from cairn.tools.system_word import fold

# ── the vocabulary of a printed tooth ────────────────────────────────────────────────
# MEASURED, NOT ASSUMED (2026-09-07). The ticket predicted two proof styles; the corpus
# has at least five. Across 189 proof files: 79 print both PASS and green, 38 print ok,
# 18 drive pytest, 15 print PASS alone, 14 print PASS+green+pytest, 7 print green alone,
# and 17 matched none of those four patterns — which turned out to be a fifth marker,
# ``GREEN``, in build_inspector's own proofs.
#
# So the extractor does NOT enumerate printing styles. It looks for a MARKER WORD beside
# a ``test_``-shaped name, which is the one thing every style in the corpus shares and the
# one thing a new style is overwhelmingly likely to share too. Enumerating the five would
# have been a hand roster beside the thing it lists — the exact shape that let sixteen
# named teeth go stale in test_trouble.py and print "16/16 green" with two teeth unrun.
GREEN_MARKERS = frozenset({"ok", "pass", "passed", "green", "good"})
RED_MARKERS = frozenset({"fail", "failed", "red", "error", "errored", "broken"})

# Marker first (``  ok   test_x``, ``  PASS  test_x``, ``  GREEN  test_x``) or marker last
# (pytest -v's ``path::test_x PASSED``). Both are anchored on a ``test_`` name so a marker
# word appearing in prose cannot mint a tooth.
_MARKER_FIRST = re.compile(r"^\s*([A-Za-z]+)[\s:]+(test_[A-Za-z0-9_]+)")
_MARKER_LAST = re.compile(r"(test_[A-Za-z0-9_]+)\s+([A-Za-z]+)\s*$")

# AND THE THIRD SHAPE, WHICH IS HALF THE CORPUS'S TEETH: a marker beside a PROSE LABEL.
# The two patterns above anchor on a ``test_`` name, and the comment above says why — a
# marker word in prose must not mint a tooth. That reasoning is right and it was applied
# to only half the problem. This ticket's own HOW says so in as many words: "a tooth name
# is the ok() label for ok-style proofs (18 in the corpus) or the test_ function name for
# pytest-style proofs (152)". The ok()-style half was specified and never built.
#
# MEASURED 2026-09-09, which is how it surfaced: of 131 green seals in the corpus, 31
# recorded ZERO teeth. Seventeen of those PRINT their teeth in plain sight and the parser
# could not see them — ``  ok the backdate refusal wrote no slate``, ``PASS: status returns
# 0 and reads liveness``, ``  PASS  a unified line is the answer``. A seal that records no
# teeth cannot serve as coverage evidence for anything, because the sieve reds when a
# DECLARED tooth is absent from teeth_green and every declared tooth is absent from an
# empty list. So seventeen proofs were structurally unable to prove any ticket, while
# reading green. (The other fourteen print no per-tooth line at all — a different gap,
# recorded on the ticket, not fixed by this regex: there is nothing there to parse.)
#
# THE ANCHOR THAT REPLACES ``test_``, because the prose case cannot have that one: the
# marker must open the line AND be punctuated as a report rather than a sentence — either
# the line is INDENTED (every ok()-style helper in the corpus indents its per-tooth lines)
# or the marker is followed by a COLON (``PASS: ...``). A narrative line a proof prints at
# the left margin — ``ok so the next thing`` — matches neither and mints nothing. This is
# the same instinct as the ``test_`` anchor, spent on the shape that actually occurs.
_MARKER_LABEL = re.compile(
    r"^(?:[ \t]+([A-Za-z]+)[ \t]+|([A-Za-z]+)[ \t]*:[ \t]+)(\S.*?)[ \t]*$")

# A clause key is the number inside a ``(N)`` marker in the DONE-when text.
_CLAUSE_MARK = re.compile(r"\((\d{1,2})\)")
# ...or the letter inside an ``(x)`` marker, for the falsifiers that enumerate with letters.
# Read ONLY under the run test below, because a bare letter in parentheses is far more often
# prose than a clause — see ``_lettered_run``.
_LETTER_MARK = re.compile(r"\(([a-z])\)")
# Everything from WRONG INTENT onward describes what would make the ticket the WRONG THING
# to have built — a disposition, not a condition a tooth can go green on. Cutting it is
# what stops the sieve demanding a tooth for "this was a bad idea".
_WRONG_INTENT = re.compile(r"WRONG[\s-]?INTENT", re.I)

# One clause, for a falsifier that names no numbered clauses. Not a special case anywhere
# downstream: it is a clause key like any other, so a flat falsifier needs exactly one
# declared tooth and gets exactly one named lack when it has none.
WHOLE = "all"


def teeth_printed(stdout: str) -> dict:
    """Split a proof's stdout into the teeth that printed green and the teeth that printed red.

    A tooth named on a red-marked line is red even if it also appears green somewhere —
    a proof that prints a name twice with two verdicts has not proved that tooth, and
    resolving the ambiguity toward green is precisely the direction a hollow build wants.

    THE FULL STDOUT, NEVER THE TAIL. ``evidence.stdout_tail`` is twenty lines by design
    (a diagnostic surface, Law 7) and a proof with forty teeth would silently report
    twenty. This takes the whole stream, before any tailing.
    """
    green: list[str] = []
    red: list[str] = []
    for line in (stdout or "").splitlines():
        # ORDER MATTERS AND IT IS NOT ARBITRARY: the two test_-anchored patterns run first,
        # so ``  ok   test_x`` records the IDENTIFIER and never the sentence that follows it.
        # The label pattern is the fallback for lines that name no test_ function at all.
        for pattern, marker_group, name_group in ((_MARKER_FIRST, 1, 2), (_MARKER_LAST, 2, 1),
                                                  (_MARKER_LABEL, None, 3)):
            m = pattern.search(line)
            if not m:
                continue
            # _MARKER_LABEL carries its marker in whichever of its two alternatives fired —
            # indented form or colon form — so the group is resolved rather than fixed.
            marker = fold(m.group(marker_group) if marker_group is not None
                          else (m.group(1) or m.group(2)))
            name = m.group(name_group)
            if marker in RED_MARKERS:
                red.append(name)
            elif marker in GREEN_MARKERS:
                green.append(name)
            break
    red_set = set(red)
    # dict.fromkeys: dedupe while keeping the order the proof printed them in, so a reader
    # comparing two seals sees a stable list rather than a set's arbitrary order.
    return {"green": [t for t in dict.fromkeys(green) if t not in red_set],
            "red": list(dict.fromkeys(red))}


def clauses(ticket: dict) -> list[str]:
    """The clause keys a proof must cover for this ticket, read off its falsifier.

    Three shapes, all present in the live corpus: a dict falsifier (all 19 at PROVEME on
    2026-09-07) whose ``proves_red`` holds the DONE-when text; a plain string falsifier
    (the older shape, still the majority of PROVED tickets); and either of those with no
    ``(N)`` markers at all, which is ONE clause covering the whole thing.

    The clauses come from ``proves_red`` rather than ``proves_green`` because ``proves_red``
    IS the DONE-when list — measured: 15d6a0ef9c11 numbers four clauses in proves_red and
    none in proves_green, and 61416fbb8013's proves_green numbers ``(1)(2)(1)(3)(1)``,
    which is prose reusing the digits, not a clause list.
    """
    fal = ticket.get("falsifier")
    if isinstance(fal, dict):
        text = fal.get("proves_red")
        if isinstance(text, dict):
            # A nested proves_red names its own clauses; its keys ARE the clause list.
            return [str(k) for k in text]
        text = text or ""
    else:
        text = fal or ""
    if not isinstance(text, str) or not text.strip():
        return []
    head = _WRONG_INTENT.split(text)[0]
    found = list(dict.fromkeys(_CLAUSE_MARK.findall(head)))
    if found:
        return found
    lettered = list(dict.fromkeys(_LETTER_MARK.findall(head)))
    if _lettered_run(lettered):
        return lettered
    return [WHOLE]


def _lettered_run(letters: list[str]) -> bool:
    """Is this letter list an ENUMERATION, or is it prose that happens to parenthesise a letter?

    ADDED 2026-09-10, ticket 95e3b9911dd0 — a bug that voyage uncovered in its own crossing and
    therefore fixed. Its falsifier numbers four DONE-when clauses (a) through (d); ``clauses()``
    read digits only, returned the one-clause fallback ``["all"]``, and the clearance gate then
    demanded a single declared tooth for a four-clause falsifier. Three of its four clauses
    needed no tooth at all. That is coverage credited for looking at less, which is the hollow
    green Law 8 exists to refuse.

    WHY THE RUN TEST AND NOT A BARE REGEX. Measured over all 272 tickets in the commons: 107
    falsifiers mark clauses with digits, 146 mark none at all, 15 mark only letters, and 4 mark
    both. Reading every ``(x)`` as a clause manufactures phantom clauses on five of those,
    because a lone parenthesised letter is usually a REFERENCE:

        73c9d3093973  "the substance of the sibling ticket's clause (c)"
        a48f95c51a41  "without half (b) this is not a distinction but a breach"
        b96f8e602da0  "filed edge (b) naming an unwired host ... must also red db_domain's edge (e)"
        feeb4c786b14  "run over the live corpus before (d), it reds all 19 PROVEME tickets"

    Demanding a tooth for "edge (e)" is not a stricter gate, it is a broken one — and a gate that
    reds for a reason nobody can satisfy teaches a caller to look for the exemption, which is how
    a real check gets plastered over. So a letter list counts only when it looks like a list: two
    or more markers, starting at ``a``, consecutive, no gaps. Every one of the five prose cases
    fails it (['c'], ['b'], ['b','e'], ['d'], and the mixed ones never reach here because digits
    win); all fifteen genuine enumerations pass it.

    DIGITS STILL WIN OUTRIGHT when both appear, which is why this is reached only after the digit
    findall comes back empty. On ``db059208bbd9`` the digits (1)-(4) are the clause list and the
    letters (a)-(c) enumerate teeth WITHIN one clause — a nesting, not a competition, and the
    outer level is the one a gate asks about.

    BLAST RADIUS, MEASURED RATHER THAN ASSUMED: 14 tickets change from ``["all"]`` to a real
    clause list. Eleven are already PROVED, one SUPERSEDED and one RETIRED, so they will not
    cross again; exactly two are in flight — 95e3b9911dd0 (this voyage) and d2ecdb867bc9, which
    is still at TICKETME and has not built. Nothing under way is blocked by the tightening.
    """
    if len(letters) < 2:
        return False
    return letters == [chr(ord("a") + i) for i in range(len(letters))]


def declared(proof_path) -> dict:
    """Read a proof's module-level ``PROVES`` without importing it.

    Returns ``{ticket_id: {clause: tooth_name}}``, or ``{}`` when the proof declares
    nothing — which is a lack the caller names, never an exemption granted here.
    """
    path = Path(proof_path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "PROVES" for t in node.targets):
            continue
        try:
            value = ast.literal_eval(node.value)
        except ValueError:
            return {}
        if not isinstance(value, dict):
            return {}
        out = {}
        for tid, mapping in value.items():
            if isinstance(mapping, dict):
                out[str(tid)] = {str(c): str(t) for c, t in mapping.items()}
        return out
    return {}


def lacks(ticket: dict, *, repo_root: Path, seal_reader=None, roots=None) -> list[dict]:
    """Every reason this ticket is not covered by the proof it names — one entry per lack.

    EVERY lack, in one pass, never the first one found: a caller who fixes what he is told
    and re-runs into a second refusal learns to distrust the report, and a report that is
    distrusted is a report nobody acts on. (Same reasoning the /sorted door carries.)

    An empty list means covered: the named proof exists, declares this ticket, declares a
    tooth for every clause, every declared tooth printed green in the seal, and the seal's
    fingerprint still matches the working tree.

    ``seal_reader`` is injectable so a proof can drive this over a fixture with no tester
    and no seal store — the default reaches the real store through cairn.tools.base.validation,
    which is the read-side door for seals (tools may import devices; devices may not import
    each other).

    ``roots`` is the WORLD THE CROSSINGS ARE DERIVED FROM — ``{"repo": ..., "commons": ...}``,
    defaulting to the live three-root table. It exists for the same reason ``seal_reader``
    does, and the reason is now sharper than injectability: since the crossings stopped
    being an array on the ticket (ruling 2026-09-10-crossings-are-derived-never-written)
    a caller holding a ticket dict no longer carries its own evidence. ``repo_root`` says
    where the PROOFS are read from; ``roots`` says where the JOURNALS are. A fixture that
    passed only the first would be checked against the live corpus's journals and derive
    nothing for its own ticket — which is exactly what the fixtures did, and it reds
    thirteen teeth rather than passing quietly, because absence of a crossing IS a lack.

    THE PROOFS ARE NEVER TAKEN FROM THE CALLER, and that was tried and measured wrong on
    2026-09-10. The clearance gate holds the crossing's own ``proven_by`` and it is tempting
    to hand it here — but the gate's coverage rung deliberately reads a DIFFERENT set from
    rule 2: rule 2 asks whether the proofs THIS crossing names stand, the rung asks whether
    the proofs THE RECORD names cover the boat. Collapsing them lets a fresh ``proven_by=``
    walk a stale record straight past both, which is the attack
    ``test_a_seal_whose_FINGERPRINT_HAS_MOVED_is_refused_at_PROVED`` exists to hold shut. It
    went green on the collapsed reader. So the reading stays derived, and a caller who wants
    a different world says so with ``roots`` — which is where the evidence is, never what it
    says.
    """
    if seal_reader is None:
        seal_reader = _latest_seal
    tid = str(ticket.get("id") or "")
    want = clauses(ticket)
    if not want:
        return [_lack(tid, "falsifier_has_clauses",
                      "the ticket's falsifier names at least one DONE-when clause",
                      "the falsifier is empty or unreadable, so there is nothing a proof "
                      "could be checked against")]

    named = _proven_by(ticket, roots)
    if not named:
        # TWO LACKS, NOT ONE, and the split is a measurement rather than a courtesy.
        # Measured 2026-09-07 over the live corpus: of 230 tickets at PROVEME or beyond,
        # 215 name no proof — but 196 of those carry NO crossings array at all, because
        # they were resolved before the crossing record existed, while the rest carry
        # crossings that simply never named one. Both are red (Law 9; a proof nobody can
        # find is a proof nobody checked), and collapsing them into one line would bury
        # nineteen actionable tickets under two hundred archaeological ones. Distinguishing
        # them is not an exemption: neither goes green, and the counts stay exact.
        # BOUND AT CALL TIME, NEVER AT IMPORT — and that is a measured requirement, not a
        # style choice. ``cairn/tools/base/crossings.py`` did not exist before ticket
        # d2ecdb867bc9, and the hollow reader proves that build load-bearing by taking the
        # file away and re-running the proofs beside it. Those proofs reach this module for
        # ``print_teeth_main`` — which has nothing to do with crossings — so a module-level
        # import turned the removal into a crash in the RUNNER: the proof printed no teeth at
        # all and hollow recorded UNRAN instead of a redded tooth. Measured 2026-09-10.
        from cairn.tools.base.crossings import has_crossings

        no_record = not has_crossings(tid, roots)
        return [_lack(tid,
                      "crossing_record_absent" if no_record else "proof_named",
                      "the ticket's latest crossing names the proof that proves it",
                      "the ticket carries no crossings at all — it reached proven-space "
                      "before the crossing record existed, so what proved it was never "
                      "written down" if no_record else
                      "the ticket has crossings and none carries proven_by — it claims "
                      "proven-space with no proof named at all")]

    if fold(str(ticket.get("node_class") or "")) == "concept-piece":
        return _concept_lacks(ticket, tid, named[0], repo_root, seal_reader)

    found = []
    # A CLAUSE MAY BE PROVED SOMEWHERE ELSE, and the crossing may say so. Measured on
    # 9579a6f9cec6 (2026-09-07): its six clauses are served by teeth in THREE proofs —
    # trouble's own, tools/base's fixture-device raise, and the panel probe — because the
    # ticket's subject is a seam between components and a seam has ends in more than one
    # place. Reading only one proof would have forced a choice between naming a proof that
    # covers a third of the ticket and inlining other components' teeth into trouble's
    # proof, which is the tighter coupling the ticket exists to remove. So `proven_by` is
    # read as one-or-many, every named proof is checked on its own terms (its own
    # declaration, its own seal, its own fingerprint), and a clause is covered if ANY of
    # them declares a green tooth for it. Nothing is relaxed: each proof still has to
    # exist, declare this ticket, be sealed, and be current.
    declaration, per_proof = {}, {}
    for one in named:
        proof_path = (repo_root / one) if not Path(one).is_absolute() else Path(one)
        if not proof_path.exists():
            found.append(_lack(tid, "proof_on_disk", f"{one} exists",
                               "the named proof is not on disk — the seal it claims cannot be "
                               "about anything", proof=one))
            continue
        mine = declared(proof_path).get(tid, {})
        if not mine:
            found.append(_lack(tid, "proof_declares_the_ticket",
                               f"{proof_path.name} carries a PROVES entry for this ticket",
                               "the proof declares nothing for this ticket, so a green seal on "
                               "it says nothing about whether THIS ticket is proven — the exact "
                               "shape measured on four of twelve tickets, 2026-09-07",
                               proof=one))
        seal = seal_reader(proof_path, artifact=False)
        if seal is None:
            found.append(_lack(tid, "seal_exists", f"{proof_path.name} carries a validation seal",
                               "the named proof has never been sealed", proof=one))
        else:
            stale = _fingerprint_stale(proof_path, seal)
            if stale:
                found.append(_lack(tid, "seal_fingerprint_current",
                                   f"the seal for {proof_path.name} matches the working tree",
                                   stale, proof=one))
        green = set((((seal or {}).get("evidence") or {}).get("teeth_green")) or [])
        per_proof[one] = (proof_path, mine, green)
        for clause, tooth in mine.items():
            # FIRST DECLARER WINS, and a second one is not a conflict to adjudicate: two
            # proofs both claiming a clause is two teeth for it, which is more evidence,
            # not less. What matters is that at least one is green — checked below.
            declaration.setdefault(clause, []).append(one)

    where = ", ".join(Path(p).name for p in named)
    for clause in want:
        holders = declaration.get(clause) or []
        if not holders:
            found.append(_lack(tid, "clause_declared",
                               f"clause ({clause}) has a declared tooth in {where}",
                               f"clause ({clause}) is undeclared — no tooth in the named "
                               f"proof{'s' if len(named) > 1 else ''} claims to cover it",
                               clause=clause, proof=named[0], proofs=named))
            continue
        greens = [(p, per_proof[p][1][clause]) for p in holders
                  if per_proof[p][1][clause] in per_proof[p][2]]
        if not greens:
            reds = [(p, per_proof[p][1][clause]) for p in holders]
            found.append(_lack(tid, "declared_tooth_green",
                               f"a tooth declared for clause ({clause}) printed green in its "
                               f"own seal",
                               f"clause ({clause}) declares "
                               + "; ".join(f"{tooth} in {Path(p).name}" for p, tooth in reds)
                               + " — none is among the teeth its seal recorded green",
                               clause=clause, tooth=reds[0][1], proof=reds[0][0]))
    # THE BINDING SIEVE RIDES THE SAME LIST, so PROVEME reds through the path that already
    # exists — one report, every lack, and nothing new for a gate to remember to call.
    found.extend(proof_binds_its_subject_at_call_time(ticket, repo_root=repo_root, roots=roots,
                                                      named=named))
    return found


# ── the binding sieve: does the proof reach its subject at call time, or at import? ─────
# THE THIRD TIME IS A SIEVE (ticket c5b6b128a376, 2026-09-14). Three proofs in five days
# bound a name their own build ADDED at module level — crossings.py from this file's own
# proofs (2026-09-10), artifact.py from test_artifact_door.py (a38204e, 2026-09-13), a name
# in citation.py two hops behind test_exemption_set.py (e1dcc6e, 2026-09-14). Each was found
# the same way: the hollow reading reverted the file, the proof crashed in its import block
# before printing a single tooth, hollow recorded UNRAN with a paragraph saying "resolve the
# names this build ADDED at call time", and a hand fixed it two to five minutes later. The
# paragraph did not stop the second or the third. A rule that matters is physics (Law 4),
# and the physics is the same join this module already makes — the ticket's proofs and the
# ticket's BUILDME crossing — plus two things hollow already reads: the pre-build commit and
# the decompose berth's ``writes_to``.
#
# WHAT IT READS, AND WHAT IT DOES NOT. Module-level ``import`` / ``from … import`` statements
# — the direct children of ``Module.body``, nothing nested. An import inside ``def``, inside
# ``try``, inside ``if`` is by construction NOT the defect: those are exactly the shapes the
# three hand fixes took (a call-time import, a try/except with a stub). The walk is
# transitive through every module it can resolve to a file under the repo (the script-dir
# rule for a proof run as a script, the repo root for ``cairn.*`` and ``skills.*``, the
# package for a relative import), because the third instance was two hops from the proof and
# a one-hop walk would have read it green. It resolves a name only against what is actually
# on disk: a ``from X import y`` where ``X/y.py`` exists binds a FILE, otherwise it binds a
# NAME in X's file. A star import binds every added name in the module it names.
#
# THE ADDED SET IS BOUNDED TO WHAT HOLLOW REVERTS — the berth's ``writes_to`` minus the files
# hollow's ``_classify`` skips (under ``proofs/``, records, outside the repo). A helper under
# ``proofs/fixtures/`` is added by the build too, but hollow never takes it away, so binding
# it at import cannot make a proof UNRAN; flagging it would be a sieve with a stricter
# opinion than the instrument it is the front door for. The walk still RECURSES through such
# a helper, because the helper may itself bind an added non-proof file at module level.
#
# WHAT IT CANNOT SEE, said here rather than discovered: a loader call (``_load(path)``,
# ``importlib``), a module-level constant computed from the subject, a fixture that binds at
# collection. Those stay hollow's, and the WATCHME on the ticket measures this sieve AGAINST
# hollow — one UNRAN it did not predict moves the instrument into hollow as a pre-flight.
#
# IT RESOLVES ITS OWN INPUTS AT CALL TIME. crossings and chain are bound inside the function,
# for the reason written at the has_crossings site above; this sieve reds the shape, so the
# sieve committing it would be the self-referential UNRAN and the ticket's own gate would
# refuse the ticket that built it.

_GIT_LOCATION_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX",
                      "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES")


def _git(repo_root: Path, *args: str) -> str | None:
    """stdout of one git command against ``repo_root``, or None when git says no. The seven
    location variables are stripped so a pre-commit hook's ``GIT_DIR`` cannot point the read
    at the wrong repository — the same list the tester's scratch module strips, kept here by
    value because a tool may not import a device."""
    import os
    import subprocess
    env = {k: v for k, v in os.environ.items() if k not in _GIT_LOCATION_VARS}
    try:
        got = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True,
                             text=True, env=env, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if got.returncode != 0:
        return None
    return got.stdout


def _prebuild_commit(at: str, *, repo_root: Path) -> str | None:
    """The last commit at or before the BUILDME crossing's ``at`` — the world the build was
    added to. Two lines, the same two hollow runs (``rev-list -1 --before``), so the two
    instruments diff against one commit by construction. None when git cannot say; the sieve
    is then silent and hollow's mouth reds the unmeasurable case in its own words."""
    if not (Path(repo_root) / ".git").exists():
        return None  # not a repository (a fixture world): nothing to diff against
    out = _git(repo_root, "rev-list", "-1", f"--before={at}", "HEAD")
    return (out or "").strip() or None


def _writes_to(ticket: dict, berths_root=None) -> list[str]:
    """The decompose berth's ``writes_to``, deduped, or [] when no berth claims the ticket.
    Empty is not a lack HERE: hollow already reds a ticket with no berth in its own words,
    and a second mouth for the same absence is how a reader learns to ignore both."""
    from cairn.tools.chain.chain import chain_for_ticket
    tid = str(ticket.get("id") or "")
    if not tid:
        return []
    berth = chain_for_ticket(tid, berths_root=berths_root).get("decompose")
    if not berth:
        return []
    try:
        packet = json.loads(Path(berth).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out: list[str] = []
    for piece in packet.get("sub_problems") or []:
        for f in piece.get("writes_to") or []:
            if str(f) not in out:
                out.append(str(f))
    return out


def _hollow_reverts(rel: str) -> bool:
    """Mirror of hollow's ``_classify`` returning True where hollow measures the file: not
    outside the repo, not an instrument, not a record."""
    p = Path(rel)
    if p.is_absolute() or rel.startswith("..") or "CairnCommons" in p.parts:
        return False
    if "proofs" in p.parts:
        return False
    if {"validations"} & set(p.parts) or p.name in {"history.json", "state.json"}:
        return False
    return True


def _top_level_names(source: str) -> set[str]:
    """The names a module binds at its top level: def, class, assignment targets, and what
    its own module-level imports bind. Unparseable reads as no names."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        out.add(n.id)
        elif isinstance(node, ast.Import):
            for a in node.names:
                out.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name != "*":
                    out.add(a.asname or a.name)
    return out


def _added_by_the_build(pre: str, writes_to: list[str], *, repo_root: Path):
    """What the build added among the files hollow would revert: the files absent at the
    pre-build commit, and for each file that existed, the top-level names its working copy
    binds that the pre-build version did not."""
    files: set[str] = set()
    names: dict[str, set[str]] = {}
    for rel in writes_to:
        if not rel.endswith(".py") or not _hollow_reverts(rel):
            continue
        now = repo_root / rel
        if not now.is_file():
            continue
        before = _git(repo_root, "show", f"{pre}:{rel}")
        if before is None:
            files.add(rel)
            continue
        try:
            current = now.read_text(encoding="utf-8")
        except OSError:
            continue
        added = _top_level_names(current) - _top_level_names(before)
        if added:
            names[rel] = added
    return files, names


def _rel_to(path: Path, repo_root: Path) -> str | None:
    try:
        return Path(path).resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        return None


def _module_file(base: Path, parts: list[str]) -> Path | None:
    """``base/a/b/c.py`` or ``base/a/b/c/__init__.py``, whichever exists."""
    if not parts:
        return None
    stem = base.joinpath(*parts)
    if stem.with_suffix(".py").is_file():
        return stem.with_suffix(".py")
    if (stem / "__init__.py").is_file():
        return stem / "__init__.py"
    return None


def _resolve(dotted: str, level: int, *, importer: Path, repo_root: Path) -> list[Path]:
    """Every repo file ``import <dotted>`` binds, in binding order: each package ``__init__``
    on the way down, then the module itself. Resolution tries the importer's own directory
    first (a proof run as a script has it at ``sys.path[0]``), then the repo root; a relative
    import resolves against the importer's package. Anything that resolves to nothing under
    the repo — stdlib, site-packages, a name no file answers to — resolves to []."""
    parts = [p for p in dotted.split(".") if p] if dotted else []
    if level:
        base = importer.parent
        for _ in range(level - 1):
            base = base.parent
        bases = [base]
    else:
        bases = [importer.parent, Path(repo_root)]
    for base in bases:
        target = _module_file(base, parts) if parts else (base / "__init__.py" if level else None)
        if target is None:
            continue
        out: list[Path] = []
        for i in range(1, len(parts)):
            init = base.joinpath(*parts[:i]) / "__init__.py"
            if init.is_file():
                out.append(init)
        out.append(target)
        return out
    return []


_BINDING_FIX = ("THE FIX BELONGS TO THE PROOF: it must survive its subject being taken away — "
                "resolve the names this build ADDED at call time rather than binding them at "
                "import (move the import inside the tooth or inside main(); the hollow reading "
                "reverts the file and a proof that crashes in its import block prints no teeth, "
                "which hollow records as UNRAN rather than as a red tooth)")


def proof_binds_its_subject_at_call_time(ticket: dict, *, repo_root: Path, roots=None,
                                         named: list[str] | None = None) -> list[dict]:
    """Every module-level binding, in any proof this ticket names or in any repo module those
    proofs reach through module-level imports, of a FILE or a top-level NAME that this build
    added — one lack per binding, carrying the proof, the line, and the import chain that
    reaches it. Empty when nothing binds early, and empty (silent, not green) when the
    inputs are not there to read: no BUILDME crossing, no pre-build commit, no decompose
    berth. Each of those is already a lack in another mouth.

    ``named`` is the proof list ``lacks`` has already derived, handed over so the journals
    are not re-indexed for the same ticket; a caller without one lets it be derived here."""
    from cairn.tools.base.crossings import buildme_crossing

    tid = str(ticket.get("id") or "")
    repo_root = Path(repo_root)
    # The berth first: it is the cached read, and most of the corpus at PROVEME or beyond
    # predates decompose berths — asking the journals for those would be paying the
    # expensive read to learn nothing.
    berths_root = (roots or {}).get("berths") if isinstance(roots, dict) else None
    wrote = _writes_to(ticket, berths_root)
    if not wrote:
        return []
    crossing = buildme_crossing(tid, roots) if tid else None
    at = str((crossing or {}).get("at") or "")
    if not at:
        return []
    pre = _prebuild_commit(at, repo_root=repo_root)
    if not pre:
        return []
    added_files, added_names = _added_by_the_build(pre, wrote, repo_root=repo_root)
    if not added_files and not added_names:
        return []

    found: list[dict] = []
    for one in (named if named is not None else _proven_by(ticket, roots)):
        proof_path = (repo_root / one) if not Path(one).is_absolute() else Path(one)
        if not proof_path.is_file():
            continue  # proof_on_disk is the mouth for this
        seen: set[str] = set()
        _walk_bindings(proof_path, [], proof=one, tid=tid, repo_root=repo_root,
                       added_files=added_files, added_names=added_names, seen=seen, found=found)
    return found


def _walk_bindings(module: Path, chain: list[str], *, proof: str, tid: str, repo_root: Path,
                   added_files: set[str], added_names: dict[str, set[str]],
                   seen: set[str], found: list[dict]) -> None:
    rel = _rel_to(module, repo_root)
    if rel is None or rel in seen:
        return
    seen.add(rel)
    try:
        tree = ast.parse(module.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return

    def lack(line: int, imported: str, *, file: str | None = None, name: str | None = None,
             via: str) -> None:
        link = f"{rel}:{line}"
        what = f"file {file}" if file else f"name {name} in {via}"
        found.append(_lack(
            tid, "proof_binds_its_subject_at_call_time",
            f"{Path(proof).name} reaches everything this build added at call time, never at import",
            f"{link} binds {what} at module level ({imported}) — the build added it, so the "
            f"hollow reading takes it away and the proof cannot reach its first tooth. "
            + (f"Chain: {' -> '.join(chain + [link])}. " if chain else "")
            + _BINDING_FIX,
            proof=proof, line=line, module=rel, chain=chain + [link], imported=imported,
            **({"file": file} if file else {"name": name, "in": via})))

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                for target in _resolve(alias.name, 0, importer=module, repo_root=repo_root):
                    trel = _rel_to(target, repo_root)
                    if trel in added_files:
                        lack(node.lineno, f"import {alias.name}", file=trel, via=trel)
                    _walk_bindings(target, chain + [f"{rel}:{node.lineno}"], proof=proof, tid=tid,
                                   repo_root=repo_root, added_files=added_files,
                                   added_names=added_names, seen=seen, found=found)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            stmt = f"from {'.' * node.level}{base} import " + ", ".join(a.name for a in node.names)
            holders = _resolve(base, node.level, importer=module, repo_root=repo_root)
            for target in holders:
                trel = _rel_to(target, repo_root)
                if trel in added_files:
                    lack(node.lineno, stmt, file=trel, via=trel)
                _walk_bindings(target, chain + [f"{rel}:{node.lineno}"], proof=proof, tid=tid,
                               repo_root=repo_root, added_files=added_files,
                               added_names=added_names, seen=seen, found=found)
            holder = holders[-1] if holders else None
            hrel = _rel_to(holder, repo_root) if holder else None
            for alias in node.names:
                if alias.name == "*":
                    for name in sorted(added_names.get(hrel or "", ())):
                        lack(node.lineno, stmt, name=name, via=hrel)
                    continue
                # ``from pkg import sub`` binds a FILE when pkg/sub.py exists, a NAME otherwise.
                sub = _resolve(f"{base}.{alias.name}" if base else alias.name, node.level,
                               importer=module, repo_root=repo_root)
                if sub:
                    srel = _rel_to(sub[-1], repo_root)
                    if srel in added_files:
                        lack(node.lineno, stmt, file=srel, via=srel)
                    _walk_bindings(sub[-1], chain + [f"{rel}:{node.lineno}"], proof=proof, tid=tid,
                                   repo_root=repo_root, added_files=added_files,
                                   added_names=added_names, seen=seen, found=found)
                elif hrel and alias.name in added_names.get(hrel, ()):
                    lack(node.lineno, stmt, name=alias.name, via=hrel)


def _concept_lacks(ticket: dict, tid: str, artifact: str, repo_root: Path, seal_reader) -> list[dict]:
    """A concept-piece is proved by PEOPLE READING IT, so there is no proof file to declare in.

    Its coverage question is therefore a different question with the same shape: is there a
    review VALIDATION beside the artifact, and does it say a review is what happened? The
    clause-by-clause join does not apply — a reader does not go green per numbered clause —
    and pretending it did would demand a ``PROVES`` block inside a markdown file. What is
    checked is the one thing the tester's own rule already says: verdict and seal from the
    same hand holds for code; for a human-proved class the reviewers are the verdict, so the
    record of the review is the whole evidence and its absence is the whole lack.
    """
    path = (repo_root / artifact) if not Path(artifact).is_absolute() else Path(artifact)
    if not path.exists():
        return [_lack(tid, "artifact_on_disk", f"{artifact} exists",
                      "the concept-piece names an artifact that is not on disk",
                      artifact=artifact)]
    seal = seal_reader(path, artifact=True)
    if not seal:
        return [_lack(tid, "review_record", f"a review VALIDATION sits beside {path.name}",
                      "no review record — a concept-piece at PROVEME with nobody's reading "
                      "recorded is a claim about readers who may never have read it",
                      artifact=artifact)]
    method = fold(str(seal.get("method") or ""))
    if "review" not in method and "read" not in method:
        return [_lack(tid, "review_record",
                      f"the seal beside {path.name} records a review",
                      f"the seal beside the artifact records method {seal.get('method')!r}, "
                      f"which is not a reading — a concept-piece is proved by readers",
                      artifact=artifact, method=seal.get("method"))]
    return []


def _lack(ticket_id: str, kind: str, about: str, why: str, **values) -> dict:
    return {"ticket": ticket_id, "kind": kind, "about": about, "why": why, "values": values}


def _proven_by(ticket: dict, roots=None) -> list[str]:
    """Every proof named since the build that stands — always a list.

    Since the latest FORWARD BUILDME, not from the beginning: a ticket kicked back and
    re-crossed must not be checked against the proof it abandoned, and crossing BUILDME
    again is exactly what marks the abandonment.

    NOT "the latest crossing that names any", which is what this read was until
    2026-09-10 and which loses evidence under the journals. One crossing ACT is journaled
    at every component address it touches, so the last record carries one component's
    share of the act. Measured against the stored arrays at b9828a2^: the last-record
    reading loses proofs on 4 of 42 tickets; this one loses none. The whole measurement is
    at the head of cairn/tools/base/crossings.py.

    ``proven_by`` may be one path or a list of them. A ticket whose subject is a SEAM has
    ends in more than one component, and its clauses are proved by teeth in each — writing
    one path there would force the crossing to lie about two thirds of the evidence.
    Duplicates are dropped and order is kept, so the first named proof stays the one a
    single-proof lack points at.

    THE CROSSINGS COME FROM THE JOURNALS NOW, not from an array on the ticket
    (ruling 2026-09-10-crossings-are-derived-never-written). The rule this function
    implements is unchanged and is why the derivation offers it by name; what changed is
    that a gate no longer reads evidence a hand wrote. Measured before the switch: 42
    tickets carried a crossings list, 2 an empty one, 1 a prose string where this loop
    parsed dicts — and NOTHING wrote any of them.
    """
    # Bound at call time — see the note at the has_crossings site above.
    from cairn.tools.base.crossings import proven_by_since_buildme

    return proven_by_since_buildme(str(ticket.get("id") or ""), roots)


def _latest_seal(path: Path, *, artifact: bool = False):
    from cairn.tools.base.validation import latest_seal
    return latest_seal(str(path), artifact=artifact)


def _fingerprint_stale(proof_path: Path, seal: dict) -> str | None:
    from cairn.tools.base.validation import sealed_fingerprint_now
    recorded = (seal.get("evidence") or {}).get("source_fingerprint")
    if not recorded:
        return ("the seal records no source_fingerprint, so nothing can say whether the code "
                "it sealed is the code on disk now")
    try:
        # THROUGH THE ONE DOOR, under the seal's OWN recipe. This used to re-take the
        # fingerprint the only way there was — over the component directory — which became
        # wrong the moment a seal could record an import closure instead: every closure seal
        # in the corpus would have read stale here while reading green in the tester, and two
        # records of truth may not contradict each other (Law 7).
        current = sealed_fingerprint_now(str(proof_path), seal)
    except OSError:
        return None
    if recorded != current:
        return (f"code changed since the seal — horizon closed (Law 3): sealed "
                f"{recorded[:12]}…, working tree {current[:12]}…")
    return None


def load_tickets(commons: Path) -> list[dict]:
    """Every readable ticket in the commons, as dicts. A malformed one is skipped HERE and
    caught by the ticket inspector, which owns that finding — two components reporting the
    same defect is how a reader learns to ignore both."""
    out = []
    tickets_dir = Path(commons) / "tickets"
    if not tickets_dir.is_dir():
        return out
    for f in sorted(tickets_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            data.setdefault("id", f.stem.split("-")[0])
            out.append(data)
    return out


def print_teeth_main(module_file: str, *extra_argv: str) -> int:
    """Run a pytest-shaped proof and print every tooth BY NAME, in the shape this module reads.

    THE DEFECT THIS EXISTS TO END, measured 2026-09-07: the tester runs a proof as
    ``python3 <proof>``, and its verdict is the exit code. Ten of the corpus's 158 proofs
    carry no ``__main__`` block at all, so running them as a script defines some functions
    and exits 0 — a GREEN SEAL over zero teeth executed, which is the hollow build Law 8
    names, sitting inside the machinery that exists to refuse it. Verified by running two
    of them: exit 0, zero bytes of output, zero tests.

    The near miss is worse than the plain gap: ``pytest.main([f, "-q"])`` DOES run the
    teeth, but prints dots, so the seal records ``teeth_green: []`` and no clause can ever
    be declared against it. A proof that ran everything and named nothing is unusable as
    coverage evidence even though its verdict is honest.

    So the printer lives HERE, beside ``teeth_printed``, and not in each proof: the reader
    of the names and the writer of the names are then one component by construction, and a
    change to the shape cannot leave half the corpus behind. A SKIPPED tooth prints under
    a marker that is neither green nor red — it did not prove and it did not fail, and
    quietly counting it either way is the direction a hollow build wants.

        if __name__ == "__main__":
            from cairn.tools.proof_coverage import print_teeth_main
            raise SystemExit(print_teeth_main(__file__))
    """
    import pytest

    class _Names:
        def pytest_runtest_logreport(self, report):
            if report.when == "call":
                marker = "ok  " if report.passed else ("skip" if report.skipped else "FAIL")
            elif report.failed:            # a setup/teardown error never reaches "call"
                marker = "FAIL"
            else:
                return
            # A NEWLINE ON BOTH SIDES, and neither is cosmetic. pytest's terminal
            # reporter writes its one-character progress mark (``.``, ``F``, ``s``) to
            # the current line with no newline of its own, so an unfenced print lands the
            # tooth in the middle of it. Without the leading newline the stream carries
            # ``.  ok   test_x`` — and both marker patterns are anchored, so every tooth
            # goes invisible to ``teeth_printed`` while looking perfectly readable to a
            # human. Without the trailing one it carries ``  FAIL test_xF``: the mark is
            # a name character, so the tooth is read back under a name no ticket can
            # ever declare. Both failures were seen, in that order, on 2026-09-07; the
            # round-trip is a tooth in this tool's own proof so neither can return.
            print(f"\n  {marker} {report.nodeid.split('::')[-1]}")

    return int(pytest.main([module_file, "-q", "-p", "no:cacheprovider", *extra_argv],
                           plugins=[_Names()]))

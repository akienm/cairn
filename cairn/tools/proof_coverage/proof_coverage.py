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

# A clause key is the number inside a ``(N)`` marker in the DONE-when text.
_CLAUSE_MARK = re.compile(r"\((\d{1,2})\)")
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
        for pattern, marker_group, name_group in ((_MARKER_FIRST, 1, 2), (_MARKER_LAST, 2, 1)):
            m = pattern.search(line)
            if not m:
                continue
            marker = fold(m.group(marker_group))
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
    return found or [WHOLE]


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


def lacks(ticket: dict, *, repo_root: Path, seal_reader=None) -> list[dict]:
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

    named = _proven_by(ticket)
    if not named:
        # TWO LACKS, NOT ONE, and the split is a measurement rather than a courtesy.
        # Measured 2026-09-07 over the live corpus: of 230 tickets at PROVEME or beyond,
        # 215 name no proof — but 196 of those carry NO crossings array at all, because
        # they were resolved before the crossing record existed, while the rest carry
        # crossings that simply never named one. Both are red (Law 9; a proof nobody can
        # find is a proof nobody checked), and collapsing them into one line would bury
        # nineteen actionable tickets under two hundred archaeological ones. Distinguishing
        # them is not an exemption: neither goes green, and the counts stay exact.
        no_record = not (ticket.get("crossings") or [])
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
    return found


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


def _proven_by(ticket: dict) -> list[str]:
    """The proof or proofs named by the LATEST crossing that names any — always a list.

    Latest, not first: a ticket kicked back to BUILDME and re-crossed names a new proof,
    and reading the first crossing would check the abandoned one forever.

    ``proven_by`` may be one path or a list of them. A ticket whose subject is a SEAM has
    ends in more than one component, and its clauses are proved by teeth in each — writing
    one path there would force the crossing to lie about two thirds of the evidence.
    Duplicates are dropped and order is kept, so the first named proof stays the one a
    single-proof lack points at.
    """
    for entry in reversed(ticket.get("crossings") or []):
        if not isinstance(entry, dict) or not entry.get("proven_by"):
            continue
        raw = entry["proven_by"]
        one = [raw] if isinstance(raw, str) else [str(p) for p in raw if p]
        seen, out = set(), []
        for p in one:
            if p not in seen:
                seen.add(p)
                out.append(p)
        return out
    return []


def _latest_seal(path: Path, *, artifact: bool = False):
    from cairn.tools.base.validation import latest_seal
    return latest_seal(str(path), artifact=artifact)


def _fingerprint_stale(proof_path: Path, seal: dict) -> str | None:
    from cairn.tools.base.validation import source_fingerprint
    recorded = (seal.get("evidence") or {}).get("source_fingerprint")
    if not recorded:
        return ("the seal records no source_fingerprint, so nothing can say whether the code "
                "it sealed is the code on disk now")
    try:
        current = source_fingerprint(str(proof_path))
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

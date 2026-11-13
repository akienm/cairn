"""THE RESEAL DOOR — the four-rung ladder a seal rides when it stops reproducing.

Charter + why: cairn/devices/tester/intention+why.json
Ticket:        CairnCommons/tickets/4d9115eb04cd-a-seal-that-cannot-be-reproven-rides-the-ruled-ladder.json
Ruling:        CairnCommons/decisions/2026-09-06-a-seal-that-cannot-be-reproven-is-red-then-repaired-then-a-trouble-then-design.json

WHY THIS EXISTS. Akien, 2026-09-06: *"if it cannot be reproven, that means something is no
longer functioning correctly."* A peer leans on a green it did not check (Law 8), so the
moment a green stops being reproducible it has to stop being green **without anyone having
to notice**. Rung 1 of that — the noticing — has been physics since 2026-08-04:
``build_inspector.component_color`` reds a component whose seal fingerprint no longer
matches the working tree, and files an ``inspector-new-finding`` trouble for it. Rungs 2,
3 and 4 were a paragraph in a ruling, which is exactly the shape CLAUDE.md's rule names:
*a deterministic red is fixed, or it carries a ruling from Akien — never a paragraph.*
This module is the three missing rungs.

THE LADDER, AND EACH RUNG'S ONE JOB

  1. RED AT MEASUREMENT — not ours. ``standing()`` is the reader; the inspector already
     fires it on every pass. This door reuses that same reader rather than growing a second
     opinion about whether a seal still holds (one recipe, one answer — see
     ``sealed_fingerprint_now``'s docstring for what the three-answer version cost).
  2. BOUNDED REPAIR — the door reruns the proof. If it is red, ANY change that leaves the
     proof file byte-identical may be made and the door will reseal green on the next pass.
     The bound is the proof file's own sha256, recorded at the first red.
  3. TROUBLE — a red that is not repaired lands ONE trouble per component carrying the
     stderr tail, and self-clears on the pass where the seal goes green.
  4. DESIGN — "the proof's claim no longer matches the spec" is Akien's ruling, never CC's
     declaration. A reseal whose proof file has moved is REFUSED, and the refusal lifts only
     for a ruling id that resolves to a CONFIRMED record in the ruling store.

WHAT THE DOOR MAY NEVER DO, and the ticket says it as a WRONG INTENT: write a seal for a
proof it did not just run, or restore green at any rung without a run. So there is exactly
one call to ``persist_validation`` per ``run_proof`` in this file, and it is downstream of
it in both branches. A rung is a DISPOSITION of a measurement, never a substitute for one.

WHERE THE LADDER'S STATE LIVES — AND WHY IT IS NOT THE FILE THE CAST NAMED. The ticket's
``watchme`` field (cast 2026-09-06) named the operational record as
``<component>/validations/*.red.json``. MEASURED 2026-09-09, before writing a line of it:
six live readers glob ``validations/*.json`` — ``tools/orient/orient.py:222``, three tester
probes (``a_proof_cannot_seed_the_tree_it_reads``, ``seal_measurements_are_not_dropped``,
``the_collapse_holds_in_live_traffic``) and ``test_validation_store.py:540`` — and a file
named ``x.red.json`` matches that glob. Every one of them would have ingested the ladger as
a VALIDATION and judged it against the ratified eight fields. So the ladder rides
``evidence.reseal_ladder`` on the standing validation instead: co-located (Law 5), inside
the record of truth it is about, in the exact shape ``record_hollow`` established the day
before for the same reason. The ticket's watchme text is repaired to name this address —
the reason has to carry a RESOLVABLE referent or it is a hollow pass, and it now does.

AND THE LADDER CLOSES ON THE GREEN RECORD RATHER THAN VANISHING. A green reseal writes
``evidence.reseal_closed`` carrying the whole ladder it just ended — when it opened, how
many red passes it took, the hash the repair was bounded by. ``read_ladder`` returns
``None`` for a green seal, so a closed ladder gates nothing; it is provenance, not state.
Erasing it would have made the one interesting thing about a repaired seal — that it WAS
repaired, under a bound — unreadable a week later.

THE RESIDUE, STATED RATHER THAN HIDDEN. ``cairn test --seal`` is a different door and this
one cannot gate it: a hand that edits a proof and runs ``--seal`` lands green with no ruling
and drops the ladder, because the store REPLACES. That hole is real and is deliberately not
closed here — the ticket bounds "the seal mechanism itself" and "the validation store" OUT,
and closing it means a rule inside ``persist_validation``, which is that other ticket's
work. What this door guarantees is that ITS act never launders a changed proof into a green.

FIRED FROM A GIT PRE-COMMIT HOOK, NEVER FROM THE BEAT (the ticket's third constraint). The
hook is at ``cairn/devices/tester/hooks/pre-commit`` and installs with
``cairn test --reseal-install``. It is deliberately NON-BLOCKING: the physics that stops a
false green is the seal not going green, which ``component_color`` then reds forever — not a
refused commit. A hook that blocked would make "commit often" (a standing instruction) and
"a red is fixed or ruled" fight each other, and the loser would be the hook, uninstalled.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from cairn.devices.tester.conditions import compare
from cairn.devices.tester.device import GREEN, TIMEOUT, TesterDevice
from cairn.devices.tester.scratch_sweep import sweep as sweep_scratch
from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
from cairn.tools.base.address import component_of
from cairn.tools.validation_store.validation_store import (
    closure_of,
    component_root_for,
    persist_validation,
    read_validations,
    seal_trouble_identity,
    sealed_fingerprint_now,
    standing,
    validations_path_for,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CALLER = "cairn test --reseal"

# WHO THE SELF-CLEAR SPEAKS FOR. A trouble is cleared PER RECIPIENT (trouble.py: `outstanding`
# is every notified name with no clear in its name), and this door's troubles are notified to
# the lane's default recipient, `cc`. Measured 2026-09-13: 11 of 12 seal-red troubles in the
# store carried up to three clears `by="cairn test --reseal"` — the fold appended each one,
# read `cc` as still outstanding, and left the trouble OPEN. A green reseal announced its fix
# into a record nobody's inbox ever left. So the clear is sent AS the recipient it discharges
# (the build inspector's reconcile does the same, `by="cc"`), and CALLER rides in
# `what_changed` where it is provenance rather than a name the fold has to match. The
# literal is a copy of trouble.DEFAULT_RECIPIENTS on purpose: a device may not import another
# (device_isolation_holds), and a seam that has to agree on one word does not need a door.
CLEARS_FOR = "cc"



class ResealRefused(Exception):
    """RUNG 4 SPOKE. The proof file moved under an open ladder and no confirmed ruling
    rode in the same act, so the door will not turn this red into a green.

    Carries the two hashes verbatim, because the ticket demands it: *"the refusal names the
    hash it saw."* A refusal that only said "the proof changed" would leave the reader
    unable to tell a real spec change from a whitespace edit without re-deriving both
    numbers by hand — Law 1 charging a re-derivation at the one moment the reader is
    already stuck."""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _rel(path) -> str:
    p = Path(path).resolve()
    return str(p.relative_to(REPO_ROOT)) if p.is_relative_to(REPO_ROOT) else str(p)


def proof_sha256(proof_path) -> str:
    """The proof FILE's own bytes — not its closure, not its component.

    ``source_fingerprint`` cannot answer rung 2's question. It is one hash over the proof
    AND everything the proof imports, so it moves when a repair moves the code, which is
    the very act rung 2 is meant to permit. The bound is "the assertions did not change",
    and the closest deterministic reading of that is the proof file's own bytes.

    THE HOLE, NAMED: byte-identity is stricter than assertion-identity. Reformatting a
    comment in a proof trips the bound and costs a ruling. That is the conservative
    direction (a false refusal is loud and cheap; a false acceptance is a green nobody
    checked), and it is the reading the ticket's own assumption_check declared
    load-bearing."""
    digest = hashlib.sha256()
    with open(proof_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ONE KEY PER PROOF, spelled by the store (ticket 87f0fc7b3514): the ladder's raises and
# clears and the store's announce and round-trip clear all name a red seal the same way.
trouble_identity = seal_trouble_identity

# THE KEYS THIS PROCESS RAISED, for a raiser with no trail to read (a fixture's). A raiser
# that has one (ModuleRaiser: ``diagnostic_trail()``) is asked through its trail instead,
# because the store's round-trip clear lands on disk before the ladder asks.
_RAISED_THIS_RUN: set[str] = set()


def _raise(raiser, identity: str, **kw) -> None:
    raiser.raise_trouble(identity, **kw)
    _RAISED_THIS_RUN.add(identity)


def _stands_raised(raiser, identity: str, ladder) -> bool:
    """Does ``identity`` stand raised, so a green may clear it? (ticket 87f0fc7b3514, D2/D7).

    Measured 2026-11-05: 5054 seal-red clears in ~/.cairn/logs/tester/0 had no standing raise —
    every green cleared whether or not anything had been raised. An open ladder on the seal is
    the record that a rung-3 raise stood; otherwise the raiser's own trail says (the newest
    raise/clear naming the key), and a raiser with no trail falls back to this process's set.
    Reads only; writes nothing."""
    if ladder:
        return True
    trail_of = getattr(raiser, "diagnostic_trail", None)
    trail = trail_of() if callable(trail_of) else None
    if trail is not None and Path(trail).is_dir():
        names = sorted((n for n in os.listdir(trail)
                        if n.endswith(".raise_trouble.json") or n.endswith(".clear_trouble.json")),
                       reverse=True)
        for name in names:
            try:
                rec = json.loads((Path(trail) / name).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if rec.get("pointer") == identity:
                return name.endswith(".raise_trouble.json")
        return False
    return identity in _RAISED_THIS_RUN


def unreproduced_siblings(proof_path) -> list[str]:
    """The OTHER proofs in this proof's component that carry a seal ``standing()`` no longer
    reads proven — what still holds the component's one trouble open (ticket 86b6bf19ed2a).
    A proof with no validations file was never sealed, so it is not counted."""
    proof = Path(proof_path).resolve()
    out = []
    for sib in sorted((Path(component_root_for(str(proof))) / "proofs").glob("*.py")):
        if sib.resolve() == proof or not Path(validations_path_for(str(sib))).is_file():
            continue
        if not standing(str(sib))["proven"]:
            out.append(_rel(sib))
    return out


def read_ladder(proof_path) -> dict | None:
    """The OPEN ladder on this proof's standing seal, or ``None``.

    A green seal closes the ladder by definition, so it returns ``None`` even when the
    record carries a ``reseal_closed`` history — provenance is not state. A red seal that
    carries no ladder (one landed by ``cairn test --seal``, say) is an honest ``None``:
    this door records what IT measured, and it has not measured anything here yet."""
    trail = read_validations(str(proof_path))
    if not trail:
        return None
    seal = trail[-1]
    if not isinstance(seal, dict) or seal.get("verdict") == GREEN:
        return None
    ladder = (seal.get("evidence") or {}).get("reseal_ladder")
    return ladder if isinstance(ladder, dict) else None


def ruling_refusal(ruling_id: str, *, question_root: Path | None = None) -> str | None:
    """``None`` if ``ruling_id`` names Akien's decision; else the sentence saying why not.

    Two stores, one per era. An ``open-`` id is a question (ticket 9adc6fddf185: since
    2026-09-14 a decision IS an answered question), read through the question tool's declared
    interface, and it lifts rung 4 when it is resolved, whoever answered it: outline 19.14.8.3
    (Akien, 2026-10-31) — *"rung 4 no longer asks who answered"* (ticket e8be83a46ea9; until
    then a measured answer was refused for not being his). Any other id is a legacy ruling in the frozen decisions/ store,
    which must be CONFIRMED (ticket 37ddc47686c2). ``question_root`` points the question read
    at a scratch store for a proof; ``None`` is the live one.

    Read directly and read-only. The ruling store is Akien's record, frozen since the ruling
    intake's code was deleted (ticket 640a7a48e1c5, outline Q#43: "decisions/ stays
    read-only"), and this door only ever asks it a question — rung 4 is his, and a door that
    could write there would be CC declaring the spec changed, which is the one thing the
    ticket's owner line forbids. ``CAIRN_ROOTS_PARENT`` points the read at a scratch world
    for a proof, the seam the intake carried; otherwise the store is the commons beside the
    repo this file stands in.

    ``confirmed`` is the field the retired intake DERIVED from his own RULED marker, never
    one an author could type — so leaning on it here is leaning on his words, not on a
    packet's self-report."""
    if not (ruling_id or "").strip():
        return "no ruling id was given"
    if ruling_id.startswith("open-"):
        from cairn.tools.question import question as question_mod
        try:
            record = question_mod.read(ruling_id, root=question_root)
        except question_mod.Refused:
            return (f"no question {ruling_id!r} exists — rung 4 is Akien's, and an id that "
                    f"resolves to nothing is a paragraph wearing an id")
        if not record.get("resolved"):
            return f"question {ruling_id!r} is still open — rung 4 waits on its answer"
        return None
    store = _decisions_dir()
    for record in _rulings(store):
        if record.get("id") != ruling_id:
            continue
        if not record.get("confirmed"):
            return (f"ruling {ruling_id!r} is on disk but NOT CONFIRMED — it carries no RULED "
                    f"marker in Akien's own words, so it is CC's reading of a ruling and not "
                    f"the ruling (the retired intake derived `confirmed` from his marker)")
        return None
    return (f"no ruling {ruling_id!r} in {store} — rung 4 is Akien's, and a "
            f"ruling id that resolves to nothing is a paragraph wearing an id")


def _decisions_dir() -> Path:
    """The frozen decisions/ store: under ``CAIRN_ROOTS_PARENT`` when set, else beside this repo."""
    parent = os.environ.get("CAIRN_ROOTS_PARENT")
    base = Path(parent) if parent else Path(__file__).resolve().parents[4]
    return base / "CairnCommons" / "decisions"


def _rulings(store: Path) -> list[dict]:
    """Every ``kind: "ruling"`` record in the store; an unreadable file is not a ruling."""
    out = []
    for p in sorted(store.glob("*.json")) if store.is_dir() else []:
        try:
            record = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and record.get("kind") == "ruling":
            out.append(record)
    return out


def census(root: Path | None = None) -> list[dict]:
    """Every proof carrying a standing validation, with what ``standing()`` says of it now.

    The door's rung-1 reader, and the thing a pre-commit narrows down FROM. Ordered by
    path so two runs over an unchanged tree report in the same order (a diagnostic surface
    that reshuffles is a diagnostic surface nobody diffs)."""
    base = Path(root or REPO_ROOT)
    rows = []
    for val in sorted(base.rglob("validations/*.json")):
        comp = val.parent.parent
        proof = comp / "proofs" / (val.stem + ".py")
        if not proof.is_file():
            continue                       # a human-proved artifact's seal, or a stale file
        trail = read_validations(path=str(val))
        if not trail:
            continue
        rows.append({
            "proof": proof,
            "component": comp,
            "seal": trail[-1] if isinstance(trail[-1], dict) else {},
            "standing": standing(str(proof)),
        })
    return rows


def staged_files(root: Path | None = None) -> list[str]:
    """Repo-relative paths git has in the index. The pre-commit's whole input.

    ``--diff-filter=d`` drops deletions: a staged deletion has no content to reprove and
    the seal it breaks will red at ``component_color`` on the next inspector pass anyway,
    which is rung 1 doing its job without this door guessing."""
    base = Path(root or REPO_ROOT)
    proc = subprocess.run(
        ["git", "-C", str(base), "diff", "--cached", "--name-only", "--diff-filter=d"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def proofs_touching(staged: list[str], *, root: Path | None = None,
                    rows: list[dict] | None = None) -> list[Path]:
    """Which censused proofs a staged change re-runs: the proofs of the component that OWNS
    a staged file, and no one else's.

    AKIEN'S ANSWER, 2026-10-05 (~/.cairn/foreground-decisions.md item 7): "tool proofs:
    agreed" — when a tool changes, the proofs of the components that use it do not re-run;
    only the tool's own do. This door used to ask each seal under its own recipe — touched
    when a staged file sat in its import closure, or under its directory for a pre-closure
    seal — and both crossed components: one line in liveness.py re-ran 55 proofs across 19
    components (b9a7d9e5), and a diagnostic.py commit reached 64 components and ran past 30
    minutes without landing (be4a7b3c7caa). The owner of a path is the deepest component
    ancestor (``component_of``), so a nested machine's change does not reach its holder
    either. A user whose ground did move is still told by ``component_color`` reading its
    seal; this door only decides what the commit re-runs."""
    base = Path(root or REPO_ROOT)
    owners = {component_of(base / s) for s in staged} - {None}
    out = []
    for row in (rows if rows is not None else census(base)):
        if Path(row["component"]).resolve() in owners:
            out.append(row["proof"])
    return out


_TICKET_ID = re.compile(r"[0-9a-f]{12}")


def _teeth(source) -> set[str]:
    """The top-level ``def test_*`` names in a proof's source; an unparseable one has none."""
    import ast
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    return {n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")}


def _recorded_bytes(proof: Path, sha: str) -> bytes | None:
    """The committed bytes of ``proof`` whose sha256 is ``sha`` — the file the ladder bounded
    the repair to — or ``None`` when git holds no such blob of it.

    The ladder stores only the hash, and git already holds the bytes, so the teeth a moved
    proof removed are read back from history rather than stored twice. The caller's GIT_*
    is dropped (a pre-commit hook carries GIT_INDEX_FILE and friends), so the repo asked is
    the one the proof sits in."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

    def git(*args: str, cwd: Path, text: bool = True):
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=text, env=env)

    top = git("rev-parse", "--show-toplevel", cwd=proof.parent)
    if top.returncode != 0:
        return None
    root = Path(top.stdout.strip())
    try:
        rel = proof.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None
    log = git("log", "--format=%H", "--", rel, cwd=root)
    if log.returncode != 0:
        return None
    for commit in log.stdout.split():
        blob = git("show", f"{commit}:{rel}", cwd=root, text=False)
        if blob.returncode == 0 and hashlib.sha256(blob.stdout).hexdigest() == sha:
            return blob.stdout
    return None


def _ticket_refusal(proof: Path, tid: str, ladder: dict, *, tickets_dir=None) -> str | None:
    """``None`` when ticket ``tid``'s kind admits the change to ``proof``; else why not.

    OUTLINE 19.14.8.2-3 (Akien, 2026-10-31): *"for new/changed code tickets the rule is x, for
    fixit tickets the rule is y"*, and *"the fix may change the test case itself without a
    ruling: the proof's why names the ticket and says what it tests and why it changed, and
    names any tooth it removed."* Read off the ticket and the bytes, so it stays deterministic:
    y — a bug whose ``fixes`` lists this proof (the ladder being open is the real red on disk:
    ``read_ladder`` reads only a non-green seal); x — a code-seam whose proof's PROVES names it.
    Then, for both, the proof names the ticket and every tooth it removed since the bytes the
    ladder bounded. A ticket cannot call itself a fixit to get y: the kind and ``fixes`` are
    read here, never claimed in the act. Ticket e8be83a46ea9."""
    from cairn.tools.base.ticket_file import find_ticket, read_ticket
    from cairn.tools.proof_coverage.proof_coverage import declared

    plan = find_ticket(tid, tickets_dir)
    if plan is None:
        return f"no ticket {tid!r} — a ticket id that resolves to nothing is a paragraph wearing an id"
    ticket = read_ticket(plan)
    kind = str(ticket.get("node_class") or "").strip().lower()
    if kind == "code-seam":
        if tid not in declared(proof):
            return (f"ticket {tid} is a code-seam and the proof's PROVES does not name it (x: "
                    f"a code-seam changes a proof it declares)")
    elif kind == "bug":
        fixes = ticket.get("fixes")
        here = proof.resolve()
        if not (isinstance(fixes, list) and any(
                (Path(f) if Path(str(f)).is_absolute() else REPO_ROOT / str(f)).resolve() == here
                for f in fixes)):
            return f"ticket {tid} is a bug and its fixes does not list {_rel(proof)} (y: a fixit names the red it fixes)"
    else:
        return f"ticket {tid} is a {kind or 'kindless'} ticket; rung 4 admits a code-seam (x) or a bug (y)"
    now_text = proof.read_text(encoding="utf-8")
    if tid not in now_text:
        return f"the proof does not name ticket {tid} — its why names the ticket that changed it"
    old = _recorded_bytes(proof, ladder.get("proof_sha256") or "")
    if old is None:
        return (f"git holds no blob of {_rel(proof)} hashing {ladder.get('proof_sha256')}, so "
                f"the teeth ticket {tid} removed cannot be measured")
    for name in sorted(_teeth(old) - _teeth(now_text)):
        if name not in now_text:
            return f"ticket {tid} removed tooth {name} and the proof does not name it"
    return None


def rung4_refusal(proof_path, ruling_id: str | None, *, tickets_dir=None) -> str | None:
    """``None`` when rung 4 lets a seal land on this proof; else the refusal, naming the proof.

    ONE GATE FOR BOTH SEAL WRITERS (ticket 2dd69b2ba087). Measured 2026-10-08 on
    test_scratch.py: this door refused at rung 4, and ``cairn test --seal`` on the same proof
    then landed a seal with the ladder gone — the second writer never asked. So the check is
    a function the reseal and the plain seal both call before they run anything."""
    proof = Path(proof_path).resolve()
    ladder = read_ladder(proof)
    now_hash = proof_sha256(proof)
    if not (ladder and ladder.get("proof_sha256") and ladder["proof_sha256"] != now_hash):
        return None
    if _TICKET_ID.fullmatch(ruling_id or ""):
        why = _ticket_refusal(proof, ruling_id, ladder, tickets_dir=tickets_dir)
    else:
        why = ruling_refusal(ruling_id or "")
    if why is None:
        return None
    return (f"{_rel(proof)}: the ladder opened {ladder.get('opened')} bounded the repair to a "
            f"proof file hashing {ladder['proof_sha256']}, and the file on disk now hashes "
            f"{now_hash}. The assertions moved, so this is not a repair — it is 'the "
            f"proof's claim no longer matches the spec', which needs a resolved question, a "
            f"confirmed ruling, or a ticket whose kind admits the change (outline 19.14.8; "
            f"ruling 2026-09-06-a-seal-that-cannot-be-reproven-is-red-then-repaired-"
            f"then-a-trouble-then-design). Refused: {why}. The component stays red until "
            f"it is reproven under one.")


def carry_ladder(record: dict, proof_path, ladder: dict, *, ruling_id: str | None = None) -> dict:
    """Land a plain seal's ``record`` over an OPEN ladder without dropping it (2dd69b2ba087).

    A green closes the ladder as rung 2 does (``reseal_closed``, plus ``reseal_ruling`` when
    one rode along); a red carries it forward, bound to the bytes on disk — the same bytes
    when nothing moved, and the re-based bytes when rung 4 was lifted, because re-basing is
    what a ruling MEANS (see rung 3 below). Returns the record that landed."""
    proof = Path(proof_path).resolve()
    now_hash = proof_sha256(proof)
    evidence = dict(record.get("evidence") or {})
    if evidence.get("fingerprint_closure"):   # the same refusal run_proof makes (8cc2a5752b6a)
        from cairn.devices.tester.working_bytes import UnnormalizedClosure, unnormalized
        from cairn.tools.validation_store import validation_store as _vs
        stale = unnormalized(evidence["fingerprint_closure"], _vs._REPO_ROOT)
        if stale:
            raise UnnormalizedClosure(stale)
    if record.get("verdict") == GREEN:
        if ruling_id:
            evidence["reseal_ruling"] = ruling_id
        evidence["reseal_closed"] = {**ladder, "closed_at": _now(), "closed_by": "cairn test --seal",
                                     "closed_proof_sha256": now_hash}
        sealed = {**record, "evidence": evidence}
        compare(sealed, proof)
    else:
        carried = {**ladder, "proof_sha256": now_hash}
        if ruling_id:
            carried["ruling"] = ruling_id
        evidence["reseal_ladder"] = carried
        sealed = {**record, "evidence": evidence}
    persist_validation(sealed, proof_path=str(proof), unsealing_because=NETWORK_SEAL_RETIRED)
    return sealed


def _clear_a_raise_a_green_settles(proof: Path, rel: str, raiser, trouble_root=None) -> str | None:
    """Clear ``proof``'s seal-red when it stands live at the holder; the cleared identity or None.

    Rung 1's half of "one identity from raise to clear" (ticket b65e965237f3). A seal that reads
    proven over today's bytes settles every raise filed under its identity, and before this
    lane nothing said so. validation_store clears only on a verdict CHANGE, so a raise filed
    while the standing verdict stayed green (a timeout, a settled-red lane re-raise) outlived
    every later green. Measured: seal-red-...-test-codemother stood at 5x after its proof
    resealed green (2026-11-10), and -test-clearance-reaches-trouble-through-its-tool stood live
    over a proven seal (2026-11-11).

    THE HOLDER'S LIVE LIST, NOT THE TRAIL. The run lane's ``_stands_raised`` scans the raiser's
    trail newest first, and that trail held 80,880 records on 2026-11-11. Rung 1 fires for
    every proof on every commit, and a never-raised proof would read the whole trail, so this
    lane asks the trouble device's published tool for its standing ids instead (RULE 1: the
    tool is ``published_by_device``). Only an id that stands is cleared, never a blind clear
    (ticket 87f0fc7b3514). A holder this lane cannot read leaves the trouble standing:
    loud and wrong beats quiet and wrong (Law 7)."""
    identity = trouble_identity(proof)
    try:
        from cairn.devices.trouble.tools.store.store import live
        standing_ids = {t.get("id") for t in live(root=trouble_root)}
    except Exception:  # noqa: BLE001 — an unreadable holder leaves the trouble standing
        return None
    if identity not in standing_ids:
        return None
    if raiser is None:
        from cairn.tools.base.diagnostic import ModuleRaiser
        raiser = ModuleRaiser("tester")
    try:
        raiser.clear_trouble(identity, by=CLEARS_FOR, what_changed=(
            f"{CALLER}: {rel} reads proven at rung 1 — its green seal still reproduces over "
            f"today's bytes, so the raise it stood under no longer measures true"))
    except Exception:  # noqa: BLE001 — a lane we cannot reach leaves the trouble standing
        return None
    _RAISED_THIS_RUN.discard(identity)
    return identity


def reseal(proof_path, *, ruling_id: str | None = None, tester=None, raiser=None,
           skip_settled: bool = False,
           timeout: int = 120, isolation: str | None = None,
           index_only: bool = False, trouble_root=None) -> dict:
    """ONE proof through the ladder. Runs it, then disposes of what the run measured.

    Raises ``ResealRefused`` at rung 4 — BEFORE the run, before any write — when the proof
    file has moved under an open ladder without a confirmed ruling. Refusing before the run
    is deliberate: a run whose result can only be discarded is a minute spent to learn
    nothing, and worse, its green would sit in the caller's return value looking like a
    verdict the door had merely declined to record.

    Returns ``{proof, outcome, rung, ran, why, ...}``. ``outcome`` is one of
    ``unchanged`` (rung 1 says the seal still holds — nothing ran, nothing was written),
    ``resealed`` (a run went green over an open ladder or a closed horizon),
    ``sealed`` (a first seal — the proof had none), ``red`` (rung 3; the trouble is filed), or
    ``held`` (``index_only``: the closure differs from the index, so nothing ran or was written).
    """
    proof = Path(proof_path).resolve()
    rel = _rel(proof)
    ladder = read_ladder(proof)
    now_hash = proof_sha256(proof)

    # ── RUNG 4: the gate, and it is the first thing that happens ──────────────────────
    refusal = rung4_refusal(proof, ruling_id)
    if refusal is not None:
        raise ResealRefused(refusal)

    before = standing(str(proof))
    if before["proven"]:
        cleared = _clear_a_raise_a_green_settles(proof, rel, raiser, trouble_root)
        return {"proof": rel, "outcome": "unchanged", "rung": 1, "ran": False,
                "cleared": cleared,
                "why": before["why"] + (f" — cleared the standing {cleared}" if cleared else "")}

    # THE COMMIT IS WHAT IS MEASURED (ticket 42075a49c121): under the hook (index_only), a
    # proof whose closure differs from the index is held BEFORE it runs — no seal, no trouble —
    # because a run over the working tree would describe bytes this commit does not carry.
    if index_only:
        top = subprocess.run(["git", "-C", str(proof.parent), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True)
        if top.returncode == 0:
            base = Path(top.stdout.strip())
            trail = read_validations(str(proof))
            closure = closure_of(trail[-1]) if trail else None
            dirty = dirty_against_index(os.path.relpath(proof, base), closure, base)
            if dirty:
                return {"proof": rel, "outcome": "held", "rung": 1, "ran": False,
                        "because": dirty,
                        "why": "the commit does not carry " + ", ".join(dirty[:3]) + " — this "
                               "proof measures what is committed, so it waits for the commit "
                               "that carries them"}

    # RESOLVED ONCE, HERE, because BOTH rung-1 lanes below can raise and the runner-side
    # lanes can too. It used to be defaulted after the run, which was fine while nothing
    # before the run had anything to say; the settled-red lane does.
    if raiser is None:
        from cairn.tools.base.diagnostic import ModuleRaiser
        raiser = ModuleRaiser("tester")

    # A SETTLED RED IS RUNG 1 TOO — and leaving it out cost 417 SECONDS PER COMMIT, measured
    # on this door's own first live fire, 2026-09-09. `standing()` has four outcomes and only
    # one is proven, so the line above sends the other three to the runner alike. Two of them
    # belong there: never sealed, and sealed-green-but-the-fingerprint-moved are both open
    # questions, and the only way to close them is to run. THE THIRD IS NOT A QUESTION AT ALL.
    # A seal that reads red over a closure that has not moved since is an answer already
    # taken, from these exact bytes; re-running it is guaranteed to reproduce it, and Law 1
    # calls re-deriving a settled answer a defect. The hook fires on EVERY commit, so the
    # defect was not academic: test_hollow.py is red at 417s and would have been re-run, in
    # full, before every commit in the repo, forever.
    #
    # THE FINGERPRINT IS WHAT MAKES THIS SAFE, and it is why the check is not merely
    # `verdict != GREEN`. A repair necessarily edits code inside the closure the red was
    # taken over, so a repair MOVES the fingerprint and this lane cannot fire — rung 2 still
    # sees every real repair. What the lane skips is the case where nothing whatsoever has
    # changed, which is exactly the case where running teaches nothing. Re-taken under the
    # SEAL'S OWN recipe (`sealed_fingerprint_now`), never today's, for the reason
    # `standing()` gives at its own line: asking the new question of an old seal would expire
    # the whole corpus at once and call it drift.
    #
    # AND IT IS OFF BY DEFAULT, because a red is not always the code's fault. A proof that
    # failed because the database was down moves no bytes when the database comes back, so a
    # door that skipped every settled red unconditionally would pin that proof red until
    # somebody edited something — a trap with no key in it. The escape had to be a real path
    # rather than a paragraph (Law 4), and the shape was already sitting in the verb: the
    # HOOK calls with no targets and is the automatic caller Law 1 is about, while a hand
    # typing `cairn test --reseal <proof>` is asking, explicitly, for that proof to run. So
    # `_reseal_run` passes skip_settled=not args.targets and the two callers get what each
    # is actually asking for. This is also what keeps rung 3's own tooth honest: it names
    # its proof, so it still measures two real failing passes folding to one trouble.
    #
    # THE TROUBLE IS RE-RAISED RATHER THAN ASSUMED, because skipping the run must never
    # quiet the red. The component IS red and rung 3 says a red is one standing trouble; if
    # a hand cleared that trouble while the red persisted, silence here would be the door
    # laundering a red into nothing. Raising folds on identity, so the standing case costs
    # one no-op and the cleared case is corrected.
    stale = before["seal"] or {}
    if skip_settled and stale.get("verdict") and stale["verdict"] != GREEN:
        recorded = (stale.get("evidence") or {}).get("source_fingerprint")
        try:
            current = sealed_fingerprint_now(str(proof), stale)
        except Exception:
            current = None
        if recorded and current and recorded == current:
            identity = trouble_identity(proof)
            try:
                _raise(raiser, identity, why=(
                    f"{rel} is sealed RED and nothing in the closure that red was taken over "
                    f"has moved since, so the door did not re-run it — the answer is already "
                    f"taken from these exact bytes (Law 1). It will run again the moment a "
                    f"repair moves the fingerprint. Standing red: {stale.get('date')}."),
                    detail={"proof": rel, "component": _rel(component_root_for(str(proof))),
                            "rung": 1, "settled": True, "sealed": stale.get("date"),
                            "source_fingerprint": recorded})
            except Exception:
                pass
            return {"proof": rel, "outcome": "settled-red", "rung": 1, "ran": False,
                    "trouble": identity, "why": (
                        f"sealed red on {stale.get('date')} and the closure has not moved "
                        f"since — re-running would re-derive a settled answer (Law 1)")}

    tester = tester or TesterDevice()
    iso = isolation or "none"
    # THE RUN. Everything below disposes of THIS record; nothing below can produce a seal
    # without it (the ticket's WRONG INTENT clause, in one line of control flow).
    # this door seals (persist_validation below), so it sweeps first (ticket 201a37bf1613)
    record = tester.run_proof(proof, sink="none", caller=CALLER, timeout=timeout,
                             isolation=iso, scratch_sweep=sweep_scratch())
    evidence = dict(record.get("evidence") or {})
    identity = trouble_identity(proof)

    # ── A TIMEOUT IS NOT A RED THE DOOR MAY RECORD ────────────────────────────────────
    # Measured 2026-09-09, on this door's own component: `test_hollow.py`'s live tooth takes
    # 364s and the door's default budget is 120s. The tester correctly reads a hang as RED —
    # "we measured a timeout, we did not measure a pass" — and for `cairn test --seal` that is
    # the whole answer. Here it is not, because THIS door does four more things with a red:
    # it replaces the standing record, bounds a repair to the proof's current bytes, opens a
    # ladder, and files a trouble. Doing all four off the door's own impatience would
    # manufacture the exact defect the door exists to detect, and the repair it demanded
    # would be for a proof that was never broken.
    #
    # No seal records how long its run took (measured: 177 records, zero durations), so the
    # door cannot size a budget from the standing green. What it CAN do is tell a timeout
    # apart — the runner returns verdict TIMEOUT for it (ticket 3dfceaa272ec) — and decline to write.
    #
    # DECLINING TO WRITE IS NOT LAUNDERING. The stale green stays on disk and `standing()`
    # keeps reading it not-proven, because the fingerprint that expired is what brought us
    # here; the component stays red at rung 1 either way. The only thing that does not happen
    # is the door adding a verdict it did not earn. The trouble still fires, saying which of
    # the two things happened (Law 7: loud at a diagnostic surface).
    #   -> ticket: a-seal-record-carries-how-long-its-run-took
    timed_out = record["verdict"] == TIMEOUT  # the runner says it outright (ticket 3dfceaa272ec)
    if timed_out:
        # the budget the run actually used: a proof's own PROOF_TIMEOUT_S beats --timeout
        budget = (evidence.get("conditions") or {}).get("timeout", timeout)
        try:
            _raise(raiser, identity, why=(
                f"the reseal door could not REPROVE {rel} inside its {budget}s budget — it "
                f"timed out. This is the door's impatience, not the proof's verdict, so no "
                f"seal was written and no repair was bounded: the standing record is "
                f"untouched and the component stays red at rung 1 because its fingerprint "
                f"moved. Declare PROOF_TIMEOUT_S in the proof (ticket 8383a32d20c5), or "
                f"re-run an undeclared proof with a bigger --timeout, to learn what the proof "
                f"actually says."),
                detail={"proof": rel, "component": _rel(component_root_for(str(proof))),
                        "isolation": iso, "timeout": budget, "rung": 3,
                        "stderr_tail": evidence.get("stderr_tail")})
        except Exception:  # noqa: BLE001 — see the raise/clear lanes below
            pass
        return {"proof": rel, "outcome": "timeout", "rung": 3, "ran": True,
                "trouble": identity, "stderr_tail": evidence.get("stderr_tail"),
                "why": f"timed out after {budget}s under isolation {iso!r}; nothing was written"}

    # ── A SEAL OVER BYTES NO CHECKOUT WRITES IS REFUSED, green or red (ticket 8cc2a5752b6a) ──
    # Either verdict would land a fingerprint of working bytes git calls unchanged but no commit
    # carries, which no other box reproduces. Nothing is written; the refusal names the files.
    _closure = evidence.get("fingerprint_closure")
    if _closure:
        from cairn.devices.tester.working_bytes import refusal_text, unnormalized
        _top = subprocess.run(["git", "-C", str(proof.parent), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True)
        _stale = unnormalized(_closure, Path(_top.stdout.strip())) if _top.returncode == 0 else []
        if _stale:
            raise ResealRefused(f"{rel}: " + refusal_text(_stale))

    if record["verdict"] == GREEN:
        # ── RUNG 2 CLOSES (or rung 4 does, when a ruling rode along) ──────────────────
        if ruling_id:
            evidence["reseal_ruling"] = ruling_id
        if ladder:
            evidence["reseal_closed"] = {**ladder, "closed_at": _now(), "closed_by": CALLER,
                                         "closed_proof_sha256": now_hash}
        # this door seals greens too, so a green over a red measured under other conditions
        # notifies here exactly as it does through run_proof (ticket f0aad0cd0f56, D9)
        sealed = {**record, "evidence": evidence}
        compare(sealed, proof)
        persist_validation(sealed, proof_path=str(proof), unsealing_because=NETWORK_SEAL_RETIRED)
        # ONE KEY PER PROOF, CLEARED ONLY WHERE IT STANDS (ticket 87f0fc7b3514). Siblings
        # carry their own keys now, so 86b6bf19ed2a's sibling gate has nothing to hold; the
        # unreproduced siblings are still named in the result, as information.
        still = unreproduced_siblings(proof)
        if _stands_raised(raiser, identity, ladder):
            try:
                raiser.clear_trouble(identity, by=CLEARS_FOR, what_changed=(
                    f"{CALLER}: {rel} ran green and its seal was landed through the store's "
                    f"door"))
                _RAISED_THIS_RUN.discard(identity)
            except Exception:  # noqa: BLE001 — a lane we cannot reach leaves the trouble standing
                pass           #   (loud and wrong beats quiet and wrong; Law 7)
        return {"proof": rel, "outcome": "resealed" if ladder or before["seal"] else "sealed",
                "rung": 4 if ruling_id else (2 if ladder else 1), "ran": True,
                "ruling": ruling_id, "ladder_closed": bool(ladder),
                "still_unreproduced": still,
                "why": f"ran green under isolation {iso!r}; the seal was replaced"
                       + (f" — unreproduced siblings: {', '.join(still)}"
                          if still else "")}

    # ── RUNG 3: the red stands, and it becomes attention ──────────────────────────────
    # THE BOUND IS TODAY'S HASH, AND THE CARRY-FORWARD IT REPLACED WAS DEAD CODE — told
    # apart by a mutation test, 2026-09-09. This line first read
    # `bound = (ladder or {}).get("proof_sha256") or now_hash`, on the reasoning that the
    # store REPLACES so a re-bound repair is no bound at all. Both halves of that were
    # wrong, and neither could be seen by reading:
    #
    #   Unruled: rung 4 above has ALREADY REFUSED every case where the proof moved, so
    #     reaching here without a ruling guarantees `now_hash == ladder["proof_sha256"]`.
    #     The carry-forward and the re-take are the same number — the branch never differed.
    #   Ruled: Akien said the proof's claim may change, and it did. Carrying the OLD hash
    #     forward makes the NEXT pass refuse over a change he has already ruled on, so his
    #     ruling buys exactly one pass and then evaporates. Re-basing is what a ruling MEANS.
    #
    # So the bound the ladder needs is "the bytes the next repair must leave alone", and on
    # every reachable path that is the bytes on disk right now. A conditional whose other
    # branch cannot be taken is not a safeguard, it is a claim about the design that the
    # design does not make (the proof's tooth 4 pins the ruled half so this cannot silently
    # revert).
    #
    # `opened` is the opposite kind of thing and is carried forward explicitly: it is WHEN
    # the component stopped reproducing, which is provenance, not state. A ruling changes
    # what the repair is bounded TO; it never changes when the trouble started.
    opened = (ladder or {}).get("opened") or _now()
    bound = now_hash
    evidence["reseal_ladder"] = {
        "proof_sha256": bound,
        "opened": opened,
        "last_red": _now(),
        "passes": int((ladder or {}).get("passes", 0)) + 1,
        "rung": 3,
        "trouble": identity,
        "ruling": ruling_id,
    }
    persist_validation({**record, "evidence": evidence}, proof_path=str(proof),
                       unsealing_because=NETWORK_SEAL_RETIRED)
    tail = evidence.get("stderr_tail") or evidence.get("stdout_tail") or ""
    try:
        _raise(raiser, identity, why=(
            f"a sealed green stopped reproducing and the reseal did not repair it: {rel} exited "
            f"{evidence.get('returncode')} under isolation {iso!r}. The repair is bounded to a "
            f"proof file hashing {bound[:12]}… — any change leaving those bytes alone reseals "
            f"green on the next pass. A change to the proof itself needs a ruling from Akien "
            f"(rung 4). Opened {opened}."),
            detail={"proof": rel, "component": _rel(component_root_for(str(proof))),
                    "returncode": evidence.get("returncode"), "isolation": iso,
                    "proof_sha256": bound, "opened": opened, "rung": 3,
                    "stderr_tail": tail})
    except Exception:  # noqa: BLE001 — see clear_trouble above; the seal is the record of truth
        pass
    return {"proof": rel, "outcome": "red", "rung": 3, "ran": True, "trouble": identity,
            "proof_sha256": bound, "stderr_tail": tail,
            "why": f"ran red (exit {evidence.get('returncode')}) under isolation {iso!r}"}


# A RESEAL THAT COULD NOT RUN IS A RECORD, NOT A SCROLLED TRACEBACK. The hook never blocks on
# what the reseal measures (Akien 2026-09-30), so it runs the reseal under `|| true`; that also
# swallowed a crash of the run itself. Measured 2026-11-12: a full /tmp crashed it and the commit
# landed rc 0 with no seals staged and nothing anywhere saying why. Law 7 wants the crash
# permanent in a record, and a trouble is the record this door already raises; the commit still
# lands. ONE key for the whole run: a crash is the run's, not any proof's.
RUN_CRASH_IDENTITY = "tester-reseal-could-not-run"


def run_or_record(run, *, raiser=None, standing=None) -> int:
    """``run()``'s exit code, or 3 when it raised — after printing the traceback and raising
    ``RUN_CRASH_IDENTITY``. A run that completes clears that trouble if it stands.

    ``standing`` answers "does the crash trouble stand?"; it defaults to the trouble store's
    published ``live()``. A holder it cannot read leaves the trouble standing (loud and wrong
    beats quiet and wrong). KeyboardInterrupt and SystemExit pass through: a kill is
    143e3974647b's, and the next run adopts what it left."""
    import traceback
    if raiser is None:
        from cairn.tools.base.diagnostic import ModuleRaiser
        raiser = ModuleRaiser("tester")
    try:
        code = run()
    except Exception as exc:  # noqa: BLE001 — this IS the record of an unexpected failure
        tail = traceback.format_exc()
        print(tail, file=sys.stderr, end="")
        print(f"reseal: COULD NOT RUN — {type(exc).__name__}: {exc}. No seal was staged; trouble "
              f"{RUN_CRASH_IDENTITY} raised. The commit is not blocked (Akien 2026-09-30).",
              file=sys.stderr)
        try:
            _raise(raiser, RUN_CRASH_IDENTITY, why=(
                f"{CALLER} could not run: {type(exc).__name__}: {exc}. The commit it was "
                f"attached to landed without the seals it would have staged, so the components "
                f"it touched read red until a reseal completes."),
                detail={"error": type(exc).__name__, "message": str(exc),
                        "traceback_tail": tail[-4000:]})
        except Exception:  # noqa: BLE001 — the traceback above is still on the surface
            print(f"reseal: and the trouble could not be raised either", file=sys.stderr)
        return 3
    if standing is None:
        def standing():
            try:
                from cairn.devices.trouble.tools.store.store import live
                return RUN_CRASH_IDENTITY in {t.get("id") for t in live()}
            except Exception:  # noqa: BLE001 — unreadable holder: leave it standing
                return False
    if standing():
        try:
            raiser.clear_trouble(RUN_CRASH_IDENTITY, by=CLEARS_FOR, what_changed=(
                f"{CALLER} ran to completion again"))
            _RAISED_THIS_RUN.discard(RUN_CRASH_IDENTITY)
        except Exception:  # noqa: BLE001 — a lane we cannot reach leaves the trouble standing
            pass
    return code


def hollow_tickets(proof_path) -> set[str]:
    """The tickets whose hollow reading rides this proof's STANDING validation."""
    trail = read_validations(str(proof_path))
    hollow = ((trail[-1].get("evidence") or {}).get("hollow") if trail else None)
    return set(hollow) if isinstance(hollow, dict) else set()


def voided_hollows(proof_path, before: set[str]) -> list[str]:
    """The tickets in ``before`` whose hollow reading the seal just taken no longer carries.

    WHY IT IS SAID AND NOT REFUSED (ticket d5a05b6d1752). ``persist_validation`` carries
    ``evidence.hollow`` forward only while the fingerprint is unchanged, so a seal over moved
    code drops the reading, and that is right (Law 3: the code it measured is gone). Refusing
    would block a legitimate reseal. What was missing, measured 2026-11-12 at n=5, is the ticket
    being told: its next PROVED crossing bounced to FIXME on ``hollow_evidence_absent`` with
    nobody having said the reading was gone."""
    return sorted(before - hollow_tickets(proof_path))


def hollow_voided_lines(rel, tickets: list[str]) -> list[str]:
    """The lines a seal writer prints for a proof whose seal voided ``tickets``' hollow."""
    return [f"\n─── HOLLOW VOIDED: {rel} " + "─" * 20,
            f"    this seal replaced the one the hollow reading of {', '.join(tickets)} was taken "
            f"over, and the code moved, so the reading expired with it (Law 3).",
            *(f"    {t}: its PROVED crossing will bounce on hollow_evidence_absent; after PROVEME, "
              f"retake it: cairn test --hollow {t} --seal" for t in tickets)]


def reseal_all(proofs, *, ruling_id: str | None = None, tester=None, raiser=None,
               skip_settled: bool = False, timeout: int = 120,
               index_only: bool = False, trouble_root=None) -> dict:
    """Every proof in ``proofs`` through the ladder; a refusal on one does not end the run.

    The same lean as a batch run: one proof whose reseal is refused is not a reason to lose
    the readings of the fifty after it. The refusals come back as data and the caller decides
    the exit code."""
    results, refusals = [], []
    for proof in proofs:
        try:
            before = hollow_tickets(proof)
            r = reseal(proof, ruling_id=ruling_id, tester=tester, raiser=raiser,
                       skip_settled=skip_settled, timeout=timeout,
                       index_only=index_only, trouble_root=trouble_root)
            r["hollow_voided"] = voided_hollows(proof, before)
            results.append(r)
        except ResealRefused as refusal:
            refusals.append({"proof": _rel(proof), "refusal": str(refusal)})
    counts = {}
    for r in results:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    return {"results": results, "refusals": refusals, "counts": counts,
            "red": [r for r in results if r["outcome"] == "red"]}


def dirty_against_index(proof_rel: str, closure: list[str] | None, base: Path) -> list[str]:
    """The files of a proof's closure (the component root when no seal records one) and the
    proof itself that carry an unstaged change or are untracked under ``base``, sorted.

    ONE PREDICATE, TWO CALLERS (ticket 42075a49c121): ``reseal(index_only=True)`` asks it
    before the run and ``stage_clean_seals`` after, so the hold and the stage cannot
    disagree about what the commit carries."""
    files = list(closure) if closure is not None else [
        os.path.relpath(component_root_for(str(base / proof_rel)), base)]
    files.append(proof_rel)
    dirty = subprocess.run(["git", "-C", str(base), "diff", "--name-only", "--", *files],
                           capture_output=True, text=True).stdout.split()
    untracked = subprocess.run(["git", "-C", str(base), "ls-files", "--others",
                                "--exclude-standard", "--", *files],
                               capture_output=True, text=True).stdout.split()
    # AND THE BYTES GIT CALLS UNCHANGED BUT NO CHECKOUT WRITES (ticket 8cc2a5752b6a): git diff
    # cleans before it compares, so a working copy left CRLF by a checkout taken before an eol
    # pin reads clean here, and its seal would fingerprint bytes no commit carries.
    from cairn.devices.tester.working_bytes import unnormalized
    stale = unnormalized(files, base)
    return sorted(set(dirty + untracked + stale))


def _posix_rel(path, base) -> str:
    """``path`` relative to ``base`` spelled with ``/`` — the form git and the held/staged keys use."""
    return os.path.relpath(path, base).replace(os.sep, "/")


def _differs_from_index(rel: str, base: Path) -> bool:
    """True when the file at ``rel`` is untracked or carries a change the index lacks."""
    if subprocess.run(["git", "-C", str(base), "ls-files", "--error-unmatch", "--", rel],
                      capture_output=True).returncode != 0:
        return (base / rel).exists()
    return bool(subprocess.run(["git", "-C", str(base), "diff", "--name-only", "--", rel],
                               capture_output=True, text=True).stdout.strip())


def stage_clean_seals(results, *, root: Path | None = None) -> dict:
    """Stage the seals the hook just wrote whose WHOLE closure is what the commit carries.

    THE MEASURED DEFECT (2026-09-30): the reseal proves the WORKING tree and writes its seals
    through ``persist_validation``, and nothing ever staged them — 104 validation files sat
    modified after a day of commits, each a seal over code that had long since landed. Akien:
    *"sounds like you should fix the pre-commit hook?"*

    WHY NOT STAGE EVERY SEAL. A seal is a claim about the bytes its proof loaded. If one of
    those files still differs from the index, the seal describes a tree this commit does not
    carry, and committing it would put a false green in the record (Law 8). So a seal is
    staged only when every file in its closure — and the proof itself — has no unstaged
    change and nothing untracked; the rest stay in the working tree, as they must, and seal
    again on the commit that carries their code.

    The artifact journal goes in with them: it is what lets ``cairn artifact check`` see that
    the staged validation bytes came through the door."""
    base = Path(root or REPO_ROOT)
    staged, held = [], []
    for r in results:
        # A HOLD BEFORE THE RUN (ticket 42075a49c121) wrote nothing, so there is nothing to
        # stage — but it is listed, so the hook's HELD line names what the commit lacks.
        if r.get("outcome") == "held":
            held.append({"validation": _posix_rel(validations_path_for(str(base / r["proof"])), base),
                         "because": r["because"]})
            continue
        # A RED IS STAGED TOO: the door seals its red (Law 7), and a red over the committed tree
        # is as true a record as a green. settled-red and timeout write nothing, so nothing moves.
        # AN UNCHANGED SEAL CAN BE A KILLED RUN'S LEFTOVER (ticket 143e3974647b): a run killed
        # after writing a seal and before this stage leaves it unstaged, and the next run reads
        # it ``unchanged`` because its fingerprint still reproduces. That seal is adopted here,
        # under the same clean-closure test, so the next clearance is not refused for it. A
        # non-reproducing leftover never reads ``unchanged``; it re-runs and its new seal stages.
        outcome = r.get("outcome")
        if outcome not in ("resealed", "sealed", "red", "unchanged"):
            continue
        proof = base / r["proof"]
        if outcome == "unchanged" and not _differs_from_index(
                _posix_rel(validations_path_for(str(proof)), base), base):
            continue
        trail = read_validations(str(proof))
        if not trail:
            continue
        closure = closure_of(trail[-1])
        dirty = dirty_against_index(r["proof"], closure, base)
        validation = _posix_rel(validations_path_for(str(proof)), base)
        if dirty:
            held.append({"validation": validation, "because": dirty})
            continue
        subprocess.run(["git", "-C", str(base), "add", "--", validation], check=True)
        staged.append(validation)
    if staged:
        from cairn.tools.artifact.artifact import journal_path
        subprocess.run(["git", "-C", str(base), "add", "--",
                        os.path.relpath(journal_path(base), base)], check=True)
    return {"staged": staged, "held": held}


# ── the host seam: the pre-commit hook ────────────────────────────────────────────────

HOOK_SOURCE = Path(__file__).parent / "hooks" / "pre-commit"
_MARK = "cairn-reseal-door"


def hook_path(root: Path | None = None) -> Path:
    """Where git will look for the hook — resolved through ``--git-common-dir`` so it is the
    SHARED hooks directory from a worktree as well as from the main tree. A worktree has its
    own ``.git`` FILE and no hooks of its own; installing to ``<worktree>/.git/hooks`` would
    write a directory git never reads."""
    base = Path(root or REPO_ROOT)
    proc = subprocess.run(["git", "-C", str(base), "rev-parse", "--path-format=absolute",
                           "--git-common-dir"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"not a git repository at {base}: {proc.stderr.strip()}")
    return Path(proc.stdout.strip()) / "hooks" / "pre-commit"


def install_hook(root: Path | None = None) -> dict:
    """THE APPLY RECIPE — replayable, and re-runnable without a different result.

    A host-seam's implementation lives where git cannot see it, so the thing that is
    tracked is the recipe (CLAUDE.md: *a host-seam carries a replayable apply and a
    re-runnable verify*). The hook body is a tracked file under this component; installing
    copies it and marks it, and a second run is a no-op that says so.

    REFUSES TO CLOBBER A HOOK THAT IS NOT OURS. Someone else's pre-commit is someone else's
    work, and a tool that silently ate it would be the ownership violation this system is
    built to make impossible (Law 6)."""
    dest = hook_path(root)
    body = HOOK_SOURCE.read_text(encoding="utf-8")
    if dest.exists():
        existing = dest.read_text(encoding="utf-8", errors="replace")
        if _MARK not in existing:
            return {"installed": False, "path": str(dest), "why": (
                f"{dest} already exists and does not carry the {_MARK!r} marker — it is "
                f"somebody else's hook and this door will not overwrite it (Law 6). Merge "
                f"the body of {HOOK_SOURCE} into it by hand, or move it aside first.")}
        if existing == body:
            return {"installed": False, "path": str(dest), "why": "already installed, unchanged"}
    dest.parent.mkdir(parents=True, exist_ok=True)
    # LF on every box (ticket 383ac6351996): a shell runs this hook, and write_text would turn
    # each newline into CRLF on Windows, so one tracked source would install as two byte strings.
    dest.write_text(body, encoding="utf-8", newline="\n")
    os.chmod(dest, 0o755)
    return {"installed": True, "path": str(dest), "why": f"copied from {HOOK_SOURCE}"}


def verify_hook(root: Path | None = None) -> dict:
    """THE RE-RUNNABLE VERIFY. A host-seam's seal expires with nothing in git changing —
    the host drifts on its own — so the check has to be a live read of the host, never a
    record of having installed it once."""
    try:
        dest = hook_path(root)
    except RuntimeError as err:
        return {"green": False, "why": str(err)}
    if not dest.exists():
        return {"green": False, "path": str(dest), "why": f"no hook at {dest} — run "
                                                          f"`cairn test --reseal-install`"}
    body = dest.read_text(encoding="utf-8", errors="replace")
    if _MARK not in body:
        return {"green": False, "path": str(dest),
                "why": f"a pre-commit hook is installed at {dest} but it is not this one "
                       f"(no {_MARK!r} marker)"}
    if not os.access(dest, os.X_OK):
        return {"green": False, "path": str(dest), "why": f"{dest} is not executable — git "
                                                          f"will skip it silently"}
    if body != HOOK_SOURCE.read_text(encoding="utf-8"):
        return {"green": False, "path": str(dest),
                "why": f"{dest} has DRIFTED from {HOOK_SOURCE} — reinstall to reconcile"}
    return {"green": True, "path": str(dest), "why": "installed, executable, and identical "
                                                     "to the tracked source"}

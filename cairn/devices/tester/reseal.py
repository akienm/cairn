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
3 and 4 were a paragraph in a ruling, which is exactly the shape CLAUDE.md's IOU names:
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
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

from cairn.devices.tester.device import GREEN, TesterDevice
from cairn.devices.tester.validation_store import (
    closure_of,
    component_root_for,
    isolation_for_seal,
    persist_validation,
    read_validations,
    sealed_fingerprint_now,
    standing,
    standing_seal,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CALLER = "cairn test --reseal"

_SLUG = re.compile(r"[^a-z0-9-]+")


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


def trouble_identity(proof_path) -> str:
    """ONE TROUBLE PER COMPONENT, not per proof — the ticket's own words, and the existing
    identity scheme (``build_inspector._finding_trouble_id`` slugs the same way).

    Per-proof would file eleven troubles for one broken import, which is the flap the
    damper exists to stop arriving by a different route: eleven identities are eleven
    first-sightings, and every one of them notifies."""
    comp = _rel(component_root_for(str(proof_path)))
    return _SLUG.sub("-", f"seal-red-{comp}".lower()).strip("-")


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


def ruling_refusal(ruling_id: str) -> str | None:
    """``None`` if ``ruling_id`` names a CONFIRMED ruling; else the sentence saying why not.

    Imported lazily and read-only. The ruling store is Akien's record and this door only
    ever asks it a question — rung 4 is his, and a door that could write there would be CC
    declaring the spec changed, which is the one thing the ticket's owner line forbids.

    ``confirmed`` is the field the intake door DERIVES from his own RULED marker
    (``ruling.open_ruling``), never one an author can type — so leaning on it here is
    leaning on his words, not on a packet's self-report."""
    from cairn.machines.ruling import ruling as ruling_mod

    if not (ruling_id or "").strip():
        return "no ruling id was given"
    for record in ruling_mod.load_all():
        if record.get("id") != ruling_id:
            continue
        if not record.get("confirmed"):
            return (f"ruling {ruling_id!r} is on disk but NOT CONFIRMED — it carries no RULED "
                    f"marker in Akien's own words, so it is CC's reading of a ruling and not "
                    f"the ruling (cairn.machines.ruling.open_ruling derives `confirmed`)")
        return None
    return (f"no ruling {ruling_id!r} in {ruling_mod.store_dir()} — rung 4 is Akien's, and a "
            f"ruling id that resolves to nothing is a paragraph wearing an id")


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
    """Which censused proofs a staged change could have moved the ground under.

    ASKED PER SEAL, UNDER THAT SEAL'S OWN RECIPE — the same rule ``sealed_fingerprint_now``
    settled for the fingerprint itself. A seal carrying an import closure is touched when a
    staged file is IN that closure; a seal predating closures was taken over its component
    directory and is touched when a staged file is under that directory. Mixing the two
    would re-red the 2026-09-08 wall: one edit to ``transitions.py`` reaching 60 seals that
    never imported it."""
    base = Path(root or REPO_ROOT)
    want = set(staged)
    out = []
    for row in (rows if rows is not None else census(base)):
        proof, comp, seal = row["proof"], row["component"], row["seal"]
        closure = closure_of(seal)
        if closure:
            if want & set(closure):
                out.append(proof)
            continue
        comp_rel = str(comp.relative_to(base)) if comp.is_relative_to(base) else str(comp)
        if any(s == comp_rel or s.startswith(comp_rel + "/") for s in want):
            out.append(proof)
    return out


def reseal(proof_path, *, ruling_id: str | None = None, tester=None, raiser=None,
           skip_settled: bool = False,
           timeout: int = 120, isolation: str | None = None) -> dict:
    """ONE proof through the ladder. Runs it, then disposes of what the run measured.

    Raises ``ResealRefused`` at rung 4 — BEFORE the run, before any write — when the proof
    file has moved under an open ladder without a confirmed ruling. Refusing before the run
    is deliberate: a run whose result can only be discarded is a minute spent to learn
    nothing, and worse, its green would sit in the caller's return value looking like a
    verdict the door had merely declined to record.

    Returns ``{proof, outcome, rung, ran, why, ...}``. ``outcome`` is one of
    ``unchanged`` (rung 1 says the seal still holds — nothing ran, nothing was written),
    ``resealed`` (a run went green over an open ladder or a closed horizon),
    ``sealed`` (a first seal — the proof had none), or ``red`` (rung 3; the trouble is filed).
    """
    proof = Path(proof_path).resolve()
    rel = _rel(proof)
    ladder = read_ladder(proof)
    now_hash = proof_sha256(proof)

    # ── RUNG 4: the gate, and it is the first thing that happens ──────────────────────
    if ladder and ladder.get("proof_sha256") and ladder["proof_sha256"] != now_hash:
        why = ruling_refusal(ruling_id or "")
        if why is not None:
            raise ResealRefused(
                f"{rel}: the ladder opened {ladder.get('opened')} bounded the repair to a proof "
                f"file hashing {ladder['proof_sha256']}, and the file on disk now hashes "
                f"{now_hash}. The assertions moved, so this is not a repair — it is 'the "
                f"proof's claim no longer matches the spec', which is a RULING and Akien's "
                f"alone (ruling 2026-09-06-a-seal-that-cannot-be-reproven-is-red-then-repaired-"
                f"then-a-trouble-then-design). Refused: {why}. The component stays red until "
                f"it is reproven under one.")

    before = standing(str(proof))
    if before["proven"]:
        return {"proof": rel, "outcome": "unchanged", "rung": 1, "ran": False,
                "why": before["why"]}

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
                raiser.raise_trouble(identity, why=(
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
    iso = isolation or isolation_for_seal(standing_seal(str(proof))) or "none"
    # THE RUN. Everything below disposes of THIS record; nothing below can produce a seal
    # without it (the ticket's WRONG INTENT clause, in one line of control flow).
    record = tester.run_proof(proof, sink="none", caller=CALLER, timeout=timeout,
                             isolation=iso)
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
    # apart — `returncode is None` with the runner's own wording — and decline to write.
    #
    # DECLINING TO WRITE IS NOT LAUNDERING. The stale green stays on disk and `standing()`
    # keeps reading it not-proven, because the fingerprint that expired is what brought us
    # here; the component stays red at rung 1 either way. The only thing that does not happen
    # is the door adding a verdict it did not earn. The trouble still fires, saying which of
    # the two things happened (Law 7: loud at a diagnostic surface).
    #   -> ticket: a-seal-record-carries-how-long-its-run-took
    timed_out = (record["verdict"] != GREEN
                 and evidence.get("returncode") is None
                 and "timed out after" in str(evidence.get("stderr_tail") or ""))
    if timed_out:
        try:
            raiser.raise_trouble(identity, why=(
                f"the reseal door could not REPROVE {rel} inside its {timeout}s budget — it "
                f"timed out. This is the door's impatience, not the proof's verdict, so no "
                f"seal was written and no repair was bounded: the standing record is "
                f"untouched and the component stays red at rung 1 because its fingerprint "
                f"moved. Re-run with a bigger --timeout to learn what the proof actually "
                f"says."),
                detail={"proof": rel, "component": _rel(component_root_for(str(proof))),
                        "isolation": iso, "timeout": timeout, "rung": 3,
                        "stderr_tail": evidence.get("stderr_tail")})
        except Exception:  # noqa: BLE001 — see the raise/clear lanes below
            pass
        return {"proof": rel, "outcome": "timeout", "rung": 3, "ran": True,
                "trouble": identity, "stderr_tail": evidence.get("stderr_tail"),
                "why": f"timed out after {timeout}s under isolation {iso!r}; nothing was written"}

    if record["verdict"] == GREEN:
        # ── RUNG 2 CLOSES (or rung 4 does, when a ruling rode along) ──────────────────
        if ruling_id:
            evidence["reseal_ruling"] = ruling_id
        if ladder:
            evidence["reseal_closed"] = {**ladder, "closed_at": _now(), "closed_by": CALLER,
                                         "closed_proof_sha256": now_hash}
        persist_validation({**record, "evidence": evidence}, proof_path=str(proof))
        try:
            raiser.clear_trouble(identity, by=CALLER, what_changed=(
                f"reseal door: {rel} ran green and its seal was landed through the store's "
                f"door — the fingerprint reproduces again"))
        except Exception:  # noqa: BLE001 — a lane we cannot reach leaves the trouble standing
            pass           #   (loud and wrong beats quiet and wrong; Law 7)
        return {"proof": rel, "outcome": "resealed" if ladder or before["seal"] else "sealed",
                "rung": 4 if ruling_id else (2 if ladder else 1), "ran": True,
                "ruling": ruling_id, "ladder_closed": bool(ladder),
                "why": f"ran green under isolation {iso!r}; the seal was replaced"}

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
    persist_validation({**record, "evidence": evidence}, proof_path=str(proof))
    tail = evidence.get("stderr_tail") or evidence.get("stdout_tail") or ""
    try:
        raiser.raise_trouble(identity, why=(
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


def reseal_all(proofs, *, ruling_id: str | None = None, tester=None, raiser=None,
               skip_settled: bool = False, timeout: int = 120) -> dict:
    """Every proof in ``proofs`` through the ladder; a refusal on one does not end the run.

    Same lean as ``cairn test --seal``'s ``SealDowngradeRefused`` handling: one proof whose
    reseal is refused is not a reason to lose the readings of the fifty after it. The
    refusals come back as data and the caller decides the exit code."""
    results, refusals = [], []
    for proof in proofs:
        try:
            results.append(reseal(proof, ruling_id=ruling_id, tester=tester, raiser=raiser,
                                  skip_settled=skip_settled, timeout=timeout))
        except ResealRefused as refusal:
            refusals.append({"proof": _rel(proof), "refusal": str(refusal)})
    counts = {}
    for r in results:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    return {"results": results, "refusals": refusals, "counts": counts,
            "red": [r for r in results if r["outcome"] == "red"]}


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
    dest.write_text(body, encoding="utf-8")
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

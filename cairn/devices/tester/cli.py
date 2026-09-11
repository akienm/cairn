"""``cairn test`` — the address of the answer to "how do I run a proof here?".

Charter + why: cairn/devices/tester/intention+why.json
Ticket:        CairnCommons/tickets/superclaude-starts-itself.json

WHY THIS FILE EXISTS (measured 2026-07-30, and the measurement is the point).
A session tried to run one proof and spent four tool calls finding out how. Its FIRST
guess was ``cairn test <path>`` — the right address, and it was empty. The next three
were pytest (nothing in this repo uses pytest), a module path (absent), and finally
reading the proof to find the answer sitting in its docstring. A docstring is not an
address: you can only read it once you have already found the file, which is the thing
you were trying to do. Law 1 — a settled answer that never became structure gets
re-derived, and re-derivation is the defect. The dispatcher already fails loud and lists
its own verbs, so a verb named ``test`` turns four calls into one, for everyone, forever.

IT ROUTES THROUGH THE REAL DOOR, ON PURPOSE. Every run goes through
``TesterDevice.run_proof`` — the same notary, the same isolation machinery, the same
exit-code-is-the-verdict rule that seals a proof at the chokepoint. A convenience runner
that invoked ``python3 <proof>`` directly would be *faster to write and would lie*: green
here would not mean green there, and the divergence would surface at the sealing door
under time pressure. (This system has already paid that bill once — "seal the twelve teeth
under the tester in netns", 2026-07-29.)

IT DOES NOT SEAL UNLESS YOU SAY ``--seal``, AND IT SAYS SO WHEN IT DOESN'T. A dev command
anyone can type twenty times an hour must not be able to mint entries in a record of truth
by default — that is the difference between a DIAGNOSTIC SURFACE (loud, cheap, disposable)
and a RECORD OF TRUTH (permanent), and Law 7 turns on keeping them apart. So the flag is
off unless asked for.

But until 2026-08-16 this verb could not seal AT ALL, and that half was a defect rather
than a discipline (ticket standing-gates-the-newest-link-and-run-proof-names-its-sink).
The tester is the only hand that may mint a seal, and its one human-facing surface had no
way to land one — so a builder who needed a validation reached past the door, and six
trails now carry entries that never came through it. An affordance that is missing does
not stop the work; it routes the work around the physics.

The ANNOUNCE half matters more than the flag: a run that printed green and persisted
nothing used to be indistinguishable from one that sealed, which is how the gap stayed
invisible while it was being worked around.

    cairn test                                  every proof in the repo (seals nothing, says so)
    cairn test cairn/tools/base/proofs/test_needs.py  one proof
    cairn test cairn/tools/base                       every proof under a subtree
    cairn test --netns <path>                   under the measured network seal
    cairn test --seal <path>                    land each verdict through the store's door
    cairn test --reseal                         the four-rung ladder over what git has staged
    cairn test --reseal --ruling <id> <path>    rung 4: reseal over a proof whose bytes moved
    cairn test --reseal-install                 install the pre-commit hook that fires it
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from cairn.devices.tester.device import GREEN, TesterDevice
from cairn.devices.tester.validation_store import (
    SealDowngradeRefused,
    isolation_for_seal,
    record_hollow,
    standing_seal,
)
from cairn.tools.system_word import fold_flags

# discover() AND REPO_ROOT LIVE IN discovery.py, and they left this file for an import-graph
# reason: _announce_seals below reaches the bus, the bus client imports inference_domain, and
# cairn/tools/base/validation.py imports THIS MODULE for discover alone — which put a static
# path to an oracle inside seven gate components. Measured 2026-09-09, ticket dd8ad9702b49.
# Re-exported here so the command's public surface is exactly what it was.
from cairn.devices.tester.discovery import REPO_ROOT, discover  # noqa: E402

__all__ = ["REPO_ROOT", "discover", "main"]


def _hollow_run(args) -> int:
    """`cairn test --hollow <ticket>` — print the reversion reading and land it on the seals.

    A SEPARATE RETURN PATH, NOT A FLAG THREADED THROUGH THE BATCH LOOP. The batch runs the
    proofs a caller named; this runs the proofs a TICKET names, each of them several times,
    against a tree that is deliberately wrong. Folding the two would mean the ordinary
    `cairn test` loop carried a branch for a mode it never takes — and, worse, that a plain
    run and a hollow run could quietly share the seal-writing path, where the code under
    measurement is reverted and nothing said about it may be sealed as standing.

    WITH --seal the finding lands as `evidence.hollow[ticket]` on each named proof's own
    standing validation, through the store's one door. Without it nothing is written, and the
    closing line says so in the same words the batch uses, because a hollow reading that is
    reported and not recorded is the same non-event as a green that was never sealed.
    """
    from cairn.devices.tester.hollow import measure, HollowUnmeasurable

    try:
        finding = measure(args.hollow, repo_root=REPO_ROOT, timeout=args.timeout,
                          log=(lambda m: None) if args.quiet else print)
    except HollowUnmeasurable as why:
        # LAW 3'S DISTINCTION AT THE SURFACE: "the measurement could not be taken" exits 2,
        # the same code discover() uses for "nothing to run", and never 0. A run that could
        # not measure has not found the build sound.
        print(f"cairn test --hollow: {why}", file=sys.stderr)
        return 2

    for line in finding["reasons"]:
        print(f"  {line}")
    n_meas, n_skip = len(finding["measured"]), len(finding["skipped"])
    print(f"\n{finding['ticket']}: {n_meas} file(s) measured · {len(finding['hollow'])} hollow "
          f"· {n_skip} skipped · reverted to {finding['commit'][:12]}")

    if args.seal:
        # AN UNREADABLE FILE IS SEALED AS UNREADABLE, NEVER AS A TOOTH LIST.
        # ``measured[rel]`` is set for every file the run touched, INCLUDING the ones whose
        # proof printed no teeth at all — it never reached a check (a broken import, a
        # timeout, a crash) rather than failing a tooth. For those the
        # tooth list is whatever survived, and it is meaningless — hollow.measure says so
        # loudly ("NOT COUNTED AS HOLLOW, AND NOT COUNTED AS COVERED"), reds the verdict, and
        # names them in `unran`. Sealing `measured` alone dropped that distinction on the way
        # to the gate: ``hollow_lacks`` reds an ABSENT key and an EMPTY list and nothing else,
        # so a file with a non-empty leftover list read as COVERED — the instrument refusing
        # to call it evidence, and the gate that reads the instrument's own record calling it
        # earned. Measured 2026-09-09 on this ticket's own reading: two files, both of them
        # the seam under test. That is a hollow green between two of our own parts, which is
        # the exact shape Law 8 names, so the marker rides the record and the gate reads it.
        reading = {f: t for f, t in finding["measured"].items()}
        for f, broke in finding["unran"].items():
            reading[f] = {"unreadable": sorted(broke)}
        persisted = 0
        for rel in finding["proofs"]:
            landed = record_hollow(str(REPO_ROOT / rel), finding["ticket"], reading)
            persisted += 1 if landed else 0
        print(f"SEALED — hollow evidence landed on {persisted} of {len(finding['proofs'])} "
              f"standing validation(s) through the store's door.")
    else:
        print("NOTHING WAS SEALED — this was a diagnostic run. Re-run with --seal to land the "
              "reading as evidence.hollow on the proofs' standing validations.")
    return 1 if finding["verdict"] == "red" else 0


def _reseal_run(args) -> int:
    """``cairn test --reseal`` — the four-rung ladder over the proofs a change touched.

    NO TARGETS MEANS THE STAGED SET, and that is the verb's real shape: the hook calls it
    with nothing, because git already knows what changed. Named targets are the direct call
    the ticket's falsifier (5) admits beside the hook — the two reachable entrances, and
    there is no third.
    """
    from cairn.devices.tester import reseal as door

    if args.targets:
        proofs = [p.resolve() for p in discover(args.targets)]
        scope = f"{len(proofs)} named proof(s)"
    else:
        staged = door.staged_files()
        proofs = door.proofs_touching(staged)
        scope = f"{len(proofs)} proof(s) sealed over {len(staged)} staged file(s)"
    if not proofs:
        print(f"reseal: nothing to reprove ({scope}).")
        return 0

    print(f"reseal: {scope} — running each and disposing of what it measures.")
    # NAMED TARGETS ALWAYS RUN. No targets is the hook, and the hook is the automatic
    # caller Law 1 is about; a hand that types a proof name is asking for that proof.
    outcome = door.reseal_all(proofs, ruling_id=args.ruling, timeout=args.timeout,
                              skip_settled=not args.targets)
    for r in outcome["results"]:
        if r["outcome"] == "unchanged":
            if not args.quiet:
                print(f"  ok      {r['proof']}  (seal still reproduces)")
        elif r["outcome"] == "red":
            print(f"  RED     {r['proof']}  (rung 3 — trouble {r['trouble']})")
        elif r["outcome"] == "settled-red":
            # STILL RED, and printed in the red column — the door skipped the RUN, not the
            # VERDICT. Printing this as "ok" would be the surface laundering a standing red
            # into a pass because nothing happened to change it (Law 7).
            print(f"  RED     {r['proof']}  (rung 1 — settled; {r['why']})")
        elif r["outcome"] == "timeout":
            # NEITHER GREEN NOR RED, and printed as neither. The door could not reprove it
            # inside the budget, so nothing was written; collapsing that into either column
            # would be a diagnostic surface reporting a verdict nobody measured (Law 7).
            print(f"  TIMEOUT {r['proof']}  ({r['why']})")
        else:
            print(f"  RESEAL  {r['proof']}  (rung {r['rung']})")
    for red in outcome["red"]:
        print(f"\n─── RUNG 3: {red['proof']} " + "─" * 20)
        for line in (red.get("stderr_tail") or "").splitlines():
            print(f"    {line}")
    for refusal in outcome["refusals"]:
        print(f"\n─── RUNG 4 REFUSED: {refusal['proof']} " + "─" * 20)
        for line in refusal["refusal"].splitlines():
            print(f"    {line}")
    counts = " · ".join(f"{v} {k}" for k, v in sorted(outcome["counts"].items()))
    print(f"\nreseal: {counts or 'nothing measured'}"
          + (f" · {len(outcome['refusals'])} refused at rung 4" if outcome["refusals"] else ""))
    settled = [r for r in outcome["results"] if r["outcome"] == "settled-red"]
    timeouts = [r for r in outcome["results"] if r["outcome"] == "timeout"]
    if timeouts:
        print(f"reseal: {len(timeouts)} proof(s) could not be reproven inside "
              f"{args.timeout}s — re-run those with a bigger --timeout.")
    if settled:
        print(f"reseal: {len(settled)} proof(s) are sealed RED over an unmoved closure — the "
              f"door did not re-run them because the answer is already taken (Law 1); they "
              f"run again when a repair moves the fingerprint.")
    # A SETTLED RED EXITS 1. The component is red; that the door saved itself a run does not
    # make it green, and an exit code that said otherwise would be the cheapest possible
    # place to lose a standing red.
    return 1 if (outcome["red"] or outcome["refusals"] or timeouts or settled) else 0


def _reseal_hook_admin(args) -> int:
    """Install or verify the pre-commit hook — the host-seam's apply and its re-runnable
    verify, at the same address as the door they fire (Law 5)."""
    from cairn.devices.tester import reseal as door

    if args.reseal_install:
        got = door.install_hook()
        print(("installed " if got["installed"] else "not installed ") + got["path"])
        print(f"  {got['why']}")
        return 0 if got["installed"] or "already installed" in got["why"] else 1
    got = door.verify_hook()
    print(("green  " if got["green"] else "RED    ") + got.get("path", ""))
    print(f"  {got['why']}")
    return 0 if got["green"] else 1


# --- THE SEAL ANNOUNCES ITSELF -------------------------------------------------------
#
# THE MEASURED DEFECT (2026-09-07, ticket 1accdc1781aa): twelve tickets sat at
# ``PROVEME:waiting`` with a green seal already standing on the proof they named. The seal
# was minted here and then sat still, because the only thing that could turn a green into a
# crossing was a mind remembering to go and do it. The operator's lived symptom is the one
# that matters: the inbox said nineteen waiting and the true number of boats actually
# needing a human was unknowable without opening every one.
#
# SENDING IS A TOOL; CODEMOTHER OWNS WHAT HAPPENS. This function announces a fact — this
# proof sealed, this verdict, this fingerprint, this record — and stops. It does not decide
# which boats move, does not cross anything, and cannot: it names no ticket. CodeMother owns
# the care of the code (ruled 2026-09-06) and the harbor owns the door; the tester owns the
# seal, and an announcement is the whole of its reach past its own edge. That separation is
# what stops this from becoming "the tester crosses boats", which is Law 6 with the owner
# filed off.
#
# A SEND FAILURE NEVER UNWINDS A SEAL, and the order is the same one ``persist_validation``
# settled for its verdict-change trouble: THE NEW MEASUREMENT OUTRANKS THE ANNOUNCEMENT. The
# record of truth landed through the store's door before this line ran. If the bus is down,
# codemother is unreachable, or the wiring raises, the failure is emitted on the tester's own
# trail (loud — Law 7) and the command's exit code is untouched. Losing a seal because
# nobody was listening would be the diagnostic surface eating the record.
#
# AND IT POSTS RATHER THAN ASKS. ``post`` drops the envelope in the bus store; if codemother
# is not up, her next beat drains it (device-owns-its-subscription — the bus is a store, not
# a router). ``request`` would block this command on her crossings, which are not its work.
def _announce_seals(tester, sealed_green: list) -> None:
    """Tell codemother about every green seal this run landed. Never raises."""
    if not sealed_green:
        return
    try:
        # ``reach`` and NOT ``connect_bus``, which is what the ticket's HOW named: a beat
        # costs ~23.5s on this machine and the probe at
        # ``tools/base/probes/a_client_reaches_and_never_beats.py`` reds any client that
        # pays it. A sealing run is a client — it wants one device to hear one thing.
        from cairn.tools.bus_client import reach
        # ``validations_path_for`` AND NOT ``..._for_artifact``, MEASURED 2026-09-09. The
        # artifact form is for a thing with no ``proofs/`` directory and derives
        # ``<dir>/validations/<stem>.json`` — applied to a PROOF that reads
        # ``<comp>/proofs/validations/<stem>.json``, one directory too deep and not where
        # the seal just landed. The message would have carried a field naming nothing on
        # disk, and a receiver has no way to tell that from a real address (Law 7: a record
        # of truth never collapses an error into a coherent shape).
        from cairn.devices.tester.validation_store import validations_path_for

        # REACHING CODEMOTHER ALONE MADE THE CROSSING IMPOSSIBLE, MEASURED 2026-09-09 ON
        # THE FIRST LIVE FIRE OF THIS SEAM. ``reach`` wires a delivery hook for each device
        # it names, and ``post`` fires that hook SYNCHRONOUSLY, in this process — so
        # codemother heard the seal here rather than on her own beat, and here the harbor
        # was not wired. She refused every boat, correctly and loudly at her own trail:
        # "'harbor_master' is not wired on this bus, so there is no door to knock on.
        # Wired: ['codemother']. Reach it first: reach('codemother', 'harbor_master')".
        # The command printed a clean SEALED and the ticket did not move. Reaching only the
        # device you are ADDRESSING is the natural reading of ``reach``, and it is wrong
        # here: the announcement sets a crossing in motion, and the door that crossing
        # knocks on has to be wired wherever the handler ends up running. So this names
        # both — the receiver and the door it will use — which is what the message actually
        # costs. It is still one exchange and no heartbeat: two shims pulsed, ~0.5s.
        bus = reach("codemother", "harbor_master")
        for proof, record in sealed_green:
            evidence = record.get("evidence") or {}
            bus.post(
                sender="tester", to="codemother", channel="personal", verb="sealed",
                why=f"a green seal landed on {proof}",
                body={"proof": str(proof),
                      "verdict": record.get("verdict", ""),
                      "source_fingerprint": evidence.get("source_fingerprint", ""),
                      "validations_path": validations_path_for(str(proof))},
            )
        # AND THE RING IS FLUSHED BEFORE THIS PROCESS DIES. ``post`` appends to an
        # in-memory ring and the ground loop's beat is what batch-writes it; a beat is the
        # one thing a sealing run never fires. So an envelope that was NOT handled by the
        # synchronous hook — codemother down, her shim unloadable, a handler that raised —
        # lived only in this process and went with it. "Her next beat drains the mail" was
        # true of the mail directory and false of the bus store, and the store is where
        # ``_check_mail`` looks (``bus.undelivered``). Measured the same run: the sealed
        # envelope was in no channel afterwards at all. Flushing costs one transaction and
        # is what makes the post a STORE rather than a hope.
        bus.flush()
    except Exception as exc:  # noqa: BLE001 — the seal already landed; this is the telling
        tester.emit("sealed_announce_failed", pointer=str(len(sealed_green)),
                    values={"error": f"{type(exc).__name__}: {exc}",
                            "unannounced": [str(one) for one, _ in sealed_green]})
        print(f"  (the {len(sealed_green)} green seal(s) landed, but codemother could not be "
              f"told: {type(exc).__name__}: {exc} — the seals stand; the crossings they "
              f"would have fired did not)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="cairn test",
        description="Run proofs through the tester and report the verdicts. "
                    "Seals nothing unless --seal.",
    )
    ap.add_argument("targets", nargs="*", help="proof files or directories (default: the whole repo)")
    ap.add_argument(
        "--netns",
        action="store_true",
        help="run under the measured network seal (tester default is bare, asked for by name)",
    )
    ap.add_argument(
        "--seal",
        action="store_true",
        help="persist each verdict as a VALIDATION through the store's door "
             "(default: run and report only, sealing nothing)",
    )
    ap.add_argument("--timeout", type=int, default=120, help="per-proof timeout in seconds (default 120)")
    ap.add_argument(
        "--hollow",
        metavar="TICKET",
        help="measure whether this ticket's build is load-bearing: revert each file its "
             "decompose berth names, in a scratch worktree, and report which declared teeth "
             "go red. A file that reds none is named and the run exits non-zero.",
    )
    ap.add_argument(
        "--reseal",
        action="store_true",
        help="run the four-rung ladder over the proofs a staged change touched (or over "
             "the named targets): rerun, reseal a green, bound the repair to the proof "
             "file's hash, file one trouble per component, refuse a moved proof without a ruling",
    )
    ap.add_argument(
        "--ruling",
        metavar="ID",
        help="rung 4: the CONFIRMED ruling id that lets a reseal land over a proof file "
             "whose bytes have moved. Akien's alone — 'the proof's claim no longer matches "
             "the spec' is a ruling, never a declaration",
    )
    ap.add_argument("--reseal-install", action="store_true",
                    help="install the reseal door's git pre-commit hook (idempotent; "
                         "refuses to overwrite a hook that is not this one)")
    ap.add_argument("--reseal-verify", action="store_true",
                    help="re-read the host: is the pre-commit hook installed, executable, "
                         "and identical to the tracked source?")
    ap.add_argument("-q", "--quiet", action="store_true", help="only print reds and the summary")
    # flags are system words and fold; targets are paths and ride verbatim (ruled 2026-09-07)
    args = ap.parse_args(fold_flags(sys.argv[1:] if argv is None else argv))

    if args.reseal_install or args.reseal_verify:
        return _reseal_hook_admin(args)

    if args.reseal:
        return _reseal_run(args)

    if args.hollow:
        return _hollow_run(args)

    proofs = discover(args.targets)
    if not proofs:
        print("cairn test: found no proofs to run", file=sys.stderr)
        return 2

    tester = TesterDevice()
    sink = "validations" if args.seal else "none"
    reds: list[tuple[Path, dict]] = []
    refused: list[tuple[Path, str]] = []
    persisted = 0
    # WHAT SEAL EACH PERSISTED RECORD ACTUALLY CARRIES (ticket 481221f45884). The count alone
    # cannot tell a record taken under a netns from one taken with the route wide open, and the
    # closing line used to print the count under the single word SEALED. Read off the record the
    # store just took, so it costs nothing and cannot disagree with what landed.
    persisted_seals: Counter[str] = Counter()
    sealed_green: list[tuple[Path, dict]] = []
    isolations: Counter[str] = Counter()

    def isolation_for(proof: Path) -> str:
        """WHICH SEAL THIS PROOF RE-RUNS UNDER — asked per proof, not hoisted out of the loop.

        The old line was ``isolation = "netns" if args.netns else "none"``, ONCE, above the
        loop, and it is what made 2026-09-08's blanket re-seal reddening three proofs possible:
        one flag decided for every proof in the corpus, so a sweep that meant "re-seal these"
        also silently meant "and change how they are sealed". Three of them could not honestly
        run inside a netns at all, and the seal measurement that said so was overwritten by one
        that said nobody had asked.

        So a sealing run asks each proof's standing validation what isolation its seal was
        taken at and reproduces THAT. ``--netns`` still wins outright — an explicit ask
        outranks a standing record, because that is the only way to seal something the first
        time. A proof that has never been sealed has nothing to reproduce and runs bare, which
        is this command's documented default.

        A DIAGNOSTIC RUN IS UNCHANGED, deliberately. Without ``--seal`` nothing lands in a
        record of truth, so there is nothing to preserve; widening the per-proof read to every
        run would be a change to what a plain ``cairn test`` COSTS, and that is outside that
        ticket's bounds.

        AND A FIRST SEAL IS TAKEN UNDER THE SEAL (ticket 481221f45884). The clause above used
        to end "runs bare, which is this command's documented default" — and that made every
        proof's FIRST seal the weakest one it would ever get. The record that landed said
        ``seal: {verdict: "open"}``, which in this device's vocabulary means *nobody asked*
        (isolation.py: "not asked for; the route is open by construction, said so"). So the
        one moment a proof enters proven-space was the one moment nothing measured whether it
        could reach the network, and the validation recorded that absence as if it were a
        reading. Measured 2026-09-10 across both roots: 218 validation files, 54 of them
        standing at ``open``.

        Reproducing a standing ``open`` is still ``none`` — that is ticket 4431cf2bc625's
        guard and this branch sits BENEATH it, never over it. The change is only what happens
        when ``standing_seal`` finds nothing at all: there is no measurement to preserve, so
        the honest default is the one that MAKES a measurement rather than the one that
        records its absence. Law 9 — green is earned, and a first seal taken bare was green
        nobody had earned.

        Not a flag. The charter's eleventh falsifier clause says the instance seal must never
        become a caller's choice, and a proof that honestly needs a route now reds loudly and
        goes to Akien as a ruling, which is a route out that leaves a record. An opt-out flag
        would be the same escape with nothing written down.
        """
        if args.netns:
            return "netns"
        if args.seal:
            return isolation_for_seal(standing_seal(str(proof))) or "netns"
        return "none"

    for proof in proofs:
        rel = proof.relative_to(REPO_ROOT) if proof.is_relative_to(REPO_ROOT) else proof
        if not proof.is_file():
            print(f"  UNRUNNABLE  {proof}")
            reds.append((proof, {}))
            continue
        isolation = isolation_for(proof)
        isolations[isolation] += 1
        try:
            record = tester.run_proof(proof, sink=sink, caller="cairn test",
                                      timeout=args.timeout, isolation=isolation)
        except SealDowngradeRefused as refusal:
            # THE DOOR REFUSED THE SEAL, NOT THE PROOF, and the difference has to survive to
            # the screen. The batch continues: one proof whose seal cannot land is not a
            # reason to lose the verdicts of the fifty after it, and swallowing the refusal
            # into a stack trace would end the run at the first one (Law 7 — loud here,
            # and the run still finishes).
            print(f"  REFUSED {rel}  (ran, but the seal was refused)")
            refused.append((proof, str(refusal)))
            continue
        if sink == "validations":
            persisted += 1
            persisted_seals[(record.get("evidence", {}).get("seal") or {}).get("verdict")
                            or "no seal key"] += 1
        verdict = record["verdict"]
        if verdict == GREEN and sink == "validations":
            sealed_green.append((proof, record))
        if verdict == GREEN:
            if not args.quiet:
                seal = record["evidence"]["seal"]["verdict"]
                print(f"  green  {rel}" + (f"  [seal={seal}]" if args.netns or args.seal else ""))
        else:
            print(f"  RED    {rel}")
            reds.append((proof, record))

    # A red prints its evidence HERE, in the first run. Akien's framework: a diagnostic
    # that makes you re-run to find out why has failed at its job. The tails are the
    # tester's own captured output (last 20 lines each), not a re-derivation.
    for proof, record in reds:
        if not record:
            continue
        rel = proof.relative_to(REPO_ROOT) if proof.is_relative_to(REPO_ROOT) else proof
        ev = record["evidence"]
        print(f"\n─── RED: {rel} (exit {ev['returncode']}) " + "─" * 20)
        for stream in ("stdout_tail", "stderr_tail"):
            if ev.get(stream):
                print(f"  [{stream}]")
                for line in ev[stream].splitlines():
                    print(f"    {line}")

    total, n_red = len(proofs), len(reds)
    n_green = total - n_red - len(refused)
    # THE ISOLATION IS A DISTRIBUTION NOW, NOT A WORD. It used to print the one hoisted value,
    # which was true only because every proof got the same one. A batch that reproduces each
    # proof's own seal genuinely runs several, so the line reports what actually happened —
    # collapsing them back to one word would be a diagnostic surface stating a convenient
    # shape instead of the measurement (Law 7).
    spread = " ".join(f"{k}={v}" for k, v in sorted(isolations.items()))
    print(f"\n{total} proof{'s' if total != 1 else ''} · {n_green} green · {n_red} red"
          + (f" · {len(refused)} seal-refused" if refused else "")
          + (f" · isolation {spread}" if (args.netns or args.seal) and spread else ""))
    # THE NOT-SEALING SAYS ITSELF. This line is the half of --seal that the ticket is
    # actually about: without it, a run that printed green and persisted nothing looked
    # exactly like a run that sealed, so nobody could see the affordance was missing —
    # they could only feel it, and route around it. Printed on every run, both ways, and
    # printed LAST so it is the line still on screen when the next decision is made.
    if args.seal:
        # THE COUNT IS WHAT LANDED, NOT WHAT PASSED. Until 2026-09-09 this line printed
        # `total - n_red` in the same breath as "a red seals its red" — measured that day over
        # the corpus: 49 proofs, 6 red, the line said 43, and all 49 files were on disk. A
        # record-of-truth command miscounting the records it just wrote is a Law 7 defect in
        # one line, and it was misreporting exactly the thing this ticket is about. `persisted`
        # is now incremented once per record that actually went through the door.
        # AND THE WORD SEALED NEVER STANDS OVER A RECORD NOBODY SEALED (ticket 481221f45884).
        # This line used to print one count under one word. A run that persisted fifty records
        # of which forty carried `seal: {verdict: "open"}` — which in this device's vocabulary
        # means NOBODY ASKED — reported itself, in the last line on screen, as a sealing run.
        # That is a diagnostic surface stating a convenient shape instead of the measurement,
        # at the exact surface a builder reads before deciding this code can be leaned on
        # (Law 7, and Law 8's false-green worse-than-a-red). The verdicts ride inside the
        # records that just landed, so the split is a read of what happened, not a new claim.
        under_seal = persisted_seals.get("sealed", 0)
        spread_seals = " ".join(f"{k}={v}" for k, v in sorted(persisted_seals.items()))
        # PERSISTED, not SEALED: the count is of records that went through the door, and how
        # many of those were actually sealed is the NEXT line. The em-dash is load-bearing —
        # test_seal_is_never_silently_dropped.py reads the count off it (ticket 4431cf2bc625).
        print(f"PERSISTED — {persisted} VALIDATION(s) persisted through the store's door beside "
              f"the proofs they seal (a red seals its red; Law 7).")
        print(f"  {under_seal} of {persisted} taken UNDER THE SEAL"
              + (f" — seal {spread_seals}" if spread_seals else "")
              + (". A record reading `open` means the route was never measured, not that it "
                 "was measured shut." if persisted_seals.get("sealed", 0) != persisted else "."))
        for proof, why in refused:
            rel = proof.relative_to(REPO_ROOT) if proof.is_relative_to(REPO_ROOT) else proof
            print(f"\n─── SEAL REFUSED: {rel} " + "─" * 20)
            for line in why.splitlines():
                print(f"    {line}")
        _announce_seals(tester, sealed_green)
    else:
        print("NOTHING WAS SEALED — this was a diagnostic run. No VALIDATION was written, "
              "so nothing here has changed what `standing()` says about any of this code. "
              "Re-run with --seal to land the verdicts.")
    return 1 if (reds or refused) else 0


if __name__ == "__main__":
    raise SystemExit(main())

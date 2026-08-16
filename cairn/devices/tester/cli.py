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
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cairn.devices.tester.device import GREEN, TesterDevice

# The repo root: cairn/devices/tester/cli.py -> cairn/devices/tester -> cairn -> root
REPO_ROOT = Path(__file__).resolve().parents[3]


def discover(targets: list[str]) -> list[Path]:
    """Resolve CLI targets to proof files.

    A directory (or no argument at all, meaning the repo) expands to every
    ``*/proofs/test_*.py`` beneath it. Sorted, because an unstable run order makes an
    intermittent red impossible to attribute — the one failure mode a proof suite must
    never add on its own.
    """
    if not targets:
        targets = [str(REPO_ROOT)]
    found: list[Path] = []
    for t in targets:
        p = Path(t)
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        if p.is_file():
            found.append(p)
        elif p.is_dir():
            found.extend(p.glob("**/proofs/test_*.py"))
        else:
            # Loud, and it exits non-zero below. A typo'd path that silently ran zero
            # proofs and reported success is a hollow green (Law 8) — the worst outcome
            # this command could produce, because it looks exactly like a good one.
            print(f"cairn test: no such path: {t}", file=sys.stderr)
            found.append(Path(t))  # kept so the run reports it as unrunnable, not skipped
    # dedupe, keep determinism
    return sorted(set(found))


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
    ap.add_argument("-q", "--quiet", action="store_true", help="only print reds and the summary")
    args = ap.parse_args(argv)

    proofs = discover(args.targets)
    if not proofs:
        print("cairn test: found no proofs to run", file=sys.stderr)
        return 2

    tester = TesterDevice()
    isolation = "netns" if args.netns else "none"
    sink = "validations" if args.seal else "none"
    reds: list[tuple[Path, dict]] = []

    for proof in proofs:
        if not proof.is_file():
            print(f"  UNRUNNABLE  {proof}")
            reds.append((proof, {}))
            continue
        record = tester.run_proof(proof, sink=sink, caller="cairn test",
                                  timeout=args.timeout, isolation=isolation)
        verdict = record["verdict"]
        rel = proof.relative_to(REPO_ROOT) if proof.is_relative_to(REPO_ROOT) else proof
        if verdict == GREEN:
            if not args.quiet:
                seal = record["evidence"]["seal"]["verdict"]
                print(f"  green  {rel}" + (f"  [seal={seal}]" if args.netns else ""))
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
    print(f"\n{total} proof{'s' if total != 1 else ''} · {total - n_red} green · {n_red} red"
          + (f" · isolation={isolation}" if args.netns else ""))
    # THE NOT-SEALING SAYS ITSELF. This line is the half of --seal that the ticket is
    # actually about: without it, a run that printed green and persisted nothing looked
    # exactly like a run that sealed, so nobody could see the affordance was missing —
    # they could only feel it, and route around it. Printed on every run, both ways, and
    # printed LAST so it is the line still on screen when the next decision is made.
    if args.seal:
        print(f"SEALED — {total - n_red} VALIDATION(s) persisted through the store's door "
              f"beside the proofs they seal (a red seals its red; Law 7).")
    else:
        print("NOTHING WAS SEALED — this was a diagnostic run. No VALIDATION was written, "
              "so nothing here has changed what `standing()` says about any of this code. "
              "Re-run with --seal to land the verdicts.")
    return 1 if reds else 0


if __name__ == "__main__":
    raise SystemExit(main())

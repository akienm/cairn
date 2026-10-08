"""cairn rehearse — the rehearsal machine's command line. Every verb is one function in
rehearsal.py; this file only parses and prints.

  cairn rehearse <ticket>                                    one pass: render, three cold reads, the diff, one record
  cairn rehearse <ticket> --decide <step> "<line>" --by <who>  dispose a gap as a decision line on the ticket (step is D<n> or "unlisted: <text>")
  cairn rehearse <ticket> --proved <proof.py> [<proof.py> ...]  after PROVED: the divergence list onto the clean record
  cairn rehearse <ticket> --standing                         what the BUILDME lane reads, as JSON
  cairn rehearse <ticket> --retire D<n> [D<n> ...] --because "<why>" [--into D<m>] --by <who>
                                                             retire superseded decision lines: out of the reader's view, kept in the file
  cairn rehearse <ticket> --scope D<n> [D<n> ...] --because "<why>" --by <who>
                                                             scope decision lines as context: handed to the reader to read, never a step

Exit 0 on a clean pass; 1 on a pass with gaps (they are printed, one per line, with the
line that would settle each); 2 on a refusal or a reader failure; 3 when the pass cap opened
a question instead of reading. Flags fold case (ruled 2026-09-07); his words never do.
"""
from __future__ import annotations

import argparse
import json
import sys

from cairn.machines.rehearsal import rehearsal as R
from cairn.tools.system_word import fold


def _print_gaps(record: dict) -> None:
    for g in record.get("gaps") or []:
        line = f"  {g['kind']:19} {g['step']}  (reads {','.join(map(str, g['reads']))})"
        for k in ("assumption", "would_settle"):
            for v in g.get(k) or []:
                line += f"\n{'':22}{k}: {v}"
        print(line)


def _decision_id(p: argparse.ArgumentParser, v: str) -> int:
    """'D3', 'd3' or '3' -> 3; anything else is a usage error."""
    t = fold(v.strip())
    t = t[1:] if t.startswith("d") else t
    if not t.isdigit() or int(t) < 1:
        p.error(f"{v!r} is not a decision id (D<n>)")
    return int(t)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    argv = [fold(a) if a.startswith("--") else a for a in argv]
    p = argparse.ArgumentParser(prog="cairn rehearse", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ticket")
    p.add_argument("--decide", nargs=2, metavar=("STEP", "LINE"),
                   help="dispose the gap at STEP (D<n> or 'unlisted: <text>') as the decision LINE on the ticket")
    p.add_argument("--by", help="who made the decision (required with --decide)")
    p.add_argument("--proved", nargs="+", metavar="PROOF",
                   help="after PROVED: diff these proofs' teeth against the converged tree")
    p.add_argument("--standing", action="store_true", help="print what the BUILDME lane reads")
    p.add_argument("--retire", nargs="+", metavar="D<n>",
                   help="retire these superseded decision lines (needs --because and --by)")
    p.add_argument("--scope", nargs="+", metavar="D<n>",
                   help="scope these decision lines as context, never a step (needs --because and --by)")
    p.add_argument("--because", help="why the lines are retired or scoped (required with --retire and --scope)")
    p.add_argument("--into", metavar="D<m>", help="the live decision that supersedes them")
    p.add_argument("--json", action="store_true", help="print the record as JSON")
    args = p.parse_args(argv)
    try:
        if args.retire:
            if args.decide or args.proved or args.standing:
                p.error("--retire stands alone: not with --decide, --proved or --standing")
            if not args.by or not args.because:
                p.error("--retire needs --by <who> and --because \"<why>\"")
            ns = [_decision_id(p, v) for v in args.retire]
            into = _decision_id(p, args.into) if args.into else None
            for d in R.retire(args.ticket, ns, by=args.by, because=args.because, into=into):
                print(f"retired D{d['n']} on {args.ticket} by {d['retired']['by']}"
                      + (f" into D{into}" if into is not None else "") + f": {d['text']}")
            print("the ticket's bytes changed — rehearse again before BUILDME")
            return 0
        if args.scope:
            if args.decide or args.proved or args.standing or args.retire:
                p.error("--scope stands alone: not with --decide, --proved, --standing or --retire")
            if not args.by or not args.because:
                p.error("--scope needs --by <who> and --because \"<why>\"")
            ns = [_decision_id(p, v) for v in args.scope]
            for d in R.scope(args.ticket, ns, by=args.by, because=args.because):
                print(f"scoped D{d['n']} on {args.ticket} by {args.by}: {d['text']}")
            print("the ticket's bytes changed — rehearse again before BUILDME")
            return 0
        if args.decide:
            if not args.by:
                p.error("--decide needs --by <who> (each decision carries who made it)")
            entry = R.decide(args.ticket, args.decide[0], args.decide[1], by=args.by)
            print(f"decided D{entry['n']} on {args.ticket} at '{entry['step']}' by {entry['by']}: {entry['text']}")
            print("the ticket's bytes changed — rehearse again before BUILDME")
            return 0
        if args.proved:
            d = R.record_divergence(args.ticket, args.proved)
            print(json.dumps(d, indent=1, ensure_ascii=False) if args.json else
                  f"divergence over {args.ticket}: {len(d['steps_unproved'])} step(s) unproved, "
                  f"{len(d['teeth_unforeseen'])} tooth/teeth unforeseen, {len(d['matched'])} matched")
            for s in d["steps_unproved"]:
                print(f"  unproved step: {s}")
            for t in d["teeth_unforeseen"]:
                print(f"  unforeseen tooth: {t}")
            return 0
        if args.standing:
            print(json.dumps(R.standing(args.ticket), indent=1))
            return 0
        rec = R.rehearse(args.ticket)
        if "question" in rec:
            print(f"pass cap ({R.PASS_CAP}) reached over {args.ticket}: opened {rec['question']} "
                  f"naming {len(rec['gaps'])} standing gap(s) — answer it, then rehearse again")
            return 3
        if args.json:
            print(json.dumps(rec, indent=1, ensure_ascii=False))
        m = rec["meta"]
        print(f"pass {rec['pass']} over {args.ticket}: {'CLEAN' if rec['clean'] else str(len(rec['gaps'])) + ' gap(s)'} "
              f"— {rec['record']} (${m['cost_usd']:.4f}, {m['duration_ms'] / 1000:.1f}s, "
              f"{len(m['attempts'])} read attempt(s))")
        if rec["clean"]:
            return 0
        _print_gaps(rec)
        print(f"dispose each: cairn rehearse {args.ticket} --decide \"<step>\" \"<line>\" --by <who>  |  "
              f"cairn question open --ticket {args.ticket} \"<q?>\" --why \"...\"")
        return 1
    except R.Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

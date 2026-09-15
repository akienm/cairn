"""cairn rehearse — the rehearsal machine's command line. Every verb is one function in
rehearsal.py; this file only parses and prints.

  cairn rehearse <ticket>                                    one pass: render, three cold reads, the diff, one record
  cairn rehearse <ticket> --decide <step> "<line>" --by <who>  dispose a gap as a decision line on the ticket (step is D<n> or "unlisted: <text>")
  cairn rehearse <ticket> --proved <proof.py> [<proof.py> ...]  after PROVED: the divergence list onto the clean record
  cairn rehearse <ticket> --standing                         what the BUILDME lane reads, as JSON

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
    p.add_argument("--json", action="store_true", help="print the record as JSON")
    args = p.parse_args(argv)
    try:
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

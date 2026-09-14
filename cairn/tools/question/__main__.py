"""cairn question — the question door's command line. Every verb is one function in
question.py; this file only parses and prints.

  cairn question open --ticket <id> "<question>" --why "<what it blocks>" [--born-of <qid>]
  cairn question answer <qid> "<his words>" [--follow-up "<question>" ...]
  cairn question list [<ticket>]                   unresolved questions (for one ticket, or all)
  cairn question show <qid>
"""

from __future__ import annotations

import argparse
import json
import sys

from cairn.tools.question import question as Q
from cairn.tools.system_word import fold


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        argv[0] = fold(argv[0])  # a system word folds case (ruled 2026-09-07); his words never do
    p = argparse.ArgumentParser(prog="cairn question")
    sub = p.add_subparsers(dest="verb", required=True)
    o = sub.add_parser("open")
    o.add_argument("question")
    o.add_argument("--ticket", required=True)
    o.add_argument("--why", required=True, dest="why_it_blocks")
    o.add_argument("--born-of", dest="born_of")
    o.add_argument("--raised-by", dest="raised_by")
    a = sub.add_parser("answer")
    a.add_argument("qid")
    a.add_argument("words")
    a.add_argument("--follow-up", action="append", default=[], dest="follow_ups")
    ls = sub.add_parser("list")
    ls.add_argument("ticket", nargs="?")
    sh = sub.add_parser("show")
    sh.add_argument("qid")
    args = p.parse_args(argv)
    try:
        if args.verb == "open":
            rec = Q.open_question(args.ticket, args.question, args.why_it_blocks,
                                  raised_by=args.raised_by, born_of=args.born_of)
            print(f"question opened: {rec['id']} against {rec['ticket']}")
            return 0
        if args.verb == "answer":
            rec = Q.answer(args.qid, args.words, follow_ups=args.follow_ups)
            print(f"answered: {rec['id']} ({rec['answered_by']})")
            for f in rec["follow_ups"]:
                print(f"  follow-up opened: {f}")
            return 0
        if args.verb == "list":
            recs = Q.open_for(args.ticket) if args.ticket else Q.list_open()
            print(Q.render(recs) if recs else "no open questions")
            return 0
        if args.verb == "show":
            print(json.dumps(Q.read(args.qid), indent=2, ensure_ascii=False))
            return 0
    except (Q.Refused, Q.door.Refused) as exc:
        print(f"cairn question: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())

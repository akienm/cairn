"""cairn artifact — the door's command line. Every verb is one function in artifact.py;
this file only parses and prints, so a proof measures the module and the CLI stays thin.

  cairn artifact write <path> --verb <verb> --why '...' [--stdin | --from <file>]
  cairn artifact remove <path> --why '...'
  cairn artifact genesis <root> --why '...'      journal every standing record once
  cairn artifact check <root>                    the pre-commit question; exit 2 on refusal
  cairn artifact verify <root>                   replay the hash chain
  cairn artifact caller                          who am I, as the door would journal it
  cairn artifact hand-edit <path> --why '...'    park a change made around the door
  cairn artifact parked                          the parked edits waiting for Akien
  cairn artifact approve <id> "his words"        refused unless the caller is akien
  cairn artifact refuse <id> "words"
  cairn artifact install-hook <root>             install the blocking pre-commit check
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from cairn.tools.artifact import artifact as A

_HOOK_SRC = Path(__file__).resolve().parent / "hooks" / "pre-commit"


def _out(doc) -> None:
    print(json.dumps(doc, indent=2, ensure_ascii=False))


def _content(args) -> bytes:
    if args.stdin:
        return sys.stdin.buffer.read()
    if args.from_file:
        return Path(args.from_file).read_bytes()
    raise A.Refused("write needs --stdin or --from <file>")


def _install_hook(name: str) -> dict:
    root = A.roots()[name]
    hooks = root / ".git" / "hooks"
    if not hooks.is_dir():
        raise A.Refused(f"{root} has no .git/hooks — is it a repository?")
    dst = hooks / "pre-commit"
    if dst.exists() and A._sha(dst.read_bytes()) != A._sha(_HOOK_SRC.read_bytes()):
        text = dst.read_text(encoding="utf-8", errors="replace")
        if "artifact check" not in text:
            raise A.Refused(f"{dst} exists and is not the artifact hook — it must be composed by "
                            f"hand (the tester's hook carries the artifact check as its first "
                            f"step; see cairn/devices/tester/hooks/pre-commit)")
    shutil.copyfile(_HOOK_SRC, dst)
    dst.chmod(0o755)
    return {"installed": str(dst), "sha": A._sha(dst.read_bytes())[:12]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cairn artifact", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="verb", required=True)

    w = sub.add_parser("write"); w.add_argument("path"); w.add_argument("--verb", dest="record_verb", required=True)
    w.add_argument("--why", required=True); w.add_argument("--count", type=int, default=1)
    w.add_argument("--stdin", action="store_true"); w.add_argument("--from", dest="from_file")
    r = sub.add_parser("remove"); r.add_argument("path"); r.add_argument("--why", required=True)
    g = sub.add_parser("genesis"); g.add_argument("root"); g.add_argument("--why", required=True)
    sub.add_parser("check").add_argument("root", help="a root name, or the path of a root's toplevel")
    sub.add_parser("verify").add_argument("root")
    sub.add_parser("caller")
    sub.add_parser("locate").add_argument("path")
    h = sub.add_parser("hand-edit"); h.add_argument("path"); h.add_argument("--why", required=True)
    sub.add_parser("parked")
    a = sub.add_parser("approve"); a.add_argument("id"); a.add_argument("words")
    f = sub.add_parser("refuse"); f.add_argument("id"); f.add_argument("words")
    sub.add_parser("install-hook").add_argument("root")
    args = ap.parse_args(argv)

    try:
        if args.verb == "write":
            _out(A.write(args.path, _content(args), verb=args.record_verb, why=args.why,
                         count=args.count))
        elif args.verb == "remove":
            _out(A.remove(args.path, why=args.why))
        elif args.verb == "genesis":
            _out(A.genesis(args.root, why=args.why))
        elif args.verb == "check":
            name = args.root if args.root in A.roots() else A.root_name_of(args.root)
            faults = A.check_staged(name)
            for f_ in faults:
                print(f"artifact check: {f_}", file=sys.stderr)
            if faults:
                print(f"\nREFUSED — {len(faults)} record(s) staged around the artifact door "
                      f"(ticket 30531f6e1c5d). A record of truth changes only through the door; "
                      f"a hand edit is parked for Akien, never committed as truth.",
                      file=sys.stderr)
                return 2
            print("artifact check: every staged record is journaled; chain intact")
        elif args.verb == "verify":
            faults = A.verify_chain(A.roots()[args.root])
            for f_ in faults:
                print(f"artifact verify: {f_}", file=sys.stderr)
            if faults:
                return 2
            print(f"artifact verify: {len(A.read_journal(A.roots()[args.root]))} entries, chain intact")
        elif args.verb == "caller":
            _out(A.caller())
        elif args.verb == "locate":
            hit = A.locate(args.path)
            _out(None if hit is None else {"root": hit[0], "rel": hit[2].as_posix()})
        elif args.verb == "hand-edit":
            _out(A.park_hand_edit(args.path, why=args.why))
        elif args.verb == "parked":
            _out([{k: v for k, v in p.items() if k not in ("proposed", "standing")}
                  for p in A.parked()])
        elif args.verb == "approve":
            _out(A.approve(args.id, args.words))
        elif args.verb == "refuse":
            _out(A.refuse(args.id, args.words))
        elif args.verb == "install-hook":
            _out(_install_hook(args.root))
    except A.Refused as exc:
        print(f"artifact {args.verb}: REFUSED — {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

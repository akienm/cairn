"""python3 -m cairn.machines.web_operator --holder <device>/<n> [--instance-root PATH] [--window] <verb> ...

The shell mouth of the web_operator machine: each verb is the class's verb, printed.

  start | stop | go URL | where | text [CSS] | find CSS | click CSS [N] | type CSS TEXT [N]
  secret CSS KEY [N] (the value is never printed) | key enter|tab|escape | shot PATH | js SCRIPT

--instance-root points the holder at a different instance root than ~/.cairn (scratch worlds).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cairn.tools.base.address import ROOTS


def main(argv: list[str]) -> int:
    from cairn.machines.web_operator import WebOperator, WebOperatorError
    ap = argparse.ArgumentParser(prog="python3 -m cairn.machines.web_operator", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--holder", required=True, help="<device>/<instance>, e.g. librarian/0")
    ap.add_argument("--instance-root", help="instance root in place of ~/.cairn")
    ap.add_argument("--window", action="store_true", help="start with a visible window")
    ap.add_argument("verb")
    ap.add_argument("rest", nargs="*")
    a = ap.parse_args(argv)
    device, _, n = a.holder.partition("/")
    if not device or not n.isdigit():
        ap.error(f"--holder must be <device>/<instance>, got {a.holder!r}")
    roots = {**ROOTS, "instance": Path(a.instance_root)} if a.instance_root else None
    op = WebOperator(device, int(n), roots=roots, headless=not a.window)
    r = a.rest
    idx = lambda i: int(r[i]) if len(r) > i else 0  # noqa: E731
    try:
        if a.verb == "start":
            op.start()
            print(f"web_operator: {a.holder} up on port {op.state()['port']}")
        elif a.verb == "stop":
            op.stop()
            print(f"web_operator: {a.holder} stopped")
        elif a.verb == "go":
            op.go(r[0])
            print(*op.where(), sep="\n")
        elif a.verb == "where":
            print(*op.where(), sep="\n")
        elif a.verb == "text":
            print(op.text(r[0] if r else None))
        elif a.verb == "find":
            for row in op.find(r[0]):
                print(*row, sep="\t")
        elif a.verb == "click":
            op.click(r[0], idx(1))
        elif a.verb == "type":
            op.type(r[0], r[1], idx(2))
        elif a.verb == "secret":
            op.secret(r[0], r[1], idx(2))
            print("web_operator: typed (value not shown)")
        elif a.verb == "key":
            op.key(r[0])
        elif a.verb == "shot":
            print(op.shot(r[0]))
        elif a.verb == "js":
            print(json.dumps(op.js(r[0]), indent=1))
        else:
            ap.error(f"unknown verb {a.verb!r}")
    except IndexError:
        ap.error(f"{a.verb}: missing argument")
    except WebOperatorError as e:
        print(f"web_operator: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

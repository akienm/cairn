"""``python3 -m cairn.tools.post_commit`` — fire | install-hook | verify-hook (ticket e0f318650123).

``fire`` is what the installed hook runs: every tracked subscriber once, each refusal printed by
name, and exit 0 always — the commit has landed, and its exit is not the commit's to read.
"""
import argparse
import sys

from cairn.tools.post_commit import fanout


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m cairn.tools.post_commit")
    ap.add_argument("action", choices=["fire", "install-hook", "verify-hook"])
    ap.add_argument("--repo", default=None, help="the repository to act on (default: this one)")
    a = ap.parse_args(argv)
    if a.action == "fire":
        try:
            results = fanout.fire(a.repo)
        except Exception as exc:  # noqa: BLE001 — loud, never blocking (Law 7)
            print(f"post-commit fan-out could not list its subscribers: "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 0
        for r in results:
            if r["exit"] != 0:
                print(f"post-commit subscriber {r['subscriber']} exited {r['exit']}: "
                      f"{r['stderr'].strip()[-400:]}", file=sys.stderr)
        return 0
    if a.action == "install-hook":
        got = fanout.install_hook(a.repo)
        print(("installed " if got["installed"] else "not installed ") + got["path"])
        print(f"  {got['why']}")
        return 0 if got["installed"] or "already installed" in got["why"] else 1
    got = fanout.verify_hook(a.repo)
    print(("green  " if got["green"] else "RED    ") + got.get("path", ""))
    print(f"  {got['why']}")
    return 0 if got["green"] else 1


if __name__ == "__main__":
    sys.exit(main())

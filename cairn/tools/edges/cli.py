"""cairn/tools/edges/cli.py — the frontier projector verb.

    cairn edges        the full frontier: every filed edge + every open question

A view: it prints, it never mutates. Always exits 0 (Law 7 presentation half).
"""

from __future__ import annotations

import sys

from cairn.tools.edges import edges


def main(argv: list[str]) -> int:
    print(edges.render())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""cairn/tools/cairnmap/cli.py — the verbs. A view's CLI: it prints, it never mutates.

    cairn cairnmap             the map, scoped by WHERE you stand (cwd)
    cairn cairnmap <name|dir>  one component's full charter (the brief)
    cairn cairnmap --gate      the derivation gate: completeness reds only,
                               exit 0 green / 1 red — the skill class's
                               prove_gate, runnable at the PROVEME crossing

Render always exits 0 — a map that fails its own gate still shows you the map,
with the reds loud in it (Law 7: loud at the surface, and a presentation surface
may not refuse to present). Only --gate carries a verdict in its exit code,
because a gate's exit code IS its verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.cairnmap import cairnmap


def _resolve(arg: str) -> Path | None:
    """A directory, or a bare component name tried against the repo's homes."""
    repo = cairnmap.repo_root()
    # A bare component name no longer says which rung it is in, so the rung is LOOKED UP
    # (address.component_dir, 2026-08-13) rather than concatenated. Kept in the candidate
    # list rather than short-circuiting: `cairn <name>` still has to try the plain-path and
    # skills readings, and the order is what makes a real directory argument win.
    by_rung = address.component_dir(arg, repo / "cairn")
    candidates = [Path(arg), repo / arg, *( [by_rung] if by_rung else [] ),
                  repo / "skills" / arg]
    for c in candidates:
        charter = c / cairnmap.CHARTER if c.is_dir() else c
        if charter.name == cairnmap.CHARTER and charter.is_file():
            return charter
    return None


def main(argv: list[str]) -> int:
    if "--gate" in argv:
        reds = cairnmap.check()
        for red in reds:
            print(f"RED: {red}")
        n = len(cairnmap.gather()[0])
        print(f"derivation gate: {'RED — ' + str(len(reds)) + ' finding(s)' if reds else 'green'}"
              f" ({n} charters)")
        return 1 if reds else 0

    if argv:
        charter = _resolve(argv[0])
        if charter is None:
            print(f"cairnmap: no charter at or under {argv[0]!r} — a component "
                  f"without an intention doesn't run, and doesn't render", file=sys.stderr)
            return 2
        print(cairnmap.render_detail(charter))
        return 0

    here = cairnmap.context_charter(Path.cwd())
    if here is not None:
        print(cairnmap.render_detail(here))
    else:
        print(cairnmap.render_map())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

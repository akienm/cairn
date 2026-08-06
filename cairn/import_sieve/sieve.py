"""import_sieve — the corpus import graph, and the sieves that shake it.

WHAT IT IS. One parse of every .py file in the tree into an import graph, plus the
queries five prose IOUs have been standing on since 2026-07-18. A rule here is a
SIEVE: it has a MESH (which imports count as the capability) and it CATCHES the
modules that do not belong on its side of the door.

WHY IT IS NOT A GREP. The mesh is the whole difficulty, and the corpus taught it
twice before this module existed:

  - learning_block's tooth (2026-08-01) grepped whole source and fired on its own
    docstring's honest mention of inference_domain. Fixed by scoping to import lines.
  - inference_domain's tooth (2026-07-21) grepped for the host's port and API paths
    and fired on cairn/base/needs.py, where ':11434/api/tags' appears in a docstring,
    an error message, and a fixture. Fixed by testing the CAPABILITY, not the mention.

Both lessons are the same lesson and both are built in here: parse with `ast`, match
full dotted names, and never ask whether a word appears. `urllib.parse.parse_qs` is
string work and no more a door than `str.split`; `urllib.request` is a door. A scan
that cannot tell those apart gets trained away by its own noise.

OUTBOUND IS NOT INBOUND. web_server imports `http.server` and can only LISTEN; it
cannot reach anything. A sole-path rule about reaching a host must name the dialing
modules exactly, or it reds on the one component whose whole job is to be reachable.

THE HOLLOW FLOOR IS PHYSICS HERE, NOT A REMEMBERED ASSERT. `catches()` refuses to
report a clean sieve over a tree it never read (Law 8 — a green over zero files is not
a green). inference_domain's hand-rolled version carried that floor as a separate
assertion at the end of the tooth, which is exactly the kind of step a second copy
forgets. It lives inside the door now, so a caller cannot skip it by not knowing.

WHAT THIS DOES NOT SEE, stated so nobody reads a green as wider than it is:
  - a subprocess. `subprocess.run(["curl", ...])` dials and imports nothing.
  - a dynamic import. `importlib.import_module(name)` with a computed name.
  - a WRITE. "no second writer of intentions-congruency-lab/" is a different scan
    over a different verb; this module does not do it and does not claim to.
"""

from __future__ import annotations

import ast
import os

# The tree is small (200 files) and every consumer wants the whole thing, so the graph
# is built in one pass and handed over whole. No caching: a stale graph would be a
# scan reporting on a corpus that no longer exists, which is the failure this component
# is for.

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv"}


class HollowScan(RuntimeError):
    """The sieve was shaken over a tree it did not read. Never a pass."""


def _walk_py(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")]
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def imports_in(source: str) -> set[str]:
    """Every dotted name this source imports, as written.

    `from x.y import z` yields BOTH `x.y` and `x.y.z`. The first is what a stdlib rule
    matches ('does it import urllib.request'); the second is what an in-tree rule needs
    ('does diagnostic_inspector import cairn.build_inspector.inspector'). Recording only
    the module — which the hand-rolled version did — makes every in-tree edge invisible
    at the leaf, and in-tree edges are half of why this exists.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()            # unparseable is unimportable; it is not a door
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level:      # relative: unresolved, and the corpus has none (measured 2026-08-06)
                continue
            if node.module:
                out.add(node.module)
                out |= {f"{node.module}.{a.name}" for a in node.names}
    return out


def import_graph(repo_root: str) -> dict[str, set[str]]:
    """{path relative to repo_root: every dotted name it imports}."""
    graph: dict[str, set[str]] = {}
    for abs_path in _walk_py(repo_root):
        rel = os.path.relpath(abs_path, repo_root)
        try:
            src = open(abs_path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        graph[rel] = imports_in(src)
    return graph


def _matches(imported: str, target: str) -> bool:
    """Dotted-prefix match. `urllib.request` catches `urllib.request.urlopen` and NOT
    `urllib.parse.parse_qs` — the whole dial/parse distinction is this one line."""
    return imported == target or imported.startswith(target + ".")


def module_name(rel_path: str) -> str:
    """'cairn/base/probe.py' -> 'cairn.base.probe'. A package __init__ names its package."""
    p = rel_path[:-3] if rel_path.endswith(".py") else rel_path
    parts = [x for x in p.split(os.sep) if x]
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def importers_of(graph: dict[str, set[str]], rel_path: str) -> list[str]:
    """Which files import the module living at `rel_path`. The ruling door's question.

    Answers by MODULE NAME, not by path string, because nobody writes
    `import cairn/base/probe.py`. A file nothing imports returns [] — which is the only
    condition under which sentencing it to death is safe.
    """
    name = module_name(rel_path)
    if not name:
        return []
    hits = []
    for path, imported in graph.items():
        if path == rel_path:
            continue                     # a module importing itself is not an importer
        if any(_matches(i, name) for i in imported):
            hits.append(path)
    return sorted(hits)


def catches(graph: dict[str, set[str]], rule: dict, floor: int = 20) -> list[str]:
    """Shake one sieve over the graph and return what its mesh caught.

    Two rule kinds, because the corpus asks two questions and they are not the same shape:

      sole_path — `modules` may be imported ONLY from inside `only`. This is the domain
                  chokepoint: one door to 5432, one door to the inference host. A second
                  importer is a second door, and the whole claim is that there is one.

      forbidden — `within` may not import `modules` at all. This is a fork: two things
                  that must not share an implementation, so that one can survive the
                  other breaking.

    Returns [] when nothing is caught. Raises HollowScan rather than returning [] when
    the graph is too small to have looked at anything — the difference between "clean"
    and "did not run" is the difference this raise exists to keep.
    """
    if len(graph) < floor:
        raise HollowScan(
            f"the sieve was shaken over {len(graph)} files (floor {floor}) — a clean "
            "result here means the scan did not read the tree, not that the tree is clean"
        )
    kind = rule.get("kind")
    modules = tuple(rule.get("modules", ()))
    what = rule.get("capability", "the capability")
    caught: list[str] = []

    if kind == "sole_path":
        only = rule["only"]
        for path, imported in sorted(graph.items()):
            if path.startswith(only):
                continue
            found = sorted(m for m in imported if any(_matches(m, t) for t in modules))
            if found:
                caught.append(f"{path} imports {found} — a SECOND door to {what}; "
                              f"{only} is supposed to be the only one")
    elif kind == "forbidden":
        within = rule["within"]
        for path, imported in sorted(graph.items()):
            if not path.startswith(within):
                continue
            found = sorted(m for m in imported if any(_matches(m, t) for t in modules))
            if found:
                caught.append(f"{path} imports {found} — {within} may not depend on "
                              f"{what}; the fork exists so one survives the other breaking")
    else:
        raise ValueError(f"unknown sieve kind {kind!r} — sole_path or forbidden")
    return caught

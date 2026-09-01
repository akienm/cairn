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
    and fired on cairn/tools/base/needs.py, where ':11434/api/tags' appears in a docstring,
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
  - a WRITE. "no second writer of intentions-congruency-lab/" is a different scan
    over a different verb; this module does not do it and does not claim to.
Two former gaps are now physics: subprocess dials and dynamic imports are caught by
the `dynamic_import` and `subprocess_dial` rule kinds in catches(). A computed
subprocess argument is flagged OPAQUE rather than silently passed.
"""

from __future__ import annotations

import ast
import os

# The tree is small (200 files) and every consumer wants the whole thing, so the graph
# is built in one pass and handed over whole. No caching: a stale graph would be a
# scan reporting on a corpus that no longer exists, which is the failure this component
# is for.

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv"}

_SUBPROCESS_CALLABLES = frozenset({
    'run', 'Popen', 'call', 'check_output', 'check_call',
})


class HollowScan(RuntimeError):
    """The sieve was shaken over a tree it did not read. Never a pass."""


# ── PHASE: when a sieve can run ─────────────────────────────────────────────
# THE BANDS ARE PHASES (Akien, 2026-08-12, ruled; confirmed 2026-08-21: "BANDING
# IS PREPROCESS, MEASURE AND POSTPROCESS"). His words: "each question is a seive.
# and because we might have seives that come after others (which is min, which is
# max) this is the kind of bands that we replace our previous ideas with:
# preprocessing, recording, postprocessing. and the which is smallest is simply a
# post processing seive."
#
# THE TELL (proposed by CC, ruled to hold): WHAT THE SIEVE READS. A recording
# sieve takes the SUBJECT; a postprocessing sieve takes PRIOR STAMPS;
# preprocessing produces the subjects rather than scoring them. Different input,
# visible in the body. Akien: "that holds."
#
# SUPERSEDES the proximity ladder (in-hand/local-disk/correlated-local/off-box).
# Those distinctions remain true about what they described and are no longer the
# spec. The derivation is still DERIVED, NEVER AUTHORED — a hand-set phase would
# be the same defect as a hand-set band was.
#
# DETERMINISTIC CODE DRIVEN BY CONFIG DATA (Akien, 2026-08-12): "mesh levels are
# now preprocess, record and postprocess, in deterministic code driven by config
# data." The levels are DATA the assembly reads, not a taxonomy compiled into the
# vocabulary.

POSTPROCESS_PARAMS = frozenset({"stamps", "scores", "gradation", "prior_stamps"})


def _local_phase(fn: ast.AST) -> int:
    """The phase this function belongs to, derived from what it reads.

    Band 0 (preprocess): no sieve-shaped parameters — produces subjects.
    Band 1 (record): takes the subject and scores it — the normal sieve.
    Band 2 (postprocess): takes prior stamps — picks from results.
    """
    params = {a.arg for a in fn.args.args}
    if params & POSTPROCESS_PARAMS:
        return 2
    if params:
        return 1
    return 0


def phase_of(source: str) -> dict[str, int]:
    """{function name: its phase}, for every module-level function in `source`.

    Phase is transitive: a function that calls a postprocess helper becomes
    postprocess. Cycle-safe; an unparseable source yields {}.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    funcs = {n.name: n for n in tree.body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def walk(name: str, seen: frozenset) -> int:
        if name in seen or name not in funcs:
            return 0
        seen = seen | {name}
        phase = _local_phase(funcs[name])
        for node in ast.walk(funcs[name]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                callee = node.func.id
                if callee in funcs:
                    phase = max(phase, walk(callee, seen))
        return phase

    return {name: walk(name, frozenset()) for name in funcs}


def walk_py(root: str):
    """Every .py file under ``root``, sorted per directory, with the noise pruned.

    PUBLIC since 2026-08-17 (ticket the-instance-address-is-resolved-never-spelled), and
    the promotion is the whole change — the body is untouched. A second component now
    needs to shake a rule over the same tree this one does: cairn.tools.base.address_rule,
    which asks a question about an EXPRESSION rather than about imports. Its two other
    options were reaching for a private symbol across a component boundary, or rebuilding
    a walker that already knows which directories are noise — and the second is how two
    walkers come to disagree about whether .venv counts.

    What is NOT promoted with it: the pruning set itself stays this component's. A caller
    that needs a different set of noise directories is asking a different question and
    should say so out loud rather than pass a parameter.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")]
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def imports_in(source: str) -> set[str]:
    """Every dotted name this source imports, as written.

    `from x.y import z` yields BOTH `x.y` and `x.y.z`. The first is what a stdlib rule
    matches ('does it import urllib.request'); the second is what an in-tree rule needs
    ('does diagnostic_inspector import cairn.machines.build_inspector.inspector'). Recording only
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
    for abs_path in walk_py(repo_root):
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
    """'cairn/tools/base/probe.py' -> 'cairn.tools.base.probe'. A package __init__ names its package."""
    p = rel_path[:-3] if rel_path.endswith(".py") else rel_path
    parts = [x for x in p.split(os.sep) if x]
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def importers_of(graph: dict[str, set[str]], rel_path: str) -> list[str]:
    """Which files import the module living at `rel_path`. The ruling door's question.

    Answers by MODULE NAME, not by path string, because nobody writes
    `import cairn/tools/base/probe.py`. A file nothing imports returns [] — which is the only
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


def reaches(graph: dict[str, set[str]], start: str) -> dict[str, list[str]]:
    """Every file `start` can reach by following imports, each with the SHORTEST chain.

    ``importers_of`` asks who points AT a module, one hop, backwards. This asks what a
    module can arrive at, any number of hops, forwards — and it is the question a rule
    about a fire path has to ask, because a module two hops out is just as reached as one
    directly imported. The value is the chain rather than a bare set so a finding can say
    HOW: a diagnostic that names the endpoint without the route makes the reader re-derive
    the walk to act on it.

    Breadth-first, so the recorded chain is the shortest one; a file already trailed is
    never re-trailed, which is also what terminates the walk on a cyclic graph.

    A PACKAGE IS REACHED BY ITS SUBMODULE, and that is Python, not looseness: ``import
    cairn.tools.base.address`` executes ``cairn/tools/base/__init__.py`` on the way, so ``_matches``
    landing on both is the truth about what runs. An imported name matching no file in the
    graph is a DEAD END rather than an error — a stdlib import, a third-party one, or a
    module outside the scanned root; the walk terminates on the graph's own node set and
    says nothing about what it cannot see (the same edge ``catches`` inherits: a
    ``subprocess`` call and a dynamic import remain invisible to every AST question).
    """
    if start not in graph:
        raise ValueError(
            f"reaches: {start!r} is not in the graph ({len(graph)} files) — a walk from a "
            "file the scan never read would return an empty closure that looks like a "
            "clean one")
    by_module: dict[str, str] = {}
    for path in sorted(graph):
        name = module_name(path)
        if name:
            by_module.setdefault(name, path)
    trail: dict[str, list[str]] = {start: [start]}
    frontier = [start]
    while frontier:
        nxt: list[str] = []
        for cur in frontier:
            for imported in sorted(graph.get(cur, ())):
                for name, path in by_module.items():
                    if path in trail or not _matches(imported, name):
                        continue
                    trail[path] = trail[cur] + [path]
                    nxt.append(path)
        frontier = nxt
    del trail[start]                 # a module does not reach itself, same as importers_of
    return trail


def _dynamic_imports_in(tree, file_imports):
    """Dynamic-import calls: importlib.import_module(X) and __import__(X).

    Returns [{module: str|None, opaque: bool, line: int}].
    """
    has_importlib = any(
        i == 'importlib' or i.startswith('importlib.') for i in file_imports)
    has_direct = 'importlib.import_module' in file_imports
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        match = False
        if isinstance(func, ast.Name) and func.id == '__import__':
            match = True
        elif (isinstance(func, ast.Attribute) and func.attr == 'import_module'
              and isinstance(func.value, ast.Name) and func.value.id == 'importlib'
              and has_importlib):
            match = True
        elif (isinstance(func, ast.Name) and func.id == 'import_module'
              and has_direct):
            match = True
        if not match or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            results.append({'module': arg.value, 'opaque': False, 'line': node.lineno})
        else:
            results.append({'module': None, 'opaque': True, 'line': node.lineno})
    return results


def _subprocess_calls_in(tree, file_imports):
    """Subprocess calls: subprocess.run / Popen / call / check_output / check_call.

    Returns [{targets: [str], opaque: bool, line: int, callable: str}].
    """
    has_subprocess = any(
        i == 'subprocess' or i.startswith('subprocess.') for i in file_imports)
    direct = {}
    for imp in file_imports:
        if imp.startswith('subprocess.'):
            name = imp.rsplit('.', 1)[-1]
            if name in _SUBPROCESS_CALLABLES:
                direct[name] = imp
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        callable_name = None
        if (isinstance(func, ast.Attribute) and func.attr in _SUBPROCESS_CALLABLES
                and isinstance(func.value, ast.Name) and func.value.id == 'subprocess'
                and has_subprocess):
            callable_name = f'subprocess.{func.attr}'
        elif isinstance(func, ast.Name) and func.id in direct:
            callable_name = direct[func.id]
        if callable_name is None:
            continue
        if not node.args:
            results.append({'targets': [], 'opaque': False,
                            'line': node.lineno, 'callable': callable_name})
            continue
        arg = node.args[0]
        targets = []
        opaque = False
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            targets = [arg.value]
        elif isinstance(arg, ast.List):
            for elt in arg.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    targets.append(elt.value)
                else:
                    opaque = True
        else:
            opaque = True
        results.append({'targets': targets, 'opaque': opaque,
                        'line': node.lineno, 'callable': callable_name})
    return results


def catches(graph: dict[str, set[str]], rule: dict, floor: int = 20,
            *, sources: dict[str, str] | None = None) -> list[str]:
    """Shake one sieve over the graph and return what its mesh caught.

    Six rule kinds, because the corpus asks six questions and they are not the same
    shape:

      sole_path — `modules` may be imported ONLY from inside `only`. This is the domain
                  chokepoint: one door to 5432, one door to the inference host. A second
                  importer is a second door, and the whole claim is that there is one.

      forbidden — `within` may not import `modules` at all. This is a fork: two things
                  that must not share an implementation, so that one can survive the
                  other breaking.

      unreachable — nothing `start` can REACH may reach `modules`. The first two ask about
                  one hop and can be answered by reading a file; this one asks about the
                  whole path and can only be answered by walking it. It exists because the
                  alternative — a list of the modules a fire path is allowed to import —
                  has to be widened by hand every time the corpus grows a legitimate
                  dependency, and the widening is a decision nobody records (measured
                  2026-08-12: `cairn.tools.base.nest` entered the build_inspector fire path and
                  the list was never widened, so a tooth that was not holding read as one
                  that was). Naming the CAPABILITY that must stay out of reach is what
                  makes the rule general: the innocent never need signatures.

      dynamic_import — a dynamic import (importlib.import_module, __import__) of a
                  ``modules``-listed target. The import graph cannot see it; this kind
                  can. Requires ``sources={path: source_text}``.

      subprocess_dial — a subprocess call (subprocess.run / Popen / call / check_output
                  / check_call) that reaches a guarded target. The guarded targets are
                  DATA in ``rule["guarded"]``: ``binaries`` (exact binary names) and
                  ``url_fragments`` (substrings in string arguments). A COMPUTED argument
                  is flagged OPAQUE — it cannot be cleared or convicted from the AST
                  alone. Requires ``sources={path: source_text}``.

      device_isolation — no file under one device directory may import from another
                  device's module, except those in ``exempt``. The device set is DISCOVERED
                  from the graph's own keys — every distinct first path segment under
                  ``device_prefix`` is a device. ``module_prefix`` is the dotted name that
                  begins every device's import (e.g. ``cairn.devices.``). Ruling
                  2026-08-31-no-cross-device-imports: "no device should ever import another
                  device except the database."

    Returns [] when nothing is caught. Raises HollowScan rather than returning [] when
    the graph is too small to have looked at anything — the difference between "clean"
    and "did not run" is the difference this raise exists to keep, and it guards ALL
    SIX kinds because it is asked before the kind is: a reachability walk over a
    half-read tree returns a short closure, and a short closure is clean for the wrong
    reason.
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
    elif kind == "unreachable":
        start = rule["start"]
        # The start is scanned too, with a one-link chain: a fire path that reaches the
        # denied door DIRECTLY is the loudest version of the failure, and a walk that only
        # examined what the start reaches would step straight over it.
        scan = {start: [start], **reaches(graph, start)}
        for path, chain in sorted(scan.items()):
            found = sorted(m for m in graph.get(path, ()) if any(_matches(m, t) for t in modules))
            if found:
                route = " -> ".join(module_name(p) for p in chain)
                caught.append(f"{path} imports {found} — {what} is reachable from {start} "
                              f"by import, along {route}; nothing on that path may reach it")
    elif kind == "dynamic_import":
        if sources is None:
            raise ValueError("dynamic_import rule requires sources={path: source_text}")
        for path in sorted(sources):
            src = sources[path]
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for dyn in _dynamic_imports_in(tree, imports_in(src)):
                if dyn['opaque']:
                    caught.append(f"{path}:{dyn['line']} has a dynamic import with a "
                                  f"computed name — OPAQUE; cannot determine the target")
                elif any(_matches(dyn['module'], t) for t in modules):
                    caught.append(f"{path}:{dyn['line']} dynamically imports "
                                  f"{dyn['module']!r} — a door to {what} invisible "
                                  f"to the import graph")
    elif kind == "subprocess_dial":
        if sources is None:
            raise ValueError("subprocess_dial rule requires sources={path: source_text}")
        guarded = rule.get("guarded", {})
        binaries = frozenset(guarded.get("binaries", ()))
        url_fragments = tuple(guarded.get("url_fragments", ()))
        for path in sorted(sources):
            src = sources[path]
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for call in _subprocess_calls_in(tree, imports_in(src)):
                if call['opaque']:
                    caught.append(f"{path}:{call['line']} calls {call['callable']} "
                                  f"with a computed argument — OPAQUE; cannot "
                                  f"determine the target")
                else:
                    for target in call['targets']:
                        if target in binaries:
                            caught.append(
                                f"{path}:{call['line']} calls {call['callable']} "
                                f"with {target!r} — a subprocess dial to {what}")
                        elif any(frag in target for frag in url_fragments):
                            caught.append(
                                f"{path}:{call['line']} calls {call['callable']} "
                                f"with {target!r} (contains guarded fragment) — "
                                f"a subprocess dial to {what}")
    elif kind == "device_isolation":
        device_prefix = rule.get("device_prefix", "")
        module_prefix = rule["module_prefix"]
        exempt = frozenset(rule.get("exempt", ()))
        devices: set[str] = set()
        for path in graph:
            if device_prefix and not path.startswith(device_prefix):
                continue
            rest = path[len(device_prefix):]
            seg = rest.split(os.sep, 1)[0]
            if seg and not seg.endswith(".py"):
                devices.add(seg)
        for path, imported in sorted(graph.items()):
            if device_prefix and not path.startswith(device_prefix):
                continue
            rest = path[len(device_prefix):]
            own_device = rest.split(os.sep, 1)[0]
            if own_device not in devices:
                continue
            for other in sorted(devices - {own_device} - exempt):
                target = module_prefix + other
                found = sorted(m for m in imported if _matches(m, target))
                if found:
                    caught.append(
                        f"{path} imports {found} — {own_device} may not import "
                        f"{other}; {what}")
    else:
        raise ValueError(
            f"unknown sieve kind {kind!r} — sole_path, forbidden, unreachable, "
            f"dynamic_import, subprocess_dial or device_isolation")
    return caught

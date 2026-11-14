"""unseen_patches — a proof that patches a name the judge it asks reads in another process.

Three cases of one class, found by hand on 2026-11-14: corrosion's ``test_weakening_with_ruling_greens`` patched
``citation.ruling_covers_path`` and asked ``constraint_enforcement_holds``; 3e08102ef35a's ``_TICKETS`` patches sat around
calls whose lanes the inspector answers; d3248e7cb2fd substituted ``crossings.ROOTS`` for a judge that now runs in CodeMother.
Since 17d570c10390 the judges run in CodeMother's process, so a name replaced in the ASKING process never reaches the judge
that reads it, and the proof goes red long after the change that moved the judge.

THE TOOTH MUST SHOW THE PATCH IS ANSWER-SIDE OR STAY SILENT (memory broad-tooth-manufactures-coverage): a patch is reported only
when all four hold, and the report names the target, the judge and the chain.

  (a) SCOPE      the patch is live across an ask-capable call: inside its ``with patch(...)`` body, or after a ``mod.attr = v``
                 assignment to the end of the function;
  (b) ASK-CAPABLE a literal ``ask('<judge>')`` naming a top-level function of this machine's inspector or run_record, a name bound to a lambda or def that asks
                 one, a call into transitions.py whose function transitively reaches the wire (computed from its own ast), or,
                 one level, a helper of the proof itself that makes such a call;
  (c) ANSWER-SIDE the patched module is in ``import_sieve.reaches`` of the judge's module AND a reached file reads the attribute
                 (an ast Name or Attribute load, never a string or docstring);
  (d) RESOLVED   the patched module resolves through the proof's own imports; a target that does not is LISTED as unresolved;
  (e) NOT HANDED the patch's value is not handed, as the SAME binding, to a ``launch(...)`` at or after the patch inside its live span:
                 that is the 3e08 fix (the asker keeps the patch it reads itself and the launched CodeMother is given the same world).

Out of scope, by design: a MODULE-LEVEL assignment (import-time configuration, e.g. a worktree's commons fallback or a sandboxed class: it is
listed under ``module_level``, never reported, because it names no scope an ask sits inside); environment patches (``patch.dict(os.environ)``) are correct when made before the launch; a signature
mismatch in a fake (the 0c2c ``env=`` fake) is not a patch the judge reads; a dynamic name or a judge named by a variable is
invisible to the ast read and passes silently.
"""

from __future__ import annotations

import ast
from pathlib import Path

# WHERE THIS MACHINE LIVES, relative to the repo: the judges are the top-level functions of the two modules beside this file, whichever
# directory the machine stands in (it moves into codemother's machines with 93fa3e3a6199), so no module path is spelled here.
_REAL_REPO = Path(__file__).resolve().parents[3]
_MACHINE = Path(__file__).resolve().parent.relative_to(_REAL_REPO).as_posix()
_JUDGE_MODULES = ("inspector", "run_record")        # every INSPECT_JUDGES entry maps to one of these two (shim.py:117-136)
_TRANSITIONS = "cairn/tools/base/transitions.py"
_WIRE_CALLS = {"_judge", "_ask_inspector", "ask_inspector", "ask", "_ask_once"}

_CTX: dict = {}


def _dotted(rel: str) -> str:
    return rel[:-3].replace("/", ".") if rel.endswith(".py") else rel.replace("/", ".")


def _ctx(repo_root: Path) -> dict:
    key = str(Path(repo_root).resolve())
    if key not in _CTX:
        from cairn.tools.import_sieve import sieve
        graph = sieve.import_graph(key)
        judges = inspect_judges(repo_root)
        _CTX[key] = {"sieve": sieve, "graph": graph, "judges": judges, "capable": _capable_transitions(repo_root),
                     "reach": {}, "reads": {}, "lane_asker": _dotted(f"{_MACHINE}/inspector.py")}
    return _CTX[key]


def clear_cache() -> None:
    _CTX.clear()


def inspect_judges(repo_root: Path) -> dict[str, str]:
    """{judge: module}: the top-level functions of this machine's two judge modules, by ast, never imported. Codemother answers
    only judges that are functions of build_inspector.inspector or run_record (her INSPECT_JUDGES table maps each entry to one of
    them), so reading the machine's own functions needs no read of her shim: a name in neither module is not a judge."""
    out: dict[str, str] = {}
    for mod in _JUDGE_MODULES:
        path = Path(repo_root) / _MACHINE / f"{mod}.py"
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        dotted = _dotted(f"{_MACHINE}/{mod}.py")
        out.update({n.name: dotted for n in tree.body if isinstance(n, ast.FunctionDef)})
    return out


def _capable_transitions(repo_root: Path) -> set[str]:
    path = Path(repo_root) / _TRANSITIONS
    if not path.is_file():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = {}
    for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
        calls[fn.name] = {c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", "")
                          for c in ast.walk(fn) if isinstance(c, ast.Call)}
    capable = {n for n, cs in calls.items() if cs & _WIRE_CALLS}
    grew = True
    while grew:
        grew = False
        for n, cs in calls.items():
            if n not in capable and cs & capable:
                capable.add(n)
                grew = True
    return capable


def _file_of(ctx: dict, dotted: str) -> str | None:
    for cand in (dotted.replace(".", "/") + ".py", dotted.replace(".", "/") + "/__init__.py"):
        if cand in ctx["graph"]:
            return cand
    return None


def _reach(ctx: dict, module: str):
    f = _file_of(ctx, module)
    if f is None:
        return None
    if f not in ctx["reach"]:
        ctx["reach"][f] = ctx["sieve"].reaches(ctx["graph"], f)
    return ctx["reach"][f]


def _reads(ctx: dict, repo_root: Path, rel: str, attr: str) -> bool:
    if rel not in ctx["reads"]:
        names: set[str] = set()
        try:
            tree = ast.parse((Path(repo_root) / rel).read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            tree = None
        if tree is not None:
            for x in ast.walk(tree):
                if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                    names.add(x.id)
                elif isinstance(x, ast.Attribute) and isinstance(x.ctx, ast.Load):
                    names.add(x.attr)
        ctx["reads"][rel] = names
    return attr in ctx["reads"][rel]


def _functions_of(ctx: dict, repo_root: Path, rel: str) -> dict:
    """{function name: (callee names, names it reads)} for every def in ``rel`` (methods included), plus '<module>': the names read at
    import time (statements outside any def). Name-based on purpose: an over-approximation of the call graph that never misses a callee."""
    cache = ctx.setdefault("fn", {})
    if rel in cache:
        return cache[rel]
    out: dict[str, tuple[set, set]] = {}
    try:
        tree = ast.parse((Path(repo_root) / rel).read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        cache[rel] = out
        return out

    def loads(node):
        names = set()
        for x in ast.walk(node):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                names.add(x.id)
            elif isinstance(x, ast.Attribute) and isinstance(x.ctx, ast.Load):
                names.add(x.attr)
        return names

    def callees(node):
        return {c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", "") for c in ast.walk(node) if isinstance(c, ast.Call)}

    module_reads: set[str] = set()
    for st in tree.body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        module_reads |= loads(st)
    out["<module>"] = (set(), module_reads)
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[fn.name] = (callees(fn), loads(fn))
    cache[rel] = out
    return out


def _transitions_judges(ctx: dict, repo_root: Path, fname: str) -> set[str]:
    """The judges the transitions.py function ``fname`` asks, directly or through the in-module functions it calls."""
    path = Path(repo_root) / _TRANSITIONS
    if not path.is_file():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    seen, todo, found = set(), [fname], set()
    while todo:
        name = todo.pop()
        if name in seen or name not in defs:
            continue
        seen.add(name)
        for c in ast.walk(defs[name]):
            if isinstance(c, ast.Call):
                f = c.func
                cname = f.id if isinstance(f, ast.Name) else getattr(f, "attr", "")
                if cname in _WIRE_CALLS and c.args and isinstance(c.args[0], ast.Constant) and isinstance(c.args[0].value, str):
                    found.add(c.args[0].value)
                todo.append(cname)
    return found


def _answer_side_reader(ctx: dict, repo_root: Path, base: str, reach: dict, starts: set[str], attr: str):
    """A file in ``reach`` that the JUDGE can actually read ``attr`` through: a function reachable (by callee name) from one of the
    ``starts`` judges reads it, or a reached file reads it at import time. A read inside a function the judge never calls (the asker's
    own ``enqueue_verdict``, which a judge module merely imports a sibling of) is the ASKER's read, not the judge's."""
    files = [base] + [r for r in reach if r != base]            # the judge's own module is not in its reach (a start never reaches itself)
    for rel in files:                                           # import-time reads run in the answerer when it imports the module
        if attr in _functions_of(ctx, repo_root, rel).get("<module>", (set(), set()))[1]:
            return rel
    table = {rel: _functions_of(ctx, repo_root, rel) for rel in files}
    todo = [(rel, name) for rel in files for name in table[rel] if name in starts]
    seen = set(todo)
    while todo:
        rel, name = todo.pop()
        callees, reads = table[rel][name]
        if attr in reads:
            return rel
        for other in files:
            for fn in table[other]:
                if fn in callees and (other, fn) not in seen and fn != "<module>":
                    seen.add((other, fn))
                    todo.append((other, fn))
    return None


def _aliases(tree) -> dict[str, str]:
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        elif isinstance(n, ast.ImportFrom) and n.module:
            for a in n.names:
                out[a.asname or a.name] = n.module + "." + a.name
    return out


def _judge_literals(node, judges: dict) -> set[str]:
    return {c.args[0].value for c in ast.walk(node)
            if isinstance(c, ast.Call) and c.args and isinstance(c.args[0], ast.Constant)
            and isinstance(c.args[0].value, str) and c.args[0].value in judges}


def _asking_names(tree, judges: dict, aliases: dict, capable: set[str]) -> dict[str, set[str]]:
    """Names in the proof (lambdas, defs, one level of helpers) whose body asks a judge: name -> the judges, or a 'via transitions'
    marker. Two passes, so a helper that calls an asking helper is found."""
    out: dict[str, set[str]] = {}
    for _ in range(2):
        for n in ast.walk(tree):
            body = n.value if isinstance(n, ast.Assign) and isinstance(n.value, ast.Lambda) else n if isinstance(n, ast.FunctionDef) else None
            name = (n.targets[0].id if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                    else n.name if isinstance(n, ast.FunctionDef) else None)
            if body is None or name is None:
                continue
            got = _judge_literals(body, judges) | _through_transitions(body, aliases, capable)
            for c in ast.walk(body):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in out and c.func.id != name:
                    got |= out[c.func.id]
            if got:
                out[name] = out.get(name, set()) | got
    return out


def _through_transitions(node, aliases: dict, capable: set[str]) -> set[str]:
    found = set()
    for c in ast.walk(node):
        if not isinstance(c, ast.Call):
            continue
        if isinstance(c.func, ast.Attribute) and c.func.attr in capable:
            base = c.func.value.id if isinstance(c.func.value, ast.Name) else ""
            mod = aliases.get(base, base)
            if mod.endswith("transitions") or base in ("T", "transitions"):
                found.add("via transitions." + c.func.attr)
        elif isinstance(c.func, ast.Name):
            # ``from cairn.tools.base.transitions import emit`` then ``emit(...)``: the alias maps the bare name to its dotted origin
            origin = aliases.get(c.func.id, "")
            if origin.rsplit(".", 1)[-1] in capable and origin.rsplit(".", 1)[0].endswith("transitions"):
                found.add("via transitions." + origin.rsplit(".", 1)[-1])
    return found


def _value_text(call: ast.Call, index: int) -> str:
    """The source text of the value a patch(...) call installs (its ``new`` argument or keyword), or ''."""
    if len(call.args) > index:
        return ast.unparse(call.args[index])
    kw = next((k for k in call.keywords if k.arg == "new"), None)
    return ast.unparse(kw.value) if kw else ""


def _is_a_restore(tree, head: str, attr: str, line: int, value: str) -> bool:
    """``X.attr = saved`` where ``saved`` was read from ``X.attr`` earlier in the same function is the patch being UNDONE, not a patch:
    the finally of every save/patch/restore. Without this rule each restore reads as a fresh patch live across the asks that follow it."""
    try:
        root = ast.parse(value, mode="eval").body
    except SyntaxError:
        return False
    while isinstance(root, (ast.Subscript, ast.Attribute, ast.Call)):
        root = root.value if isinstance(root, (ast.Subscript, ast.Attribute)) else (root.args[0] if root.args else None)
        if root is None:
            return False
    if not isinstance(root, ast.Name):
        return False
    fns = [f for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.lineno <= line <= (f.end_lineno or f.lineno)]
    scope = min(fns, key=lambda f: (f.end_lineno or 0) - f.lineno) if fns else tree
    needle = f"{head}.{attr}"
    for a in ast.walk(scope):
        if isinstance(a, ast.Assign) and a.lineno < line and needle in ast.unparse(a.value):
            names = {n.id for t in a.targets for n in ast.walk(t) if isinstance(n, ast.Name)}
            if root.id in names:
                return True
    return False


def _unwrap(text: str) -> str:
    """``str(x)`` and ``Path(x)`` hand the same binding as ``x``; nothing else is unwrapped."""
    try:
        node = ast.parse(text, mode="eval").body
    except SyntaxError:
        return text
    while isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("str", "Path") and len(node.args) == 1:
        node = node.args[0]
    return ast.unparse(node)


def _launches_open_across(tree, line: int):
    """``launch(...)`` calls made BEFORE ``line`` that are still open across it: entered into an ExitStack (``stack.enter_context(
    launch(...))``, which stays open until the stack closes) or inside a ``with`` that encloses ``line``. A launch whose ``with`` block
    has already closed does not count."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.With) and n.lineno <= line <= (n.end_lineno or n.lineno):
            for item in n.items:
                if isinstance(item.context_expr, ast.Call):
                    out.append(item.context_expr)
        if isinstance(n, ast.Call) and getattr(n, "lineno", line) < line and isinstance(n.func, ast.Attribute) and n.func.attr == "enter_context":
            out.extend(a for a in n.args if isinstance(a, ast.Call))
    return out


def _handed_to_a_launch(body, value: str, before=()) -> bool:
    """The patch's VALUE is handed to a ``launch(...)`` AT OR AFTER the patch, inside the patch's live span (``body``): that is the fix,
    not the defect (3e08102ef35a: the asker keeps the patch it reads itself, and the launched CodeMother is given the same world).
    NARROW ON PURPOSE: the handed argument must be the SAME binding (the same text, or the same text under str()/Path()); a launch
    that merely carries some keyword, a different value, or a launch BEFORE the patch silences nothing."""
    if not value:
        return False
    want = _unwrap(value)
    try:
        if isinstance(ast.parse(want, mode="eval").body, ast.Constant):
            return False          # a literal (None, 1, "x") names no binding: handing the same literal proves nothing
    except SyntaxError:
        return False
    calls = [c for st in body for c in ast.walk(st) if isinstance(c, ast.Call)]
    for root in list(before):
        calls.extend(c for c in ast.walk(root) if isinstance(c, ast.Call))
    for c in calls:
        f = c.func
        if (f.id if isinstance(f, ast.Name) else getattr(f, "attr", "")) != "launch":
            continue
        if any(_unwrap(ast.unparse(a)) == want for a in list(c.args) + [k.value for k in c.keywords]):
            return True
    return False


def _scopes(tree):
    """(target, attr, lineno, body, value): the statements during which a patch is live, and the value it installs."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.With):
            for item in n.items:
                ce = item.context_expr
                if not isinstance(ce, ast.Call):
                    continue
                f = ce.func
                name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                base = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else ""
                if name == "patch" and ce.args and isinstance(ce.args[0], ast.Constant) and isinstance(ce.args[0].value, str) \
                        and "." in ce.args[0].value:
                    d = ce.args[0].value
                    out.append((d.rsplit(".", 1)[0], d.rsplit(".", 1)[1], n.lineno, n.body, _value_text(ce, 1), True, []))
                elif name == "object" and base == "patch" and len(ce.args) >= 2 and isinstance(ce.args[1], ast.Constant):
                    out.append((("alias", ast.unparse(ce.args[0])), ce.args[1].value, n.lineno, n.body, _value_text(ce, 2), True, []))

    def blocks(node):
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list) and block and isinstance(block[0], ast.stmt):
                yield block
        for h in getattr(node, "handlers", []) or []:
            yield h.body

    def with_sites(cls_name: str):
        return [n for n in ast.walk(tree) if isinstance(n, ast.With)
                and any(isinstance(i.context_expr, ast.Call) and isinstance(i.context_expr.func, ast.Name)
                        and i.context_expr.func.id == cls_name for i in n.items)]

    def walk(block, outer_rest, in_def=False, cls=None, fn=None):
        """Every statement of ``block``; an assignment is live for the rest of its block AND of every enclosing block (a try's
        finalbody restores it, the code after the try does not)."""
        for i, st in enumerate(block):
            rest = block[i + 1:] + outer_rest
            if isinstance(st, ast.Assign):
                for tg in st.targets:
                    xs = tg.elts if isinstance(tg, ast.Tuple) else [tg]
                    vs = st.value.elts if isinstance(tg, ast.Tuple) and isinstance(st.value, ast.Tuple) and len(st.value.elts) == len(xs) else None
                    for k, x in enumerate(xs):
                        if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id not in ("self", "cls"):
                            # a tuple target takes the value at ITS position (``a.X, b.Y = str(x), str(y)``), never the whole tuple
                            val = ast.unparse(vs[k] if vs else st.value)
                            out.append((("alias", x.value.id), x.attr, st.lineno, rest, val, in_def, []))
                            if cls and fn is not None and fn.name == "__enter__":
                                # a context manager's __enter__ patches for the BODY of every ``with Class(...)`` that uses it; a launch made in
                                # the same __enter__ stays open across that body (it closes in __exit__), so it counts as handed
                                for w in with_sites(cls):
                                    out.append((("alias", x.value.id), x.attr, w.lineno, w.body, val, True, [fn]))
            inner_rest = rest if not isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else []
            for sub in blocks(st):
                walk(sub, inner_rest, in_def or isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)),
                     st.name if isinstance(st, ast.ClassDef) else cls, st if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn)

    walk(tree.body, [])
    return out


def unseen_patches(source: str, repo_root: Path, *, proof: str = "<proof>") -> dict:
    """The patches in ``source`` (a proof's text) that a judge it asks reads in another process.

    ``{"findings": [{proof, line, target, attr, judge, chain}], "unresolved": [{proof, line, target}]}``. The repo's own judges,
    transitions and import graph are read from ``repo_root``; the proof's TEXT is separate so a pre-fix revision can be judged
    against today's tree."""
    repo_root = Path(repo_root)
    ctx = _ctx(repo_root)
    judges = ctx["judges"]
    tree = ast.parse(source)
    aliases = _aliases(tree)
    asking = _asking_names(tree, judges, aliases, ctx["capable"])
    findings, unresolved, skipped = [], [], []
    for target, attr, line, body, value, in_def, extra_before in _scopes(tree):
        if not in_def:
            # a MODULE-LEVEL assignment is process configuration at import (a worktree's commons fallback, a sandboxed class), not a patch
            # live across one ask: it names no scope the tooth can show an ask inside. Listed as a limit in the module doc.
            skipped.append({"proof": proof, "line": line, "target": f"{target[1] if isinstance(target, tuple) else target}.{attr}"})
            continue
        if _handed_to_a_launch(body, value, list(_launches_open_across(tree, line)) + extra_before):
            continue
        if isinstance(target, tuple) and _is_a_restore(tree, target[1].split(".")[0], attr, line, value):
            continue
        if isinstance(target, tuple):
            head = target[1].split(".")[0]
            mod = aliases.get(head)
            if mod is None:
                unresolved.append({"proof": proof, "line": line, "target": target[1] + "." + attr})
                continue
            target = mod + ("." + target[1].split(".", 1)[1] if "." in target[1] else "")
        f = _file_of(ctx, target) or (_file_of(ctx, target.rsplit(".", 1)[0]) if "." in target else None)
        if f is None:
            continue                                   # a name outside the repo's own modules (stdlib, a seam): not the judge's
        asked: set[str] = set()
        for st in body:
            asked |= _judge_literals(st, judges) | _through_transitions(st, aliases, ctx["capable"])
            for c in ast.walk(st):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in asking:
                    asked |= asking[c.func.id]
        for judge in sorted(asked):
            module = ctx["lane_asker"] if judge.startswith("via transitions") else judges.get(judge)
            reach = _reach(ctx, module) if module else None
            if not reach or f not in reach:
                continue
            starts = _transitions_judges(ctx, repo_root, judge.split(".", 1)[1]) if judge.startswith("via transitions") else {judge}
            reader = _answer_side_reader(ctx, repo_root, _file_of(ctx, module), reach, starts, attr)
            if reader:
                findings.append({"proof": proof, "line": line, "target": f"{target}.{attr}", "attr": attr, "judge": judge,
                                 "chain": reach[f], "read_by": reader})
    return {"findings": findings, "unresolved": unresolved, "module_level": skipped}


def unseen_patch_proofs(repo_root: Path) -> dict[str, list[dict]]:
    """{proof path: findings} over every ``proofs/test_*.py`` of the repo that has any."""
    repo_root = Path(repo_root)
    out: dict[str, list[dict]] = {}
    for p in sorted(repo_root.rglob("proofs/test_*.py")):
        rel = p.relative_to(repo_root).as_posix()
        if "/." in "/" + rel:
            continue
        try:
            got = unseen_patches(p.read_text(encoding="utf-8"), repo_root, proof=rel)["findings"]
        except SyntaxError:
            continue
        if got:
            out[rel] = got
    return out

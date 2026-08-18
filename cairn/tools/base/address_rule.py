"""ADDRESS RULE — the one spelling of "instance-space is resolved, never spelled by hand".

The refusal half of ``address.py``. That module owns where a thing lives; this one owns the
question *did somebody build that address themselves instead of asking*. It is a separate
module for a measured reason and not for tidiness: ``address.py`` imports ``pathlib`` AND
NOTHING ELSE, a property leaned on by every caller that pins an import allowlist, and this
rule needs ``ast``. One file, two import closures, no negotiation.

**IT IS AN AST PREDICATE OVER AN EXPRESSION, NOT A TEXT SCAN — and that is the whole
difference.** The text scan it replaces (``cairn/tools/base/probes/hand_spelled_instance_paths.py``)
had to exclude two files BY NAME, because a probe that must say what it looks for spells the
pattern in its own prose and then finds itself. import_sieve's falsifier names that failure
in one line — *"a mention becomes a catch"* — and the fix is not a better exclusion list, it
is asking a question a mention cannot answer. A mention lives in an ``ast.Constant``. A
spelling is an ``ast.BinOp``. Nothing has to remember to exclude anything.

THE MEASUREMENT THAT CHOSE THE SHAPE (2026-08-17, ticket
``the-instance-address-is-resolved-never-spelled``). Run over the whole package with NO
name-based exclusions at all, the rule draws **9 hits across 270 files**: the 7 hand-spelled
sites this voyage converted, ``address.py`` itself, and one proof. The text scan's own file —
whose docstring spells ``expanduser('~/.cairn')`` twice — does not appear. That is what
collapsed the exemption set from a LIST OF THREE NAMES to a RULE WITH TWO MEMBERS, which was
the ticket's declared load-bearing unknown: *"if the exemption set cannot be stated as a rule
rather than a list of names, this shape is wrong."*

THE TWO EXEMPTIONS, and each is a rule about the file's JOB rather than about its name:

  1. **The module that owns the address.** Somewhere the address is spelled exactly once, and
     that place is ``address.py`` by construction. It is resolved from the module object's own
     ``__file__``, never written as a string here — a hard-coded path would be a second
     spelling of the very thing this module refuses.
  2. **Any file under a ``proofs/`` directory.** A proof that asserts the rule has to construct
     the thing the rule forbids. This is not a courtesy: the live case is
     ``cairn/devices/aider_shim/proofs/test_fence.py:285``, which asserts that the fence's
     record berths under ``Path.home() / ".cairn"`` — the assertion IS the forbidden
     expression, and a rule that redded it would be forbidding its own enforcement.

WHAT THIS DOES NOT SEE, declared rather than discovered later. A path built by concatenation
from a variable, by a dynamic join, or by an f-string that the parser sees as a plain
Constant. The measured corpus has none of those shapes, so the rule is UNFALSIFIED on them
rather than proven complete — carried forward unchanged from the parent ticket's own cast,
where the same blind spot was declared.

**A SCAN THAT READ NO FILES RAISES.** ``HollowScan``, composed from import_sieve rather than
re-invented: a sieve shaken over a tree it did not read reports clean, and clean is what a
working corpus looks like. Law 8's floor — a green over zero files is not a green.

THE WALKER IS COMPOSED, NOT REBUILT. ``import_sieve.walk_py`` already knows that
``__pycache__``, ``.git``, ``node_modules``, ``.venv``, ``venv`` and ``*.egg-info`` are noise;
it was promoted from private to public on 2026-08-17 for this caller, because the two
alternatives were reaching across a component boundary for a private symbol, or growing a
second walker that would eventually disagree with the first about whether ``.venv`` counts.

AUTHORITY: none. This module answers a question. Whether an answer reds a build is
``build_inspector``'s to say, and whether a red is a defect or a ruling is Akien's (Law 6).
"""

from __future__ import annotations

import ast
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.import_sieve import HollowScan, walk_py

# The instance root, named once. Not imported from address.py: what lives there is a resolved
# ``Path``, and what is needed here is the LITERAL a source file would have to contain — the
# two are the same word for opposite reasons, and coupling them would mean a change to the
# resolver silently changing what the rule looks for.
INSTANCE_ROOT = ".cairn"
TILDE_INSTANCE_ROOT = "~/" + INSTANCE_ROOT

# EXEMPTION 1, derived from the module object rather than spelled. If ``address.py`` ever moves
# rung — and components have moved rung once already, on 2026-08-13 — this follows it without
# anyone remembering to.
OWNS_THE_ADDRESS = Path(address.__file__).resolve()

# EXEMPTION 2. A directory name, because that is what the rule is about: not "these files" but
# "anything whose job is to assert the rule", and ``proofs/`` is how this system spells that job.
PROOFS_DIR = "proofs"


def exemption_of(path: Path | str) -> str | None:
    """Why this file may spell the address, or ``None`` if it may not.

    Returns the REASON rather than a boolean, so a caller reporting a skip can say which of the
    two rules applied. A third reason appearing here is the signal the ticket named: the sieve
    has become the hand-widened allowlist this same address retired once, and the honest move
    is to route back rather than add a member.
    """
    p = Path(path).resolve()
    if p == OWNS_THE_ADDRESS:
        return "the module that owns the address"
    if PROOFS_DIR in p.parts:
        return "a proof asserting the rule must construct what the rule forbids"
    return None


def _is_home_call(node: ast.AST) -> bool:
    """``Path.home()`` — the call, with no arguments, off a bare name ``Path``.

    A bare ``Path`` name and not a resolved import: the rule reads source, and a module that
    aliased pathlib would defeat this. That is the same blind spot as the dynamic join, and it
    is declared in the module docstring rather than half-handled here.
    """
    return (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "home"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "Path"
            and not node.args)


def _div_chain(node: ast.BinOp) -> tuple[ast.AST, list[ast.AST]]:
    """Unwind ``a / b / c`` into its left-most operand and its segments, in written order.

    ``/`` is left-associative, so the tree leans left and the base is at the bottom. Only the
    FIRST segment matters to the rule — ``Path.home() / ".cairn" / anything`` is a spelling of
    instance space whatever follows, and ``Path.home() / "dev" / "src"`` is not one however
    long it grows (``venv.py``'s ``AIDER_SRC`` is the live case, and it is legitimate).
    """
    segments: list[ast.AST] = []
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        segments.append(node.right)
        node = node.left
    segments.reverse()
    return node, segments


def _startswith_instance_root(node: ast.AST) -> bool:
    """A string constant naming the tilde form of instance space."""
    return (isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.startswith(TILDE_INSTANCE_ROOT))


def spellings_in(source: str) -> list[dict]:
    """Every hand-spelled instance-space address in one source string, by line.

    Two shapes, which are the two the corpus actually contains:

      A. ``Path.home() / ".cairn" / ...`` — a division chain whose base is the home call and
         whose first literal segment is the instance root.
      B. ``<anything>.expanduser()`` with a ``"~/.cairn"`` literal in its receiver or its
         arguments — which covers both the ``Path("~/.cairn").expanduser()`` dialect and the
         ``os.path.expanduser("~/.cairn")`` one, in one predicate rather than two.

    One entry per LINE, deduplicated: a line holding both shapes is one site to fix, and a
    count that said two would make the floor a number nobody could check against the file.

    Raises ``SyntaxError`` — deliberately unhandled. A source file this cannot parse is not a
    clean file, and swallowing it here is how a scan goes quietly hollow one file at a time
    (Law 7: loud at the diagnostic surface). The caller decides what to do with it.
    """
    found: dict[int, str] = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            base, segments = _div_chain(node)
            if (_is_home_call(base) and segments
                    and isinstance(segments[0], ast.Constant)
                    and segments[0].value == INSTANCE_ROOT):
                found.setdefault(node.lineno, f'Path.home() / "{INSTANCE_ROOT}"')
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "expanduser"):
            reachable = list(ast.walk(node.func.value)) + [a for arg in node.args
                                                           for a in ast.walk(arg)]
            if any(_startswith_instance_root(c) for c in reachable):
                found.setdefault(node.lineno, f'expanduser("{TILDE_INSTANCE_ROOT}")')
    return [{"line": ln, "shape": found[ln]} for ln in sorted(found)]


def scan(root: Path | str | None = None) -> dict:
    """Shake the rule over a tree. ``{count, sites, files_read, exempted, unreadable}``.

    ``root`` defaults to the package (``<repo>/cairn``) and is injectable, which is what lets a
    proof plant a spelling in a temp world instead of asserting against the live corpus — the
    difference between a tooth that pins a rule and one that pins today's count.

    Sites are repo-relative when the tree is inside the repo and absolute otherwise, so a
    fixture scan and a live scan both read plainly.

    An unreadable or unparseable file RIDES THE RETURN rather than vanishing from it: a scan
    that silently skipped what it could not read would report a cleaner corpus the worse its
    own condition got.
    """
    base = Path(root) if root is not None else address.package_root()
    sites: list[dict] = []
    exempted: list[dict] = []
    unreadable: list[dict] = []
    files_read = 0

    for path_str in walk_py(str(base)):
        path = Path(path_str)
        reason = exemption_of(path)
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as e:
            unreadable.append({"path": _rel(path), "why": f"UNREADABLE: {e}"})
            continue
        files_read += 1
        try:
            hits = spellings_in(source)
        except SyntaxError as e:
            unreadable.append({"path": _rel(path), "why": f"UNPARSEABLE: {e}"})
            continue
        if not hits:
            continue
        if reason:
            # AN EXEMPTION IS RECORDED ONLY WHEN IT BEARS WEIGHT. The exempt file is scanned
            # like any other and reported only if it actually spelled the address — so
            # ``exempted`` measures which members of the two-member rule are EARNING their
            # place, rather than listing the hundred-odd proofs that never needed it. An
            # exemption that never appears here is one nothing would notice the loss of, and
            # that is the question the ticket asks about the rule staying closed at two.
            exempted.append({"path": _rel(path), "why": reason,
                             "lines": [h["line"] for h in hits]})
            continue
        for hit in hits:
            sites.append({"site": f"{_rel(path)}:{hit['line']}", "shape": hit["shape"]})

    if files_read == 0:
        raise HollowScan(
            f"the address rule was shaken over {base} and read zero files — "
            "a count of 0 hand-spellings over 0 files is not a measurement"
        )
    return {
        "count": len(sites),
        "sites": sites,
        "files_read": files_read,
        "exempted": exempted,
        "unreadable": unreadable,
    }


def _rel(path: Path) -> str:
    """Repo-relative if it is under the repo, absolute otherwise. Presentation only."""
    try:
        return str(path.resolve().relative_to(address.ROOTS["repo"]))
    except ValueError:
        return str(path)

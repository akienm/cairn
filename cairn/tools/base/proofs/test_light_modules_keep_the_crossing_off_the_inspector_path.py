#!/usr/bin/env python3
"""Proof that the workflow grammar and the ticket-file helpers live in modules that cannot post.

Measured 2026-10-27 (ticket 632edb992aa3, child 3 of e41a94da3fd0): the inspector imported
transitions.py for four grammar names, and transitions.emit fires gate_probes, which dials
bus_client/remote.py and its socket — so the verdict path could reach a host and
test_inspector_nexus.py's fire-path tooth went red. import_sieve.reaches found five edges from
the inspector into transitions: two wanted only the grammar (inspector.py, skill_block.py) and
three wanted only the ticket-file helpers (crossings.py, chain.py, ticket_log.py via
rehearsal.py). The grammar moves to workflow_grammar.py, the helpers to ticket_file.py,
transitions.py imports both back under their old names, and the five edges are repointed.
Akien's answer to open-495f7be4789b: the inspector stops reaching emit.

Teeth, one per falsifier clause (PROVES below), each binding the new modules at call time so
the hollow reading (neither module present) reds the tooth instead of crashing the reader:
  (1) workflow_grammar.py loads nothing that posts: its top-level imports are the standard
      library and DiagnosticBase, and diagnostic.py's own top-level imports are the standard
      library only (Akien 2026-10-27, open-d32047bb1759: "it can write it's own logs, it just
      can't make decisions based on what it's written");
  (2) ticket_file.py's import closure reaches neither transitions.py, nor gate_probes.py,
      nor anything under bus_client/;
  (3) transitions' old names ARE the new modules' objects (one definition, re-exported —
      which is also what keeps ``except transitions.IllegalTransition`` catching);
  (4) the five edges D5 repointed — inspector.py, skill_block.py, chain.py, crossings.py and
      ticket_log.py — import nothing from cairn.tools.base.transitions;
  (5) the base charter's public_interface names both modules;
  (6) ticket_file._TICKETS is the one patch point (D10): transitions carries no _TICKETS, and
      no Python file in cairn/, bin/ or skills/ reads, assigns or imports _TICKETS from
      transitions.
Measured 2026-10-28 (FIXME 1-2): the hollow reading found seven built files no tooth reached.
Clause 4 had named only the two base-side edges and left the other three to
cairn/machines/build_inspector/proofs/test_inspector_nexus.py, which declares no PROVES for this
ticket, so hollow could not count it; and nothing measured D10's patch-point move at all.

    bin/cairn test cairn/tools/base/proofs/test_light_modules_keep_the_crossing_off_the_inspector_path.py
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_BASE = _REPO / "cairn" / "tools" / "base"
_GRAMMAR = _BASE / "workflow_grammar.py"
_TICKET_FILE = _BASE / "ticket_file.py"
_EDGES = ("cairn/machines/build_inspector/inspector.py", "cairn/machines/skill_block/skill_block.py",
          "cairn/tools/chain/chain.py", "cairn/tools/base/crossings.py",
          "cairn/tools/base/ticket_log.py")
_TRANSITIONS = "cairn.tools.base.transitions"

PROVES = {"632edb992aa3": {
    "1": "test_the_grammar_loads_nothing_that_posts",
    "2": "test_the_ticket_file_never_reaches_the_crossing",
    "3": "test_transitions_reexports_the_one_definition",
    "4": "test_the_base_edges_no_longer_import_transitions",
    "5": "test_the_charter_declares_both_modules",
    "6": "test_ticket_file_holds_the_one_patch_point",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            mod = "." * node.level + (node.module or "")
            names.add(mod)
            names.update(f"{mod}.{a.name}" for a in node.names)
    return names


def _top_level_imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            mod = "." * node.level + (node.module or "")
            names.add(mod)
            names.update(f"{mod}.{a.name}" for a in node.names)
    return names


def _stdlib(name: str) -> bool:
    return name.split(".")[0] in sys.stdlib_module_names or name.split(".")[0] == "__future__"


def test_the_grammar_loads_nothing_that_posts() -> None:
    """Akien 2026-10-27, open-d32047bb1759: the grammar may carry the mixin and write its own
    logs; what it may not load is anything that posts or decides. Ticket 66ee1ffc1ec7 moved
    the rules grammar here, which folds case through system_word — a stdlib-only module."""
    mixin = {"cairn.tools.base.diagnostic", "cairn.tools.base.diagnostic.DiagnosticBase",
             "cairn.tools.system_word.system_word", "cairn.tools.system_word.system_word.canon"}
    names = _top_level_imports(_GRAMMAR)
    stray = sorted(n for n in names if not _stdlib(n) and n not in mixin)
    under = sorted(n for f in (_BASE / "diagnostic.py",
                               _REPO / "cairn" / "tools" / "system_word" / "system_word.py")
                   for n in _top_level_imports(f) if not _stdlib(n))
    check("test_the_grammar_loads_nothing_that_posts", not stray and not under and bool(names),
          f"grammar stray {stray}; diagnostic/system_word stray {under}")


def test_the_ticket_file_never_reaches_the_crossing() -> None:
    from cairn.tools.import_sieve import sieve
    graph = sieve.import_graph(str(_REPO))
    reached = sieve.reaches(graph, str(_TICKET_FILE.relative_to(_REPO)))
    bad = sorted(p for p in reached
                 if p in ("cairn/tools/base/transitions.py", "cairn/tools/base/gate_probes.py")
                 or p.startswith("cairn/tools/bus_client/"))
    check("test_the_ticket_file_never_reaches_the_crossing", not bad,
          "; ".join(" -> ".join(reached[p]) for p in bad))


def test_transitions_reexports_the_one_definition() -> None:
    from cairn.tools.base import ticket_file, transitions, workflow_grammar
    pairs = {name: (getattr(transitions, name), getattr(workflow_grammar, name))
             for name in ("parse_workflow", "is_terminal", "is_summons", "MalformedWorkflow",
                          "IllegalTransition", "Workflow", "TERMINAL_STATES",
                          "verify_crossing_fingerprint")}
    pairs.update({old: (getattr(transitions, old), getattr(ticket_file, new))
                  for old, new in (("_find_ticket", "find_ticket"),
                                   ("_ticket_shape", "ticket_shape"),
                                   ("_write_ticket", "write_ticket"))})
    differ = sorted(n for n, (a, b) in pairs.items() if a is not b)
    subclass = issubclass(transitions.EntryGateRed, workflow_grammar.IllegalTransition)
    check("test_transitions_reexports_the_one_definition", not differ and subclass,
          f"not the same object: {differ}; EntryGateRed under the moved IllegalTransition: {subclass}")


def test_the_base_edges_no_longer_import_transitions() -> None:
    if not (_GRAMMAR.is_file() and _TICKET_FILE.is_file()):
        check("test_the_base_edges_no_longer_import_transitions", False,
              "workflow_grammar.py / ticket_file.py absent — the edges have nowhere to point")
        return
    hits = {f: sorted(n for n in _imports(_REPO / f)
                      if n.startswith("cairn.tools.base.transitions")
                      or n == "cairn.tools.base.transitions")
            for f in _EDGES}
    hits = {f: h for f, h in hits.items() if h}
    check("test_the_base_edges_no_longer_import_transitions", not hits, repr(hits))


def test_the_charter_declares_both_modules() -> None:
    if not (_GRAMMAR.is_file() and _TICKET_FILE.is_file()):
        check("test_the_charter_declares_both_modules", False, "the modules it would declare are absent")
        return
    pi = json.loads((_BASE / "intention+why.json").read_text(encoding="utf-8")).get("public_interface") or []
    missing = [m for m in ("cairn.tools.base.workflow_grammar", "cairn.tools.base.ticket_file")
               if m not in pi]
    check("test_the_charter_declares_both_modules", not missing, f"missing {missing}")


def _reads_transitions_tickets(path: Path) -> list[str]:
    """Every place one file reaches _TICKETS through transitions: an import of it, or an
    attribute read or assignment on any name the file binds to the transitions module."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []
    aliases: set[str] = set()
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == _TRANSITIONS:
                hits += [f"{path.name}:{node.lineno} imports _TICKETS"
                         for a in node.names if a.name == "_TICKETS"]
            elif node.module == "cairn.tools.base":
                aliases |= {a.asname or a.name for a in node.names if a.name == "transitions"}
        elif isinstance(node, ast.Import):
            aliases |= {a.asname for a in node.names if a.name == _TRANSITIONS and a.asname}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and node.attr == "_TICKETS"
                and isinstance(node.value, ast.Name) and node.value.id in aliases):
            hits.append(f"{path.name}:{node.lineno} {node.value.id}._TICKETS")
    return hits


def test_ticket_file_holds_the_one_patch_point() -> None:
    from cairn.tools.base import ticket_file, transitions
    own = "_TICKETS" in vars(transitions)
    hits: list[str] = []
    for top in ("cairn", "bin", "skills"):
        for path in sorted((_REPO / top).rglob("*.py")):
            if path.resolve() != Path(__file__).resolve():
                hits += _reads_transitions_tickets(path)
    check("test_ticket_file_holds_the_one_patch_point",
          not own and not hits and hasattr(ticket_file, "_TICKETS"),
          f"transitions carries its own _TICKETS: {own}; reached through transitions: {hits}")


def main() -> int:
    for tooth in (test_the_grammar_loads_nothing_that_posts,
                  test_the_ticket_file_never_reaches_the_crossing,
                  test_transitions_reexports_the_one_definition,
                  test_the_base_edges_no_longer_import_transitions,
                  test_the_charter_declares_both_modules,
                  test_ticket_file_holds_the_one_patch_point):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

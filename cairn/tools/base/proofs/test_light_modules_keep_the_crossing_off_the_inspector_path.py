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
  (1) workflow_grammar.py imports only the standard library, at any depth in the file;
  (2) ticket_file.py's import closure reaches neither transitions.py, nor gate_probes.py,
      nor anything under bus_client/;
  (3) transitions' old names ARE the new modules' objects (one definition, re-exported —
      which is also what keeps ``except transitions.IllegalTransition`` catching);
  (4) crossings.py and ticket_log.py, the two base-side edges, import nothing from
      cairn.tools.base.transitions;
  (5) the base charter's public_interface names both modules.
The inspector-side edges are measured where they belong, by
cairn/machines/build_inspector/proofs/test_inspector_nexus.py's fire-path tooth.

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

PROVES = {"632edb992aa3": {
    "1": "test_the_grammar_imports_only_the_standard_library",
    "2": "test_the_ticket_file_never_reaches_the_crossing",
    "3": "test_transitions_reexports_the_one_definition",
    "4": "test_the_base_edges_no_longer_import_transitions",
    "5": "test_the_charter_declares_both_modules",
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


def test_the_grammar_imports_only_the_standard_library() -> None:
    names = _imports(_GRAMMAR)
    stray = sorted(n for n in names
                   if n.split(".")[0] not in sys.stdlib_module_names and n.split(".")[0] != "__future__")
    check("test_the_grammar_imports_only_the_standard_library", not stray and bool(names),
          f"stray {stray}")


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
    hits = {f: sorted(n for n in _imports(_BASE / f)
                      if n.startswith("cairn.tools.base.transitions")
                      or n == "cairn.tools.base.transitions")
            for f in ("crossings.py", "ticket_log.py")}
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


def main() -> int:
    for tooth in (test_the_grammar_imports_only_the_standard_library,
                  test_the_ticket_file_never_reaches_the_crossing,
                  test_transitions_reexports_the_one_definition,
                  test_the_base_edges_no_longer_import_transitions,
                  test_the_charter_declares_both_modules):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

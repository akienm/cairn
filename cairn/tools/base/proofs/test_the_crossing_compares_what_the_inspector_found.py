#!/usr/bin/env python3
"""Proof that every crossing check is measured by build_inspector and the gate only compares.

Akien 2026-10-27, outline 19.14.1: "the inspector does all the checks. so there is no need for
more checks." Measured 2026-10-28 (ticket 66ee1ffc1ec7, child 2 of e41a94da3fd0): nine lanes in
transitions.py read tickets, journals, validations and repos themselves, so a crossing's verdict
had two mouths. The measuring bodies move into crossing_* functions in
cairn/machines/build_inspector/inspector.py that return each lane's identity, expected, actual
and values; transitions wraps them into the same record entries (only ``source`` changes),
compares them and kicks back.

Teeth, one per falsifier clause (PROVES below), each binding what the build adds at call time
so the hollow reading reds the tooth instead of crashing the reader:
  (1) none of the nine transitions functions calls a world reader, and none calls _lane with
      expected= (it would be building a measurement of its own);
  (2) each of the nine imports exactly one name from the inspector, a crossing_ function the
      inspector defines;
  (3) on fixtures needing no world, every entry transitions returns carries the inspector's
      source and equals what the crossing_ function returns for the same arguments;
  (4) workflow_grammar defines the seven rules helpers, and transitions' names for them are
      the same objects;
  (5) the inspector defines the nine crossing_ functions, and its import closure reaches
      neither transitions.py, nor gate_probes.py, nor anything under bus_client/.

    bin/cairn test cairn/tools/base/proofs/test_the_crossing_compares_what_the_inspector_found.py
"""

from __future__ import annotations

import ast
import json
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_TRANSITIONS = _REPO / "cairn" / "tools" / "base" / "transitions.py"
_INSPECTOR = _REPO / "cairn" / "machines" / "build_inspector" / "inspector.py"
_INSPECTOR_MOD = "cairn.machines.build_inspector.inspector"

NINE = {"inspect_emission": "crossing_emission", "inspect_rules": "crossing_rules",
        "inspect_named_ticket": "crossing_named_ticket", "inspect_fixme": "crossing_fixme",
        "_require_demo": "crossing_demo", "inspect_clearance": "crossing_clearance",
        "inspect_proof_named": "crossing_proof_named", "inspect_durability": "crossing_durability",
        "_quorum_gate": "crossing_quorum"}

WORLD_READERS = {"open", "read_text", "read_bytes", "loads", "load", "is_file", "exists", "glob",
                 "iterdir", "stat", "_find_ticket", "find_ticket", "standing", "read_validations",
                 "validations_path_for_artifact", "repo_truth", "proven_by_since_buildme",
                 "spec_for", "armed_error", "watchme_spec_error", "read_history",
                 "_latest_kick_back", "_when", "_named_on", "_dead_names", "_repo_toplevel",
                 "_durability_roots"}

# The node-class table is live SPEC, borrowed by path from the commons beside the repo, else
# $HOME's — hollow.py's own resolution order. `cairn test --hollow` runs from a worktree with no
# CairnCommons beside it, where transitions' repo-relative _NODE_CLASSES points at nothing
# (measured 2026-10-28: tooth 3 red AT HEAD there, "unknown node-class 'code-seam'").
_NODE_CLASSES = next((c / "node_classes" for c in (_REPO.parent / "CairnCommons",
                                                   Path.home() / "dev" / "src" / "CairnCommons")
                      if (c / "node_classes" / "code-seam.json").is_file()), None)

GRAMMAR = ("is_disposition", "_registered_workflow", "_conform", "canon_target",
           "resolve_target", "_REST_DISPOSITIONS", "legal_targets")

PROVES = {"66ee1ffc1ec7": {
    "1": "test_the_gate_reads_nothing_of_the_world",
    "2": "test_each_lane_asks_its_inspector_function",
    "3": "test_the_record_is_what_the_inspector_found",
    "4": "test_the_rules_grammar_is_one_definition",
    "5": "test_the_inspector_never_reaches_the_crossing",
}, "e41a94da3fd0": {
    "3": "test_each_lane_asks_its_inspector_function",
    "4": "test_the_gate_reads_nothing_of_the_world",
    "5": "test_the_inspector_never_reaches_the_crossing",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _functions(path: Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}


def _called(node: ast.AST) -> str | None:
    f = node.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def test_the_gate_reads_nothing_of_the_world() -> None:
    fns = _functions(_TRANSITIONS)
    faults = []
    for name in NINE:
        fn = fns.get(name)
        if fn is None:
            faults.append(f"{name}: not defined")
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            called = _called(node)
            if called in WORLD_READERS:
                faults.append(f"{name}:{node.lineno} calls {called}")
            if called == "_lane" and any(k.arg == "expected" for k in node.keywords):
                faults.append(f"{name}:{node.lineno} builds a lane with expected=")
    check("test_the_gate_reads_nothing_of_the_world", not faults, "; ".join(faults[:12]))


def test_each_lane_asks_its_inspector_function() -> None:
    fns = _functions(_TRANSITIONS)
    defined = set(_functions(_INSPECTOR))
    faults = []
    for name, want in NINE.items():
        fn = fns.get(name)
        got = sorted({a.name for node in ast.walk(fn) if isinstance(node, ast.ImportFrom)
                      and node.module == _INSPECTOR_MOD for a in node.names}) if fn else []
        if got != [want]:
            faults.append(f"{name} imports {got} from the inspector, not [{want!r}]")
        elif want not in defined:
            faults.append(f"the inspector defines no {want}")
    check("test_each_lane_asks_its_inspector_function", not faults, "; ".join(faults))


def _plain(entry: dict) -> str:
    return json.dumps({k: entry.get(k) for k in ("identity", "expected", "actual", "values")},
                      sort_keys=True, default=str)


def _quorum_record(T) -> list[dict]:
    """_quorum_gate hands its record to BUILD_GATE.run, which raises on red; read it there."""
    seen: list[list[dict]] = []
    gate_ = T.BUILD_GATE
    real = gate_.run
    gate_.run = lambda record, **_kw: (seen.append(record), ("", record))[1]
    try:
        T._quorum_gate(None, {})
    finally:
        gate_.run = real
    return seen[-1] if seen else []


def test_the_record_is_what_the_inspector_found() -> None:
    from cairn.tools.base import ticket_file, transitions as T
    faults = []
    try:
        I = __import__(_INSPECTOR_MOD, fromlist=["x"])
    except Exception as exc:  # noqa: BLE001 — a hollow build reds here, it does not crash
        check("test_the_record_is_what_the_inspector_found", False, f"{type(exc).__name__}: {exc}")
        return
    cd = T.load_class_def("code-seam", root=_NODE_CLASSES or T._NODE_CLASSES)
    at_build = T.parse_workflow("code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED")
    nobody = "000000000000"
    with tempfile.TemporaryDirectory() as tmp:
        hist = str(Path(tmp) / "comp" / "history.json")
        Path(hist).parent.mkdir()
        saved = ticket_file._TICKETS
        ticket_file._TICKETS = Path(tmp) / "tickets"   # the one patch point (632edb992aa3)
        ticket_file._TICKETS.mkdir()
        cases = [
            ("crossing_rules", lambda: T.inspect_rules(at_build, "PROVEME", class_def=cd),
             lambda: I.crossing_rules(at_build, "PROVEME", cd)),
            ("crossing_rules", lambda: T.inspect_rules(at_build, "PROVED", class_def=cd),
             lambda: I.crossing_rules(at_build, "PROVED", cd)),
            ("crossing_emission", lambda: T.inspect_emission("x", None),
             lambda: I.crossing_emission("x", None)),
            ("crossing_named_ticket", lambda: T.inspect_named_ticket("BUILDME", None, history_path=hist),
             lambda: I.crossing_named_ticket("BUILDME", None, history_path=hist,
                                             roster=T._EXEMPT_ROSTER)),
            ("crossing_named_ticket", lambda: T.inspect_named_ticket("BUILDME", nobody, history_path=hist),
             lambda: I.crossing_named_ticket("BUILDME", nobody, history_path=hist,
                                             roster=T._EXEMPT_ROSTER)),
            ("crossing_fixme", lambda: T.inspect_fixme(nobody, history_path=hist),
             lambda: I.crossing_fixme(nobody, history_path=hist)),
            ("crossing_clearance", lambda: T.inspect_clearance("PROVED", {}, history_path=hist),
             lambda: I.crossing_clearance("PROVED", {}, history_path=hist,
                                          roster=T._CLEARANCE_EXEMPT_ROSTER)),
            ("crossing_clearance",
             lambda: T.inspect_clearance("PROVED", {"cleared_by": "cc"}, history_path=hist),
             lambda: I.crossing_clearance("PROVED", {"cleared_by": "cc"}, history_path=hist,
                                          roster=T._CLEARANCE_EXEMPT_ROSTER)),
            ("crossing_proof_named", lambda: T.inspect_proof_named(nobody, {}),
             lambda: I.crossing_proof_named(nobody, {})),
            ("crossing_durability", lambda: T.inspect_durability(nobody, history_path=hist),
             lambda: I.crossing_durability(nobody, history_path=hist)),
            ("crossing_quorum", lambda: _quorum_record(T), lambda: I.crossing_quorum(None, {})),
            ("crossing_demo", lambda: T._require_demo(nobody, {})[1],
             lambda: I.crossing_demo(nobody)),
        ]
        try:
            for fn, gate_record, ask in cases:
                try:
                    record, checks = gate_record(), ask()
                except Exception as exc:  # noqa: BLE001 — each case reds alone
                    faults.append(f"{fn}: {type(exc).__name__}: {exc}")
                    continue
                want = "build_inspector.inspector." + fn
                wrong = [e.get("identity") for e in record if e.get("source") != want]
                if wrong or not record:
                    faults.append(f"{fn}: entries {wrong or '(none)'} do not carry source {want!r}")
                if [_plain(e) for e in record] != [_plain(c) for c in checks]:
                    faults.append(f"{fn}: the record differs from the inspector's own checks")
        finally:
            ticket_file._TICKETS = saved
    check("test_the_record_is_what_the_inspector_found", not faults, "; ".join(faults[:8]))


def test_the_rules_grammar_is_one_definition() -> None:
    from cairn.tools.base import transitions, workflow_grammar
    missing = [n for n in GRAMMAR if not hasattr(workflow_grammar, n)]
    differ = [n for n in GRAMMAR if n not in missing
              and getattr(transitions, n, None) is not getattr(workflow_grammar, n)]
    check("test_the_rules_grammar_is_one_definition", not missing and not differ,
          f"workflow_grammar lacks {missing}; transitions differs on {differ}")


def test_the_inspector_never_reaches_the_crossing() -> None:
    from cairn.tools.import_sieve import sieve
    graph = sieve.import_graph(str(_REPO))
    reached = sieve.reaches(graph, str(_INSPECTOR.relative_to(_REPO)))
    bad = sorted(p for p in reached
                 if p in ("cairn/tools/base/transitions.py", "cairn/tools/base/gate_probes.py")
                 or p.startswith("cairn/tools/bus_client/"))
    absent = sorted(set(NINE.values()) - set(_functions(_INSPECTOR)))   # the checks must BE there
    check("test_the_inspector_never_reaches_the_crossing", not bad and not absent,
          "; ".join([" -> ".join(reached[p]) for p in bad[:3]]
                    + ([f"the inspector defines none of {absent}"] if absent else [])))


def main() -> int:
    print("the crossing compares what the inspector found (ticket 66ee1ffc1ec7):")
    for tooth in (test_the_gate_reads_nothing_of_the_world, test_each_lane_asks_its_inspector_function,
                  test_the_record_is_what_the_inspector_found, test_the_rules_grammar_is_one_definition,
                  test_the_inspector_never_reaches_the_crossing):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — every tooth prints, none crashes the run
            check(tooth.__name__, False, f"{type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

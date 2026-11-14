#!/usr/bin/env python3
"""Teeth about the inspector's own source, moved in from outside proofs (ticket 93fa3e3a6199, D5).

Each of these used to sit in a proof outside codemother and join a path into her to read
inspector.py. Once build_inspector berths among codemother's machines, a proof ABOUT her source
is hers, so each tooth moved here with its PROVES key, and the outside proof keeps a pointer:

  - the exemption sieve's def stands in the inspector, from
    cairn/machines/exemptions/proofs/test_exemption_set.py (892a0f9cd925, the closure tooth);
  - the inspector defines the nine crossing_ checks and its import closure reaches neither the
    crossing nor the bus client, from cairn/tools/base/proofs/test_the_crossing_compares_what_the_inspector_found.py
    (66ee1ffc1ec7 clause 5, e41a94da3fd0 clause 5);
  - crossing_durability composes repo_truth and shells no git, from
    cairn/tools/base/proofs/test_the_stones_are_pushed.py, step (e) (c2460ae6c3d1);
  - the verdict path cannot reach the graph tree, and every inspector sieve is a record
    sieve, from cairn/tools/import_sieve/proofs/test_import_sieve.py;
  - the inspector imports nothing from transitions, from
    cairn/tools/base/proofs/test_light_modules_keep_the_crossing_off_the_inspector_path.py
    (632edb992aa3 clause 4, the inspector's one edge of the five);
  - the inspector never says follow-up, from cairn/tools/question/proofs/test_question_links.py's
    wording tooth (bc7b64626405 wording).

    bin/cairn test cairn/devices/codemother/machines/build_inspector/proofs/test_the_inspectors_own_source_answers_what_outside_proofs_asked.py
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_INSPECTOR = Path(__file__).resolve().parents[1] / "inspector.py"
_INSPECTOR_REL = _INSPECTOR.relative_to(_REPO).as_posix()

PROVES = {
    "892a0f9cd925": {"nothing here reaches an inference host": "the_exemption_sieve_def_stands_in_the_inspector"},
    "66ee1ffc1ec7": {"5": "test_the_inspector_never_reaches_the_crossing"},
    "e41a94da3fd0": {"5": "test_the_inspector_never_reaches_the_crossing"},
    "c2460ae6c3d1": {"all": "crossing_durability_composes_repo_truth_and_shells_no_git"},
    "bc7b64626405": {"wording": "the_inspector_never_says_follow_up"},
    "632edb992aa3": {"4": "the_inspector_edge_no_longer_imports_transitions"},
}

_EXEMPTION_SIEVE = "every_exemption_cites_a_ruling_or_an_impossibility"
NINE = ("crossing_emission", "crossing_rules", "crossing_named_ticket", "crossing_fixme",
        "crossing_demo", "crossing_clearance", "crossing_proof_named", "crossing_durability",
        "crossing_quorum")


def _source() -> str:
    return _INSPECTOR.read_text(encoding="utf-8")


def _functions() -> dict[str, ast.FunctionDef]:
    return {n.name: n for n in ast.parse(_source()).body if isinstance(n, ast.FunctionDef)}


def the_exemption_sieve_def_stands_in_the_inspector() -> None:
    assert ("\ndef %s(" % _EXEMPTION_SIEVE) in _source(), (
        f"the sieve {_EXEMPTION_SIEVE} is not defined in {_INSPECTOR_REL}")


def test_the_inspector_never_reaches_the_crossing() -> None:
    from cairn.tools.import_sieve import sieve
    reached = sieve.reaches(sieve.import_graph(str(_REPO)), _INSPECTOR_REL)
    bad = sorted(p for p in reached
                 if p in ("cairn/tools/base/transitions.py", "cairn/tools/base/gate_probes.py")
                 or p.startswith("cairn/tools/bus_client/"))
    absent = sorted(set(NINE) - set(_functions()))   # the checks must BE there
    assert not bad and not absent, "; ".join(
        [" -> ".join(reached[p]) for p in bad[:3]]
        + ([f"the inspector defines none of {absent}"] if absent else []))


def crossing_durability_composes_repo_truth_and_shells_no_git() -> None:
    fn = _functions().get("crossing_durability")
    assert fn is not None, f"no FunctionDef crossing_durability in {_INSPECTOR_REL}"
    imports = [n for n in ast.walk(fn) if isinstance(n, ast.ImportFrom)
               and n.module == "cairn.tools.orient.orient"
               and any(a.name == "repo_truth" for a in n.names)]
    assert imports, "crossing_durability must import repo_truth from cairn.tools.orient.orient"
    shelled = [n for n in ast.walk(fn)
               if (isinstance(n, ast.Name) and n.id == "subprocess")
               or (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "subprocess")]
    assert not shelled, "crossing_durability composes repo_truth — it shells no git of its own"


def the_verdict_path_cannot_reach_the_graph_tree() -> None:
    """Measured 2026-08-12: the closure from inspector.py was 17 files, no denied door among
    them. Asserted as an invariant, with a floor so an empty walk cannot read green."""
    from cairn.tools.import_sieve import sieve
    g = sieve.import_graph(str(_REPO))
    caught = sieve.catches(g, {"kind": "unreachable", "capability": "the graph tree",
                               "modules": ("cairn.tools.tree.tree", "cairn.devices.librarian",
                                           "cairn.devices.db_domain"),
                               "start": _INSPECTOR_REL})
    assert caught == [], f"the verdict path can reach the graph tree: {caught}"
    assert len(sieve.reaches(g, _INSPECTOR_REL)) > 5, (
        "the closure from the verdict path came back nearly empty — the tooth above would be "
        "green because nothing was walked")


def every_inspector_sieve_is_a_record_sieve() -> None:
    from cairn.tools.import_sieve import sieve
    from cairn.devices.codemother.machines.build_inspector import inspector
    wanted = set(inspector.sieve_names())
    phases = {k: v for k, v in sieve.phase_of(_source()).items() if k in wanted}
    assert phases, "no SIEVES resolved to module-level functions — the walk missed them"
    assert all(v == 1 for v in phases.values()), f"expected all record (1), got: {phases}"


def the_inspector_never_says_follow_up() -> None:
    word = re.compile(r"follow[-_]ups?\b", re.IGNORECASE)
    tellers = [f"{_INSPECTOR_REL}:{n}" for n, line in enumerate(_source().splitlines(), 1)
               if word.search(line) and "pre-build" not in line and "pre-2026-09-14" not in line]
    assert not tellers, f"the inspector still says follow-up: {tellers[:6]}"


def the_inspector_edge_no_longer_imports_transitions() -> None:
    names = set()
    for n in ast.walk(ast.parse(_source())):
        if isinstance(n, ast.Import):
            names.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            names.add(n.module)
            names.update(f"{n.module}.{a.name}" for a in n.names)   # from cairn.tools.base import transitions
    hits = sorted(n for n in names if n == "cairn.tools.base.transitions"
                  or n.startswith("cairn.tools.base.transitions."))
    assert names, f"no imports read from {_INSPECTOR_REL} — the walk saw nothing"
    assert not hits, f"{_INSPECTOR_REL} imports {hits}"


TEETH = (the_exemption_sieve_def_stands_in_the_inspector, test_the_inspector_never_reaches_the_crossing,
         crossing_durability_composes_repo_truth_and_shells_no_git,
         the_verdict_path_cannot_reach_the_graph_tree, every_inspector_sieve_is_a_record_sieve,
         the_inspector_never_says_follow_up, the_inspector_edge_no_longer_imports_transitions)


def main() -> int:
    red = 0
    for fn in TEETH:
        try:
            fn()
            print(f"  green  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            red += 1
            print(f"  RED    {fn.__name__}: {type(e).__name__}: {e}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())

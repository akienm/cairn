"""Proof for ticket d23ca0e54d00 — the tree tool names itself the one graph-tree tool every
learning block uses (outline 19.29, Q#54, Akien 2026-11-05).

Teeth a hollow build could not pass (the build is prose: the module docstring and the charter):

  1. tree.py's module docstring names cairn/tools/tree/tree.py as the one graph-tree tool every
     learning block uses, cites outline 19.29 (Q#54), and carries none of the chart-only
     phrasings ('chart/tree.py', 'Stone 2 of the chart device', "that rung for chart's nexi").
  2. the docstring says a learning block needing a special adaptation subclasses the tool, and
     names OWNER = 'chart' as the default.
  3. the charter's what and why say the same: one tool, users not an owner, a subclass for an
     adaptation, outline 19.29.
  4. behaviour unchanged (a guard): OWNER == 'chart', nexus_table('survey') ==
     'chart_survey_nodes', and the tree tool's two other proofs stay green.

    python3 cairn/tools/tree/proofs/test_tree_names_itself_the_one_tool.py   # exit 0 = green
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

TOOL = REPO / "cairn" / "tools" / "tree"
PROOF_TIMEOUT_S = 900

PROVES = {
    "d23ca0e54d00": {
        "1": "clause_1_docstring_names_the_one_tool",
        "2": "clause_2_docstring_names_subclass_and_default",
        "3": "clause_3_charter_says_the_same",
        "4": "clause_4_behaviour_unchanged",
    },
}

FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:900]}", flush=True)
        FAILURES.append(name)


def _doc() -> str:
    return ast.get_docstring(ast.parse((TOOL / "tree.py").read_text())) or ""


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def clause_1_docstring_names_the_one_tool() -> None:
    d = _norm(_doc())
    lacks = []
    if "cairn/tools/tree/tree.py" not in d:
        lacks.append("does not name cairn/tools/tree/tree.py")
    if "one graph-tree tool every learning block uses" not in d:
        lacks.append("does not say 'the one graph-tree tool every learning block uses'")
    if "19.29" not in d or "q#54" not in d:
        lacks.append("does not cite outline 19.29 and Q#54")
    for bad in ("chart/tree.py", "stone 2 of the chart device", "that rung for chart's nexi"):
        if bad in d:
            lacks.append(f"still carries {bad!r}")
    _check("clause_1_docstring_names_the_one_tool", not lacks, "; ".join(lacks))


def clause_2_docstring_names_subclass_and_default() -> None:
    d = _norm(_doc())
    lacks = []
    if "subclass" not in d:
        lacks.append("does not say a special adaptation is a subclass")
    if "owner = 'chart'" not in d and 'owner = "chart"' not in d:
        lacks.append("does not name OWNER = 'chart' as the default")
    elif "default" not in d:
        lacks.append("names OWNER = 'chart' but not as the default")
    _check("clause_2_docstring_names_subclass_and_default", not lacks, "; ".join(lacks))


def clause_3_charter_says_the_same() -> None:
    ch = json.loads((TOOL / "intention+why.json").read_text())
    text = _norm(ch.get("what", "") + " " + ch.get("why", ""))
    lacks = []
    if "every learning block" not in text:
        lacks.append("what/why does not say it is the one tool every learning block uses")
    if "users" not in text or "not an owner" not in text:
        lacks.append("what/why does not say it has users, not an owner")
    if "subclass" not in text:
        lacks.append("what/why does not say an adaptation is a subclass")
    if "19.29" not in text:
        lacks.append("what/why does not cite outline 19.29")
    _check("clause_3_charter_says_the_same", not lacks, "; ".join(lacks))


def clause_4_behaviour_unchanged() -> None:
    from cairn.tools.base.script_argv import bash_script_argv
    from cairn.tools.tree import tree
    lacks = []
    if tree.OWNER != "chart":
        lacks.append(f"OWNER is {tree.OWNER!r}, not 'chart'")
    if tree.nexus_table("survey") != "chart_survey_nodes":
        lacks.append(f"nexus_table('survey') is {tree.nexus_table('survey')!r}")
    proofs = [str(TOOL / "proofs" / "test_chart_tree.py"), str(TOOL / "proofs" / "test_questions.py")]
    try:
        r = subprocess.run([*bash_script_argv(REPO / "bin" / "cairn"), "test", "--timeout", "600", *proofs],
                           capture_output=True, text=True, timeout=800, cwd=REPO)
        out = r.stdout + r.stderr
        if "2 green · 0 red" not in out:
            lacks.append("the tree tool's two proofs are not both green: " + out[-600:])
    except subprocess.TimeoutExpired:
        lacks.append("the tree tool's two proofs did not finish in 800s")
    _check("clause_4_behaviour_unchanged", not lacks, "; ".join(lacks))


def main() -> int:
    for name in PROVES["d23ca0e54d00"].values():
        try:
            globals()[name]()
        except Exception as e:  # a tooth that raises is a red, loudly (Law 7)
            _check(name, False, f"{type(e).__name__}: {e}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    raise SystemExit(main())

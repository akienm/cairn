"""Proof for ticket 3415a742fd0a — the ground loop reads the ruled cadence from the liveness tool.

CADENCE_S = 60.0 (Akien, 2026-08-22) moves down to cairn/tools/liveness/liveness.py (ticket
c3b14029d6d8). The ground loop stops defining its own copy and imports the tool's, so the number
has one definition site and nothing outside the cairn device needs to reach into __main__ for it
(RULE 1, Akien 2026-10-01). __main__ still binds the name, so the ground loop's own proofs that
import it from __main__ (test_stop_is_prompt.py, same component) read the same value.

This proof measures only the ground loop (RULE 1: a ticket's proofs measure its own component);
it reads the tool only through its public interface.

  1. THE LOOP DEFINES NO CADENCE OF ITS OWN. __main__.py has no top-level assignment to CADENCE_S.
  2. THE LOOP IMPORTS THE TOOL'S. __main__.py imports CADENCE_S from cairn.tools.liveness.liveness.
  3. THE LOOP BEATS AT IT. main()'s default `cadence` is the name CADENCE_S, and the value
     __main__ binds is the tool's own object.

    python3 cairn/devices/cairn/machines/ground_loop/proofs/test_the_ground_loop_reads_the_tools_cadence.py
"""
import ast
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"3415a742fd0a": {"1": "the_loop_defines_no_cadence_of_its_own",
                           "2": "the_loop_imports_the_tools",
                           "3": "the_loop_beats_at_it"}}

TOOL = "cairn.tools.liveness.liveness"
MAIN_FILE = Path(__file__).resolve().parents[1] / "__main__.py"

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _tree():
    return ast.parse(MAIN_FILE.read_text(encoding="utf-8"))


def the_loop_defines_no_cadence_of_its_own():
    own = [n.lineno for n in _tree().body
           if isinstance(n, (ast.Assign, ast.AnnAssign))
           and any(isinstance(t, ast.Name) and t.id == "CADENCE_S"
                   for t in (n.targets if isinstance(n, ast.Assign) else [n.target]))]
    assert not own, f"__main__.py still defines CADENCE_S at line(s) {own}"


def the_loop_imports_the_tools():
    hits = [n for n in _tree().body if isinstance(n, ast.ImportFrom) and n.module == TOOL
            and any(a.name == "CADENCE_S" and a.asname in (None, "CADENCE_S") for a in n.names)]
    assert hits, f"__main__.py does not import CADENCE_S from {TOOL}"


def the_loop_beats_at_it():
    main = next((n for n in _tree().body if isinstance(n, ast.FunctionDef) and n.name == "main"), None)
    assert main is not None, "__main__.py has no main()"
    a = main.args
    pairs = list(zip(a.kwonlyargs, a.kw_defaults)) + \
        list(zip(a.args[len(a.args) - len(a.defaults):], a.defaults))
    default = next((d for x, d in pairs if x.arg == "cadence"), None)
    assert isinstance(default, ast.Name) and default.id == "CADENCE_S", \
        f"main()'s default cadence is {ast.unparse(default) if default else None!r}, not CADENCE_S"
    import importlib
    mine = importlib.import_module("cairn.devices.cairn.machines.ground_loop.__main__").CADENCE_S
    tools = getattr(importlib.import_module(TOOL), "CADENCE_S", None)
    assert mine is tools, f"__main__ binds CADENCE_S={mine!r}, not the tool's object ({tools!r})"


TEETH = [the_loop_defines_no_cadence_of_its_own, the_loop_imports_the_tools, the_loop_beats_at_it]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)

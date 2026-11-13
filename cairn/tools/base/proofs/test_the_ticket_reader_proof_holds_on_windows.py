"""Proof that test_the_ticket_is_three_files reads Windows paths as Windows spells them.

Measured 2026-11-13 on Windows, three of that proof's four red reader teeth were the proof's own
spelling, not a reader's defect:
  - r_whatsnext ran the bare word ``bash``, which CreateProcess resolves to the WSL launcher, and
    handed it a backslash path;
  - r_inbox cut the source path at the last ``/``, so a backslash path never split;
  - r_skill_block looked for ``/nowhere/idea-berth.json`` inside ``repr(got)``, where the key the
    reader resolved reads ``C:\\\\nowhere\\\\...`` (backslashes doubled by repr).
On Linux all three spellings already agree, so only a read of the proof's source can red there.

No tooth spawns a process. Each scanner first runs over a known-bad and a known-good snippet, so
neither can read green by finding nothing.

    python <this file>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SUBJECT = REPO / "cairn/tools/base/proofs/test_the_ticket_is_three_files.py"

PROVES = {
    "349584bb8f69": {
        "1": "whatsnext_runs_the_hosts_bash_on_a_posix_path",
        "2": "the_inbox_source_is_named_by_path_not_by_slash",
        "3": "the_skill_block_berth_is_looked_up_as_the_reader_resolved_it",
    },
}


def _func(source: str, name: str) -> ast.FunctionDef:
    fn = next((n for n in ast.walk(ast.parse(source))
               if isinstance(n, ast.FunctionDef) and n.name == name), None)
    if fn is None:
        raise AssertionError(f"{name} is gone from the proof under scan")
    return fn


def run_argv_is_bare_bash(source: str, func: str) -> list[int]:
    """Lines of ``subprocess.run([...])`` in ``func`` whose argv starts with the bare string "bash"."""
    bad, seen = [], 0
    for n in ast.walk(_func(source, func)):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
                and n.args and isinstance(n.args[0], ast.List) and n.args[0].elts):
            seen += 1
            head = n.args[0].elts[0]
            if isinstance(head, ast.Constant) and head.value == "bash":
                bad.append(n.lineno)
    if not seen:
        raise AssertionError(f"{func} runs no subprocess any more — the scan has nothing to hold")
    return bad


def run_path_is_not_posix(source: str, func: str) -> list[int]:
    """Lines of ``subprocess.run([bash, <path>])`` in ``func`` whose script argument is not ``.as_posix()``."""
    bad, seen = [], 0
    for n in ast.walk(_func(source, func)):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
                and n.args and isinstance(n.args[0], ast.List) and len(n.args[0].elts) >= 2):
            seen += 1
            v = n.args[0].elts[1]
            if not (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                    and v.func.attr == "as_posix"):
                bad.append(n.lineno)
    if not seen:
        raise AssertionError(f"{func} runs no subprocess with a script path any more")
    return bad


def slash_splits(source: str, func: str) -> list[int]:
    """Lines in ``func`` that call ``.rsplit("/", ...)`` or ``.split("/")`` on something."""
    bad = []
    for n in ast.walk(_func(source, func)):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("rsplit", "split") and n.args
                and isinstance(n.args[0], ast.Constant) and n.args[0].value == "/"):
            bad.append(n.lineno)
    return bad


def repr_lookups(source: str, func: str) -> list[int]:
    """Lines in ``func`` of ``<x> in repr(<y>)``."""
    bad, seen = [], 0
    for n in ast.walk(_func(source, func)):
        if isinstance(n, ast.Compare) and any(isinstance(o, ast.In) for o in n.ops):
            seen += 1
            r = n.comparators[0]
            if isinstance(r, ast.Call) and isinstance(r.func, ast.Name) and r.func.id == "repr":
                bad.append(n.lineno)
    if not seen:
        raise AssertionError(f"{func} looks nothing up with `in` any more")
    return bad


_BAD = (
    "def f():\n"
    "    p = subprocess.run(['bash', str(x)], capture_output=True)\n"
    "    a = s.rsplit('/', 1)[-1]\n"
    "    return '/n' in repr(got), got\n"
)
_GOOD = (
    "def f():\n"
    "    p = subprocess.run([shutil.which('bash') or 'bash', x.as_posix()], capture_output=True)\n"
    "    a = Path(s).name\n"
    "    return str(Path('/n').resolve()) in got, got\n"
)


def _the_scanners_red_the_bad_spelling_and_pass_the_good_one() -> None:
    assert run_argv_is_bare_bash(_BAD, "f") == [2] and run_argv_is_bare_bash(_GOOD, "f") == []
    assert run_path_is_not_posix(_BAD, "f") == [2] and run_path_is_not_posix(_GOOD, "f") == []
    assert slash_splits(_BAD, "f") == [3] and slash_splits(_GOOD, "f") == []
    assert repr_lookups(_BAD, "f") == [4] and repr_lookups(_GOOD, "f") == []


def _src() -> str:
    _the_scanners_red_the_bad_spelling_and_pass_the_good_one()
    return SUBJECT.read_text(encoding="utf-8")


def whatsnext_runs_the_hosts_bash_on_a_posix_path():
    src = _src()
    bare = run_argv_is_bare_bash(src, "r_whatsnext")
    notposix = run_path_is_not_posix(src, "r_whatsnext")
    assert not bare and not notposix, f"r_whatsnext: bare bash at {bare}, non-posix script path at {notposix}"


def the_inbox_source_is_named_by_path_not_by_slash():
    bad = slash_splits(_src(), "r_inbox")
    assert not bad, f"r_inbox splits a path on '/' at {bad}"


def the_skill_block_berth_is_looked_up_as_the_reader_resolved_it():
    bad = repr_lookups(_src(), "r_skill_block")
    assert not bad, f"r_skill_block looks a path up inside repr(...) at {bad}"


TEETH = [whatsnext_runs_the_hosts_bash_on_a_posix_path,
         the_inbox_source_is_named_by_path_not_by_slash,
         the_skill_block_berth_is_looked_up_as_the_reader_resolved_it]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {type(e).__name__}: {e}  [{t.__name__}]")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

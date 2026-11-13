"""Proof for the dotted-address proof's path comparison — it compares POSIX against POSIX.

Measured 2026-11-13 on Windows: ``cairn <device>.<n> <verb>`` prints the resolved verb path with
the dispatcher's own ``/`` joints under a root Windows spells with backslashes, so the line is
``C:\\...\\devices/<device>/0/bin/verb`` while ``str(root / ...)`` is all backslashes. The
launcher is right; the byte compare in ``test_cairn_instance_address.py`` was not. Re-spelling
both sides as POSIX turned that proof and ``test_the_launcher_reads_the_bin_beside_the_code``
(which runs it) from red to green. On Linux the two spellings are already equal, so only a read
of the proof's own source can red there.

Neither tooth spawns a process. Each runs its scanner over a known-bad and a known-good snippet
first, so neither can read green by finding nothing.

    python <this file>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUBJECT = REPO / "bin/proofs/test_cairn_instance_address.py"
FUNCS = ("_clause_a", "_clause_b", "_fold_before_split")

PROVES = {
    "f695fac922cd": {
        "1": "every_expected_path_is_spelled_posix",
        "2": "every_resolved_path_is_compared_posix",
    },
}


def _func(source: str, name: str) -> ast.FunctionDef:
    fn = next((n for n in ast.walk(ast.parse(source))
               if isinstance(n, ast.FunctionDef) and n.name == name), None)
    if fn is None:
        raise AssertionError(f"{name} is gone from the proof under scan")
    return fn


def want_assigns_not_posix(source: str, func: str) -> list[int]:
    """Lines of ``want = <expr>`` in ``func`` whose value is not ``<expr>.as_posix()``.
    Raises when ``func`` assigns no ``want``, so a rename cannot read green."""
    bad, seen = [], 0
    for n in ast.walk(_func(source, func)):
        if (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "want"):
            seen += 1
            v = n.value
            if not (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                    and v.func.attr == "as_posix"):
                bad.append(n.lineno)
    if not seen:
        raise AssertionError(f"{func} assigns no `want` any more — the scan has nothing to hold")
    return bad


def stdout_compares_not_posix(source: str, func: str) -> list[int]:
    """Lines of ``assert r.stdout == want + ...`` in ``func`` whose left side is the bare
    ``r.stdout`` instead of ``_posix(r.stdout)``."""
    bad, seen = [], 0
    for n in ast.walk(_func(source, func)):
        if not (isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.ops[0], ast.Eq)):
            continue
        right = n.comparators[0]
        if not (isinstance(right, ast.BinOp) and isinstance(right.left, ast.Name)
                and right.left.id == "want"):
            continue
        seen += 1
        left = n.left
        wrapped = (isinstance(left, ast.Call) and isinstance(left.func, ast.Name)
                   and left.func.id == "_posix")
        if not wrapped:
            bad.append(n.lineno)
    if not seen:
        raise AssertionError(f"{func} compares no stdout to `want + ...` any more")
    return bad


def _the_scanners_red_a_bare_spelling_and_pass_a_posix_one() -> None:
    bare = "def f():\n    want = str(root / 'a')\n    assert r.stdout == want + '\\n'\n"
    good = "def f():\n    want = (root / 'a').as_posix()\n    assert _posix(r.stdout) == want + '\\n'\n"
    assert want_assigns_not_posix(bare, "f") == [2]
    assert want_assigns_not_posix(good, "f") == []
    assert stdout_compares_not_posix(bare, "f") == [3]
    assert stdout_compares_not_posix(good, "f") == []


def every_expected_path_is_spelled_posix():
    _the_scanners_red_a_bare_spelling_and_pass_a_posix_one()
    src = SUBJECT.read_text(encoding="utf-8")
    bad = {f: want_assigns_not_posix(src, f) for f in FUNCS}
    bad = {f: ls for f, ls in bad.items() if ls}
    assert not bad, f"`want` is not spelled with as_posix(): {bad}"


def every_resolved_path_is_compared_posix():
    _the_scanners_red_a_bare_spelling_and_pass_a_posix_one()
    src = SUBJECT.read_text(encoding="utf-8")
    bad = {f: stdout_compares_not_posix(src, f) for f in FUNCS}
    bad = {f: ls for f, ls in bad.items() if ls}
    assert not bad, f"stdout is compared without _posix(): {bad}"


TEETH = [every_expected_path_is_spelled_posix, every_resolved_path_is_compared_posix]


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

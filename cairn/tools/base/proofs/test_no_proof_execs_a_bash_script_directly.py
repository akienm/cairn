"""Proof for ticket d423852d0a68 — ten proofs build the argv for a bash script (bin/cairn, a
launcher, an askpass, a berth ``ask``) with ``bash_script_argv`` instead of the bare path.

Measured 2026-11-12 on Windows: ``subprocess`` on a shebang script raises ``OSError: [WinError
193] %1 is not a valid Win32 application``. ``bash_script_argv`` returns ``[path]`` on POSIX and
``[bash, path]`` on NT, so the edit is a no-op on Linux and the proofs run on Windows.

Both teeth read the ten files' source with ast; neither spawns a process. Tooth 1 first runs the
scanner over a fixture, so it cannot read green by finding nothing.

    python <this file>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]

TEN = [
    "cairn/devices/cc/proofs/test_superclaude_bare_box.py",
    "cairn/devices/codemother/machines/clearance/proofs/test_clearance_berths_in_codemother.py",
    "cairn/devices/codemother/proofs/test_codemother_learning_lands_in_its_own_tables.py",
    "cairn/devices/codemother/proofs/test_codemother_shows_an_artifact.py",
    "cairn/devices/librarian/proofs/test_librarian_ask.py",
    "cairn/devices/operator/proofs/test_the_operator_verbs_are_in_its_bin.py",
    "cairn/devices/recovery/proofs/test_launchers_moved_to_their_devices.py",
    "cairn/tools/operator_inbox/proofs/test_one_status_everywhere.py",
    "cairn/tools/operator_inbox/proofs/test_operator_inbox.py",
    "cairn/tools/tree/proofs/test_tree_names_itself_the_one_tool.py",
]

PROVES = {
    "d423852d0a68": {
        "1": "the_ast_scan_finds_no_argv_headed_by_a_bare_script_path",
        "2": "each_of_the_ten_proofs_imports_bash_script_argv",
    },
}

_SPAWNERS = {"run", "Popen", "check_output", "check_call", "call", "_run"}


def bare_heads(source: str) -> list[int]:
    """Line numbers of spawn calls whose argv head is ``str(<path>)`` rather than a starred
    ``bash_script_argv(...)`` (or ``sys.executable``, which is no script)."""
    out = []
    for n in ast.walk(ast.parse(source)):
        if not isinstance(n, ast.Call):
            continue
        name = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
        if name not in _SPAWNERS or not n.args:
            continue
        first = n.args[0]
        head = first.elts[0] if isinstance(first, (ast.List, ast.Tuple)) and first.elts else first
        if isinstance(head, ast.Call) and isinstance(head.func, ast.Name) and head.func.id == "str":
            out.append(head.lineno)
    return out


def imports_bash_script_argv(source: str) -> bool:
    return any(isinstance(n, ast.ImportFrom) and n.module == "cairn.tools.base.script_argv"
               and any(a.name == "bash_script_argv" for a in n.names)
               for n in ast.walk(ast.parse(source)))


def the_ast_scan_finds_no_argv_headed_by_a_bare_script_path():
    _the_scanner_reds_a_bare_head_and_passes_a_starred_one()  # the scan cannot read green by seeing nothing
    found = {}
    for rel in TEN:
        lines = bare_heads((REPO / rel).read_text(encoding="utf-8"))
        if lines:
            found[rel] = lines
    assert not found, f"bare script path at the head of an argv: {found}"


def each_of_the_ten_proofs_imports_bash_script_argv():
    missing = [rel for rel in TEN
               if not imports_bash_script_argv((REPO / rel).read_text(encoding="utf-8"))]
    assert not missing, f"no `from cairn.tools.base.script_argv import bash_script_argv`: {missing}"


def _the_scanner_reds_a_bare_head_and_passes_a_starred_one():
    bare = ("import subprocess\n"
            "subprocess.run([str(P / 'bin' / 'cairn'), 'x'])\n"
            "_run(str(P / 'bin/cairn'), 'y')\n")
    fixed = ("import subprocess\n"
             "subprocess.run([*bash_script_argv(P / 'bin' / 'cairn'), 'x'])\n"
             "_run(*bash_script_argv(P / 'bin/cairn'), 'y')\n"
             "_run(sys.executable, '-m', 'z')\n")
    assert bare_heads(bare) == [2, 3], bare_heads(bare)
    assert bare_heads(fixed) == [], bare_heads(fixed)


TEETH = [the_ast_scan_finds_no_argv_headed_by_a_bare_script_path,
         each_of_the_ten_proofs_imports_bash_script_argv]


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

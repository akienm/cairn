#!/usr/bin/env python3
"""Proof for ticket a577fd03e307: exactly one place in Cairn asks the OS for this box's name, the
tool the system device publishes (cairn/devices/system_rackmount/tools/host/host.py).

Outline 6.6.3.7: nothing else in Cairn asks the OS for the hostname; callers reach it through the
client tool (RULE 1). Each site was repointed by its own child ticket (cffb99063d09, 15d5d434f336,
183f9389c5fa, ddbaaf055105, 6f91a994055d, c2eb9618c31d, ee2c8a73518b, 4366edb56144); this proof
reads red until every child lands.

  (1) an AST scan of every Python file under cairn/, skills/ and bin/ (a .py file, or an
      extensionless file whose first line is a python shebang) finds a call to os.uname,
      platform.node, platform.uname or socket.gethostname in exactly one file, host.py;
  (2) the same scanner over a scratch tree with one planted call of each spelling reports all
      four, so the scan cannot read green by seeing nothing.

Out of scope (the ticket's bounds): superclaude spells the host in bash, which cannot import the
tool; OS-family checks are not hostname reads.

    bin/cairn test cairn/devices/system_rackmount/tools/host/proofs/test_only_the_host_tool_asks_the_os_which_box.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"a577fd03e307": {"1": "test_only_the_host_tool_asks_the_os_which_box",
                           "2": "test_the_scanner_sees_every_planted_spelling"}}

TOOL = "cairn/devices/system_rackmount/tools/host/host.py"
ROOTS = ("cairn", "skills", "bin")
_OS_HOSTNAME_CALLS = {("os", "uname"), ("platform", "node"), ("platform", "uname"),
                      ("socket", "gethostname")}


def _is_python(p: Path) -> bool:
    if p.suffix == ".py":
        return True
    if p.suffix:
        return False
    try:
        with p.open("rb") as f:
            first = f.readline(200)
    except OSError:
        return False
    return first.startswith(b"#!") and b"python" in first


def _calls(src: str) -> list:
    """``[(lineno, spelling)]`` for each call that asks the OS which box."""
    tree = ast.parse(src)
    bare = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
            for a in n.names if (n.module, a.name) in _OS_HOSTNAME_CALLS}
    found = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                and (f.value.id, f.attr) in _OS_HOSTNAME_CALLS):
            found.append((n.lineno, f.value.id + "." + f.attr))
        elif isinstance(f, ast.Name) and f.id in bare:
            found.append((n.lineno, f.id))
    return found


def scan(root: Path, roots=ROOTS) -> dict:
    """``{relative path: [(lineno, spelling)]}`` over every Python file under ``roots``."""
    out = {}
    for top in roots:
        base = Path(root) / top
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts or not _is_python(p):
                continue
            try:
                src = p.read_text(encoding="utf-8")
                hits = _calls(src)
            except (UnicodeDecodeError, SyntaxError):
                continue
            if hits:
                out[p.relative_to(root).as_posix()] = hits
    return out


def test_only_the_host_tool_asks_the_os_which_box() -> None:
    found = scan(_REPO_ROOT)
    assert TOOL in found, f"the host tool itself asks nothing: {sorted(found)}"
    others = {k: v for k, v in found.items() if k != TOOL}
    assert not others, f"{len(others)} file(s) besides the host tool ask the OS which box: {others}"


def test_the_scanner_sees_every_planted_spelling() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir("cairn-hostscan-")
    plants = {
        "cairn/a.py": "import os\nn = os.uname().nodename\n",
        "skills/b.py": "import platform\nn = platform.node()\n",
        "bin/c": "#!/usr/bin/env python3\nimport platform\nn = platform.uname()\n",
        "cairn/d.py": "from socket import gethostname\nn = gethostname()\n",
        "bin/not_python": "#!/bin/sh\nhostname\n",
    }
    for rel, src in plants.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(src)
    found = scan(root)
    want = {"cairn/a.py": [(2, "os.uname")], "skills/b.py": [(2, "platform.node")],
            "bin/c": [(3, "platform.uname")], "cairn/d.py": [(2, "gethostname")]}
    assert found == want, found


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 2 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())

"""Proof for ticket 3301915df481, clauses 2 and 3: a tools/base proof that gives a subprocess a
scratch HOME gives it no bus address from its caller.

Measured 2026-11-12 on akienasus: with CAIRN_BUS_HOME=akiendelllinux.local:7419 in the session env,
test_root_verb_vocabulary.py's _run (dict(os.environ, HOME=scratch)) let the scratch-HOME child dial
the Dell's live bus, and test_get_status_is_uniform_across_the_roster red over the Dell's cairn status
while the Dell's own seal read it green. Under CAIRN_BUS_HOME=nowhere.invalid:7419 the same tooth
fails "the bus at nowhere.invalid:7419 did not answer", which is the deterministic falsifier below.

2. clause_2_the_status_tooth_ignores_the_callers_bus: the status tooth passes, run as written
   (pytest -k), with CAIRN_BUS_HOME=nowhere.invalid:7419 in the parent env;
3. clause_3_every_scratch_home_env_goes_through_home_env: no function in
   cairn/tools/base/proofs/test_*.py copies os.environ and sets a HOME key on the copy; a
   scratch-HOME env is built through cairn.tools.scratch.scratch.home_env.

    PYTHONPATH=. python3 cairn/tools/base/proofs/test_a_scratch_home_proof_reaches_no_live_bus.py
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "3301915df481": {
        "2": "clause_2_the_status_tooth_ignores_the_callers_bus",
        "3": "clause_3_every_scratch_home_env_goes_through_home_env",
    },
}

PROOFS = REPO / "cairn" / "tools" / "base" / "proofs"
VOCAB = PROOFS / "test_root_verb_vocabulary.py"
UNREACHABLE = "nowhere.invalid:7419"
_KEY = "HO" + "ME"   # spelled apart so this file's own scan does not read it as a HOME key
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail and not ok:
        print(f"        {detail[-1500:]}")
    if not ok:
        FAILURES.append(name)


def _is_environ(node: ast.AST) -> bool:
    return (isinstance(node, ast.Attribute) and node.attr == "environ"
            and isinstance(node.value, ast.Name) and node.value.id == "os")


def _copies_environ(node: ast.AST) -> bool:
    """dict(os.environ ...), {**os.environ}, os.environ.copy(), or a comprehension over it."""
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name) and f.id == "dict" and node.args and _is_environ(node.args[0]):
            return True
        if isinstance(f, ast.Attribute) and f.attr == "copy" and _is_environ(f.value):
            return True
    if isinstance(node, ast.Dict):
        return any(k is None and _is_environ(v) for k, v in zip(node.keys, node.values))
    if isinstance(node, ast.DictComp):
        it = node.generators[0].iter
        return (_is_environ(it) or (isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute)
                                    and _is_environ(it.func.value)))
    return False


def _sets_home(node: ast.AST) -> bool:
    if isinstance(node, ast.keyword) and node.arg == _KEY:
        return True
    if isinstance(node, ast.Dict):
        return any(isinstance(k, ast.Constant) and k.value == _KEY for k in node.keys)
    if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Store):
        return isinstance(node.slice, ast.Constant) and node.slice.value == _KEY
    return False


def scratch_home_from_environ(root: Path) -> list[str]:
    """'<file>:<line> <function>' for each function that copies os.environ and sets HOME."""
    out = []
    for py in sorted(root.glob("test_*.py")):
        tree = ast.parse(py.read_text(errors="replace"))
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            nodes = list(ast.walk(fn))
            if any(_copies_environ(n) for n in nodes) and any(_sets_home(n) for n in nodes):
                out.append(f"{py.name}:{fn.lineno} {fn.name}")
    return out


def tooth_2() -> None:
    name = PROVES["3301915df481"]["2"]
    env = dict(os.environ, CAIRN_BUS_HOME=UNREACHABLE)
    env["PYTHONPATH"] = str(REPO) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(VOCAB),
                            "-k", "test_get_status_is_uniform_across_the_roster"],
                           cwd=str(PROOFS), env=env, capture_output=True, text=True, timeout=600)
        check(name, r.returncode == 0, r.stdout + r.stderr)
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3() -> None:
    name = PROVES["3301915df481"]["3"]
    try:
        # non-vacuity: the scan names the measured spelling in a fixture, and passes a routed one
        from cairn.tools.scratch.scratch import scratch_dir
        fx = scratch_dir("cairn-proof-3301915df481-")
        (fx / "test_bare.py").write_text(
            "import os\ndef _run(home):\n    return dict(os.environ, " + _KEY + "=str(home))\n")
        (fx / "test_routed.py").write_text(
            "from cairn.tools.scratch.scratch import home_env\n"
            "def _run(home):\n    return home_env(home, PYTHONPATH='p')\n")
        sees = scratch_home_from_environ(fx)
        if sees != ["test_bare.py:2 _run"]:
            check(name, False, f"the scan is blind or over-broad on its fixture: {sees}")
            return
        hits = scratch_home_from_environ(PROOFS)
        check(name, hits == [], "scratch-HOME envs built from os.environ: " + "; ".join(hits))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    tooth_2()
    tooth_3()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
